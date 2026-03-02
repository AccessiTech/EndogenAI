# Phase 5 — Cognitive Processing Implementation Handoff

## Phase 5 Implementation Handoff — Pre-Implementation State

**Date**: 2026-03-01 | **Branch**: `feature/phase-5-cognitive-processing` | **Status**: Nothing committed in group-ii-cognitive-processing (all untracked)

---

## Part 1 — What Has Been Built (Current State)

### 6 modules, 133 unit tests passing

All source code already written and quality-gated. No server wiring yet.

| Module | Source files | Test files | Tests | ruff | mypy |
|--------|-------------|-----------|-------|------|------|
| `memory/short-term-memory` | store, novelty, consolidation, search, mcp_tools, a2a_handler, models | test_store, test_novelty, test_consolidation, test_search + integration | 16 | ✅ | ✅ |
| `memory/long-term-memory` | vector_store, graph_store, sql_store, seed_pipeline, retrieval, reconsolidation, mcp_tools, a2a_handler, models | test_vector_store, test_graph_store, test_sql_store, test_seed_pipeline, test_retrieval + integration | 14 | ✅ | ✅ |
| `memory/episodic-memory` | indexer, store, retrieval, timeline, distillation, mcp_tools, a2a_handler, models | test_indexer, test_store, test_retrieval, test_timeline, test_distillation + integration | 16 | ✅ | ✅ |
| `memory/working-memory` | store, loader, consolidation, mcp_tools, a2a_handler, models | test_store, test_loader, test_consolidation, test_mcp_tools | 21 | ✅ | ✅ |
| `affective` | rpe, drive, weighting, store, mcp_tools, a2a_handler, models | test_rpe, test_drive, test_weighting + integration | 37 | ✅ | ✅ |
| `reasoning` | inference, planner, store, mcp_tools, a2a_handler, models | test_inference, test_planner, test_store + integration | 29 | ✅ | ✅ |

### What each module has
Every module has: README.md, `agent-card.json`, pyproject.toml, `src/`, `tests/`, `py.typed`, uv.lock, config JSONs, .pytest_cache (from previous test runs).

`pyrightconfig.json` present: STM ✅ LTM ✅ Episodic ✅ WM ✅ — **Affective ❌ Reasoning ❌**

---

## Part 2 — What Needs to Be Built (Implementation Work)

### Step 1 — `shared/a2a/python/` shared client package

**New directory**: `shared/a2a/python/`  
**Pattern**: Mirror python layout — own pyproject.toml, `uv`-based env, `ruff` + `mypy`, `pytest`.

Key deliverables:
- `src/endogenai_a2a/client.py` — `A2AClient`: async httpx wrapper, speaks JSON-RPC 2.0 (`tasks/send`, `tasks/get`), accepts target URL + timeout config
- `src/endogenai_a2a/models.py` — Pydantic models: `A2ARequest`, `A2AResponse`, `A2ATask`, `A2AMessage` (mirrors a2a-task.schema.json and `a2a-message.schema.json` — schemas already exist, schemas-first gate satisfied)
- `src/endogenai_a2a/exceptions.py` — `A2AError`, `A2ATaskNotFound`, `A2AProtocolError`
- Unit tests with `httpx.MockTransport`
- `py.typed`, README.md

**Note**: Modules may include a module-local `_a2a_client.py` override if they need specialised behaviour — the shared package is the default, not a mandate.

---

### Step 2 — Per-module `server.py` (all 6 modules)

Each module gains a `server.py` in its `src/<package>/` directory and the following new deps in pyproject.toml:

```
fastapi>=0.115
uvicorn[standard]>=0.30
mcp[cli]>=1.6   # FastMCP SSE
```

`server.py` template (single process, two interfaces):
- `POST /` — JSON-RPC 2.0 dispatcher → `a2a_handler.py` `handle(task_type, payload)`
- `GET /.well-known/agent-card.json` — serves `agent-card.json`
- `GET /sse` — FastMCP SSE endpoint exposing tools from `mcp_tools.py`
- Startup event registers module with `CHROMADB_URL` / `REDIS_URL` env vars; graceful shutdown

Each module also gets a pyproject.toml `[project.scripts]` entry:
```
serve = "<package>.server:main"
```

---

### Step 3 — Fix 3 protocol-violation files

Replace raw `httpx` calls with `A2AClient.send_task()` (JSON-RPC 2.0):

| File | Current violation | Fix |
|------|------------------|-----|
| working-memory/consolidation.py | `httpx.AsyncClient().post("http://localhost:8052", json={"task_type":...})` | `A2AClient(url).send_task("consolidate_item", payload)` |
| episodic-memory/distillation.py | `httpx.AsyncClient().post("http://localhost:8053", json={"task_type":...})` | `A2AClient(url).send_task("write_item", payload)` |
| affective/weighting.py | `httpx.AsyncClient().post("http://localhost:8051", json={"task_type":...})` | `A2AClient(url).send_task("boost_importance", payload)` |

Existing unit tests for these three files will need mock updates (mock `A2AClient.send_task` instead of `httpx.AsyncClient.post`).

---

### Step 4 — Port renumbering (4 memory modules)

Renumber from ad-hoc 8051–8054 → coherent Group II scheme 8201–8204 to match affective (8205) and reasoning (8206):

| Module | Old A2A | New A2A | Old MCP | New MCP |
|--------|---------|---------|---------|---------|
| working-memory | 8051 | **8201** | 8151 | **8301** |
| short-term-memory | 8052 | **8202** | 8152 | **8302** |
| long-term-memory | 8053 | **8203** | 8153 | **8303** |
| episodic-memory | 8054 | **8204** | 8154 | **8304** |

Files touched: 4 × `agent-card.json`; default URL constants in `consolidation.py`, `distillation.py`, `weighting.py`; `server.py` default port env var fallbacks.

---

### Step 5 — Fix all 6 `agent-card.json` files

Add two missing fields and update ports for the 4 memory modules:

```json
"wellKnown": "/.well-known/agent-card.json",
"schema": "shared/types/memory-item.schema.json"   // memory modules
"schema": "shared/types/reward-signal.schema.json" // affective
```
(Reasoning `agent-card.json` gets `wellKnown` only — no canonical schema equivalent yet.)

---

### Step 6 — Missing `pyrightconfig.json` (2 modules)

Copy from any memory module. Affective and Reasoning both missing it.

---

### Step 7 — `pytest.mark.integration` registration (4 modules)

Add markers entry to `[tool.pytest.ini_options]` in STM, LTM, Episodic, WM pyproject.toml:
```toml
markers = ["integration: marks tests requiring live services (Redis, ChromaDB, Ollama)"]
```
Affective ✅ and Reasoning ✅ already have this.

---

### Step 8 — docker-compose.yml — 6 new service entries

Add under a modules profile so they are opt-in:
```yaml
docker compose --profile modules up -d
```

Each service entry:
- Builds from module directory with a `Dockerfile` (Python 3.11-slim + `uv`)
- Or runs `uv run uvicorn <package>.server:app` directly in a `python:3.11-slim` image
- `depends_on: chromadb, redis, ollama`
- Two exposed ports (A2A + MCP/SSE)
- `healthcheck` on `GET /.well-known/agent-card.json`
- Environment variables: `CHROMADB_URL`, `REDIS_URL`, `OLLAMA_URL`, `INFERENCE_MODEL`

Each module also needs a `Dockerfile` (6 new files).

---

### Step 9 — Integration tests for A2A round-trips

Each module already has an `test_integration_*.py`. These need expanding to cover:
- Full `A2AClient.send_task()` round-trip against a live `server.py` (started in-process with `uvicorn.Server` / `TestClient`)
- `pytest.mark.integration` decorator on all live-service tests

---

### Step 10 — Quality gate (all must pass before handoff to Review)

```bash
# Per module (×6)
cd <module> && uv sync && uv run ruff check . && uv run mypy src/ && uv run pytest -m "not integration"

# Shared A2A package
cd shared/a2a/python && uv sync && uv run ruff check . && uv run mypy src/ && uv run pytest

# Full repo TS checks
pnpm run lint && pnpm run typecheck
```

---

### Step 11 — AGENTS.md update (post-implementation)

Add `shared/a2a/python/` to the package boundary table and note that it is the approved outbound A2A call mechanism for all Python modules. This happens after Step 1 lands.

---

## Part 3 — File Change Summary

| Location | Action | Step |
|----------|--------|------|
| `shared/a2a/python/` | **Create** — new package | 1 |
| `<6 modules>/src/<pkg>/server.py` | **Create** — FastAPI + FastMCP SSE | 2 |
| `<6 modules>/pyproject.toml` | **Edit** — add fastapi/uvicorn/mcp deps + scripts entry | 2 |
| `<6 modules>/Dockerfile` | **Create** | 8 |
| docker-compose.yml | **Edit** — add 6 service entries + modules profile | 8 |
| `working-memory/consolidation.py` | **Edit** — A2AClient refactor | 3 |
| `episodic-memory/distillation.py` | **Edit** — A2AClient refactor | 3 |
| `affective/weighting.py` | **Edit** — A2AClient refactor | 3 |
| 3 unit test files for above | **Edit** — mock target update | 3 |
| 4 memory `agent-card.json` | **Edit** — port renumber + wellKnown + schema | 4+5 |
| `affective/agent-card.json` | **Edit** — wellKnown + schema | 5 |
| `reasoning/agent-card.json` | **Edit** — wellKnown | 5 |
| `affective/pyrightconfig.json` | **Create** | 6 |
| `reasoning/pyrightconfig.json` | **Create** | 6 |
| 4 memory pyproject.toml | **Edit** — add markers | 7 |
| 6 `test_integration_*.py` | **Edit** — A2AClient round-trip tests | 9 |
| AGENTS.md | **Edit** — document shared/a2a/python | 11 |

**Total new files**: `shared/a2a/python/` package (~8 files) + 6 `server.py` + 6 `Dockerfile` + 2 `pyrightconfig.json` = **~22 new files**  
**Total edited files**: 6 pyproject.toml + 6 agent-card.json + 3 violation refactors + 3 test updates + docker-compose.yml + AGENTS.md = **~25 edits**

---

## Part 4 — No Open Decisions

All architecture decisions are resolved and documented. Implementation can proceed in the sequence above. Ready to start on your go-ahead — Step 1 (`shared/a2a/python/`) is the logical first commit.