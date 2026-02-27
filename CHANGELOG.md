# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

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
