---
id: guide-security
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Security

> **Status: draft** — Boundary validation patterns are defined (Phase 1). Sandboxing policies and container-level
> security will be documented in Phase 8.

Security model, boundary validation, sandboxing policies, and least-privilege patterns.

## Principles

- **Security & Privacy by Design** — security is a first-class concern at every layer boundary
- **Least Privilege** — each module operates with the minimum permissions required
- **Module Sandboxing** — modules are isolated via container-level policies
- **Validate at Every Boundary** — never trust data that crosses a module boundary (see below)

## Boundary Validation (Phase 1)

The canonical input validation and sanitization patterns are defined in
[`shared/utils/validation.md`](../../shared/utils/validation.md).

Key rules that apply to every module:

1. **Schema validation first** — validate all inbound JSON against the shared schemas in `shared/schemas/` and
   `shared/types/` before any processing.
2. **Content sanitization** — strip prompt injection tokens from user-supplied text; sanitize HTML output; validate URL
   schemes; use parameterized queries only.
3. **Size limits** — reject payloads exceeding `ENDOGEN_MAX_PAYLOAD_BYTES` (default: 1 MB) before parsing.
4. **LLM output validation** — all LLM inference routes through LiteLLM; always validate structured LLM output against
   the expected schema.
5. **Error handling** — log full detail internally (with `traceId`); return only generic error messages to callers.

See [Validation Spec](../../shared/utils/validation.md) for the full language-specific patterns and the per-module
boundary-hardening checklist.

## Module Sandboxing

_OPA policies and gVisor sandbox templates to be added in Phase 8 (`security/`)._

## Inter-Module Interface Review

_Security review of all inter-module interfaces to be conducted in Phase 8._

## References

- [Validation Spec](../../shared/utils/validation.md)
- [Architecture Overview](../architecture.md)
- [Workplan — Phase 8](../Workplan.md#phase-8--cross-cutting-security-deployment--documentation)
