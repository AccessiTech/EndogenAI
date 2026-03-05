# modules/AGENTS.md

> This file narrows the constraints in the root [AGENTS.md](../AGENTS.md).
> It does not contradict any root constraint — it only adds module-development-specific rules.

---

## Programmatic-First

> The **programmatic-first** constraint from [root AGENTS.md](../AGENTS.md#programmatic-first-principle) applies here without exception.

Before scaffolding, validating, or migrating any module interactively, check `scripts/` for an existing scaffold or validation script.
Module boilerplate generation, test scaffolding, and coverage checks are all encoded as scripts — extend them, don't repeat steps by hand.
Escalate scripting gaps to the `Executive Scripter`; automation design (watchers, hooks) to the `Executive Automator`.

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

- [ ] Module runs a **per-module FastAPI + Uvicorn A2A server** (JSON-RPC 2.0, `POST /tasks`) whose handler is
      `a2a_handler.py`; the server is declared as `server.py` in the module `src/` package
- [ ] Module runs a **per-module FastMCP SSE server** (MCP tools, `GET /sse`) whose tool list is `mcp_tools.py`;
      the server is co-hosted in `server.py`
- [ ] All **outbound** cross-module A2A calls use `shared/a2a/python/` `A2AClient` (JSON-RPC 2.0 `tasks/send`);
      no raw `httpx` calls or custom JSON payloads to other modules
- [ ] `agent-card.json` `endpoints.a2a` and `endpoints.mcp` URLs resolve in the local `docker-compose` environment
- [ ] Integration tests cover at least one round-trip A2A task delegation using `A2AClient`

> **Phase 6 note**: The `MCPToA2ABridge` (`infrastructure/adapters/bridge.ts`) and central MCP broker
> (`infrastructure/mcp`) are composed in Phase 8 by the application-host layer, which becomes the single
> orchestrating surface above all module agents. Module servers built in Phase 5 require no refactoring —
> the app host routes to them.

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
