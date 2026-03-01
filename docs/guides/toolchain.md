---
id: guide-toolchain
version: 0.2.0
status: active
last-reviewed: 2026-02-28
---

# Developer Toolchain

Reference guide for every tool used in the EndogenAI development workflow. Covers installation, configuration, and how
to run each check manually.

> **Who this is for**: contributors opening PRs or developing new modules. If you just want to _run_ the project, see
> [Getting Started](getting-started.md).

---

## Stack Overview

EndogenAI is a polyglot monorepo. Each layer of the toolchain governs one or both language surfaces:

| Tool         | Language   | Purpose                                              |
| ------------ | ---------- | ---------------------------------------------------- |
| `pnpm`       | TypeScript | Package manager and monorepo workspace               |
| `turbo`      | TypeScript | Task pipeline (build, lint, test, typecheck)         |
| `eslint`     | TypeScript | Linting                                              |
| `prettier`   | Both       | Code formatting                                      |
| `typescript` | TypeScript | Type-checking (`tsc`)                                |
| `uv`         | Python     | Package manager and virtual-environment              |
| `ruff`       | Python     | Linting and import sorting (replaces flake8 + isort) |
| `mypy`       | Python     | Static type-checking                                 |
| `pre-commit` | Both       | Git hook runner — enforces all of the above          |
| `commitlint` | Both       | Enforces Conventional Commit message format          |
| `buf`        | Protobuf   | Protobuf schema linting and code generation          |

---

## Node.js / pnpm

**Install**: follow the [official pnpm installation guide](https://pnpm.io/installation) (requires Node.js ≥ 20).

```bash
# Install all workspace dependencies
pnpm install

# Run a specific Turborepo task across all packages
pnpm run lint        # turbo run lint
pnpm run typecheck   # turbo run typecheck
pnpm run test        # turbo run test
pnpm run build       # turbo run build
```

Workspace package globs are defined in [`pnpm-workspace.yaml`](../../pnpm-workspace.yaml): `infrastructure/*`,
`modules/**/*`, `apps/*`, `shared/*`.

---

## Python / uv

**Install**:
[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# Sync all dev dependencies from pyproject.toml into a managed venv
uv sync --dev

# Run any Python tool inside the managed environment
uv run ruff check .
uv run mypy .
uv run pytest
```

Root-level Python dev dependencies are declared in [`pyproject.toml`](../../pyproject.toml) under
`[dependency-groups] dev`. Each Python module has its own `pyproject.toml` for module-specific dependencies.

---

## Python Module Development (Group I and II modules)

Each cognitive module under `modules/` is an independent Python package with its own managed virtual environment. The
pattern mirrors `shared/vector-store/python/` — use it as the reference implementation.

### First-time setup for a module

```bash
# Navigate to the module
cd modules/group-i-signal-processing/<module-name>

# Sync the locked environment (creates .venv/ if absent)
uv sync

# Verify tools are available
uv run python --version
uv run pytest --version
```

Run `uv sync` once at the start of each session if the `uv.lock` may have changed.

### Daily development commands

```bash
# From the module directory:

# Run all tests
uv run pytest

# Unit tests only (no Docker / services required)
uv run pytest tests/unit/ -v

# Integration tests (requires Docker + ChromaDB container)
uv run pytest tests/integration/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Lint
uv run ruff check .

# Lint + auto-fix
uv run ruff check --fix .

# Type-check
uv run mypy src/

# Format
uv run ruff format .
```

### Running a module server locally

```bash
cd modules/group-i-signal-processing/<module-name>
uv sync
uv run uvicorn <module_pkg>.server:app --host 0.0.0.0 --port <port> --reload
```

Port assignments for Group I modules:

| Module                | Package               | Port |
| --------------------- | --------------------- | ---- |
| `sensory-input`       | `sensory_input`       | 8101 |
| `attention-filtering` | `attention_filtering` | 8102 |
| `perception`          | `perception`          | 8103 |

See [Deployment Guide](deployment.md) for the full environment variable reference.

### Adding a dependency to a module

```bash
# Runtime dependency
cd modules/group-i-signal-processing/<module-name> && uv add <package>

# Dev-only dependency
cd modules/group-i-signal-processing/<module-name> && uv add --dev <package>
```

Never hand-edit `uv.lock`. Commit both `pyproject.toml` and the updated `uv.lock` together.

### docker-compose profile for modules

Module processes are opt-in via the `modules` compose profile:

```bash
# Start all backing services only (default)
docker compose up -d

# Start backing services + all cognitive module processes
docker compose --profile modules up -d

# Start a single module service
docker compose --profile modules up -d sensory-input
```

See [Deployment Guide](deployment.md) for full details.

---

## ESLint

Configuration: [`eslint.config.js`](../../eslint.config.js) (ESLint v9 flat config, `typescript-eslint`).

```bash
# Lint all TypeScript files from the root
npx eslint .

# Lint a specific package
npx eslint shared/
```

Key rules:

- `@typescript-eslint/no-unused-vars` — error (args/vars prefixed `_` are exempt)
- `@typescript-eslint/no-explicit-any` — warn
- `no-console` — warn (allow `console.warn` / `console.error`)

Ignored paths: `**/dist/**`, `**/build/**`, `**/node_modules/**`, `**/.turbo/**`.

---

## Prettier

Configuration: [`.prettierrc.json`](../../.prettierrc.json).  
Ignore list: [`.prettierignore`](../../.prettierignore) (excludes `pnpm-lock.yaml`, `raw_data_dumps/`).

```bash
# Check formatting (CI mode — no writes)
npx prettier --check .

# Fix formatting in-place
npx prettier --write .
```

Prettier is also wired into the `pre-commit` hook (see below) and runs automatically on staged files.

---

## ruff

Configuration: `[tool.ruff]` section of [`pyproject.toml`](../../pyproject.toml).

```bash
# Lint all Python files
uv run ruff check .

# Lint and auto-fix safe issues
uv run ruff check --fix .

# Format Python files (replaces black)
uv run ruff format .
```

Active rule sets: `E`, `W`, `F`, `I` (isort), `B`, `C4`, `UP`, `N`, `SIM`, `RUF`.  
Line length: 100. Target: Python 3.11.

---

## mypy

Configuration: `[tool.mypy]` section of [`pyproject.toml`](../../pyproject.toml) (strict mode).

```bash
uv run mypy .
```

Required stub packages are declared in `pyproject.toml` dev dependencies (e.g. `types-PyYAML`). When adding a new
dependency that lacks inline types, add `types-<package>` to both `pyproject.toml` and the
[`pre-commit` mypy hook](#mypy-1) `additional_dependencies`.

---

## pre-commit

Configuration: [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml).

**Install hooks** (one-time, after `uv sync --dev`):

```bash
uv run pre-commit install          # install commit-msg + pre-commit hooks
uv run pre-commit install --hook-type commit-msg
```

**Run all hooks manually** (equivalent to what CI runs):

```bash
uv run pre-commit run --all-files
```

**Run a single hook**:

```bash
uv run pre-commit run prettier --all-files
uv run pre-commit run ruff --all-files
uv run pre-commit run mypy --all-files
uv run pre-commit run validate-frontmatter --all-files
uv run pre-commit run buf-lint --all-files
```

### Hooks reference

| Hook ID                   | Source                                    | What it checks                                                       |
| ------------------------- | ----------------------------------------- | -------------------------------------------------------------------- |
| `trailing-whitespace`     | `pre-commit-hooks`                        | No trailing whitespace in any file                                   |
| `end-of-file-fixer`       | `pre-commit-hooks`                        | All files end with a single newline                                  |
| `check-yaml`              | `pre-commit-hooks`                        | Valid YAML syntax                                                    |
| `check-json`              | `pre-commit-hooks`                        | Valid JSON syntax                                                    |
| `check-toml`              | `pre-commit-hooks`                        | Valid TOML syntax                                                    |
| `check-merge-conflict`    | `pre-commit-hooks`                        | No unresolved merge conflict markers                                 |
| `check-added-large-files` | `pre-commit-hooks`                        | No files > 500 KB added                                              |
| `mixed-line-ending`       | `pre-commit-hooks`                        | Enforces LF line endings                                             |
| `no-commit-to-branch`     | `pre-commit-hooks`                        | Blocks direct commits to `main`                                      |
| `commitizen`              | `commitizen-tools/commitizen`             | Commit message conforms to Conventional Commits (`commit-msg` stage) |
| `prettier`                | `mirrors-prettier`                        | Formatting for JS/TS/JSON/YAML/Markdown                              |
| `ruff`                    | `astral-sh/ruff-pre-commit`               | Python linting (auto-fixes safe issues)                              |
| `ruff-format`             | `astral-sh/ruff-pre-commit`               | Python formatting                                                    |
| `mypy`                    | `mirrors-mypy`                            | Python static type-checking                                          |
| `buf-lint`                | `bufbuild/buf`                            | Protobuf schema linting against `shared/buf.yaml`                    |
| `validate-frontmatter`    | local (`scripts/validate_frontmatter.py`) | Required YAML frontmatter keys in `resources/**/*.md`                |

---

## buf

Configuration: [`shared/buf.yaml`](../../shared/buf.yaml), [`shared/buf.gen.yaml`](../../shared/buf.gen.yaml).

**Install**: [https://buf.build/docs/installation](https://buf.build/docs/installation)

```bash
# Lint all .proto files in shared/
cd shared && buf lint

# Check for breaking changes against main branch (enabled after Phase 1 baseline)
# cd shared && buf breaking --against '.git#branch=main'
```

All Protobuf schemas live under `shared/schemas/proto/`. The `buf-breaking` hook is commented out in
`.pre-commit-config.yaml` until a stable `.proto` baseline is established at the end of Phase 1.

---

## commitlint

Configuration: [`.commitlintrc.json`](../../.commitlintrc.json) (extends `@commitlint/config-conventional`).

Commit messages must follow **Conventional Commits**:

```
<type>(<scope>): <Description starting with capital letter>

[optional body]

[optional footer(s)]
```

**Allowed types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`

**Allowed scopes** (enforced by `scope-enum`):

`mcp`, `a2a`, `adapters`, `shared`, `sensory-input`, `attention-filtering`, `perception`, `working-memory`,
`short-term-memory`, `long-term-memory`, `episodic-memory`, `affective`, `reasoning`, `executive-agent`,
`agent-runtime`, `motor-output`, `learning-adaptation`, `metacognition`, `observability`, `resources`, `deploy`,
`security`, `apps`, `ci`, `docs`, `repo`

**Manual check**:

```bash
echo "feat(shared): Add new schema" | npx commitlint
```

The `commitizen` pre-commit hook enforces this automatically at the `commit-msg` stage.

---

## Test coverage

Coverage is not run by the pre-commit hooks — run it manually or in CI after the test suite passes.

### Python — pytest-cov

`pytest-cov` must be added to each Python sub-package's `pyproject.toml` individually:

```bash
# Add pytest-cov to a sub-package
cd shared/vector-store/python && uv add --dev pytest-cov
```

Run coverage for a sub-package:

```bash
cd shared/vector-store/python
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Persist a JSON report for `scan_coverage_gaps.py` to parse:

```bash
uv run pytest --cov=src --cov-report=term-missing --cov-report=json:coverage.json --cov-fail-under=80
```

Recommended `pyproject.toml` additions per sub-package:

```toml
[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### TypeScript — @vitest/coverage-v8

`@vitest/coverage-v8` must be added to each TypeScript package's `devDependencies` individually:

```bash
# Add to a specific package
pnpm add -D @vitest/coverage-v8 --filter @accessitech/mcp
```

Run coverage for a package:

```bash
pnpm --filter @accessitech/mcp run test -- --coverage
```

To enforce thresholds, add a `vitest.config.ts` to the package root:

```typescript
import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "json-summary"],
      thresholds: { lines: 80, functions: 80, branches: 80 },
    },
  },
});
```

### Scanning all packages

Use `scripts/testing/scan_coverage_gaps.py` to check all registered packages at once:

```bash
# Preview coverage commands without executing (always exits 0)
uv run python scripts/testing/scan_coverage_gaps.py --dry-run

# Run full scan — exits 1 if any package is below threshold
uv run python scripts/testing/scan_coverage_gaps.py
```

The script reports missing tooling setup (`pytest-cov` / `@vitest/coverage-v8`) with exact installation commands. Add
new packages to the `PYTHON_PACKAGES` / `TS_PACKAGES` lists in the script as modules are created.

---

## Quick Reference

| What you want to check   | Command                                                   |
| ------------------------ | --------------------------------------------------------- |
| All hooks at once        | `uv run pre-commit run --all-files`                       |
| TypeScript lint          | `npx eslint .`                                            |
| Code formatting          | `npx prettier --check .`                                  |
| Fix formatting           | `npx prettier --write .`                                  |
| Python lint              | `uv run ruff check .`                                     |
| Python types             | `uv run mypy .`                                           |
| Protobuf lint            | `cd shared && buf lint`                                   |
| Frontmatter validation   | `uv run pre-commit run validate-frontmatter --all-files`  |
| Commit message format    | `echo "<msg>" \| npx commitlint`                          |
| Full Turborepo pipeline  | `pnpm run lint && pnpm run typecheck && pnpm run test`    |
| Python test coverage     | `cd <pkg> && uv run pytest --cov=src --cov-fail-under=80` |
| TypeScript test coverage | `pnpm --filter <pkg> run test -- --coverage`              |
| Scan all coverage gaps   | `uv run python scripts/testing/scan_coverage_gaps.py`     |

---

## References

- [Getting Started](getting-started.md) — install and run the local stack
- [Adding a Module](adding-a-module.md) — module scaffolding guide
- [Observability](observability.md) — telemetry setup and dashboards
- [Agent Fleet Guide](agents.md) — testing agent fleet and coverage workflow
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — PR process and module contract rules
