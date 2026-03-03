"""feedback.py — Corollary discharge: MotorFeedback emission after every dispatch.

Spinocerebellar tract analogue: proprioceptive feedback comparing predicted
vs. actual outcomes. Active push to executive-agent after every dispatch.

The deviation_score is computed as 1 - Jaccard similarity between predicted
and actual outcome keys that are present in both dicts. This is a simple
heuristic; more sophisticated scoring can be substituted as Phase 7 metrics
become available.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from endogenai_a2a import A2AClient

from motor_output.models import ActionSpec, ChannelType, MotorFeedback

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def _compute_deviation(
    predicted: dict[str, Any] | None,
    actual: dict[str, Any],
) -> float:
    """Jaccard-based deviation between predicted and actual outcome dicts.

    Returns a float in [0.0, 1.0] where 0 = perfect match, 1 = total divergence.
    """
    if not predicted:
        return 0.5  # no prediction available → neutral deviation

    pred_keys = set(predicted.keys())
    actual_keys = set(actual.keys())
    intersection_keys = pred_keys & actual_keys

    if not intersection_keys and not (pred_keys | actual_keys):
        return 0.0

    # Key-level Jaccard distance
    key_score = len(intersection_keys) / max(len(pred_keys | actual_keys), 1)

    # For shared keys, compare values (1 if equal, 0.5 if not)
    value_matches = sum(
        1 if predicted.get(k) == actual.get(k) else 0.5
        for k in intersection_keys
    )
    value_score = value_matches / max(len(intersection_keys), 1)

    similarity = key_score * value_score
    return round(1.0 - similarity, 3)


class FeedbackEmitter:
    """Builds and emits MotorFeedback to executive-agent after every dispatch."""

    def __init__(self, executive_agent_url: str = "http://localhost:8161") -> None:
        self._executive_url = executive_agent_url

    def build_feedback(
        self,
        action_spec: ActionSpec,
        dispatch_result: dict[str, Any],
        dispatched_at: datetime,
    ) -> MotorFeedback:
        """Build MotorFeedback from ActionSpec + dispatch result."""
        completed_at = datetime.now(UTC)
        actual_outcome = {
            k: v for k, v in dispatch_result.items()
            if k not in {"retry_count", "escalated"}
        }
        deviation_score = _compute_deviation(
            action_spec.predicted_outcome,
            actual_outcome,
        )
        success: bool = dispatch_result.get("success", False)
        escalate: bool = (
            dispatch_result.get("escalated", False)
            or deviation_score > 0.8
        )
        retry_count: int = dispatch_result.get("retry_count", 0)
        latency_ms = (completed_at - dispatched_at).total_seconds() * 1000

        if not action_spec.goal_id:
            raise ValueError(
                "ActionSpec.goal_id is required to build MotorFeedback — "
                "cannot dispatch without a goal context."
            )

        return MotorFeedback(
            action_id=action_spec.action_id,
            goal_id=action_spec.goal_id,
            channel=action_spec.channel or ChannelType.HTTP,
            actual_outcome=actual_outcome,
            predicted_outcome=action_spec.predicted_outcome,
            deviation_score=deviation_score,
            success=success,
            escalate=escalate,
            reward_signal={"value": 1.0 if success else 0.0, "source": "motor_output"},
            dispatched_at=dispatched_at,
            completed_at=completed_at,
            retry_count=retry_count,
            latency_ms=latency_ms,
            error=dispatch_result.get("error"),
        )

    async def emit(self, feedback: MotorFeedback) -> None:
        """POST MotorFeedback to executive-agent A2A receive_feedback endpoint.

        Tolerant: logs errors but does not raise (non-fatal to the dispatch).
        """
        client = A2AClient(url=self._executive_url, timeout=10.0)
        try:
            await client.send_task("receive_feedback", feedback.model_dump(mode="json"))
            logger.info(
                "feedback.emitted",
                action_id=feedback.action_id,
                deviation_score=feedback.deviation_score,
                success=feedback.success,
            )
        except Exception as exc:
            logger.warning(
                "feedback.emit_failed",
                action_id=feedback.action_id,
                error=str(exc),
            )

    async def emit_preaction_signal(self, action_spec: ActionSpec) -> None:
        """SMA corollary discharge: send predicted ActionSpec BEFORE dispatch.

        Non-fatal if the executive-agent is unavailable.
        """
        client = A2AClient(url=self._executive_url, timeout=5.0)
        try:
            await client.send_task("preaction_signal", action_spec.model_dump(mode="json"))
            logger.debug("feedback.preaction_sent", action_id=action_spec.action_id)
        except Exception as exc:
            logger.debug("feedback.preaction_failed", error=str(exc))
