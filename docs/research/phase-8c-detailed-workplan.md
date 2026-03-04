# Phase 8C — Detailed Workplan: Observability

> **Status**: ⬜ NOT STARTED — Can begin in parallel with Phase 8B once Phase 8 Gate 2 is cleared.
> **Scope**: §8.4 Observability — OTel instrumentation, Prometheus metrics, Grafana dashboards, structured logging
> **Milestone**: Phase 8 Gate 5 (OTel spans flowing; dashboards rendering; Prometheus scraping)
> **Prerequisite**: Phase 8 Gate 2 (Hono gateway operational); `traceparent` schema change landed
> **Research references**:
> - [phase-8-neuroscience-interface-layer.md](phase-8-neuroscience-interface-layer.md) (D1) — §iv
> - [phase-8-technologies-interface-layer.md](phase-8-technologies-interface-layer.md) (D2) — §iv
> - [phase-8-synthesis-workplan.md](phase-8-synthesis-workplan.md) (D3) — §iv
> - [phase-8-overview.md](phase-8-overview.md) (D7) — Gates, Docker Compose changes, schema pre-landing

---

## Contents

1. [Design Discussion — Frontend Observability Features](#1-design-discussion--frontend-observability-features)
2. [Pre-Implementation Checklist](#2-pre-implementation-checklist)
3. [Build Sequence and Gate Definitions](#3-build-sequence-and-gate-definitions)
4. [OTel Gateway Instrumentation](#4-otel-gateway-instrumentation)
5. [Structured Logging (gateway)](#5-structured-logging-gateway)
6. [TraceContext Propagation into MCPContext](#6-tracecontext-propagation-into-mcpcontext)
7. [Cross-Module Audit — Python Modules (Groups I–IV)](#7-cross-module-audit--python-modules-groups-iiv)
8. [Grafana Dashboard Specifications](#8-grafana-dashboard-specifications)
9. [Prometheus Alert Rules (Phase 8 Additions)](#9-prometheus-alert-rules-phase-8-additions)
10. [Distributed Trace Backend (Tempo)](#10-distributed-trace-backend-tempo)
11. [Phase 8C Completion Gate (Gate 5)](#11-phase-8c-completion-gate-gate-5)
12. [Decisions Recorded](#12-decisions-recorded)

---

## 1. Design Discussion — Frontend Observability Features

> **Purpose**: Before implementing dashboards and panels, this section establishes what observability data the Internals tab (Phase 8B) should surface, and what backend infrastructure is required to support it. The Phase Executive must review and sign off on the decisions marked **[DECISION REQUIRED]** before §§4–10 work begins.

### 1.1 Biological Framing (from D1 §iv)

The observability layer is the brain's interoceptive system — the insular cortex and vagus nerve composite that continuously monitors internal body state without interrupting conscious action. The analogy is precise:

- **OTel Collector** = vagus nerve afferents — the raw signal pipeline from every organ (module) to the integrating cortex
- **Prometheus** = posterior insula — raw, undifferentiated metric values accumulated over time
- **Grafana dashboards** = anterior insula — the processed, experienced map of internal state; where raw signals become actionable readouts
- **Alerting rules** = anterior cingulate cortex (ACC) interoceptive prediction error — fires when the expected internal state diverges from the measured state

The critical insight from D1 §iv is that **self-monitoring is not a luxury feature** — interoceptive dysfunction (anosognosia) is among the most debilitating neurological conditions. An AI system that cannot observe its own internal state cannot self-regulate. Phase 8.4 is therefore not auxiliary to Phase 8; it is architecturally foundational.

### 1.2 What Goes in the Grafana Dashboards vs the Internals Tab

These are two different surfaces with different purposes:

| Surface | Primary user | Data type | Refresh |
|---|---|---|---|
| **Grafana dashboards** | Developer / operator | Time-series metrics, aggregates, rates | Seconds–minutes |
| **Internals tab panels** | End-user / power user | Current state snapshots, live event feeds | Real-time via SSE |

The Internals tab (Phase 8B) surfaces *current state* via MCP resource reads/subscriptions. The Grafana dashboards surface *historical trends and aggregated rates*. They are complementary, not duplicates.

**Grafana-only** (not in Internals tab):
- Request rate / error rate over time (time-series)
- P99 latency histograms
- Prometheus alert state
- Distributed trace waterfall (if Tempo enabled)

**Internals-tab-only** (via MCP resources — not in Grafana):
- Current context window content (Working Memory Inspector)
- Agent card browser (static configuration data)
- Confidence score snapshot (most recent value, not trend)

**Both surfaces** (Grafana = trend, Internals = current):
- Active SSE connection count (Grafana: gauge over time; Internals: current count on StatusBar)
- Module health status (Grafana: history; Internals: Agent Card health field)

### 1.3 Grafana Dashboard Scope

**D6-A — RESOLVED ✅**: **All 5 gateway dashboard panels confirmed** (resolved 2026-03-03). The following panels are in scope for `observability/grafana/dashboards/gateway.json`:

| Panel | Metric | Type |
|---|---|---|
| Request rate | `rate(hono_gateway_requests_total[5m])` | Graph |
| Error rate | `rate(hono_gateway_requests_total{status=~"5.."}[5m])` | Graph |
| Active SSE connections | `hono_gateway_sse_active_connections` | Gauge |
| P50/P95/P99 latency (`/api/input`) | `histogram_quantile(0.99, ...)` | Graph |
| Auth failures | `rate(hono_gateway_auth_failures_total[5m])` | Stat |

**D6-B — RESOLVED ✅**: **Option A — Prometheus histograms** (resolved 2026-03-03). Per-module latency is derived from OTel spans exported to Prometheus histograms via the Collector. No Tempo required for Phase 8C. A Grafana Tempo waterfall panel is the natural next addition to this dashboard once Tempo is confirmed functional under the optional `observability-full` profile (D6-D ✅).

**D6-C — RESOLVED ✅**: **Option A + C — Blackbox Exporter + existing Prometheus metrics** (resolved 2026-03-03). The Blackbox Exporter provides a reliable HTTP-level health probe per module (detects full process failure). Existing module metrics (e.g. `brain_metacognition_task_confidence`) provide the detail panels. Option B (OTel heartbeat spans) is a Phase 9 enhancement.

**D6-D — RESOLVED ✅**: **Distributed trace backend** — Grafana Tempo added as an optional `observability-full` Docker Compose profile (resolved 2026-03-03). Non-blocking for Gate 5. See §10 for full implementation detail.

**D6-E — RESOLVED ✅**: **Option C — Both SSE-side detection and `GET /api/health` polling** (resolved 2026-03-03). The StatusBar shows two signals: SSE connection state (from the `useSSEStream` hook — already in D5) and gateway reachability (from a `GET /api/health` poll every 30 s). The poll is ~20 lines of client code with a cleanup interval. Distinguishing "stream error" from "gateway unreachable" is worth the minimal additional scope.

### 1.4 Cross-Module OTel Audit Scope

**D6-F — RESOLVED ✅**: **Option B — audit all modules, fix critical-path modules in Phase 8C** (resolved 2026-03-03). Run the §7.1 audit checklist across all Group I–IV modules and populate the §7.4 tracking table. Apply fixes only to critical-path modules (Groups II + III: `working-memory`, `reasoning`, `executive-agent`, `motor-output`, `metacognition`). Non-critical modules' audit results are recorded for Phase 9 handoff.

### 1.5 Design Decisions — All Resolved ✅

| ID | Decision | Resolution | Date |
|---|---|---|---|
| D6-A | Gateway dashboard panel set? | **All 5 panels** — request rate, error rate, active SSE, auth failures, P50/95/99 latency | 2026-03-03 |
| D6-B | Signal Flow dashboard approach? | **Option A — Prometheus histograms**; Tempo waterfall as follow-on | 2026-03-03 |
| D6-C | Module Health dashboard approach? | **Option A + C** — Blackbox Exporter + existing Prometheus metrics | 2026-03-03 |
| D6-D | Tempo optional Docker profile in Phase 8C? | **Yes — optional `observability-full` profile**, non-blocking for Gate 5 | 2026-03-03 |
| D6-E | Internals StatusBar connection indicator? | **Option C — SSE-side detection + `GET /api/health` polling every 30 s** | 2026-03-03 |
| D6-F | Cross-module OTel audit scope? | **Option B — audit all, fix critical-path (Groups II + III) in Phase 8C** | 2026-03-03 |

---

## 2. Pre-Implementation Checklist

### 2.1 Schema Pre-Landing Verified

```bash
# Verify traceparent field in mcp-context.schema.json
grep -l "traceparent" shared/schemas/mcp-context.schema.json
# If absent: land schema change first (see D7 §4.1)

# buf lint passes
cd shared && buf lint
```

### 2.2 OTel Collector Accepts OTLP HTTP

```bash
# Verify OTLP HTTP receiver on port 4318
grep "4318" observability/otel-collector.yaml
# If absent: add http protocol under otlp receiver (see D7 §6.4)

# OTel Collector running
docker compose ps otel-collector
curl -s http://localhost:4318/v1/traces -X POST \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' -w "%{http_code}"
# Should return 200
```

### 2.3 Prometheus Running and Scraping

```bash
docker compose ps prometheus
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep "health"
```

### 2.4 Grafana Running

```bash
docker compose ps grafana
curl -s http://localhost:3000/api/health | grep '"database": "ok"'
```

### 2.5 Gate 2 Verified (Gateway Operational)

Phase 8C can run in parallel with Phase 8B once Gate 2 is cleared:
```bash
curl -s http://localhost:3001/api/health | grep '"status":"ok"'
```

---

## 3. Build Sequence and Gate Definitions

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 8C Build Sequence                                                 │
│                                                                          │
│  0.  Design discussion signed off (§1)                                  │
│  0a. traceparent schema change verified/landed                           │
│  0b. OTel Collector OTLP HTTP verified                                   │
│                                                                          │
│  ─── GATE C0: OTel stack verified; schema pre-landing complete ────────  │
│                                                                          │
│  1.  Gateway OTel instrumentation (§4)                                  │
│      NodeSDK, Hono tracing middleware, pino logging                      │
│                                                                          │
│  ─── GATE C1: gateway spans visible in OTel Collector output ─────────  │
│                                                                          │
│  2.  TraceContext propagation into MCPContext (§6)                      │
│      Inject traceparent into MCP JSON-RPC messages                       │
│                                                                          │
│  ─── GATE C2: traceparent present in MCP messages; verify in MCP logs ─ │
│                                                                          │
│  3.  Cross-module audit (§7)                                            │
│      Audit Groups I–IV; fix critical-path modules (per D6-F)            │
│                                                                          │
│  ─── GATE C3: critical-path modules emit trace_id in structlog output ─  │
│                                                                          │
│  4.  Grafana dashboards (§8)                                            │
│      gateway.json + signal-flow.json + module-health.json                │
│                                                                          │
│  5.  Prometheus alert rules (§9)                                        │
│      Phase 8 gateway + auth alerts                                       │
│                                                                          │
│  6.  Tempo optional profile (§10) — non-blocking                        │
│                                                                          │
│  ─── GATE C4 (Gate 5): spans flow; dashboards render; Prom scraping ─── │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. OTel Gateway Instrumentation

### 4.1 `telemetry.ts` — NodeSDK Initialization

```typescript
/**
 * telemetry.ts — OTel NodeSDK setup for Hono gateway.
 *
 * Must be the FIRST import in index.ts, before any Hono or application code.
 * This ensures auto-instrumentations are registered before modules load.
 *
 * Biological analogue: insular cortex setup — all afferent signals route to
 * the interoceptive integration centre before reaching the executive surface.
 */
import { NodeSDK } from '@opentelemetry/sdk-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { W3CTraceContextPropagator } from '@opentelemetry/core'
import { Resource } from '@opentelemetry/resources'
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from '@opentelemetry/semantic-conventions'

const sdk = new NodeSDK({
  resource: new Resource({
    [SEMRESATTRS_SERVICE_NAME]: process.env.OTEL_SERVICE_NAME ?? 'hono-gateway',
    [SEMRESATTRS_SERVICE_VERSION]: '0.1.0',
    'service.namespace': 'brain',
  }),
  traceExporter: new OTLPTraceExporter({
    url: `${process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318'}/v1/traces`,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
  textMapPropagator: new W3CTraceContextPropagator(),
})

sdk.start()

process.on('SIGTERM', () => sdk.shutdown())
process.on('SIGINT', () => sdk.shutdown())
```

**Critical**: `import './telemetry.js'` must appear as the first line of `index.ts`.

### 4.2 Hono Tracing Middleware

Hono is not auto-instrumented by `@opentelemetry/auto-instrumentations-node` (which covers Express, Fastify, Koa, etc.). Manual middleware is required:

```typescript
// src/middleware/tracing.ts
import { createMiddleware } from 'hono/factory'
import { trace, context, propagation, SpanStatusCode } from '@opentelemetry/api'
import { W3CTraceContextPropagator } from '@opentelemetry/core'

const propagator = new W3CTraceContextPropagator()
const tracer = trace.getTracer('hono-gateway', '0.1.0')

export const tracingMiddleware = createMiddleware(async (c, next) => {
  // Extract incoming W3C TraceContext from browser headers (if present)
  const carrier: Record<string, string> = {}
  c.req.raw.headers.forEach((val, key) => { carrier[key] = val })
  const parentCtx = propagation.extract(context.active(), carrier)

  // Create span for this request
  const span = tracer.startSpan(
    `${c.req.method} ${c.req.routePath ?? c.req.path}`,
    { kind: 1 /* SERVER */ },
    parentCtx
  )

  // Make span active in async context
  await context.with(trace.setSpan(parentCtx, span), async () => {
    try {
      await next()
      span.setStatus({ code: c.res.status < 400 ? SpanStatusCode.OK : SpanStatusCode.ERROR })
    } catch (err) {
      span.recordException(err as Error)
      span.setStatus({ code: SpanStatusCode.ERROR })
      throw err
    } finally {
      span.setAttribute('http.status_code', c.res.status)
      span.setAttribute('http.method', c.req.method)
      span.setAttribute('http.route', c.req.routePath ?? c.req.path)
      span.end()
    }
  })
})
```

Mount globally in `app.ts`:
```typescript
app.use('*', tracingMiddleware)
```

### 4.3 Prometheus Metrics via OTel Meter

Custom gateway metrics (emitted from request lifecycle):

```typescript
// src/middleware/metrics.ts
import { metrics } from '@opentelemetry/api'

const meter = metrics.getMeter('hono-gateway', '0.1.0')

export const requestCounter = meter.createCounter('hono_gateway_requests_total', {
  description: 'Total HTTP requests handled by Hono gateway',
})

export const authFailureCounter = meter.createCounter('hono_gateway_auth_failures_total', {
  description: 'Total auth failures (401 responses)',
})

export const sseConnectionGauge = meter.createUpDownCounter('hono_gateway_sse_active_connections', {
  description: 'Currently active SSE connections',
})

export const inputLatencyHistogram = meter.createHistogram('hono_gateway_input_latency_ms', {
  description: 'Latency histogram for POST /api/input → 202 response (ms)',
  unit: 'ms',
})
```

Usage in route handlers:
```typescript
// In /api/input handler
const start = Date.now()
requestCounter.add(1, { route: '/api/input', method: 'POST' })
// ... process request ...
inputLatencyHistogram.record(Date.now() - start, { route: '/api/input' })

// In authMiddleware on 401
authFailureCounter.add(1, { reason: 'missing_token' | 'invalid_token' | 'expired' })

// In SSE stream open/close
sseConnectionGauge.add(1)   // on open
sseConnectionGauge.add(-1)  // on close/abort
```

**Prometheus exporter**: The OTel Prometheus exporter is not used here — OTel exports to the Collector via OTLP, and the Collector's Prometheus exporter scrapes to Prometheus. This is the correct pipeline for the existing observability stack.

### 4.4 OTel Collector Prometheus Exporter Naming

The OTel Collector transforms metric names. Verify that `hono_gateway_*` metrics flow through correctly:

```yaml
# observability/otel-collector.yaml
processors:
  resource:
    attributes:
      - key: service.namespace
        value: "brain"
        action: upsert

# Ensure Prometheus exporter config preserves hono_gateway_ prefix
exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: ""    # Do not add namespace prefix — metrics already have hono_gateway_ prefix
```

---

## 5. Structured Logging (Gateway)

### 5.1 Pino Setup

```typescript
// src/logger.ts
import pino from 'pino'
import { trace } from '@opentelemetry/api'

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  formatters: {
    log: (obj) => {
      // Inject OTel trace context into every log record
      const span = trace.getActiveSpan()
      if (span?.isRecording()) {
        const ctx = span.spanContext()
        return {
          ...obj,
          trace_id: ctx.traceId,
          span_id: ctx.spanId,
          trace_flags: ctx.traceFlags,
        }
      }
      return obj
    },
  },
})
```

### 5.2 Log Field Standards

All gateway log records must include:

```json
{
  "level": "info",
  "time": 1741000000000,
  "msg": "...",
  "service": "hono-gateway",
  "trace_id": "00-<traceId>-<spanId>-01",
  "span_id": "<spanId>",
  "method": "POST",
  "path": "/api/input",
  "status": 202
}
```

This matches the `shared/utils/logging.md` structured log format specification.

---

## 6. TraceContext Propagation into MCPContext

### 6.1 Schema Pre-Landing Required

Before this section is implemented, verify `shared/schemas/mcp-context.schema.json` has the `traceparent` field (see D7 §4.1). If absent, land the schema change first.

### 6.2 Injection in `mcp-client.ts`

```typescript
// In McpClient.send() — inject current span's traceparent into every MCP message
import { propagation, context } from '@opentelemetry/api'

private async post(body: object): Promise<Response> {
  const carrier: Record<string, string> = {}
  propagation.inject(context.active(), carrier)   // injects 'traceparent' and 'tracestate'

  return fetch(this.serverUrl, {
    method: 'POST',
    headers: {
      ...this.buildHeaders(),
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream',
      ...carrier,   // propagates 'traceparent' to MCP server
    },
    body: JSON.stringify(body),
  })
}
```

### 6.3 MCPContext Envelope Injection

For JSON-RPC messages that carry an MCPContext payload (e.g. `chat` tool calls), inject `traceparent` into the MCPContext envelope body as well:

```typescript
// When building the MCP tool call payload
const carrier: Record<string, string> = {}
propagation.inject(context.active(), carrier)

const mcpMessage = {
  jsonrpc: '2.0',
  id: sessionId,
  method: 'tools/call',
  params: {
    name: 'chat',
    arguments: {
      message,
      traceparent: carrier['traceparent'],    // MCPContext field per schema
    },
  },
}
```

### 6.4 `infrastructure/mcp` — Span Continuation

The MCP server (`infrastructure/mcp`) must extract `traceparent` from incoming HTTP headers and continue the trace:

```typescript
// In infrastructure/mcp/src/middleware.ts (or equivalent)
import { propagation, context, trace } from '@opentelemetry/api'

// Extract from HTTP headers
const carrier = Object.fromEntries(req.headers)
const parentCtx = propagation.extract(context.active(), carrier)

// Create child span
const span = tracer.startSpan('mcp.handle', {}, parentCtx)
```

This ensures the trace flows: Browser → Gateway → MCP server → downstream modules.

---

## 7. Cross-Module Audit — Python Modules (Groups I–IV)

### 7.1 Audit Checklist (run for each module)

For each Python module under `modules/`:

```bash
MODULE_PATH=modules/group-ii-cognitive-processing/working-memory

# Check structlog is in dependencies
grep "structlog" $MODULE_PATH/pyproject.toml

# Check trace_id injection in log calls
grep -r "trace_id" $MODULE_PATH/src/ || echo "MISSING: trace_id injection"
grep -r "structlog" $MODULE_PATH/src/ || echo "MISSING: structlog usage"

# Check OTel in dependencies
grep "opentelemetry" $MODULE_PATH/pyproject.toml || echo "MISSING: OTel dependency"

# Check OTLP exporter config
grep -r "OTLPSpanExporter\|OTLPTraceExporter" $MODULE_PATH/src/ || echo "MISSING: OTLP exporter"
```

### 7.2 Critical-Path Modules (fix in Phase 8C per D6-F)

Priority order for Phase 8C remediation:

| Module | Path | Priority | Required for M8 smoke test? |
|---|---|---|---|
| `working-memory` | `modules/group-ii-cognitive-processing/memory/working-memory/` | P0 | Yes — subscribed by Internals panel |
| `reasoning` | `modules/group-ii-cognitive-processing/reasoning/` | P0 | Yes — processes chat input |
| `executive-agent` | `modules/group-iii-executive-output/executive-agent/` | P0 | Yes — orchestrates response |
| `motor-output` | `modules/group-iii-executive-output/motor-output/` | P0 | Yes — emits final output |
| `metacognition` | `modules/group-iv-adaptive-systems/metacognition/` | P1 | Yes — confidence panel in Internals |
| `learning-adaptation` | `modules/group-iv-adaptive-systems/learning-adaptation/` | P1 | No — passive during chat |
| `perception`, `attention-filtering`, `sensory-input` | `modules/group-i-signal-processing/` | P2 | Partial — needed for full trace |
| `affective`, `episodic-memory`, `long-term-memory` | `modules/group-ii-cognitive-processing/` | P2 | Partial |

### 7.3 Standard `structlog` + OTel Trace Injection Pattern (Python)

Apply this pattern to any critical-path module missing OTel trace injection:

```python
# In each module's otel_setup.py
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def configure_module_telemetry(service_name: str, otlp_endpoint: str) -> trace.Tracer:
    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name,
        "service.namespace": "brain",
    }))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

# structlog processor to inject OTel trace_id
def add_otel_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

structlog.configure(
    processors=[
        add_otel_trace_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
```

### 7.4 Audit Output Format

For each module audited, record the result in a tracking table:

| Module | structlog present | OTel dep present | trace_id injected | OTLP exporter | Status |
|---|---|---|---|---|---|
| `working-memory` | ☐ | ☐ | ☐ | ☐ | Pending audit |
| `reasoning` | ☐ | ☐ | ☐ | ☐ | Pending audit |
| `executive-agent` | ☐ | ☐ | ☐ | ☐ | Pending audit |
| `motor-output` | ☐ | ☐ | ☐ | ☐ | Pending audit |
| `metacognition` | ☐ | ☐ | ☐ | ☐ | Pending audit |
| `learning-adaptation` | ☐ | ☐ | ☐ | ☐ | Pending audit |

(Fill in after audit runs.)

---

## 8. Grafana Dashboard Specifications

All Grafana dashboard JSON files are stored in `observability/grafana/dashboards/` and provisioned automatically via the Grafana provisioning config.

### 8.1 Gateway Dashboard (`gateway.json`)

**UID**: `brain-gateway`
**Title**: `brAIn — Gateway`

| Panel | Query | Type |
|---|---|---|
| Request Rate | `rate(hono_gateway_requests_total[5m])` | Time series |
| Error Rate (4xx/5xx) | `rate(hono_gateway_requests_total{status=~"[45].."}[5m])` | Time series |
| Auth Failures | `rate(hono_gateway_auth_failures_total[5m])` | Stat |
| Active SSE Connections | `hono_gateway_sse_active_connections` | Gauge |
| P50 Latency `/api/input` | `histogram_quantile(0.50, rate(hono_gateway_input_latency_ms_bucket[5m]))` | Stat |
| P95 Latency `/api/input` | `histogram_quantile(0.95, rate(hono_gateway_input_latency_ms_bucket[5m]))` | Stat |
| P99 Latency `/api/input` | `histogram_quantile(0.99, rate(hono_gateway_input_latency_ms_bucket[5m]))` | Stat |

### 8.2 Signal Flow Dashboard (`signal-flow.json`)

**UID**: `brain-signal-flow`
**Title**: `brAIn — Signal Flow Latency`

Per-module latency approximation using OTel-derived Prometheus histograms:

| Panel | Query | Type |
|---|---|---|
| Gateway → MCP latency P99 | `histogram_quantile(0.99, rate(hono_gateway_input_latency_ms_bucket[5m]))` | Stat |
| Executive-Agent latency P99 | (OTel span duration exported as Prometheus histogram) | Stat |
| Motor-Output latency P99 | (OTel span duration exported as Prometheus histogram) | Stat |
| End-to-end latency (Browser → first token) | Derived from gateway SSE first-event latency | Graph |

**Note**: Per-module latency histograms require OTel spans to be exported from each module's OTLP pipeline to the Collector and from the Collector to Prometheus. Verify each critical-path module exports spans to the Collector (audit in §7).

**If Tempo is enabled** (D6-D): Replace the histogram panels with a Grafana Tempo datasource trace explorer panel for the end-to-end trace waterfall.

### 8.3 Module Health Dashboard (`module-health.json`)

**UID**: `brain-module-health`
**Title**: `brAIn — Module Health`

Requires Prometheus Blackbox Exporter (add to `docker-compose.yml` if not present):

```yaml
# docker-compose.yml addition
blackbox:
  image: prom/blackbox-exporter:latest
  ports:
    - "9115:9115"
  volumes:
    - ./observability/blackbox.yml:/etc/blackbox/blackbox.yml:ro
```

```yaml
# observability/blackbox.yml
modules:
  http_health:
    prober: http
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200]
      fail_if_body_not_matches_regexp: ["ok"]
```

```yaml
# prometheus.yml — Blackbox scrape config
- job_name: 'module-health-blackbox'
  metrics_path: /probe
  params:
    module: [http_health]
  static_configs:
    - targets:
        - http://gateway:3001/api/health
        - http://working-memory:8160/health
        - http://reasoning:8161/health
        - http://executive-agent:8162/health
        - http://motor-output:8163/health
        - http://metacognition:8171/health
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: blackbox:9115
```

Dashboard panels:
| Panel | Query | Type |
|---|---|---|
| Module health status | `probe_success{job="module-health-blackbox"}` | State timeline |
| Module probe latency | `probe_duration_seconds{job="module-health-blackbox"}` | Table |
| Metacognition confidence (all goal classes) | `brain_metacognition_task_confidence` | Gauge per label |
| Escalation rate | `rate(brain_metacognition_escalation_total[5m])` | Graph |

### 8.4 Grafana Provisioning

Grafana datasource and dashboard provisioning (`observability/grafana/provisioning/`):

```yaml
# observability/grafana/provisioning/dashboards/phase-8.yaml
apiVersion: 1
providers:
  - name: 'phase-8'
    folder: 'Phase 8 — Interface Layer'
    type: file
    options:
      path: /etc/grafana/dashboards
```

**Note**: The Grafana Docker service in `docker-compose.yml` must mount `observability/grafana/dashboards/` to `/etc/grafana/dashboards`. Verify this is configured; add volume mount if absent.

---

## 9. Prometheus Alert Rules (Phase 8 Additions)

**File**: `observability/prometheus-rules/gateway.yml`

```yaml
groups:
  - name: gateway
    interval: 30s
    rules:
      - alert: GatewayHighErrorRate
        expr: rate(hono_gateway_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Gateway 5xx error rate above 5%"
          description: "Error rate: {{ $value | humanize }}/s"

      - alert: GatewayAuthFailureSpike
        expr: rate(hono_gateway_auth_failures_total[5m]) > 0.1
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Elevated auth failures on gateway"
          description: "Auth failure rate: {{ $value | humanize }}/s — potential invalid token issue"

      - alert: GatewayHighLatency
        expr: histogram_quantile(0.99, rate(hono_gateway_input_latency_ms_bucket[5m])) > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Gateway /api/input P99 latency above 5 s"
          description: "P99: {{ $value | humanize }} ms"

      - alert: NoActiveSSEConnections
        expr: hono_gateway_sse_active_connections == 0
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "No active SSE connections to gateway"
          description: "No browser sessions active — system idle or unreachable"
```

Add to `prometheus.yml`:
```yaml
rule_files:
  - "prometheus-rules/gateway.yml"
  # (existing rule files) ...
```

---

## 10. Distributed Trace Backend (Tempo)

> **Status**: Optional deliverable for Phase 8C (non-blocking for Gate 5). Implement if Gate C3 is cleared with time remaining.

### 10.1 `docker-compose.yml` Addition (optional `observability-full` profile)

See D7 §6.3 for the full Tempo Docker Compose service definition.

### 10.2 `observability/tempo.yaml`

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks
```

### 10.3 OTel Collector — Tempo Export Pipeline

```yaml
# observability/otel-collector.yaml additions (for observability-full profile)
exporters:
  otlp/tempo:
    endpoint: "tempo:4317"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [prometheus, otlp/tempo]   # add otlp/tempo
```

### 10.4 Grafana Tempo Datasource

```yaml
# observability/grafana/provisioning/datasources/tempo.yaml
apiVersion: 1
datasources:
  - name: Tempo
    type: tempo
    url: http://tempo:3200
    isDefault: false
    jsonData:
      tracesToMetrics:
        datasourceUid: 'prometheus'
```

### 10.5 Activation

```bash
# Start with Tempo enabled
docker compose --profile observability-full up -d

# Verify Tempo receiving spans
curl -s http://localhost:3200/status/config | head -10
```

---

## 11. Phase 8C Completion Gate (Gate 5)

```bash
# Gate C1: Gateway spans in OTel Collector
# Send a request and verify span appears
curl -s -H "Authorization: Bearer <token>" \
  -X POST http://localhost:3001/api/input \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}' > /dev/null

# Check collector logs for span
docker compose logs otel-collector | grep "hono-gateway" | tail -5

# Gate C2: traceparent in MCP messages
docker compose logs mcp | grep "traceparent" | tail -3

# Gate C3: critical-path module trace_id in logs
docker compose logs working-memory | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        record = json.loads(line)
        assert 'trace_id' in record, 'MISSING trace_id'
        print('trace_id OK:', record['trace_id'][:8])
        break
    except (json.JSONDecodeError, KeyError):
        continue
"

# Prometheus scraping gateway metrics
curl -s "http://localhost:9090/api/v1/query?query=hono_gateway_requests_total" \
  | python3 -m json.tool | grep '"status": "success"'

# Grafana dashboards loading
curl -s http://localhost:3000/api/dashboards/uid/brain-gateway \
  -u admin:admin | python3 -m json.tool | grep '"title"'

curl -s http://localhost:3000/api/dashboards/uid/brain-signal-flow \
  -u admin:admin | python3 -m json.tool | grep '"title"'

curl -s http://localhost:3000/api/dashboards/uid/brain-module-health \
  -u admin:admin | python3 -m json.tool | grep '"title"'

# TypeScript clean
cd apps/default/server && pnpm typecheck

# Lint
cd apps/default/server && pnpm lint
```

---

## 12. Decisions Recorded

| ID | Decision | Rationale |
|---|---|---|
| D8C-1 | `telemetry.ts` must be first import in `index.ts` | OTel auto-instrumentations must register before any module loads |
| D8C-2 | W3C TraceContext propagation (not B3) | MCP spec propagation model; cross-language support (D2 §iv) |
| D8C-3 | OTLP HTTP (not gRPC) from TypeScript gateway | Browser-friendly transport; consistent with Node.js OTel SDKs |
| D8C-4 | Pino with OTel trace_id injection | `structlog` equivalent for TypeScript; JSON output matches shared log format spec (D2 §iv) |
| D8C-5 | Prometheus scraping via OTel Collector (not direct exporter) | Consistent with existing observability stack architecture |
| D8C-6 | Dashboard set: gateway + signal-flow + module-health | Insular cortex body map analogy — one panel per "organ" (D1 §iv) |
| D8C-7 | Blackbox Exporter for module health probes | HTTP-level health check; detects full process failure vs metric degradation |
| D8C-8 | Tempo under optional `observability-full` profile | Non-blocking for M8; avoids adding mandatory infra to the default stack |
| D8C-9 | Audit all modules; fix critical-path (Groups II + III) in Phase 8C ✅ | Full audit gives complete Phase 9 handoff picture; fix scope bounded to M8 critical path (D6-F resolved 2026-03-03) |
| D6-A | All 5 gateway dashboard panels confirmed ✅ | Resolved 2026-03-03 |
| D6-B | Prometheus histograms for signal-flow dashboard ✅ | Option A confirmed; Tempo waterfall panel deferred until Tempo optional profile is verified (resolved 2026-03-03) |
| D6-C | Blackbox Exporter + existing Prometheus metrics for module health ✅ | Option A + C confirmed; OTel heartbeat spans deferred to Phase 9 (resolved 2026-03-03) |
| D6-D | Grafana Tempo optional `observability-full` profile ✅ | Non-blocking for M8; avoids adding mandatory infra to the default stack (resolved 2026-03-03) |
| D6-E | Option C — SSE-side detection + `GET /api/health` polling every 30 s ✅ | Distinguishes "stream error" from "gateway unreachable"; ~20 lines of client code (resolved 2026-03-03) |
| D6-F | Audit all modules; fix critical-path only in Phase 8C ✅ | Option B confirmed — non-critical module results recorded for Phase 9 handoff (resolved 2026-03-03) |
