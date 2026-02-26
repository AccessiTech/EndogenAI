---
id: guide-toolchain
version: 0.1.0
status: in-progress
last-reviewed: 2026-02-24
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

## Quick Reference

| What you want to check  | Command                                                  |
| ----------------------- | -------------------------------------------------------- |
| All hooks at once       | `uv run pre-commit run --all-files`                      |
| TypeScript lint         | `npx eslint .`                                           |
| Code formatting         | `npx prettier --check .`                                 |
| Fix formatting          | `npx prettier --write .`                                 |
| Python lint             | `uv run ruff check .`                                    |
| Python types            | `uv run mypy .`                                          |
| Protobuf lint           | `cd shared && buf lint`                                  |
| Frontmatter validation  | `uv run pre-commit run validate-frontmatter --all-files` |
| Commit message format   | `echo "<msg>" \| npx commitlint`                         |
| Full Turborepo pipeline | `pnpm run lint && pnpm run typecheck && pnpm run test`   |

---

## References

- [Getting Started](getting-started.md) — install and run the local stack
- [Adding a Module](adding-a-module.md) — module scaffolding guide
- [Observability](observability.md) — telemetry setup and dashboards
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — PR process and module contract rules
