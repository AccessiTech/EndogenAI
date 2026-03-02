"""Shared pytest fixtures for the affective module tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter

from affective.a2a_handler import A2AHandler
from affective.drive import DriveStateMachine
from affective.mcp_tools import MCPTools
from affective.models import RewardSignal, SignalType, TriggerType
from affective.store import AffectiveStore
from affective.weighting import WeightingDispatcher


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


@pytest.fixture
def drive_machine() -> DriveStateMachine:
    return DriveStateMachine(
        urgency_threshold=0.7,
        novelty_decay_rate=0.1,
        curiosity_boost_factor=1.5,
    )


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=None)
    return adapter


@pytest.fixture
def affective_store(mock_adapter: MagicMock) -> AffectiveStore:
    return AffectiveStore(adapter=mock_adapter)


@pytest.fixture
def dispatcher() -> WeightingDispatcher:
    return WeightingDispatcher()


@pytest.fixture
def a2a_handler(
    affective_store: AffectiveStore,
    drive_machine: DriveStateMachine,
    dispatcher: WeightingDispatcher,
) -> A2AHandler:
    return A2AHandler(
        store=affective_store,
        drive_machine=drive_machine,
        dispatcher=dispatcher,
    )


@pytest.fixture
def mcp_tools(
    affective_store: AffectiveStore,
    drive_machine: DriveStateMachine,
    dispatcher: WeightingDispatcher,
) -> MCPTools:
    return MCPTools(
        store=affective_store,
        drive_machine=drive_machine,
        dispatcher=dispatcher,
    )
