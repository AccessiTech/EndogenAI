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

- [x] Author `mcp-context.schema.json` — MCP context object schema
- [x] Author `a2a-message.schema.json` — A2A message envelope schema
- [x] Author `a2a-task.schema.json` — A2A task lifecycle schema

### 1.2 Shared Types (`shared/types/`)

- [x] Author `signal.schema.json` — common signal envelope
- [x] Author `memory-item.schema.json` — unified memory record structure
- [x] Author `reward-signal.schema.json` — reward / affective weighting structure

### 1.3 Shared Utils (`shared/utils/`)

- [x] Write `logging.md` — structured log format spec (JSON, required fields, severity levels)
- [x] Write `tracing.md` — distributed trace context propagation spec (W3C TraceContext)
- [x] Write `validation.md` — input sanitization and boundary validation patterns

### 1.4 Vector Store Adapter (`shared/vector-store/`)

- [x] Author `adapter.interface.json` — language-agnostic interface contract: `upsert`, `query`, `delete`,
      `create-collection`, `drop-collection`, `list-collections`
- [x] Author `collection-registry.json` — canonical registry of all `brain.<module-name>` collections
- [x] Author `chroma.config.schema.json`, `qdrant.config.schema.json`, `pgvector.config.schema.json`
- [x] Author `embedding.config.schema.json` — provider, model, base URL, dimensions, fallback policy
- [x] Implement Python adapter (ChromaDB default; Qdrant production) conforming to `adapter.interface.json`
- [x] Implement TypeScript adapter (ChromaDB default) conforming to `adapter.interface.json`
- [x] Write `README.md` — adapter pattern, collection namespacing, backend selection, Ollama integration

**Deliverables**: validated schemas, working ChromaDB adapter with unit tests via Testcontainers,
`collection-registry.json` pre-populated with all module collection names.

---

## Phase 2 — Communication Infrastructure (MCP + A2A)

**Goal**: Stand up the MCP context backbone and A2A agent coordination layer that all cognitive modules will communicate
through.

### 2.1 MCP Infrastructure (`infrastructure/mcp/`)

- [x] Scaffold TypeScript package using `@modelcontextprotocol/sdk`
- [x] Implement MCP server, context broker, and capability registry
- [x] Implement state synchronization primitives
- [x] Write unit and integration tests
- [x] Author `README.md` and `docs/protocols/mcp.md`

### 2.2 A2A Infrastructure (`infrastructure/a2a/`)

- [x] Scaffold TypeScript + Python packages aligned to the
      [A2A Project specification](https://github.com/a2aproject/A2A)
- [x] Implement A2A server, request handler, agent card endpoint (`/.well-known/agent-card.json`), and task orchestrator
- [x] Add conformance test suite; version-lock A2A dependency
- [x] Author `README.md` and `docs/protocols/a2a.md`

### 2.3 MCP + A2A Adapter (`infrastructure/adapters/`)

- [x] Implement adapter bridge enabling modules to participate in both MCP context exchange and A2A task protocols
      without duplicated logic
- [x] Write integration tests covering round-trip context propagation and agent task delegation
- [x] Author `README.md`

**Deliverables**: locally runnable MCP + A2A stack, all conformance tests passing, adapter verified end-to-end.

---

## Phase 3 — Development Agent Infrastructure

**Goal**: Establish a fleet of VS Code Copilot agents and supporting scripts that encode the system's own development
process — enabling documentation generation, test scaffolding, schema validation, and module auditing to be driven
endogenously from the codebase itself. Recursive `AGENTS.md` files in each subdirectory give agents context-specific
guidance without contradicting root constraints.

### 3.1 Agent Conventions & Recursive `AGENTS.md` Hierarchy

- [x] Author `docs/AGENTS.md` — documentation-specific agent guidance: target audiences, frontmatter requirements,
      link and cross-reference conventions
- [x] Author `modules/AGENTS.md` — module development conventions: per-group constraints, `agent-card.json` contract,
      MCP/A2A wiring checklist
- [x] Author `infrastructure/AGENTS.md` — infra-specific patterns: MCP/A2A conformance gates, adapter boundary rules,
      TypeScript-only constraint for this directory
- [x] Author `shared/AGENTS.md` — contract/schema authoring rules: `buf lint` gate, JSON Schema meta-schema
      compliance, no hand-editing of lockfiles
- [x] Author `.github/agents/AGENTS.md` — agent development conventions: frontmatter schema, tool selection rationale,
      handoff graph patterns, mandatory script coupling
- [x] Author `.github/agents/README.md` — agent catalog: name, posture, trigger conditions, handoff graph, and
      supporting scripts for every agent currently in the fleet

#### 3.1 Verification

- [x] Every nested `AGENTS.md` opens with a cross-reference to root `AGENTS.md` and only narrows (never contradicts)
      its constraints
- [x] `.github/agents/README.md` lists all agents with posture, trigger, and handoff targets
- [x] `pre-commit run validate-frontmatter --all-files` continues to exit 0 after all new files are added

### 3.2 Documentation Agent Fleet (`.github/agents/`)

Uses an Executive → sub-agent hierarchy: the Executive orchestrates and produces a gap report; sub-agents own
discrete tasks and are individually invokeable. All sub-agents read `docs/AGENTS.md` for context before acting.

- [x] Author `docs-executive.agent.md` — orchestrates all documentation work; delegates to scaffold / completeness /
      accuracy sub-agents; produces a documentation gap report; handoffs to Review and GitHub
- [x] Author `docs-scaffold.agent.md` — generates initial documentation (READMEs, JSDoc stubs, architecture diagram
      outlines) from module structure, schemas, and seed knowledge; driven by `scripts/docs/scaffold_doc.py`
- [x] Author `docs-completeness-review.agent.md` — audits the workspace for missing required documentation sections
      (README, interface docstrings, `agent-card.json` descriptions); driven by
      `scripts/docs/scan_missing_docs.py`; exits non-zero on gaps
- [x] Author `docs-accuracy-review.agent.md` — cross-references existing documentation against current implementation;
      flags stale descriptions, wrong paths, and outdated API references
- [x] Author `scripts/docs/scaffold_doc.py` — generates documentation scaffolds from module structure and
      `shared/schemas/`; `--dry-run` mode prints output without writing; `--module` flag scopes to one module
- [x] Author `scripts/docs/tests/test_scaffold_doc.py` — unit tests for scaffold logic and `--dry-run` flag
- [x] Author `scripts/docs/scan_missing_docs.py` — walks workspace and reports all modules/files missing required
      documentation; exits non-zero when gaps are found; `--dry-run` flag for CI use
- [x] Author `scripts/docs/tests/test_scan_missing_docs.py` — unit tests for gap detection and exit codes

#### 3.2 Verification

- [x] `uv run python scripts/docs/scan_missing_docs.py --dry-run` exits 0 on the current workspace
- [x] `uv run pytest scripts/docs/tests/ -v` exits 0
- [x] `docs-scaffold.agent.md` can generate a complete README stub for a hypothetical module without hallucinating
      file paths or API names
- [x] All docs agents appear in `.github/agents/README.md` with correct posture and handoff targets

### 3.3 Testing Agent Fleet (`.github/agents/`)

Mirrors the documentation fleet pattern: Executive orchestrates; sub-agents own scaffold / coverage / quality.
All sub-agents read `shared/AGENTS.md` and the relevant module `AGENTS.md` before running checks.

- [x] Author `test-executive.agent.md` — orchestrates the full testing lifecycle; runs coverage scan; delegates to
      scaffold and review sub-agents; ensures `uv run pytest` and `pnpm run test` pass before handoff to Review
- [x] Author `test-scaffold.agent.md` — generates test file stubs from TypeScript interfaces and Python type stubs
      (signatures + docstrings only; no business logic inferred); driven by `scripts/testing/scaffold_tests.py`
- [x] Author `test-coverage.agent.md` — identifies untested code paths; maps coverage gaps to module contracts;
      driven by `scripts/testing/scan_coverage_gaps.py`; exits non-zero if any module is below threshold
- [x] Author `test-review.agent.md` — reviews test quality: checks for meaningful assertions, validates
      Testcontainers use for integration tests, flags excessive mocking of internal collaborators
- [x] Author `scripts/testing/scaffold_tests.py` — generates test file stubs from source file interfaces;
      `--dry-run` mode; `--file` flag to scope to one source file
- [x] Author `scripts/testing/tests/test_scaffold_tests.py` — unit tests for stub generation logic and `--dry-run`
      flag
- [x] Author `scripts/testing/scan_coverage_gaps.py` — runs coverage tooling and reports all untested symbols by
      module; exits non-zero if any module is below its declared threshold; `--dry-run` flag for CI use
- [x] Author `scripts/testing/tests/test_scan_coverage_gaps.py` — unit tests for gap detection and threshold
      enforcement

#### 3.3 Verification

- [x] `uv run python scripts/testing/scan_coverage_gaps.py --dry-run` exits 0 on the current codebase
- [x] `uv run pytest scripts/testing/tests/ -v` exits 0
- [x] `test-scaffold.agent.md` can generate a test skeleton for `infrastructure/mcp/src/broker.ts` referencing
      correct import paths
- [x] All testing agents appear in `.github/agents/README.md`

### 3.4 Schema & Contract Agent Fleet (`.github/agents/`)

- [x] Author `schema-executive.agent.md` — orchestrates schema authoring and safe migration; enforces schemas-first
      constraint; delegates to validator and migration sub-agents; blocks implementation agents until schemas pass
- [x] Author `schema-validator.agent.md` — validates all JSON Schema files in `shared/schemas/` and `shared/types/`
      against their `$schema` meta-schema; runs `buf lint`; driven by `scripts/schema/validate_all_schemas.py`
- [x] Author `schema-migration.agent.md` — guides safe, backwards-compatible schema evolution; inventories all
      downstream consumers before approving field removals or type changes; records migration notes in
      `shared/schemas/CHANGELOG.md`
- [x] Author `scripts/schema/validate_all_schemas.py` — validates all JSON Schema files; checks required keys
      (`$schema`, `$id`, `title`, `type`); exits non-zero on any violation; `--dry-run` flag
- [x] Author `scripts/schema/tests/test_validate_all_schemas.py` — unit tests for required-key validation and exit
      codes

#### 3.4 Verification

- [x] `uv run python scripts/schema/validate_all_schemas.py` exits 0 on current `shared/schemas/` and
      `shared/types/`
- [x] `uv run pytest scripts/schema/tests/ -v` exits 0
- [x] All schema agents appear in `.github/agents/README.md`

### 3.5 Executive Planner Agent (`.github/agents/`)

- [x] Author `executive-planner.agent.md` — surveys codebase against `docs/Workplan.md`; reconciles checklist state;
      updates Workplan with minimum-diff edits; recommends next agent to engage; read-only on code

#### 3.5 Verification

- [x] `executive-planner.agent.md` is present at `.github/agents/executive-planner.agent.md` with valid
      frontmatter (`name`, `description`, `tools`, `handoffs`)
- [x] Agent posture is `read + edit`; `edit/editFiles` tool present; `runInTerminal` tool absent (minimum
      posture enforced)
- [x] Guardrails section explicitly restricts edits to `docs/Workplan.md` and `CHANGELOG.md` only — no code
      files may be modified
- [x] Agent listed in `.github/agents/README.md` under **Planning & Orchestration Agents** with posture
      `read + edit` and correct handoff targets (Review, GitHub, Executive Planner iterate)
- [x] `AGENTS.md` VS Code Custom Agents table updated to include Executive Planner
- [x] `executive-planner.agent.md` appears in VS Code Copilot agents dropdown *(manual: confirm in VS Code
      Copilot chat panel — file is correctly placed and formatted; auto-discovery is VS Code's responsibility)*

**Deliverables**: recursive `AGENTS.md` hierarchy established; documentation, testing, and schema agent fleets
operational with supporting scripts; Executive Planner tracking project state; all agents catalogued in
`.github/agents/README.md`.

### 3.6 Agent Governance Fleet (`.github/agents/`)

- [x] Author `executive-agent-scaffold.agent.md` — full posture; orchestrates
      new agent creation; provides brief to Scaffold Agent; runs post-creation
      validation; delegates to Review Agent and GitHub
- [x] Update `scaffold-agent.agent.md` — add `.github/agents/AGENTS.md` as
      source #1; update handoffs to `Review Agent` and `Agent Scaffold Executive`
- [x] Author `review-agent.agent.md` — read-only specialist review of `.agent.md`
      and `AGENTS.md` hierarchy files; FAIL/WARN/PASS report format
- [x] Author `update-agent.agent.md` — read + create; applies minimum-diff
      corrections to existing agent files; hands off to Review Agent
- [x] Author `govern-agent.agent.md` — read-only fleet-wide compliance audit;
      produces fleet health report; hands off to Update Agent

#### 3.6 Verification

- [x] All five governance agent files present in `.github/agents/` with valid
      frontmatter (`name`, `description`, `tools`, `handoffs`)
- [x] Posture enforced: `executive-agent-scaffold` is full; `review-agent` and
      `govern-agent` are read-only; `update-agent` is read + create
- [x] All `handoffs[].agent` values reference existing agent `name` fields exactly
- [x] Each agent body has: bold role statement, endogenous sources section,
      workflow/checklist, and guardrails section
- [x] All five agents listed in `.github/agents/README.md` under Agent Governance
      Fleet with posture, trigger, and handoff targets
- [x] Root `AGENTS.md` VS Code Custom Agents table updated to include all five
      new agents
- [x] `pre-commit run validate-frontmatter --all-files` exits 0 after all new
      files are added

---

## Phase 4 — Group I: Signal Processing Modules

**Goal**: Implement the sensory boundary of the system — raw signal ingestion,
attentional gating, and feature extraction.

### 4.1 Sensory / Input Layer (`modules/group-i-signal-processing/sensory-input/`)

- [x] Implement signal ingestion for text, image, audio, API events, and sensor stream modalities
- [x] Implement normalization, timestamping, and upward dispatch
- [ ] Wire MCP + A2A interfaces; author `agent-card.json`
- [x] Write unit and integration tests; author `README.md`

### 4.2 Attention & Filtering Layer (`modules/group-i-signal-processing/attention-filtering/`)

- [x] Implement salience scoring, relevance filtering, and signal routing
- [x] Implement top-down attention modulation interface (receives directives from Executive layer)
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.3 Perception Layer (`modules/group-i-signal-processing/perception/`)

- [x] Implement feature extraction, pattern recognition, language understanding, scene parsing, and multimodal fusion
      pipeline
- [x] Wire `brain.perception` vector collection via shared adapter; embed extracted feature representations
- [x] Configure `pipeline.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: end-to-end signal flow from raw input through perception, with features persisted to
`brain.perception`.

---

## Phase 5 — Group II: Cognitive Processing Modules

**Goal**: Implement memory across all timescales, affective modulation, and the reasoning/planning engine.

### 5.1 Working Memory (`modules/group-ii-cognitive-processing/memory/working-memory/`)

- [ ] Implement in-process KV store with read, write, evict operations
- [ ] Implement retrieval-augmented loader: queries `brain.short-term-memory` and `brain.long-term-memory` to assemble
      context window per turn; respect token budget
- [ ] Implement consolidation pipeline: dispatch evicted items to episodic / long-term memory
- [ ] Configure `capacity.config.json` and `retrieval.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.2 Short-Term Memory (`modules/group-ii-cognitive-processing/memory/short-term-memory/`)

- [ ] Implement session-scoped record store with TTL management (Redis/Valkey backend)
- [ ] Wire `brain.short-term-memory` collection; embed session records via Ollama `nomic-embed-text`
- [ ] Implement semantic search over current session to serve working memory loader
- [ ] Configure `ttl.config.json`, `vector-store.config.json`, `embedding.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.3 Long-Term Memory (`modules/group-ii-cognitive-processing/memory/long-term-memory/`)

- [ ] Implement configurable vector DB adapter for `brain.long-term-memory` (ChromaDB default, Qdrant for production)
- [ ] Implement knowledge graph adapter (Kuzu default, Neo4j for production)
- [ ] Implement SQL adapter for structured fact storage (SQLite default, PostgreSQL for production)
- [ ] Implement embedding pipeline with frontmatter-aware section chunking (respects `brain-structure.md` region
      boundaries)
- [ ] Implement semantic + hybrid retrieval (vector + keyword) with re-ranking
- [ ] Implement boot-time seed pipeline: chunk and embed all `resources/static/knowledge/` documents via LlamaIndex
- [ ] Configure `vector-store.config.json`, `embedding.config.json`, `indexing.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.4 Episodic Memory (`modules/group-ii-cognitive-processing/memory/episodic-memory/`)

- [ ] Implement ordered event log with temporal indexing
- [ ] Wire `brain.episodic-memory` collection; embed episode records for semantic + temporal composite queries
- [ ] Implement temporal replay, semantic episode search, and composite queries
- [ ] Configure `vector-store.config.json`, `embedding.config.json`, `retention.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.5 Affective / Motivational Layer (`modules/group-ii-cognitive-processing/affective/`)

- [ ] Implement reward signal generation, emotional weighting, urgency scoring, and prioritization cue dispatch
- [ ] Wire `brain.affective` collection; embed reward and emotional state history
- [ ] Configure `drive.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.6 Decision-Making & Reasoning Layer (`modules/group-ii-cognitive-processing/reasoning/`)

- [ ] Implement logical reasoning, causal inference, planning under uncertainty, and conflict resolution via DSPy
- [ ] Integrate Guidance for constrained/structured generation in policy-following contexts
- [ ] Wire `brain.reasoning` collection; embed inference traces, plans, and causal models
- [ ] Route all LLM calls through LiteLLM
- [ ] Configure `strategy.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: full memory stack operational with seed pipeline verified, reasoning layer producing traceable
inference records.

---

## Phase 6 — Group III: Executive & Output Modules

**Goal**: Implement the agent's executive identity, runtime orchestration, and environment effectors.

### 6.1 Executive / Agent Layer (`modules/group-iii-executive-output/executive-agent/`)

- [ ] Implement agent identity management and self-model
- [ ] Implement persistent goal stack with prioritization and lifecycle management
- [ ] Implement policy engine with value evaluation and top-down modulation dispatch
- [ ] Wire `brain.executive-agent` collection; embed goals, values, policies, and identity state
- [ ] Configure `identity.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 6.2 Agent Execution (Runtime) Layer (`modules/group-iii-executive-output/agent-runtime/`)

- [ ] Implement task decomposition, tool/function selection, and skill pipeline execution via Temporal (primary) or
      Prefect (fallback)
- [ ] Implement sequencing and inter-module coordination
- [ ] Configure tool registry
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 6.3 Motor / Output / Effector Layer (`modules/group-iii-executive-output/motor-output/`)

- [ ] Implement API call dispatch, message delivery, file writes, rendered output generation, and control signal
      emission
- [ ] Implement upward feedback confirmation loop
- [ ] Configure output channel definitions
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: end-to-end decision-to-action pipeline verified; agent can receive a goal, reason about it, and
produce a measurable environmental output.

---

## Phase 7 — Group IV: Adaptive Systems (Cross-Cutting)

**Goal**: Implement learning, reinforcement, and meta-cognitive monitoring layers that refine the system over time.

### 7.1 Learning & Adaptation Layer (`modules/group-iv-adaptive-systems/learning-adaptation/`)

- [ ] Implement reinforcement signal processing and parameter update dispatch via Stable-Baselines3 (scale to RLlib /
      TorchRL as needed)
- [ ] Implement behavioural conditioning pipelines
- [ ] Implement skill acquisition and capability registration
- [ ] Wire `brain.learning-adaptation` collection; embed feedback logs and skill acquisition records
- [ ] Configure `learning.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 7.2 Meta-cognition & Monitoring Layer (`modules/group-iv-adaptive-systems/metacognition/`)

- [ ] Implement confidence tracking, error detection, performance evaluation, and anomaly escalation to executive layer
      via OpenTelemetry
- [ ] Implement corrective action trigger dispatch and remediation pipelines
- [ ] Wire `brain.metacognition` collection; embed confidence scores, error patterns, and performance snapshots
- [ ] Configure `monitoring.config.json` and `vector-store.config.json`
- [ ] Wire MCP + A2A hooks; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: system can detect its own errors, escalate anomalies, and register reinforcement signals that
influence subsequent decisions.

---

## Phase 8 — Application Layer & Observability

**Goal**: Expose the system to external users and operators through a minimal, accessible, mobile-responsive web
interface; provide developer transparency into internal signal and memory state; wire the full MCP authorization
layer; and verify end-to-end signal flow with full telemetry. The default shell is intentionally generic boilerplate
— designed to be forked, styled, and extended without requiring changes to the underlying cognitive modules.

**Architecture note**: The browser client does NOT connect directly to the MCP server. The Hono API gateway acts as
a Backend-for-Frontend (BFF): it is an MCP client (connecting to `infrastructure/mcp` via the canonical Streamable
HTTP transport, spec 2025-06-18), an SSE relay (streaming MCP push events to the browser), and an auth gate
(validating Bearer tokens on all `/api/*` routes). This keeps the MCP port off the public network, prevents DNS
rebinding attacks as required by the MCP transport security spec, and provides a single surface for CORS policy.

### 8.1 Hono API Gateway (`apps/default/server/`)

- [ ] Scaffold TypeScript package: Hono on Node.js (`@hono/node-server`); add to `pnpm-workspace.yaml`
- [ ] Implement MCP client adapter: connect to `infrastructure/mcp` server via Streamable HTTP; relay `MCPContext`
      envelopes between browser sessions and the MCP backbone
- [ ] Expose SSE endpoint `GET /api/stream` — relay server-side MCP push events (token streaming, module
      notifications) to the browser via `text/event-stream`; support `Last-Event-ID` header for resumability per
      MCP transport spec
- [ ] Expose REST endpoint `POST /api/input` — accept user input, wrap in `Signal` envelope, dispatch to
      Sensory/Input Layer via MCP; return `202 Accepted` + SSE session ID
- [ ] Expose health endpoint `GET /api/health` — return gateway + MCP server connectivity status
- [ ] Add CORS middleware: validate `Origin` header; restrict to configured allowed origins (default:
      `http://localhost:*`); reject unrecognised origins to prevent DNS rebinding per MCP spec §2.0.1
- [ ] Serve Vite-built SPA static assets from `apps/default/client/dist/`
- [ ] Configure environment via `.env` (MCP server URL, allowed origins, JWT secret, token TTL); document all
      variables in `apps/default/.env.example`
- [ ] Write unit and integration tests; author `README.md`

#### 8.1 Verification

- [ ] `pnpm run dev` starts gateway on `localhost:3001` without error
- [ ] `POST /api/input` returns `202 Accepted` with a valid SSE session ID when MCP server is running
- [ ] `GET /api/stream` opens an SSE stream and receives push events from MCP
- [ ] `GET /api/health` returns `{ "gateway": "ok", "mcp": "ok" }` when both services are up
- [ ] CORS middleware rejects requests from non-allowlisted origins with `HTTP 403`

### 8.2 MCP OAuth 2.1 Auth Layer (`apps/default/server/auth/` + `infrastructure/mcp/src/auth.ts`)

- [ ] Expose `GET /.well-known/oauth-protected-resource` on the MCP server — return Protected Resource Metadata
      per RFC 9728, pointing to the local authorization server on the Hono gateway
- [ ] Expose `GET /.well-known/oauth-authorization-server` on the Hono gateway — return Authorization Server
      Metadata per RFC 8414
- [ ] Implement local JWT auth stub: `POST /auth/login` (username + password → short-lived JWT access token +
      longer-lived refresh token); document this as a replaceable boilerplate identity provider in `README.md`
- [ ] Implement PKCE authorization code flow: `GET /auth/authorize`, `POST /auth/token`, `POST /auth/refresh`,
      `DELETE /auth/session` (explicit session termination per MCP session management spec)
- [ ] Add Bearer token validation middleware to all `/api/*` routes; return `HTTP 401` with `WWW-Authenticate`
      header on failure per RFC 9728 §5.1
- [ ] Store refresh token in `HttpOnly` cookie (never `localStorage`); access token in memory only
- [ ] Write unit tests for token issuance, validation, PKCE flow, clock-skew tolerance, and expiry; author
      `README.md`

#### 8.2 Verification

- [ ] `POST /auth/login` with valid credentials returns a JWT access token and `HttpOnly` refresh-token cookie
- [ ] `GET /.well-known/oauth-protected-resource` returns a conformant RFC 9728 document
- [ ] `GET /.well-known/oauth-authorization-server` returns a conformant RFC 8414 document
- [ ] Unauthenticated `POST /api/input` returns `HTTP 401` with `WWW-Authenticate` header
- [ ] Authenticated request with valid Bearer token is accepted and forwarded to the MCP backbone
- [ ] Expired access token returns `HTTP 401`; `POST /auth/refresh` with valid cookie issues a new access token

### 8.3 Browser Client (`apps/default/client/`)

- [ ] Scaffold Vite + React TypeScript SPA (`@vitejs/plugin-react`); add to `pnpm-workspace.yaml`; configure
      `vite.config.ts` for HMR in dev and an optimized production build; document the framework choice as
      explicitly replaceable boilerplate in `README.md` (Preact, Solid, Svelte, vanilla are all valid swaps)
- [ ] Implement two-tab shell layout:
  - **Tab 1 — Chat**: text input → `POST /api/input`; `EventSource` listener on `GET /api/stream` renders
        streamed tokens in real time; conversation history persisted in session storage; clear/reset control;
        visual loading and error states
  - **Tab 2 — Internals** (developer transparency panel): see components below
- [ ] Implement Internals panel components:
  - **Agent card browser**: fetches `/.well-known/agent-card.json` from each registered module via the
        gateway; displays name, version, A2A endpoint, capabilities, and MCP tool list
  - **Active collections viewer**: queries the vector store collection registry API; shows collection name,
        backend, record count, and last-updated timestamp
  - **Signal trace feed**: live SSE subscription to internal MCP message events; displays `traceId`, source
        module, target module, message type, and ISO timestamp; filterable by module name
  - **Working memory inspector**: shows the last N context window items assembled by Working Memory;
        token-budget bar visualization; auto-refreshes every 5 s
- [ ] Implement auth UI: login form, logout button, silent token refresh (auto-retry on `401`), token expiry
      countdown indicator
- [ ] Apply **WCAG 2.1 AA** accessibility standards throughout: semantic HTML5 landmarks, ARIA roles and
      live-regions for streamed content, full keyboard navigation, visible focus indicators, color contrast
      ≥ 4.5:1 (normal text) and ≥ 3:1 (large/UI), `prefers-reduced-motion` support
- [ ] Apply **mobile-responsive layout**: CSS custom properties for theming (no CSS-framework lock-in for
      forks); single-column stack below 768 px; touch-friendly interactive targets ≥ 44 × 44 px; no
      horizontal scroll at any viewport width ≥ 320 px
- [ ] Write component unit tests (Vitest + Testing Library); write E2E smoke test (Playwright: login → send
      message → receive streamed response → verify Internals panel loads); author `README.md`

#### 8.3 Verification

- [ ] `pnpm run build` in `apps/default/client/` produces a valid `dist/` bundle; initial gzipped JS chunk
      < 200 kB
- [ ] Chat tab sends a message and renders a streamed response end-to-end with the live system
- [ ] Internals panel loads agent cards and at least one active collection when the system is running
- [ ] Signal trace feed shows live MCP events in real time
- [ ] Lighthouse accessibility audit scores ≥ 90 on both tabs in production build
- [ ] Layout renders correctly at 320 px, 768 px, and 1440 px viewport widths (Playwright snapshot assertions)
- [ ] All Vitest unit tests and Playwright E2E smoke test pass

### 8.4 Observability (`observability/`)

- [ ] Finalize structured log emitters (structlog / pino) across all modules per `shared/utils/logging.md`
- [ ] Wire OpenTelemetry trace context propagation across all inter-module boundaries per
      `shared/utils/tracing.md`
- [ ] Instrument Hono gateway: emit OTel spans for all `/api/*` routes; propagate `traceId` from incoming
      request headers into `MCPContext` envelopes forwarded to the backbone
- [ ] Provision Grafana dashboards: module health, signal-flow latency, memory collection sizes, and gateway
      request rate / error rate
- [ ] Author `README.md`

#### 8.4 Verification

- [ ] A browser request generates a complete trace in Grafana — gateway → Sensory/Input → … →
      Motor/Output/Effector — with a single propagated `traceId`
- [ ] Gateway error rate dashboard shows non-zero data after a test run with deliberate failures
- [ ] All module log emitters produce valid structured JSON per `shared/utils/logging.md`

### 8.5 MCP Resource Registry (`resources/`)

- [ ] Populate `uri-registry.json` with all resource URI patterns across modules
- [ ] Author `access-control.md`
- [ ] Populate per-layer resource definition files (`group-i` → `group-iv`)
- [ ] Author `README.md`

**Deliverables**: fully accessible, mobile-responsive two-tab web shell; OAuth 2.1 + PKCE JWT auth stub with spec-
compliant `/.well-known/` metadata endpoints; end-to-end SSE streaming from user input to rendered response;
Internals transparency panel showing live agent cards, signal traces, and memory state; trace IDs propagating
from browser request to effector output, visible in Grafana.

---

## Phase 9 — Cross-Cutting: Security, Deployment & Documentation

**Goal**: Harden the system, package it for deployment, and ensure the documentation is complete and self-referential.

### 9.1 Security (`security/`)

- [ ] Define module sandboxing policies and capability isolation rules with OPA
- [ ] Configure gVisor sandbox templates for module containers
- [ ] Perform security review of all inter-module interfaces; document findings
- [ ] Author `README.md` and `docs/guides/security.md`

### 9.2 Deployment (`deploy/`)

- [ ] Write per-module `Dockerfile` definitions; author base image
- [ ] Write Kubernetes manifests: per-module deployments, services, HPA configurations
- [ ] Validate `docker-compose.yml` covers the full local development stack
- [ ] Author `docs/guides/deployment.md`

### 9.3 Documentation Completion

- [ ] Author `docs/architecture.md` — full architectural overview with signal-flow diagrams
- [ ] Author `docs/guides/getting-started.md` — environment setup and first-run walkthrough
- [ ] Author `docs/guides/adding-a-module.md` — step-by-step module creation guide
- [ ] Author `docs/guides/observability.md` — telemetry setup and dashboard usage
- [ ] Review and finalize `README.md` quick-start guide

**Deliverables**: system deployable via `docker-compose up` locally and via `kubectl apply` to a Kubernetes cluster, all
documentation complete and cross-linked.

---

## Phase 10 — Neuromorphic Layer (Optional / Pluggable)

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
| **M3 — Dev Agent Fleet Live**     | 3        | All agent fleets operational; recursive `AGENTS.md` hierarchy in place; scripts passing   |
| **M4 — Signal Boundary Live**     | 4        | Text input reaches `brain.perception` collection                                          |
| **M5 — Memory Stack Live**        | 5        | Seed pipeline populates `brain.long-term-memory`; working memory assembles context window |
| **M6 — End-to-End Decision Loop** | 6        | Goal → Reason → Act pipeline produces verifiable output                                   |
| **M7 — Adaptive Systems Active**  | 7        | Error detection escalates to executive; reinforcement signals registered                  |
| **M8 — User-Facing**              | 8        | Browser shell accessible at `localhost`; Chat tab streams responses end-to-end; Internals panel shows live agent state; OAuth 2.1 auth stub operational; traces visible in Grafana |
| **M9 — Production-Ready**         | 9        | Kubernetes deploy succeeds; all documentation complete                                    |

---

## Open Questions & Deferred Decisions

- **A2A version lock**: confirm which A2A spec release to align to before Phase 2 begins.
- **Temporal vs. Prefect**: run a comparative spike during Phase 6 before committing to Temporal for `agent-runtime/`.
- **Graph store selection**: Kuzu (embedded) is the default for `long-term-memory/graph-store/`; validate storage limits
  before Phase 5 closes.
- **WebMCP evaluation**: ~~resolved in Phase 8 planning~~ — `webmcp.dev` is a library that makes existing websites
  controllable *by* external MCP clients (e.g. Claude Desktop); it is the reverse of what EndogenAI needs, and the
  underlying `WebMCP/webmcp` GitHub project is pre-production (1 star, no releases). The boilerplate uses the MCP
  **Streamable HTTP** transport (spec 2025-06-18) via the Hono BFF gateway instead. Closed.
- **Client-side framework**: the boilerplate SPA defaults to React (Vite + `@vitejs/plugin-react`); confirm whether
  Preact is preferred (identical API, ~3 kB vs ~45 kB gzipped) — defer final decision to Phase 8.3 start.
- **External IdP integration**: the Phase 8.2 JWT stub is the minimum viable auth layer; production forks replace it
  with an OIDC provider (Keycloak, Auth0, Okta). Decide before Phase 8.2 closes whether the boilerplate should
  include an optional Keycloak Docker Compose profile as a second reference implementation.
- **SSE proxy compatibility**: some corporate proxies and browser extensions buffer SSE streams, breaking real-time
  token rendering. Determine whether a long-polling fallback for `GET /api/stream` is required in the boilerplate
  or left to forks — defer to Phase 8.3.
- **Neuromorphic prioritization**: decide if Phase 10 is in-scope for v1 or deferred to v2.
- **Agent fleet scope**: confirm whether all four Phase 3 sub-fleets (docs, testing, schema, planner) are in-scope
  together or should be time-boxed and delivered incrementally within Phase 3.
- **Phase-3 Executive agent**: determine whether a dedicated Phase-3 Executive agent should be scaffolded to drive
  Phase 3 delivery, or whether the existing Plan → Implement → Review workflow is sufficient.
