# Short-Term Memory

Session-scoped transient memory store for the EndogenAI cognitive processing stack.

## Purpose

The Short-Term Memory (STM) module implements a hippocampal-inspired, session-scoped buffer that:

- Stores recent experience items for the duration of a session, governed by configurable TTL.
- Applies **novelty detection** (Dentate Gyrus analogue) before every write — near-duplicates are merged rather than duplicated.
- Runs a **consolidation pipeline** (SCAN→SCORE→GATE→EMBED→PRUNE) on session expiry, promoting important items into `brain.long-term-memory` or `brain.episodic-memory`.
- Provides **semantic search** over the current session via `brain.short-term-memory`.

## Interface

### MCP Tools

| Tool | Input | Output |
|------|-------|--------|
| `stm.write` | `{item: MemoryItem}` | `{item_id: str}` |
| `stm.search` | `{session_id, query, top_k}` | `{items: list[MemoryItem]}` |
| `stm.expire_session` | `{session_id}` | `ConsolidationReport` |
| `stm.get_by_session` | `{session_id}` | `{items: list[MemoryItem]}` |

### A2A Task Types

| Task | Input | Output |
|------|-------|--------|
| `write_record` | `{item: MemoryItem}` | `{item_id: str}` |
| `search_session` | `{session_id, query, top_k}` | `{items: list[MemoryItem]}` |
| `consolidate_session` | `{session_id}` | `ConsolidationReport` |
| `consolidate_item` | `{item: MemoryItem}` | `{promoted_to: str}` |

## Configuration

| File | Purpose |
|------|---------|
| `ttl.config.json` | TTL and threshold settings |
| `vector-store.config.json` | ChromaDB connection |
| `embedding.config.json` | Ollama embedding model |

## Key Behaviours

### Novelty Detection

Before every write, the nearest neighbour in `brain.short-term-memory` is queried. If cosine similarity > `0.9` (configurable), the existing item's `importanceScore` is boosted by `0.05` and no new item is created.

### Affective Boost

If `affective_valence` is present in the item's `metadata`, it contributes to the `importanceScore` at consolidation time.

### Consolidation Pipeline

On `stm.expire_session`:
1. **SCAN** — retrieve all items for the session from Redis.
2. **SCORE** — `finalScore = importanceScore + (accessCount × 0.1) + (affectiveValence × 0.2)`.
3. **GATE** — `finalScore ≥ 0.5`: promote; else delete.
4. **EMBED** — promoted items are re-embedded by the ChromaAdapter.
5. **PRUNE** — processed items removed from `brain.short-term-memory` and Redis.

## Deployment

```bash
# Start backing services
docker compose up -d redis chromadb ollama

# Install and run
cd modules/group-ii-cognitive-processing/memory/short-term-memory
uv sync
uv run python -m short_term_memory
```

## Development

```bash
uv run ruff check .
uv run mypy src/
uv run pytest
```

---

## Testing

Framework: **pytest**. Coverage threshold: **80%**.

```bash
cd modules/group-ii-cognitive-processing/memory/short-term-memory

# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Skip integration tests that require Redis, ChromaDB, and Ollama:
SKIP_INTEGRATION_TESTS=1 uv run pytest tests/ -m "not integration" -q
SKIP_CHROMA_TESTS=1 uv run pytest tests/ -m "not integration" -q
```

Actual coverage: **89%** (above threshold, 2026-03-03 sweep — see
[workplan §7](../../../../docs/test-upgrade-workplan.md)).

Skip variables:

| Variable | Effect |
|----------|--------|
| `SKIP_INTEGRATION_TESTS=1` | Skips all integration tests (coarse monorepo-wide override) |
| `SKIP_CHROMA_TESTS=1` | Skips ChromaDB-dependent tests |

Known gaps: `src/a2a_handler.py` (P09), `src/mcp_tools.py` (P10) — see workplan.
