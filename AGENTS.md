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

## Repository Map

```
shared/
  schemas/          # Canonical JSON Schema / Protobuf contracts — land here first
  types/            # Shared type definitions (signal, memory-item, reward-signal)
  utils/            # Logging, tracing, validation specs
  vector-store/     # Backend-agnostic vector store adapter (Python + TypeScript)

infrastructure/     # MCP server, A2A agent coordination, adapter bridges (Phase 2+)

modules/            # Cognitive modules, grouped by brain-layer analogy
  group-i-signal-processing/
  group-ii-cognitive-processing/
  group-iii-executive-output/
  group-iv-adaptive-systems/

apps/               # End-user application surfaces (Phase 5+)

resources/
  static/knowledge/ # Morphogenetic seed documents — source of endogenous scaffolding
  neuroanatomy/     # Brain-region reference stubs

docs/               # Architecture, guides, protocol specs
observability/      # OTel collector, Prometheus, Grafana configs
```

---

## Environment Bootstrap

Bring up the full local stack before running integration tests:

```bash
# 1. Install JS/TS dependencies
pnpm install

# 2. Start backing services (ChromaDB, Ollama, observability stack)
docker compose up -d

# 3. Sync each Python sub-package you're working in
cd shared/vector-store/python && uv sync && cd -

# 4. Verify
pnpm run lint && pnpm run typecheck
cd shared/vector-store/python && uv run ruff check . && uv run mypy src/
```

> Ollama must be running at `http://localhost:11434` for embedding tests. Pull the default model:
> `ollama pull nomic-embed-text`

---

## Guardrails

**Never do these without explicit instruction:**

- Edit `pnpm-lock.yaml` or `uv.lock` by hand — always use `pnpm install` / `uv sync`
- Modify files under `.venv/`, `node_modules/`, or `dist/`
- Commit secrets, API keys, or credentials of any kind
- Run `docker compose down -v` (destroys volumes) in a shared or production context
- Delete or rename `shared/schemas/` files that are already imported by other packages
- `git push --force` to `main`

**Prefer caution over assumption for:**

- Any change that touches more than one sub-package boundary
- Schema changes (downstream consumers may break)
- Dependency version bumps (run the full check suite first)

---

## When to Ask vs. Proceed

**Default posture: stop and ask before any ambiguous or irreversible action.**

Ask when:
- Requirements or acceptance criteria are unclear
- A change would delete, rename, or restructure existing files
- A schema change could break other sub-packages
- The correct approach involves a genuine trade-off the user should decide

Proceed when:
- The task is unambiguous and reversible
- A best-practice default exists and is well-established in this codebase
- The action can be undone with `git revert` or a follow-up commit

When proceeding under ambiguity, **document the assumption inline** (code comment or commit message body) so it can be reviewed and corrected.

---

## Development Scripts

This repository is designed to grow **endogenously** — scripts encode system knowledge locally so that repetitive or
exploratory work does not need to be re-discovered in every agent session. Prefer writing a reusable script over
performing the same work interactively with an AI agent multiple times.

### When to write a script (instead of doing it interactively)

| Situation | Write a script when… |
|-----------|----------------------|
| You've done the same multi-step task twice | The third time, encode it as a script |
| A task requires reading many files to build context | Pre-compute and cache the output |
| Validation logic can be expressed as code | It should be, so CI can enforce it too |
| You're generating boilerplate from a template | A generator script is more reliable than prompting |
| The task could break something if done wrong | A script can include guard-rails and dry-run modes |

### Script conventions

- **Location**: `scripts/` at the repo root for cross-cutting tools; `<package>/scripts/` for package-local tools.
- **Language**: Python for logic-heavy scripts (`uv run python scripts/my_script.py`); shell (`.sh`) for simple glue.
- **Invocation**: always run Python scripts via `uv run` from the relevant package directory, or from the root if the
  script has no package dependency.
- **Committed, not throwaway**: scripts are first-class repo artifacts — commit them, document their purpose at the top
  of the file, and keep them passing in CI.
- **Dry-run mode**: any script that writes or deletes files should support a `--dry-run` flag.

### Script categories

#### Scaffolding
Generate new module / package boilerplate from a template rather than authoring from scratch:

```bash
uv run python scripts/scaffold_module.py --name perception --group group-i-signal-processing
```

Scaffolding scripts should derive their templates from existing modules and `AGENTS.md` conventions, embodying the
endogenous-first principle.

#### Validation
Re-run any validation that the pre-commit hooks perform, on demand:

```bash
uv run python scripts/validate_frontmatter.py resources/
cd shared && buf lint
```

These are already encoded — extend `scripts/validate_frontmatter.py` rather than adding a new one-off script.

#### Code generation
Derive TypeScript types, Python dataclasses, or Protobuf stubs directly from existing JSON Schemas in
`shared/schemas/` — no manual transcription:

```bash
uv run python scripts/codegen_types.py --schema shared/schemas/memory-item.schema.json --out shared/types/
```

#### Health checks
Verify the local stack is fully up before running integration tests — avoids spending tokens diagnosing a
test failure that is actually a missing service:

```bash
bash scripts/healthcheck.sh   # exits 0 only when ChromaDB, Ollama, and OTel are reachable
```

#### Seed ingestion
Chunk and load morphogenetic seed documents into the vector store without manual steps:

```bash
uv run python scripts/ingest_seed.py --source resources/static/knowledge/ --collection brain.knowledge
```

### Guidelines for agents

1. **Check `scripts/` first** — before implementing a multi-step task interactively, check whether a script already
   exists for it.
2. **Extend, don't duplicate** — if a script partially covers your need, extend it rather than creating a second one
   that overlaps.
3. **Propose new scripts proactively** — if you perform a multi-step investigation or transformation that took
   significant context to execute, encapsulate it as a script and commit it so future sessions start with that
   knowledge already encoded.
4. **Document at the top** — every script must open with a docstring or comment block describing its purpose, inputs,
   outputs, and usage example.

---

## VS Code Custom Agents

Four workspace agents are defined in [`.github/agents/`](.github/agents/) and
appear in the Copilot chat agents dropdown automatically.

| Agent | Posture | Trigger |
|-------|---------|---------|
| **Plan** | read-only | Start of any new task — survey workplan + codebase, produce a scoped plan |
| **Scaffold Module** | read + create | Adding a new cognitive module — derives structure from endogenous knowledge |
| **Implement** | full tools | Execute an approved plan; enforces all AGENTS.md constraints |
| **Review** | read-only | Pre-commit gate — verify changes against constraints and module contracts |

Typical workflow: **Plan → (approve) → Implement → (complete) → Review → commit**.

For a new module: **Scaffold Module → (approve scaffold) → Implement → Review → commit**.

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
