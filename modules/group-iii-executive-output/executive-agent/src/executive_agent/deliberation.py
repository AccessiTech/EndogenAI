"""deliberation.py — BDI interpreter loop for executive-agent.

Implements the classic BDI cycle:
  1. option_generation: select PENDING goals for evaluation
  2. value_scoring: score via OFC (priority + drive state)
  3. policy_evaluation: run OPA allow check for each candidate
  4. intention_commitment: commit the highest-scoring OPA-allowed goal
  5. reconsideration_check: re-evaluate COMMITTED goals on feedback

Neuroanatomical analogues:
  - DLPFC: maintains goal stack across cycle iterations
  - OFC: value scoring drives priority ordering
  - ACC: OPA violations trigger deliberation pause
  - BG direct / indirect / hyperdirect: commit / suppress / abort
  - vmPFC: fast heuristic pre-filter before full OPA call
"""
from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from executive_agent.models import (
    BDIPlan,
    DriveState,
    GoalItem,
    LifecycleState,
)

if TYPE_CHECKING:
    from executive_agent.goal_stack import GoalStack
    from executive_agent.policy import PolicyEngine

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class DeliberationLoop:
    """Runs the BDI deliberation cycle on a configurable tick.

    Each tick:
      1. Pop top-n PENDING goals for evaluation.
      2. Score each against the current drive state.
      3. Run OPA allow check (endogenai.goals).
      4. Commit the highest-scoring allowed goal.
      5. Enforce capacity limits (BG indirect suppression).

    The loop runs as an asyncio background task. Start with start() and
    stop with stop().
    """

    def __init__(
        self,
        goal_stack: GoalStack,
        policy: PolicyEngine,
        cycle_ms: int = 1000,
        max_eval_per_cycle: int = 3,
        active_goals_for_opa: list[GoalItem] | None = None,
    ) -> None:
        self._goal_stack = goal_stack
        self._policy = policy
        self._cycle_ms = cycle_ms
        self._max_eval = max_eval_per_cycle
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._drive_state: DriveState = DriveState()
        self._committed_plans: list[BDIPlan] = []
        self._on_commit_callbacks: list[Any] = []

    def add_commit_callback(self, fn: Any) -> None:  # noqa: ANN401 – callback type
        """Register a callback invoked when a goal is committed."""
        self._on_commit_callbacks.append(fn)

    def update_drive_state(self, drive: DriveState) -> None:
        """Update drive variables from the affective module (called externally)."""
        self._drive_state = drive

    async def start(self) -> None:
        """Start the deliberation background loop."""
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("deliberation.started", cycle_ms=self._cycle_ms)

    async def stop(self) -> None:
        """Stop the deliberation loop gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("deliberation.stopped")

    async def run_once(self) -> list[BDIPlan]:
        """Execute a single deliberation cycle. Useful for testing."""
        return await self._tick()

    # -------------------------------------------------------------------------
    # Internal loop
    # -------------------------------------------------------------------------

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as exc:
                logger.error("deliberation.tick_error", error=str(exc))
            await asyncio.sleep(self._cycle_ms / 1000.0)

    async def _tick(self) -> list[BDIPlan]:
        """One deliberation cycle. Returns list of newly committed plans."""
        # 1. Option generation — select PENDING goals
        candidates = await self._goal_stack.pop_for_evaluation(self._max_eval)
        if not candidates:
            return []

        # Mark as EVALUATING
        for goal in candidates:
            with contextlib.suppress(KeyError, ValueError):
                await self._goal_stack.transition(goal.id, LifecycleState.EVALUATING)

        # 2. Value scoring — boost priority by urgency drive variable
        scored = _apply_drive_scores(candidates, self._drive_state)

        # 3. OPA policy evaluation — endogenai.goals.allow
        active_goals = await self._goal_stack.get_all(
            filter_states=[LifecycleState.COMMITTED, LifecycleState.EXECUTING]
        )
        allowed: list[GoalItem] = []
        for goal in scored:
            decision = await self._policy.evaluate_policy(
                package="endogenai.goals",
                rule="allow",
                input_data={
                    "candidate": goal.model_dump(),
                    "active_goals": [g.model_dump() for g in active_goals],
                    "config": {"maxActiveGoals": self._goal_stack.max_active_goals},
                },
            )
            if decision.allow:
                allowed.append(goal)
            else:
                logger.warning(
                    "deliberation.goal_denied",
                    goal_id=goal.id,
                    violations=decision.violations,
                )
                await self._goal_stack.transition(goal.id, LifecycleState.FAILED)

        if not allowed:
            # Return unchosen goals to PENDING
            pending_back = [g for g in scored if g.id not in {a.id for a in allowed}]
            for goal in pending_back:
                with contextlib.suppress(KeyError, ValueError):
                    await self._goal_stack.transition(goal.id, LifecycleState.PENDING)
            return []

        # 4. Intention commitment — commit the highest-scoring allowed goal
        best = max(allowed, key=lambda g: g.priority)
        committing = [best]

        # Return remaining allowed goals to PENDING
        for goal in allowed:
            if goal.id != best.id:
                with contextlib.suppress(KeyError, ValueError):
                    await self._goal_stack.transition(goal.id, LifecycleState.PENDING)

        # Return denied/not-selected candidates to PENDING
        not_selected = [g for g in scored if g.id not in {c.id for c in committing}]
        for goal in not_selected:
            if goal.id != best.id:
                with contextlib.suppress(KeyError, ValueError):
                    await self._goal_stack.transition(goal.id, LifecycleState.PENDING)

        plans: list[BDIPlan] = []
        for goal in committing:
            plan = BDIPlan(
                goal_id=goal.id,
                pipeline_request={"goal_id": goal.id, "context_payload": goal.context_payload},
                committed_at=datetime.now(UTC),
            )
            self._committed_plans.append(plan)
            await self._goal_stack.commit(goal.id)
            for callback in self._on_commit_callbacks:
                try:
                    await callback(goal, plan)
                except Exception as exc:
                    logger.error("deliberation.commit_callback_error", error=str(exc))
            plans.append(plan)

        # 5. Enforce capacity (BG indirect suppression)
        await self._goal_stack.enforce_capacity()

        logger.info("deliberation.tick_complete", committed_count=len(plans))
        return plans


def _apply_drive_scores(goals: list[GoalItem], drive: DriveState) -> list[GoalItem]:
    """OFC analogue: boost priority by drive urgency, then re-sort."""
    for goal in goals:
        boost = drive.urgency * 0.1  # small boost from affective state
        goal.priority = min(1.0, goal.priority + boost)
    goals.sort(key=lambda g: g.priority, reverse=True)
    return goals
