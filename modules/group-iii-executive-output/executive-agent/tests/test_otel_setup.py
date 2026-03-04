"""test_otel_setup.py — Unit tests for executive-agent OTel configuration.

Tests:
  - configure_telemetry() succeeds without a live OTel collector
  - Idempotency: second call is a no-op (no duplicate providers)
  - reset_telemetry() resets the configured flag
  - _add_otel_trace_context() passes through event_dict when no active span
  - _add_otel_trace_context() injects trace_id/span_id when span is recording
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import executive_agent.instrumentation.otel_setup as _otel


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
    _otel.configure_telemetry(otlp_endpoint="http://localhost:14317")


def test_configure_telemetry_sets_flag() -> None:
    _otel.configure_telemetry()
    assert _otel._telemetry_configured is True


def test_configure_telemetry_idempotent() -> None:
    """Second call must be a no-op — _telemetry_configured prevents re-init."""
    _otel.configure_telemetry()
    with patch("opentelemetry.trace.set_tracer_provider") as mock_set:
        _otel.configure_telemetry()
    mock_set.assert_not_called()


def test_configure_telemetry_custom_service_name() -> None:
    """Service name and namespace are accepted without error."""
    _otel.configure_telemetry(
        service_name="custom-agent",
        service_namespace="custom-ns",
    )
    assert _otel._telemetry_configured is True


# ---------------------------------------------------------------------------
# reset_telemetry
# ---------------------------------------------------------------------------


def test_reset_telemetry_clears_flag() -> None:
    _otel.configure_telemetry()
    _otel.reset_telemetry()
    assert _otel._telemetry_configured is False


def test_reset_then_configure_again() -> None:
    _otel.configure_telemetry()
    _otel.reset_telemetry()
    _otel.configure_telemetry()
    assert _otel._telemetry_configured is True


# ---------------------------------------------------------------------------
# _add_otel_trace_context
# ---------------------------------------------------------------------------


def test_add_otel_trace_context_no_active_span() -> None:
    event_dict: dict = {"event": "test_event"}
    result = _otel._add_otel_trace_context(None, "info", event_dict)
    assert result["event"] == "test_event"
    assert "trace_id" not in result
    assert "span_id" not in result


def test_add_otel_trace_context_with_active_span() -> None:
    mock_ctx = MagicMock()
    mock_ctx.trace_id = 0xDEADBEEF0123456789ABCDEF01234567
    mock_ctx.span_id = 0xFEEDFACEDEADBEEF

    mock_span = MagicMock()
    mock_span.is_recording.return_value = True
    mock_span.get_span_context.return_value = mock_ctx

    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        event_dict: dict = {"event": "traced_event"}
        result = _otel._add_otel_trace_context(None, "info", event_dict)

    assert "trace_id" in result
    assert "span_id" in result
    assert len(result["trace_id"]) == 32
    assert len(result["span_id"]) == 16


def test_add_otel_trace_context_suppresses_errors() -> None:
    with patch("opentelemetry.trace.get_current_span", side_effect=RuntimeError("boom")):
        event_dict: dict = {"event": "safe"}
        result = _otel._add_otel_trace_context(None, "info", event_dict)
    assert result["event"] == "safe"
