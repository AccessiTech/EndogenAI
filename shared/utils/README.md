---
id: shared-utils
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-03-02
---

# Shared Utilities

Observability specifications and cross-cutting validation patterns for all EndogenAI modules (Python and TypeScript).

## Purpose

`shared/utils/` contains the normative specifications that govern how every EndogenAI module emits logs, propagates trace context, and validates inbound data at module boundaries. These are not library packages — they are authored specs that module implementations must conform to. The observability stack (OpenTelemetry Collector → Prometheus / Grafana / Tempo) depends on correct adherence to the logging and tracing specs to provide end-to-end visibility.

---

## Specifications

| File | Title | Applies to |
|------|-------|------------|
| [`logging.md`](logging.md) | Structured Log Format Specification | All EndogenAI modules (Python + TypeScript). Defines the mandatory JSON log envelope, field names, severity levels, and stdout convention. |
| [`tracing.md`](tracing.md) | Distributed Trace Context Propagation Specification | All EndogenAI modules (Python + TypeScript). Defines how W3C `traceparent` / `tracestate` headers are established, injected, and extracted across MCP and A2A boundaries. |
| [`validation.md`](validation.md) | Input Sanitisation & Boundary Validation Patterns | All EndogenAI modules (Python + TypeScript). Defines mandatory validation and sanitisation patterns at every module boundary — schema validation, size limits, allow-listing, and error response conventions. |

---

## Quick Reference

### Logging

Every log entry must be a single-line JSON object written to `stdout`:

```json
{
  "timestamp": "2026-03-02T10:00:00.000Z",
  "level": "INFO",
  "module": "working-memory",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Context loaded",
  "data": {}
}
```

See [logging.md](logging.md) for the full field set and severity conventions.

### Tracing

All module-to-module calls (MCP publish, A2A task submission) must propagate W3C trace context. The `MCPContext` envelope carries `traceContext.traceparent` and `traceContext.tracestate` fields for this purpose.

See [tracing.md](tracing.md) for injection / extraction patterns for Python (`opentelemetry-sdk`) and TypeScript (`@opentelemetry/sdk-node`).

### Validation

Every inbound payload at a module boundary must be validated against its JSON Schema using Ajv (TypeScript) or `jsonschema` / Pydantic (Python) before processing. Invalid payloads must be rejected with a structured error log entry and never silently ignored.

See [validation.md](validation.md) for allow-list patterns, size limits, and error response conventions.

---

## See Also

- [observability/](../../observability/README.md) — OTel Collector, Prometheus, and Grafana configuration
- [shared/schemas/mcp-context.schema.json](../schemas/mcp-context.schema.json) — defines the `traceContext` fields on MCPContext
- [docs/guides/observability.md](../../docs/guides/observability.md) — observability stack setup guide
