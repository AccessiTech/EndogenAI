---
id: guide-observability
version: 0.2.0
status: current
last-reviewed: 2026-03-04
---

# Observability

> **Status: current** — Full telemetry pipeline is operational as of Phase 8. Gateway OTel instrumentation, Prometheus
> Blackbox Exporter health probes, and Grafana dashboards (`gateway.json`, `signal-flow.json`, `module-health.json`)
> are provisioned and auto-imported into the local stack.

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

## Module OTel Instrumentation

Phase 7 introduces the first modules that own a `TracerProvider` + `MeterProvider` directly (rather than relying
solely on the Collector's filelog receiver). Two patterns are in use:

### Pattern 1 — FastAPI auto-instrumentation (HTTP tracing, zero new code)

Adds HTTP-level spans for every request to an existing FastAPI service. Applied to Phase 6 modules as Tier 1
observability when Phase 7 deploys:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)  # after app = FastAPI(...)
```

Dependency: `opentelemetry-instrumentation-fastapi>=0.50b0` in `pyproject.toml`.

### Pattern 2 — Domain metric `MeterProvider` (module-owned Prometheus metrics)

For modules that compute business-level metrics (not just HTTP traces). The `metacognition` module is the
reference implementation.

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

resource = Resource.create({SERVICE_NAME: "metacognition", "service.namespace": "brain"})
meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PrometheusMetricReader(port=9464)]
)
```

**Metric naming rule**: all metric names MUST be prefixed `brain_` (e.g. `brain_metacognition_task_confidence`)
to pass the `brain_.*` relabel filter in `prometheus.yml`. The sub-namespace convention is
`brain_<module-name>_<metric>`.

### Phase 7 metric namespace

Phase 7 provisioned the `brain_metacognition_*` metric namespace. The full set is live:

| Metric | Type | Description |
| --- | --- | --- |
| `brain_metacognition_task_confidence` | Gauge | Rolling task confidence per `goal_class` [0, 1] |
| `brain_metacognition_deviation_zscore` | Gauge | Deviation z-score vs rolling mean (>2 = anomaly) |
| `brain_metacognition_escalation_total` | Counter | Cumulative escalation events from `motor-output` |
| `brain_metacognition_reward_delta` | Histogram | Reward delta distribution per episode [−0.15, 0.15] |
| `brain_metacognition_policy_denial_rate` | Gauge | BDI policy denial rate (ACC conflict-monitoring analogue) |

Activated by setting `METACOGNITION_URL` on the `executive-agent` process (default `None` — Phase 6 runs
with no Phase 7 dependency). Phase 6 OTel Tier 1 (FastAPI auto-instrumentation) bootstraps additional HTTP
metrics on the existing `brain_.*` namespace.

---

## Phase 8 Additions

Phase 8.4 extended the observability stack with gateway-level telemetry, HTTP health probes, distributed trace
visualization, and three new Grafana dashboards.

### Gateway OTel Instrumentation

The Hono API gateway (`apps/default/server`) emits structured telemetry via
`apps/default/server/src/telemetry.ts` (bootstrapped as the first import in `src/index.ts`):

- **Traces** — `NodeSDK` with OTLP HTTP exporter; `traceparent` injected into every forwarded MCP context
  envelope; W3C TraceContext propagated end-to-end.
- **Logs** — `pino` structured JSON with `trace_id` and `span_id` injected into every log record.
- **Metrics** — custom Hono middleware emits Prometheus metrics under the `brain_hono_gateway_*` namespace.

#### `brain_hono_gateway_*` metric namespace

| Metric | Type | Description |
| --- | --- | --- |
| `brain_hono_gateway_requests_total` | Counter | Total HTTP requests by method, path, and status code |
| `brain_hono_gateway_request_duration_seconds` | Histogram | Request latency (P50 / P95 / P99 visible in Grafana) |
| `brain_hono_gateway_sse_connections_active` | Gauge | Currently open SSE stream connections |
| `brain_hono_gateway_auth_failures_total` | Counter | 401 responses by failure reason |

### Prometheus Blackbox Exporter

The [Blackbox Exporter](https://github.com/prometheus/blackbox_exporter) (port `9115`) performs HTTP
`http_2xx` probes against each module’s `/health` endpoint. `probe_success = 1` is the authoritative health
signal consumed by the `brain-module-health` Grafana dashboard.

Configuration files: `observability/blackbox.yml` (probe definitions), `observability/prometheus.yml`
(scrape targets), `observability/prometheus-rules/gateway.yml` (alert rules).

### Grafana Dashboards (auto-provisioned)

Dashboard JSON files in `observability/grafana/dashboards/` are auto-imported via
`observability/grafana/provisioning/dashboards/phase-8.yaml`:

| File | UID | Key panels |
| --- | --- | --- |
| `gateway.json` | `brain-gateway` | Request rate, error rate, active SSE connections, P50/P95/P99 latency, auth failure rate |
| `signal-flow.json` | `brain-signal-flow` | Gateway→MCP P99 latency, end-to-end latency trend, per-module span histograms |
| `module-health.json` | `brain-module-health` | Blackbox probe status per module, probe duration, metacognition confidence |

See [Observability Stack Config](../../observability/README.md) for the full port reference and Phase 8.4
detail.

### Grafana Tempo (optional profile)

[Grafana Tempo](https://grafana.com/oss/tempo/) is available under the `observability-full` Docker Compose
profile for distributed trace waterfall views (TraceQL). Without this profile, only histogram-derived latency
quantiles are available.

```bash
docker compose --profile observability-full up -d
```

Configurations: `observability/tempo.yaml`. The Grafana Tempo datasource is pre-provisioned at port `3200`.

---

## Dashboards

Grafana dashboards are provisioned and auto-imported into the local stack as of Phase 8.4. The
`brain_metacognition_*` and `brain_hono_gateway_*` metric namespaces are both live. See
[Phase 8 Additions](#phase-8-additions) above for the full dashboard inventory.

**Coverage**: signal flow latency (gateway → MCP), per-module health (Blackbox probes), reward signal
distribution (metacognition), and gateway request / error / SSE / auth metrics.

---

## References

- [Logging Spec](../../shared/utils/logging.md)
- [Tracing Spec](../../shared/utils/tracing.md)
- [Observability Stack Config](../../observability/README.md)
- [Workplan — Phase 7](../Workplan.md#phase-7--group-iv-adaptive-systems-cross-cutting)
