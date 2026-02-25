# Initial Workplan Document

This document outlines the initial workplan for the development of the brAIn framework. It serves as a roadmap for the
first phase of implementation, focusing on establishing the core architecture, defining module interfaces, and creating
foundational components.

---

## Guiding Constraints

- **Documentation-first**: all implementation must be accompanied by clear documentation; define documentation standards
  and templates in Phase 0. See [README — File Directory](../readme.md#file-directory) for structure reference.
- **Endogenous-first**: scaffold from existing system knowledge, not from scratch in isolation.
- **Local compute first**: Ollama embeddings (`nomic-embed-text`) and local vector stores (ChromaDB) are the default;
  cloud services are opt-in.
- **Polyglot with convention**: Python for ML/cognitive modules, TypeScript for MCP/A2A infrastructure and application
  surfaces, JSON Schema / Protobuf for all shared contracts.
- **No direct LLM SDK calls**: all LLM inference routes through LiteLLM.
- **Autopoietic lifecycle**: every deliverable added to the repo should expand the system's capacity to generate further
  components.
- **Test-driven**: all components must have comprehensive unit and integration tests; define test strategy in Phase 0.

---

## Phase 0 — Repo Bootstrap & Tooling

**Goal**: Establish the monorepo skeleton, developer environment, and project conventions from which all subsequent
phases grow.

### 0.1 Monorepo Initialization

- [x] Init Turborepo workspace; configure `pnpm` workspaces for TypeScript packages and `uv` for Python packages
- [x] Add root `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`
- [x] Configure `turbo.json` with pipeline tasks: `build`, `test`, `lint`, `typecheck`
- [x] Add `docker-compose.yml` for local multi-service orchestration (ChromaDB, Ollama, Redis, observability stack)

#### 0.1 Verification

- [x] `pnpm install` completes without errors
- [x] `turbo run build` exits 0 (no packages yet, pipeline resolves cleanly)
- [x] `turbo run lint` exits 0
- [x] `turbo run test` exits 0
- [x] `docker compose config` validates without errors
- [x] `pnpm-workspace.yaml` globs cover `infrastructure/*`, `modules/**/*`, `apps/*`, `shared/*`

### 0.2 Shared Tooling & Conventions

- [x] Define root ESLint + Prettier config (TypeScript); define root `ruff` + `mypy` config (Python)
- [x] Configure `buf` toolchain for Protobuf/JSON Schema management in `shared/`
- [x] Set up pre-commit hooks: lint, typecheck, schema validation
- [x] Establish commit message convention and PR template

#### 0.2 Verification

- [x] `npx eslint .` exits 0 on root TypeScript files
- [x] `npx prettier --check .` exits 0
- [x] `uv run ruff check .` exits 0
- [x] `uv run mypy .` exits 0 (or reports only expected no-source warnings)
- [x] `pre-commit run --all-files` passes all hooks (trailing-whitespace, end-of-file-fixer, check-yaml, check-json,
      check-toml, prettier, ruff, ruff-format, mypy, validate-frontmatter)
- [x] `git log --oneline -1` subject conforms to Conventional Commits (verified by `commitlint`)
- [x] `.github/pull_request_template.md` is present and non-empty
- [x] `cd shared && buf lint` exits 0 (stub `placeholder.proto` satisfies the linter; real schemas authored in Phase 1)

### 0.3 Observability Stub

- [x] Provision `observability/` with OpenTelemetry collector config, Prometheus scrape config, and Grafana datasource
      definitions
- [x] Wire `docker-compose.yml` to bring up the local observability stack

#### 0.3 Verification

- [x] `docker compose up otel-collector prometheus grafana -d` starts all three services without error
- [x] `curl -f http://localhost:4318` (or configured OTLP HTTP port) returns a non-5xx response from the OTel collector
- [x] `curl -f http://localhost:9090/-/healthy` returns `Prometheus Server is Healthy`
- [x] `curl -f http://localhost:3000/api/health` returns `{"database":"ok","..."}` from Grafana
- [x] Grafana Prometheus datasource (`observability/grafana/datasources/default.yaml`) appears as **connected** in the
      Grafana UI at `http://localhost:3000`
- [x] `observability/README.md` documents port assignments and how to bring up the stack

### 0.4 Seed Knowledge Fixtures

- [x] Move or create `resources/static/knowledge/brain-structure.md` with YAML frontmatter (`id`, `version`, `status`,
      `maps-to-modules`)
- [x] Populate `resources/neuroanatomy/` stubs (8 region files) with frontmatter and placeholder content, to be enriched
      from `raw_data_dumps/Human_Brain__wiki.md`
- [x] Validate frontmatter schema for all seed documents

#### 0.4 Verification

- [x] `resources/static/knowledge/brain-structure.md` frontmatter contains `id`, `version`, `status`, `seed-collection`,
      `chunking`, and `maps-to-modules` keys
- [x] All 8 region files are present under `resources/neuroanatomy/`: `association-cortices.md`, `cerebellum.md`,
      `frontal-lobe.md`, `hippocampus.md`, `limbic-system.md`, `prefrontal-cortex.md`, `sensory-cortex.md`,
      `thalamus.md`
- [x] Each region file frontmatter contains `id`, `version`, `status`, `seed-collection`, `source`, and
      `maps-to-modules` keys
- [x] `pre-commit run validate-frontmatter --all-files` exits 0 across all resource files
- [x] `resources/README.md` documents the resource directory structure and frontmatter schema

**Deliverables**: runnable `docker-compose up`, passing `turbo run lint`, usable seed knowledge directory, initial test
suite configured, documentation templates established.

---

## Phase 1 — Shared Contracts & Vector Store Adapter

**Goal**: Define all language-agnostic schemas and the backend-agnostic vector store adapter — the shared foundation
consumed by every cognitive module.

### 1.1 Shared Schemas (`shared/schemas/`)

- [ ] Author `mcp-context.schema.json` — MCP context object schema
- [ ] Author `a2a-message.schema.json` — A2A message envelope schema
- [ ] Author `a2a-task.schema.json` — A2A task lifecycle schema

### 1.2 Shared Types (`shared/types/`)

- [ ] Author `signal.schema.json` — common signal envelope
- [ ] Author `memory-item.schema.json` — unified memory record structure
- [ ] Author `reward-signal.schema.json` — reward / affective weighting structure

### 1.3 Shared Utils (`shared/utils/`)

- [ ] Write `logging.md` — structured log format spec (JSON, required fields, severity levels)
- [ ] Write `tracing.md` — distributed trace context propagation spec (W3C TraceContext)
- [ ] Write `validation.md` — input sanitization and boundary validation patterns

### 1.4 Vector Store Adapter (`shared/vector-store/`)

- [ ] Author `adapter.interface.json` — language-agnostic interface contract: `upsert`, `query`, `delete`,
      `create-collection`, `drop-collection`, `list-collections`
- [ ] Author `collection-registry.json` — canonical registry of all `brain.<module-name>` collections
- [ ] Author `chroma.config.schema.json`, `qdrant.config.schema.json`, `pgvector.config.schema.json`
- [ ] Author `embedding.config.schema.json` — provider, model, base URL, dimensions, fallback policy
- [ ] Implement Python adapter (ChromaDB default; Qdrant production) conforming to `adapter.interface.json`
- [ ] Implement TypeScript adapter (ChromaDB default) conforming to `adapter.interface.json`
- [ ] Write `README.md` — adapter pattern, collection namespacing, backend selection, Ollama integration

**Deliverables**: validated schemas, working ChromaDB adapter with unit tests via Testcontainers,
`collection-registry.json` pre-populated with all module collection names.

---

## Phase 2 — Communication Infrastructure (MCP + A2A)

**Goal**: Stand up the MCP context backbone and A2A agent coordination layer that all cognitive modules will communicate
through.

### 2.1 MCP Infrastructure (`infrastructure/mcp/`)

- [ ] Scaffold TypeScript package using `@modelcontextprotocol/sdk`
- [ ] Implement MCP server, context broker, and capability registry
- [ ] Implement state synchronization primitives
- [ ] Write unit and integration tests
- [ ] Author `README.md` and `docs/protocols/mcp.md`

### 2.2 A2A Infrastructure (`infrastructure/a2a/`)

- [ ] Scaffold TypeScript + Python packages aligned to the
      [A2A Project specification](https://github.com/a2aproject/A2A)
- [ ] Implement A2A server, request handler, agent card endpoint (`/.well-known/agent-card.json`), and task orchestrator
- [ ] Add conformance test suite; version-lock A2A dependency
- [ ] Author `README.md` and `docs/protocols/a2a.md`

### 2.3 MCP + A2A Adapter (`infrastructure/adapters/`)

- [ ] Implement adapter bridge enabling modules to participate in both MCP context exchange and A2A task protocols
      without duplicated logic
- [ ] Write integration tests covering round-trip context propagation and agent task delegation
- [ ] Author `README.md`

**Deliverables**: locally runnable MCP + A2A stack, all conformance tests passing, adapter verified end-to-end.

---

## Phase 3 — Group I: Signal Processing Modules

**Goal**: Implement the sensory boundary of the system — raw signal ingestion, attentional gating, and feature
extraction.

### 3.1 Sensory / Input Layer (`modules/group-i-signal-processing/sensory-input/`)

- [ ] Implement signal ingestion for text, image, audio, API events, and sensor stream modalities
- [ ] Implement normalization, timestamping, and upward dispatch
- [ ] Wire MCP + A2A interfaces; author `agent-card.json`
- [ ] Write unit and integration tests; author `README.md`

### 3.2 Attention & Filtering Layer (`modules/group-i-signal-processing/attention-filtering/`)

- [ ] Implement salience scoring, relevance filtering, and signal routing
- [ ] Implement top-down attention modulation interface (receives directives from Executive layer)
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 3.3 Perception Layer (`modules/group-i-signal-processing/perception/`)

- [ ] Implement feature extraction, pattern recognition, language understanding, scene parsing, and multimodal fusion
      pipeline
- [ ] Wire `brain.perception` vector collection via shared adapter; embed extracted feature representations
- [ ] Configure `pipeline.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: end-to-end signal flow from raw input through perception, with features persisted to
`brain.perception`.

---

## Phase 4 — Group II: Cognitive Processing Modules

**Goal**: Implement memory across all timescales, affective modulation, and the reasoning/planning engine.

### 4.1 Working Memory (`modules/group-ii-cognitive-processing/memory/working-memory/`)

- [ ] Implement in-process KV store with read, write, evict operations
- [ ] Implement retrieval-augmented loader: queries `brain.short-term-memory` and `brain.long-term-memory` to assemble
      context window per turn; respect token budget
- [ ] Implement consolidation pipeline: dispatch evicted items to episodic / long-term memory
- [ ] Configure `capacity.config.json` and `retrieval.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.2 Short-Term Memory (`modules/group-ii-cognitive-processing/memory/short-term-memory/`)

- [ ] Implement session-scoped record store with TTL management (Redis/Valkey backend)
- [ ] Wire `brain.short-term-memory` collection; embed session records via Ollama `nomic-embed-text`
- [ ] Implement semantic search over current session to serve working memory loader
- [ ] Configure `ttl.config.json`, `vector-store.config.json`, `embedding.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.3 Long-Term Memory (`modules/group-ii-cognitive-processing/memory/long-term-memory/`)

- [ ] Implement configurable vector DB adapter for `brain.long-term-memory` (ChromaDB default, Qdrant for production)
- [ ] Implement knowledge graph adapter (Kuzu default, Neo4j for production)
- [ ] Implement SQL adapter for structured fact storage (SQLite default, PostgreSQL for production)
- [ ] Implement embedding pipeline with frontmatter-aware section chunking (respects `brain-structure.md` region
      boundaries)
- [ ] Implement semantic + hybrid retrieval (vector + keyword) with re-ranking
- [ ] Implement boot-time seed pipeline: chunk and embed all `resources/static/knowledge/` documents via LlamaIndex
- [ ] Configure `vector-store.config.json`, `embedding.config.json`, `indexing.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.4 Episodic Memory (`modules/group-ii-cognitive-processing/memory/episodic-memory/`)

- [ ] Implement ordered event log with temporal indexing
- [ ] Wire `brain.episodic-memory` collection; embed episode records for semantic + temporal composite queries
- [ ] Implement temporal replay, semantic episode search, and composite queries
- [ ] Configure `vector-store.config.json`, `embedding.config.json`, `retention.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.5 Affective / Motivational Layer (`modules/group-ii-cognitive-processing/affective/`)

- [ ] Implement reward signal generation, emotional weighting, urgency scoring, and prioritization cue dispatch
- [ ] Wire `brain.affective` collection; embed reward and emotional state history
- [ ] Configure `drive.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.6 Decision-Making & Reasoning Layer (`modules/group-ii-cognitive-processing/reasoning/`)

- [ ] Implement logical reasoning, causal inference, planning under uncertainty, and conflict resolution via DSPy
- [ ] Integrate Guidance for constrained/structured generation in policy-following contexts
- [ ] Wire `brain.reasoning` collection; embed inference traces, plans, and causal models
- [ ] Route all LLM calls through LiteLLM
- [ ] Configure `strategy.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: full memory stack operational with seed pipeline verified, reasoning layer producing traceable
inference records.

---

## Phase 5 — Group III: Executive & Output Modules

**Goal**: Implement the agent's executive identity, runtime orchestration, and environment effectors.

### 5.1 Executive / Agent Layer (`modules/group-iii-executive-output/executive-agent/`)

- [ ] Implement agent identity management and self-model
- [ ] Implement persistent goal stack with prioritization and lifecycle management
- [ ] Implement policy engine with value evaluation and top-down modulation dispatch
- [ ] Wire `brain.executive-agent` collection; embed goals, values, policies, and identity state
- [ ] Configure `identity.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.2 Agent Execution (Runtime) Layer (`modules/group-iii-executive-output/agent-runtime/`)

- [ ] Implement task decomposition, tool/function selection, and skill pipeline execution via Temporal (primary) or
      Prefect (fallback)
- [ ] Implement sequencing and inter-module coordination
- [ ] Configure tool registry
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.3 Motor / Output / Effector Layer (`modules/group-iii-executive-output/motor-output/`)

- [ ] Implement API call dispatch, message delivery, file writes, rendered output generation, and control signal
      emission
- [ ] Implement upward feedback confirmation loop
- [ ] Configure output channel definitions
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: end-to-end decision-to-action pipeline verified; agent can receive a goal, reason about it, and
produce a measurable environmental output.

---

## Phase 6 — Group IV: Adaptive Systems (Cross-Cutting)

**Goal**: Implement learning, reinforcement, and meta-cognitive monitoring layers that refine the system over time.

### 6.1 Learning & Adaptation Layer (`modules/group-iv-adaptive-systems/learning-adaptation/`)

- [ ] Implement reinforcement signal processing and parameter update dispatch via Stable-Baselines3 (scale to RLlib /
      TorchRL as needed)
- [ ] Implement behavioural conditioning pipelines
- [ ] Implement skill acquisition and capability registration
- [ ] Wire `brain.learning-adaptation` collection; embed feedback logs and skill acquisition records
- [ ] Configure `learning.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 6.2 Meta-cognition & Monitoring Layer (`modules/group-iv-adaptive-systems/metacognition/`)

- [ ] Implement confidence tracking, error detection, performance evaluation, and anomaly escalation to executive layer
      via OpenTelemetry
- [ ] Implement corrective action trigger dispatch and remediation pipelines
- [ ] Wire `brain.metacognition` collection; embed confidence scores, error patterns, and performance snapshots
- [ ] Configure `monitoring.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A hooks; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: system can detect its own errors, escalate anomalies, and register reinforcement signals that
influence subsequent decisions.

---

## Phase 7 — Application Layer & Observability

**Goal**: Expose the system to external users and operators; verify end-to-end signal flow with full telemetry.

### 7.1 Default Application Shell (`apps/default/`)

- [ ] Implement request routing into Sensory/Input Layer and output surfacing from Motor/Output/Effector Layer
- [ ] Build chatbot / API / dashboard entry point (TypeScript, Hono or Next.js)
- [ ] Configure environment and write integration tests; author `README.md`

### 7.2 Observability (`observability/`)

- [ ] Finalize structured log emitters (structlog / pino) across all modules per `shared/utils/logging.md`
- [ ] Wire OpenTelemetry trace context propagation across all inter-module boundaries per `shared/utils/tracing.md`
- [ ] Provision Grafana dashboards for module health, signal flow latency, and memory collection sizes
- [ ] Author `README.md`

### 7.3 MCP Resource Registry (`resources/`)

- [ ] Populate `uri-registry.json` with all resource URI patterns across modules
- [ ] Author `access-control.md`
- [ ] Populate per-layer resource definition files (`group-i` → `group-iv`)
- [ ] Author `README.md`

**Deliverables**: system accessible end-to-end via the application shell, with trace IDs propagating from input to
effector output, visible in Grafana.

---

## Phase 8 — Cross-Cutting: Security, Deployment & Documentation

**Goal**: Harden the system, package it for deployment, and ensure the documentation is complete and self-referential.

### 8.1 Security (`security/`)

- [ ] Define module sandboxing policies and capability isolation rules with OPA
- [ ] Configure gVisor sandbox templates for module containers
- [ ] Perform security review of all inter-module interfaces; document findings
- [ ] Author `README.md` and `docs/guides/security.md`

### 8.2 Deployment (`deploy/`)

- [ ] Write per-module `Dockerfile` definitions; author base image
- [ ] Write Kubernetes manifests: per-module deployments, services, HPA configurations
- [ ] Validate `docker-compose.yml` covers the full local development stack
- [ ] Author `docs/guides/deployment.md`

### 8.3 Documentation Completion

- [ ] Author `docs/architecture.md` — full architectural overview with signal-flow diagrams
- [ ] Author `docs/guides/getting-started.md` — environment setup and first-run walkthrough
- [ ] Author `docs/guides/adding-a-module.md` — step-by-step module creation guide
- [ ] Author `docs/guides/observability.md` — telemetry setup and dashboard usage
- [ ] Review and finalize `README.md` quick-start guide

**Deliverables**: system deployable via `docker-compose up` locally and via `kubectl apply` to a Kubernetes cluster, all
documentation complete and cross-linked.

---

## Phase 9 — Neuromorphic Layer (Optional / Pluggable)

**Goal**: Evaluate and integrate spiking-neuron computation as an independently deployable, non-blocking extension.

- [ ] Prototype BindsNET (PyTorch-native, lowest barrier to entry) on a representative Perception sub-task
- [ ] Evaluate Nengo (broadest hardware pathway via NengoLoihi) for Attention & Filtering spiking equivalent
- [ ] Define the MCP interface contract for neuromorphic module interchangeability with their standard counterparts
- [ ] Benchmark: energy, latency, and accuracy trade-offs vs. conventional modules on equivalent tasks
- [ ] Document selection rationale; integrate winning candidate as optional pluggable module

---

## Milestones Summary

| Milestone                         | Phase(s) | Key Signal                                                                                |
| --------------------------------- | -------- | ----------------------------------------------------------------------------------------- |
| **M0 — Repo Live**                | 0        | `docker-compose up` green; seed knowledge committed                                       |
| **M1 — Contracts Stable**         | 1        | All schemas validated; vector adapter tests pass                                          |
| **M2 — Infrastructure Online**    | 2        | MCP + A2A conformance tests pass end-to-end                                               |
| **M3 — Signal Boundary Live**     | 3        | Text input reaches `brain.perception` collection                                          |
| **M4 — Memory Stack Live**        | 4        | Seed pipeline populates `brain.long-term-memory`; working memory assembles context window |
| **M5 — End-to-End Decision Loop** | 5        | Goal → Reason → Act pipeline produces verifiable output                                   |
| **M6 — Adaptive Systems Active**  | 6        | Error detection escalates to executive; reinforcement signals registered                  |
| **M7 — User-Facing**              | 7        | chatbot/API shell accessible; traces visible in Grafana                                   |
| **M8 — Production-Ready**         | 8        | Kubernetes deploy succeeds; all documentation complete                                    |

---

## Open Questions & Deferred Decisions

- **A2A version lock**: confirm which A2A spec release to align to before Phase 2 begins.
- **Temporal vs. Prefect**: run a comparative spike during Phase 5 before committing to Temporal for `agent-runtime/`.
- **Graph store selection**: Kuzu (embedded) is the default for `long-term-memory/graph-store/`; validate storage limits
  before Phase 4 closes.
- **WebMCP evaluation**: determine whether browser-native UI modules require WebMCP before Phase 7 begins.
- **Neuromorphic prioritization**: decide if Phase 9 is in-scope for v1 or deferred to v2.
