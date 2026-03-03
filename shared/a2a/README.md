---
id: shared-a2a
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-03-02
---

# Shared A2A

Client library packages for Agent-to-Agent (A2A) task delegation between EndogenAI cognitive modules.

## Purpose

`shared/a2a/` provides the approved outbound A2A client packages that cognitive modules use to delegate tasks to one another. Modules must use these packages rather than making raw HTTP calls to A2A endpoints, ensuring consistent JSON-RPC 2.0 framing, error handling, and timeout behaviour across the system.

This directory contains language-specific sub-packages. The Python sub-package (`endogenai-a2a`) is the primary consumer interface for all Group II and Group III Python modules.

---

## Sub-packages

| Directory | Package | Language | Status |
|-----------|---------|----------|--------|
| [`python/`](python/README.md) | `endogenai-a2a` | Python | Active — used by all Phase 5 modules |

---

## Python (`endogenai-a2a`)

The Python client wraps JSON-RPC 2.0 `tasks/send` and `tasks/get` over HTTP using `httpx`. All Group II cognitive modules (memory sub-modules, affective, reasoning) use this package instead of raw HTTP calls.

```python
from endogenai_a2a import A2AClient

client = A2AClient(url="http://localhost:8202", timeout=10.0)
result = await client.send_task("consolidate_item", {"item": item.model_dump()})
```

See [python/README.md](python/README.md) for the full interface, error handling, and configuration reference.

---

## See Also

- [infrastructure/a2a/](../../infrastructure/a2a/README.md) — TypeScript A2A server infrastructure (task orchestrator, JSON-RPC handler, HTTP server)
- [docs/protocols/a2a.md](../../docs/protocols/a2a.md) — A2A protocol specification
- [shared/schemas/a2a-task.schema.json](../schemas/a2a-task.schema.json) — canonical `A2ATask` schema
- [shared/schemas/a2a-message.schema.json](../schemas/a2a-message.schema.json) — canonical `A2AMessage` schema
