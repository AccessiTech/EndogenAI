"""goal_stack.py — DLPFC-modelled goal stack with priority ordering and lifecycle management.

Neuroanatomical analogue:
  - DLPFC (BA 9/46): active maintenance, capacity-constrained, priority-ordered working memory
  - BG direct pathway: commit / disinhibit selected goal
  - BG indirect pathway: suppress competing goals of the same class
  - BG hyperdirect pathway: abort executing goal immediately (stop signal)
  - OFC: priority score updates from RPE actor-critic (MotorFeedback reward_signal)
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from executive_agent.models import GoalItem, LifecycleState

if TYPE_CHECKING:
    from collections.abc import Callable

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class GoalStack:
    """Priority-ordered goal stack with BDI lifecycle enforcement.

    Thread-safe via asyncio.Lock. Capacity enforced per IdentityConfig.maxActiveGoals.
    """

    def __init__(
        self,
        max_active_goals: int = 5,
        on_commit: Callable[[GoalItem], None] | None = None,
    ) -> None:
        self._goals: list[GoalItem] = []
        self._lock = asyncio.Lock()
        self.max_active_goals = max_active_goals
        self._on_commit = on_commit

    # -------------------------------------------------------------------------
    # Write operations
    # -------------------------------------------------------------------------

    async def push(self, goal: GoalItem) -> GoalItem:
        """Add a goal in PENDING state, then re-sort by priority descending."""
        async with self._lock:
            goal.lifecycle_state = LifecycleState.PENDING
            goal.updated_at = datetime.now(UTC)
            self._goals.append(goal)
            self._sort()
            logger.info("goal.pushed", goal_id=goal.id, priority=goal.priority)
            return goal

    async def transition(
        self,
        goal_id: str,
        new_state: LifecycleState,
        workflow_id: str | None = None,
    ) -> GoalItem:
        """Transition a goal to a new lifecycle state.

        Raises:
            KeyError: if goal_id not found.
            ValueError: if transition is invalid.
        """
        async with self._lock:
            goal = self._find(goal_id)
            _validate_transition(goal.lifecycle_state, new_state)
            goal.lifecycle_state = new_state
            goal.updated_at = datetime.now(UTC)
            if workflow_id is not None:
                goal.workflow_id = workflow_id
            logger.info(
                "goal.transitioned",
                goal_id=goal_id,
                new_state=new_state,
                workflow_id=workflow_id,
            )
            return goal

    async def commit(self, goal_id: str, workflow_id: str | None = None) -> GoalItem:
        """BG direct pathway: COMMITTED → triggers agent-runtime A2A call."""
        goal = await self.transition(goal_id, LifecycleState.COMMITTED, workflow_id)
        if self._on_commit:
            self._on_commit(goal)
        return goal

    async def abort(self, goal_id: str, reason: str) -> GoalItem:
        """BG hyperdirect pathway: immediately abort any executing goal."""
        async with self._lock:
            goal = self._find(goal_id)
            final_state = (
                LifecycleState.FAILED
                if goal.lifecycle_state == LifecycleState.EVALUATING
                else LifecycleState.DEFERRED
            )
            goal.lifecycle_state = final_state
            goal.updated_at = datetime.now(UTC)
            logger.warning("goal.aborted", goal_id=goal_id, reason=reason, final_state=final_state)
            return goal

    async def update_score(self, goal_id: str, reward_delta: float) -> GoalItem:
        """OFC actor-critic update: adjust priority by reward_delta and re-sort."""
        async with self._lock:
            goal = self._find(goal_id)
            goal.priority = max(0.0, min(1.0, goal.priority + reward_delta))
            goal.updated_at = datetime.now(UTC)
            self._sort()
            logger.debug("goal.score_updated", goal_id=goal_id, new_priority=goal.priority)
            return goal

    async def enforce_capacity(self) -> list[GoalItem]:
        """BG indirect pathway: defer lowest-priority PENDING goals if at capacity."""
        async with self._lock:
            active = [
                g
                for g in self._goals
                if g.lifecycle_state in (LifecycleState.COMMITTED, LifecycleState.EXECUTING)
            ]
            deferred: list[GoalItem] = []
            if len(active) >= self.max_active_goals:
                pending = [g for g in self._goals if g.lifecycle_state == LifecycleState.PENDING]
                for goal in pending:
                    goal.lifecycle_state = LifecycleState.DEFERRED
                    goal.updated_at = datetime.now(UTC)
                    deferred.append(goal)
                    logger.info("goal.deferred_capacity", goal_id=goal.id)
            return deferred

    # -------------------------------------------------------------------------
    # Read operations
    # -------------------------------------------------------------------------

    async def pop_for_evaluation(self, n: int = 3) -> list[GoalItem]:
        """Return top-n PENDING goals for the deliberation loop."""
        async with self._lock:
            pending = [g for g in self._goals if g.lifecycle_state == LifecycleState.PENDING]
            return pending[:n]

    async def get_all(self, filter_states: list[LifecycleState] | None = None) -> list[GoalItem]:
        """Return all goals, optionally filtered by lifecycle state."""
        async with self._lock:
            if filter_states is None:
                return list(self._goals)
            return [g for g in self._goals if g.lifecycle_state in filter_states]

    async def get(self, goal_id: str) -> GoalItem:
        """Return a single goal by ID. Raises KeyError if not found."""
        async with self._lock:
            return self._find(goal_id)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _find(self, goal_id: str) -> GoalItem:
        for goal in self._goals:
            if goal.id == goal_id:
                return goal
        raise KeyError(f"Goal not found: {goal_id}")

    def _sort(self) -> None:
        self._goals.sort(key=lambda g: g.priority, reverse=True)


# ---------------------------------------------------------------------------
# Transition validation table
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.PENDING: {LifecycleState.EVALUATING, LifecycleState.DEFERRED},
    LifecycleState.EVALUATING: {
        LifecycleState.COMMITTED,
        LifecycleState.PENDING,
        LifecycleState.FAILED,
        LifecycleState.DEFERRED,
    },
    LifecycleState.COMMITTED: {LifecycleState.EXECUTING, LifecycleState.DEFERRED},
    LifecycleState.EXECUTING: {
        LifecycleState.COMPLETED,
        LifecycleState.FAILED,
        LifecycleState.DEFERRED,
    },
    LifecycleState.COMPLETED: set(),
    LifecycleState.FAILED: set(),
    LifecycleState.DEFERRED: {LifecycleState.EVALUATING, LifecycleState.PENDING},
}


def _validate_transition(current: LifecycleState, new: LifecycleState) -> None:
    allowed = _VALID_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValueError(
            f"Invalid lifecycle transition: {current} → {new}. "
            f"Allowed from {current}: {allowed or 'none (terminal state)'}",
        )
