"""otel_setup.py — OpenTelemetry TracerProvider configuration for executive-agent.

Configures:
  - TracerProvider with OTLP gRPC span exporter → OTel Collector
  - structlog processor to inject trace_id / span_id into every log record

Usage (in server.py lifespan)::

    from executive_agent.instrumentation.otel_setup import configure_telemetry
    configure_telemetry(otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))

Note: opentelemetry-sdk and opentelemetry-exporter-otlp-proto-grpc are required.
They are currently provided as transitive dependencies; add explicit deps in Phase 9
(see docs/research/phase-8c-detailed-workplan.md §7.2).
"""
from __future__ import annotations

import logging

import structlog

logger = logging.getLogger(__name__)

_telemetry_configured = False


def _add_otel_trace_context(
    logger_obj: object, method_name: str, event_dict: dict
) -> dict:
    """structlog processor: inject OTel trace_id and span_id into log records."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except Exception:  # noqa: BLE001
        pass
    return event_dict


def configure_telemetry(
    otlp_endpoint: str = "http://localhost:4317",
    service_name: str = "executive-agent",
    service_namespace: str = "brain",
) -> None:
    """Configure OTel TracerProvider and wire trace_id into structlog.

    Idempotent — safe to call multiple times; subsequent calls are no-ops.

    Args:
        otlp_endpoint: OTLP gRPC collector endpoint (default: localhost:4317).
        service_name: OTel resource service.name attribute.
        service_namespace: OTel resource service.namespace attribute.
    """
    global _telemetry_configured
    if _telemetry_configured:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": service_namespace,
            }
        )
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )
        trace.set_tracer_provider(tracer_provider)
        logger.info("OTel TracerProvider configured for %s", service_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OTel setup failed (non-fatal): %s", exc)

    # Configure structlog to inject trace_id into every log record
    structlog.configure(
        processors=[
            _add_otel_trace_context,
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _telemetry_configured = True


def reset_telemetry() -> None:
    """Reset telemetry state — for testing only."""
    global _telemetry_configured
    _telemetry_configured = False
