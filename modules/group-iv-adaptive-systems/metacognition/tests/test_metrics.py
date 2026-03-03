"""test_metrics.py — Unit tests for OTel metric instruments.

Tests:
  - All 8 OTel metric instruments created without error
  - Gauge/counter/histogram record without raising exceptions
  - MetricsBundle has all expected attribute names
"""

from __future__ import annotations

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

from metacognition.instrumentation.metrics import MetricsBundle, create_metrics

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def meter() -> metrics.Meter:
    """Return a fresh in-memory MeterProvider + Meter for testing."""
    provider = MeterProvider()
    metrics.set_meter_provider(provider)
    return metrics.get_meter("test.metacognition")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_metrics_returns_metrics_bundle(meter: metrics.Meter) -> None:
    """create_metrics() returns a MetricsBundle instance."""
    bundle = create_metrics(meter)
    assert isinstance(bundle, MetricsBundle)


def test_metrics_bundle_has_all_expected_attributes(meter: metrics.Meter) -> None:
    """MetricsBundle exposes all 8 expected instrument attributes."""
    bundle = create_metrics(meter)
    expected_attrs = [
        "task_confidence",
        "deviation_score",
        "reward_delta",
        "task_success_rate",
        "escalation_total",
        "retry_count",
        "policy_denial_rate",
        "deviation_zscore",
    ]
    for attr in expected_attrs:
        assert hasattr(bundle, attr), f"MetricsBundle missing attribute: {attr}"


def test_gauge_records_without_error(meter: metrics.Meter) -> None:
    """Gauge instruments accept set() calls without raising."""
    bundle = create_metrics(meter)
    labels = {"task_type": "test"}
    # Should not raise
    bundle.task_confidence.set(0.85, labels)
    bundle.deviation_score.set(0.3, labels)
    bundle.task_success_rate.set(0.9, labels)
    bundle.deviation_zscore.set(1.2, labels)
    bundle.policy_denial_rate.set(0.05, labels)


def test_counter_increments_without_error(meter: metrics.Meter) -> None:
    """Counter instrument accepts add() calls without raising."""
    bundle = create_metrics(meter)
    labels = {"task_type": "test"}
    bundle.escalation_total.add(1, labels)
    bundle.escalation_total.add(3, labels)


def test_histogram_records_without_error(meter: metrics.Meter) -> None:
    """Histogram instruments accept record() calls without raising."""
    bundle = create_metrics(meter)
    labels = {"task_type": "test"}
    bundle.reward_delta.record(0.5, labels)
    bundle.reward_delta.record(-0.2, labels)
    bundle.retry_count.record(2.0, labels)
    bundle.retry_count.record(0.0, labels)


def test_multiple_bundles_from_same_meter_do_not_raise(meter: metrics.Meter) -> None:
    """Creating a MetricsBundle twice with the same meter does not raise."""
    bundle1 = create_metrics(meter)
    bundle2 = create_metrics(meter)
    assert bundle1 is not bundle2  # distinct objects
    # Both should be usable
    bundle1.task_confidence.set(0.5, {"task_type": "a"})
    bundle2.task_confidence.set(0.7, {"task_type": "b"})
