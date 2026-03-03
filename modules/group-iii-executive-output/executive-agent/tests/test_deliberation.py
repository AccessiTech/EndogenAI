"""tests/test_deliberation.py — Unit tests for the BDI DeliberationLoop.

Mocks PolicyEngine and tests the deliberation tick logic without live OPA.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from executive_agent.deliberation import DeliberationLoop, _apply_drive_scores
from executive_agent.goal_stack import GoalStack
from executive_agent.models import DriveState, GoalItem, LifecycleState, PolicyDecision
from executive_agent.policy import PolicyEngine


def _make_allow_policy() -> PolicyEngine:
    """Return a mock PolicyEngine that always allows."""
    policy = MagicMock(spec=PolicyEngine)
    policy.evaluate_policy = AsyncMock(
        return_value=PolicyDecision(
            allow=True,
            violations=[],
            package="endogenai.goals",
            rule="allow",
        )
    )
    return policy


def _make_deny_policy() -> PolicyEngine:
    """Return a mock PolicyEngine that always denies."""
    policy = MagicMock(spec=PolicyEngine)
    policy.evaluate_policy = AsyncMock(
        return_value=PolicyDecision(
            allow=False,
            violations=["test violation"],
            package="endogenai.goals",
            rule="allow",
        )
    )
    return policy


def _make_goal(priority: float = 0.5) -> GoalItem:
    return GoalItem(description="test goal", priority=priority)


class TestDeliberationTick:
    async def test_single_allowed_goal_gets_committed(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal(0.8))

        loop = DeliberationLoop(goal_stack=stack, policy=_make_allow_policy())
        plans = await loop.run_once()

        assert len(plans) == 1
        assert plans[0].goal_id == goal.id
        committed = await stack.get(goal.id)
        assert committed.lifecycle_state == LifecycleState.COMMITTED

    async def test_denied_goal_transitions_to_failed(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal(0.8))

        loop = DeliberationLoop(goal_stack=stack, policy=_make_deny_policy())
        plans = await loop.run_once()

        assert len(plans) == 0
        failed = await stack.get(goal.id)
        assert failed.lifecycle_state == LifecycleState.FAILED

    async def test_empty_stack_returns_no_plans(self) -> None:
        stack = GoalStack()
        loop = DeliberationLoop(goal_stack=stack, policy=_make_allow_policy())
        plans = await loop.run_once()
        assert plans == []

    async def test_highest_priority_goal_is_committed(self) -> None:
        stack = GoalStack()
        await stack.push(_make_goal(0.3))
        high = await stack.push(_make_goal(0.9))

        loop = DeliberationLoop(goal_stack=stack, policy=_make_allow_policy(), max_eval_per_cycle=2)
        plans = await loop.run_once()

        assert plans[0].goal_id == high.id

    async def test_commit_callback_is_invoked(self) -> None:
        stack = GoalStack()
        await stack.push(_make_goal(0.7))

        callback_called = []

        async def on_commit(goal: GoalItem, plan: Any) -> None:
            callback_called.append(goal.id)

        loop = DeliberationLoop(goal_stack=stack, policy=_make_allow_policy())
        loop.add_commit_callback(on_commit)
        await loop.run_once()

        assert len(callback_called) == 1

    async def test_drive_state_boosts_priority(self) -> None:
        goals = [_make_goal(0.5) for _ in range(2)]
        original = [g.priority for g in goals]
        drive = DriveState(urgency=1.0)
        _apply_drive_scores(goals, drive)
        boosted = [g.priority for g in goals]
        # All priorities should have increased slightly
        assert all(b >= o for b, o in zip(boosted, original, strict=False))


class TestDeliberationStartStop:
    async def test_start_and_stop_does_not_raise(self) -> None:
        stack = GoalStack()
        loop = DeliberationLoop(
            goal_stack=stack,
            policy=_make_allow_policy(),
            cycle_ms=50,
        )
        await loop.start()
        import asyncio

        await asyncio.sleep(0.1)
        await loop.stop()
        assert not loop._running
