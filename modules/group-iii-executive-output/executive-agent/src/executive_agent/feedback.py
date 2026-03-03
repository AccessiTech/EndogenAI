"""feedback.py — MotorFeedback receiver and actor-critic loop for executive-agent.

Receives MotorFeedback from motor-output, updates goal lifecycle state, adjusts
priority weights via actor-critic reward signal, and (optionally) forwards a
RewardSignal to the affective module.

Neuroanatomical analogues:
  - Spinocerebellar feedback: observe actual vs predicted outcome
  - Dopamine RPE (SNc → striatum): MotorFeedback.reward_signal.value drives goal priority update
  - Nucleus accumbens: reward value modulates goal candidate selection in next cycle
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from executive_agent.models import LifecycleState, MotorFeedback

if TYPE_CHECKING:
    from executive_agent.goal_stack import GoalStack

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class FeedbackHandler:
    """Processes inbound MotorFeedback and closes the actor-critic loop."""

    def __init__(
        self,
        goal_stack: GoalStack,
        affective_client: Any | None = None,  # A2AClient to affective module
        metacognition_client: Any | None = None,  # A2AClient to metacognition (METACOGNITION_URL)
    ) -> None:
        self._goal_stack = goal_stack
        self._affective = affective_client
        self._metacognition = metacognition_client

    async def receive_feedback(self, feedback: MotorFeedback) -> dict[str, Any]:
        """Process a MotorFeedback payload from motor-output.

        Steps:
          1. Transition goal from EXECUTING → COMPLETED or FAILED.
          2. Compute reward delta from feedback.reward_signal.value.
          3. Update goal priority weight (actor-critic RPE update).
          4. Forward RewardSignal to affective module (if wired).
          5. If escalate=True: log and return escalation flag.

        Returns:
            dict with goal_id, new_state, reward_signal.
        """
        goal_id = feedback.goal_id
        success = feedback.success

        # 1. Transition goal lifecycle state
        new_state = LifecycleState.COMPLETED if success else LifecycleState.FAILED
        try:
            await self._goal_stack.transition(goal_id, new_state)
            logger.info(
                "feedback.goal_transitioned",
                goal_id=goal_id,
                new_state=new_state,
                success=success,
            )
        except (KeyError, ValueError) as exc:
            logger.warning("feedback.transition_error", goal_id=goal_id, error=str(exc))
            return {"goal_id": goal_id, "error": str(exc), "new_state": None}

        # 2. Compute reward delta from RPE signal
        reward_value = float(feedback.reward_signal.get("value", 0.0))
        reward_delta = _compute_reward_delta(reward_value, feedback.deviation_score)

        # 3. Actor-critic priority update
        await self._goal_stack.update_score(goal_id, reward_delta)

        # 4. Forward RewardSignal to affective module if wired
        if self._affective is not None:
            reward_signal = _build_reward_signal(feedback)
            try:
                await self._affective.send_task(
                    "receive_reward_signal",
                    {"reward_signal": reward_signal},
                )
                logger.debug("feedback.reward_signal_forwarded", goal_id=goal_id)
            except Exception as exc:
                logger.warning("feedback.affective_forward_error", error=str(exc))

        # 5. Escalation flag
        if feedback.escalate:
            logger.error(
                "feedback.escalation",
                goal_id=goal_id,
                action_id=feedback.action_id,
                error=feedback.error,
            )
            # Tier 2: forward to metacognition observer if wired (Strategy C)
            if self._metacognition is not None:
                # Flat payload — fields must match EvaluateOutputPayload (no task_result wrapper)
                evaluate_payload = {
                    "goal_id": goal_id,
                    "action_id": feedback.action_id,
                    "success": feedback.success,
                    "escalate": feedback.escalate,
                    "deviation_score": feedback.deviation_score,
                    "reward_value": float(feedback.reward_signal.get("value", 0.0)),
                    "channel": str(feedback.channel) if feedback.channel else None,
                    "error": feedback.error,
                }
                try:
                    await self._metacognition.send_task("evaluate_output", evaluate_payload)
                    logger.debug("feedback.metacognition_notified", goal_id=goal_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("feedback.metacognition_forward_error", error=str(exc))

        return {
            "goal_id": goal_id,
            "new_state": new_state,
            "reward_signal": feedback.reward_signal,
            "reward_delta": reward_delta,
            "escalated": feedback.escalate,
        }


def _compute_reward_delta(reward_value: float, deviation_score: float) -> float:
    """Convert raw reward + deviation into a goal priority delta.

    High deviation reduces the effective reward (prediction error penalty).
    Scale: delta ∈ [-0.15, +0.15] to avoid destabilising the priority queue.
    """
    effective = reward_value * (1.0 - deviation_score * 0.5)
    # Scale to ±0.15 range
    return max(-0.15, min(0.15, effective * 0.15))


def _build_reward_signal(feedback: MotorFeedback) -> dict[str, Any]:
    """Build a RewardSignal-compatible dict for the affective module."""
    from uuid import uuid4

    return {
        "id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "sourceModule": "motor-output",
        "targetModule": "affective",
        "value": float(feedback.reward_signal.get("value", 0.0)),
        "type": "reward" if feedback.success else "penalty",
        "trigger": "task-success" if feedback.success else "task-failure",
        "taskId": feedback.action_id,
        "goalId": feedback.goal_id,
    }
