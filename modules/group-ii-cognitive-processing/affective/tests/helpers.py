"""Test helper factories for the affective module test suite."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from affective.models import RewardSignal, SignalType, TriggerType


def make_reward_signal(
    signal_id: str | None = None,
    value: float = 0.6,
    signal_type: SignalType = SignalType.REWARD,
    trigger: TriggerType = TriggerType.TASK_SUCCESS,
    memory_item_id: str | None = None,
    session_id: str | None = None,
) -> RewardSignal:
    """Factory helper for RewardSignal test instances."""
    return RewardSignal(
        id=signal_id or str(uuid.uuid4()),
        timestamp=datetime.now(UTC).isoformat(),
        sourceModule="affective",
        value=value,
        type=signal_type,
        trigger=trigger,
        associatedMemoryItemId=memory_item_id,
        sessionId=session_id,
    )
