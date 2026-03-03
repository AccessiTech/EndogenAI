"""tests/test_goal_stack.py — Unit tests for GoalStack.

Tests the priority queue, lifecycle transitions, capacity enforcement,
and BG pathway analogues (commit, suppress, abort).
"""
from __future__ import annotations

import pytest

from executive_agent.goal_stack import GoalStack, _validate_transition
from executive_agent.models import GoalItem, LifecycleState


def _make_goal(priority: float = 0.5, goal_class: str | None = None) -> GoalItem:
    return GoalItem(
        description="Test goal",
        priority=priority,
        goal_class=goal_class,
    )


class TestGoalStackPush:
    async def test_push_sets_pending_state(self) -> None:
        stack = GoalStack()
        goal = _make_goal(0.8)
        result = await stack.push(goal)
        assert result.lifecycle_state == LifecycleState.PENDING

    async def test_push_sorts_by_priority_descending(self) -> None:
        stack = GoalStack()
        await stack.push(_make_goal(0.3))
        await stack.push(_make_goal(0.9))
        await stack.push(_make_goal(0.6))
        all_goals = await stack.get_all()
        priorities = [g.priority for g in all_goals]
        assert priorities == sorted(priorities, reverse=True)

    async def test_push_returns_goal_with_id(self) -> None:
        stack = GoalStack()
        goal = _make_goal()
        result = await stack.push(goal)
        assert result.id is not None
        assert len(result.id) > 0


class TestGoalStackTransitions:
    async def test_valid_transition_pending_to_evaluating(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal())
        result = await stack.transition(goal.id, LifecycleState.EVALUATING)
        assert result.lifecycle_state == LifecycleState.EVALUATING

    async def test_invalid_transition_raises(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal())
        with pytest.raises(ValueError, match="Invalid lifecycle transition"):
            await stack.transition(goal.id, LifecycleState.COMPLETED)

    async def test_unknown_goal_raises_key_error(self) -> None:
        stack = GoalStack()
        with pytest.raises(KeyError):
            await stack.transition("nonexistent-id", LifecycleState.EVALUATING)

    async def test_commit_transitions_to_committed(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal())
        await stack.transition(goal.id, LifecycleState.EVALUATING)
        result = await stack.commit(goal.id, workflow_id="wf-123")
        assert result.lifecycle_state == LifecycleState.COMMITTED
        assert result.workflow_id == "wf-123"

    async def test_abort_from_executing_defers(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal())
        await stack.transition(goal.id, LifecycleState.EVALUATING)
        await stack.transition(goal.id, LifecycleState.COMMITTED)
        await stack.transition(goal.id, LifecycleState.EXECUTING)
        result = await stack.abort(goal.id, reason="test abort")
        assert result.lifecycle_state == LifecycleState.DEFERRED

    async def test_abort_from_evaluating_fails(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal())
        await stack.transition(goal.id, LifecycleState.EVALUATING)
        result = await stack.abort(goal.id, reason="deny")
        assert result.lifecycle_state == LifecycleState.FAILED


class TestGoalStackScoreUpdate:
    async def test_update_score_adjusts_priority(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal(0.5))
        await stack.update_score(goal.id, 0.1)
        updated = await stack.get(goal.id)
        assert abs(updated.priority - 0.6) < 0.001

    async def test_update_score_clamps_to_one(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal(0.95))
        await stack.update_score(goal.id, 0.2)
        updated = await stack.get(goal.id)
        assert updated.priority <= 1.0

    async def test_update_score_clamps_to_zero(self) -> None:
        stack = GoalStack()
        goal = await stack.push(_make_goal(0.05))
        await stack.update_score(goal.id, -0.2)
        updated = await stack.get(goal.id)
        assert updated.priority >= 0.0


class TestGoalStackCapacity:
    async def test_enforce_capacity_defers_pending_when_full(self) -> None:
        stack = GoalStack(max_active_goals=2)
        # Put 2 goals in EXECUTING state
        g1 = await stack.push(_make_goal(0.9))
        g2 = await stack.push(_make_goal(0.8))
        for g in [g1, g2]:
            await stack.transition(g.id, LifecycleState.EVALUATING)
            await stack.transition(g.id, LifecycleState.COMMITTED)
            await stack.transition(g.id, LifecycleState.EXECUTING)

        # Add a pending goal
        g3 = await stack.push(_make_goal(0.5))
        deferred = await stack.enforce_capacity()
        assert len(deferred) >= 1
        g3_state = await stack.get(g3.id)
        assert g3_state.lifecycle_state == LifecycleState.DEFERRED


class TestPopForEvaluation:
    async def test_pop_returns_pending_goals(self) -> None:
        stack = GoalStack()
        await stack.push(_make_goal(0.9))
        await stack.push(_make_goal(0.7))
        candidates = await stack.pop_for_evaluation(n=3)
        assert len(candidates) == 2
        assert all(g.lifecycle_state == LifecycleState.PENDING for g in candidates)

    async def test_pop_respects_n_limit(self) -> None:
        stack = GoalStack()
        for _ in range(5):
            await stack.push(_make_goal())
        candidates = await stack.pop_for_evaluation(n=2)
        assert len(candidates) == 2


class TestTransitionValidation:
    def test_terminal_states_allow_no_transitions(self) -> None:
        for terminal in [LifecycleState.COMPLETED, LifecycleState.FAILED]:
            with pytest.raises(ValueError):
                _validate_transition(terminal, LifecycleState.PENDING)
