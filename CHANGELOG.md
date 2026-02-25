# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

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
