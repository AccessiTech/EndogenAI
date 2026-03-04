# Working Memory

**Module**: `endogenai-working-memory`  
**Group**: II – Cognitive Processing  
**MCP Port**: 8151  
**A2A Port**: 8051  
**Brain region analogy**: Prefrontal cortex / dorsolateral PFC — active context maintenance, rapid gating, and goal-directed attention span.

---

## Purpose

Working Memory is the active context buffer for EndogenAI. It holds the minimal, most-relevant set of memory items required for the current reasoning step, assembles context from downstream stores (short-term, long-term, and episodic memory) via a **three-source hybrid retrieval pattern**, and enforces strict capacity limits so that inference budget is never exhausted by stale or irrelevant context.

Items are evicted when either the **item-count cap** (default 20) or the **token budget** (default 8000 tokens) is exceeded. Eviction is governed by a compound priority score that weights:

- Recency of access (exponential decay, configurable half-life)
- Importance score (from the canonical `MemoryItem` schema)
- Cosine similarity to the current query embedding

Evicted items are dispatched downstream to short-term or episodic memory via the **ConsolidationDispatcher**, preserving continuity across sessions.

---

## Architecture

```
ContextLoader
 ├── 1. STM query  (brain.short-term-memory, semantic NN, session filter)
 ├── 2. LTM query  (brain.long-term-memory, semantic NN)
 └── 3. Episodic query (brain.episodic-memory, semantic NN, time-window)
      └── merge + SHA256 dedup + importance sort → capacity trim → ContextPayload

WorkingMemoryStore (in-process dict KV)
 ├── write()  → evict if over maxItems or tokenBudget
 ├── read()   → accessCount++
 ├── update() → field patch
 ├── evict()  → explicit removal
 └── list_active() → sorted by importanceScore desc

ConsolidationDispatcher
 ├── Tulving triple present (sessionId + sourceTaskId + createdAt) → episodic A2A
 └── No triple → STM A2A
```

---

## Capacity Limits

Two independent limits are enforced on every `write()`:

| Limit | Default | Config key |
|-------|---------|-----------|
| Item count | 20 | `capacity.config.json → maxItems` |
| Token budget | 8 000 tokens | `capacity.config.json → tokenBudget` |

Token count is estimated at `len(content) × 0.25` characters-to-tokens. When either limit is breached, the item with the **highest eviction priority** is removed. Tied priority → oldest `created_at`.

---

## Eviction Priority Formula

$$
P_{evict} = (1 - \text{importanceScore}) \times w_{importance}
           + (1 - e^{-\Delta t / \tau}) \times w_{decay}
           + (1 - \cos(\vec{q}, \vec{e})) \times w_{relevance}
$$

Where:

- $\Delta t$ = seconds since last access
- $\tau$ = `decayHalfLife` (default 300 s)
- $\vec{q}$ = query embedding (None → 0.5 sentinel)
- $w_{importance} = 0.6$, $w_{relevance} = 0.4$ (configurable)

---

## Interface

### MCP Tools

| Tool name | Description |
|-----------|-------------|
| `working_memory.assemble_context` | Load context from STM + LTM + Episodic, populate store, return `ContextPayload` |
| `working_memory.write_item` | Write a `MemoryItem` directly into the active store |
| `working_memory.update_item` | Patch fields on an existing active item |
| `working_memory.evict_item` | Explicitly remove an item and dispatch it downstream |
| `working_memory.list_active` | List all active items, optionally filtered by `session_id` |

### A2A Tasks

| Task type | Description |
|-----------|-------------|
| `assemble_context` | Assemble context for a session and query |
| `consolidate_session` | Evict all items for a session and dispatch downstream |
| `apply_affective_boost` | Boost `importanceScore` by `boost_delta` for a given item |

---

## Configuration

### `capacity.config.json`

```json
{
  "maxItems": 20,
  "tokenBudget": 8000,
  "decayHalfLife": 300,
  "importanceWeight": 0.6,
  "relevanceWeight": 0.4
}
```

### `retrieval.config.json`

```json
{
  "sources": ["short-term-memory", "long-term-memory", "episodic-memory"],
  "topK": 10,
  "minImportanceScore": 0.1,
  "stmEndpoint": "http://localhost:8052",
  "ltmEndpoint": "http://localhost:8053",
  "episodicEndpoint": "http://localhost:8054"
}
```

---

## Development

```bash
cd modules/group-ii-cognitive-processing/memory/working-memory

# Install dependencies
uv sync

# Lint
uv run ruff check .

# Type-check
uv run mypy src/

# Tests
uv run pytest

# Integration tests (requires live STM, LTM, Episodic endpoints)
ENDOGENAI_INTEGRATION_TESTS=1 uv run pytest tests/ -m integration
```

---

## Agent Card

Exposed at `/.well-known/agent-card.json` — see [agent-card.json](agent-card.json).

---

## Dependencies

All inference routes through **LiteLLM**. All vector store operations route through the `endogenai-vector-store` adapter — no direct ChromaDB, Qdrant, or Redis SDK calls.

Cross-module consolidation dispatches via `infrastructure/adapters/bridge.ts`.

---

## Testing

Framework: **pytest**. Coverage threshold: **80%**.

```bash
cd modules/group-ii-cognitive-processing/memory/working-memory

# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Skip integration tests that require live STM/LTM/Episodic endpoints:
SKIP_INTEGRATION_TESTS=1 uv run pytest tests/ -m "not integration" -q
```

Actual coverage: **83%** (above threshold, 2026-03-03 sweep — see
[workplan §7](../../../../docs/test-upgrade-workplan.md)).

Skip variables:

| Variable | Effect |
|----------|--------|
| `SKIP_INTEGRATION_TESTS=1` | Skips all integration tests (coarse monorepo-wide override) |
| `SKIP_CHROMA_TESTS=1` | Skips ChromaDB-dependent tests |

Known gap: `src/instrumentation/otel_setup.py` — see workplan P11.
