---
id: architecture
version: 0.4.0
status: active
last-reviewed: 2026-03-04
---

# Architecture

> **Status: active** — Phase 1–8 deliverables documented. Group I (Signal Processing) live as of Phase 4;
> Group II (Cognitive Processing) live as of Phase 5; Group III (Executive & Output) live as of Phase 6;
> Group IV (Adaptive Systems) live as of Phase 7. Group V (Interface Layer, `apps/default/`) is complete
> as of M8 (2026-03-03). Phase 9 (Security & Deployment cross-cutting layer) is in progress.

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
| Browser Client — Chat tab      | `apps/default/client/`      | User-facing input/output surface; `fetch()`-based SSE token streaming (custom `Authorization` header required); WCAG 2.1 AA + mobile responsive |
| Browser Client — Internals tab | `apps/default/client/`      | Developer transparency: agent card browser, signal trace feed, memory state inspector, active collections viewer |

---

## Shared Contracts (Phase 1)

All inter-module communication is governed by the schemas and specs in `shared/`. These are the canonical contracts that
every module MUST conform to.

### Schemas (`shared/schemas/`)

| File                                                                   | Purpose                                                    |
| ---------------------------------------------------------------------- | ---------------------------------------------------------- |
| [`mcp-context.schema.json`](../shared/schemas/mcp-context.schema.json)                       | MCP envelope — all backbone messages                                          |
| [`a2a-message.schema.json`](../shared/schemas/a2a-message.schema.json)                       | A2A message parts (text, data, file, function call/result)                    |
| [`a2a-task.schema.json`](../shared/schemas/a2a-task.schema.json)                             | A2A task lifecycle, artifacts, and errors                                     |
| [`motor-feedback.schema.json`](../shared/schemas/motor-feedback.schema.json)                 | Phase 6 motor feedback: deviation score, reward signal, latency, channel      |
| `learning-adaptation-episode.schema.json` _(⬜ Phase 7)_                                     | RL episode: state, action (goal-priority deltas), reward, next-state          |
| `metacognitive-evaluation.schema.json` _(⬜ Phase 7)_                                        | Metacognitive event: confidence score, deviation z-score, error flag          |

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

### Group II service ports

Each Group II module runs a **FastAPI + Uvicorn A2A server** (JSON-RPC 2.0 on `POST /tasks`) and a **FastMCP SSE server**
(MCP tools on `GET /sse`), both co-hosted in a single `server.py` process.

| Service              | A2A Port | MCP (FastMCP SSE) Port |
| -------------------- | -------- | ---------------------- |
| `working-memory`     | 8201     | 8301                   |
| `short-term-memory`  | 8202     | 8302                   |
| `long-term-memory`   | 8203     | 8303                   |
| `episodic-memory`    | 8204     | 8304                   |
| `affective`          | 8205     | 8305                   |
| `reasoning`          | 8206     | 8306                   |

### Group III service ports

Group III modules each run a single **FastAPI + Uvicorn** process serving both A2A (JSON-RPC 2.0 on `POST /tasks`)
and MCP tool routes on the same port.

| Service           | Port | Protocol                 |
| ----------------- | ---- | ------------------------ |
| `executive-agent` | 8161 | HTTP (FastAPI + Uvicorn) |
| `agent-runtime`   | 8162 | HTTP (FastAPI + Uvicorn) |
| `motor-output`    | 8163 | HTTP (FastAPI + Uvicorn) |

### Group IV service ports _(Phase 7 — design resolved, not yet live)_

| Service               | Port | Protocol                 |
| --------------------- | ---- | ------------------------ |
| `learning-adaptation` | 8170 | HTTP (FastAPI + Uvicorn) |
| `metacognition`       | 8171 | HTTP (FastAPI + Uvicorn) |

The `metacognition` module additionally exposes a **Prometheus metrics scrape endpoint** on port `9464`
(via `opentelemetry-exporter-prometheus`). This is separate from the A2A/MCP port.

Module services are started via the `modules` docker-compose profile:

```bash
docker compose --profile modules up -d
```

Local development without Docker: each module runs independently with `uv run uvicorn ... --reload`. See
[Deployment Guide](guides/deployment.md) for the full environment variable reference.

### Communication routing rule

> All cross-module communication routes through the A2A JSON-RPC 2.0 protocol. Modules never make raw or custom
> HTTP calls to each other — all outbound cross-module calls use `A2AClient` from `shared/a2a/python/`.

```
Module A ──► A2AClient (shared/a2a/python) ──► Module B A2A server (POST /tasks)
```

**Phase 5 note**: Each module IS its own A2A server (FastAPI + Uvicorn, JSON-RPC 2.0) and its own MCP server
(FastMCP SSE). There is no central broker process running at this layer. The `MCPToA2ABridge`
(`infrastructure/adapters/bridge.ts`) and the central `infrastructure/mcp` + `infrastructure/a2a` broker roles
are composed in Phase 8 by the application-host layer, which becomes the single orchestrating surface above all
module agents. The per-module servers built here require no refactoring at that point — the app host simply
routes to them.

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

<!-- Phase 9 addition — 2026-03-04 -->
## Phase 9 — Cross-Cutting: Security & Deployment

Phase 9 does **not** add new cognitive modules. It hardens and packages Groups I–V for production by adding three
cross-cutting concerns that were deliberately deferred from the functional build phases:

### Security (`security/`)

The security layer follows the **immune privilege** model: the system protects its own cognitive modules the same
way the CNS protecting neural tissue from immune system intrusion.

| Mechanism | Biological analogue | Implementation |
| --- | --- | --- |
| Policy enforcement | Microglial patrolling | OPA Rego rules derived from `agent-card.json` (endogenous-first) |
| Container sandboxing | Apoptosis / MHC-I isolation | gVisor `runtimeClassName` (CI + production) |
| Network isolation | Glial scar | Kubernetes `NetworkPolicy` default-deny per module |
| Workload identity | MHC-I molecule | mTLS with self-signed CA (Phase 9); SPIFFE/SPIRE deferred to Phase 10 |

OPA runs as a single shared server (`docker compose --profile security`); policy data is generated endogenously
from all `agent-card.json` files via `scripts/gen_opa_data.py`.

### Deployment (`deploy/`)

```
deploy/
  docker/
    base-python.Dockerfile    # Multi-stage Python 3.11; non-root; gVisor-compatible
    base-node.Dockerfile      # Multi-stage Node.js 20; non-root; gVisor-compatible
  k8s/
    namespace.yaml            # endogenai-modules + endogenai-infra namespaces
    runtime-class-gvisor.yaml # gVisor RuntimeClass
    network-policy-default-deny.yaml
    <module>/
      deployment.yaml         # non-root securityContext, runtimeClassName, HPA-ready
      service.yaml
      hpa.yaml                # 70% CPU threshold; HA services at minReplicas: 2
      network-policy.yaml
```

All 16 Kubernetes `Deployment` manifests enforce: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`,
`capabilities.drop: [ALL]`, `seccompProfile.type: RuntimeDefault`, `runtimeClassName: gvisor` (production).

### Relationship to existing architecture

Phase 9 wraps the full Groups I–V cognitive architecture without modifying any module interfaces or contracts.
The OPA policies derive their rules _from_ the existing `agent-card.json` declarations; the Kubernetes manifests
package the existing module processes; the mTLS certificates secure the existing A2A/MCP communication paths
that were designed in Phases 1–2. This is the endogenous-first principle applied at the deployment layer.

---

## References

- [Workplan](Workplan.md) — phased implementation roadmap
- [MCP Protocol Guide](protocols/mcp.md)
- [A2A Protocol Guide](protocols/a2a.md)
- [Getting Started Guide](guides/getting-started.md)
- [Adding a Module Guide](guides/adding-a-module.md)
- [Brain Structure](../resources/static/knowledge/brain-structure.md)
