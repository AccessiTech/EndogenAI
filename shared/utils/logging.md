---
id: spec-logging
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Structured Log Format Specification

> **Applies to**: all EndogenAI modules (Python and TypeScript).

Every log entry emitted by any EndogenAI module MUST be a single JSON object written to `stdout`. This document defines
the canonical field set, severity levels, and conventions that must be respected for the observability stack
(OpenTelemetry Collector → Prometheus / Grafana) to function correctly.

---

## 1. Canonical Log Record

```json
{
  "timestamp": "2026-02-26T12:34:56.789Z",
  "level": "INFO",
  "message": "Signal ingested from sensory-input layer",
  "service": "sensory-input",
  "version": "0.1.0",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "traceFlags": "01",
  "moduleId": "sensory-input",
  "layer": "sensory-input",
  "sessionId": "session-abc123",
  "signalId": "550e8400-e29b-41d4-a716-446655440000",
  "error": null,
  "data": {
    "modality": "text"
  }
}
```

---

## 2. Required Fields

| Field       | Type     | Description                                                                                   |
| ----------- | -------- | --------------------------------------------------------------------------------------------- |
| `timestamp` | `string` | ISO 8601 UTC timestamp with millisecond precision (`YYYY-MM-DDTHH:mm:ss.sssZ`).               |
| `level`     | `string` | Severity level (see §3). MUST be uppercase.                                                   |
| `message`   | `string` | Human-readable log message. Must be a static, descriptive string — not interpolated IDs/URLs. |
| `service`   | `string` | Canonical module identifier (matches `source.moduleId` in `MCPContext`).                      |
| `version`   | `string` | Semantic version of the emitting module (e.g. `"0.1.0"`).                                     |

## 3. Conditional Fields

These fields MUST be populated when the relevant context is available:

| Field        | Type           | Condition                                                                        |
| ------------ | -------------- | -------------------------------------------------------------------------------- |
| `traceId`    | `string`       | Present whenever a W3C `traceparent` is in scope.                                |
| `spanId`     | `string`       | Present whenever a W3C `traceparent` is in scope.                                |
| `traceFlags` | `string`       | Present whenever a W3C `traceparent` is in scope. Hex string `"01"` for sampled. |
| `moduleId`   | `string`       | Always. Should equal `service`.                                                  |
| `layer`      | `string`       | Always. One of the architectural layers from `MCPContext.ModuleRef`.             |
| `sessionId`  | `string`       | When processing a user session.                                                  |
| `signalId`   | `string\|null` | When processing a `Signal`. UUID v4.                                             |
| `taskId`     | `string\|null` | When executing an A2A task.                                                      |
| `error`      | `object\|null` | Always present on `ERROR` / `FATAL` records (see §5).                            |

## 4. Optional Fields

| Field  | Type     | Description                                                                                                                                                |
| ------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data` | `object` | Arbitrary structured context relevant to the log event. Values MUST be serializable to JSON. Keys should use `snake_case`. Do not put PII or secrets here. |

---

## 5. Severity Levels

| Level   | Numeric | When to Use                                                                                            |
| ------- | ------- | ------------------------------------------------------------------------------------------------------ |
| `TRACE` | 0       | Fine-grained diagnostic events; disabled in production by default.                                     |
| `DEBUG` | 1       | Development-time diagnostics: function entry/exit, variable values. Disabled in production by default. |
| `INFO`  | 2       | Normal operational events: module startup, signal received, task completed.                            |
| `WARN`  | 3       | Recoverable anomalies: retries, near-capacity conditions, deprecated-API calls.                        |
| `ERROR` | 4       | Unrecoverable errors within a single operation. Module remains running. **Requires `error` field.**    |
| `FATAL` | 5       | Unrecoverable errors that cause the module to terminate. **Requires `error` field.**                   |

### `error` Object Schema (required for ERROR / FATAL)

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Missing required field 'id' in signal payload",
    "stack": "..."
  }
}
```

| Field     | Type     | Description                                               |
| --------- | -------- | --------------------------------------------------------- |
| `type`    | `string` | Exception class / error type name.                        |
| `message` | `string` | Concise error message.                                    |
| `stack`   | `string` | Stack trace (development / staging only; redact in prod). |

---

## 6. Output Transport

- All log entries MUST be written to **`stdout`** as newline-delimited JSON (NDJSON).
- Log entries MUST NOT be written to files directly — the container runtime captures `stdout`.
- The OpenTelemetry Collector filelog receiver ingests structured logs from `stdout`.

---

## 7. Language-Specific Guidance

### Python

Use [`structlog`](https://www.structlog.org/) with a JSON renderer:

```python
import structlog

log = structlog.get_logger()
log.info("signal_ingested", service="sensory-input", version="0.1.0", signal_id=str(signal.id))
```

Configure `structlog` to output JSON with the canonical fields at module startup. See the module bootstrap template for
the recommended `structlog` configuration.

### TypeScript

Use [`pino`](https://getpino.io/) with default JSON output:

```typescript
import pino from "pino";

const log = pino({ name: "sensory-input", level: "info" });
log.info({ signalId: signal.id, sessionId }, "Signal ingested");
```

Pino's default JSON format aligns with the canonical schema above. The `name` field maps to `service`.

---

## 8. Prohibited Patterns

- **Do not** interpolate dynamic values into the `message` field (use structured `data` instead).
- **Do not** log PII, credentials, or secrets — not even in `DEBUG` level.
- **Do not** emit multi-line log entries; each entry must be a single JSON object on one line.
- **Do not** use a human-readable formatter in production (text logs break the OTel pipeline).

---

## References

- [OpenTelemetry Semantic Conventions — Logs](https://opentelemetry.io/docs/specs/semconv/general/logs/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Observability Setup Guide](../observability/README.md)
- [Tracing Spec](./tracing.md)
