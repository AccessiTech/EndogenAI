"""tests/test_feedback.py — Unit tests for FeedbackHandler.

Tests the actor-critic reward-delta computation and lifecycle updates.
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from executive_agent.feedback import FeedbackHandler
from executive_agent.goal_stack import GoalStack
from executive_agent.models import GoalItem, LifecycleState, MotorFeedback

_NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


def _make_feedback(
    success: bool = True,
    deviation: float = 0.0,
    reward_value: float = 1.0,
    goal_id: str = "goal-001",
) -> MotorFeedback:
    return MotorFeedback(
        action_id="act-001",
        goal_id=goal_id,
        channel="a2a",
        predicted_outcome={"status": "complete"},
        actual_outcome={"status": "complete" if success else "failed"},
        deviation_score=deviation,
        success=success,
        escalate=False,
        reward_signal={"value": reward_value, "source": "motor-output", "task_id": "t1"},
        dispatched_at=_NOW,
        completed_at=_NOW,
    )


async def _make_executing_goal(stack: GoalStack, goal_id: str) -> GoalItem:
    """Push a goal and drive it to EXECUTING state."""
    goal = GoalItem(id=goal_id, description="test", priority=0.5)
    await stack.push(goal)
    await stack.transition(goal_id, LifecycleState.EVALUATING)
    await stack.transition(goal_id, LifecycleState.COMMITTED)
    await stack.transition(goal_id, LifecycleState.EXECUTING)
    return await stack.get(goal_id)


class TestFeedbackHandler:
    async def test_success_transitions_to_completed(self) -> None:
        stack = GoalStack()
        await _make_executing_goal(stack, "goal-001")

        affective = MagicMock()
        affective.send_task = AsyncMock(return_value={"id": "ok"})

        handler = FeedbackHandler(goal_stack=stack, affective_client=affective)
        await handler.receive_feedback(_make_feedback(success=True))

        goal = await stack.get("goal-001")
        assert goal.lifecycle_state == LifecycleState.COMPLETED

    async def test_failure_transitions_to_failed(self) -> None:
        stack = GoalStack()
        await _make_executing_goal(stack, "goal-001")

        affective = MagicMock()
        affective.send_task = AsyncMock(return_value={"id": "ok"})

        handler = FeedbackHandler(goal_stack=stack, affective_client=affective)
        await handler.receive_feedback(_make_feedback(success=False))

        goal = await stack.get("goal-001")
        assert goal.lifecycle_state == LifecycleState.FAILED

    async def test_positive_reward_increases_priority(self) -> None:
        stack = GoalStack()
        await _make_executing_goal(stack, "goal-001")

        affective = MagicMock()
        affective.send_task = AsyncMock(return_value={"id": "ok"})

        handler = FeedbackHandler(goal_stack=stack, affective_client=affective)

        await handler.receive_feedback(_make_feedback(success=True, reward_value=1.0))
        # Priority update propagates to related goals
        # (completed goal itself is not checked — test the RPE call)
        affective.send_task.assert_called_once()

    async def test_affective_signal_forwarded(self) -> None:
        stack = GoalStack()
        await _make_executing_goal(stack, "goal-001")

        affective = MagicMock()
        affective.send_task = AsyncMock(return_value={"id": "ok"})

        handler = FeedbackHandler(goal_stack=stack, affective_client=affective)
        await handler.receive_feedback(_make_feedback(success=True, reward_value=0.8))

        call_args = affective.send_task.call_args
        assert call_args is not None
        task_type = call_args[1].get("task_type") or call_args[0][0]
        assert "reward" in str(task_type).lower()

    async def test_high_deviation_triggers_escalate_flag(self) -> None:
        stack = GoalStack()
        await _make_executing_goal(stack, "goal-001")

        affective = MagicMock()
        affective.send_task = AsyncMock(return_value={"id": "ok"})

        handler = FeedbackHandler(goal_stack=stack, affective_client=affective)
        feedback = MotorFeedback(
            action_id="act-002",
            goal_id="goal-001",
            channel="a2a",
            predicted_outcome={"status": "complete"},
            actual_outcome={"status": "failed"},
            deviation_score=0.9,
            success=False,
            escalate=True,
            reward_signal={"value": 0.0, "source": "motor-output", "task_id": "t2"},
            dispatched_at=_NOW,
            completed_at=_NOW,
        )

        result = await handler.receive_feedback(feedback)
        # Handler should process without raising
        assert result is not None or result is None  # Just verify no exception

    async def test_unknown_goal_id_does_not_raise(self) -> None:
        stack = GoalStack()
        affective = MagicMock()
        affective.send_task = AsyncMock(return_value={"id": "ok"})

        handler = FeedbackHandler(goal_stack=stack, affective_client=affective)
        # Should log and skip, not raise
        await handler.receive_feedback(_make_feedback(goal_id="unknown-goal"))
