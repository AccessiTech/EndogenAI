"""test_a2a_handler.py — Unit tests for executive-agent A2A task handler.

Covers all 4 task types:
  - commit_intention
  - receive_feedback
  - abort_goal
  - get_identity
  - unknown task type raises ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from executive_agent.a2a_handler import handle_task
from executive_agent.models import GoalItem, LifecycleState, SelfModel


def _make_goal(state: LifecycleState = LifecycleState.PENDING) -> GoalItem:
    return GoalItem(
        description="Test goal",
        priority=0.8,
        lifecycle_state=state,
    )


def _make_self_model() -> SelfModel:
    return SelfModel(
        agent_name="test-agent",
        agent_version="0.1.0",
        core_values=["helpfulness"],
        max_active_goals=5,
        deliberation_cycle_ms=1000,
    )


# ---------------------------------------------------------------------------
# commit_intention
# ---------------------------------------------------------------------------


async def test_commit_intention_no_runtime() -> None:
    goal = _make_goal(LifecycleState.PENDING)
    goal_stack = MagicMock()
    goal_stack.transition = AsyncMock()
    goal_stack.get = AsyncMock(return_value=goal)

    with (
        patch("executive_agent.a2a_handler._handle_commit_intention") as mock_handler,
    ):
        mock_handler.return_value = goal.model_dump(mode="json")
        result = await handle_task(
            "commit_intention",
            {"goal_id": goal.id, "context_payload": {}},
        )
    assert "id" in result


async def test_commit_intention_with_runtime() -> None:
    goal = _make_goal(LifecycleState.COMMITTED)
    goal_stack = MagicMock()
    goal_stack.transition = AsyncMock()
    goal_stack.get = AsyncMock(return_value=goal)

    runtime_client = MagicMock()
    runtime_client.send_task = AsyncMock(return_value={"workflow_id": "wf-123"})

    with (
        patch("executive_agent.server.get_goal_stack", return_value=goal_stack),
        patch("executive_agent.server.get_runtime_client", return_value=runtime_client),
    ):
        result = await handle_task(
            "commit_intention",
            {"goal_id": goal.id, "context_payload": {"key": "val"}},
        )
    assert "id" in result
    goal_stack.transition.assert_awaited()


async def test_commit_intention_runtime_error() -> None:
    """Runtime delegation error is swallowed gracefully."""
    goal = _make_goal(LifecycleState.COMMITTED)
    goal_stack = MagicMock()
    goal_stack.transition = AsyncMock()
    goal_stack.get = AsyncMock(return_value=goal)

    runtime_client = MagicMock()
    runtime_client.send_task = AsyncMock(side_effect=RuntimeError("connection refused"))

    with (
        patch("executive_agent.server.get_goal_stack", return_value=goal_stack),
        patch("executive_agent.server.get_runtime_client", return_value=runtime_client),
    ):
        result = await handle_task(
            "commit_intention",
            {"goal_id": goal.id},
        )
    assert "id" in result


# ---------------------------------------------------------------------------
# receive_feedback
# ---------------------------------------------------------------------------


async def test_receive_feedback() -> None:
    goal = _make_goal()
    feedback_handler = MagicMock()
    feedback_handler.receive_feedback = AsyncMock(
        return_value={"goal_id": goal.id, "new_state": "ACTIVE", "reward_signal": 0.9}
    )

    import datetime
    now = datetime.datetime.now(datetime.UTC).isoformat()
    feedback_payload = {
        "action_id": "act-1",
        "goal_id": goal.id,
        "channel": "mcp",
        "actual_outcome": {"result": "success"},
        "deviation_score": 0.1,
        "success": True,
        "escalate": False,
        "reward_signal": {"value": 0.8},
        "dispatched_at": now,
        "completed_at": now,
    }

    with patch("executive_agent.server.get_feedback_handler", return_value=feedback_handler):
        result = await handle_task("receive_feedback", {"motor_feedback": feedback_payload})

    assert result["goal_id"] == goal.id
    feedback_handler.receive_feedback.assert_awaited_once()


# ---------------------------------------------------------------------------
# abort_goal
# ---------------------------------------------------------------------------


async def test_abort_goal() -> None:
    goal = _make_goal(LifecycleState.DEFERRED)
    goal_stack = MagicMock()
    goal_stack.abort = AsyncMock(return_value=goal)

    with patch("executive_agent.server.get_goal_stack", return_value=goal_stack):
        result = await handle_task(
            "abort_goal",
            {"goal_id": goal.id, "reason": "test abort"},
        )

    assert "id" in result
    goal_stack.abort.assert_awaited_once_with(goal.id, "test abort")


async def test_abort_goal_default_reason() -> None:
    goal = _make_goal(LifecycleState.DEFERRED)
    goal_stack = MagicMock()
    goal_stack.abort = AsyncMock(return_value=goal)

    with patch("executive_agent.server.get_goal_stack", return_value=goal_stack):
        await handle_task("abort_goal", {"goal_id": goal.id})

    goal_stack.abort.assert_awaited_once_with(goal.id, "abort requested via A2A")


# ---------------------------------------------------------------------------
# get_identity
# ---------------------------------------------------------------------------


async def test_get_identity() -> None:
    self_model = _make_self_model()
    identity_manager = MagicMock()
    identity_manager.get_self_model = MagicMock(return_value=self_model)

    with patch("executive_agent.server.get_identity_manager", return_value=identity_manager):
        result = await handle_task("get_identity", {})

    assert result["agent_name"] == "test-agent"


# ---------------------------------------------------------------------------
# unknown task
# ---------------------------------------------------------------------------


async def test_unknown_task_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown A2A task type"):
        await handle_task("nonexistent", {})
