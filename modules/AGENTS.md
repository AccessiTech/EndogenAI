# modules/AGENTS.md

> This file narrows the constraints in the root [AGENTS.md](../AGENTS.md).
> It does not contradict any root constraint — it only adds module-development-specific rules.

---

## Purpose

This file governs all AI coding agent activity inside the `modules/` directory.
Cognitive modules are the core computational units of the EndogenAI system, each
corresponding to a brain-region analogy defined in `resources/neuroanatomy/`.

---

## Module Groups

| Group | Directory | Analogy | Phase |
|-------|-----------|---------|-------|
| **Group I** | `group-i-signal-processing/` | Sensory boundary, attention, perception | Phase 4 |
| **Group II** | `group-ii-cognitive-processing/` | Memory, affect, reasoning | Phase 5 |
| **Group III** | `group-iii-executive-output/` | Decision, planning, action, language generation | Phase 6 |
| **Group IV** | `group-iv-adaptive-systems/` | Reward, meta-learning, self-monitoring | Phase 7 |

**Per-group constraints:**
- Group I modules are Python-only (ML/signal processing).
- Group II memory modules depend on `shared/vector-store/` adapters — always wire via the adapter interface,
  never call ChromaDB or Qdrant SDKs directly.
- Group III modules may have TypeScript surfaces for MCP/A2A coordination but core logic is Python.
- Group IV modules must not call external reward APIs — all reward signals flow through
  `shared/types/reward-signal.schema.json`.

---

## Mandatory Module Contract

Every module directory must contain:

| File | Required | Description |
|------|----------|-------------|
| `README.md` | ✅ | Purpose, interface, configuration, and deployment instructions |
| `agent-card.json` | ✅ | Exposed at `/.well-known/agent-card.json` — A2A agent identity and capabilities |
| `pyproject.toml` or `package.json` | ✅ | Dependency manifest for the module's primary language |
| `src/` | ✅ | All source code |
| `tests/` | ✅ | Unit and integration tests |

### `agent-card.json` Required Fields

```json
{
  "name": "<module-name>",
  "description": "<one-sentence purpose>",
  "version": "<semver>",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:<port>",
    "mcp": "http://localhost:<port>"
  }
}
```

Derive the `name` and `description` from the corresponding `resources/neuroanatomy/` stub and
`resources/static/knowledge/brain-structure.md`. Do not invent descriptions.

---

## MCP + A2A Wiring Checklist

Before marking a module as complete, verify:

- [ ] Module registers its capabilities with the MCP broker (`infrastructure/mcp/`)
- [ ] Module exposes an A2A task endpoint handled by the A2A server (`infrastructure/a2a/`)
- [ ] All cross-module communication routes through `infrastructure/adapters/bridge.ts` — no direct HTTP calls
      between modules
- [ ] `agent-card.json` endpoint URLs resolve in the local `docker-compose` environment
- [ ] Integration tests cover at least one round-trip MCP context exchange and one A2A task delegation

---

## Python Module Conventions

Follows root `AGENTS.md` Python tooling rules, plus:

- **`uv run` only** — never invoke Python directly or via `.venv/bin/`
- **`uv sync`** before running tests in a module for the first time in a session
- **`ruff check .` + `mypy src/`** must pass before committing
- **LiteLLM for all inference** — no direct `openai`, `anthropic`, or `ollama` SDK calls
- **Vector store access via adapter** — import from `endogenai_vector_store`, never from `chromadb` directly

---

## Cross-Group Dependency Rule

A module in Group N may depend on contracts (JSON Schemas) from `shared/schemas/` or `shared/types/`.
It must **not** import source code from a module in a different group.
Cross-group data exchange happens exclusively via MCP context or A2A task messages.

If a new shared contract is needed, land the JSON Schema in `shared/schemas/` first (schemas-first gate),
then wire the consumer module.

---

## Verification Gate

```bash
# From the module directory
uv run ruff check .
uv run mypy src/
uv run pytest

# From repo root — integration smoke test
pnpm run lint && pnpm run typecheck
```
