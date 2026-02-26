# AGENTS.md

Guidance for AI coding agents working in this repository.

---

## Guiding Constraints

- **Documentation-first**: every implementation change must be accompanied by clear documentation. Follow the structure
  in [`README.md — File Directory`](readme.md#file-directory).
- **Endogenous-first**: scaffold from existing system knowledge (schemas, specs, seed docs) — do not author from
  scratch in isolation.
- **Local compute first**: default to Ollama embeddings (`nomic-embed-text`) and local vector stores (ChromaDB); cloud
  services are opt-in only.
- **Polyglot with convention**: Python for ML/cognitive modules; TypeScript for MCP/A2A infrastructure and application
  surfaces; JSON Schema / Protobuf for all shared contracts.
- **No direct LLM SDK calls**: all LLM inference must route through LiteLLM.
- **Schemas first**: if a change requires a new shared contract, land the JSON Schema or Protobuf in `shared/schemas/`
  before the implementation.
- **Test-driven**: all new functionality must be covered by unit tests; adapter/protocol changes require integration
  tests.

---

## Python Tooling

**Always use `uv run` — never invoke Python or package executables directly.**

```bash
# Correct
cd shared/vector-store/python && uv run pytest
cd shared/vector-store/python && uv run python -c "import chromadb; print('ok')"
cd shared/vector-store/python && uv run mypy src/
cd shared/vector-store/python && uv run ruff check .

# Wrong — do not do this
.venv/bin/python -c "..."
python src/some_script.py
```

`uv run` ensures the correct locked environment is used regardless of shell state. Each Python sub-package under
`shared/` and `modules/` manages its own `uv`-based virtual environment.

---

## Commit Discipline

**Make small, incremental commits** — one logical change per commit, not one large commit at the end of a session.

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

| Type | When to use |
|------|-------------|
| `feat` | new functionality |
| `fix` | bug or type error correction |
| `docs` | documentation only |
| `refactor` | restructuring without behaviour change |
| `test` | adding or fixing tests |
| `chore` | tooling, config, CI, lockfile updates |
| `perf` | performance improvements |

**Scope** = the module or area affected (e.g. `mcp`, `a2a`, `memory`, `shared`, `vector-store`).

Good commit cadence:

1. Schema / interface change → commit
2. Implementation → commit
3. Tests → commit
4. Docs / README update → commit

---

## Running Checks

```bash
# TypeScript (from repo root)
pnpm run lint        # turbo run lint
pnpm run typecheck   # turbo run typecheck
pnpm run test        # turbo run test

# Python (from the relevant sub-package directory)
uv run ruff check .
uv run mypy src/
uv run pytest

# Protobuf
cd shared && buf lint
```

All checks must pass before committing. The pre-commit hooks enforce formatting, linting, type-checking, schema
validation, and commit message convention automatically.

---

## Module Contracts

Every module must:

- Expose an `agent-card.json` at `/.well-known/agent-card.json`
- Communicate exclusively via MCP (context exchange) and A2A (task delegation)
- Emit structured telemetry (logs, metrics, traces) per `shared/utils/`
- Include a `README.md` covering purpose, interface, configuration, and deployment

---

## Key References

| Resource | Purpose |
|----------|---------|
| [`docs/Workplan.md`](docs/Workplan.md) | Phase-by-phase implementation roadmap |
| [`docs/architecture.md`](docs/architecture.md) | Full architectural overview and signal-flow diagrams |
| [`docs/guides/adding-a-module.md`](docs/guides/adding-a-module.md) | Step-by-step module scaffolding guide |
| [`docs/guides/toolchain.md`](docs/guides/toolchain.md) | Full toolchain command reference |
| [`shared/vector-store/README.md`](shared/vector-store/README.md) | Vector store adapter pattern and collection registry |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branch naming, PR guidelines, and coding standards |
