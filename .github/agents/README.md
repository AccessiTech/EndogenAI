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
| **Scaffold Agent** | `scaffold-agent.agent.md` | read + create | Generate a new VS Code Copilot agent file from a brief; invoked by Agent Scaffold Executive | Review Agent, Agent Scaffold Executive, GitHub |

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

## Documentation Agent Fleet

Executive → sub-agent hierarchy for all documentation work. Sub-agents read `docs/AGENTS.md` before acting.

| Agent | File | Posture | Trigger | Handoffs | Backing Script |
|-------|------|---------|---------|----------|----------------|
| **Docs Executive** | `docs-executive.agent.md` | full | Orchestrate all documentation work; produce gap report; coordinate scaffold / completeness / accuracy passes | Docs Scaffold, Docs Completeness Review, Docs Accuracy Review, Review | `scripts/docs/scan_missing_docs.py` |
| **Docs Scaffold** | `docs-scaffold.agent.md` | read + create | Generate missing READMEs, JSDoc stubs, and architecture outlines from module structure and schemas | Docs Completeness Review, Docs Executive | `scripts/docs/scaffold_doc.py` |
| **Docs Completeness Review** | `docs-completeness-review.agent.md` | read-only | Audit workspace for modules missing required documentation sections; exits non-zero on gaps | Docs Scaffold, Docs Executive | `scripts/docs/scan_missing_docs.py` |
| **Docs Accuracy Review** | `docs-accuracy-review.agent.md` | read-only | Cross-reference docs against implementation; flag stale paths, wrong API names, outdated descriptions | Implement, Docs Executive | — |

---

## Testing Agent Fleet

Executive → sub-agent hierarchy for the full testing lifecycle. Sub-agents read `shared/AGENTS.md` and the relevant module `AGENTS.md` before acting.

Coverage tooling: **pytest-cov** (Python) and **@vitest/coverage-v8** (TypeScript). Default threshold: **80%**.

| Agent | File | Posture | Trigger | Handoffs | Backing Script |
|-------|------|---------|---------|----------|----------------|
| **Test Executive** | `test-executive.agent.md` | full | Orchestrate the full testing lifecycle; run coverage scan; delegate to scaffold and review sub-agents; confirm all tests pass | Test Scaffold, Test Coverage, Test Review, Review | `scripts/testing/scan_coverage_gaps.py` |
| **Test Scaffold** | `test-scaffold.agent.md` | read + create | Generate test stubs for source files with no test counterpart | Test Review, Test Executive | `scripts/testing/scaffold_tests.py` |
| **Test Coverage** | `test-coverage.agent.md` | full | Run coverage tooling; map untested code paths to module contracts; enforce thresholds | Test Scaffold, Test Executive | `scripts/testing/scan_coverage_gaps.py` |
| **Test Review** | `test-review.agent.md` | read-only | Review assertion quality, Testcontainers use for integration tests, and mocking discipline | Implement, Test Executive | — |

---

## Schema Agent Fleet

An executive to sub-agent hierarchy for schema authoring and safe migration. Invoke **Schema Executive** to run the full pipeline; invoke sub-agents individually for targeted passes.

| Agent | File | Posture | Trigger | Handoffs | Backing Script |
|-------|------|---------|---------|----------|----------------|
| **Schema Executive** | `schema-executive.agent.md` | full | Start of any schema authoring or migration task; blocks implementation until schemas pass | Schema Validator, Schema Migration, Review | `scripts/schema/validate_all_schemas.py` |
| **Schema Validator** | `schema-validator.agent.md` | read-only | After any .schema.json or .proto file is created or edited | Schema Executive, Schema Migration | `scripts/schema/validate_all_schemas.py`, `buf lint` |
| **Schema Migration** | `schema-migration.agent.md` | read-only (+ CHANGELOG.md) | After validation passes on a changed schema; assesses backwards compatibility | Schema Executive, Review | `shared/schemas/CHANGELOG.md` |


## Agent Governance Fleet

Executive and specialist agents for creating, reviewing, updating, and auditing the `.github/agents/` fleet itself.
Invoke **Agent Scaffold Executive** to add a new agent; invoke **Govern Agent** for periodic fleet audits.

| Agent | File | Posture | Trigger | Handoffs |
|-------|------|---------|---------|----------|
| **Agent Scaffold Executive** | `executive-agent-scaffold.agent.md` | full | Adding a new VS Code Copilot agent to the workflow | Scaffold Agent, Review Agent, GitHub |
| **Review Agent** | `review-agent.agent.md` | read-only | After any `.agent.md` or `AGENTS.md` hierarchy file is created or modified | Update Agent, GitHub, Agent Scaffold Executive |
| **Update Agent** | `update-agent.agent.md` | read + create | After Govern Agent or Review Agent reports FAILs on existing agent files | Review Agent, GitHub |
| **Govern Agent** | `govern-agent.agent.md` | read-only | Periodic fleet-wide compliance audit; before merging PRs that add or change agent files | Update Agent, Govern Agent (re-audit) |

---

## Phase Executive Agents

Phase executives drive all deliverables for a specific phase to the milestone gate, then hand off to Review.

| Agent | File | Posture | Phase Scope | Handoffs |
|-------|------|---------|------------|----------|
| **Phase 1 Executive** | `phase-1-executive.agent.md` | full | Phase 1 — Shared Contracts & Vector Store Adapter (`shared/`) | Review, GitHub |
| **Phase 2 Executive** | `phase-2-executive.agent.md` | full | Phase 2 — Communication Infrastructure (`infrastructure/`) | Review, GitHub |
| **Phase 3 Executive** | `phase-3-executive.agent.md` | full | Phase 3 — Development Agent Infrastructure (`.github/agents/`, `scripts/`, nested `AGENTS.md`) | Review, GitHub |
| **Phase 4 Executive** | `phase-4-executive.agent.md` | full | Phase 4 — Group I: Signal Processing Modules (`modules/group-i-signal-processing/`) | Review, GitHub, Plan |

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

Use the **Agent Scaffold Executive** agent. It will:
1. Survey existing agents to establish context and detect naming conflicts.
2. Prepare a brief (name, posture, tools, handoffs, backing script) and delegate file creation to **Scaffold Agent**.
3. Validate frontmatter post-creation and update this README and root `AGENTS.md`.
4. Hand off to **Review Agent** (specialist `.agent.md` review), then **GitHub** (commit).

After adding an agent, confirm it appears in the correct table above and in the handoff graph.
