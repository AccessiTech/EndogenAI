# @accessitech/adapters — MCP + A2A Adapter Bridge

Adapter bridge enabling EndogenAI modules to participate in both **MCP context exchange** and **A2A task delegation**
without duplicated logic.

---

## Purpose

`@accessitech/adapters` provides the `MCPToA2ABridge` — the sole permitted pathway for cross-module communication in EndogenAI. It routes inbound A2A tasks over MCP to the target module, then automatically completes the A2A task when the target module publishes an MCP reply carrying the matching `taskId`. No cognitive module communicates directly with another via raw HTTP; all cross-module calls pass through this bridge, which composes `@accessitech/mcp` and `@accessitech/a2a`.

---

## Overview

The adapter bridge (`MCPToA2ABridge`) connects the two communication protocols:

```
A2A task (user/agent message)
        │
        ▼
  MCPToA2ABridge.sendAndRoute()
        │
        ├─── Creates A2A task (TaskOrchestrator)
        │
        └─── Publishes MCPContext (ContextBroker) ──► module handler
                                                              │
                                                              │ reply MCPContext
                                                              ▼
                                                    MCPToA2ABridge (subscriber)
                                                              │
                                                              └─► Completes A2A task
                                                                  with reply as artifact
```

| Direction | What happens |
| --------- | ------------ |
| A2A → MCP | `sendAndRoute` submits an A2A task, transitions to `working`, wraps the initial message in an `MCPContext`, and publishes it to the context broker. |
| MCP → A2A | The bridge subscribes to MCP replies for `replyTargetModuleId`. On receipt, if the context carries a `taskId`, the referenced A2A task is completed with the reply payload as an artifact. |

---

## Architecture

```
           ┌──────────────────────────────────────────────┐
  A2A task │  MCPToA2ABridge.sendAndRoute()               │
──────────►│  1. TaskOrchestrator.submit()                │
           │  2. broker.publish(MCPContext → target)      │
           │                                              │
           │  On MCP reply addressed to replyTargetModule:│
           │  3. orchestrator.complete(taskId, reply)     │◄── MCP reply
           └──────────────────────────────────────────────┘
```

The bridge is stateless beyond the `ContextBroker` subscription and `TaskOrchestrator` reference provided at construction. It can be instantiated multiple times to bridge different module pairs.

---

## Installation

```bash
pnpm add @accessitech/adapters
```

---

## Usage

```typescript
import { createMCPServer } from '@accessitech/mcp';
import { TaskOrchestrator } from '@accessitech/a2a';
import { MCPToA2ABridge } from '@accessitech/adapters';

const { broker, registry } = createMCPServer();
const orchestrator = new TaskOrchestrator();

const bridge = new MCPToA2ABridge(broker, orchestrator, {
  source: { moduleId: 'perception', layer: 'signal-processing' },
  replyTargetModuleId: 'perception-reply',
});

// Subscribe a module handler to MCP
broker.subscribe('working-memory', async (ctx) => {
  // Process ctx.payload ...
  // Reply back through the broker
  const reply = broker.buildReply(ctx, { moduleId: 'working-memory', layer: 'cognitive-processing' }, 'application/json', { stored: true });
  await broker.publish(reply);  // This auto-completes the A2A task
});

// Send a task — it auto-routes through MCP to the working-memory module
const { taskId, contextId, task } = await bridge.sendAndRoute({
  message: {
    id: 'msg-uuid',
    role: 'user',
    parts: [{ type: 'text', text: 'Store this.' }],
    timestamp: new Date().toISOString(),
  },
  sessionId: 'session-1',
});

console.log('Task:', taskId, '| Context:', contextId);
```

---

## API

### `MCPToA2ABridge`

```typescript
class MCPToA2ABridge {
  constructor(
    broker: ContextBroker,
    orchestrator: TaskOrchestrator,
    config: BridgeConfig,
  );

  /** Submit an A2A task and route its initial message as an MCPContext to the target module. */
  sendAndRoute(options: SendAndRouteOptions): Promise<{
    taskId: string;
    contextId: string;
    task: A2ATask;
  }>;
}
```

See the `BridgeConfig` type definition in [Configuration](#configuration) and `src/bridge.ts` for the full source.

---

## Configuration

```typescript
interface BridgeConfig {
  /** Module identity the bridge uses when publishing MCP context messages. */
  source: { moduleId: string; layer: string };

  /**
   * Module ID the bridge subscribes to for inbound MCP replies.
   * Replies addressed to this module with a taskId are auto-completed.
   */
  replyTargetModuleId: string;

  /** Content type for wrapped A2A messages (default: 'application/json'). */
  contentType?: string;
}
```

---

## Agent Card

`/.well-known/agent-card.json` — see [`.well-known/agent-card.json`](.well-known/agent-card.json).

---

## Running locally

```bash
# From the infrastructure/adapters package directory
pnpm install
pnpm run build

# Start backing services
docker compose up -d

# Run round-trip integration tests
pnpm run test
```

---

## Tests

```bash
pnpm run test
```

Runs round-trip integration tests covering:
- A2A → MCP publish path
- MCP reply → A2A task completion path
- Edge cases: no taskId, completed task idempotency, sessionId propagation

---

## Dependencies

- [`@accessitech/mcp`](../mcp/README.md) — `ContextBroker`, `CapabilityRegistry`, `StateSynchronizer`
- [`@accessitech/a2a`](../a2a/README.md) — `TaskOrchestrator`, types
