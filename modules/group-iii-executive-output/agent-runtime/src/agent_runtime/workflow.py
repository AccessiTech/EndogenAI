"""workflow.py — Temporal IntentionWorkflow for agent-runtime.

DETERMINISM RULE: All I/O, LLM calls, side-effects, and timestamps MUST be
placed in Activities, never inside Workflow definitions. Workflow code
must be 100% deterministic and replay-safe.

Neuroanatomical analogue:
  - Striatal motor programme: pre-compiled action sequence loaded into execution
    buffer before movement begins.
  - BG direct pathway: disinhibited, committed motor sequence runs to completion.
  - BG hyperdirect: abort Signal interrupts the programme mid-execution.
  - Cerebellar BDI loop: revise_plan Update injects a corrected pipeline.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class IntentionWorkflow:
    """Durable Temporal Workflow for executing a committed BDI intention.

    Receives a goal_id and context_payload, decomposes via Activity,
    executes each SkillStep via Activity, and returns a result dict.

    Signals:
      abort() — gracefully stop after the current step completes.

    Updates:
      revise_plan(revised_pipeline) — inject a new pipeline mid-execution.

    Queries:
      get_status() — return current execution state.
    """

    def __init__(self) -> None:
        self._abort_requested: bool = False
        self._revision: dict[str, Any] | None = None
        self._current_step: str = ""
        self._steps_completed: int = 0

    @workflow.run
    async def run(self, goal_id: str, context_payload: dict[str, Any]) -> dict[str, Any]:
        """Main workflow execution.

        Phase 1: Decompose goal into SkillPipeline (Activity).
        Phase 2: Execute each SkillStep as an Activity.
        Phase 3: Emit final feedback.
        """
        # Phase 1: Decomposition (pre-SMA analogue — plan before execute)
        pipeline: dict[str, Any] = await workflow.execute_activity(
            "decompose_goal",
            args=[goal_id, context_payload],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        results: list[dict[str, Any]] = []
        for step in pipeline.get("steps", []):
            if self._abort_requested:
                return {"status": "aborted", "goal_id": goal_id, "results": results}

            # Apply pending revision if any
            if self._revision:
                pipeline = self._revision
                self._revision = None
                # Continue with revised pipeline from the beginning of remaining steps
                remaining_steps = pipeline.get("steps", [])[self._steps_completed :]
                for revised_step in remaining_steps:
                    if self._abort_requested:
                        break
                    result = await self._execute_step(revised_step, goal_id)
                    results.append(result)
                    await self._maybe_emit_partial_feedback(goal_id, result)
                # Propagate abort that arrived during the revision inner loop
                if self._abort_requested:
                    return {"status": "aborted", "goal_id": goal_id, "results": results}
                break

            result = await self._execute_step(step, goal_id)
            results.append(result)
            await self._maybe_emit_partial_feedback(goal_id, result)

        return {"status": "completed", "goal_id": goal_id, "results": results}

    async def _execute_step(
        self, step: dict[str, Any], goal_id: str
    ) -> dict[str, Any]:
        self._current_step = step.get("step_id", "")
        result: dict[str, Any] = await workflow.execute_activity(
            "dispatch_to_motor_output",
            args=[step, goal_id],
            start_to_close_timeout=timedelta(
                seconds=int(step.get("timeout_seconds", 120))
            ),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        self._steps_completed += 1
        return result

    async def _maybe_emit_partial_feedback(
        self, goal_id: str, result: dict[str, Any]
    ) -> None:
        if result.get("deviation_score", 0) > 0.5:
            await workflow.execute_activity(
                "emit_partial_feedback",
                args=[goal_id, result],
                start_to_close_timeout=timedelta(seconds=10),
            )

    @workflow.signal
    def abort(self) -> None:
        """BG hyperdirect pathway: interrupt execution after current step."""
        self._abort_requested = True

    @workflow.update
    def revise_plan(self, revised_pipeline: dict[str, Any]) -> str:
        """Cerebellar error correction: inject revised pipeline mid-execution."""
        self._revision = revised_pipeline
        return f"revision_accepted:{workflow.info().workflow_id}"

    @workflow.query
    def get_status(self) -> dict[str, Any]:
        """Return current workflow execution state."""
        return {
            "abort_requested": self._abort_requested,
            "has_pending_revision": self._revision is not None,
            "current_step": self._current_step,
            "steps_completed": self._steps_completed,
        }
