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
  a2a/
    python/         # Approved outbound A2A client package (endogenai-a2a) — JSON-RPC 2.0

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
cd shared/a2a/python && uv sync && cd -

# 4. Verify
pnpm run lint && pnpm run typecheck
cd shared/vector-store/python && uv run ruff check . && uv run mypy src/
cd shared/a2a/python && uv run ruff check . && uv run mypy src/
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

## Agent Communication

### `.tmp/` — Per-session cross-agent scratchpad

`.tmp/` at the workspace root is the **designated scratchpad folder** for cross-agent context
preservation. It is gitignored and never committed.

**Folder structure:**
```
.tmp/
  <branch-slug>/          # one folder per branch
    _index.md             # one-line stubs of all closed sessions on this branch
    <YYYY-MM-DD>.md       # one file per session day — the active scratchpad
```

**`<branch-slug>`** = branch name with `/` replaced by `-`
(e.g. `docs/test-upgrade-workplan` → `docs-test-upgrade-workplan`)

**Active scratchpad path** = `.tmp/<branch-slug>/<YYYY-MM-DD>.md`

Rules:
- Each delegated agent **appends** findings under a named heading: `## <Phase> Results` or
  `## <Task> Output`. Never overwrite another agent's section.
- The executive **reads today's session file first** before delegating to avoid re-discovering
  context another agent already gathered. Check `_index.md` for a one-line stub of prior sessions.
- At session end, the executive writes a `## Session Summary` section so the next session starts
  with an orientation point rather than a cold start.
- Use the active session file for inter-agent handoff notes, gap reports, and aggregated sub-agent results.
- Each new session day gets a fresh file — run `python scripts/prune_scratchpad.py --init` at
  session start to create it. Prior-session context is available as one-line stubs in `_index.md`.

### Size guard and archive convention

| Situation | Action |
|-----------|--------|
| `.tmp.md` < 200 lines | No action needed |
| `.tmp.md` ≥ 200 lines | Invoke Scratchpad Janitor or run `python scripts/prune_scratchpad.py` |
| Session end / PR close | Write `## Session Summary`, then run `python scripts/prune_scratchpad.py --force` (also updates `_index.md`) |
| New session day | Run `python scripts/prune_scratchpad.py --init` to create today's file |
| New branch start | Re-init: `python scripts/prune_scratchpad.py --init` on the new branch |

> **Scratchpad pruning — do not automate.** Running `scripts/prune_scratchpad.py`
> (or any automated janitor pass) costs more tokens in orchestrator context than
> it saves in file size. Prune manually only when a session file exceeds ~500 lines.

**Archive convention:** completed sections may be compressed to one-line stubs:
```
## <Heading> (archived <YYYY-MM-DD> — <first-content-line>)
```
The stub preserves date and a content hint for traceability without consuming tokens.

### Scope-narrowing in delegations

When delegating with a restricted scope, **state exclusions explicitly** in the delegation prompt.
Executive agents default to full scope; they need explicit constraints to narrow it.

Good examples:
> "Edit `.md` files and `.tmp.md` only — do not modify source code, config, test files, or
> `pyproject.toml` / `package.json`."

> "Read-only pass — do not create or edit any files."

Without explicit exclusions, a full-execution agent will follow its toolset and modify whatever
it finds relevant.

### Insufficient-posture escalation

When a sub-agent encounters a task that exceeds its posture or context capacity, it must **not
silently fail or stop**. Instead it must:

1. Write a structured summary to `.tmp.md` under `## <AgentName> Escalation`:
   - Current state (what was completed)
   - Blocking issue (what requires elevated posture or specialist knowledge)
   - Recommended next action (which agent to invoke, or whether a new specialist should be created)
   - Step-by-step instructions for the receiving agent or executive
2. Hand off to the delegating executive with the "Back to [Executive]" handoff button.

The executive reads the escalation note, decides whether to re-delegate to a different agent,
spin up a new specialist agent, or handle the block directly.

### On-demand specialist agent creation

Create a new specialist `.agent.md` when a task domain is deep enough to warrant reuse.
Indicators:
- The task has its own toolchain commands not covered by existing executive scope
- The task is likely to recur (across phases, audit cycles, or PR workflows)
- Forcing a generalist executive to handle it inline would exceed its stated scope

**Process:**
1. Author the `.agent.md` file FIRST (it is the documentation of the decision)
2. Commit it to the branch before invoking it for the first time
3. Add the new agent to the invoking executive's `agents:` list and a handoff button

### Clarifying questions before proceeding

For any task involving trade-offs, irreversible changes, or ambiguous scope, **ask the user a
clarifying question before taking action**. This is especially important when:
- Multiple valid implementation approaches exist with different cost/quality trade-offs
- The scope of a delegation could be interpreted narrowly or broadly
- A decision will affect multiple downstream agents or phases

Asking one well-framed question costs far less context than completing work that needs revision.

### Context window efficiency via delegation and `.tmp/`

Delegation + the active session file together let an orchestrator's context window go much further:
- The orchestrator delegates bounded sub-tasks to specialists with short, focused context windows
- Specialists write structured output to the active session file rather than returning it inline
- The orchestrator reads the active session file summaries rather than full sub-agent transcripts
- Sub-delegation (specialist delegates to sub-specialist) amplifies this effect further

Prefer deep delegation trees over wide inline execution for large tasks.

### Delegation model — inline over handoff

The **preferred delegation pattern** is inline delegation via `@agentname` within the
orchestrator's context window. This keeps the orchestrator's context intact and avoids the
cost of restarting it after each sub-agent completes.

**Inline delegation** (preferred):
```
Orchestrator (persistent context)
  @Phase5Executive → reports back inline
  reads .tmp/<branch>/<date>.md for summary
  @ReviewAgent → reports back inline
  @GitHub → commit confirmed
```

**Handoff buttons** (session boundary events only):
- Session start → Scratchpad Janitor (if file is stale/large)
- Session end → Review → GitHub
- Escalation → specialist with relevant posture

When delegating, always include in the prompt: **"Sub-delegate where appropriate before returning
results. Write a `## <Task> Results` summary to `.tmp/<branch>/<date>.md` for persistence."**

---

## Writing Files from the Terminal Tool

The `run_in_terminal` tool has an **implicit input character limit**. Shell heredocs that embed
large file content inside a single command string will be silently truncated — the tool emits
`"The tool simplified the command to..."` and the output file is incomplete or empty.

**Never use `cat << 'EOF' ... EOF` or multi-line Python heredoc strings for files longer than ~30 lines.**

### Safe patterns for writing files

#### For small files (< 30 lines) — direct `printf`

```bash
printf '# Title\n\nContent.\n' > /path/to/file.md
```

#### For medium files (30–150 lines) — multiple `printf >>` appends

Keep each terminal call to **≤ 20 lines of content**. Use `>` for the first call, `>>` for all
subsequent calls:

```bash
printf '# Title\n\nFirst section.\n' > /path/to/file.md
printf '\n## Second Section\n\nMore content.\n' >> /path/to/file.md
# repeat until complete — verify with: wc -l /path/to/file.md
```

#### For large files (150+ lines) — Python tmpfile script

Build a Python script at `/tmp/` with small appends, then execute it:

```bash
printf 'import pathlib\n' > /tmp/write_file.py
printf 'p = pathlib.Path("/repo/target.md")\n' >> /tmp/write_file.py
printf 'lines = []\n' >> /tmp/write_file.py
printf 'lines.append("# Title\\n")\n' >> /tmp/write_file.py
printf 'lines.append("Content.\\n")\n' >> /tmp/write_file.py
printf 'p.write_text("".join(lines))\n' >> /tmp/write_file.py
uv run python /tmp/write_file.py
```

For patching an **existing** file, prefer the `edit` tool —
it has no size limit and is the safest option for non-creation edits.

### Rule of thumb

> If the terminal command is longer than a screen, split it into multiple calls.
> Verify each file after creation with `wc -l` and `head`/`tail`.

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

All `.agent.md` files in [`.github/agents/`](.github/agents/) appear in the
Copilot chat agents dropdown automatically.

| Agent | Posture | Trigger |
|-------|---------|---------|| **Executive Orchestrator** | full tools | Cold-start session orientation and cross-cutting request triage — reads `.tmp.md` and workplan, then delegates to the correct phase executive or specialist || **Plan** | read-only | Start of any new task — survey workplan + codebase, produce a scoped plan |
| **Scaffold Module** | read + create | Adding a new cognitive module — derives structure from endogenous knowledge |
| **Scaffold Agent** | read + create | Adding a new VS Code Copilot agent to the development workflow |
| **Implement** | full tools | Execute an approved plan; enforces all AGENTS.md constraints |
| **Review** | read-only | Pre-commit gate — verify changes against constraints and module contracts |
| **GitHub** | terminal + read | Git/PR workflows — branching, committing, opening and merging PRs |
| **Executive Debugger** | full tools | Diagnose and fix runtime or test failures |
| **Executive Planner** | read + edit | Reconcile `docs/Workplan.md` against codebase; recommend next agent |
| **Agent Scaffold Executive** | full tools | Orchestrate new agent creation — brief Scaffold Agent, validate, update catalog |
| **Review Agent** | read-only | Specialist review of `.agent.md` and `AGENTS.md` files against authoring rules |
| **Update Agent** | read + create | Update existing agent files for compliance with current authoring rules |
| **Scratchpad Janitor** | read + create | Prune `.tmp.md` when it exceeds 200 lines — compress completed sections to archive stubs, preserve live context |
| **Govern Agent** | read-only | Fleet-wide compliance audit of `.github/agents/` against all guardrails |
| **Docs Executive Researcher** | read + create | Pre-planning; invoked by Phase Executives to research codebase and docs state, write a phase-scoped research brief to `docs/research/`, and hand back to the invoking executive before workplan authoring |
| **Phase-1 Executive** | full tools | Phase-1 specific orchestration and delivery tasks |
| **Phase-2 Executive** | full tools | Phase-2 specific orchestration and delivery tasks |
| **Phase-3 Executive** | full tools | Phase-3 specific orchestration and delivery tasks |
| **Phase-4 Executive** | full tools | Phase-4 specific orchestration and delivery tasks |
| **Phase 5 Executive** | full tools | Phase 5 top-level orchestration — sequences Memory → Motivation → Reasoning domain executives |
| **Phase 5 Memory Executive** | full tools | Phase 5 memory stack delivery — working, short-term, long-term, and episodic memory (§§5.1–5.4) |
| **Phase 5 Motivation Executive** | full tools | Phase 5 affective/motivational layer delivery — reward signals, emotional weighting, urgency scoring (§5.5) |
| **Phase 5 Reasoning Executive** | full tools | Phase 5 reasoning layer delivery — DSPy inference, causal planning, LiteLLM-routed LLM calls (§5.6) |
| **Phase 6 Executive** | full tools | Phase 6 top-level orchestration — sequences executive-agent → agent-runtime → motor-output (§§6.1–6.3) to M6 milestone |
| **Playwright Executive** | full tools | P27 Playwright CT delivery — set up `@playwright/experimental-ct-react` and author component integration tests for `apps/default/client` |
| **Test Executive** | full tools | Orchestrate the full testing lifecycle — run coverage scans, delegate to Test Scaffold and Test Review sub-agents, ensure all thresholds met before handoff |
| **Test Coverage** | full execution | Identify untested code paths, map coverage gaps to module contracts, and enforce per-module 80% coverage thresholds |
| **Test Review** | read-only | Audit test quality — meaningful assertions, Testcontainers hygiene, mocking discipline; produces PASS / WARN / FAIL report |
| **Test Scaffold** | read + create | Generate vitest and pytest test stubs from actual source file interfaces — no invented signatures; always `--dry-run` first |
| **Schema Executive** | full tools | Orchestrate schema authoring and safe migration — enforces schemas-first constraint before any implementation agent proceeds |
| **Schema Validator** | read + execute | Validate all JSON Schema files in `shared/` and run `buf lint` against Protobuf schemas |
| **Schema Migration** | read + create | Guide safe backwards-compatible schema evolution — inventory downstream consumers, assess breaking-change risk, record migration notes |
| **Phase 7 Executive** | full tools | Phase 7 top-level orchestration — sequences metacognition → learning-adaptation → integration in strict gate order to M7 milestone |
| **Phase 7 Metacognition Executive** | full tools | §7.2 Metacognition & Monitoring Layer — OTel setup, evaluator, Prometheus metrics, corrective A2A trigger |
| **Phase 7 Learning Executive** | full tools | §7.1 Learning & Adaptation Layer — BrainEnv, PPO trainer, ReplayBuffer, HabitManager |
| **Phase 7 Integration Executive** | full tools | §7.3 Phase 7 end-to-end integration tests and M7 milestone declaration |
| **Phase 8 Executive** | full tools | Phase 8 top-level orchestration — gate-sequences auth, gateway, registry, browser client, and observability to M8 milestone |
| **Phase 8 MCP OAuth Executive** | full tools | §8.2 MCP OAuth 2.1 auth layer — PKCE flow, JWT tokens, well-known endpoints, auth middleware |
| **Phase 8 Hono Gateway Executive** | full tools | §8.1 Hono API Gateway — MCP Streamable HTTP client, SSE relay, CORS, static serving, integration tests |
| **Phase 8 Browser Client Executive** | full tools | §8.3 Browser client — React + Vite, PKCE auth, `useSSEStream` hook, Chat tab, Internals tab, WCAG 2.1 AA |
| **Phase 8 Observability Executive** | full tools | §8.4 Gateway OTel instrumentation, pino logging, Prometheus Blackbox probes, Grafana dashboards |
| **Phase 8 Resource Registry Executive** | full tools | §8.5 `brain://` URI resource registry, MCP `resources/list` and `resources/read` handlers, access-control docs |

Typical workflow: **Plan → (approve) → Implement → (complete) → Review → commit**.

For a new module: **Scaffold Module → (approve scaffold) → Implement → Review → commit**.

For a new agent: **Scaffold Agent → (approve scaffold) → Review → commit**.

### Gate conventions

Tests and documentation are **mandatory gates**, not optional follow-up steps:

- **Before committing implementation**: tests must pass and coverage must meet the 80% threshold.
  Run `uv run pytest --cov=src --cov-fail-under=80` (Python) or `pnpm run test -- --coverage`
  (TypeScript) before opening a PR.
- **Before committing any implementation change**: documentation must be updated in the same
  commit or the immediately following one. The Docs Executive runs a completeness check as a
  gate before any phase milestone is declared complete.
- **Before merging**: the Review Agent must pass all `.agent.md` files changed in the PR. Run
  `grep -h "^name:" .github/agents/*.agent.md | sort | uniq -d` to confirm name uniqueness.

---

## Key References

| Resource | Purpose |
|----------|---------|
| [`docs/Workplan.md`](docs/Workplan.md) | Phase-by-phase implementation roadmap |
| [`docs/architecture.md`](docs/architecture.md) | Full architectural overview and signal-flow diagrams |
| [`docs/guides/agents.md`](docs/guides/agents.md) | Human-readable agent fleet guide: what each agent does, postures, typical workflows |
| [`docs/guides/adding-a-module.md`](docs/guides/adding-a-module.md) | Step-by-step module scaffolding guide |
| [`docs/guides/toolchain.md`](docs/guides/toolchain.md) | Full toolchain command reference |
| [`shared/vector-store/README.md`](shared/vector-store/README.md) | Vector store adapter pattern and collection registry |
| [`shared/a2a/python/README.md`](shared/a2a/python/README.md) | Approved outbound A2A client (`endogenai-a2a`) — JSON-RPC 2.0 `send_task` / `get_task` |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branch naming, PR guidelines, and coding standards |
