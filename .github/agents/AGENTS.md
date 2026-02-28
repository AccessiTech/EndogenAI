# .github/agents/AGENTS.md

> This file narrows the constraints in the root [AGENTS.md](../../AGENTS.md).
> It does not contradict any root constraint — it only adds agent-development-specific rules.

---

## Purpose

This file governs the authoring, review, and maintenance of VS Code Copilot custom agents
(`.agent.md` files) in this directory. Every agent in the fleet must comply with both the
root `AGENTS.md` and the rules below.

---

## Frontmatter Schema

Agent files begin with a YAML front-matter block. The allowed fields are:

```yaml
---
name: <Display Name>            # Required. Shown in the Copilot agents dropdown. Must be unique.
description: <One-line summary> # Required. ≤ 200 characters.
argument-hint: <hint>           # Optional. Placeholder shown in the chat input box.
tools:                          # Required. Minimal subset — see posture table below.
  - <tool-id>
handoffs:                       # Required. At least one handoff per agent.
  - label: <Button text>
    agent: <Target agent name>  # Must match the `name` field of the target exactly.
    prompt: <Pre-filled prompt>
    send: false
---
```

**Validation rules:**
- `name` must be unique across all `.agent.md` files in this directory.
- `description` must be one sentence, ≤ 200 characters.
- Every `handoffs[].agent` value must match an existing agent's `name` field exactly.
- `tools` must be the **minimum** set required for the agent's posture (see below).

---

## Tool Selection by Posture

Choose the minimum posture that fulfils the agent's stated purpose. Do not add tools speculatively.

| Posture | Permitted tool IDs |
|---------|-------------------|
| **Read-only** (review, plan, audit) | `codebase`, `problems`, `search`, `usages`, `changes` |
| **Read + create** (scaffold) | adds `editFiles`, `edit`, `fetch` |
| **Full execution** (implement, debug, executive) | adds `runInTerminal`, `getTerminalOutput`, `runTests`, `terminalLastCommand` |

If an executive or implement agent is granted `execute/runInTerminal`, it inherits the Python
`uv run`-only rule and the TypeScript `pnpm`-only rule from root `AGENTS.md`. It also inherits
the **Writing Files from the Terminal Tool** safe-pattern rules from root `AGENTS.md` —
never use heredocs for files > 30 lines; use small `printf >>` appends or a `/tmp/` Python script.

---

## Handoff Graph Patterns

Every agent must hand off to at least one downstream agent. Standard patterns:

```
Action agent  →  Review  →  GitHub
Scaffold agent  →  Review  →  GitHub
Executive  →  sub-agents  →  Review  →  GitHub
```

- An executive agent orchestrates its fleet and must hand off to Review before committing.
- Sub-agents should hand off back to their executive or directly to Review/GitHub.
- Read-only agents (review, plan, audit) hand off to action agents or GitHub.
- The `send: false` default is strongly preferred — avoid auto-submitting prompts.

---

## Mandatory Script Coupling

Every agent that **performs an auditable action** (generates, validates, scans, or modifies files)
must be coupled to a backing Python script in `scripts/`:

| Agent action | Required backing script |
|-------------|------------------------|
| Generates documentation stubs | `scripts/docs/scaffold_doc.py` |
| Audits for missing docs | `scripts/docs/scan_missing_docs.py` |
| Generates test stubs | `scripts/testing/scaffold_tests.py` |
| Scans coverage gaps | `scripts/testing/scan_coverage_gaps.py` |
| Validates schemas | `scripts/schema/validate_all_schemas.py` |

The agent body must reference the script by path and instruct the agent to invoke it via `uv run`.
Read-only audit agents (review, plan) are exempt — they do not modify files.

---

## Body Structure Requirements

Every agent body must follow this structure:

1. **Bold role statement**: `You are the **X agent** for the EndogenAI project.`
2. **Endogenous sources section**: list every file the agent must read before acting, with relative links.
3. **Workflow or checklist**: numbered steps or a role-specific checklist.
4. **Guardrails section**: explicit list of what the agent must NOT do.

Each rule in the body must trace to root `AGENTS.md`, `CONTRIBUTING.md`, or an existing agent.
If genuinely new, include an inline rationale comment.

---

## Naming Conventions

| Agent type | File name pattern | `name` field |
|-----------|------------------|-------------|
| Phase executive | `phase-N-executive.agent.md` | `Phase N Executive` |
| Fleet executive | `<area>-executive.agent.md` | `<Area> Executive` |
| Fleet sub-agent | `<area>-<role>.agent.md` | `<Area> <Role>` |
| Workflow agent | `<verb>.agent.md` or `<noun>.agent.md` | `<Verb>` or `<Noun>` |

Use lowercase kebab-case for filenames. Match the pattern of existing files exactly.

---

## Verification Gate

Before committing a new or modified agent file:

```bash
# Check for name uniqueness
grep -h "^name:" .github/agents/*.agent.md | sort | uniq -d

# Verify all handoff targets resolve (manual: every `agent:` field must match a `name:`)

# Pre-commit hooks (frontmatter/formatting)
pre-commit run --all-files
```
