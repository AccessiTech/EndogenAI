"""test_a2a_handler.py — Unit tests for A2A task handler."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from motor_output.a2a_handler import handle_task
from motor_output.models import ChannelType, DispatchRecord, DispatchStatus, MotorFeedback


def _now() -> datetime:
    return datetime.now(UTC)


def _sample_feedback(action_id: str = "act-001") -> MotorFeedback:
    return MotorFeedback(
        action_id=action_id,
        goal_id="goal-001",
        channel=ChannelType.HTTP,
        actual_outcome={"success": True},
        success=True,
        dispatched_at=_now(),
        completed_at=_now(),
    )


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    d = MagicMock()
    d.dispatch = AsyncMock(return_value=_sample_feedback())
    d.dispatch_batch = AsyncMock(return_value=[_sample_feedback()])
    d.get_record = MagicMock(return_value=None)
    d.abort_dispatch = MagicMock(return_value=True)
    return d


@pytest.mark.asyncio
async def test_dispatch_action(mock_dispatcher: MagicMock) -> None:
    result = await handle_task(
        "dispatch_action",
        {"action_id": "act-001", "type": "test.call", "channel": "http", "params": {}},
        mock_dispatcher,
    )
    assert result["action_id"] == "act-001"
    assert result["success"] is True


@pytest.mark.asyncio
async def test_get_status_not_found(mock_dispatcher: MagicMock) -> None:
    result = await handle_task("get_status", {"action_id": "nope"}, mock_dispatcher)
    assert "error" in result


@pytest.mark.asyncio
async def test_get_status_found(mock_dispatcher: MagicMock) -> None:
    mock_dispatcher.get_record.return_value = DispatchRecord(
        action_id="act-001",
        channel=ChannelType.HTTP,
        status=DispatchStatus.SUCCESS,
    )
    result = await handle_task("get_status", {"action_id": "act-001"}, mock_dispatcher)
    assert result["action_id"] == "act-001"


@pytest.mark.asyncio
async def test_abort_dispatch(mock_dispatcher: MagicMock) -> None:
    result = await handle_task("abort_dispatch", {"action_id": "act-001"}, mock_dispatcher)
    assert result["aborted"] is True


@pytest.mark.asyncio
async def test_dispatch_batch(mock_dispatcher: MagicMock) -> None:
    payload = {
        "action_specs": [
            {"action_id": "b1", "type": "test.call", "channel": "http", "params": {}},
        ]
    }
    result = await handle_task("dispatch_batch", payload, mock_dispatcher)
    assert "results" in result
    assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_unknown_task_type(mock_dispatcher: MagicMock) -> None:
    result = await handle_task("unknown_type", {}, mock_dispatcher)
    assert "error" in result
