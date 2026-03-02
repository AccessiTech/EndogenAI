"""Unit tests for the inference pipeline (InferencePipeline, run_inference).

LiteLLM is mocked via unittest.mock.patch so no live LLM calls are made.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reasoning.inference import InferencePipeline, _parse_response
from reasoning.models import InferenceTrace, ReasoningStrategy

# ---------------------------------------------------------------------------
# _parse_response unit tests (pure function, no mocking needed)
# ---------------------------------------------------------------------------


class TestParseResponse:
    """Tests for the internal response-parsing helper."""

    def test_explicit_conclusion_marker(self) -> None:
        raw = "Step 1: analyse.\nStep 2: synthesise.\nConclusion: X causes Y."
        chain, conclusion = _parse_response(raw)
        assert "X causes Y." in conclusion
        assert len(chain) >= 1

    def test_no_marker_falls_back_to_last_paragraph(self) -> None:
        raw = "First paragraph content.\n\nSecond paragraph is the conclusion."
        chain, conclusion = _parse_response(raw)
        assert conclusion == "Second paragraph is the conclusion."

    def test_single_line_raw(self) -> None:
        raw = "Only one line."
        chain, conclusion = _parse_response(raw)
        assert conclusion == "Only one line."

    def test_empty_raw(self) -> None:
        chain, conclusion = _parse_response("")
        assert conclusion == ""

    def test_case_insensitive_conclusion(self) -> None:
        raw = "Step A.\nCONCLUSION: Done."
        _, conclusion = _parse_response(raw)
        assert "Done." in conclusion


# ---------------------------------------------------------------------------
# InferencePipeline tests (LiteLLM mocked)
# ---------------------------------------------------------------------------


def _make_mock_response(content: str) -> MagicMock:
    """Build a mock litellm.ModelResponse with the given content."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


class TestInferencePipeline:
    """Unit tests for InferencePipeline.run_inference with mocked LiteLLM."""

    @pytest.fixture
    def pipeline(self) -> InferencePipeline:
        return InferencePipeline(model="ollama/mistral", max_tokens=256, temperature=0.0)

    @pytest.mark.asyncio
    async def test_run_inference_returns_trace(self, pipeline: InferencePipeline) -> None:
        raw_response = "I reviewed the evidence.\nConclusion: The answer is 42."
        mock_resp = _make_mock_response(raw_response)

        with patch("reasoning.inference.litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            trace = await pipeline.run_inference(
                query="What is the answer?",
                context=["Evidence: 42 is the ultimate answer."],
            )

        assert isinstance(trace, InferenceTrace)
        assert trace.query == "What is the answer?"
        assert "42" in trace.conclusion
        assert 0.0 <= trace.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_run_inference_stores_context(self, pipeline: InferencePipeline) -> None:
        mock_resp = _make_mock_response("Step 1.\nConclusion: Result.")
        with patch("reasoning.inference.litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            trace = await pipeline.run_inference(
                query="Q?",
                context=["ctx A", "ctx B"],
            )
        assert "ctx A" in trace.context
        assert "ctx B" in trace.context

    @pytest.mark.asyncio
    async def test_run_inference_uses_model_override(self, pipeline: InferencePipeline) -> None:
        mock_resp = _make_mock_response("Conclusion: ok.")
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("reasoning.inference.litellm.acompletion", new=_capture):
            trace = await pipeline.run_inference(
                query="Q?",
                context=[],
                model_override="openai/gpt-4o",
            )

        assert captured["model"] == "openai/gpt-4o"
        assert trace.model_used == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_run_inference_strategy_is_recorded(self, pipeline: InferencePipeline) -> None:
        mock_resp = _make_mock_response("Conclusion: causal result.")
        with patch("reasoning.inference.litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            trace = await pipeline.run_inference(
                query="Why?",
                context=[],
                strategy=ReasoningStrategy.CAUSAL,
            )
        assert trace.strategy == ReasoningStrategy.CAUSAL

    @pytest.mark.asyncio
    async def test_run_inference_empty_response_handled(self, pipeline: InferencePipeline) -> None:
        mock_resp = _make_mock_response("")
        with patch("reasoning.inference.litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            trace = await pipeline.run_inference(query="Q?", context=[])
        assert isinstance(trace, InferenceTrace)
        assert trace.conclusion == ""

    @pytest.mark.asyncio
    async def test_run_inference_passes_api_base(self) -> None:
        pipeline = InferencePipeline(api_base="http://custom:11434")
        mock_resp = _make_mock_response("Conclusion: yes.")
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("reasoning.inference.litellm.acompletion", new=_capture):
            await pipeline.run_inference(query="Q?", context=[])

        assert captured.get("api_base") == "http://custom:11434"
