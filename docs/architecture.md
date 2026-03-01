---
id: architecture
version: 0.2.0
status: active
last-reviewed: 2026-02-28
---

# Architecture

> **Status: active** — Phase 1–4 deliverables documented. Group I (Signal Processing) modules are live as of Phase 4.
> Group II–IV detail will be added as subsequent phases deliver live modules.

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

| Component                      | Location                    | Role                                                                                                             |
| ------------------------------ | --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Hono API Gateway               | `apps/default/server/`      | BFF: MCP client (Streamable HTTP), SSE relay to browser, CORS policy, endpoint for all `/api/*` routes           |
| OAuth 2.1 Auth Layer           | `apps/default/server/auth/` | JWT-based local IdP stub (PKCE flow, RFC 8414/9728 metadata endpoints); replaceable with external OIDC in forks  |
| Browser Client — Chat tab      | `apps/default/client/`      | User-facing input/output surface; SSE token streaming via `EventSource`; WCAG 2.1 AA + mobile responsive         |
| Browser Client — Internals tab | `apps/default/client/`      | Developer transparency: agent card browser, signal trace feed, memory state inspector, active collections viewer |

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

## Signal Flow

### Group I — Detailed Signal-Processing Flow (Phase 4)

The three Group I modules form an ordered pipeline. Signals travel bottom-up through the pipeline; top-down attention
directives travel in the reverse direction from the Executive Layer (Phase 6).

```
External input
      │
      ▼
┌─────────────────────────────────────────────────────────────
│  sensory-input  (port 8101)
│
│  1. Accept raw input (text / image / audio / api-event / sensor)
│  2. Validate modality; assign UUID + ISO-8601 timestamp
│  3. Build Signal envelope (signal.schema.json)
│  4. Publish MCPContext{payload: Signal} → MCP broker
└─────────────────────────────────────────────────────────────
      │  MCPContext (signal/v1)
      ▼
┌─────────────────────────────────────────────────────────────
│  attention-filtering  (port 8102)
│
│  1. Receive Signal via MCP subscription
│  2. Score salience (heuristic rule engine; configurable weights)
│  3. Apply top-down directives (attention.directive signals from Executive)
│  4. Drop signals below threshold; promote high-priority signals
│  5. Publish gated Signal → MCP broker
└─────────────────────────────────────────────────────────────
      │  MCPContext (signal/v1, salience-annotated)
      ▼
┌─────────────────────────────────────────────────────────────
│  perception  (port 8103)
│
│  1. Receive gated Signal via MCP subscription
│  2. Extract features via modality-specific extractor
│     └─ text     → LiteLLM (entities, intent, topics, sentiment)
│     └─ api-event → deterministic JSON schema extraction
│     └─ image/audio/sensor → skeleton (Phase 5 enrichment)
│  3. Fuse features (multimodal fusion when multiple modalities present)
│  4. Embed fused representation via nomic-embed-text (Ollama)
│  5. Persist MemoryItem to brain.perception (ChromaDB)
│  6. Publish feature Signal → MCP broker (→ Group II)
└─────────────────────────────────────────────────────────────
      │  MCPContext (signal/v1, features embedded + persisted)
      ▼
  Group II — Cognitive Processing (Phase 5)
```

**Top-down attention path** (Phase 6 → Group I):

```
Executive Layer
      │  attention.directive Signal
      ▼
  attention-filtering.modulation  (active directive store)
      │  adjusts salience thresholds for subsequent signals
```

### Full System Narrative

1. **Application Layer** receives external input, authenticates (OAuth 2.1 Bearer token), wraps in a `Signal` envelope,
   and dispatches to `sensory-input` via the MCP backbone. Streaming token responses are relayed back to the browser via
   SSE (`GET /api/stream`).
2. **Sensory / Input Layer** normalizes, timestamps, and dispatches the signal upward via MCP.
3. **Attention & Filtering Layer** scores salience, applies relevance gates, and routes the prioritised signal. Receives
   top-down priority directives from the Executive Layer.
4. **Perception Layer** extracts features, embeds the result into `brain.perception`, and publishes a feature `Signal`
   to the Memory and Decision-Making layers.
5. **Memory Layer** queries and updates the appropriate timescale store; returns a context window to Working Memory.
6. **Decision-Making & Reasoning Layer** integrates memory, perception, and affective signals to produce a plan or
   judgment.
7. **Executive / Agent Layer** evaluates the plan against goals and policies; issues tool invocations or directs further
   reasoning via A2A tasks.
8. **Motor / Output / Effector Layer** executes actions and dispatches feedback signals back up the stack.

---

## Module Networking Topology (Phase 4+)

Each cognitive module runs as an **independent process** (Python FastAPI + Uvicorn). There is no shared process boundary
between modules — all communication is over MCP context messages or A2A task RPC.

### Group I service ports

| Service               | Port | Protocol                 |
| --------------------- | ---- | ------------------------ |
| `sensory-input`       | 8101 | HTTP (FastAPI + Uvicorn) |
| `attention-filtering` | 8102 | HTTP (FastAPI + Uvicorn) |
| `perception`          | 8103 | HTTP (FastAPI + Uvicorn) |

Module services are started via the `modules` docker-compose profile:

```bash
docker compose --profile modules up -d
```

Local development without Docker: each module runs independently with `uv run uvicorn ... --reload`. See
[Deployment Guide](guides/deployment.md) for the full environment variable reference.

### Communication routing rule

> All cross-module communication routes through `infrastructure/adapters/bridge.ts`. Modules never make direct HTTP
> calls to each other.

```
Module A ──► MCP broker (infrastructure/mcp) ──► Module B
Module A ──► A2A server (infrastructure/a2a) ──► Module B
             (via MCPToA2ABridge)
```

---

## Inference Abstraction

All LLM inference in EndogenAI is:

1. **Routed through LiteLLM** — no direct calls to `openai`, `anthropic`, or `ollama` SDKs.
2. **Config-driven** — model name, provider, and base URL are read from `inference.config.json` at the module root and
   overridable via environment variables (`INFERENCE_MODEL`, `INFERENCE_BASE_URL`).
3. **Dependency-injected** — all inference consumers accept an `InferencePort` Protocol, enabling unit tests to pass a
   `StubInferenceAdapter` with no live service required.

**Default local configuration (Phase 4):**

| Role               | Provider                          | Model              | Env var override  |
| ------------------ | --------------------------------- | ------------------ | ----------------- |
| Feature extraction | Ollama (via LiteLLM)              | `llama3.2`         | `INFERENCE_MODEL` |
| Embedding          | Ollama (via vector-store adapter) | `nomic-embed-text` | `EMBEDDING_MODEL` |

**Production:** swap provider by setting `INFERENCE_MODEL=gpt-4o` or `INFERENCE_MODEL=claude-3-5-sonnet-20241022` in the
environment — no code changes required. LiteLLM handles the translation.

See [Adding a Module — Step 7](guides/adding-a-module.md#7-provide-inference-configuration-modules-that-call-llms) for
the implementation pattern.

---

## References

- [Workplan](Workplan.md) — phased implementation roadmap
- [MCP Protocol Guide](protocols/mcp.md)
- [A2A Protocol Guide](protocols/a2a.md)
- [Getting Started Guide](guides/getting-started.md)
- [Adding a Module Guide](guides/adding-a-module.md)
- [Brain Structure](../resources/static/knowledge/brain-structure.md)
