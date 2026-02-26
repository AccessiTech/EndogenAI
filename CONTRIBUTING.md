# Contributing to brAIn / EndogenAI

Thank you for your interest in contributing! This project follows a **documentation-first, endogenous-growth**
philosophy — every contribution should expand the system's capacity to generate further components.

---

## Code of Conduct

By participating in this project you agree to uphold our Code of Conduct: be respectful, constructive, and
collaborative.

---

## Getting Started

See [docs/guides/getting-started.md](docs/guides/getting-started.md) for prerequisites, installation steps, and bringing
up the local service stack.

For the full developer toolchain (linting, type-checking, pre-commit hooks, buf, and commit conventions), see
[docs/guides/toolchain.md](docs/guides/toolchain.md).

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

See the [Toolchain Guide](docs/guides/toolchain.md) for the full command reference, including how to run ESLint,
Prettier, ruff, mypy, pre-commit, buf, and commitlint individually or all at once.

```bash
# Quick reference — run all checks via Turborepo
pnpm run lint        # turbo run lint
pnpm run typecheck   # turbo run typecheck
pnpm run test        # turbo run test
pnpm run build       # turbo run build
```

---

## Pull Request Guidelines

1. **One concern per PR**: keep changes focused; avoid mixing features with refactors.
2. **Tests required**: all new functionality must be covered by unit tests; integration tests for protocol/adapter
   changes.
3. **Documentation required**: update or create `README.md` for the affected module; add/update `docs/` entries if the
   change affects architecture or protocols.
4. **Schemas first**: if your change requires a new shared contract (JSON Schema / Protobuf), land the schema in
   `shared/schemas/` before the implementation.
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
