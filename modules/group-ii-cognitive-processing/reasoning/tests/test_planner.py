"""Unit tests for the CausalPlanner.

LiteLLM is mocked via unittest.mock.patch so no live LLM calls are made.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from reasoning.models import CausalPlan, InferenceTrace, ReasoningStrategy
from reasoning.planner import CausalPlanner


def _make_mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


class TestCausalPlanner:
    """Unit tests for CausalPlanner.create_plan with mocked LiteLLM."""

    @pytest.fixture
    def planner(self) -> CausalPlanner:
        return CausalPlanner(model="ollama/mistral", max_tokens=256, temperature=0.0, horizon=3)

    @pytest.mark.asyncio
    async def test_create_plan_returns_causal_plan(self, planner: CausalPlanner) -> None:
        """create_plan returns a valid CausalPlan with at least one step."""
        # Responses: step 1, step 2, DONE (stops loop), then uncertainty score
        step_responses = ["Step A: initialise system.", "Step B: process data.", "DONE", "0.25"]
        call_count = 0

        async def _side_effect(**kwargs: Any) -> MagicMock:
            nonlocal call_count
            idx = min(call_count, len(step_responses) - 1)
            resp = _make_mock_response(step_responses[idx])
            call_count += 1
            return resp

        with patch("reasoning.planner.litellm.acompletion", new=_side_effect):
            plan = await planner.create_plan(goal="Process data end-to-end.", context=[])

        assert isinstance(plan, CausalPlan)
        assert plan.goal == "Process data end-to-end."
        assert len(plan.steps) >= 1
        assert 0.0 <= plan.uncertainty <= 1.0

    @pytest.mark.asyncio
    async def test_create_plan_stops_at_done(self, planner: CausalPlanner) -> None:
        """Planning stops immediately when LLM returns 'DONE'."""
        call_count = 0

        async def _side_effect(**kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_mock_response("DONE")
            return _make_mock_response("0.5")

        with patch("reasoning.planner.litellm.acompletion", new=_side_effect):
            plan = await planner.create_plan(goal="Trivial goal.", context=[])

        assert plan.steps == []

    @pytest.mark.asyncio
    async def test_create_plan_respects_horizon(self) -> None:
        """Planner stops after horizon steps even if LLM never returns DONE."""
        short_planner = CausalPlanner(horizon=2)
        call_count = 0

        async def _side_effect(**kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            # Always return a step (never DONE), plus one uncertainty call
            if call_count <= 2:
                return _make_mock_response(f"Step {call_count}: do something.")
            return _make_mock_response("0.4")

        with patch("reasoning.planner.litellm.acompletion", new=_side_effect):
            plan = await short_planner.create_plan(goal="Open-ended goal.", context=[])

        assert len(plan.steps) == 2

    @pytest.mark.asyncio
    async def test_create_plan_uses_inference_traces(self, planner: CausalPlanner) -> None:
        """Prior inference traces are incorporated into context."""
        prior_trace = InferenceTrace(
            query="Prior question?",
            context=[],
            chain_of_thought=[],
            conclusion="Prior conclusion here.",
            confidence=0.9,
            strategy=ReasoningStrategy.DEDUCTIVE,
        )
        captured_prompts: list[str] = []

        async def _capture(**kwargs: Any) -> MagicMock:
            msgs = kwargs.get("messages", [])
            for m in msgs:
                captured_prompts.append(m.get("content", ""))
            return _make_mock_response("DONE")

        with patch("reasoning.planner.litellm.acompletion", new=_capture):
            await planner.create_plan(
                goal="Test goal.", context=[], inference_traces=[prior_trace]
            )

        all_content = " ".join(captured_prompts)
        assert "Prior conclusion here." in all_content

    @pytest.mark.asyncio
    async def test_create_plan_uncertainty_fallback_on_bad_response(
        self, planner: CausalPlanner
    ) -> None:
        """Uncertainty defaults to 0.5 when LLM returns non-numeric uncertainty text."""
        call_count = 0

        async def _side_effect(**kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_mock_response("Step 1: something meaningful.")
            return _make_mock_response("not a number at all")

        with patch("reasoning.planner.litellm.acompletion", new=_side_effect):
            plan = await planner.create_plan(goal="Goal.", context=[])

        assert plan.uncertainty == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_create_plan_ids_are_populated(self, planner: CausalPlanner) -> None:
        """All returned trace_ids come from prior inference traces."""
        traces = [
            InferenceTrace(
                query="Q?", context=[], chain_of_thought=[], conclusion="C.", confidence=0.7,
                strategy=ReasoningStrategy.DEDUCTIVE,
            )
        ]

        async def _side_effect(**kwargs: Any) -> MagicMock:
            return _make_mock_response("DONE")

        with patch("reasoning.planner.litellm.acompletion", new=_side_effect):
            plan = await planner.create_plan(goal="G.", context=[], inference_traces=traces)

        assert traces[0].id in plan.trace_ids
