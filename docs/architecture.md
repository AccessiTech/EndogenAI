---
id: architecture
version: 0.1.0
status: draft
last-reviewed: 2026-02-26
---

# Architecture

> **Status: draft** — Shared contract layer documented (Phase 1). Signal-flow diagrams and per-layer implementation
> detail will be added as phases deliver live modules.

Full architectural overview of the EndogenAI framework, including layer descriptions, shared contracts, and signal flow.

## Overview

EndogenAI is organized into layered groups that mirror the brain's bottom-up signal processing, bidirectional cognitive
feedback, and adaptive learning. MCP and A2A are **cross-cutting infrastructure** — they are not sequential layers but
rather a communication backbone that spans all groups.

Information flows **bottom-up** (Input → Perception → Cognition → Action) for stimulus-driven processing, and
**top-down** (Executive → Decision-Making → Attention → Sensory) for goal-directed modulation.

---

## Layers

### Group I — Signal Processing

| Module                | Analogy              | Key output                                               |
| --------------------- | -------------------- | -------------------------------------------------------- |
| Sensory / Input       | Sensory cortices     | Raw `Signal` envelopes                                   |
| Attention & Filtering | Thalamus             | Gated, prioritised `Signal` stream                       |
| Perception            | Association cortices | Feature-extracted `Signal`; embeds to `brain.perception` |

### Group II — Cognitive Processing

| Module                      | Analogy                   | Key output                                                            |
| --------------------------- | ------------------------- | --------------------------------------------------------------------- |
| Working Memory              | Prefrontal working buffer | Assembled context window                                              |
| Short-Term Memory           | Hippocampal session state | Session-scoped `MemoryItem` store (Redis + `brain.short-term-memory`) |
| Long-Term Memory            | Neocortical storage       | Persistent `MemoryItem` store (`brain.long-term-memory`)              |
| Episodic Memory             | Hippocampal episodic      | Event sequences (`brain.episodic-memory`)                             |
| Affective / Motivational    | Limbic system             | `RewardSignal` output                                                 |
| Decision-Making & Reasoning | Prefrontal cortex         | Plans, judgments, action decisions                                    |

### Group III — Executive & Output

| Module                    | Analogy                   | Key output                                     |
| ------------------------- | ------------------------- | ---------------------------------------------- |
| Executive / Agent         | Frontal lobes             | Goals, policies, top-down attention directives |
| Agent Execution (Runtime) | Motor planning            | Tool calls, skill pipelines                    |
| Motor / Output / Effector | Motor cortex + cerebellum | API calls, messages, file writes               |

### Group IV — Adaptive Systems _(cross-cutting)_

| Module                      | Analogy                    | Key output                                 |
| --------------------------- | -------------------------- | ------------------------------------------ |
| Learning & Adaptation       | Basal ganglia + cerebellum | Parameter updates, behavioral conditioning |
| Meta-cognition & Monitoring | Anterior cingulate cortex  | Confidence scores, error signals           |

### Group V — Interface

| Component                        | Location                        | Role                                                                                                                 |
| -------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Hono API Gateway                 | `apps/default/server/`          | BFF: MCP client (Streamable HTTP), SSE relay to browser, CORS policy, endpoint for all `/api/*` routes              |
| OAuth 2.1 Auth Layer             | `apps/default/server/auth/`     | JWT-based local IdP stub (PKCE flow, RFC 8414/9728 metadata endpoints); replaceable with external OIDC in forks     |
| Browser Client — Chat tab       | `apps/default/client/`          | User-facing input/output surface; SSE token streaming via `EventSource`; WCAG 2.1 AA + mobile responsive             |
| Browser Client — Internals tab  | `apps/default/client/`          | Developer transparency: agent card browser, signal trace feed, memory state inspector, active collections viewer     |

---

## Shared Contracts (Phase 1)

All inter-module communication is governed by the schemas and specs in `shared/`. These are the canonical contracts that
every module MUST conform to.

### Schemas (`shared/schemas/`)

| File                                                                   | Purpose                                                    |
| ---------------------------------------------------------------------- | ---------------------------------------------------------- |
| [`mcp-context.schema.json`](../shared/schemas/mcp-context.schema.json) | MCP envelope — all backbone messages                       |
| [`a2a-message.schema.json`](../shared/schemas/a2a-message.schema.json) | A2A message parts (text, data, file, function call/result) |
| [`a2a-task.schema.json`](../shared/schemas/a2a-task.schema.json)       | A2A task lifecycle, artifacts, and errors                  |

### Types (`shared/types/`)

| File                                                                     | Purpose                                                        |
| ------------------------------------------------------------------------ | -------------------------------------------------------------- |
| [`signal.schema.json`](../shared/types/signal.schema.json)               | Universal inter-layer signal envelope                          |
| [`memory-item.schema.json`](../shared/types/memory-item.schema.json)     | Unified memory record (all timescales, all vector collections) |
| [`reward-signal.schema.json`](../shared/types/reward-signal.schema.json) | Affective / motivational reward signal                         |

### Utils (`shared/utils/`)

| File                                             | Purpose                                                               |
| ------------------------------------------------ | --------------------------------------------------------------------- |
| [`logging.md`](../shared/utils/logging.md)       | Structured JSON log format, severity levels, language guidance        |
| [`tracing.md`](../shared/utils/tracing.md)       | W3C TraceContext propagation, span lifecycle, sampling policy         |
| [`validation.md`](../shared/utils/validation.md) | Boundary validation, sanitization, LLM output validation, size limits |

---

## Cross-Cutting Infrastructure

### MCP — Module Context Protocol

The communication backbone. All inter-module data travels as `MCPContext` envelopes. Modules register capabilities with
the MCP broker and route messages through it. See [MCP Protocol Guide](protocols/mcp.md).

### A2A — Agent-to-Agent

Task delegation and multi-agent coordination. Modules that act as autonomous agents expose A2A endpoints and manage task
lifecycle via `A2ATask` objects. A2A messages are carried inside MCP context envelopes. See
[A2A Protocol Guide](protocols/a2a.md).

### Vector Store

All modules that maintain embedded state use the backend-agnostic vector store adapter (`shared/vector-store/`, Phase
1.4). Collections follow the naming convention `brain.<module-name>`. The default backend is ChromaDB (local,
zero-infrastructure); Qdrant is recommended for production.

### Observability

Every module emits structured JSON logs to `stdout` (see [Logging Spec](../shared/utils/logging.md)) and propagates W3C
trace context (see [Tracing Spec](../shared/utils/tracing.md)). The OpenTelemetry Collector, Prometheus, and Grafana
stack is provisioned in `observability/`.

---

## Signal Flow

_Signal-flow sequence diagrams will be added when Phase 3 (Signal Processing) modules are live._

Narrative summary:

1. **Application Layer (Hono gateway + browser client)** receives external input from the user, authenticates
   the request (OAuth 2.1 Bearer token), and issues a `POST /api/input` that the gateway wraps in a `Signal`
   envelope and dispatches to the Sensory / Input Layer via the MCP backbone. Streaming token responses are
   relayed back to the browser via SSE (`GET /api/stream`, `text/event-stream`).
2. **Sensory / Input Layer** ingests the signal, assigns a `traceId`, normalizes it to a `Signal` envelope, and
   dispatches it upward via MCP.
3. **Attention & Filtering Layer** scores salience, applies relevance gates, and routes the prioritized signal. May drop
   low-priority signals. Receives top-down priority directives from the Executive layer.
4. **Perception Layer** extracts features, embeds the result into `brain.perception`, and publishes a feature `Signal`
   to the Memory and Decision-Making layers.
5. **Memory Layer** queries and updates the appropriate timescale store; returns a context window to Working Memory.
6. **Decision-Making & Reasoning Layer** integrates memory, perception, and affective signals to produce a plan or
   judgment.
7. **Executive / Agent Layer** evaluates the plan against goals and policies; issues tool invocations or directs further
   reasoning via A2A tasks.
8. **Motor / Output / Effector Layer** executes actions and dispatches feedback signals back up the stack.

---

## References

- [Workplan](Workplan.md) — phased implementation roadmap
- [MCP Protocol Guide](protocols/mcp.md)
- [A2A Protocol Guide](protocols/a2a.md)
- [Getting Started Guide](guides/getting-started.md)
- [Adding a Module Guide](guides/adding-a-module.md)
- [Brain Structure](../resources/static/knowledge/brain-structure.md)
