# @accessitech/a2a — A2A Infrastructure

EndogenAI **Agent-to-Agent (A2A)** infrastructure: task orchestrator, JSON-RPC request handler, HTTP server with agent
card endpoint, and conformance test suite.

## Specification Version

| Item | Value |
| ---- | ----- |
| Spec | A2A Project |
| Release | **v0.3.0** |
| Tag commit | `2d3dc909972d9680b974e0fc9a1354c1ba8f519d` |
| Published | 2025-07-30 |
| URL | <https://github.com/a2aproject/A2A/releases/tag/v0.3.0> |

---

## Overview

A2A governs **direct communication between autonomous module agents** — task delegation, multi-agent orchestration, and
agent capability advertisement. It complements MCP: MCP carries context through the backbone; A2A structures the work
units (tasks) and their conversational history (messages).

| Component            | File                  | Responsibility                                                      |
| -------------------- | --------------------- | ------------------------------------------------------------------- |
| `TaskOrchestrator`   | `src/orchestrator.ts` | Full A2A task lifecycle: submit, startWork, complete, fail, cancel. |
| `A2ARequestHandler`  | `src/handler.ts`      | JSON-RPC 2.0 request dispatch for A2A task methods.                 |
| `createA2AServer`    | `src/server.ts`       | HTTP server: POST `/` (JSON-RPC), GET `/.well-known/agent-card.json`. |
| Types                | `src/types.ts`        | A2AMessage, A2ATask, Part types, AgentCard — from shared schemas.   |
| validate             | `src/validate.ts`     | Ajv-powered validation for A2AMessage and A2ATask.                  |

---

## Usage

### Start the A2A server

```typescript
import { createA2AServer } from '@accessitech/a2a';

const server = createA2AServer({
  agentCard: {
    id: 'working-memory',
    name: 'Working Memory Agent',
    version: '0.1.0',
    description: 'Manages the current-turn context window.',
    url: 'http://working-memory:8081',
    skills: [],
    mcp: { accepts: ['memory/item'], emits: ['memory/item'], version: '0.1.0' },
  },
});

const port = await server.listen(8081);
console.log(`A2A server listening on port ${port}`);
```

### JSON-RPC methods

| Method              | Params                              | Returns     |
| ------------------- | ----------------------------------- | ----------- |
| `tasks/send`        | `{ message?, requester?, ... }`     | `A2ATask`   |
| `tasks/get`         | `{ taskId: string }`                | `A2ATask`   |
| `tasks/cancel`      | `{ taskId: string }`                | `A2ATask`   |
| `tasks/addMessage`  | `{ taskId: string, message: A2AMessage }` | `A2ATask` |

### Task lifecycle

```
submitted → working → completed
                    → failed
                    → input-required → working
submitted → canceled
```

---

## Agent Card

`/.well-known/agent-card.json` is served automatically at startup. See
[`.well-known/agent-card.json`](.well-known/agent-card.json) for the infrastructure server's own card.

---

## Tests

```bash
pnpm run test
```

Runs:
- **Conformance tests** (`tests/conformance.test.ts`) — full task lifecycle and JSON-RPC protocol correctness
- **Server tests** (`tests/server.test.ts`) — HTTP endpoint integration

---

## Protocol Reference

See [`docs/protocols/a2a.md`](../../docs/protocols/a2a.md) for message format, task lifecycle, and agent identity
documentation.
