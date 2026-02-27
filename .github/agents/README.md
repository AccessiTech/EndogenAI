# Agent Fleet Catalog

All VS Code Copilot custom agents for the EndogenAI project.
Each `.agent.md` file appears in the Copilot chat agents dropdown automatically.

For authoring rules — frontmatter schema, posture table, handoff patterns, and script
coupling requirements — see [`.github/agents/AGENTS.md`](./AGENTS.md).

Typical workflow: **Plan → (approve) → Implement → (complete) → Review → GitHub (commit)**

---

## Workflow Agents

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Plan** | `plan.agent.md` | read-only | Start of any new task — survey workplan + codebase, produce a scoped plan | Implement, Plan (retry) |
| **Implement** | `implement.agent.md` | full | Execute an approved plan; enforces all AGENTS.md constraints | Review |
| **Review** | `review.agent.md` | read-only | Pre-commit gate — verify changes against AGENTS.md constraints and module contracts | GitHub |
| **GitHub** | `github.agent.md` | terminal + read | Git/PR workflows — branching, committing, opening and merging PRs | Review |

---

## Scaffolding Agents

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Scaffold Module** | `scaffold-module.agent.md` | read + create | Adding a new cognitive module — derives structure from endogenous knowledge | Review, GitHub |
| **Scaffold Agent** | `scaffold-agent.agent.md` | read + create | Adding a new VS Code Copilot agent to the development workflow | Review, GitHub |

---

## Diagnostic Agents

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Debugger** | `executive-debugger.agent.md` | full | Diagnose and fix runtime errors or test failures across the codebase | Review, GitHub |

---

## Planning & Orchestration Agents

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Executive Planner** | `executive-planner.agent.md` | read + edit | Reconcile `docs/Workplan.md` against current codebase state; update checklist; recommend next agent | Review, GitHub, Executive Planner (iterate) |

---

## Phase Executive Agents

Phase executives drive all deliverables for a specific phase to the milestone gate, then hand off to Review.

| Agent | File | Posture | Phase Scope | Handoffs |
|-------|------|---------|------------|----------|
| **Phase 1 Executive** | `phase-1-executive.agent.md` | full | Phase 1 — Shared Contracts & Vector Store Adapter (`shared/`) | Review, GitHub |
| **Phase 2 Executive** | `phase-2-executive.agent.md` | full | Phase 2 — Communication Infrastructure (`infrastructure/`) | Review, GitHub |
| **Phase 3 Executive** | `phase-3-executive.agent.md` | full | Phase 3 — Development Agent Infrastructure (`.github/agents/`, `scripts/`, nested `AGENTS.md`) | Review, GitHub |

---

## Handoff Graph

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

**Detour**: if Review raises FAILs → back to Implement/Executive for fixes, then re-Review.

**Debug path**: Implement or Phase Executive → Executive Debugger → back to Implement/Phase Executive.

---

## Supporting Scripts

Scripts that back agents in this fleet. All scripts support `--dry-run` and must exit 0 on the
current codebase. Each script has a co-located `tests/` directory.

| Script | Backing Agent(s) | Purpose |
|--------|-----------------|---------|
| `scripts/validate_frontmatter.py` | Review, Executive Planner | Validate YAML frontmatter in `resources/` |
| `scripts/docs/scaffold_doc.py` | Docs Scaffold | Generate README / JSDoc stubs from module structure |
| `scripts/docs/scan_missing_docs.py` | Docs Completeness Review | Report modules missing required documentation |
| `scripts/testing/scaffold_tests.py` | Test Scaffold | Generate test stubs from source file interfaces |
| `scripts/testing/scan_coverage_gaps.py` | Test Coverage | Report modules below coverage threshold |
| `scripts/schema/validate_all_schemas.py` | Schema Validator | Validate JSON Schema required keys; run `buf lint` |

> Scripts in `scripts/docs/`, `scripts/testing/`, and `scripts/schema/` are Phase 3 deliverables.
> The table above represents the full intended fleet; scripts are added as sections are completed.

---

## Adding a New Agent

Use the **Scaffold Agent** agent. It will:
1. Read all existing agents to infer naming conventions and posture.
2. Create the `.agent.md` file with correct frontmatter and body structure per `.github/agents/AGENTS.md`.
3. Hand off to Review, then GitHub.

After adding an agent, update this README to include it in the appropriate table and handoff graph.
