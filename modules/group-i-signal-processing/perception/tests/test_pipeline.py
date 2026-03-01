"""Tests for the Perception pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from endogenai_perception.imports import Modality, Signal, SignalSource
from endogenai_perception.models import PerceptionResult
from endogenai_perception.pipeline import PerceptionPipeline


def _make_signal(
    modality: Modality = Modality.TEXT,
    payload: Any = "The quick brown fox",
    priority: int = 5,
) -> Signal:
    return Signal(
        type=f"{modality.value}.input",
        modality=modality,
        source=SignalSource(moduleId="attention-filtering", layer="attention-filtering"),
        payload=payload,
        priority=priority,
        timestamp=datetime.now(tz=UTC),
    )


def _make_mock_vs() -> MagicMock:
    """Return a mock VectorStoreAdapter."""
    vs = MagicMock()
    vs.upsert = AsyncMock(return_value=MagicMock(inserted=1, updated=0))
    return vs


class TestPerceptionPipeline:
    @pytest.mark.asyncio
    async def test_text_signal_produces_result(self) -> None:
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)

        llm_response = MagicMock()
        llm_response.choices[0].message.content = (
            '{"entities": ["fox"], "intent": "statement", '
            '"summary": "A quick fox.", "language": "en"}'
        )

        with patch("endogenai_perception.pipeline.litellm.acompletion", new=AsyncMock(return_value=llm_response)):
            result = await pipeline.process(_make_signal())

        assert isinstance(result, PerceptionResult)
        assert result.signal_id is not None
        assert result.features.entities == ["fox"]
        assert result.features.intent == "statement"
        assert result.features.language == "en"

    @pytest.mark.asyncio
    async def test_embedding_id_set_on_success(self) -> None:
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)

        llm_response = MagicMock()
        llm_response.choices[0].message.content = (
            '{"entities": [], "intent": "unknown", "summary": "test", "language": null}'
        )

        with patch("endogenai_perception.pipeline.litellm.acompletion", new=AsyncMock(return_value=llm_response)):
            result = await pipeline.process(_make_signal())

        assert result.embedding_id is not None
        vs.upsert.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_llm_failure_gracefully_degrades(self) -> None:
        """Pipeline must not raise when LLM call fails; features should be empty."""
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)

        with patch(
            "endogenai_perception.pipeline.litellm.acompletion",
            new=AsyncMock(side_effect=Exception("LLM unavailable")),
        ):
            result = await pipeline.process(_make_signal())

        assert isinstance(result, PerceptionResult)
        assert result.features.entities == []
        assert result.embedding_id is not None  # still stored

    @pytest.mark.asyncio
    async def test_image_signal_does_not_call_llm(self) -> None:
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)

        with patch("endogenai_perception.pipeline.litellm.acompletion", new=AsyncMock()) as mock_llm:
            result = await pipeline.process(_make_signal(modality=Modality.IMAGE, payload=b"\x89PNG\r\n"))

        mock_llm.assert_not_awaited()
        assert result.features.modality == "image"

    @pytest.mark.asyncio
    async def test_sensor_signal_extracts_dict_keys(self) -> None:
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)
        payload = {"temperature": 23.5, "humidity": 60.0}

        with patch("endogenai_perception.pipeline.litellm.acompletion", new=AsyncMock()):
            result = await pipeline.process(
                _make_signal(modality=Modality.SENSOR, payload=payload)
            )

        assert set(result.features.entities) == {"temperature", "humidity"}

    @pytest.mark.asyncio
    async def test_upsert_called_with_correct_collection(self) -> None:
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)

        llm_response = MagicMock()
        llm_response.choices[0].message.content = '{"entities": [], "intent": "observation", "summary": "ok", "language": "en"}'

        with patch("endogenai_perception.pipeline.litellm.acompletion", new=AsyncMock(return_value=llm_response)):
            await pipeline.process(_make_signal())

        call_args = vs.upsert.call_args
        request = call_args[0][0]
        assert request.collection_name == "brain.perception"

    @pytest.mark.asyncio
    async def test_priority_maps_to_importance_score(self) -> None:
        vs = _make_mock_vs()
        pipeline = PerceptionPipeline(vector_store=vs)
        signal = _make_signal(priority=8)

        llm_response = MagicMock()
        llm_response.choices[0].message.content = '{"entities": [], "intent": "observation", "summary": "ok", "language": "en"}'

        with patch("endogenai_perception.pipeline.litellm.acompletion", new=AsyncMock(return_value=llm_response)):
            await pipeline.process(signal)

        request = vs.upsert.call_args[0][0]
        item = request.items[0]
        assert item.importance_score == pytest.approx(0.8)
