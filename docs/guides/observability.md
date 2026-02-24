---
id: guide-observability
version: 0.1.0
status: stub
last-reviewed: 2026-02-24
---

# Observability

> **Status: stub** — This document will be expanded during Phase 7 (Observability).

Telemetry setup, distributed tracing, and Grafana dashboard usage for the EndogenAI framework.

## Overview

The observability stack consists of:
- **OpenTelemetry Collector** — receives traces, metrics, and logs from all modules
- **Prometheus** — time-series metrics storage and alerting
- **Grafana** — dashboards for module health, signal flow latency, and memory collection sizes

## Local Stack

The observability stack is included in `docker-compose.yml` and starts automatically with `docker compose up -d`.

- **Grafana**: [http://localhost:3000](http://localhost:3000) (admin / admin)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **OTLP gRPC endpoint**: `localhost:4317`
- **OTLP HTTP endpoint**: `localhost:4318`

## Structured Logging

_Structured log format specification: [`shared/utils/logging.md`](../../shared/utils/logging.md) (Phase 1)._

## Distributed Tracing

_Trace context propagation spec: [`shared/utils/tracing.md`](../../shared/utils/tracing.md) (Phase 1)._

## Dashboards

_Grafana dashboards to be provisioned in Phase 7._

## References

- [Workplan — Phase 7](../Workplan.md#phase-7--application-layer--observability)
- [Observability Stack Config](../../observability/README.md)
