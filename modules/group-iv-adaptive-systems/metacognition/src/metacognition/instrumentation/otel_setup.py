"""otel_setup.py — OpenTelemetry TracerProvider + MeterProvider configuration.

Configures:
  - TracerProvider with OTLP gRPC span exporter
  - MeterProvider with OTLP metric exporter + Prometheus reader
  - Resource: service.name=metacognition, service.namespace=brain

Usage::

    tracer, meter = configure_telemetry(
        otlp_endpoint="http://localhost:4317",
        prometheus_port=9464,
    )
"""

from __future__ import annotations

import logging

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

_telemetry_configured = False


def configure_telemetry(
    otlp_endpoint: str = "http://localhost:4317",
    prometheus_port: int = 9464,
    service_name: str = "metacognition",
    service_namespace: str = "brain",
) -> tuple[trace.Tracer, metrics.Meter]:
    """Configure OTel TracerProvider and MeterProvider.

    Idempotent — safe to call multiple times; subsequent calls return the
    already-configured tracer/meter without re-registering exporters.

    Args:
        otlp_endpoint: OTLP gRPC collector endpoint.
        prometheus_port: Port on which the Prometheus HTTP scrape endpoint listens.
        service_name: OTel resource service.name attribute.
        service_namespace: OTel resource service.namespace attribute.

    Returns:
        Tuple of (Tracer, Meter) bound to the configured providers.
    """
    global _telemetry_configured

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": service_namespace,
        }
    )

    if not _telemetry_configured:
        # --- Tracing ---
        otlp_span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_span_exporter))
        trace.set_tracer_provider(tracer_provider)

        # --- Metrics: OTLP periodic export ---
        otlp_metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        otlp_reader = PeriodicExportingMetricReader(
            otlp_metric_exporter, export_interval_millis=15_000
        )

        # --- Metrics: Prometheus scrape endpoint ---
        prometheus_reader = PrometheusMetricReader()

        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[otlp_reader, prometheus_reader],
        )
        metrics.set_meter_provider(meter_provider)

        # Start prometheus HTTP server for direct scraping
        try:
            from prometheus_client import start_http_server

            start_http_server(prometheus_port)
            logger.info("Prometheus metrics server started on port %d", prometheus_port)
        except OSError as exc:
            # Port already in use (e.g. during tests) — log and continue
            logger.warning("Could not start Prometheus HTTP server: %s", exc)

        _telemetry_configured = True
        logger.info(
            "OTel configured",
            extra={
                "otlp_endpoint": otlp_endpoint,
                "prometheus_port": prometheus_port,
                "service": f"{service_namespace}/{service_name}",
            },
        )

    tracer = trace.get_tracer(service_name)
    meter = metrics.get_meter(service_name)
    return tracer, meter


def reset_telemetry() -> None:
    """Reset telemetry state — for testing only."""
    global _telemetry_configured
    _telemetry_configured = False
