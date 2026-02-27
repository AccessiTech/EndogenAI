# docs/AGENTS.md

> This file narrows the constraints in the root [AGENTS.md](../AGENTS.md).
> It does not contradict any root constraint — it only adds documentation-specific rules.

---

## Purpose

This file governs all AI coding agent activity inside the `docs/` directory:
architecture references, protocol specs, guides, and the workplan.

---

## Target Audiences

Documentation in `docs/` is written for four audiences:

| Audience | Scope |
|----------|-------|
| **Module developers** | Guides in `docs/guides/` — implementation patterns, module scaffolding, toolchain usage |
| **Protocol integrators** | Specs in `docs/protocols/` — MCP and A2A message formats, endpoint contracts |
| **Project contributors** | Top-level architecture and workplan — onboarding, phase gates, milestone definitions |
| **AI coding agents** | `AGENTS.md` hierarchy — instructions that narrow root constraints per directory |

---

## Document Structure Requirements

Every document in `docs/` must include:

1. **H1 title** — one per document, matching the file subject
2. **Opening overview** — a short paragraph (≤ 5 sentences) stating purpose and audience
3. **Required sections** — determined by document type:

| Type | Required sections |
|------|------------------|
| Architecture doc | Overview, Component Map, Signal Flow, Data Flow, Key Decisions |
| Guide | Prerequisites, Step-by-step instructions, Verification, Troubleshooting |
| Protocol spec | Purpose, Message Format, Endpoint Reference, Error Handling, Examples |
| Workplan | Goal statement, Checklist items, Verification block, Deliverables |

4. **Closing references** — link to related docs, schemas, or module READMEs

---

## Frontmatter Rules

`docs/` files are **plain Markdown** — no YAML frontmatter block is required or expected.

Files under `resources/` (not `docs/`) require frontmatter. See
[`scripts/validate_frontmatter.py`](../scripts/validate_frontmatter.py) for the required fields
(`id`, `version`, `status`, `maps-to-modules`) and validation logic.

---

## Link Conventions

- **Relative links always**: use `../shared/schemas/foo.schema.json`, not absolute paths or bare filenames.
- **No bare URLs** in body text — always use `[descriptive text](url)`.
- **Cross-references to schemas**: link directly to the `.schema.json` file in `shared/schemas/` or `shared/types/`.
- **Cross-references to code**: link to the source file, not the compiled output under `dist/`.
- **Anchor links**: use lowercase with hyphens matching the heading text (GitHub-flavoured Markdown rules).
- **External specification links**: include version or commit hash in the link text where stability matters
  (e.g. `[A2A spec v0.2.1](https://github.com/a2aproject/A2A/tree/v0.2.1)`).

---

## Authoring Constraints for Agents

- **Endogenous-first**: derive all descriptions, module names, and API references from existing schemas and
  implementation files — do not invent names.
- **No implementation detail in `docs/`**: architecture docs describe *what* and *why*; implementation
  lives in code and module READMEs.
- **Workplan edits are minimum-diff**: when updating `docs/Workplan.md`, change only checklist state
  (`[ ]` → `[x]`) and add new open questions — do not restructure headings or reorder phases.
- **Protocol specs must match implementation**: before editing `docs/protocols/`, confirm the actual
  behaviour in `infrastructure/mcp/` or `infrastructure/a2a/`. Flag divergences rather than silently
  updating the spec to match a potentially broken implementation.
- **Guides must be runnable**: every shell command in a guide must be copy-pasteable and exit 0 on a
  clean local environment (following the bootstrap in root `AGENTS.md`).

---

## Verification Gate

```bash
# Frontmatter on resource files only (docs/ files are exempt)
pre-commit run validate-frontmatter --all-files

# Markdown links — visually verify using VS Code Markdown preview or a link-checker tool
```
