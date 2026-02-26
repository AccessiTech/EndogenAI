---
id: guide-adding-a-module
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Adding a Module

> **Status: draft** — Shared contract requirements are defined (Phase 1). MCP/A2A wiring steps will be expanded when
> Phase 2 infrastructure is live. Scaffolding templates will be added in Phase 8.

Step-by-step guide for creating a new cognitive module within the EndogenAI framework.

## Overview

Each cognitive module follows a consistent structure and must implement the MCP and A2A interfaces. Modules are
organized under `modules/` grouped by cognitive layer.

## Module Structure

```
modules/<group>/<module-name>/
├── src/                  # Module source code
├── tests/                # Unit and integration tests
├── docs/
│   └── README.md         # Module overview, inputs/outputs, config reference
├── agent-card.json       # A2A agent identity and capability advertisement
├── package.json          # TypeScript package (or pyproject.toml for Python)
└── ...
```

## Steps

### 1. Identify the cognitive group and module analogy

Consult [`brain-structure.md`](../../resources/static/knowledge/brain-structure.md) and the
[Architecture Overview](../architecture.md) to confirm:

- Which **architectural group** the module belongs to (I–V).
- The **neuroanatomical analogy** the module embodies.
- The cognitive layer enum value (used in `source.layer` of all outbound messages).

### 2. Scaffold the module directory

Create the directory under the appropriate group path. Python modules get a `pyproject.toml`; TypeScript modules get a
`package.json` named `@accessitech/<module-name>`.

### 3. Author `agent-card.json`

Every module acts as an autonomous agent and MUST expose an `agent-card.json`. Minimum required fields (see
[A2A Protocol Guide](../protocols/a2a.md#agent-identity)):

```json
{
  "id": "<module-name>",
  "name": "<Human-readable name>",
  "version": "0.1.0",
  "description": "<One-sentence description of the module's cognitive function>",
  "url": "http://<module-name>:<port>",
  "skills": [],
  "mcp": {
    "accepts": ["<contentType>"],
    "emits": ["<contentType>"],
    "version": "0.1.0"
  }
}
```

### 4. Implement the shared contract interfaces

All modules MUST:

#### Validate inbound messages

Validate every inbound JSON payload against the relevant shared schema **before processing**. See
[Validation Spec](../../shared/utils/validation.md) for language-specific patterns and the boundary validation
checklist.

| Payload type  | Schema to validate against                                                  |
| ------------- | --------------------------------------------------------------------------- |
| MCP envelope  | [`mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json)   |
| A2A message   | [`a2a-message.schema.json`](../../shared/schemas/a2a-message.schema.json)   |
| A2A task      | [`a2a-task.schema.json`](../../shared/schemas/a2a-task.schema.json)         |
| Signal        | [`signal.schema.json`](../../shared/types/signal.schema.json)               |
| Memory item   | [`memory-item.schema.json`](../../shared/types/memory-item.schema.json)     |
| Reward signal | [`reward-signal.schema.json`](../../shared/types/reward-signal.schema.json) |

#### Emit structured logs

Every log entry MUST be a single JSON object to `stdout` following the canonical format in
[Logging Spec](../../shared/utils/logging.md). Required fields: `timestamp`, `level`, `message`, `service`, `version`.

#### Propagate trace context

Extract `traceparent` from every inbound message, create a child span, and inject the updated `traceparent` into every
outbound message. See [Tracing Spec](../../shared/utils/tracing.md).

#### Emit typed signals (Group I modules)

Inter-layer data transfer MUST use the `Signal` envelope defined in
[`signal.schema.json`](../../shared/types/signal.schema.json). Assign `traceContext` and `timestamp` at ingestion.

#### Use memory items (memory modules)

All memory records MUST conform to [`memory-item.schema.json`](../../shared/types/memory-item.schema.json). The
`collectionName` field MUST use the `brain.<module-name>` naming convention.

### 5. Wire the vector store adapter _(Phase 1.4)_

_The vector store adapter (Python + TypeScript) will be implemented in Phase 1.4. Until then, document the collection
name your module will use in `shared/vector-store/collection-registry.json`._

### 6. Wire MCP + A2A interfaces _(Phase 2)_

_Full wiring instructions will be provided when Phase 2 infrastructure (`infrastructure/mcp/`, `infrastructure/a2a/`) is
live. See [MCP Protocol Guide](../protocols/mcp.md) and [A2A Protocol Guide](../protocols/a2a.md) for the expected
interface contract._

### 7. Write unit and integration tests

- All components MUST have unit tests.
- Integration tests MUST cover at least: valid input, missing required field, trace context propagation, and validation
  rejection.
- Python modules use `pytest`; TypeScript modules use the test runner configured in `turbo.json`.

### 8. Author `docs/README.md`

Every module MUST have a `README.md` that documents:

- Purpose and neuroanatomical analogy
- Inputs (accepted `contentType` values and schemas)
- Outputs (emitted `contentType` values and schemas)
- Vector store collections used
- Configuration reference
- How to run locally
- Links to relevant shared specs

## Boundary Validation Checklist

Before a module is merged, verify:

- [ ] All inbound message types validated against their JSON Schemas
- [ ] Semantic validation rules documented in `README.md`
- [ ] `ENDOGEN_MAX_PAYLOAD_BYTES` limit enforced
- [ ] Prompt injection mitigation applied to all user-originated text fields
- [ ] Validation error logs include `traceId` and structured `error` object
- [ ] No raw validation error details leaked to external callers
- [ ] Unit tests cover: valid input, missing required field, oversized payload, invalid enum

## References

- [Architecture Overview](../architecture.md)
- [MCP Protocol Guide](../protocols/mcp.md)
- [A2A Protocol Guide](../protocols/a2a.md)
- [Logging Spec](../../shared/utils/logging.md)
- [Tracing Spec](../../shared/utils/tracing.md)
- [Validation Spec](../../shared/utils/validation.md)
- [Brain Structure](../../resources/static/knowledge/brain-structure.md)
- [Workplan](../Workplan.md)
