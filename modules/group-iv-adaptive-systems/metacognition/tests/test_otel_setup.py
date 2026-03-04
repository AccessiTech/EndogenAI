"""test_otel_setup.py — Unit tests for metacognition OTel configuration.

Tests:
  - configure_telemetry() succeeds without a live OTel collector or Prometheus
  - Returns (Tracer, Meter) tuple
  - Idempotency: second call returns the same tracer/meter without re-registering
  - reset_telemetry() resets the configured flag
  - Prometheus port-in-use OSError is suppressed (not fatal)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from opentelemetry import metrics, trace

import metacognition.instrumentation.otel_setup as _otel


@pytest.fixture(autouse=True)
def _reset_otel_state() -> None:
    """Always reset the telemetry flag before and after each test."""
    _otel.reset_telemetry()
    yield
    _otel.reset_telemetry()


# ---------------------------------------------------------------------------
# configure_telemetry
# ---------------------------------------------------------------------------


def test_configure_telemetry_does_not_raise() -> None:
    """configure_telemetry() must not raise even without a real OTel collector."""
    with patch("prometheus_client.start_http_server", side_effect=OSError("port in use")):
        tracer, meter = _otel.configure_telemetry(
            otlp_endpoint="http://localhost:14317",
            prometheus_port=0,
        )

    assert tracer is not None
    assert meter is not None


def test_configure_telemetry_sets_flag() -> None:
    with patch("prometheus_client.start_http_server"):
        _otel.configure_telemetry(prometheus_port=0)
    assert _otel._telemetry_configured is True


def test_configure_telemetry_returns_tracer_and_meter() -> None:
    with patch("prometheus_client.start_http_server"):
        result = _otel.configure_telemetry(prometheus_port=0)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_configure_telemetry_idempotent() -> None:
    """Second call must not re-configure providers."""
    with patch("prometheus_client.start_http_server"):
        _otel.configure_telemetry(prometheus_port=0)

    with patch("opentelemetry.trace.set_tracer_provider") as mock_trace_set, \
         patch("opentelemetry.metrics.set_meter_provider") as mock_metrics_set:
        _otel.configure_telemetry(prometheus_port=0)

    mock_trace_set.assert_not_called()
    mock_metrics_set.assert_not_called()


def test_prometheus_port_in_use_is_non_fatal() -> None:
    """An OSError from Prometheus start_http_server must not propagate."""
    with patch("prometheus_client.start_http_server", side_effect=OSError("Address already in use")):
        # Should not raise
        _otel.configure_telemetry(prometheus_port=9999)
    assert _otel._telemetry_configured is True


def test_configure_telemetry_custom_service() -> None:
    with patch("prometheus_client.start_http_server"):
        _otel.configure_telemetry(
            service_name="my-service",
            service_namespace="my-ns",
            prometheus_port=0,
        )
    assert _otel._telemetry_configured is True


# ---------------------------------------------------------------------------
# reset_telemetry
# ---------------------------------------------------------------------------


def test_reset_telemetry_clears_flag() -> None:
    with patch("prometheus_client.start_http_server"):
        _otel.configure_telemetry(prometheus_port=0)
    assert _otel._telemetry_configured is True
    _otel.reset_telemetry()
    assert _otel._telemetry_configured is False


def test_reset_then_configure_again() -> None:
    with patch("prometheus_client.start_http_server"):
        _otel.configure_telemetry(prometheus_port=0)
    _otel.reset_telemetry()
    with patch("prometheus_client.start_http_server"):
        _otel.configure_telemetry(prometheus_port=0)
    assert _otel._telemetry_configured is True
