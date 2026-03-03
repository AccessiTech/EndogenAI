"""metrics.py — All Prometheus / OTel metric instrument definitions.

All instruments use the ``brain_metacognition_`` prefix as required by the
Prometheus relabel filter in ``observability/prometheus.yml``.

Usage::

    tracer, meter = configure_telemetry(...)
    bundle = create_metrics(meter)
    bundle.task_confidence.set(0.85, {"task_type": "navigation"})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opentelemetry import metrics


@dataclass(frozen=True)
class MetricsBundle:
    """Container for all metacognition OTel metric instruments."""

    task_confidence: Any
    deviation_score: Any
    reward_delta: Any
    task_success_rate: Any
    escalation_total: Any
    retry_count: Any
    policy_denial_rate: Any
    deviation_zscore: Any


def create_metrics(meter: metrics.Meter) -> MetricsBundle:
    """Create all 8 metacognition metric instruments from the given meter.

    Args:
        meter: OTel Meter obtained from ``metrics.get_meter()``.

    Returns:
        MetricsBundle with all instruments ready to record.
    """
    task_confidence = meter.create_gauge(
        name="brain_metacognition_task_confidence",
        description="Rolling confidence score per task_type: f(reward_delta, success_rate). "
        "Range [0.0, 1.0]. Breach of confidence_threshold triggers request_correction.",
        unit="1",
    )

    deviation_score = meter.create_gauge(
        name="brain_metacognition_deviation_score",
        description="Rolling mean deviation_score from Phase 6 MotorFeedback over the "
        "observation window. Range [0.0, 1.0].",
        unit="1",
    )

    reward_delta = meter.create_histogram(
        name="brain_metacognition_reward_delta",
        description="Distribution of reward_delta values observed in the rolling window. "
        "Positive = improving; negative = degrading.",
        unit="1",
    )

    task_success_rate = meter.create_gauge(
        name="brain_metacognition_task_success_rate",
        description="Rolling fraction of successful task outcomes per task_type.",
        unit="1",
    )

    escalation_total = meter.create_counter(
        name="brain_metacognition_escalation_total",
        description="Cumulative count of escalation events received from Phase 6 modules.",
        unit="1",
    )

    retry_count = meter.create_histogram(
        name="brain_metacognition_retry_count",
        description="Distribution of retry_count values from Phase 6 motor-output feedback.",
        unit="1",
    )

    policy_denial_rate = meter.create_gauge(
        name="brain_metacognition_policy_denial_rate",
        description="Rolling fraction of BDI deliberation cycles where OPA policy denied "
        "an action.",
        unit="1",
    )

    deviation_zscore = meter.create_gauge(
        name="brain_metacognition_deviation_zscore",
        description="Z-score of deviation_score relative to rolling mean and std: "
        "(deviation_score - mu) / sigma.",
        unit="1",
    )

    return MetricsBundle(
        task_confidence=task_confidence,
        deviation_score=deviation_score,
        reward_delta=reward_delta,
        task_success_rate=task_success_rate,
        escalation_total=escalation_total,
        retry_count=retry_count,
        policy_denial_rate=policy_denial_rate,
        deviation_zscore=deviation_zscore,
    )
