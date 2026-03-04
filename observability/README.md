# Observability Stack

Local observability stack for the brAIn framework, providing structured telemetry collection, metrics scraping, and
dashboarding.

## Components

| Service                     | Port                     | Purpose                                            |
| --------------------------- | ------------------------ | -------------------------------------------------- |
| **OpenTelemetry Collector** | 4317 (gRPC), 4318 (HTTP) | Receives OTLP traces/metrics/logs from all modules |
| **Prometheus**              | 9090                     | Scrapes and stores time-series metrics             |
| **Grafana**                 | 3000                     | Dashboard UI — default login: `admin` / `admin`    |
| **Blackbox Exporter**       | 9115                     | HTTP health probes for each module (Phase 8.4)     |
| **Grafana Tempo** _(opt.)_  | 3200                     | Distributed trace backend (`observability-full` profile, Phase 8.4) |

## Starting the Stack

```bash
docker compose up -d otel-collector prometheus grafana
```

Or start the full local development stack:

```bash
docker compose up -d
```

## Configuration Files

| File                                                       | Purpose                                                     |
| ---------------------------------------------------------- | ----------------------------------------------------------- |
| `otel-collector.yaml`                                      | OTel Collector pipeline: receivers → processors → exporters |
| `prometheus.yml`                                           | Prometheus scrape targets and global config                 |
| `prometheus-rules/gateway.yml`                             | Gateway + module-health alert rules (Phase 8.4)             |
| `grafana/datasources/default.yaml`                         | Grafana datasource provisioning (Prometheus UID: `prometheus`) |
| `grafana/provisioning/dashboards/phase-8.yaml`             | Grafana dashboard auto-provisioning config (Phase 8.4)      |
| `grafana/dashboards/gateway.json`                          | Gateway dashboard (request rate, latency, SSE, auth failures) |
| `grafana/dashboards/signal-flow.json`                      | Signal flow latency dashboard (Phase 8.4)                   |
| `grafana/dashboards/module-health.json`                    | Module health via Blackbox + metacognition metrics (Phase 8.4) |
| `blackbox.yml`                                             | Blackbox Exporter HTTP probe config (Phase 8.4)             |
| `tempo.yaml`                                               | Grafana Tempo config for `observability-full` profile (Phase 8.4) |

## Instrumenting a Module

All modules emit telemetry via the OpenTelemetry SDK and the shared utilities defined in `shared/utils/`:

- **Logs**: structured JSON, emitted via `structlog` (Python) or `pino` (TypeScript)
- **Traces**: W3C TraceContext propagated across all inter-module boundaries
- **Metrics**: counters, histograms, and gauges for signal throughput, latency, and collection sizes

See [`shared/utils/logging.md`](../shared/utils/logging.md), [`shared/utils/tracing.md`](../shared/utils/tracing.md),
and [`shared/utils/validation.md`](../shared/utils/validation.md) for specifications.

<!-- Phase 8 addition — 2026-03-04 -->
## Phase 8.4 — Gateway OTel Instrumentation

The Hono API gateway (`apps/default/server`) wires full OpenTelemetry instrumentation in Phase 8.4.

### NodeSDK initialisation (`src/telemetry.ts`)

```typescript
// src/telemetry.ts — imported as the FIRST import in src/index.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { W3CTraceContextPropagator } from '@opentelemetry/core';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318/v1/traces',
  }),
  textMapPropagator: new W3CTraceContextPropagator(),
  resource: { attributes: { 'service.name': 'hono-gateway', 'service.namespace': 'brain' } },
});
sdk.start();
```

`NodeSDK` must be imported **before** Hono and all application code to guarantee auto-instrumentation hooks fire.

### Manual Hono tracing middleware

A custom tracing middleware (`src/middleware/tracing.ts`) wraps every request:

1. Extracts the incoming `traceparent` header (W3C TraceContext)
2. Creates a child span per request with `http.method`, `http.route`, `http.status_code` attributes
3. Injects the active `traceId` into `MCPContext` envelopes forwarded by `mcp-client.ts`
4. Sets span status on response (OK / ERROR)

This propagates a single `traceId` from browser → gateway → MCP backbone → module, making traces visible in
Grafana Tempo and correlating with `structlog` records in Group I–IV Python modules.

### Structured logging with `pino`

Every gateway log record includes `trace_id` and `span_id` injected from the active OTel span:

```typescript
// src/logger.ts
import pino from 'pino';
import { trace } from '@opentelemetry/api';

export const logger = pino({
  mixin() {
    const span = trace.getActiveSpan();
    const ctx = span?.spanContext();
    return ctx
      ? { trace_id: ctx.traceId, span_id: ctx.spanId }
      : {};
  },
});
```

Metric naming: gateway metrics emitted via OTLP receive a `brain_` prefix from the OTel Collector Prometheus
exporter (`namespace: brain`). Prometheus metric names are therefore `brain_hono_gateway_*`.

## Phase 8.4 Dashboards (provisioned)

Dashboard JSON files in `grafana/dashboards/` are auto-provisioned into Grafana via
`grafana/provisioning/dashboards/phase-8.yaml` (mounted to `/etc/grafana/provisioning/dashboards`
in the `docker-compose.yml` Grafana service).

| File | UID | Panels |
| --- | --- | --- |
| `grafana/dashboards/gateway.json` | `brain-gateway` | Request rate, error rate, active SSE connections, P50/P95/P99 latency (`/api/input`), auth failure rate |
| `grafana/dashboards/signal-flow.json` | `brain-signal-flow` | Gateway→MCP P99 latency, end-to-end latency trend, per-module span histograms (requires spanmetrics connector in Phase 9) |
| `grafana/dashboards/module-health.json` | `brain-module-health` | Module health status (Blackbox), probe duration, metacognition confidence |

**Metric naming**: Gateway metrics emitted via OTLP receive a `brain_` prefix from the OTel Collector
Prometheus exporter (`namespace: brain`). Prometheus metric names are therefore `brain_hono_gateway_*`.

## Blackbox Exporter _(Phase 8.4)_

Prometheus [Blackbox Exporter](https://github.com/prometheus/blackbox_exporter) probes are added in Phase 8.4 to
provide reliable HTTP-level health checks per module. Each module's `/health` endpoint receives an `http_2xx` probe;
`probe_success = 1` is the health signal. Configuration added to `docker-compose.yml` and `prometheus.yml`.

## Distributed Traces — Grafana Tempo _(optional profile)_

[Grafana Tempo](https://grafana.com/oss/tempo/) is available as an optional `observability-full` Docker Compose
profile, added in Phase 8.4:

```bash
# Start full observability stack including Tempo
docker compose --profile observability-full up -d
```

Tempo provides distributed trace waterfall views (TraceQL). Without this profile, only latency histograms are
available (from OTel spans exported as Prometheus metrics). Configuration in `observability/tempo.yaml`.

The `observability-full` profile is non-blocking for Phase 8 Gate 5 — all gate criteria can be met with
Prometheus + Grafana alone.
