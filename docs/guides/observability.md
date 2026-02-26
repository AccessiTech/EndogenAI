---
id: guide-observability
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Observability

> **Status: draft** — Logging and tracing specs are defined (Phase 1). Grafana dashboards, per-module metrics, and the
> full telemetry pipeline will be documented in Phase 7.

Telemetry setup, distributed tracing, and Grafana dashboard usage for the EndogenAI framework.

## Overview

The observability stack consists of:

- **OpenTelemetry Collector** — receives traces, metrics, and logs from all modules
- **Prometheus** — time-series metrics storage and alerting
- **Grafana** — dashboards for module health, signal flow latency, and memory collection sizes

## Local Stack

The observability stack is included in `docker-compose.yml` and starts automatically with `docker compose up -d`.

| Service    | URL                                            | Default credentials |
| ---------- | ---------------------------------------------- | ------------------- |
| Grafana    | [http://localhost:3000](http://localhost:3000) | admin / admin       |
| Prometheus | [http://localhost:9090](http://localhost:9090) | —                   |
| OTLP gRPC  | `localhost:4317`                               | —                   |
| OTLP HTTP  | `localhost:4318`                               | —                   |

See [Observability Stack Config](../../observability/README.md) for service details and port reference.

---

## Structured Logging

Full spec: [`shared/utils/logging.md`](../../shared/utils/logging.md).

Every module MUST emit newline-delimited JSON logs to `stdout`. The OTel Collector filelog receiver ingests them.

### Quick reference — required fields

| Field       | Example                                                     |
| ----------- | ----------------------------------------------------------- |
| `timestamp` | `"2026-02-26T12:34:56.789Z"`                                |
| `level`     | `"INFO"` (uppercase)                                        |
| `message`   | `"Signal ingested"` (static string, no interpolated values) |
| `service`   | `"sensory-input"` (canonical module ID)                     |
| `version`   | `"0.1.0"`                                                   |

When a trace is in scope, also include `traceId`, `spanId`, and `traceFlags`.

### Library recommendations

| Language   | Library                                                      |
| ---------- | ------------------------------------------------------------ |
| Python     | [`structlog`](https://www.structlog.org/) with JSON renderer |
| TypeScript | [`pino`](https://getpino.io/) (default JSON output)          |

---

## Distributed Tracing

Full spec: [`shared/utils/tracing.md`](../../shared/utils/tracing.md).

EndogenAI uses **W3C Trace Context** (traceparent / tracestate). All modules MUST propagate trace context without
modification.

### Trace lifecycle summary

1. The **Sensory / Input Layer** (or Application Layer) establishes a new trace on first signal ingestion: generates a
   128-bit `traceId` and 64-bit `parentId`, attaches them to `Signal.traceContext` and `MCPContext.traceContext`.
2. Each downstream module extracts `traceparent`, creates a child span, and injects the updated `traceparent` into every
   outbound message.
3. The library call (OTel SDK) handles span creation, context injection, and export to the Collector automatically.

### Library recommendations

| Language   | Library                                                                                     |
| ---------- | ------------------------------------------------------------------------------------------- |
| Python     | [`opentelemetry-sdk`](https://opentelemetry-python.readthedocs.io/)                         |
| TypeScript | [`@opentelemetry/api`](https://opentelemetry.io/docs/languages/js/) + `@opentelemetry/core` |

### Sampling defaults

| Environment | Rate | Env var                         |
| ----------- | ---- | ------------------------------- |
| Development | 100% | `OTEL_TRACES_SAMPLER=always_on` |
| Production  | 10%  | `OTEL_TRACES_SAMPLER_ARG=0.1`   |

---

## Dashboards

_Grafana dashboards for signal flow latency, memory collection sizes, reward signal frequency, and module error rates
will be provisioned in Phase 7._

---

## References

- [Logging Spec](../../shared/utils/logging.md)
- [Tracing Spec](../../shared/utils/tracing.md)
- [Observability Stack Config](../../observability/README.md)
- [Workplan — Phase 7](../Workplan.md#phase-7--application-layer--observability)
