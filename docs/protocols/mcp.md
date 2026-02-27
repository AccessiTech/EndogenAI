---
id: protocol-mcp
version: 0.2.0
status: stable
last-reviewed: 2026-02-26
---

# MCP (Module Context Protocol) Integration Guide

> **Status: stable** \u2014 Full server implementation is live in `infrastructure/mcp/`. See
> [`infrastructure/mcp/README.md`](../../infrastructure/mcp/README.md) for usage.

Guide covering MCP message formats, context propagation, and capability discovery within the EndogenAI framework.

## Overview

MCP is the **communication backbone** of EndogenAI. Every message exchanged between modules — signals, memory requests,
decisions, rewards — travels as an `MCPContext` envelope. MCP is not a cognitive layer; it is cross-cutting
infrastructure that spans all groups.

All modules MUST:

- Accept inbound messages as `MCPContext` objects validated against
  [`shared/schemas/mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json).
- Emit outbound messages as `MCPContext` objects with the `source`, `contentType`, and `payload` fields populated.
- Propagate `traceContext` unchanged (see [Tracing Spec](../../shared/utils/tracing.md)).

---

## Message Format

Every MCP message is a JSON object conforming to
[`mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json).

### Minimal valid envelope

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "version": "0.1.0",
  "timestamp": "2026-02-26T12:00:00.000Z",
  "source": {
    "moduleId": "sensory-input",
    "layer": "sensory-input"
  },
  "contentType": "signal/text",
  "payload": {
    "text": "Hello, world."
  }
}
```

### Key fields

| Field           | Required | Description                                                                                       |
| --------------- | -------- | ------------------------------------------------------------------------------------------------- |
| `id`            | ✅       | UUID v4 — globally unique message ID.                                                             |
| `version`       | ✅       | Schema version in use (currently `"0.1.0"`).                                                      |
| `timestamp`     | ✅       | ISO 8601 UTC creation time.                                                                       |
| `source`        | ✅       | `ModuleRef` — originating module ID and architectural layer.                                      |
| `contentType`   | ✅       | MIME-like descriptor for `payload` (e.g. `"signal/text"`, `"memory/item"`, `"application/json"`). |
| `payload`       | ✅       | Message content — any JSON value. Structure governed by `contentType`.                            |
| `destination`   | ➖       | `ModuleRef` — target module. Omit for broadcast / registry-routed messages.                       |
| `traceContext`  | ➖       | W3C `traceparent` + optional `tracestate`. Required when a distributed trace is in scope.         |
| `correlationId` | ➖       | UUID — links a response message back to the originating request.                                  |
| `sessionId`     | ➖       | Cognitive session scope (maps to short-term memory TTL).                                          |
| `taskId`        | ➖       | Associates this message with an active A2A task.                                                  |
| `priority`      | ➖       | Integer 0–10 (default 5). Routing hint for the Attention & Filtering layer.                       |
| `metadata`      | ➖       | `Record<string, string>` — arbitrary annotations. No routing, security, or PII data.              |

### `contentType` conventions

| Value              | Use case                                                              |
| ------------------ | --------------------------------------------------------------------- |
| `signal/text`      | Raw or processed text signal                                          |
| `signal/image`     | Image signal (base64 or URI payload)                                  |
| `signal/audio`     | Audio chunk signal                                                    |
| `signal/api-event` | Incoming API / webhook event                                          |
| `memory/item`      | `MemoryItem` payload (see `shared/types/memory-item.schema.json`)     |
| `reward/signal`    | `RewardSignal` payload (see `shared/types/reward-signal.schema.json`) |
| `application/json` | Generic structured JSON                                               |
| `text/plain`       | Unstructured text                                                     |

---

## Context Propagation

Every module that receives an `MCPContext` MUST:

1. Validate the envelope against the JSON Schema before processing.
2. Extract `traceContext.traceparent` and create a child span (see [Tracing Spec](../../shared/utils/tracing.md)).
3. Emit a structured log record for the receipt event, carrying `traceId` and `spanId` (see
   [Logging Spec](../../shared/utils/logging.md)).
4. Populate the outbound `MCPContext` with:
   - A fresh `id` (new UUID v4).
   - Its own `source` identity.
   - The updated `traceparent` (new `spanId`, same `traceId`).
   - The same `correlationId` if this is a response; a new one if originating a new request chain.

### Propagation diagram

```
Sensory Input         Attention Layer        Perception
──────────────        ───────────────        ──────────
Create traceId   ───► Validate schema   ───► Validate schema
Create spanId         Extract trace          Extract trace          ...
Emit MCPContext       Create child span      Create child span
                      Emit MCPContext         Emit MCPContext
```

---

## Capability Discovery

Each module advertises its MCP capabilities via a `capabilities` block in its `agent-card.json` (see
[A2A Protocol Guide](a2a.md)). The `CapabilityRegistry` (see Phase 2 Implementation below) reads these cards at
startup to build the routing table.

Capability advertisement shape:

```json
{
  "mcp": {
    "accepts": ["signal/text", "signal/image"],
    "emits": ["memory/item"],
    "version": "0.1.0"
  }
}
```

---

## Phase 2 Implementation

The `infrastructure/mcp/` package (`@accessitech/mcp`) provides the complete MCP infrastructure:

| Export | Description |
| --- | --- |
| `createMCPServer(agentCard)` | Returns an `{ server, broker, registry, sync, close }` bundle. Registers four tools and one resource on the MCP SDK server. |
| `ContextBroker` | Routes `MCPContext` messages — `route()` for directed delivery, `broadcast()` for fan-out, `buildReply()` for correlated responses. |
| `CapabilityRegistry` | Map-backed capability store. `register()`, `deregister()`, `getByContentType()`, `list()`. |
| `StateSynchronizer` | Tracks `ModuleState` with heartbeat timestamps. `updateState()`, `getState()`, `pruneStale()`, `listAll()`. |
| `validateMCPContext()` / `isMCPContext()` | Ajv-based validation against `mcp-context.schema.json`. |

### MCP Server Tools

| Tool name | Description |
| --- | --- |
| `register_capability` | Register a module capability (contentType, layer, name). |
| `deregister_capability` | Remove a capability by id. |
| `publish_context` | Publish an `MCPContext` object through the broker. |
| `list_states` | List current module states tracked by the synchronizer. |

### MCP Server Resources

| Resource URI | Description |
| --- | --- |
| `mcp://capabilities/{moduleId}` | Returns all capabilities registered by the specified module. |

### Quick start

```typescript
import { createMCPServer } from '@accessitech/mcp';

const agentCard = { id: 'my-module', name: 'My Module', version: '0.1.0', description: '...', url: 'http://my-module:8080', skills: [] };
const { server, broker, registry, sync, close } = createMCPServer(agentCard);

// route an MCPContext
await broker.route(context);

// register a capability
registry.register({ id: 'cap-1', moduleId: 'my-module', name: 'text-in', contentType: 'signal/text', layer: 'sensory-input' });
```

See [`infrastructure/mcp/README.md`](../../infrastructure/mcp/README.md) for the full API reference.

---

## Validation

All modules MUST validate inbound `MCPContext` objects against
[`mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json) before processing. See
[Validation Spec](../../shared/utils/validation.md) for language-specific patterns, error handling contract, and size
limits.

---

## References

- [MCP Context Schema](../../shared/schemas/mcp-context.schema.json)
- [Signal Schema](../../shared/types/signal.schema.json)
- [MemoryItem Schema](../../shared/types/memory-item.schema.json)
- [RewardSignal Schema](../../shared/types/reward-signal.schema.json)
- [Tracing Spec](../../shared/utils/tracing.md)
- [Logging Spec](../../shared/utils/logging.md)
- [Validation Spec](../../shared/utils/validation.md)
- [A2A Protocol Guide](a2a.md)
- [Architecture Overview](../architecture.md)
- [Workplan — Phase 2](../Workplan.md#phase-2--communication-infrastructure-mcp--a2a)
