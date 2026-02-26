---
id: spec-tracing
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Distributed Trace Context Propagation Specification

> **Applies to**: all EndogenAI modules (Python and TypeScript).

This document specifies how distributed trace context is established, propagated, and used across all module boundaries
in the EndogenAI framework. The observability stack (OpenTelemetry Collector → Prometheus / Grafana / Tempo) depends on
correct trace propagation to provide end-to-end request visibility.

---

## 1. Standard: W3C Trace Context

EndogenAI adopts **[W3C Trace Context Level 1](https://www.w3.org/TR/trace-context/)** as the single standard for
distributed trace propagation. All modules MUST parse and forward the `traceparent` header without modification.

### 1.1 `traceparent` Format

```
version-traceId-parentId-traceFlags
```

| Component    | Length | Description                                                         |
| ------------ | ------ | ------------------------------------------------------------------- |
| `version`    | 2 hex  | Always `00` for the current spec.                                   |
| `traceId`    | 32 hex | 128-bit globally unique trace identifier. Established at ingestion. |
| `parentId`   | 16 hex | 64-bit identifier for the current span.                             |
| `traceFlags` | 2 hex  | `01` = sampled, `00` = not sampled.                                 |

**Example**: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`

### 1.2 `tracestate` Format

An optional, vendor-specific comma-separated list of `key=value` pairs. Pass through unchanged. The EndogenAI framework
reserves the `endogen` key for internal use:

```
endogen=layer:sensory-input;module:sensory-input-01,ot=...
```

---

## 2. Trace Lifecycle

### 2.1 Trace Establishment

A new trace MUST be created at the **system boundary** — wherever an external signal first enters the EndogenAI
framework:

- **Sensory / Input Layer**: on receipt of any raw input (text, image, audio, API event, sensor).
- **Application Layer**: on receipt of an inbound API request, webhook, or user message.

The first module to receive a signal is responsible for:

1. Checking for an existing `traceparent` in the inbound request headers / envelope.
2. If absent: generate a new `traceId` (128-bit random UUID) and a new `parentId` (64-bit random).
3. Attach `traceparent` (and optionally `tracestate`) to the `Signal.traceContext` and `MCPContext.traceContext`.
4. Include the trace context in the structured log entry for the ingestion event.

### 2.2 Trace Propagation

Every module that receives a `Signal` or `MCPContext` MUST:

1. Extract `traceparent` from the incoming envelope.
2. Create a new **child span** (`parentId` = new random 64-bit ID; `traceId` = unchanged).
3. Send the updated `traceparent` (with the new `parentId`) in any outbound messages.
4. Log the `traceId` and `spanId` in every log record emitted while processing (see [Logging Spec](./logging.md)).

### 2.3 Trace Termination

A trace ends when:

- The Motor / Output / Effector Layer delivers the final action (API call, message dispatch, file write).
- An unrecoverable error causes the processing pipeline to halt.

The terminal span MUST log the final outcome (`INFO` for success, `ERROR` / `FATAL` for failure) with the full
`traceId`.

---

## 3. Schema Integration (TraceContext Object)

All shared schemas that carry trace context use the following embedded object:

```json
{
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "tracestate": "endogen=layer:sensory-input"
}
```

This appears as the `traceContext` property in:

- [`MCPContext`](../schemas/mcp-context.schema.json) — `$.traceContext`
- [`A2AMessage`](../schemas/a2a-message.schema.json) — `$.traceContext`
- [`A2ATask`](../schemas/a2a-task.schema.json) — `$.traceContext`
- [`Signal`](../types/signal.schema.json) — `$.traceContext`
- [`RewardSignal`](../types/reward-signal.schema.json) — `$.traceContext`

The `traceparent` pattern (validated in all schemas): `^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$`

---

## 4. Language-Specific Guidance

### Python

Use the [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/en/latest/):

```python
from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer("sensory-input", "0.1.0")

# Extract from inbound envelope
carrier = {"traceparent": signal.trace_context.traceparent}
ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

# Start a child span
with tracer.start_as_current_span("process_signal", context=ctx) as span:
    span.set_attribute("signal.id", str(signal.id))
    # ... processing ...
    # Inject updated traceparent for outbound envelope
    outbound_carrier: dict = {}
    inject(outbound_carrier)
    outbound_signal.trace_context.traceparent = outbound_carrier["traceparent"]
```

### TypeScript

Use the [OpenTelemetry JS SDK](https://opentelemetry.io/docs/languages/js/):

```typescript
import { context, propagation, trace } from "@opentelemetry/api";
import { W3CTraceContextPropagator } from "@opentelemetry/core";

const tracer = trace.getTracer("sensory-input", "0.1.0");

// Extract from inbound envelope
const carrier = { traceparent: signal.traceContext.traceparent };
const ctx = propagation.extract(context.active(), carrier);

const span = tracer.startSpan("process_signal", undefined, ctx);
span.setAttribute("signal.id", signal.id);

try {
  // ... processing ...
  const outboundCarrier: Record<string, string> = {};
  propagation.inject(trace.setSpan(context.active(), span), outboundCarrier);
  outboundSignal.traceContext.traceparent = outboundCarrier["traceparent"];
} finally {
  span.end();
}
```

---

## 5. Sampling Policy

| Environment | Default Sampling Rate | Override Mechanism                        |
| ----------- | --------------------- | ----------------------------------------- |
| Development | 100% (always sample)  | `OTEL_TRACES_SAMPLER=always_on`           |
| Staging     | 100%                  | `OTEL_TRACES_SAMPLER=always_on`           |
| Production  | 10% (head-based)      | `OTEL_TRACES_SAMPLER_ARG=0.1` (configure) |

The `traceFlags` byte in `traceparent` reflects the sampling decision: `01` = sampled, `00` = not sampled. Modules MUST
forward the sampling decision as-is and MUST NOT override it mid-trace.

---

## 6. Prohibited Patterns

- **Do not** generate a new `traceId` for signals that already carry a `traceparent`.
- **Do not** drop or transform the `tracestate` value — pass it through unchanged.
- **Do not** use a non-W3C propagation format (e.g. B3, Jaeger) unless explicitly required by an external dependency, in
  which case use an OTel propagator bridge.
- **Do not** embed the full `traceparent` string in business data (only carry it in `traceContext`).

---

## References

- [W3C Trace Context Level 1](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)
- [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/)
- [OpenTelemetry JavaScript SDK](https://opentelemetry.io/docs/languages/js/)
- [Logging Spec](./logging.md)
- [Observability Setup Guide](../../observability/README.md)
- [MCP Context Schema](../schemas/mcp-context.schema.json)
