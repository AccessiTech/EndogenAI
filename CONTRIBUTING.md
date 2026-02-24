# Contributing to brAIn / EndogenAI

Thank you for your interest in contributing! This project follows a **documentation-first, endogenous-growth** philosophy — every contribution should expand the system's capacity to generate further components.

---

## Code of Conduct

By participating in this project you agree to uphold our Code of Conduct: be respectful, constructive, and collaborative.

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | ≥ 20 | TypeScript modules, MCP/A2A infra |
| pnpm | ≥ 9 | Package manager / monorepo workspaces |
| Python | ≥ 3.11 | ML / cognitive modules |
| uv | latest | Python package management |
| Docker | ≥ 24 | Local service orchestration |
| Docker Compose | ≥ 2.20 | Multi-service local stack |

### Environment Setup

```bash
# 1. Install Node dependencies
pnpm install

# 2. Install Python dependencies (per-package, using uv)
uv sync

# 3. Start local services
docker compose up -d

# 4. Verify everything is healthy
docker compose ps
```

---

## Development Workflow

### Branch Naming

```
feat/<short-description>      # new feature
fix/<short-description>        # bug fix
docs/<short-description>       # documentation only
refactor/<short-description>   # code refactoring
test/<short-description>       # test additions/fixes
chore/<short-description>      # tooling, CI, config
```

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`

Scopes: module or area name (e.g. `mcp`, `a2a`, `memory`, `perception`, `shared`)

Examples:
```
feat(a2a): implement agent card endpoint
fix(memory): correct TTL eviction logic
docs(readme): add getting-started section
```

### Running Tasks

```bash
# Lint all packages
pnpm run lint

# Type-check all TypeScript packages
pnpm run typecheck

# Run all tests
pnpm run test

# Build all packages
pnpm run build
```

---

## Pull Request Guidelines

1. **One concern per PR**: keep changes focused; avoid mixing features with refactors.
2. **Tests required**: all new functionality must be covered by unit tests; integration tests for protocol/adapter changes.
3. **Documentation required**: update or create `README.md` for the affected module; add/update `docs/` entries if the change affects architecture or protocols.
4. **Schemas first**: if your change requires a new shared contract (JSON Schema / Protobuf), land the schema in `shared/schemas/` before the implementation.
5. **Pass all CI checks** before requesting review.

---

## Module Contribution Guidelines

Each module must conform to the module contract defined in the root `README.md`:

- Implements the `agent-card.json` endpoint at `/.well-known/agent-card.json`
- Communicates exclusively via MCP (context exchange) and A2A (task delegation)
- Emits structured telemetry (logs, metrics, traces) as defined in `shared/utils/`
- Has a `README.md` describing purpose, interface, configuration, and deployment
- All LLM inference routes through LiteLLM — no direct SDK calls

---

## Reporting Issues

Use GitHub Issues with the appropriate label:

- `bug` — something is broken
- `enhancement` — new feature request
- `docs` — documentation gap or error
- `question` — clarification needed

---

## License

By contributing you agree that your contributions will be licensed under the [MIT License](LICENSE).
