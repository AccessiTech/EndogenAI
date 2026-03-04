# @accessitech/mcp — MCP Infrastructure

EndogenAI **Module Context Protocol (MCP)** infrastructure: context broker, capability registry, state synchroniser,
and MCP server built on [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk).

---

## Purpose

`@accessitech/mcp` is the context-routing backbone for the entire EndogenAI system. All synchronous module-to-module communication travels as an `MCPContext` envelope validated against [`shared/schemas/mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json) and dispatched through this package's `ContextBroker`. No cognitive module may address another directly — all cross-module messages must be published through the broker. This package is the TypeScript implementation of the [Module Context Protocol](../../docs/protocols/mcp.md).

---

## Overview

The MCP infrastructure is the communication backbone of EndogenAI. Every message exchanged between cognitive modules
travels as an `MCPContext` envelope conforming to
[`shared/schemas/mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json).

This package provides:

| Component            | File               | Responsibility                                                          |
| -------------------- | ------------------ | ----------------------------------------------------------------------- |
| `CapabilityRegistry` | `src/registry.ts`  | Module capability store — accepts/emits, versions, and endpoint URLs.   |
| `StateSynchronizer`  | `src/sync.ts`      | Runtime module state and heartbeat tracking.                            |
| `ContextBroker`      | `src/broker.ts`    | Validates and routes `MCPContext` messages to registered handlers.      |
| `createMCPServer`    | `src/server.ts`    | Factory that wires the above into an MCP server via `@modelcontextprotocol/sdk`. |
| `validateMCPContext` | `src/validate.ts`  | Ajv-powered schema validation against the canonical MCP context schema. |

---

## Architecture

The MCP infrastructure follows a publish/subscribe topology. `ContextBroker` is the central hub; all other components are wired to it by `createMCPServer`:

```
Module A
  │  broker.publish(MCPContext)
  ▼
ContextBroker ── validateMCPContext (Ajv schema guard)
  │
  ├── CapabilityRegistry  (endpoint + capability lookup, heartbeat)
  ├── StateSynchronizer   (module liveness tracking)
  └── Subscribed handler → Module B
                              │
                              ▼  broker.publish(reply)
                          ContextBroker → Module A subscriber
```

The `createMCPServer` factory wraps this topology behind `@modelcontextprotocol/sdk` tools and resources so external callers interact via the standard MCP wire protocol.

---

## Installation

```bash
pnpm add @accessitech/mcp
```

---

## Usage

### Start the MCP server

```typescript
import { createMCPServer } from '@accessitech/mcp';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const { server, registry, broker, sync } = createMCPServer({
  name: 'endogenai-mcp',
  version: '0.1.0',
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Register a module's capabilities

```typescript
registry.register({
  moduleId: 'sensory-input',
  layer: 'signal-processing',
  accepts: ['signal/text', 'signal/image'],
  emits: ['memory/item'],
  version: '0.1.0',
  url: 'http://sensory-input:8080',
});
```

### Publish and subscribe to context messages

```typescript
// Subscribe
broker.subscribe('working-memory', async (ctx) => {
  console.log('Received:', ctx.contentType, ctx.payload);
});

// Publish (validates against MCPContext schema)
await broker.publish({
  id: '550e8400-e29b-41d4-a716-446655440000',
  version: '0.1.0',
  timestamp: new Date().toISOString(),
  source: { moduleId: 'sensory-input', layer: 'signal-processing' },
  destination: { moduleId: 'working-memory', layer: 'cognitive-processing' },
  contentType: 'signal/text',
  payload: { text: 'Hello, world.' },
});
```

### Build a reply

```typescript
const reply = broker.buildReply(
  original,
  { moduleId: 'working-memory', layer: 'cognitive-processing' },
  'memory/item',
  { id: '...', content: '...' },
);
await broker.publish(reply);
```

---

## API

`@accessitech/mcp` exposes its interface as `@modelcontextprotocol/sdk` tools and resources. All calls are validated against the canonical MCP context schema before routing. See **MCP Tools** and **MCP Resources** below for the complete programmatic surface.

---

## MCP Tools (via @modelcontextprotocol/sdk)

| Tool name              | Arguments              | Effect                                          |
| ---------------------- | ---------------------- | ----------------------------------------------- |
| `register_capability`  | `Capability` object    | Registers module in registry, records heartbeat |
| `deregister_capability`| `{ moduleId: string }` | Removes module from registry and sync           |
| `publish_context`      | `MCPContext` object    | Routes message through the context broker       |
| `list_states`          | (none)                 | Returns all module sync states as JSON          |

## MCP Resources

| Resource URI | Description |
| --- | --- |
| `mcp://capabilities/{moduleId}` | Returns all capabilities registered by the specified module. |
| `brain://` URIs _(Phase 8.5)_ | Module-level cognitive resources (working-memory context, signal traces, etc.). Registered via `resources/uri-registry.json`; served via `resources/list`, `resources/read`, and `resources/subscribe` JSON-RPC handlers added in Phase 8.5. |

---

## Phase 8 Additions

Phase 8 adds the following routes and handlers to `infrastructure/mcp` — tracked in
[`docs/Workplan.md §8.2`](../../docs/Workplan.md#82-mcp-oauth-21-auth-layer) and
[`docs/Workplan.md §8.5`](../../docs/Workplan.md#85-mcp-resource-registry-resources):

### `GET /.well-known/oauth-protected-resource` _(Phase 8.2)_

RFC 9728 requires the Protected Resource Metadata endpoint to be served **by the resource server** (this package),
not the gateway. Once added to `src/`, it returns:

```json
{
  "resource": "<MCP_SERVER_URI>",
  "authorization_servers": ["http://localhost:3001"]
}
```

This is a Gate 1 prerequisite for the OAuth auth stub in `apps/default/server/src/auth/`.

### `resources/list`, `resources/read`, `resources/subscribe` _(Phase 8.5)_

MCP JSON-RPC handlers that serve `brain://` URI resources from `resources/uri-registry.json`.
`resources/subscribe` is required for the browser Internals tab panels:
- `brain://group-ii/working-memory/context/current` — Working Memory Inspector
- `brain://group-iv/metacognition/confidence/current` — Confidence Scores panel

### External transport note

The Phase 8 Hono gateway connects to this server over the **MCP Streamable HTTP transport**
(spec 2025-06-18): `POST /mcp` with `Content-Type: application/json` and
`MCP-Protocol-Version: 2025-06-18` header; `GET /mcp` for server-side push SSE. The gateway's
`src/mcp-client.ts` manages `Mcp-Session-Id` and `Last-Event-ID` headers for session continuity.

---

## Agent Card

`/.well-known/agent-card.json` — see [`.well-known/agent-card.json`](.well-known/agent-card.json).

---

## Running locally

```bash
# From the infrastructure/mcp package directory
pnpm install
pnpm run build

# Start backing services (ChromaDB, Ollama, OTel collector)
docker compose up -d

# Run all tests
pnpm run test
```

---

## Tests

```bash
pnpm run test
```

Runs unit tests for `CapabilityRegistry`, `ContextBroker`, `StateSynchronizer`, and integration tests for
`createMCPServer`.

---

## Protocol Reference

See [`docs/protocols/mcp.md`](../../docs/protocols/mcp.md) for message format, context propagation rules, and
`contentType` conventions.
