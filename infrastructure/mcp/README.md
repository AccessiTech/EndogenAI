# @accessitech/mcp — MCP Infrastructure

EndogenAI **Module Context Protocol (MCP)** infrastructure: context broker, capability registry, state synchroniser,
and MCP server built on [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk).

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

## MCP Tools (via @modelcontextprotocol/sdk)

| Tool name              | Arguments              | Effect                                          |
| ---------------------- | ---------------------- | ----------------------------------------------- |
| `register_capability`  | `Capability` object    | Registers module in registry, records heartbeat |
| `deregister_capability`| `{ moduleId: string }` | Removes module from registry and sync           |
| `publish_context`      | `MCPContext` object    | Routes message through the context broker       |
| `list_states`          | (none)                 | Returns all module sync states as JSON          |

## MCP Resources

- `mcp://capabilities/{moduleId}` — read a specific module's capability entry (JSON)
- `list_resources` — enumerates all registered modules

---

## Agent Card

`/.well-known/agent-card.json` — see [`.well-known/agent-card.json`](.well-known/agent-card.json).

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
