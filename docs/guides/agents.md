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

### Toolsets

All tool references in `.agent.md` frontmatter use **toolset names** — stable named bundles provided by the
VS Code Copilot API. Using toolsets instead of individual tool IDs makes frontmatter resilient to API-level
renames (e.g. `runInTerminal` → `execute/runInTerminal`).

| Toolset | Individual tools bundled | Purpose |
|---------|-------------------------|---------|
| `search` | `codebase`, `findFiles`, `findTestFiles`, `grep` | Search code and files |
| `read` | `readFile`, `problems`, `terminalLastCommand`, `listDirectory` | Read files, errors, terminal state |
| `edit` | `editFiles`, `insertEdit` | Create, edit, and delete files |
| `web` | `fetch` + web search | Fetch URLs, web search |
| `execute` | `runInTerminal`, `getTerminalOutput`, `runTests` | Run shell commands and tests |
| `terminal` | `runInTerminal`, `getTerminalOutput`, `terminalLastCommand` | Full terminal read/write access |
| `changes` | — | Read current git diff |
| `usages` | — | Find symbol definitions and references |
| `agent` | — | Invoke another agent as a subagent (see [Subagent model](#subagent-model)) |

> **Note:** Individual tool names like `codebase`, `editFiles`, and `runInTerminal` still work at runtime but
> are not the canonical form — use toolset names in all new and updated `.agent.md` files. Slash-prefixed
> forms (`search/codebase`, `edit/editFiles`, etc.) are also not used here.

---

## Subagent model

Executive agents orchestrate their contextual sub-fleet by invoking other agents as **subagents** — delegating
specialist tasks while retaining editorial control over the overall workflow. This is the mechanism that allows
Documents Executive, Test Executive, and Phase Executives to run multi-step pipelines without every agent needing
full tool access.

### How it works

An agent becomes an **orchestrator** by:
1. Including `agent` in its `tools` list.
2. Declaring an `agents` property listing the names of agents it may invoke.
3. Issuing subagent calls in its prompt, e.g. `"Use the Docs Scaffold agent to generate missing READMEs."`

A subagent that should never appear in the user-facing dropdown (only invokable from an executive) sets
`user-invokable: false` in its frontmatter.

```yaml
# Executive frontmatter example
---
name: Docs Executive
tools:
  - search
  - read
  - edit
  - web
  - execute
  - terminal
  - changes
  - usages
  - agent
agents:
  - Docs Scaffold
  - Docs Completeness Review
  - Docs Accuracy Review
---
```

```yaml
# Sub-agent frontmatter example (hidden from dropdown)
---
name: Docs Scaffold
user-invokable: false
tools:
  - search
  - read
  - edit
  - web
  - usages
---
```

### Sequential vs. parallel

- **Sequential**: default — the executive calls one subagent, waits for its result, then calls the next based on
  findings. Use this when each step depends on the previous output (e.g. scaffold → review → fix).
- **Parallel**: the executive instructs multiple subagents to run simultaneously and synthesises their independent
  results. Use for independent review perspectives (e.g. accuracy, completeness, and freshness in parallel).

### Context window efficiency and `.tmp/`

Delegation + the active session file (`.tmp/<branch-slug>/<YYYY-MM-DD>.md`) allow an orchestrator to handle large tasks without exhausting its
context window:

- The orchestrator delegates bounded sub-tasks to specialists. Each specialist operates with a
  short, focused context window and writes structured output to the active session file under a named heading.
- The orchestrator reads the active session file's section summaries rather than receiving full sub-agent
  transcripts inline, keeping the executive's context window clear for high-level decisions.
- Sub-delegation (a specialist delegates to a sub-specialist) amplifies this further — context
  savings multiply with each delegation tier.

The active session file is gitignored and never committed. Each agent appends under `## <Phase/Task> Results`.
The executive reads the active session file before each delegation step to avoid re-discovering already-gathered context.

**Size guard:** if the active session file exceeds 200 lines, invoke the **Scratchpad Janitor** before
the next delegation. The Janitor compresses completed sections to one-line archive stubs
so the file stays lean without losing traceability.
Each new day starts with a fresh, empty session file — daily rotation is the primary size management mechanism; the Janitor is the fallback for sessions that grow large within a single day.

### Insufficient-posture escalation

When a sub-agent cannot complete a task, it must not stop silently. It must:

1. Write `## <AgentName> Escalation` to the active session file: what was completed, the blocking issue, the
   recommended next agent, and step-by-step instructions.
2. Return to the executive via the “Back to [Executive]” handoff button.

The executive then decides: re-delegate to a different agent, create a new specialist, or handle
the block directly.

### Sub-fleet map

| Executive | Sub-agents |
|-----------|------------|
| **Docs Executive** | Docs Scaffold → Docs Completeness Review → Docs Accuracy Review |
| **Test Executive** | Test Scaffold → Test Coverage → Test Review |
| **Schema Executive** | Schema Validator, Schema Migration |
| **Phase 1 Executive** | Plan, Scaffold Module, Implement, Schema Validator, Schema Migration |
| **Phase 2 Executive** | Plan, Implement, Schema Validator |
| **Phase 3 Executive** | Plan, Scaffold Agent, Implement, Review Agent |
| **Agent Scaffold Executive** | Scaffold Agent, Review Agent |

> See [VS Code subagents docs](https://code.visualstudio.com/docs/copilot/agents/subagents) for the full
> specification, including multi-turn feedback loops and parallel execution patterns.

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

### Running a large orchestrated session (Executive Orchestrator pattern)

For multi-phase, multi-domain work (test upgrades, full docs passes, phase deliveries):

0. **Initialise the session file** — run `python scripts/prune_scratchpad.py --init` to create
   today's `.tmp/<branch-slug>/<YYYY-MM-DD>.md`. Check `_index.md` for prior-session context.
1. **Use Plan first** — agree scope before any agent acts.
2. **Delegate, don't inline** — use one executive per domain (Test, Docs, Phase N).
3. **Gate phases with Review** — after each domain executive completes, route through Review
   before committing, then GitHub.
4. **Use the active session file as scratchpad** — executives write phase summaries; sub-agents write gap
   reports and escalation notes. Read the active session file at the start of each step.
5. **Ask clarifying questions** — for any trade-off or ambiguous scope, ask before acting.
   One question costs less context than redoing large amounts of work.
6. **Create specialist agents on demand** — when a task domain is deep enough to recur, author
   a `.agent.md`, commit it, then invoke it. The file is itself the documentation of the decision.
7. **State exclusions explicitly** — full-execution agents default to full scope. Always tell a
   delegated agent which file types it must NOT touch.

```
Orchestrator (Copilot Agent mode / Plan agent)
     │
     ├─ Domain Executive A → active session output → Review → GitHub (commit)
     ├─ Domain Executive B → active session output → Review → GitHub (commit)
     └─ Docs Executive    → completeness + accuracy → Review → GitHub (commit)
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

**Executive Orchestrator** (`executive-orchestrator.agent.md`) — full execution  
Top-level "CEO" agent with two modes of operation:

- **Cold-start orientation**: invoked at the beginning of a new session or branch. Reads the active session file (`.tmp/<branch-slug>/<YYYY-MM-DD>.md`) and `docs/Workplan.md`, identifies the active phase and milestone, lists blocked and ready tasks, and recommends (or delegates to) the correct next agent. If the active session file ≥ 200 lines, invokes Scratchpad Janitor before proceeding.
- **Request triage**: receives ambiguous or cross-cutting requests, decomposes them into atomic sub-tasks, maps each to the right specialist, and delegates using the takeback pattern (each sub-agent's final handoff returns results to the Orchestrator before the next step begins).

The Orchestrator acts directly only for lightweight coordination (reading files, updating the active session file). All implementation, testing, documentation, schema, and phase work is delegated. At session end it writes `## Session Summary` to the active session file and runs `python scripts/prune_scratchpad.py --force` to archive completed sections. Has handoff buttons to every phase executive (1–8), Executive Planner, Executive Debugger, Plan, Review, GitHub, Schema Executive, Test Executive, Docs Executive, and Scratchpad Janitor.

**Executive Planner** (`executive-planner.agent.md`) — read + edit  
Reconciles `docs/Workplan.md` against the actual codebase state. Marks completed items `[x]`, surfaces gaps, and
recommends the next agent to engage. Edits only `docs/Workplan.md` — never touches source files. Run at the start of
a session to orient yourself before calling Plan or an executive.

---

### Utility agents

**Scratchpad Janitor** (`scratchpad-janitor.agent.md`) — read + create  
Prunes the active session file (`.tmp/<branch-slug>/<YYYY-MM-DD>.md`) when it exceeds the 200-line size guard. Compresses completed sections
(those with headings containing "Results", "Complete", "Summary", "Done", etc.) to
one-line archive stubs, inserts an `## Active Context` table of contents, and returns
control to the invoking executive. Invoke manually at session start when the active session file is
stale, or via the "Prune Scratchpad" handoff button on any executive agent. Backed by
[`scripts/prune_scratchpad.py`](../../scripts/prune_scratchpad.py).

---

### Documentation agent fleet

An executive → sub-agent hierarchy driven by the [subagent model](#subagent-model). Invoke **Docs Executive** to
run the full pipeline; invoke sub-agents individually when you only need one pass. Sub-agents in this fleet are
`user-invokable: false` — they appear in the dropdown only for direct use but are primarily orchestrated by the
executive.

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

An executive → sub-agent hierarchy for the full testing lifecycle, orchestrated via the [subagent model](#subagent-model). Coverage tooling: **pytest-cov** (Python) and
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

**Playwright Executive** (`playwright-executive.agent.md`) — full execution  
Owns setup and delivery of `@playwright/experimental-ct-react` component testing for `apps/default/client`
(workplan task P27). Confirms P18 jsdom unit tests are passing before authoring Playwright tests,
installs and configures `@playwright/experimental-ct-react` with the Vite CT plugin, then authors
component integration tests covering all client routes and key user flows. Delegates quality review to
Test Review and final commit to GitHub.

---

### Phase executive agents

Each phase executive drives all deliverables for its phase to the milestone gate, then hands off to Review. They are
aware of the full roadmap but will not author deliverables belonging to another phase. They use the
[subagent model](#subagent-model) to delegate specialist work — invoking Plan, Implement, Scaffold, and Review
agents as subagents in sequence, synthesising results, and iterating until the milestone gate is met.

| Agent | Phase | Milestone | Sub-agents |
|-------|-------|-----------|------------|
| **Phase 1 Executive** | Shared Contracts & Vector Store Adapter | M1 — Contracts Stable | Plan, Scaffold Module, Implement, Schema Validator, Schema Migration |
| **Phase 2 Executive** | Communication Infrastructure (MCP + A2A) | M2 — Infrastructure Online | Plan, Implement, Schema Validator |
| **Phase 3 Executive** | Development Agent Infrastructure | M3 — Dev Agent Fleet Live | Plan, Scaffold Agent, Implement, Review Agent |
| **Playwright Executive** | P27 — Playwright CT for `apps/default/client` | P27 complete | Test Executive, Test Review, Implement, Review, GitHub |

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

**Sub-agent produced incomplete or unexpected output**  
Check the active session file for an escalation note under `## <AgentName> Escalation`. If present, follow
the recommended next action. If absent, re-invoke the sub-agent with a more tightly scoped
prompt or elevated posture.

**Agent edited files outside its stated scope (scope bleed)**  
Full-execution agents default to full scope. When delegating with restricted scope, always list
excluded file types explicitly in the delegation prompt. To recover: `git diff` the affected
files, `git checkout HEAD -- <file>` to revert unwanted changes, then re-invoke with exclusions.

---

## Async Terminal Process Handling

_Addresses Issue #33 — guidance for agents running long-lived or async terminal processes._

Agents frequently run commands that take seconds to minutes (Docker builds, `uv sync`, model
downloads, test suites). Incorrectly managing these — blocking when the response is ready, or
fire-and-forgetting when status is needed — is the most common source of stuck or silent agents.
This section gives a decision framework and concrete patterns.

### Decision table — sync vs. interval check-in vs. background

| Situation | Strategy | Why |
|-----------|----------|-----|
| Command completes in < 15 s reliably | **Sync** (wait for output) | No polling overhead; output in one step |
| Command takes 15–120 s with observable status (Docker, uv, pytest) | **Interval check-in** (poll every 15–30 s) | Avoids context-window stall; lets agent act on partial output |
| Command takes > 120 s or is open-ended (model download, server start) | **Background + status request** (`isBackground: true`, then `get_terminal_output`) | Frees the agent context for other work; status fetched on demand |
| Command is one-shot batch with no useful intermediate output | **Sync** — but set an explicit timeout | Output only arrives at end; no benefit from polling |
| Command must be running for a subsequent step (e.g. `docker compose up -d`) | **Background**, verify with a health check before proceeding | Service needs time to bind; health check confirms readiness |

**Rule of thumb**: if you cannot predict the wall-clock time, use background + status request.
If you _can_ predict < 30 s, use sync. The interval check-in middle path is for commands that
print progress lines and where partial output helps diagnose stalls.

### Recommended timeout values by task type

| Task | Sync timeout | Notes |
|------|-------------|-------|
| `pip install` / `uv add` (single package, cached) | 30 s | Network-dependent; 60 s on first cold download |
| `uv sync` (full environment) | 120 s | Resolves + fetches all wheels |
| `pnpm install` (from lockfile) | 90 s | Network-dependent |
| `pytest` (unit tests, no containers) | 120 s | Integration tests: 300 s |
| `pnpm run test` / `vitest` | 60 s | |
| `docker compose build` (cached layers) | 180 s | First build (no cache): 600 s+ — go background |
| `docker compose up -d` (start services) | 30 s | Wait for health check separately |
| `ollama pull <model>` (first download, 4 GB+) | background only | Can take 10–40 min on slow links |
| `ollama pull <model>` (already cached) | 5 s | Instant if weights are local |
| `curl`/`fetch` health check | 5 s | Use `--max-time 5` |

These values match the patterns in [`scripts/healthcheck.sh`](../../scripts/healthcheck.sh), which uses `--max-time 5` for curl checks.

### Code-pattern examples

#### Sync — wait with explicit timeout

```bash
# Run pytest synchronously; timeout after 120 s
timeout 120 uv run pytest tests/ -v 2>&1
echo "exit: $?"
```

#### Interval check-in — poll Docker build progress

```bash
# Start Docker build in background, save PID
docker compose build --progress=plain 2>&1 &
DOCKER_PID=$!
echo "Docker build started, PID=$DOCKER_PID"

# Poll every 30 s; exit when done
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 30
  if ! kill -0 "$DOCKER_PID" 2>/dev/null; then
    echo "Docker build finished after ${i}x30 s"
    break
  fi
  echo "Still building... (${i}x30 s elapsed)"
  # Optional: grep last line of log to show progress
done
```

#### Background + status request — model download

```bash
# Start download in background, redirect output to log
nohup ollama pull qwen2.5-coder:7b > /tmp/ollama-pull.log 2>&1 &
echo "Pull PID=$! — check /tmp/ollama-pull.log for progress"
```

Then in a later step (separate `get_terminal_output` call or terminal read):

```bash
tail -5 /tmp/ollama-pull.log
# Check if model is ready
ollama list | grep qwen2.5-coder
```

#### Service readiness — health check after `docker compose up`

```bash
docker compose up -d
# Poll health endpoint until ready (up to 60 s)
for i in $(seq 1 12); do
  if curl -s --max-time 5 http://localhost:8000/api/v1/heartbeat | grep -q nanoseconds; then
    echo "[PASS] ChromaDB ready"
    break
  fi
  echo "Waiting for ChromaDB ($i/12)..."
  sleep 5
done
```

This is the same pattern used in `scripts/healthcheck.sh`.

### Observability reference — what to parse per tool

Use these patterns to get structured status for each tool without reading all output.

| Tool | Observable output | What to grep / parse |
|------|-------------------|---------------------|
| `docker compose build` | `--progress=plain` lines to stderr | `=> CACHED`, `=> ERROR`, `Successfully built` |
| `docker compose up` | `docker compose ps` JSON | `--format json \| python3 -c "import json,sys; [print(s['Service'],s['State']) for s in json.load(sys.stdin)]"` |
| `docker compose logs` | per-service stdout | `--tail=10 <service>` to limit output |
| `uv sync` / `uv add` | stdout summary line | grep `Resolved N packages` or `error:` |
| `uv run pytest` | exit code + summary line | `PASSED`, `FAILED`, `ERROR`; last line contains totals |
| `pnpm run test` / `vitest` | exit code + summary | `Tests N passed`, `Tests N failed` |
| `pnpm run build` | exit code + turbo summary | `Tasks: N successful` or `ERROR in` |
| `ollama pull` | progress bar lines | `pulling manifest`, `verifying sha256`, `success` — or `tail -1 /tmp/ollama-pull.log` |
| `curl` health check | HTTP status code | `-s -o /dev/null -w "%{http_code}"` — expect `200` |

### Executive agent: delegating long-running status checks

When an executive delegates a sub-task that involves a long-running process, it should:

1. **Pass the PID or log file path** to the sub-agent in the delegation prompt:
   `"The Docker build was started with PID 12345, logging to /tmp/docker-build.log. Check status and report."`

2. **Request a structured status line** rather than raw output:
   `"Report: [RUNNING|DONE|FAILED], elapsed seconds, last log line."`

3. **Set a check-in interval**: for processes > 5 min, instruct the sub-agent to check every
   60 s and write progress to the active session file (`.tmp/<branch>/<date>.md`) under
   `## Build Status` so the executive can read it without blocking on the sub-agent.

4. **Never block the orchestrator context** on a background process. Start it in one step,
   verify readiness with a health check in a second step, proceed with dependent work in a third.

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
- [`scripts/fix_agent_tools.py`](../../scripts/fix_agent_tools.py) — tool ID canonicalisation script

### VS Code documentation

- [Custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents) — agent frontmatter schema, tool aliases, handoffs, `agents` property
- [Custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions) — `.agent.md` file format and `chatagent` fence syntax
- [Subagents](https://code.visualstudio.com/docs/copilot/agents/subagents) — subagent invocation, `user-invokable: false`, parallel execution patterns
