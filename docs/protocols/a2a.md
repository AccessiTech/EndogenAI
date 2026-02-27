---
id: protocol-a2a
version: 0.2.0
status: stable
last-reviewed: 2026-02-26
---

# A2A Protocol Guide

> **Status: stable** \u2014 Full server implementation is live in `infrastructure/a2a/`. See
> [`infrastructure/a2a/README.md`](../../infrastructure/a2a/README.md) for usage.
>
> **Specification Version**: A2A v0.3.0 (commit `2d3dc909972d9680b974e0fc9a1354c1ba8f519d`)

Guide covering A2A agent identity, message parts, task lifecycle, and the MCP + A2A interoperability model.

## Overview

A2A (Agent-to-Agent) governs **direct communication between autonomous module agents** — task delegation, multi-agent
orchestration, and agent capability advertisement. It complements MCP: MCP carries all context through the backbone; A2A
structures the work units (tasks) and their conversational history (messages).

All agent modules MUST:

- Expose an `agent-card.json` describing identity, skills, and MCP capability block.
- Accept and emit `A2AMessage` objects conforming to
  [`shared/schemas/a2a-message.schema.json`](../../shared/schemas/a2a-message.schema.json).
- Manage task lifecycle via `A2ATask` objects conforming to
  [`shared/schemas/a2a-task.schema.json`](../../shared/schemas/a2a-task.schema.json).

---

## Agent Identity

Each agent is identified by an `AgentRef`:

```json
{
  "id": "working-memory",
  "name": "Working Memory Agent",
  "url": "http://working-memory:8080"
}
```

| Field  | Required | Description                                             |
| ------ | -------- | ------------------------------------------------------- |
| `id`   | ✅       | Canonical module identifier (e.g. `"working-memory"`).  |
| `name` | ➖       | Human-readable display name for the agent.              |
| `url`  | ➖       | Base URL for the agent's A2A endpoint (set in Phase 2). |

### `agent-card.json`

Each module exposes a static `agent-card.json` file at `/.well-known/agent-card.json`. It is the source of truth for
the agent's identity and capabilities. The required minimum is:

```json
{
  "id": "working-memory",
  "name": "Working Memory Agent",
  "version": "0.1.0",
  "description": "Manages the current-turn context window and consolidation pipeline.",
  "url": "http://working-memory:8080",
  "skills": [],
  "mcp": {
    "accepts": ["memory/item", "signal/text"],
    "emits": ["memory/item"],
    "version": "0.1.0"
  }
}
```

---

## Message Format

An `A2AMessage` is one exchange unit within a task conversation. Its content is an ordered array of typed **parts**.

### Minimal valid message

```json
{
  "id": "7f3e4a20-0c1b-4d8e-82f6-9a4b1c3d5e7f",
  "role": "agent",
  "parts": [
    {
      "type": "text",
      "text": "I have stored the memory item."
    }
  ],
  "timestamp": "2026-02-26T12:01:00.000Z"
}
```

### Part types

| Type              | Key fields                                 | Use case                                             |
| ----------------- | ------------------------------------------ | ---------------------------------------------------- |
| `text`            | `text`, `mimeType`                         | Plain text or markdown responses                     |
| `data`            | `data`, `schema`                           | Structured JSON payload (validated against `schema`) |
| `file`            | `file.mimeType`, `file.uri` / `file.bytes` | Images, audio clips, documents                       |
| `function_call`   | `functionCall.id`, `name`, `args`          | Tool invocation request from the agent               |
| `function_result` | `functionResult.id`, `name`, `response`    | Tool invocation result                               |

All part types are defined in [`a2a-message.schema.json`](../../shared/schemas/a2a-message.schema.json).

---

## Task Lifecycle

A **Task** is the top-level work unit. It aggregates a message history and tracks state through a defined state machine.

### State machine

```
           ┌─────────────────┐
           │   submitted    │
           └──────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │    working     │◄─────────┐
           └─┬─────┬─────┘         │
             │         │               │
    ┌─────┘         └──────┐        │
    ▼                       ▼        │
┌───────────┐   ┌───────────────┐  │
│ completed │   │input-required │─┘
└───────────┘   └───────────────┘
    ▲                   ▲
┌─────────┐   ┌─────────┐
│  failed  │   │ canceled │
└─────────┘   └─────────┘
```

| State            | Terminal | Description                                                 |
| ---------------- | -------- | ----------------------------------------------------------- |
| `submitted`      | ❌       | Task accepted; not yet picked up by an agent.               |
| `working`        | ❌       | Agent is actively processing the task.                      |
| `input-required` | ❌       | Agent needs additional user or system input to proceed.     |
| `completed`      | ✅       | Task finished successfully; `artifacts` array is populated. |
| `failed`         | ✅       | Unrecoverable error; `error` object is populated.           |
| `canceled`       | ✅       | Task was explicitly canceled by the requester.              |

### Task artifacts

Completed tasks carry an `artifacts` array. Each artifact has a unique `id`, a `name`, and the same typed `parts`
structure as `A2AMessage`. Modules downstream of a completed task MUST validate artifact structure before consumption.

### Error handling

Failed tasks carry a `TaskError` object with `code`, `message`, `retryable`, and optional `details`.

| Error code          | Meaning                                              | Retryable |
| ------------------- | ---------------------------------------------------- | --------- |
| `timeout`           | Agent did not respond within the configured deadline | ✅        |
| `agent-unavailable` | Target agent is not registered / unreachable         | ✅        |
| `invalid-input`     | Task input failed schema validation                  | ❌        |
| `unauthorized`      | Requester lacks permission for the requested skill   | ❌        |
| `internal-error`    | Unexpected error inside the agent                    | ❌        |

---

## MCP + A2A Interoperability Model

- **MCP** carries all context through the system backbone (`MCPContext` envelope). It is the default communication path
  for all inter-module signals.
- **A2A** structures discrete **tasks** — units of work with a start, a conversation history, and a terminal state. A2A
  messages travel _inside_ MCP context envelopes when routed through the backbone:

  ```json
  {
    "contentType": "application/json",
    "payload": { "$ref": "A2AMessage" },
    "taskId": "<a2a-task-id>"
  }
  ```

- Modules that only exchange signals (perception, memory reads) use MCP alone.
- Modules that act as autonomous agents (Executive, Decision-Making) use A2A for task delegation and use MCP for context
  propagation around those tasks.

---

## Phase 2 Implementation

The `infrastructure/a2a/` package (`@accessitech/a2a`) provides the complete A2A infrastructure.

**Specification Version:** A2A v0.3.0 — commit `2d3dc909972d9680b974e0fc9a1354c1ba8f519d` (2025-07-30)

| Export | Description |
| --- | --- |
| `createA2AServer(agentCard, options?)` | Creates an HTTP server with `GET /.well-known/agent-card.json` and `POST /` (JSON-RPC). Returns `{ server, handler, orchestrator, listen, close }`. |
| `TaskOrchestrator` | Manages task lifecycle: `submit()`, `startWork()`, `addMessage()`, `requestInput()`, `complete()`, `fail()`, `cancel()`. Enforces terminal-state guard. |
| `A2ARequestHandler` | JSON-RPC dispatcher for `tasks/send`, `tasks/get`, `tasks/cancel`, `tasks/addMessage`. |
| `validateA2AMessage()` / `validateA2ATask()` | Ajv-based validation against the canonical schemas. |

### JSON-RPC Methods

| Method | Description |
| --- | --- |
| `tasks/send` | Submit a new task (auto-transitions to `working`). |
| `tasks/get` | Retrieve current task state and message history. |
| `tasks/cancel` | Cancel a non-terminal task. |
| `tasks/addMessage` | Append a message to an existing task. |

### Quick start

```typescript
import { createA2AServer } from '@accessitech/a2a';

const agentCard = { id: 'memory', name: 'Memory Agent', version: '0.1.0', description: '...', url: 'http://memory:8080', skills: [] };
const { listen, close } = createA2AServer(agentCard);

const { port } = await listen(); // binds to a random port unless options.port is specified
console.log(`A2A server listening on port ${port}`);
```

See [`infrastructure/a2a/README.md`](../../infrastructure/a2a/README.md) for the full API reference.

The `infrastructure/adapters/` package (`@accessitech/adapters`) provides the `MCPToA2ABridge` that connects both
protocols — see [`infrastructure/adapters/README.md`](../../infrastructure/adapters/README.md).

---

## Validation

All modules MUST validate inbound `A2AMessage` and `A2ATask` objects against their schemas before processing. See
[Validation Spec](../../shared/utils/validation.md) for language-specific patterns, error handling, and size limits.

Additionally, state transition validation is **semantic** (not covered by JSON Schema alone) — modules MUST reject
transitions that violate the state machine defined above.

---

## References

- [A2AMessage Schema](../../shared/schemas/a2a-message.schema.json)
- [A2ATask Schema](../../shared/schemas/a2a-task.schema.json)
- [MCP Context Schema](../../shared/schemas/mcp-context.schema.json)
- [Validation Spec](../../shared/utils/validation.md)
- [Tracing Spec](../../shared/utils/tracing.md)
- [MCP Protocol Guide](mcp.md)
- [Architecture Overview](../architecture.md)
- [A2A Project Specification](https://github.com/a2aproject/A2A)
- [Workplan — Phase 2](../Workplan.md#phase-2--communication-infrastructure-mcp--a2a)
