---
id: spec-validation
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Input Sanitization & Boundary Validation Patterns

> **Applies to**: all EndogenAI modules (Python and TypeScript). This document is part of the _Security & Privacy by
> Design_ and _Robustness and Fault Tolerance_ guiding principles.

Every module boundary in EndogenAI is a potential attack surface. This document specifies the mandatory validation and
sanitization patterns that all modules MUST apply when processing inbound data.

---

## 1. Principle: Validate at Every Boundary

Validation must happen **before** any processing occurs. The rule is:

> **Never trust data that crosses a module boundary.**

This applies to:

- Inbound `Signal` payloads from the Application / Sensory layers.
- Inbound `MCPContext` messages from any module.
- Inbound `A2AMessage` and `A2ATask` objects from peer agents.
- External API responses, webhook payloads, database reads, and file system reads.
- LLM outputs (route through LiteLLM; validate returned structured data against the expected schema).

---

## 2. Validation Layers

### 2.1 Schema Validation (Structural)

All inbound JSON payloads MUST be validated against the relevant JSON Schema before use. Use the shared schemas \
located in `shared/schemas/` and `shared/types/`:

| Schema                                                            | Applied at                               |
| ----------------------------------------------------------------- | ---------------------------------------- |
| [`mcp-context.schema.json`](../schemas/mcp-context.schema.json)   | MCP broker, all module MCP handlers      |
| [`a2a-message.schema.json`](../schemas/a2a-message.schema.json)   | A2A request handler                      |
| [`a2a-task.schema.json`](../schemas/a2a-task.schema.json)         | A2A task orchestrator                    |
| [`signal.schema.json`](../types/signal.schema.json)               | Sensory Input, Attention & Filtering     |
| [`memory-item.schema.json`](../types/memory-item.schema.json)     | All memory modules, vector store adapter |
| [`reward-signal.schema.json`](../types/reward-signal.schema.json) | Affective Layer, Learning & Adaptation   |

**Python** — use [`jsonschema`](https://python-jsonschema.readthedocs.io/) or [`pydantic`](https://docs.pydantic.dev/)
v2 (preferred for typed integration):

```python
from pydantic import BaseModel, ValidationError

class SignalModel(BaseModel):
    id: str
    type: str
    modality: str
    # ... (generated from JSON Schema or hand-authored)

try:
    signal = SignalModel.model_validate(raw_dict)
except ValidationError as exc:
    log.error("invalid_signal", error={"type": "ValidationError", "message": str(exc)})
    raise
```

**TypeScript** — use [`ajv`](https://ajv.js.org/) (preferred) or [`zod`](https://zod.dev/):

```typescript
import Ajv from "ajv";
import signalSchema from "../../shared/types/signal.schema.json";

const ajv = new Ajv({ strict: true });
const validate = ajv.compile(signalSchema);

if (!validate(rawSignal)) {
  throw new ValidationError("Invalid signal", validate.errors);
}
```

### 2.2 Semantic Validation (Business Rules)

After schema validation, apply semantic checks. Examples:

- `Signal.timestamp` MUST NOT be in the future (clock skew > 5 seconds is rejected).
- `MemoryItem.ttl` MUST be > 0 for `short-term` type items.
- `RewardSignal.value` MUST be in `[-1.0, 1.0]` (enforced by schema but re-check before use in ML pipelines).
- `A2ATask.status.state` transitions MUST follow the allowed graph:
  `submitted → working → {completed | failed | canceled | input-required}`.
- UUIDs (all `id` fields) MUST be valid UUID v4 format.
- `collectionName` in `MemoryItem` MUST match the prefix `brain.` (enforced by schema regex).

### 2.3 Content Sanitization

Apply sanitization rules to untrusted string content **before** it is used in any downstream operation:

| Context                    | Rule                                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Prompt injection           | Strip or escape common injection tokens (`<                                                                | `, `</s>`, `[INST]`, `###`) from user-supplied text before embedding in LLM prompts. |
| HTML / markdown output     | Sanitize with an allowlist (e.g. DOMPurify for TS, `bleach` for Python) before rendering to a UI.          |
| File paths                 | Normalize and validate against an allowlist of directories; reject `..` path traversal.                    |
| URLs                       | Parse and validate scheme against `["http", "https"]`; reject `javascript:`, `data:`, `file:` schemes.     |
| Shell commands             | Do not construct commands from user-supplied data. Use parameterized subprocess calls with argument lists. |
| SQL / vector store queries | Use parameterized queries only; never interpolate user data into query strings.                            |

---

## 3. Error Handling Contract

When validation fails, the module MUST:

1. **Log** the failure at `WARN` or `ERROR` level with the `error` field populated (see [Logging Spec](./logging.md)).
2. **Reject** the message — return an error response or drop the signal (do not silently corrupt state).
3. **Never** expose raw validation error details to external callers in production. Use generic error messages
   externally; log the full detail internally.
4. **Propagate** the `traceId` in the error response so the failure can be correlated in the observability stack.

```python
# Python — ValidationError response pattern
def _reject(trace_id: str, code: str, message: str) -> dict:
    return {
        "error": {"code": code, "message": message},
        "traceId": trace_id,
    }
```

```typescript
// TypeScript — ValidationError response pattern
function reject(traceId: string, code: string, message: string) {
  return { error: { code, message }, traceId };
}
```

---

## 4. Size & Rate Limits

All module boundaries MUST enforce the following defaults (configurable per module via environment variables):

| Limit                   | Default     | Env Var                     |
| ----------------------- | ----------- | --------------------------- |
| Max JSON payload        | 1 MB        | `ENDOGEN_MAX_PAYLOAD_BYTES` |
| Max string field length | 32 KB       | `ENDOGEN_MAX_STRING_BYTES`  |
| Max array length        | 1 000 items | `ENDOGEN_MAX_ARRAY_LENGTH`  |
| Max metadata keys       | 50          | `ENDOGEN_MAX_METADATA_KEYS` |

Reject any payload that exceeds these limits with a `payload-too-large` error code before attempting JSON parsing.

---

## 5. LLM Output Validation

All LLM inference routes through **LiteLLM** (no direct SDK calls). When a module expects structured output from an LLM:

1. Request structured output using the model's JSON mode or response schema feature (via LiteLLM).
2. **Always** validate the returned JSON against the expected schema (§2.1) before acting on it.
3. If validation fails: retry up to `ENDOGEN_LLM_VALIDATION_RETRIES` (default: 2) times with an error-correcting prompt,
   then escalate as an `internal-error`.

---

## 6. Dependency Checklist (per module)

Before a module can be considered _boundary-hardened_, the following MUST be in place:

- [ ] All inbound message types validated against their JSON Schemas.
- [ ] Semantic validation rules documented in the module's `README.md`.
- [ ] `ENDOGEN_MAX_PAYLOAD_BYTES` limit enforced.
- [ ] Prompt injection mitigation applied to all user-originated text fields.
- [ ] Validation error logs include `traceId` and structured `error` object.
- [ ] No raw validation error details leaked to external callers.
- [ ] Unit tests cover at least: valid input, missing required field, oversized payload, invalid enum value.

---

## References

- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OWASP Prompt Injection](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [AJV Documentation](https://ajv.js.org/)
- [Security Guide](../../docs/guides/security.md)
- [Logging Spec](./logging.md)
- [Tracing Spec](./tracing.md)
