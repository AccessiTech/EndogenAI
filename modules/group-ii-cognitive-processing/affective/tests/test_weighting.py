"""Unit tests for WeightingDispatcher — importanceScore boost dispatch."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from affective.models import RewardSignal, SignalType, TriggerType
from affective.weighting import WeightingDispatcher


def _make_signal(
    value: float = 0.6,
    signal_type: SignalType = SignalType.REWARD,
    trigger: TriggerType = TriggerType.TASK_SUCCESS,
    memory_item_id: str | None = None,
) -> RewardSignal:
    return RewardSignal(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(UTC).isoformat(),
        sourceModule="affective",
        value=value,
        type=signal_type,
        trigger=trigger,
        associatedMemoryItemId=memory_item_id,
    )


class TestWeightingDispatcher:
    """Unit tests for WeightingDispatcher without live network calls."""

    def test_tag_from_signal_with_memory_link(self) -> None:
        memory_id = str(uuid.uuid4())
        signal = _make_signal(value=0.7, memory_item_id=memory_id)
        dispatcher = WeightingDispatcher()
        tag = dispatcher.tag_from_signal(signal)
        assert tag is not None
        assert tag.memory_item_id == memory_id
        assert tag.valence == pytest.approx(0.7)
        assert tag.arousal == pytest.approx(0.7)
        assert tag.source_signal_id == signal.id

    def test_tag_from_signal_without_memory_link(self) -> None:
        signal = _make_signal(value=0.5, memory_item_id=None)
        dispatcher = WeightingDispatcher()
        assert dispatcher.tag_from_signal(signal) is None

    async def test_dispatch_boost_no_memory_link_skips(self) -> None:
        signal = _make_signal(value=0.8, memory_item_id=None)
        dispatcher = WeightingDispatcher()
        result = await dispatcher.dispatch_boost(signal)
        assert result["status"] == "skipped"
        assert result["reason"] == "no_memory_link"

    async def test_dispatch_boost_below_threshold_skips(self) -> None:
        memory_id = str(uuid.uuid4())
        signal = _make_signal(value=0.05, memory_item_id=memory_id)
        dispatcher = WeightingDispatcher()
        result = await dispatcher.dispatch_boost(signal)
        assert result["status"] == "skipped"
        assert result["reason"] == "below_threshold"

    async def test_dispatch_boost_intent_logged_without_client(self) -> None:
        memory_id = str(uuid.uuid4())
        signal = _make_signal(value=0.6, memory_item_id=memory_id)
        dispatcher = WeightingDispatcher()  # no client → logs intent
        result = await dispatcher.dispatch_boost(signal)
        assert result["status"] == "intent_logged"
        assert result["boost"] == pytest.approx(0.5, abs=0.1)

    async def test_dispatch_boost_calls_a2a_client(self, mocker: object) -> None:
        """When an A2AClient is injected, send_task is called with correct args."""
        from unittest.mock import AsyncMock, MagicMock

        from endogenai_a2a import A2AClient

        memory_id = str(uuid.uuid4())
        signal = _make_signal(value=0.8, memory_item_id=memory_id)

        mock_client = MagicMock(spec=A2AClient)
        mock_client.send_task = AsyncMock(return_value={"status": "ok"})

        dispatcher = WeightingDispatcher(a2a_client=mock_client)
        result = await dispatcher.dispatch_boost(signal)
        assert result["status"] == "dispatched"
        mock_client.send_task.assert_awaited_once()

    def test_compute_importance_boost_positive(self) -> None:
        signal = _make_signal(value=0.9)
        dispatcher = WeightingDispatcher()
        boost = dispatcher._compute_importance_boost(signal)
        assert boost == pytest.approx(0.5)  # clamped at 0.5

    def test_compute_importance_boost_negative(self) -> None:
        signal = _make_signal(
            value=-0.8,
            signal_type=SignalType.PENALTY,
            trigger=TriggerType.TASK_FAILURE,
        )
        dispatcher = WeightingDispatcher()
        boost = dispatcher._compute_importance_boost(signal)
        assert boost == pytest.approx(-0.5)  # clamped at -0.5

    def test_compute_importance_boost_neutral(self) -> None:
        signal = _make_signal(value=0.0, signal_type=SignalType.NEUTRAL)
        dispatcher = WeightingDispatcher()
        boost = dispatcher._compute_importance_boost(signal)
        assert boost == pytest.approx(0.0)
