---
id: shared-schemas
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-03-02
---

# Shared Schemas

Canonical JSON Schema and Protobuf contracts for the EndogenAI system. All shared message types, task envelopes, and cognitive data structures are defined here and must be landed in this directory **before** any implementation that depends on them.

## Purpose

`shared/schemas/` is the single source of truth for all inter-module contracts in EndogenAI. TypeScript types, Python dataclasses, and Protobuf stubs throughout the system must be derived from these schemas — never hand-authored in isolation. Keeping contracts here ensures that changes to shared data structures are visible across all consumers and can be validated in CI.

---

## Schema Catalogue

| File | `$id` title | Description |
|------|------------|-------------|
| `a2a-message.schema.json` | `A2AMessage` | A2A message envelope for agent-to-agent communication. Aligned with A2A Project spec v0.3.0. |
| `a2a-task.schema.json` | `A2ATask` | A2A task lifecycle record — a discrete unit of delegated work between agents. |
| `action-spec.schema.json` | `ActionSpec` | A single parameterised action ready for dispatch by `motor-output`. Includes corollary-discharge `predicted_outcome`. |
| `executive-goal.schema.json` | `ExecutiveGoal` | Goal item managed by the `executive-agent` BDI loop. Encodes desired state transition with priority, lifecycle, and constraints. |
| `mcp-context.schema.json` | `MCPContext` | MCP context envelope — every module-to-module message must conform to this schema. |
| `motor-feedback.schema.json` | `MotorFeedback` | Action outcome reported by `motor-output` back to `executive-agent`. Closes the corollary-discharge feedback loop. |
| `policy-decision.schema.json` | `PolicyDecision` | OPA policy evaluation result from `executive-agent`. Encodes allow/deny with violation explanations. |
| `skill-pipeline.schema.json` | `SkillPipeline` | Ordered sequence of `SkillStep`s produced by `agent-runtime`. Represents the cerebellar inverse-model execution plan. |

### Protobuf

| Directory | Contents |
|-----------|----------|
| `proto/` | Protobuf equivalents of the above JSON Schemas for high-throughput or polyglot serialisation. Lint with `cd shared && buf lint`. |

---

## Versioning Policy

- All schemas use JSON Schema Draft-07 (`$schema: http://json-schema.org/draft-07/schema#`).
- The `$id` for every schema follows the pattern `https://endogenai.accessitech.com/shared/schemas/<name>.schema.json`.
- Breaking changes (removing required fields, changing types) require a `CHANGELOG.md` entry and a semver bump in the affected schema's `version` property.
- Non-breaking additions (new optional fields) are allowed in patch releases.
- See `CHANGELOG.md` in this directory for the full schema change history.

---

## Usage

### TypeScript

```typescript
import Ajv from 'ajv';
import mcpContextSchema from '@accessitech/shared/schemas/mcp-context.schema.json';

const ajv = new Ajv();
const validate = ajv.compile(mcpContextSchema);
```

The `@accessitech/mcp` and `@accessitech/a2a` infrastructure packages bundle Ajv validators pre-compiled from these schemas — modules should use those rather than compiling directly.

### Python

```python
from endogenai_vector_store.models import MemoryItem  # derived from shared/types/
```

Python dataclasses are code-generated from the schemas in `shared/types/` (not this directory). Run `scripts/codegen_types.py` to regenerate.

---

## Adding a New Schema

1. Create `shared/schemas/<name>.schema.json` with a `$id`, `title`, `description`, and `version`.
2. Run `cd shared && buf lint` if adding a Protobuf companion under `proto/`.
3. Update this README's catalogue table.
4. Add a `CHANGELOG.md` entry.
5. Commit the schema **before** any implementation that depends on it (schemas-first rule).

---

## See Also

- [shared/types/](../types/README.md) — simplified type schemas used by Python modules
- [docs/protocols/mcp.md](../../docs/protocols/mcp.md) — MCPContext message format
- [docs/protocols/a2a.md](../../docs/protocols/a2a.md) — A2ATask / A2AMessage format
