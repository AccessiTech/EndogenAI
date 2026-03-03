"""test_evaluator.py — Unit tests for MetacognitionEvaluator.

Tests:
  - evaluate() with mock payload: correct z-score computation
  - Confidence falls with failure sequence (5 failures)
  - error_detected set when zscore > threshold
  - task_confidence rises with success sequence (5 successes)
  - _should_trigger_correction() returns False initially, True after window elapsed
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from metacognition.evaluation.evaluator import (
    EvaluateOutputPayload,
    MetacognitionEvaluator,
    MonitoringConfig,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_metrics_bundle() -> Any:
    """Return a mock MetricsBundle where all instruments are MagicMocks."""
    bundle = MagicMock()
    bundle.task_confidence = MagicMock()
    bundle.deviation_score = MagicMock()
    bundle.reward_delta = MagicMock()
    bundle.task_success_rate = MagicMock()
    bundle.escalation_total = MagicMock()
    bundle.retry_count = MagicMock()
    bundle.policy_denial_rate = MagicMock()
    bundle.deviation_zscore = MagicMock()
    return bundle


def make_payload(
    success: bool = True,
    escalate: bool = False,
    deviation_score: float = 0.2,
    reward_value: float = 0.8,
    task_type: str = "default",
    retry_count: int = 0,
    policy_denied: bool = False,
) -> EvaluateOutputPayload:
    return EvaluateOutputPayload(
        goal_id="goal-001",
        action_id="action-001",
        success=success,
        escalate=escalate,
        deviation_score=deviation_score,
        reward_value=reward_value,
        task_type=task_type,
        retry_count=retry_count,
        policy_denied=policy_denied,
    )


def make_evaluator(
    confidence_threshold: float = 0.7,
    deviation_error_threshold: float = 0.75,
    alert_window_minutes: int = 5,
    rolling_window_size: int = 20,
) -> MetacognitionEvaluator:
    config = MonitoringConfig(
        confidence_threshold=confidence_threshold,
        deviation_error_threshold=deviation_error_threshold,
        alert_window_minutes=alert_window_minutes,
        rolling_window_size=rolling_window_size,
        escalation_enabled=False,  # disable A2A calls in unit tests
    )
    bundle = make_metrics_bundle()
    return MetacognitionEvaluator(config=config, metrics_bundle=bundle)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_basic_payload_produces_evaluation() -> None:
    """evaluate() returns a MetacognitiveEvaluation with expected fields."""
    evaluator = make_evaluator()
    payload = make_payload(success=True, deviation_score=0.3, reward_value=0.9)
    result = await evaluator.evaluate(payload)

    assert result.task_type == "default"
    assert 0.0 <= result.task_confidence <= 1.0
    assert isinstance(result.error_detected, bool)
    assert result.evaluation_id != ""


@pytest.mark.asyncio
async def test_zscore_single_observation_uses_unit_std() -> None:
    """With one observation, std=1.0 (guard), so zscore = (dev - dev) / 1 = 0."""
    evaluator = make_evaluator()
    payload = make_payload(deviation_score=0.5)
    result = await evaluator.evaluate(payload)
    # With one sample, mu=0.5, sigma=1.0 (guard), zscore should be 0.0
    assert result.deviation_zscore == pytest.approx(0.0, abs=1e-6)


@pytest.mark.asyncio
async def test_zscore_computation_with_multiple_observations() -> None:
    """Z-score is computed correctly as (current - mu) / sigma."""
    evaluator = make_evaluator()
    # Push 4 identical low-deviation scores
    for _ in range(4):
        await evaluator.evaluate(make_payload(deviation_score=0.2))
    # Now push a high-deviation score
    result = await evaluator.evaluate(make_payload(deviation_score=0.8))
    # The high deviation should produce a positive z-score
    assert result.deviation_zscore > 0.0


@pytest.mark.asyncio
async def test_confidence_falls_with_failure_sequence() -> None:
    """Confidence decreases after a sequence of 5 failures."""
    evaluator = make_evaluator()
    # Establish a baseline with a few successes
    await evaluator.evaluate(make_payload(success=True, reward_value=1.0))
    baseline = evaluator.get_current_confidence()["default"]

    # Now inject 5 failures with negative reward
    for _ in range(5):
        await evaluator.evaluate(make_payload(success=False, reward_value=-1.0))

    after_failures = evaluator.get_current_confidence()["default"]
    assert after_failures < baseline


@pytest.mark.asyncio
async def test_confidence_rises_with_success_sequence() -> None:
    """Confidence increases after a sequence of 5 successes."""
    evaluator = make_evaluator()
    # Establish low baseline with failures
    for _ in range(5):
        await evaluator.evaluate(make_payload(success=False, reward_value=-1.0))
    baseline = evaluator.get_current_confidence()["default"]

    # Now inject 5 successes with high reward
    for _ in range(5):
        await evaluator.evaluate(make_payload(success=True, reward_value=1.0))

    after_successes = evaluator.get_current_confidence()["default"]
    assert after_successes > baseline


@pytest.mark.asyncio
async def test_error_detected_set_when_zscore_exceeds_threshold() -> None:
    """error_detected=True when deviation_zscore > deviation_error_threshold."""
    evaluator = make_evaluator(deviation_error_threshold=0.5)
    # Seed the window with low deviations to establish low mu/sigma
    for _ in range(10):
        await evaluator.evaluate(make_payload(deviation_score=0.1))
    # Now inject a high deviation that should exceed threshold z-score
    result = await evaluator.evaluate(make_payload(deviation_score=0.95))
    assert result.error_detected is True


@pytest.mark.asyncio
async def test_error_not_detected_when_zscore_below_threshold() -> None:
    """error_detected=False when deviation_zscore <= deviation_error_threshold."""
    evaluator = make_evaluator(deviation_error_threshold=5.0)  # very high threshold
    for _ in range(5):
        await evaluator.evaluate(make_payload(deviation_score=0.2))
    result = await evaluator.evaluate(make_payload(deviation_score=0.3))
    assert result.error_detected is False


def test_should_trigger_correction_false_initially() -> None:
    """_should_trigger_correction() returns False before any low-confidence event."""
    evaluator = make_evaluator()
    assert evaluator._should_trigger_correction("default") is False  # noqa: SLF001


def test_should_trigger_correction_false_before_window() -> None:
    """_should_trigger_correction() returns False if window hasn't elapsed."""
    evaluator = make_evaluator(alert_window_minutes=5)
    window = evaluator._window("default")  # noqa: SLF001
    # Simulate low confidence since 1 minute ago
    window.low_confidence_since = datetime.now(UTC) - timedelta(minutes=1)
    assert evaluator._should_trigger_correction("default") is False  # noqa: SLF001


def test_should_trigger_correction_true_after_window() -> None:
    """_should_trigger_correction() returns True once alert_window has elapsed."""
    evaluator = make_evaluator(alert_window_minutes=5)
    window = evaluator._window("default")  # noqa: SLF001
    # Simulate low confidence since 6 minutes ago
    window.low_confidence_since = datetime.now(UTC) - timedelta(minutes=6)
    assert evaluator._should_trigger_correction("default") is True  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_recent_anomalies_returns_only_error_detected() -> None:
    """get_recent_anomalies() returns only evaluations with error_detected=True."""
    evaluator = make_evaluator(deviation_error_threshold=0.5)
    # Seed low deviations
    for _ in range(10):
        await evaluator.evaluate(make_payload(deviation_score=0.1))
    # Inject anomaly
    await evaluator.evaluate(make_payload(deviation_score=0.99))

    anomalies = evaluator.get_recent_anomalies()
    assert all(a.error_detected for a in anomalies)


@pytest.mark.asyncio
async def test_get_current_confidence_returns_per_task_type() -> None:
    """get_current_confidence() returns a dict keyed by task_type."""
    evaluator = make_evaluator()
    await evaluator.evaluate(make_payload(task_type="navigation"))
    await evaluator.evaluate(make_payload(task_type="planning"))

    confidence = evaluator.get_current_confidence()
    assert "navigation" in confidence
    assert "planning" in confidence
