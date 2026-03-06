# scripts/

Reusable endogenous scripts for the EndogenAI monorepo. All scripts are first-class repo
artifacts: committed, documented, and runnable from CI. Per `AGENTS.md` conventions, every
script opens with a docstring or comment block describing its purpose, inputs, outputs, and
usage example.

---

## Directory Layout

```
scripts/
  healthcheck.sh                   # Backing-service pre-flight verifier
  validate_frontmatter.py          # Frontmatter validator (pre-commit hook)
  fetch_source.py                  # Source manifest fetcher
  fix_agent_tools.py               # Agent tool ID canonicalisation
  rename_brain_to_frankenbrain.py  # Rename brAIn => frankenbrAIn across all text files
  tests/                           # Tests for root-level scripts

  docs/
    scan_missing_docs.py           # Documentation gap scanner
    scaffold_doc.py                # Documentation stub generator
    tests/                         # Tests for docs scripts

  testing/
    scan_coverage_gaps.py          # Aggregate cross-package coverage scanner
    scan_opa_coverage.py           # OPA test coverage specialist scanner
    scan_temporal_coverage.py      # Temporal workflow test coverage specialist scanner
    scaffold_tests.py              # Test stub generator
    tests/                         # Tests for testing scripts

  schema/
    validate_all_schemas.py        # JSON/YAML schema validator
    tests/                         # Tests for schema scripts

  fetch_manifests/                 # Manifest-fetch helpers (see fetch_source.py)
```

---

## scripts/healthcheck.sh

**Purpose**: Verify all EndogenAI backing services are reachable and ready for integration
tests. Checks ChromaDB, Ollama (including `nomic-embed-text` model presence), the OTel
collector gRPC port, and Prometheus.

**Usage**:

```bash
bash scripts/healthcheck.sh
# Exits 0 only when ALL services pass.

# Override service URLs:
CHROMADB_URL=http://chromadb:8000 OLLAMA_URL=http://ollama:11434 bash scripts/healthcheck.sh
```

**When to run**: before executing integration tests in CI or locally; wired into the
[`docs/test-upgrade-workplan.md`](../docs/test-upgrade-workplan.md) T6/P24 integration CI job.

---

## scripts/validate_frontmatter.py

**Purpose**: Validate YAML frontmatter in `resources/**/*.md` files. Checks for required keys
(`id`, `version`, `status`, `maps-to-modules`). Used as a `pre-commit` hook.

**Usage**:

```bash
uv run python scripts/validate_frontmatter.py resources/
uv run pre-commit run validate-frontmatter --all-files
```

---

## scripts/fetch_source.py

**Purpose**: Fetch external source manifests referenced by the codebase (schema stubs,
neuroanatomy references). Populates `resources/static/` from remote URIs declared in
`resources/uri-registry.json`.

**Usage**:

```bash
uv run python scripts/fetch_source.py
```

---

## scripts/fix_agent_tools.py

**Purpose**: Canonicalise agent tool IDs in `.github/agents/*.agent.md` files. Replaces
slash-prefixed forms (`search/codebase`) and legacy individual tool names with the approved
toolset names (`search`, `read`, `edit`, etc.) as defined in `.github/agents/AGENTS.md`.

**Usage**:

```bash
uv run python scripts/fix_agent_tools.py              # dry-run by default
uv run python scripts/fix_agent_tools.py --apply      # write changes
```

---

## scripts/rename_brain_to_frankenbrain.py

**Purpose**: Rename all occurrences of `brAIn` to `frankenbrAIn` throughout the EndogenAI
repository. Processes every text file that is not binary, not in a generated/dependency
directory (`.git`, `node_modules`, `.venv`, `dist`, `__pycache__`, `.mypy_cache`,
`.ruff_cache`, `coverage`), and not an auto-generated lockfile (`pnpm-lock.yaml`,
`uv.lock`).

**API**:

| Name | Kind | Description |
|------|------|-------------|
| `REPO_ROOT` | `str` | Absolute path to the repository root (derived from the script's own location). |
| `SKIP_DIRS` | `set[str]` | Directory names that are pruned from the `os.walk` traversal. |
| `SKIP_FILES` | `set[str]` | Filenames that are skipped unconditionally (lockfiles). |
| `OLD` | `str` | The string being replaced (`"brAIn"`). |
| `NEW` | `str` | The replacement string (`"frankenbrAIn"`). |
| `is_binary(path)` | `(str) -> bool` | Returns `True` if the file contains a null byte in its first 8,192 bytes, or if the file cannot be read. |
| `process_file(path, dry_run)` | `(str, bool) -> bool` | Reads a file, replaces `OLD` with `NEW`, writes it back (unless `dry_run`). Returns `True` when the file was (or would be) changed. |
| `main()` | `() -> None` | CLI entry-point. Walks `REPO_ROOT`, calls `process_file` on each eligible file, and prints a summary. |

**Usage**:

```bash
# Preview changes without writing
uv run python scripts/rename_brain_to_frankenbrain.py --dry-run

# Apply changes
uv run python scripts/rename_brain_to_frankenbrain.py
```

**Tests**:

```bash
uv run pytest scripts/tests/test_rename_brain_to_frankenbrain.py -v
```

---

## scripts/testing/scan_coverage_gaps.py

**Purpose**: Aggregate cross-package coverage scanner. Runs `pytest --cov` and
`vitest --coverage` for all registered Python and TypeScript packages. Reports packages below
the 80% threshold with exact installation commands for missing tooling. Hard-fails (exit 1) if
any package is below threshold or if coverage tooling is not configured.

**Usage**:

```bash
# Preview — prints commands, exits 0
uv run python scripts/testing/scan_coverage_gaps.py --dry-run

# Full scan — exits 1 if any package below 80%
uv run python scripts/testing/scan_coverage_gaps.py
```

**Packages registered**: all 16 Python modules (group-i through group-iv), `shared/vector-store/python`,
`shared/a2a/python`, `infrastructure/mcp`, `infrastructure/a2a`, `infrastructure/adapters`,
`shared/vector-store/typescript`, `apps/default/client`, `apps/default/server`. Add new packages
to `PYTHON_PACKAGES` / `TS_PACKAGES` as modules are created (see workplan P07).

---

## scripts/testing/scan_opa_coverage.py

**Purpose**: Specialist scanner for OPA test coverage. Identifies Python packages that use Open
Policy Agent and verifies:

- Tests exercise OPA policy evaluation paths.
- `SKIP_OPA_TESTS` environment guard is wired in `conftest.py`.
- `pytest-cov` and `--cov` addopts are present.
- Testcontainer or httpx-mock patterns are used to avoid live-service dependencies.

Exits 1 if any module has hard configuration errors (missing skip guard, missing tests);
exits 0 for warnings only.

**Usage**:

```bash
uv run python scripts/testing/scan_opa_coverage.py [--dry-run]
```

**Registry**: `modules/group-iii-executive-output/executive-agent` (uses OPA for BDI policy
evaluation via `src/executive_agent/bdi/policy_engine.py`).

**Related**: [`scripts/healthcheck.sh`](healthcheck.sh) to verify OPA service is reachable.

---

## scripts/testing/scan_temporal_coverage.py

**Purpose**: Specialist scanner for Temporal workflow test coverage. Identifies Python packages
that use Temporal (or its Prefect fallback) and verifies:

- Tests exist for `workflow.py`, `worker.py`, and `prefect_fallback.py`.
- `SKIP_TEMPORAL_TESTS` and `SKIP_INTEGRATION_TESTS` guards are wired in `conftest.py`.
- `temporalio.testing.WorkflowEnvironment.start_time_skipping()` is used for integration tests
  (no live Temporal dev server required).
- Prefect fallback is covered by unit tests using mocked `httpx`.

Exits 1 if any module has hard configuration errors; exits 0 for warnings only.

**Usage**:

```bash
uv run python scripts/testing/scan_temporal_coverage.py [--dry-run]
```

**Registry**: `modules/group-iii-executive-output/agent-runtime` (implements Temporal workflows
and Prefect fallback in `src/agent_runtime/`).

**Related**: [`scan_opa_coverage.py`](testing/scan_opa_coverage.py) (OPA specialist scanner),
[`healthcheck.sh`](healthcheck.sh) (service verifier).

---

## scripts/testing/scaffold_tests.py

**Purpose**: Generate `pytest` and `vitest` test stubs for source files with no test counterpart.
Derives all symbol names from actual source file exports — never invents function signatures.

**Usage**:

```bash
# Dry-run (print stubs, do not write)
uv run python scripts/testing/scaffold_tests.py --dry-run

# Scaffold for a single source file
uv run python scripts/testing/scaffold_tests.py --file infrastructure/mcp/src/broker.ts
```

---

## scripts/docs/scan_missing_docs.py

**Purpose**: Documentation gap scanner. Checks every module and package for a `README.md` with
all required sections. Reports missing files and missing required sections at HIGH / WARN / INFO
severity. Exits 1 if any HIGH gaps remain.

**Usage**:

```bash
# Dry-run
uv run python scripts/docs/scan_missing_docs.py --dry-run

# Full scan
uv run python scripts/docs/scan_missing_docs.py
```

---

## scripts/docs/scaffold_doc.py

**Purpose**: Generate missing `README.md` stubs from endogenous codebase knowledge — module name,
schemas, collection registry, and `pyproject.toml` / `package.json`. Always run `--dry-run` first.

**Usage**:

```bash
# Dry-run
uv run python scripts/docs/scaffold_doc.py --dry-run --target modules/group-i-signal-processing/sensory-input

# Write
uv run python scripts/docs/scaffold_doc.py --target modules/group-i-signal-processing/sensory-input
```

---

## scripts/schema/validate_all_schemas.py

**Purpose**: Validate all JSON and YAML schemas referenced by agents and backing tools against
their declared meta-schemas. Ensures every schema in `shared/schemas/` is syntactically valid and
internally consistent.

**Usage**:

```bash
uv run python scripts/schema/validate_all_schemas.py
```

---

## Running Script Tests

Each script sub-directory (and the root `scripts/tests/` folder) has a `tests/` folder with `pytest` tests:

```bash
# Test all scripts at once
uv run pytest scripts/tests/ scripts/docs/tests/ scripts/testing/tests/ scripts/schema/tests/ -v

# Test root-level scripts only
uv run pytest scripts/tests/ -v

# Test a specific sub-directory
uv run pytest scripts/testing/tests/ -v
```

---

## References

- [`AGENTS.md` — Development Scripts section](../AGENTS.md#development-scripts) — conventions for when to write scripts, naming, and documentation requirements
- [`docs/test-upgrade-workplan.md`](../docs/test-upgrade-workplan.md) — P07, P26, T3, T6: coverage tooling and healthcheck tasks
- [`docs/guides/toolchain.md`](../docs/guides/toolchain.md) — full toolchain command reference including coverage scanning
