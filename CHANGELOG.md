# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Phase 6 (M6): End-to-end decision-to-action pipeline live — Group III executive & output modules fully operational with corollary-discharge feedback loop closed
- Phase 6 §6.1: `executive-agent` module — BDI deliberation loop (`deliberation.py`), DLPFC-modelled goal stack (`goal_stack.py`), agent identity & capability declaration (`identity.py`), OPA policy gating via HTTP client (`policy.py`), corollary discharge handler (`feedback.py`), vector store writes to `brain.executive-agent` collection (`store.py`), MCP tools and A2A handler
- Phase 6 §6.1: OPA Rego policy bundles (`executive-agent/policies/`) — `commit_goal`, `abort_goal`, `bdi_deliberate`, `resource_constraints` rules; standalone OPA HTTP service at localhost:8181
- Phase 6 §6.2: `agent-runtime` module — cerebellum-modelled skill pipeline decomposition (`decomposer.py`), Temporal workflow definition (`workflow.py`), retryable activities (`activities.py`), Temporal worker startup (`worker.py`), Prefect fallback orchestrator (`prefect_fallback.py`), runtime-agnostic facade (`orchestrator.py`), dynamic tool registry (`tool_registry.py`)
- Phase 6 §6.3: `motor-output` module — channel-based action dispatch router (`dispatcher.py`), HTTP/A2A/file/render channel adapters, SMA-modelled channel selector (`channel_selector.py`), retry/abort/escalation error policy (`error_policy.py`), corollary discharge outcome reporting (`feedback.py`)
- Phase 6 §6.4: End-to-end integration test (`tests/test_integration_full_pipeline.py`) — `test_full_pipeline_goal_to_completed` verifies synthetic goal PENDING→COMPLETED via motor dispatch with corollary discharge closure
- Phase 6: Five shared schemas landed — `executive-goal.schema.json`, `skill-pipeline.schema.json`, `action-spec.schema.json`, `motor-feedback.schema.json`, `policy-decision.schema.json`
- Phase 6: `brain.executive-agent` collection registered in `shared/vector-store/collection-registry.json`
- Phase 6: `temporal` (port 7233/8233) and `opa` (port 8181) services added to `docker-compose.yml`
- Phase 6: Temporal + Prefect spike decision recorded in `docs/research/temporal-prefect-spike.md` (Temporal primary, Prefect fallback)
- Phase 2: `@accessitech/mcp` — MCP infrastructure package: `ContextBroker`, `CapabilityRegistry`, `StateSynchronizer`, `createMCPServer` with tools and resources via `@modelcontextprotocol/sdk`
- Phase 2: `@accessitech/a2a` — A2A infrastructure package: `TaskOrchestrator`, `A2ARequestHandler`, `createA2AServer`; spec-locked to A2A v0.3.0 (commit `2d3dc909`)
- Phase 2: `@accessitech/adapters` — MCP + A2A adapter bridge: `MCPToA2ABridge` with round-trip context propagation and A2A task completion
- Phase 2: `/.well-known/agent-card.json` for all three infrastructure packages
- Phase 2: `docs/protocols/mcp.md` and `docs/protocols/a2a.md` updated to `stable` with Phase 2 implementation references
- Phase 1: `shared/schemas/mcp-context.schema.json` — canonical MCP context envelope schema
- Phase 1: `shared/schemas/a2a-message.schema.json` — canonical A2A message schema
- Phase 1: `shared/schemas/a2a-task.schema.json` — canonical A2A task schema (full lifecycle state machine)
- Phase 1: `shared/types/signal.schema.json`, `memory-item.schema.json`, `reward-signal.schema.json` — shared signal type contracts
- Phase 1: `@accessitech/vector-store` (TypeScript) — backend-agnostic vector store adapter with ChromaDB implementation
- Phase 1: `endogenai-vector-store` (Python) — ChromaDB + Qdrant vector store adapters with Ollama embedding support
- Phase 0: Monorepo bootstrap with pnpm workspaces and Turborepo pipeline configuration
- Phase 0: Root ESLint + Prettier configuration for TypeScript packages
- Phase 0: Python tooling configuration (`pyproject.toml`) with ruff and mypy
- Phase 0: `docker-compose.yml` for local multi-service orchestration (ChromaDB, Ollama, Redis, observability stack)
- Phase 0: Observability stub — OpenTelemetry Collector, Prometheus, and Grafana provisioning configs
- Phase 0: Seed knowledge directory (`resources/static/knowledge/`) with `brain-structure.md`
- Phase 0: Neuroanatomy region stubs (`resources/neuroanatomy/`) for all 8 primary module-mapped brain regions
- Phase 0: `CONTRIBUTING.md`, `LICENSE`, and `CHANGELOG.md`
- Phase 0: Pre-commit hook configuration and PR template

---

[Unreleased]: https://github.com/AccessiTech/EndogenAI/compare/HEAD...HEAD
