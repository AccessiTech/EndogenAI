---
id: guide-agents
version: 0.1.0
status: in-progress
last-reviewed: 2026-02-27
---

# Agent Fleet Guide

This guide explains the EndogenAI VS Code Copilot agent fleet: what each agent does, when to use it, and how the
agents hand off work to each other. The authoritative machine-readable catalog is in
[`.github/agents/README.md`](../../.github/agents/README.md); this document is the human-readable companion.

---

## Prerequisites

- VS Code with the GitHub Copilot extension installed and signed in.
- The repository open as the workspace root — agents scan from the workspace root when using tool calls.
- Familiarity with the project conventions in [`AGENTS.md`](../../AGENTS.md) (read it once before invoking any
  action-taking agent).

### Opening an agent

Open the Copilot Chat panel (`⌃⌘I` / `Ctrl+Alt+I`), click the **agent dropdown** (the `@` icon or the agent selector
next to the chat input), and choose the agent by name. Every `.agent.md` file in `.github/agents/` appears in the
dropdown automatically.

---

## Agent posture

Every agent has a declared *posture* that controls what tools it is allowed to use. Choose the minimum posture that
fits the task — never invoke a full-execution agent when a read-only audit will do.

| Posture | What it can do | When to use it |
|---------|---------------|----------------|
| **Read-only** | Searches, reads files, checks errors | Reviews, audits, planning passes |
| **Read + create** | Reads + creates new files | Scaffolding new modules or agents |
| **Full execution** | Reads, edits, runs terminal commands, runs tests | Implementation, debugging, executive orchestration |

---

## Typical day-to-day workflows

### Starting a new feature or task

```
Executive Planner   — check Workplan, confirm what's next
        ↓
Plan                — produce a scoped implementation plan
        ↓ (approve the plan)
Implement           — execute the plan
        ↓
Review              — pre-commit gate
        ↓
GitHub              — commit, push, open PR
```

### Adding a new cognitive module

```
Scaffold Module     — derive skeleton from endogenous knowledge
        ↓ (review scaffold)
Implement           — fill in src/ and tests/
        ↓
Review → GitHub
```

### Running a documentation pass

```
Docs Executive      — runs scan_missing_docs.py, produces gap report
        ↓ (gaps found)
Docs Scaffold       — generate missing READMEs / JSDoc stubs
        ↓
Docs Completeness Review  — confirm all required sections present
        ↓
Docs Accuracy Review      — cross-check paths and API names
        ↓
Review → GitHub
```

### Running a test coverage pass

```
Test Executive      — runs uv run pytest + pnpm run test, then scan_coverage_gaps.py
        ↓ (gaps found)
Test Scaffold       — generate stubs for uncovered source files
        ↓
Test Coverage       — re-run coverage; enforce 80% threshold per module
        ↓
Test Review         — assert quality, Testcontainers hygiene, mocking discipline
        ↓
Review → GitHub
```

### Diagnosing a failing test or runtime error

```
Executive Debugger  — diagnose and fix the failure
        ↓
Review → GitHub
```

---

## Agent catalog

### Workflow agents

These four agents form the backbone of every development session.

**Plan** (`plan.agent.md`) — read-only  
Surveys `docs/Workplan.md` and the codebase, then produces a scoped, ordered implementation plan. Always start here
before touching code. Does not create or edit files.

**Implement** (`implement.agent.md`) — full execution  
Executes a pre-approved plan. Enforces all `AGENTS.md` constraints inline: schemas-first, `uv run` only, no direct
LLM calls, incremental commits. Runs lint and typecheck after every logical boundary. Hands off to Review.

**Review** (`review.agent.md`) — read-only  
Pre-commit gate. Audits all changed files against `AGENTS.md` constraints and module contracts; produces a structured
PASS / WARN / FAIL report. Does not fix anything — it flags. Hands off to GitHub (on PASS) or back to Implement
(on FAIL).

**GitHub** (`github.agent.md`) — terminal + read  
Handles all git operations: branching, staging, incremental commits (Conventional Commits format), pushing, and
opening or merging PRs. Invoke after Review has passed.

---

### Scaffolding agents

**Scaffold Module** (`scaffold-module.agent.md`) — read + create  
Generates a complete module skeleton from endogenous knowledge: `README.md`, `agent-card.json`, `pyproject.toml` or
`package.json`, and empty `src/` / `tests/` stubs. Derives structure from `readme.md`, `shared/schemas/`, and
`collection-registry.json`. Never invents file paths or API names. Provide the module name and cognitive group:
`perception in group-i-signal-processing`.

**Scaffold Agent** (`scaffold-agent.agent.md`) — read + create  
Generates a new `.agent.md` file by reading all existing agents and inferring naming and posture conventions from
`.github/agents/AGENTS.md`. Use when adding a net-new agent to the fleet.

---

### Diagnostic agents

**Executive Debugger** (`executive-debugger.agent.md`) — full execution  
Diagnoses and fixes runtime errors or failing tests across the codebase. Has full tool access. Invoke when a test
suite is red and the root cause is non-obvious. Hands off to Review.

---

### Planning & orchestration agents

**Executive Planner** (`executive-planner.agent.md`) — read + edit  
Reconciles `docs/Workplan.md` against the actual codebase state. Marks completed items `[x]`, surfaces gaps, and
recommends the next agent to engage. Edits only `docs/Workplan.md` — never touches source files. Run at the start of
a session to orient yourself before calling Plan or an executive.

---

### Documentation agent fleet

An executive → sub-agent hierarchy. Invoke **Docs Executive** to run the full documentation pipeline; invoke
sub-agents individually when you only need one pass.

**Docs Executive** (`docs-executive.agent.md`) — full execution  
Orchestrates the documentation pipeline: runs `scripts/docs/scan_missing_docs.py` to produce a gap report, then
delegates to sub-agents in sequence, and hands off to Review when done.

**Docs Scaffold** (`docs-scaffold.agent.md`) — read + create  
Generates missing `README.md` files and JSDoc stubs by reading module structure, `shared/schemas/`, and
`collection-registry.json`. Backed by [`scripts/docs/scaffold_doc.py`](../../scripts/docs/scaffold_doc.py). Always
runs `--dry-run` first before writing files.

**Docs Completeness Review** (`docs-completeness-review.agent.md`) — read-only  
Audits every module and package for missing required documentation sections. Backed by
[`scripts/docs/scan_missing_docs.py`](../../scripts/docs/scan_missing_docs.py). Produces a gap table with HIGH /
WARN / INFO severity. Checks README sections automatically; checks JSDoc, Python docstrings, and `agent-card.json`
descriptions manually.

**Docs Accuracy Review** (`docs-accuracy-review.agent.md`) — read-only  
Cross-references every documentation claim against the current codebase. Flags stale file paths, wrong API names,
outdated schema references, and protocol descriptions that diverge from the implementation. Never updates docs to
match potentially broken code — flags divergences instead.

---

### Testing agent fleet

An executive → sub-agent hierarchy for the full testing lifecycle. Coverage tooling: **pytest-cov** (Python) and
**@vitest/coverage-v8** (TypeScript). Default threshold: **80%** lines, functions, and branches per package.
Invoke **Test Executive** to run the full pipeline; invoke sub-agents individually for targeted passes.

**Test Executive** (`test-executive.agent.md`) — full execution  
Orchestrates the complete testing lifecycle: runs `uv run pytest` and `pnpm run test` for a baseline, then runs
`scripts/testing/scan_coverage_gaps.py` to identify modules below threshold. Delegates stub generation to Test
Scaffold, quality review to Test Review, and hands off to Review when all tests pass and all thresholds are met.

**Test Scaffold** (`test-scaffold.agent.md`) — read + create  
Generates vitest (`describe`/`it`) and pytest (`class Test…`/`def test_…`) stubs for source files with no test
counterpart. Backed by [`scripts/testing/scaffold_tests.py`](../../scripts/testing/scaffold_tests.py). Derives all
symbol names from actual source file exports — never invents function signatures. Always runs `--dry-run` first.
Use `--file infrastructure/mcp/src/broker.ts` to scope to a single file.

**Test Coverage** (`test-coverage.agent.md`) — full execution  
Runs `pytest --cov` and `vitest --coverage` for all registered packages. Reports which packages are below the 80%
threshold and provides the exact `uv add --dev pytest-cov` / `pnpm add -D @vitest/coverage-v8` setup commands for
any package not yet wired. Backed by [`scripts/testing/scan_coverage_gaps.py`](../../scripts/testing/scan_coverage_gaps.py).

**Test Review** (`test-review.agent.md`) — read-only  
Audits the test suite for quality issues: checks that no `expect(true).toBe(false)` / `assert False` placeholder
stubs remain, validates Testcontainers use for integration tests, flags excessive mocking of internal collaborators.
Produces a PASS / WARN / FAIL report with file and line references.

---

### Phase executive agents

Each phase executive drives all deliverables for its phase to the milestone gate, then hands off to Review. They are
aware of the full roadmap but will not author deliverables belonging to another phase.

| Agent | Phase | Milestone |
|-------|-------|-----------|
| **Phase 1 Executive** | Shared Contracts & Vector Store Adapter | M1 — Contracts Stable |
| **Phase 2 Executive** | Communication Infrastructure (MCP + A2A) | M2 — Infrastructure Online |
| **Phase 3 Executive** | Development Agent Infrastructure | M3 — Dev Agent Fleet Live |

---

## Handoff graph

```
                    ┌──────────────────────────────────────────────────────┐
                    │                Executive Planner                     │
                    │ (workplan reconciliation; recommends next agent)      │
                    └────────────────────┬─────────────────────────────────┘
                                         │
              ┌──────────────────────────▼──────────────────────────┐
              │                       Plan                           │
              │ (read-only; produces scoped implementation plan)     │
              └──────────────────────────┬──────────────────────────┘
                                         │ approve
              ┌──────────────────────────▼──────────────────────────┐
              │  Implement / Phase N Executive / Scaffold Agent      │
              │  (full-execution; creates and edits files)           │
              └──────────────────────────┬──────────────────────────┘
                                         │
              ┌──────────────────────────▼──────────────────────────┐
              │                      Review                          │
              │ (read-only; structured PASS/WARN/FAIL report)        │
              └──────────────────────────┬──────────────────────────┘
                                         │ approved
              ┌──────────────────────────▼──────────────────────────┐
              │                      GitHub                          │
              │ (terminal; commits, branches, PRs)                   │
              └─────────────────────────────────────────────────────┘
```

**Detour**: Review raises FAILs → back to Implement / Executive for fixes → re-Review.  
**Debug path**: Implement or Executive → Executive Debugger → back to Implement / Executive.  
**Docs path**: Docs Executive → sub-agents → Review → GitHub (see [Documentation pass](#documentation-agent-fleet) above).  
**Testing path**: Test Executive → sub-agents → Review → GitHub (see [Testing pass](#testing-agent-fleet) above).

---

## Verification

To confirm the agent fleet is healthy before starting a session:

```bash
# Confirm all required docs are present
uv run python scripts/docs/scan_missing_docs.py --dry-run

# Confirm coverage tooling is wired for all packages
uv run python scripts/testing/scan_coverage_gaps.py --dry-run

# Run the full script test suite (docs + testing scripts)
uv run pytest scripts/docs/tests/ scripts/testing/tests/ -v

# Confirm frontmatter on resource files is valid
uv run pre-commit run validate-frontmatter --all-files
```

---

## Troubleshooting

**Agent doesn't appear in the dropdown**  
Confirm the `.agent.md` file has valid YAML frontmatter with a unique `name` field. Reload VS Code if the file was
just added.

**Agent takes an action I didn't expect**  
Every action-taking agent (`send: false`) pre-fills a prompt but does not auto-submit. Read the pre-filled prompt
before confirming. If an agent modifies files it shouldn't, raise it as an issue — all agents are governed by
[`.github/agents/AGENTS.md`](../../.github/agents/AGENTS.md).

**scan_missing_docs.py exits 1 in CI**  
The script found a missing README or required section. Run it locally with `--dry-run` to see the gap report, then
invoke **Docs Scaffold** to generate the missing files.

**Schema validation script fails or reports missing schemas**  
`scripts/schema/validate_all_schemas.py` validates JSON/YAML schemas used by agents and backing tools. Run it locally
to reproduce CI failures and update or add the referenced schemas as needed. See `docs/Workplan.md` §3.4 for expected
schema coverage.

---

## References

- [`.github/agents/README.md`](../../.github/agents/README.md) — machine-readable agent catalog (posture, triggers, handoffs, scripts)
- [`.github/agents/AGENTS.md`](../../.github/agents/AGENTS.md) — authoring rules: frontmatter schema, posture table, handoff patterns
- [`docs/Workplan.md`](../Workplan.md) — current phase checklist and milestone gates
- [`AGENTS.md`](../../AGENTS.md) — root constraints that all agents inherit
- [`scripts/docs/scaffold_doc.py`](../../scripts/docs/scaffold_doc.py) — documentation scaffold script
- [`scripts/docs/scan_missing_docs.py`](../../scripts/docs/scan_missing_docs.py) — documentation gap scanner
- [`scripts/testing/scaffold_tests.py`](../../scripts/testing/scaffold_tests.py) — test stub generator
- [`scripts/testing/scan_coverage_gaps.py`](../../scripts/testing/scan_coverage_gaps.py) — coverage gap scanner
