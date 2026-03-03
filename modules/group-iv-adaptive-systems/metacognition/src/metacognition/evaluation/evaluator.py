"""evaluator.py — MetacognitionEvaluator: rolling confidence and deviation z-score.

Implements the ACC error-detection and PFC-BA10 confidence estimation analogue:

  task_confidence = 0.5 * clamp01(rolling_mean_reward_delta) + 0.5 * success_rate
  deviation_zscore = (deviation_score - mu) / sigma
  error_detected   = deviation_zscore > deviation_error_threshold
  correction_triggered = task_confidence < confidence_threshold
                         sustained for >= alert_window_minutes

Neuroanatomical reference:
  ACC (anterior cingulate cortex) — error detection via deviation z-score
  PFC BA10 — prospective confidence calibration via rolling reward and success rate
"""

from __future__ import annotations

import math
import uuid
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from metacognition.instrumentation.metrics import MetricsBundle

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Config model (mirrors monitoring.config.json)
# ---------------------------------------------------------------------------


class MonitoringConfig(BaseModel):
    """Runtime configuration for the metacognition module."""

    confidence_threshold: float = 0.7
    anomaly_zscore_threshold: float = 2.5
    deviation_error_threshold: float = 0.75
    rolling_window_size: int = 20
    alert_window_minutes: int = 5
    otlp_endpoint: str = "http://localhost:4317"
    prometheus_port: int = 9464
    metrics_export: dict[str, bool] = Field(
        default_factory=lambda: {"otlp_enabled": True, "prometheus_enabled": True}
    )
    escalation_enabled: bool = True
    executive_agent_url: str = "http://localhost:8161"
    chromadb_url: str = "http://localhost:8000"
    service_name: str = "metacognition"
    service_namespace: str = "brain"


# ---------------------------------------------------------------------------
# Inbound A2A payload model
# ---------------------------------------------------------------------------


class EvaluateOutputPayload(BaseModel):
    """Inbound payload for the ``evaluate_output`` A2A task."""

    goal_id: str
    action_id: str
    success: bool
    escalate: bool
    deviation_score: float
    reward_value: float
    channel: str | None = None
    error: str | None = None
    task_type: str = "default"
    retry_count: int = 0
    policy_denied: bool = False
    trace_id: str | None = None


# ---------------------------------------------------------------------------
# Output evaluation model (mirrors metacognitive-evaluation.schema.json)
# ---------------------------------------------------------------------------


class MetacognitiveEvaluation(BaseModel):
    """A single metacognitive evaluation event."""

    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    task_type: str
    task_confidence: float
    deviation_score: float
    deviation_zscore: float
    success_rate: float
    reward_delta: float
    escalation_rate: float = 0.0
    retry_count_mean: float = 0.0
    policy_denial_rate: float = 0.0
    error_detected: bool
    correction_triggered: bool = False
    alert_window_elapsed: bool = False
    trace_id: str | None = None
    source_feedback_ids: list[str] = Field(default_factory=list)
    session_id: str | None = None


# ---------------------------------------------------------------------------
# Per-task rolling window state
# ---------------------------------------------------------------------------


class _WindowState:
    """Rolling window statistics for a single task_type."""

    def __init__(self, maxlen: int) -> None:
        self.maxlen = maxlen
        self.reward_values: deque[float] = deque(maxlen=maxlen)
        self.success_flags: deque[bool] = deque(maxlen=maxlen)
        self.deviation_scores: deque[float] = deque(maxlen=maxlen)
        self.escalation_flags: deque[bool] = deque(maxlen=maxlen)
        self.retry_counts: deque[int] = deque(maxlen=maxlen)
        self.policy_denied_flags: deque[bool] = deque(maxlen=maxlen)
        self.action_ids: deque[str] = deque(maxlen=maxlen)
        # alert window: timestamp when confidence first dropped below threshold
        self.low_confidence_since: datetime | None = None

    def push(self, payload: EvaluateOutputPayload) -> None:
        self.reward_values.append(payload.reward_value)
        self.success_flags.append(payload.success)
        self.deviation_scores.append(payload.deviation_score)
        self.escalation_flags.append(payload.escalate)
        self.retry_counts.append(payload.retry_count)
        self.policy_denied_flags.append(payload.policy_denied)
        self.action_ids.append(payload.action_id)

    def mean_reward(self) -> float:
        if not self.reward_values:
            return 0.0
        return sum(self.reward_values) / len(self.reward_values)

    def success_rate(self) -> float:
        if not self.success_flags:
            return 1.0
        return sum(1 for f in self.success_flags if f) / len(self.success_flags)

    def mean_deviation(self) -> float:
        if not self.deviation_scores:
            return 0.0
        return sum(self.deviation_scores) / len(self.deviation_scores)

    def std_deviation(self) -> float:
        if len(self.deviation_scores) < 2:
            return 1.0  # avoid division by zero; treat as unit std
        mu = self.mean_deviation()
        variance = sum((x - mu) ** 2 for x in self.deviation_scores) / len(self.deviation_scores)
        return math.sqrt(variance) or 1.0  # guard zero std

    def escalation_rate(self) -> float:
        if not self.escalation_flags:
            return 0.0
        return sum(1 for f in self.escalation_flags if f) / len(self.escalation_flags)

    def mean_retry_count(self) -> float:
        if not self.retry_counts:
            return 0.0
        return sum(self.retry_counts) / len(self.retry_counts)

    def policy_denial_rate(self) -> float:
        if not self.policy_denied_flags:
            return 0.0
        return sum(1 for f in self.policy_denied_flags if f) / len(self.policy_denied_flags)


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------


class MetacognitionEvaluator:
    """Rolling window confidence computation and error detection.

    ACC-analogue error detection: fires ``error_detected`` when
    ``deviation_zscore > deviation_error_threshold``.

    BA10-analogue confidence estimation:
      ``task_confidence = 0.5 * clamp01((mean_reward + 1) / 2) + 0.5 * success_rate``

    Correction trigger: fires ``request_correction`` A2A task when
    ``task_confidence < confidence_threshold`` has been sustained for
    ``alert_window_minutes`` minutes.
    """

    def __init__(
        self,
        config: MonitoringConfig,
        metrics_bundle: MetricsBundle,
    ) -> None:
        self._config = config
        self._metrics = metrics_bundle
        self._windows: dict[str, _WindowState] = {}
        self._recent_evaluations: deque[MetacognitiveEvaluation] = deque(maxlen=100)
        # optional A2A client — set by server after startup
        self._a2a_client: Any | None = None

    def set_a2a_client(self, client: Any) -> None:  # noqa: ANN401
        """Inject an A2AClient for outbound request_correction calls."""
        self._a2a_client = client

    def _window(self, task_type: str) -> _WindowState:
        if task_type not in self._windows:
            self._windows[task_type] = _WindowState(self._config.rolling_window_size)
        return self._windows[task_type]

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _compute_confidence(self, window: _WindowState) -> float:
        """BA10: confidence = 0.5 * normalised_reward + 0.5 * success_rate."""
        normalised_reward = self._clamp01((window.mean_reward() + 1.0) / 2.0)
        return 0.5 * normalised_reward + 0.5 * window.success_rate()

    def _compute_zscore(self, window: _WindowState, current_deviation: float) -> float:
        """ACC: z-score of current deviation relative to rolling window."""
        mu = window.mean_deviation()
        sigma = window.std_deviation()
        return (current_deviation - mu) / sigma

    def _should_trigger_correction(self, task_type: str) -> bool:
        """Return True if low confidence has been sustained >= alert_window_minutes."""
        window = self._window(task_type)
        if window.low_confidence_since is None:
            return False
        elapsed = datetime.now(UTC) - window.low_confidence_since
        return elapsed >= timedelta(minutes=self._config.alert_window_minutes)

    async def evaluate(self, payload: EvaluateOutputPayload) -> MetacognitiveEvaluation:
        """Evaluate a single Phase 6 output event and update rolling state.

        Args:
            payload: Inbound evaluate_output A2A payload.

        Returns:
            MetacognitiveEvaluation with all computed fields.
        """
        window = self._window(payload.task_type)
        window.push(payload)

        task_confidence = self._compute_confidence(window)
        deviation_zscore = self._compute_zscore(window, payload.deviation_score)
        error_detected = deviation_zscore > self._config.deviation_error_threshold
        mean_dev = window.mean_deviation()
        success_rate = window.success_rate()
        mean_reward = window.mean_reward()
        esc_rate = window.escalation_rate()
        retry_mean = window.mean_retry_count()
        pd_rate = window.policy_denial_rate()

        # Alert window tracking
        now = datetime.now(UTC)
        if task_confidence < self._config.confidence_threshold:
            if window.low_confidence_since is None:
                window.low_confidence_since = now
        else:
            window.low_confidence_since = None

        alert_window_elapsed = self._should_trigger_correction(payload.task_type)

        # Correction trigger
        correction_triggered = False
        if (
            self._config.escalation_enabled
            and alert_window_elapsed
            and self._a2a_client is not None
        ):
            try:
                await self._a2a_client.send_task(
                    "request_correction",
                    {
                        "task_type": payload.task_type,
                        "task_confidence": task_confidence,
                        "deviation_zscore": deviation_zscore,
                        "goal_id": payload.goal_id,
                    },
                )
                correction_triggered = True
                logger.warning(
                    "request_correction sent",
                    task_type=payload.task_type,
                    task_confidence=task_confidence,
                )
                # Reset alert window after sending
                window.low_confidence_since = None
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to send request_correction", error=str(exc))

        evaluation = MetacognitiveEvaluation(
            task_type=payload.task_type,
            task_confidence=task_confidence,
            deviation_score=mean_dev,
            deviation_zscore=deviation_zscore,
            success_rate=success_rate,
            reward_delta=mean_reward,
            escalation_rate=esc_rate,
            retry_count_mean=retry_mean,
            policy_denial_rate=pd_rate,
            error_detected=error_detected,
            correction_triggered=correction_triggered,
            alert_window_elapsed=alert_window_elapsed,
            trace_id=payload.trace_id,
            source_feedback_ids=list(window.action_ids),
        )

        # Record OTel metrics
        labels = {"task_type": payload.task_type}
        self._metrics.task_confidence.set(task_confidence, labels)
        self._metrics.deviation_score.set(mean_dev, labels)
        self._metrics.reward_delta.record(mean_reward, labels)
        self._metrics.task_success_rate.set(success_rate, labels)
        self._metrics.deviation_zscore.set(deviation_zscore, labels)
        self._metrics.policy_denial_rate.set(pd_rate, labels)
        self._metrics.retry_count.record(float(payload.retry_count), labels)
        if payload.escalate:
            self._metrics.escalation_total.add(1, labels)

        self._recent_evaluations.append(evaluation)

        logger.info(
            "metacognition.evaluated",
            task_type=payload.task_type,
            task_confidence=round(task_confidence, 4),
            deviation_zscore=round(deviation_zscore, 4),
            error_detected=error_detected,
        )

        return evaluation

    def get_current_confidence(self) -> dict[str, float]:
        """Return current task_confidence per task_type."""
        return {
            task_type: self._compute_confidence(window)
            for task_type, window in self._windows.items()
        }

    def get_recent_anomalies(self, n: int = 10) -> list[MetacognitiveEvaluation]:
        """Return up to n most recent evaluations where error_detected=True."""
        anomalies = [e for e in self._recent_evaluations if e.error_detected]
        return list(anomalies)[-n:]

    def get_all_recent(self, n: int = 100) -> list[MetacognitiveEvaluation]:
        """Return up to n most-recent evaluations."""
        return list(self._recent_evaluations)[-n:]

    def get_confidence_threshold(self) -> float:
        """Return the current confidence threshold."""
        return self._config.confidence_threshold

    def set_confidence_threshold(self, value: float) -> None:
        """Update the confidence threshold."""
        self._config.confidence_threshold = value
