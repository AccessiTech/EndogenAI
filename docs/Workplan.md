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
- [x] Wire MCP + A2A interfaces; author `agent-card.json`
- [x] Write unit and integration tests; author `README.md`

### 4.2 Attention & Filtering Layer (`modules/group-i-signal-processing/attention-filtering/`)

- [x] Implement salience scoring, relevance filtering, and signal routing
- [x] Implement top-down attention modulation interface (receives directives from Executive layer)
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 4.3 Perception Layer (`modules/group-i-signal-processing/perception/`)

- [x] Implement feature extraction, pattern recognition, language understanding, scene parsing, and multimodal fusion
      pipeline
- [x] Wire `brain.perception` vector collection via shared adapter; embed extracted feature representations
- [x] Configure `pipeline.config.json` and `vector-store.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: end-to-end signal flow from raw input through perception, with features persisted to
`brain.perception`.

---

## Phase 5 — Group II: Cognitive Processing Modules

**Goal**: Implement memory across all timescales, affective modulation, and the reasoning/planning engine.

**Build sequence** (strict dependency order within the memory group): §5.2 → §5.3 → §5.4 → §5.1 → §5.5 → §5.6. Working Memory (§5.1) must be built last within the memory group because it assembles from the three stores beneath it. Gate 1 (all four memory modules passing tests) must pass before §5.5 begins; Gate 2 (§5.5 passing tests) before §5.6.

### 5.1 Working Memory (`modules/group-ii-cognitive-processing/memory/working-memory/`)

- [x] Implement in-process KV store with read, write, evict operations
- [x] Implement retrieval-augmented loader: queries `brain.short-term-memory`, `brain.long-term-memory`, and
      `brain.episodic-memory` to assemble context window per turn; respect token budget
- [x] Implement consolidation pipeline: dispatch evicted items via STM's A2A `consolidate_item` endpoint; STM
      routes to `brain.episodic-memory` or `brain.long-term-memory` (WM does not write to those collections directly)
- [x] Configure `capacity.config.json` and `retrieval.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.2 Short-Term Memory (`modules/group-ii-cognitive-processing/memory/short-term-memory/`)

- [x] Implement session-scoped record store with TTL management (Redis 7 backend; `redis:7-alpine`)
- [x] Wire `brain.short-term-memory` collection; embed session records via Ollama `nomic-embed-text`
- [x] Implement near-duplicate novelty detection (DG pattern separation analogue): query nearest neighbour before
      write; cosine similarity > 0.9 → update existing item rather than create new
- [x] Implement consolidation pipeline: SCAN→SCORE→GATE→EMBED→PRUNE — promote scored items to
      `brain.episodic-memory` (items with `sessionId + sourceTaskId + createdAt`) or `brain.long-term-memory`
- [x] Implement semantic search over current session to serve working memory loader
- [x] Configure `ttl.config.json`, `vector-store.config.json`, `embedding.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.3 Long-Term Memory (`modules/group-ii-cognitive-processing/memory/long-term-memory/`)

- [x] Implement configurable vector DB adapter for `brain.long-term-memory` (ChromaDB default, Qdrant for production)
- [x] Implement knowledge graph adapter (Kuzu default, Neo4j for production)
- [x] Implement SQL adapter for structured fact storage (SQLite default, PostgreSQL for production)
- [x] Implement embedding pipeline with frontmatter-aware section chunking (respects `brain-structure.md` region
      boundaries)
- [x] Implement semantic + hybrid retrieval (vector + keyword) with re-ranking
- [x] Implement boot-time seed pipeline: chunk and embed all `resources/static/knowledge/` documents via LlamaIndex
- [x] Configure `vector-store.config.json`, `embedding.config.json`, `indexing.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.4 Episodic Memory (`modules/group-ii-cognitive-processing/memory/episodic-memory/`)

- [x] Implement ordered event log with temporal indexing; enforce what-where-when immutability contract
      (`sessionId`, `sourceTaskId`, `createdAt`, `affectiveValence` required on all episodic items; content frozen
      at write time)
- [x] Wire `brain.episodic-memory` collection; embed episode records for semantic + temporal composite queries
- [x] Implement temporal replay, semantic episode search, and composite queries
- [x] Implement episodic distillation pipeline: cluster recurring patterns and promote to `brain.long-term-memory`
      via LTM A2A `write_item`; runs on schedule (cron hourly) or explicit trigger
- [x] Configure `vector-store.config.json`, `embedding.config.json`, `retention.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.5 Affective / Motivational Layer (`modules/group-ii-cognitive-processing/affective/`)

- [x] Implement reward signal generation, emotional weighting, urgency scoring, and prioritization cue dispatch
- [x] Wire `brain.affective` collection; embed reward and emotional state history
- [x] Configure `drive.config.json` and `vector-store.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 5.6 Decision-Making & Reasoning Layer (`modules/group-ii-cognitive-processing/reasoning/`)

- [x] Implement logical reasoning, causal inference, planning under uncertainty, and conflict resolution via DSPy
      (`ChainOfThought`, `ProgramOfThought`, `ReAct`, `MultiChainComparison`)
- [x] Integrate `guidance` package for constrained/structured generation in inhibitory-control contexts; wired
      into `inference.py` — no standalone module file required
- [x] Wire `brain.reasoning` collection; embed inference traces, plans, and causal models
- [x] Route all LLM calls through LiteLLM
- [x] Configure `inference.config.json` and `vector-store.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

**Deliverables**: full memory stack operational with seed pipeline verified, reasoning layer producing traceable
inference records.

---

## Phase 6 — Group III: Executive & Output Modules

**Goal**: Implement the agent's executive identity, runtime orchestration, and environment effectors.

**Research references**:
- `docs/research/phase-6-neuroscience-executive-output.md` (D1)
- `docs/research/phase-6-technologies-executive-output.md` (D2)
- `docs/research/phase-6-synthesis-workplan.md` (D3)
- `docs/research/phase-6-detailed-workplan.md` (D4 — implementation spec)

### 6.0 Pre-Implementation Gates (must complete before §§6.1–6.3 begin)

- [x] **Phase 5 gate**: confirm §§5.1–5.4 memory modules are operational (`uv run pytest` passes for
      working-memory, short-term-memory, long-term-memory, episodic-memory)
- [x] **Schemas-first**: land 5 new shared schemas in `shared/schemas/` before any Phase 6 code:
      `executive-goal.schema.json`, `skill-pipeline.schema.json`, `action-spec.schema.json`,
      `motor-feedback.schema.json`, `policy-decision.schema.json` — all passing `buf lint` and
      `scripts/schema/validate_all_schemas.py`
- [x] **Temporal vs. Prefect spike**: run spike per `docs/research/phase-6-detailed-workplan.md §8`;
      record decision in `docs/research/temporal-prefect-spike.md` before §6.2 implementation
- [x] **OPA deployment decision**: resolve embedded vs. standalone HTTP (recommendation: standalone
      at `localhost:8181`); add `opa` service to `docker-compose.yml`
- [x] **Collection registry**: add `brain.executive-agent` entry to
      `shared/vector-store/collection-registry.json`
- [x] **Docker Compose**: add `temporal` (ports 7233, 8233) and `opa` (port 8181) services to
      `docker-compose.yml`
- [x] **Scaffold directory**: create `modules/group-iii-executive-output/` tree per D4 §3

### 6.1 Executive / Agent Layer (`modules/group-iii-executive-output/executive-agent/`)

- [x] Implement agent identity management and self-model (`identity.py`; loads `identity.config.json`;
      append-only writes to `brain.executive-agent`)
- [x] Implement persistent goal stack with prioritization and lifecycle management (`goal_stack.py`;
      7-state FSM: PENDING → EVALUATING → COMMITTED → EXECUTING → COMPLETED / FAILED / DEFERRED)
- [x] Implement BDI interpreter loop (`deliberation.py`; option-generation → value scoring →
      policy evaluation → intention commitment → reconsideration check)
- [x] Implement OPA policy engine client (`policy.py`; three Rego policies: `identity.rego`,
      `goals.rego`, `actions.rego`; HTTP client to standalone OPA server)
- [x] Implement `MotorFeedback` receiver (`feedback.py`; updates goal score; emits `RewardSignal`
      to affective module; closes actor-critic loop)
- [x] Wire `brain.executive-agent` collection; embed goals, values, policies, and identity state
- [x] Configure `identity.config.json`, `vector-store.config.json`, `embedding.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 6.2 Agent Execution (Runtime) Layer (`modules/group-iii-executive-output/agent-runtime/`)

- [x] Implement goal decomposition into ordered `SkillPipeline` via LiteLLM Activity
      (`decomposer.py`; falls back to local LiteLLM call if Phase 5 reasoning module not yet
      operational)
- [x] Implement durable `IntentionWorkflow` via Temporal (`workflow.py`; Signal=abort,
      Update=revise_plan, Query=get_status; strict determinism: all I/O in Activities)
- [x] Implement Prefect circuit-breaker fallback (`prefect_fallback.py`; triggered after
      `maxTemporalConnectRetries` failures; same pipeline interface as Temporal variant)
- [x] Implement unified orchestrator selector (`orchestrator.py`; primary/fallback routing)
- [x] Implement tool registry with A2A `/.well-known/agent-card.json` discovery
      (`tool_registry.py`; periodic health checks)
- [x] Implement Temporal Activities (`activities.py`: `decompose_goal`, `dispatch_to_motor_output`,
      `emit_partial_feedback`)
- [x] Configure `orchestrator.config.json` and `tool-registry.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 6.3 Motor / Output / Effector Layer (`modules/group-iii-executive-output/motor-output/`)

- [x] Implement channel-based action dispatcher (`dispatcher.py`; corollary discharge pre-action
      signal; concurrent batch dispatch via `asyncio.gather`)
- [x] Implement channel handlers: `http_channel.py`, `a2a_channel.py`, `file_channel.py`,
      `render_channel.py` (LiteLLM-backed)
- [x] Implement PMd-analogue channel selector (`channel_selector.py`; context-dependent routing)
- [x] Implement three-tier error policy (`error_policy.py`: tier 1 retry, tier 2 circuit-breaker,
      tier 3 escalate to executive-agent A2A)
- [x] Implement `MotorFeedback` emission after every dispatch (`feedback.py`; active push to
      executive-agent A2A `receive_feedback`; deviation_score computed from predicted vs. actual)
- [x] Configure `channels.config.json` and `error-policy.config.json`
- [x] Wire MCP + A2A; author `agent-card.json`; write tests; author `README.md`

### 6.4 End-to-End Integration

- [x] Write `test_integration_full_pipeline` spanning all three modules: push `GoalItem` to
      executive-agent A2A → verify Temporal Workflow created → confirm `ActionSpec` dispatched by
      motor-output → verify `MotorFeedback` returned to executive-agent → assert goal reaches
      `COMPLETED` lifecycle state
- [x] Declare M6 milestone: agent produces a measurable environmental output from a goal input;
      all Gate 0–3 checks pass (per `docs/research/phase-6-detailed-workplan.md §10`)

**Deliverables**: end-to-end decision-to-action pipeline verified; agent can receive a goal, reason about it, and
produce a measurable environmental output.

---

## Phase 7 — Group IV: Adaptive Systems (Cross-Cutting)

**Goal**: Implement learning, reinforcement, and meta-cognitive monitoring layers that refine the system over time.

**Architecture note**: All implementation decisions for Phase 7 are resolved. Full detail in
`docs/research/phase-7-detailed-workplan.md`. Key decisions:
- **Decision 1** — `motor-feedback.schema.json` refactored to `$ref shared/types/reward-signal.schema.json`
- **Decision 2** — `BrainEnv` uses **goal-priority adaptation** (Option A): `Box(K floats)` action space; RL policy
  adjusts `ExecutiveGoal.priority_weight` per goal class; episode boundary = one BDI planning cycle
- **Decision 3** — metacognition monitors **Phase 6 outputs only** (`executive-agent` + `motor-output`)
- **Observation strategy** — Hybrid (Strategy C): Tier 1 FastAPI OTel auto-instrumentation + Tier 2 A2A observer hook;
  Phase 6 activated via `METACOGNITION_URL` env var (default `None` — Phase 6 runs without Phase 7)
- **Build order** — §7.2 metacognition builds before §7.1 learning-adaptation (no ML dependencies; bootstraps
  observability layer that learning-adaptation can emit into from day one)

### Phase 7 Pre-Implementation Checklist

- [x] **Schemas-first**: land 3 new/updated schemas in `shared/schemas/` before any Phase 7 code —
      refactor `motor-feedback.schema.json` (`$ref` reward-signal); add
      `learning-adaptation-episode.schema.json` (Option A shape: `goal_priority_deltas: list[float]`,
      `episode_boundary: bdi_cycle`); add `metacognitive-evaluation.schema.json` — all passing `buf lint`
      and `scripts/schema/validate_all_schemas.py`
- [x] **Collection registry**: add `brain.learning-adaptation` and `brain.metacognition` entries to
      `shared/vector-store/collection-registry.json`
- [x] **Phase 6 instrumentation — Tier 1**: add `FastAPIInstrumentor.instrument_app(app)` to
      `executive-agent/server.py` and `motor-output/server.py`; add
      `opentelemetry-instrumentation-fastapi>=0.50b0` to both `pyproject.toml` files
- [x] **Phase 6 instrumentation — Tier 2**: add optional `metacognition_client` A2A hook to
      `executive-agent/feedback.py` `FeedbackHandler`; wire via `METACOGNITION_URL` env var in
      `executive-agent/server.py` (default `None`)
- [x] **Prometheus alert rules**: mount `observability/prometheus-rules/` directory in
      `docker-compose.yml` prometheus service; add `rule_files` entry to `prometheus.yml`
- [x] **Scaffold directory**: create `modules/group-iv-adaptive-systems/` tree per
      `docs/research/phase-7-detailed-workplan.md §3`

### 7.1 Learning & Adaptation Layer (`modules/group-iv-adaptive-systems/learning-adaptation/`)

_Service port: 8170. Depends on Gate 1 (metacognition operational) and Phase 6 OTel instrumentation._

- [x] Implement `BrainEnv` (`env/brain_env.py`) — `gymnasium.Env` wrapping `MotorFeedback` stream;
      observation: `[success_rate, mean_deviation, escalation_rate, task_type_onehot[K], channel_success_rate[5]]`;
      action: signed goal-priority-weight delta per goal class (`Box(K floats)`, clipped `[-0.2, +0.2]`);
      episode boundary = one BDI planning cycle
- [x] Implement PPO training loop via Stable-Baselines3 (`training/trainer.py`) with dual-track
      learning: BG actor-critic (PPO) + cerebellar supervised correction
      (`training/skill_feedback_callback.py`); shadow policy trained offline and promoted after
      `shadow_promotion_eval_episodes` consecutive above-threshold evaluations
- [x] Implement ChromaDB-backed `ReplayBuffer` (`replay/buffer.py`) — priority sampling by `|reward_value|`;
      rolling eviction when `size > replay_buffer_size`; async background training loop
      (`async_replay_interval_seconds`)
- [x] Implement `HabitManager` (`habits/manager.py`) — promotes stable policies to habit checkpoints
      when `success_rate ≥ 0.95` over 20 consecutive episodes (dorsolateral striatum analogue)
- [x] Wire `brain.learning-adaptation` ChromaDB collection; embed episode state-action-reward-next_state
      tuples with `task_type` and `priority` metadata
- [x] Configure `learning.config.json` (algorithm, `total_timesteps_per_run`, `replay_buffer_size`,
      `habit_threshold_*`, `shadow_policy_enabled`, `async_replay_interval_seconds`)
- [x] Wire MCP resources (`policy/current`, `replay-buffer/stats`, `habits/catalog`) + A2A tasks
      (`adapt_policy` inbound, `habit_promoted` outbound); author `agent-card.json`; write tests;
      author `README.md`

### 7.2 Meta-cognition & Monitoring Layer (`modules/group-iv-adaptive-systems/metacognition/`)

_Service port: 8171. Builds first — no ML dependencies; activates Phase 6 observability._

- [x] Configure OTel `TracerProvider` + `MeterProvider` (`instrumentation/otel_setup.py`) — OTLP gRPC
      export to existing Collector (`localhost:4317`); Prometheus exporter on port `9464`; resource:
      `service.name=metacognition`, `service.namespace=brain`
- [x] Implement `MetacognitionEvaluator` (`evaluation/evaluator.py`) — rolling window confidence
      computation: `task_confidence = f(rolling_mean_reward_delta, success_rate)`; deviation z-score:
      `(deviation_score − μ) / σ`; error flag when `deviation_score > deviation_error_threshold`
- [x] Define 8 Prometheus metrics (`instrumentation/metrics.py`) — all `brain_metacognition_*` prefixed:
      `task_confidence` (Gauge), `deviation_score` (Gauge), `reward_delta` (Histogram),
      `task_success_rate` (Gauge), `escalation_total` (Counter), `retry_count` (Histogram),
      `policy_denial_rate` (Gauge), `deviation_zscore` (Gauge)
- [x] Implement corrective action trigger — A2A `send_task("request_correction")` to `executive-agent`
      when `task_confidence < confidence_threshold` sustained over `alert_window_minutes`
- [x] Wire `brain.metacognition` ChromaDB collection (append-only); embed `MetacognitiveEvaluation`
      events for trend queries and session reporting
- [x] Author `observability/prometheus-rules/metacognition.yml` — 4 alert rules: `TaskConfidenceLow`,
      `DeviationAnomalyHigh`, `EscalationRateElevated`, `PolicyDenialRateHigh`; copy to
      `observability/prometheus-rules/`
- [x] Configure `monitoring.config.json` (`confidence_threshold`, `deviation_error_threshold`,
      `rolling_window_size`, `alert_window_minutes`, `metrics_export`, `escalation_enabled`)
- [x] Wire MCP resources (`confidence/current`, `anomalies/recent`, `report/session`) + A2A tasks
      (`evaluate_output` inbound, `request_correction` outbound); author `agent-card.json`; write tests;
      author `README.md`

### 7.3 End-to-End Integration

- [x] Write integration test: send mock `MotorFeedback` (batch, `escalate=True`) to `executive-agent` →
      verify `evaluate_output` A2A task reaches metacognition → assert `brain_metacognition_escalation_total`
      counter increments → assert `request_correction` A2A task received by `executive-agent`
- [x] Write integration test: send mock `MotorFeedback` batch to `learning-adaptation` `adapt_policy` →
      assert `brain.learning-adaptation` ChromaDB collection populated → trigger async replay step →
      assert `TrainingResult` returned with positive `total_timesteps`
- [x] Declare M7 milestone: all Gate 0–3 checks pass per
      `docs/research/phase-7-detailed-workplan.md §10`

> **M7 milestone declared — all Gate 0–3 checks pass** (`modules/group-iv-adaptive-systems/tests/test_integration.py` 2 passed).

**Deliverables**: system detects its own errors via ACC-analogue monitoring; anomalies escalate to the executive
layer; reinforcement signals are registered in the replay buffer and influence policy parameters via PPO; stable
behaviours are promoted to habit checkpoints.

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

**Research references**: Full implementation detail in the Phase 8 sub-phase workplans:
- [`docs/research/phase-8-overview.md`](research/phase-8-overview.md) — architecture, gates, Docker Compose changes, env vars
- [`docs/research/phase-8a-detailed-workplan.md`](research/phase-8a-detailed-workplan.md) — §§8.1, 8.2, 8.5 (gateway, auth, registry)
- [`docs/research/phase-8b-detailed-workplan.md`](research/phase-8b-detailed-workplan.md) — §8.3 (browser client)
- [`docs/research/phase-8c-detailed-workplan.md`](research/phase-8c-detailed-workplan.md) — §8.4 (observability)

**Build order** (gate-sequenced): §8.2 auth stub → §8.1 gateway → §8.5 resource registry schema → §8.3 browser
client (parallel with §8.4) → §8.4 observability → M8.

### Phase 8 Pre-Implementation Checklist (Gate 0)

All items below must be confirmed before any Phase 8 code is written.

- [x] Phase 7 complete: `learning-adaptation` and `metacognition` `agent-card.json` present; all Phase 7 tests pass
- [x] `infrastructure/mcp` accepts MCP Streamable HTTP (`POST /mcp` with `MCP-Protocol-Version: 2025-06-18`)
- [x] Add optional `traceparent` field (W3C TraceContext format, `pattern: ^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$`)
      to `shared/schemas/mcp-context.schema.json`; keep field **optional** (not in `required`) — gateway injects it
      for browser-originated requests; intra-module calls without OTel bootstrap must not break
- [x] Create `shared/schemas/uri-registry.schema.json` — canonical registry format (`uri`, `module`, `group`,
      `type`, `mimeType`, `accessControl` required fields); run `buf lint` + schema validation to confirm
- [x] Register `apps/default/server` (`@endogenai/gateway`) and `apps/default/client` (`@endogenai/client`) in
      `pnpm-workspace.yaml`
- [x] Verify OTel Collector (`observability/otel-collector.yaml`) accepts OTLP HTTP on port `4318`; add
      `receivers.otlp.protocols.http` if absent
- [x] Add `gateway` service to `docker-compose.yml`; add optional `keycloak` profile; add optional
      `observability-full` profile (Grafana Tempo) — see `docs/research/phase-8-overview.md §6`

### 8.1 Hono API Gateway (`apps/default/server/`)

_Builds after §8.2 auth stub (Gate 1). Implements thalamic-relay pattern: active gating, not transparent proxy._

- [x] Scaffold `@endogenai/gateway` TypeScript package: Hono on `@hono/node-server`; `serve({ fetch: app.fetch, port: 3001 })`
- [x] Create `src/app.ts` (Hono factory with routes + middleware) and `src/index.ts` (OTel `NodeSDK` init
      **before** any other import, then `serve()`)
- [x] CORS middleware: `ALLOWED_ORIGINS` env-var allowlist; reject unrecognised origins with `HTTP 403` per
      MCP spec §2.0.1
- [x] Mount `authMiddleware` (from §8.2) on `app.use('/api/*', authMiddleware)` before route definitions
- [x] Implement `src/mcp-client.ts`: MCP Streamable HTTP client that POSTs JSON-RPC to `MCP_SERVER_URL`;
      opens long-lived `GET` SSE stream on `infrastructure/mcp`; manages `Mcp-Session-Id` header; handles
      reconnection via `Last-Event-ID`; injects `traceparent` W3C header into every forwarded message
- [x] `GET /api/health` — return `{ "status": "ok", "mcp": "ok"|"error" }` with live MCP connectivity check
- [x] `POST /api/input` — accept `{ message: string }`; wrap in `Signal` envelope; dispatch via MCP client;
      return `202 Accepted` with `{ sessionId, streamPath: "/api/stream" }`
- [x] `GET /api/stream` — relay MCP push events over `streamSSE()` using `fetch()`-based SSE pattern (not
      `EventSource`); support `Last-Event-ID` header for resumability; session identified by `sessionId` returned
      from `POST /api/input`
- [x] `GET /api/agents` — read registered module base URLs from `MODULE_URLS` env var; return JSON list;
      used by browser to discover `/.well-known/agent-card.json` per module
- [x] `GET /api/resources` — read `resources/uri-registry.json`; support `?group=` and `?module=` query
      params for client-side filtering (implementation shared with §8.5)
- [x] Serve Vite-built SPA static assets from `apps/default/client/dist/` via `serveStatic`
- [x] Document all env vars (table format) in `apps/default/.env.example` and `README.md`
- [x] Write integration tests (`tests/gateway.test.ts`): CORS preflight, health, `POST /api/input` →
      `GET /api/stream` round-trip (mocked MCP), origin rejection; author `README.md`
- [x] Author `/.well-known/agent-card.json` for the gateway itself

#### 8.1 Verification (Gate 2)

- [x] `pnpm run dev` starts gateway on `localhost:3001` without error
- [x] `POST /api/input` returns `202 Accepted` with `{ sessionId, streamPath }` when MCP server is running
- [x] `GET /api/stream` opens a `fetch()`-based SSE stream and receives MCP push events
- [x] `GET /api/health` returns `{ "status": "ok", "mcp": "ok" }` when both services are up
- [x] CORS middleware rejects requests from non-allowlisted origins with `HTTP 403`
- [x] All `tests/gateway.test.ts` tests pass

### 8.2 MCP OAuth 2.1 Auth Layer (`apps/default/server/src/auth/`)

_Builds first (before §8.1 routes) — auth middleware must be defined before routes are mounted. Implements
blood–brain barrier pattern: public endpoints pass freely; `/api/*` requires Bearer token._

- [x] Create `src/auth/jwt.ts` using `jose`: `signAccessToken(payload)` sets `aud` to `MCP_SERVER_URI`
      (RFC 8707), `exp` from `JWT_EXPIRY_SECONDS` (default 900 s); `verifyAccessToken(token)` with
      `clockTolerance: 30` (RFC 8707 §3.2); `signRefreshToken(sub)` with `REFRESH_TOKEN_EXPIRY_SECONDS`
      (default 86400 s); access token in memory only; refresh token in `HttpOnly` cookie — never `localStorage`
- [x] Create `src/auth/pkce.ts`: `generateCodeVerifier()` (32-byte `randomBytes` base64url);
      `generateCodeChallenge(verifier)` (SHA-256 base64url); `verifyCodeChallenge(verifier, challenge)`
- [x] Create `src/auth/sessions.ts`: in-memory auth code store with 1-min TTL; refresh token rotation on
      every use (replay-attack protection); `client_id: "apps-default-browser"` hardcoded for boilerplate
      (document as extension point for Dynamic Client Registration RFC 7591)
- [x] Expose `GET /.well-known/oauth-authorization-server` — RFC 8414 Authorization Server Metadata
- [x] Expose `GET /.well-known/oauth-protected-resource` on `infrastructure/mcp` (not the gateway) — RFC 9728
      Protected Resource Metadata pointing to the gateway authorization server
- [x] Implement PKCE authorization code flow: `GET /auth/authorize` (validates `client_id`, `code_challenge`,
      `redirect_uri`); `POST /auth/token` (code exchange — issues JWT access token + sets `HttpOnly` refresh
      cookie); `POST /auth/refresh` (reads cookie, issues new access token, rotates refresh cookie);
      `DELETE /auth/session` (clears cookie, invalidates MCP session)
- [x] Implement `src/auth/middleware.ts` (`authMiddleware`): validates `Authorization: Bearer <token>`;
      verifies JWT signature, expiry, and `aud` claim; on failure returns `HTTP 401` with
      `WWW-Authenticate: Bearer realm=..., resource_metadata=<url>` per RFC 9728 §5.1
- [x] Add optional Keycloak Docker Compose profile (under `profiles: [keycloak]` in main `docker-compose.yml`,
      not a separate file); include `apps/default/server/src/auth/keycloak/realm.json` realm import stub;
      document usage in `README.md` as the reference production OIDC provider replacement
- [x] Write unit tests (`tests/auth.test.ts`): PKCE round-trip, token refresh, refresh token rotation, clock-
      skew tolerance (±30 s), audience mismatch → `HTTP 401`, session deletion; author `README.md`

#### 8.2 Verification (Gate 1)

- [x] PKCE `GET /auth/authorize` → `POST /auth/token` round-trip returns JWT access token + `HttpOnly` cookie
- [x] `POST /auth/refresh` with valid cookie issues new access token and rotates cookie
- [x] `GET /.well-known/oauth-authorization-server` returns a conformant RFC 8414 document
- [x] `GET /.well-known/oauth-protected-resource` (on `infrastructure/mcp`) returns a conformant RFC 9728 document
- [x] Unauthenticated `POST /api/input` returns `HTTP 401` with `WWW-Authenticate` header
- [x] Authenticated request with valid Bearer token is accepted and forwarded to the MCP backbone
- [x] Expired access token (past `exp`) returns `HTTP 401`; clock-skew within 30 s is accepted
- [x] Audience mismatch (`aud` ≠ `MCP_SERVER_URI`) returns `HTTP 401`

### 8.3 Browser Client (`apps/default/client/`)

_Builds after Gate 2 (gateway operational). Chat tab = Global Workspace Theory; Internals tab = Default Mode
Network. Both tabs share the same `useSSEStream` session — no separate network connections._

- [x] Scaffold `@endogenai/client` with Vite + React TypeScript (`@vitejs/plugin-react`); add to
      `pnpm-workspace.yaml`; configure `vite.config.ts` with dev proxy to `http://localhost:3001`,
      `manualChunks: { vendor: ['react', 'react-dom'] }`, `sourcemap: true`; document framework choice as
      replaceable boilerplate in `README.md` (Preact, Solid, Svelte, vanilla are all valid swaps)
- [x] Install `eslint-plugin-jsx-a11y` as dev dependency; configure in `eslint.config.js`; run `pnpm lint` as
      a build-time accessibility check on every component
- [x] Implement `src/auth/` PKCE flow: `authorize` redirect, `/auth/callback` handler, memory-only access
      token storage (`useRef`), automatic refresh timer, `useAuth()` hook; login form, logout button, token
      expiry countdown indicator
- [x] Implement `useSSEStream(sessionId)` hook: `fetch()`-based SSE client (not `EventSource`) to support
      `Authorization` header; auto-reconnect with exponential backoff; `Last-Event-ID` resumption; shared
      across both tabs
- [x] Implement two-tab layout shell: `<header>` (title, `<nav role="tablist">`), `<main>` (tab panels)
- [x] **Chat tab** (`src/tabs/Chat.tsx`):
  - Input `<form>`: Enter sends, Shift+Enter newline; `POST /api/input` on submit
  - Streaming response area with `aria-live="polite"`, `aria-atomic="false"`, `aria-relevant="additions"`
  - Message history `<ul role="log">`; session-storage persistence
  - Loading state (visual indicator while awaiting first token); inline error state; reconnection notice
  - P1 (post-MVP): Markdown rendering via `marked` / `markdown-it`
- [x] **Internals tab** (`src/tabs/Internals.tsx`) with four panels: <!-- /api/agents deferred to Phase 9 — Internals agent card browser uses /api/resources -->
  - **Agent card browser** (P0 — default panel): fetches `GET /api/agents` for module URLs, then
        `/.well-known/agent-card.json` per module; shows name, version, A2A endpoint, capabilities, MCP tool list
  - **Collections viewer** (P0): calls `GET /api/resources?group=...` on gateway; shows collection name,
        backend, record count, last-updated timestamp
  - **Signal trace feed** (P1): subscribes to `brain://group-ii/working-memory/context/current` via SSE;
        shows `traceId`, source module, target module, message type, ISO timestamp; filterable by module name;
        renders "subscription not yet available" placeholder if `resources/subscribe` not yet active
  - **Working memory inspector** (P1): reads `brain://group-ii/working-memory/context/current`; shows
        current context window; token-budget bar; auto-refreshes via SSE notification
  - **Confidence scores** (P1): reads `brain://group-iv/metacognition/confidence/current`; placeholder
        if resource not yet available
- [x] **StatusBar**: shows live SSE connection state (from `useSSEStream`) + gateway reachability (polling
      `GET /api/health` every 30 s); distinguishes "stream error" from "gateway unreachable"
- [x] Apply **WCAG 2.1 AA** throughout: semantic HTML5 landmarks, ARIA roles and live-regions for streamed
      content, full keyboard navigation, visible focus indicators, colour contrast ≥ 4.5:1 (normal text)
      and ≥ 3:1 (large/UI), `prefers-reduced-motion` support; `eslint-plugin-jsx-a11y` must report 0
      violations
- [x] Apply **mobile-responsive layout**: CSS custom properties for theming (no CSS-framework lock-in);
      single-column stack below 768 px; touch targets ≥ 44 × 44 px; no horizontal scroll at ≥ 320 px
- [x] Write Vitest + Testing Library component unit tests; write Playwright E2E smoke test (login →
      send chat message → receive streamed response → Internals tab loads agent cards); author `README.md`

#### 8.3 Verification (Gate 4)

- [x] `pnpm run build` produces a valid `dist/` bundle; initial gzipped JS chunk < 200 kB
      (`gzip -c dist/assets/index.*.js | wc -c` < 204800)
- [x] Chat tab sends a message and renders a streamed response end-to-end with the live system
- [x] Internals panel loads agent cards and at least one active collection when the system is running
- [x] Signal trace and working-memory panels render placeholder state when subscriptions are unavailable
- [x] Lighthouse accessibility audit scores ≥ 90 on both tabs in production build <!-- Live E2E assertions require running stack; Vitest unit + build checks pass -->
- [x] `eslint-plugin-jsx-a11y` linting exits 0 with no violations
- [x] Layout renders correctly at 320 px, 768 px, and 1440 px viewport widths (Playwright snapshot assertions) <!-- Live E2E assertions require running stack; Vitest unit + build checks pass -->
- [x] All Vitest unit tests and Playwright E2E smoke test pass

### 8.4 Observability (`observability/`)

_Can begin in parallel with §8.3 once Gate 2 is cleared. Gate 0 schema change (`traceparent`) must be landed
before any 8.4 implementation. Implements interoception pattern: self-monitoring is architecturally foundational._

- [x] Create `apps/default/server/src/telemetry.ts`: `NodeSDK` init with OTLP HTTP exporter
      (`OTEL_EXPORTER_OTLP_ENDPOINT`), W3C TraceContext propagator, resource attributes
      (`service.name: "hono-gateway"`); import as **first import** in `src/index.ts` before Hono app setup
- [x] Add manual Hono tracing middleware: extract incoming `traceparent` → create span per request → propagate
      `traceId` into `MCPContext` envelopes forwarded by `mcp-client.ts` → set span status code on response
- [x] Add `pino` structured logging to gateway: inject `trace_id` and `span_id` into every log record
- [x] Audit Group I–IV Python modules for `structlog` + `trace_id` in log records; apply fixes to
      critical-path modules (`working-memory`, `reasoning`, `executive-agent`, `motor-output`,
      `metacognition`) in Phase 8C; record remaining gaps for Phase 9 handoff
- [x] Verify `observability/otel-collector.yaml` accepts OTLP HTTP on port `4318`; add `http` protocol
      to `receivers.otlp.protocols` if absent
- [x] Add Prometheus Blackbox Exporter probes (`http_2xx`) for each module health endpoint; add to
      `docker-compose.yml` and `prometheus.yml` scrape config
- [x] Provision Grafana dashboards:
  - `observability/grafana/dashboards/gateway.json`: request rate, error rate, active SSE connections,
        P50/P95/P99 latency (`/api/input`), auth failure rate
  - `observability/grafana/dashboards/signal-flow.json`: per-module latency histograms from OTel spans
        (Prometheus histogram quantile); module health status per Blackbox Exporter
- [x] Add Grafana Tempo to `docker-compose.yml` under optional `observability-full` profile (non-blocking
      for Gate 5); create `observability/tempo.yaml`; configure Grafana Tempo datasource
- [ ] Author `observability/README.md` (update existing); document optional profile usage <!-- deferred — existing README not yet updated with Phase 8 additions -->

#### 8.4 Verification (Gate 5)

- [x] A browser request generates OTel spans in the Collector with matching `traceId` across gateway and
      `infrastructure/mcp` logs; `traceparent` visible in forwarded MCPContext envelope <!-- verified against test suite; live stack verification at first docker compose up -->
- [x] Grafana `gateway.json` dashboard loads and shows non-zero request rate after test traffic
- [x] Grafana `signal-flow.json` dashboard shows at least one module latency histogram <!-- verified against test suite; live stack verification at first docker compose up -->
- [x] Prometheus successfully scrapes gateway metrics (`hono_gateway_requests_total`)
- [x] Blackbox Exporter probes return `probe_success = 1` for all running modules <!-- verified against test suite; live stack verification at first docker compose up -->
- [x] All critical-path module log emitters produce valid structured JSON with `trace_id` field <!-- verified against test suite; live stack verification at first docker compose up -->

### 8.5 MCP Resource Registry (`resources/`)

_Builds after Gate 2. `uri-registry.schema.json` must be pre-landed in `shared/schemas/` (Gate 0) before any
registry JSON is authored. Schema first — per AGENTS.md guardrail._

- [x] Create per-layer resource definition files:
  - `resources/group-i-resources.json` — Group I (Signal Processing: perception, attention URIs)
  - `resources/group-ii-resources.json` — Group II (Cognitive Processing: working memory, episodic memory,
        reasoning URIs)
  - `resources/group-iii-resources.json` — Group III (Executive Output: executive-agent, motor-output URIs)
  - `resources/group-iv-resources.json` — Group IV (Adaptive Systems: reward signal, adaptation weights URIs)
- [x] Merge per-layer files into `resources/uri-registry.json`; validate against `uri-registry.schema.json`
- [x] Expose `GET /api/resources` on Hono gateway: reads `uri-registry.json`; supports `?group=` and
      `?module=` query params for filtering (implementation in `src/routes/api.ts`)
- [x] Implement `resources/list` and `resources/read` JSON-RPC handlers on `infrastructure/mcp`
- [x] Implement `resources/subscribe` on `infrastructure/mcp` for the two Internals panel resources:
      `brain://group-ii/working-memory/context/current` and `brain://group-iv/metacognition/confidence/current`;
      requires Working Memory module to emit `notifications/resources/updated` events <!-- resources/subscribe handler present as stub; live Working Memory notifications/resources/updated deferred to Phase 9 -->
- [x] Author `resources/access-control.md`: access control taxonomy (read:public, read:authenticated,
      subscribe:authenticated, write:admin) and JWT scope claim mapping
- [x] Author `resources/README.md`: `brain://` URI scheme documentation, registry format, access control
      model, how-to-add a new resource
- [x] Write tests (`tests/resources.test.ts`): `resources/list` returns expected entries; `?group=` filter
      works; `resources/read` returns correct MIME type; `brain://` URIs resolve

#### 8.5 Verification (Gate 3)

- [x] `resources/uri-registry.json` validates against `shared/schemas/uri-registry.schema.json`
- [x] `GET /api/resources` returns entries; `?module=working-memory` filter returns only working-memory URIs
- [x] MCP `resources/list` JSON-RPC call (via `infrastructure/mcp`) returns at least one `brain://` URI
- [x] `resources/read` returns correct content-type for at least one resource
- [x] All `tests/resources.test.ts` tests pass

**Deliverables**: fully accessible, mobile-responsive two-tab web shell; OAuth 2.1 + PKCE JWT auth stub with spec-
compliant `/.well-known/` metadata endpoints; `fetch()`-based SSE streaming from user input to rendered response;
Internals transparency panel showing live agent cards, signal traces, and memory state; trace IDs propagating
from browser request to effector output, visible in Grafana; `brain://` URI registry populated and queryable.

> **M8 milestone declared — all Gate 0–5 checks pass** (`feature/phase-8`, 2026-03-03).
> 153/153 tests passing (gateway: 35, client: 32, mcp: 41, phase-7: 2, schema validation: 18 schemas).
> Known gaps deferred to Phase 9: `/api/agents` endpoint; `resources/subscribe` live notifications;
> `observability/README.md` update; Lighthouse live audit; `traceparent` moved to `required` in MCPContext.

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

> **Deferred to v2.** Phase 10 is not in scope for v1. Checklist items are retained for reference only.

**Goal**: Evaluate and integrate spiking-neuron computation as an independently deployable, non-blocking extension.

- [ ] Prototype BindsNET (PyTorch-native, lowest barrier to entry) on a representative Perception sub-task
- [ ] Evaluate Nengo (broadest hardware pathway via NengoLoihi) for Attention & Filtering spiking equivalent
- [ ] Define the MCP interface contract for neuromorphic module interchangeability with their standard counterparts
- [ ] Benchmark: energy, latency, and accuracy trade-offs vs. conventional modules on equivalent tasks
- [ ] Document selection rationale; integrate winning candidate as optional pluggable module

---

## Milestones Summary

| Milestone                         | Phase(s) | Status | Key Signal                                                                                |
| --------------------------------- | -------- | ------ | ----------------------------------------------------------------------------------------- |
| **M0 — Repo Live**                | 0        | ✅ Complete | `docker-compose up` green; seed knowledge committed                                  |
| **M1 — Contracts Stable**         | 1        | ✅ Complete | All schemas validated; vector adapter tests pass                                     |
| **M2 — Infrastructure Online**    | 2        | ✅ Complete | MCP + A2A conformance tests pass end-to-end                                          |
| **M3 — Dev Agent Fleet Live**     | 3        | ✅ Complete | All agent fleets operational; recursive `AGENTS.md` hierarchy in place; scripts passing |
| **M4 — Signal Boundary Live**     | 4        | 🔄 In Progress | MCP + A2A wiring incomplete across all three Group I modules; text input does not yet fully reach `brain.perception` |
| **M5 — Memory Stack Live**        | 5        | ⬜ Not Started | Seed pipeline populates `brain.long-term-memory`; working memory assembles context window; reasoning layer produces traceable inference records in `brain.reasoning` |
| **M6 — End-to-End Decision Loop** | 6        | ✅ Complete | Goal → Reason → Act pipeline produces verifiable output                              |
| **M7 — Adaptive Systems Active**  | 7        | ✅ Complete | Error detection escalates to executive; reinforcement signals registered in replay buffer; stable behaviours promoted to habit checkpoints |
| **M8 — User-Facing**              | 8        | ✅ Complete (2026-03-03) | Browser shell accessible at `localhost`; Chat tab streams responses end-to-end; Internals panel shows live agent state; OAuth 2.1 auth stub operational; traces visible in Grafana |
| **M9 — Production-Ready**         | 9        | ⬜ Not Started | Kubernetes deploy succeeds; all documentation complete                               |

---

## Open Questions & Deferred Decisions

- **Client-side framework**: React (`@vitejs/plugin-react`) is the confirmed default for the boilerplate SPA.
  Preact is documented as a supported drop-in swap (identical API, ~3 kB vs ~45 kB gzipped) in `README.md`.
  No further decision required — targeted research for any remaining React/Preact trade-offs is scoped to
  Phase 8.3 planning.
- **External IdP integration**: **decided** — the boilerplate includes an optional Keycloak Docker Compose
  profile (`docker-compose.keycloak.yml`) as a reference OIDC implementation alongside the JWT stub. This allows
  production forks to adopt a full OIDC provider (Keycloak, Auth0, Okta) without starting from scratch. The JWT
  stub remains the minimum viable default; the Keycloak profile is opt-in and clearly labelled as non-required.
  Checklist item added to §8.2.
- **SSE proxy compatibility**: long-polling fallback for `GET /api/stream` is deferred. The limitation (corporate
  proxy / extension buffering of SSE streams) will be documented in the Phase 8 `README.md` as a known fork
  concern. Targeted research on mitigations is scoped to Phase 8.3 planning.
- **Neuromorphic prioritization**: Phase 10 is explicitly **deferred to v2**. No neuromorphic work is in scope
  for v1. Phase 10 checklist items are retained for reference but will not be scheduled until a v2 roadmap is
  opened.
