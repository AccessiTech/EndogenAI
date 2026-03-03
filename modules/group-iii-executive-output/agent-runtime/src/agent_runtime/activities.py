"""activities.py — Temporal Activities for agent-runtime.

All non-deterministic operations live here (I/O, LLM calls, HTTP, timestamps).
Activities are retryable by Temporal; keep them idempotent where possible.

Neuroanatomical analogue:
  - M1 motor neurons: the actual muscle activation — real-world side-effects occur here.
  - Spinocerebellar tract: each Activity reports actual outcome vs. predicted.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from endogenai_a2a import A2AClient
from temporalio import activity

from agent_runtime.models import ActionSpec, ChannelType

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class RuntimeActivities:
    """Container for Temporal Activity implementations.

    Receives injected dependencies (decomposer, motor-output URL, executive-agent URL)
    via constructor — supports dependency injection in tests.
    """

    def __init__(
        self,
        motor_output_url: str = "http://localhost:8163",
        executive_agent_url: str = "http://localhost:8161",
        decomposer: Any = None,  # PipelineDecomposer injected to break circular import
    ) -> None:
        self._motor_url = motor_output_url
        self._executive_url = executive_agent_url
        self._decomposer = decomposer

    @activity.defn(name="decompose_goal")
    async def decompose_goal(
        self, goal_id: str, context_payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Decompose a goal into a SkillPipeline.

        Phase 5 stub: calls LiteLLM directly via PipelineDecomposer.
        When reasoning module is available, delegate to it via A2A instead.
        """
        if self._decomposer is None:
            from agent_runtime.decomposer import PipelineDecomposer

            self._decomposer = PipelineDecomposer()

        description = context_payload.get("description", f"Goal {goal_id}")
        pipeline = await self._decomposer.decompose(
            goal_id=goal_id,
            description=description,
            context_payload=context_payload,
        )
        serialised: dict[str, Any] = pipeline.model_dump(mode="json")
        logger.info("activity.decompose_goal", goal_id=goal_id)
        return serialised

    @activity.defn(name="dispatch_to_motor_output")
    async def dispatch_to_motor_output(
        self, step: dict[str, Any], goal_id: str
    ) -> dict[str, Any]:
        """Build an ActionSpec and dispatch to motor-output via A2A.

        Returns the MotorFeedback dict from motor-output.
        """
        action_spec = ActionSpec(
            type=step.get("tool_id", "unknown"),
            channel=ChannelType(step.get("channel", "a2a")),
            params=step.get("params", {}),
            goal_id=goal_id,
            step_id=step.get("step_id"),
            timeout_seconds=int(step.get("timeout_seconds", 120)),
            predicted_outcome=step.get("expected_output"),
        )

        client = A2AClient(
            url=self._motor_url,
            timeout=float(action_spec.timeout_seconds),
        )
        result: dict[str, Any] = await client.send_task(
            "dispatch_action",
            action_spec.model_dump(mode="json"),
        )
        logger.info(
            "activity.dispatch_to_motor_output",
            goal_id=goal_id,
            step_id=step.get("step_id"),
            success=result.get("success"),
        )
        return result

    @activity.defn(name="emit_partial_feedback")
    async def emit_partial_feedback(
        self, goal_id: str, result: dict[str, Any]
    ) -> None:
        """Emit partial MotorFeedback to executive-agent after a high-deviation step.

        Spinocerebellum analogue: intermediate error correction before pipeline completes.
        """
        now = datetime.now(UTC).isoformat()
        feedback_payload = {
            "action_id": result.get("action_id", ""),
            "goal_id": goal_id,
            "channel": result.get("channel", "a2a"),
            "predicted_outcome": result.get("predicted_outcome"),
            "actual_outcome": result.get("actual_outcome", {}),
            "deviation_score": result.get("deviation_score", 0.0),
            "success": result.get("success", True),
            "escalate": result.get("deviation_score", 0.0) > 0.8,
            "reward_signal": result.get("reward_signal", {"value": 0.5, "source": "partial"}),
            "dispatched_at": result.get("dispatched_at", now),
            "completed_at": now,
        }

        client = A2AClient(url=self._executive_url, timeout=10.0)
        try:
            await client.send_task("receive_feedback", feedback_payload)
            logger.info("activity.partial_feedback_sent", goal_id=goal_id)
        except Exception as exc:
            logger.warning(
                "activity.partial_feedback_error", goal_id=goal_id, error=str(exc)
            )
            # Non-fatal: continue execution even if feedback fails
