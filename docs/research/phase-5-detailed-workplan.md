# Phase 5 — Detailed Implementation Workplan

> **Status**: ✅ APPROVED — all open questions resolved; implementation in progress on `feat/phase-5-cognitive-processing`.  
> **Scope**: Group II: Cognitive Processing — §§5.1–5.6  
> **Milestone**: M5 — Memory Stack Live (full memory stack operational with seed pipeline
> verified, reasoning layer producing traceable inference records)  
> **Prerequisite**: Phase 4 (Group I: Signal Processing) all gate checks passing.  
> **Research references**:
> - [phase-5-neuroscience-of-organic-memory.md](phase-5-neuroscience-of-organic-memory.md)
> - [phase-5-mcp-solutions-and-programmatic-techniques.md](phase-5-mcp-solutions-and-programmatic-techniques.md)
> - [phase-5-synthesis-workplan.md](phase-5-synthesis-workplan.md)

---

## Contents

1. [Pre-Implementation Checklist](#1-pre-implementation-checklist)
2. [Build Sequence and Gate Definitions](#2-build-sequence-and-gate-definitions)
3. [Directory Structure Overview](#3-directory-structure-overview)
4. [§5.1 — Working Memory](#4-51--working-memory)
5. [§5.2 — Short-Term Memory](#5-52--short-term-memory)
6. [§5.3 — Long-Term Memory](#6-53--long-term-memory)
7. [§5.4 — Episodic Memory](#7-54--episodic-memory)
8. [§5.5 — Affective / Motivational Layer](#8-55--affective--motivational-layer)
9. [§5.6 — Decision-Making & Reasoning](#9-56--decision-making--reasoning)
10. [Cross-Cutting: Consolidation Pipeline](#10-cross-cutting-consolidation-pipeline)
11. [Cross-Cutting: Docker Compose Services](#11-cross-cutting-docker-compose-services)
12. [Phase 5 Completion Gate](#12-phase-5-completion-gate)
13. [Open Questions Requiring Owner Decision](#13-open-questions-requiring-owner-decision)

---

## 1. Pre-Implementation Checklist

All items below must be confirmed before any Phase 5 code is written.

### 1.1 Phase 4 Gate

```bash
# All Group I modules must have required files and passing tests
ls modules/group-i-signal-processing/{sensory-input,attention-filtering,perception}/{README.md,agent-card.json}
cd modules/group-i-signal-processing/sensory-input && uv run pytest
cd modules/group-i-signal-processing/attention-filtering && uv run pytest
cd modules/group-i-signal-processing/perception && uv run pytest
pnpm run lint && pnpm run typecheck
```

If any item fails, raise with Phase 4 Executive before proceeding.

### 1.2 Collection Registry Confirmation

All five Phase 5 collections are already registered in
[shared/vector-store/collection-registry.json](../../shared/vector-store/collection-registry.json):

| Collection | Layer | Memory Type | Notes |
|------------|-------|-------------|-------|
| `brain.working-memory` | prefrontal | working | Capacity-constrained; evict by lowest `importanceScore` |
| `brain.short-term-memory` | memory | short-term | TTL-governed; triggers consolidation on expiry |
| `brain.long-term-memory` | memory | long-term | `importanceScore ≥ 0.5` gate for admission |
| `brain.episodic-memory` | memory | episodic | Requires `sessionId + sourceTaskId + createdAt` |
| `brain.affective` | limbic | short-term | High churn; links to triggering event IDs |
| `brain.reasoning` | prefrontal | working | High churn; reusable flag for cached plans |

✅ No new collection registry additions required for Phase 5.

### 1.3 Shared Schema Status

No new JSON Schemas are required before Phase 5 implementation begins. The following
existing schemas are sufficient:

| Schema | Location | Purpose |
|--------|----------|---------|
| `MemoryItem` | `shared/types/memory-item.schema.json` | Canonical memory record |
| `RewardSignal` | `shared/types/reward-signal.schema.json` | Affective payload |
| `Signal` | `shared/types/signal.schema.json` | Input signal envelope |
| `MCPContext` | `shared/schemas/mcp-context.schema.json` | Context exchange |
| `A2ATask` | `shared/schemas/a2a-task.schema.json` | Task delegation |

If any module implementation requires a new shared type (e.g. `ConsolidationEvent`,
`InferenceTrace`), the schema must be landed in `shared/schemas/` and all checks must
pass **before** the implementation module imports it. This is the schemas-first gate.

### 1.4 Docker Compose Services Required

The following services must be running for integration tests. They should already be
present in `docker-compose.yml` from Phase 1/2. Verify:

```bash
docker compose config --services | grep -E "chromadb|redis|ollama"
```

Expected output includes: `chromadb`, `redis` (or `valkey`), `ollama`.

If `redis` or `valkey` is not in `docker-compose.yml`, it must be added before §5.2
integration tests can run. This is a blocker — record as an open question if missing.

---

## 2. Build Sequence and Gate Definitions

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 5 Build Sequence (strict order within domain)            │
│                                                                 │
│  1. §5.2 Short-Term Memory  ←── simplest; no upstream deps      │
│  2. §5.3 Long-Term Memory   ←── seeds bootstrap pipeline        │
│  3. §5.4 Episodic Memory    ←── depends on STM consolidation    │
│  4. §5.1 Working Memory     ←── assembles from 5.2 + 5.3 + 5.4 │
│                                                                 │
│  ── GATE 1: all four memory modules pass tests ──               │
│                                                                 │
│  5. §5.5 Affective Layer    ←── needs working memory for boost  │
│                                                                 │
│  ── GATE 2: affective module passes tests ──                    │
│                                                                 │
│  6. §5.6 Reasoning          ←── needs WM assembly + affective   │
└─────────────────────────────────────────────────────────────────┘
```

**Within each module**, follow this sub-sequence:
1. `pyproject.toml` + `uv sync` + `agent-card.json`
2. Core data types / Pydantic models
3. Vector store integration (adapter wiring only)
4. Core logic
5. MCP interface
6. A2A interface
7. Unit tests (mocked dependencies)
8. Integration tests (Testcontainers)
9. `README.md`
10. Commit: `feat(<scope>): implement <module>`

**Gate 1 check** (run before §5.5):
```bash
ls modules/group-ii-cognitive-processing/memory/{working-memory,short-term-memory,long-term-memory,episodic-memory}/{README.md,agent-card.json}
cd modules/group-ii-cognitive-processing/memory/working-memory && uv run pytest
cd modules/group-ii-cognitive-processing/memory/short-term-memory && uv run pytest
cd modules/group-ii-cognitive-processing/memory/long-term-memory && uv run pytest
cd modules/group-ii-cognitive-processing/memory/episodic-memory && uv run pytest
```

**Gate 2 check** (run before §5.6):
```bash
ls modules/group-ii-cognitive-processing/affective/{README.md,agent-card.json}
cd modules/group-ii-cognitive-processing/affective && uv run pytest
```

---

## 3. Directory Structure Overview

The complete directory tree for Phase 5 (all files to be created):

```
modules/group-ii-cognitive-processing/
├── memory/
│   ├── working-memory/
│   │   ├── README.md
│   │   ├── agent-card.json
│   │   ├── pyproject.toml
│   │   ├── pyrightconfig.json
│   │   ├── uv.lock                         (generated by uv sync)
│   │   ├── capacity.config.json
│   │   ├── retrieval.config.json
│   │   ├── src/
│   │   │   └── working_memory/
│   │   │       ├── __init__.py
│   │   │       ├── py.typed
│   │   │       ├── models.py               (ContextPayload, ActiveItem, EvictionPolicy)
│   │   │       ├── store.py                (in-process KV store + importanceScore eviction)
│   │   │       ├── loader.py               (retrieval-augmented context assembler)
│   │   │       ├── consolidation.py        (dispatch evicted items downstream)
│   │   │       ├── mcp_tools.py            (MCP tool definitions)
│   │   │       └── a2a_handler.py          (A2A task handler)
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_store.py
│   │       ├── test_loader.py
│   │       ├── test_consolidation.py
│   │       └── test_mcp_tools.py
│   ├── short-term-memory/
│   │   ├── README.md
│   │   ├── agent-card.json
│   │   ├── pyproject.toml
│   │   ├── pyrightconfig.json
│   │   ├── uv.lock
│   │   ├── ttl.config.json
│   │   ├── vector-store.config.json
│   │   ├── embedding.config.json
│   │   ├── src/
│   │   │   └── short_term_memory/
│   │   │       ├── __init__.py
│   │   │       ├── py.typed
│   │   │       ├── models.py               (SessionRecord, ConsolidationCandidate)
│   │   │       ├── store.py                (Redis/Valkey backend — session-keyed lists with TTL)
│   │   │       ├── novelty.py              (near-duplicate detection — DG analogue)
│   │   │       ├── consolidation.py        (SCAN→SCORE→GATE→EMBED→PRUNE pipeline)
│   │   │       ├── search.py               (semantic search over current session)
│   │   │       ├── mcp_tools.py
│   │   │       └── a2a_handler.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_store.py
│   │       ├── test_novelty.py
│   │       ├── test_consolidation.py
│   │       ├── test_search.py
│   │       └── test_integration_consolidation.py  (Testcontainers: Redis + ChromaDB)
│   ├── long-term-memory/
│   │   ├── README.md
│   │   ├── agent-card.json
│   │   ├── pyproject.toml
│   │   ├── pyrightconfig.json
│   │   ├── uv.lock
│   │   ├── vector-store.config.json
│   │   ├── embedding.config.json
│   │   ├── indexing.config.json
│   │   ├── src/
│   │   │   └── long_term_memory/
│   │   │       ├── __init__.py
│   │   │       ├── py.typed
│   │   │       ├── models.py               (SemanticFact, GraphEdge, LTMItem)
│   │   │       ├── vector_store.py         (ChromaDB/Qdrant via endogenai_vector_store)
│   │   │       ├── graph_store.py          (Kuzu default / Neo4j production)
│   │   │       ├── sql_store.py            (SQLite default / PostgreSQL production)
│   │   │       ├── retrieval.py            (semantic + hybrid re-ranking)
│   │   │       ├── seed_pipeline.py        (LlamaIndex chunker + boot-time ingest)
│   │   │       ├── reconsolidation.py      (increment accessCount + re-embed on retrieval)
│   │   │       ├── mcp_tools.py
│   │   │       └── a2a_handler.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_vector_store.py
│   │       ├── test_graph_store.py
│   │       ├── test_sql_store.py
│   │       ├── test_retrieval.py
│   │       ├── test_seed_pipeline.py
│   │       └── test_integration_retrieval.py       (Testcontainers: ChromaDB)
│   └── episodic-memory/
│       ├── README.md
│       ├── agent-card.json
│       ├── pyproject.toml
│       ├── pyrightconfig.json
│       ├── uv.lock
│       ├── vector-store.config.json
│       ├── embedding.config.json
│       ├── retention.config.json
│       ├── src/
│       │   └── episodic_memory/
│       │       ├── __init__.py
│       │       ├── py.typed
│       │       ├── models.py               (Episode, EpisodeEvent, TimelineQuery)
│       │       ├── store.py                (append-only episode log + ChromaDB)
│       │       ├── indexer.py              (what-where-when metadata enforcer)
│       │       ├── retrieval.py            (composite semantic + temporal queries)
│       │       ├── timeline.py             (session-ordered replay)
│       │       ├── distillation.py         (episodic → semantic LTM background job)
│       │       ├── mcp_tools.py
│       │       └── a2a_handler.py
│       └── tests/
│           ├── __init__.py
│           ├── test_store.py
│           ├── test_indexer.py
│           ├── test_retrieval.py
│           ├── test_timeline.py
│           ├── test_distillation.py
│           └── test_integration_timeline.py        (Testcontainers: ChromaDB)
├── affective/
│   ├── README.md
│   ├── agent-card.json
│   ├── pyproject.toml
│   ├── pyrightconfig.json
│   ├── uv.lock
│   ├── drive.config.json
│   ├── vector-store.config.json
│   ├── src/
│   │   └── affective/
│   │       ├── __init__.py
│   │       ├── py.typed
│   │       ├── models.py                   (DriveState, RPEResult, AffectiveTag)
│   │       ├── rpe.py                      (reward prediction error computation)
│   │       ├── drive.py                    (drive variable state machine)
│   │       ├── weighting.py               (importanceScore boost dispatch)
│   │       ├── store.py                    (brain.affective via endogenai_vector_store)
│   │       ├── mcp_tools.py
│   │       └── a2a_handler.py
│   └── tests/
│       ├── __init__.py
│       ├── test_rpe.py
│       ├── test_drive.py
│       ├── test_weighting.py
│       └── test_integration_signal_flow.py (Testcontainers: ChromaDB)
└── reasoning/
    ├── README.md
    ├── agent-card.json
    ├── pyproject.toml
    ├── pyrightconfig.json
    ├── uv.lock
    ├── strategy.config.json
    ├── vector-store.config.json
    ├── src/
    │   └── reasoning/
    │       ├── __init__.py
    │       ├── py.typed
    │       ├── models.py                   (InferenceTrace, CausalPlan, ReasoningResult)
    │       ├── signatures.py               (DSPy typed signatures)
    │       ├── inference.py                (LogicalInference + ChainOfThought)
    │       ├── causal.py                   (CausalPlan + ProgramOfThought)
    │       ├── planning.py                 (PlanUnderUncertainty + ReAct)
    │       ├── conflict.py                 (ConflictResolution + MultiChainComparison)
    │       ├── lm_config.py                (LiteLLM → DSPy wiring; NO direct SDK calls)
    │       ├── store.py                    (brain.reasoning via endogenai_vector_store)
    │       ├── mcp_tools.py
    │       └── a2a_handler.py
    └── tests/
        ├── __init__.py
        ├── test_signatures.py
        ├── test_inference.py
        ├── test_causal.py
        ├── test_planning.py
        ├── test_conflict.py
        └── test_integration_trace_storage.py  (Testcontainers: ChromaDB)
```

---

## 4. §5.1 — Working Memory

### 4.1 Biological Basis

| Region | Mapping |
|--------|---------|
| DLPFC | Active assembler: pulls context from all memory stores |
| vlPFC | Passive hold: items in `brain.working-memory` until evicted |
| Baddeley episodic buffer | Multi-source integration from STM + LTM + episodic |
| Central executive | Score-and-filter step before context payload delivery |

Source: [resources/neuroanatomy/prefrontal-cortex.md](../../resources/neuroanatomy/prefrontal-cortex.md)

### 4.2 `agent-card.json`

```json
{
  "name": "working-memory",
  "description": "Assembles and manages the active context window — the agent's immediate focus of attention. Retrieval-augmented: draws from short-term, long-term, and episodic stores, scoring items by importance and token budget before delivery.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8051",
    "mcp": "http://localhost:8151"
  }
}
```

### 4.3 `capacity.config.json`

```json
{
  "maxItems": 20,
  "tokenBudget": 8000,
  "evictionPolicy": "compound-priority",
  "decayHalfLifeSeconds": 300,
  "contextualRelevanceWeight": 0.4,
  "importanceScoreWeight": 0.6,
  "tieBreaker": "oldest-createdAt"
}
```

**Compound eviction priority** — items are not evicted on a timer. Eviction fires only
when capacity is breached, at which point the item with the **highest `eviction_priority`**
is dropped:

```
eviction_priority =
    (1 - importanceScore) * importanceScoreWeight
  + time_decay(last_accessed_at, now, half_life=decayHalfLifeSeconds)
  + (1 - cosine_similarity(item.embedding, current_query.embedding)) * contextualRelevanceWeight
```

- `time_decay` uses exponential decay: `1 - exp(-Δt / half_life)` — items lose priority
  gradually rather than hard-cutting at a timestamp.
- `contextual_relevance` is cosine similarity between the item's stored embedding and the
  current query embedding — items unrelated to the current task deprioritise faster.
- High `importanceScore` (accumulated via access count + affective valence) directly
  counteracts decay, letting frequently-accessed valuable items survive longer.
- Both `decayHalfLifeSeconds` and weight parameters are configurable here.

### 4.4 `retrieval.config.json`

```json
{
  "sources": ["brain.short-term-memory", "brain.long-term-memory", "brain.episodic-memory"],
  "topKPerSource": 10,
  "mergeStrategy": "importance-rank-merge",
  "minImportanceScore": 0.1,
  "embeddingModel": "nomic-embed-text",
  "ollamaBaseUrl": "http://localhost:11434"
}
```

### 4.5 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-working-memory"
version = "0.1.0"
description = "Working memory module — active context window assembly with retrieval-augmented loading."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",       # shared adapter — local path dep
  "pydantic>=2.7",
  "structlog>=24.1",
  "httpx>=0.27",
  "tiktoken>=0.7",                # token budget counting
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[chromadb]>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 4.6 Core Implementation Notes

**`store.py`** — in-process KV store:
- Dictionary keyed by `item_id` → `MemoryItem`.
- `write(item)`: apply capacity check; if `len > maxItems`, compute `eviction_priority` for
  all active items and evict the highest-scoring candidate (compound priority: decay +
  contextual relevance + inverse importance).
- `read(item_id)`: return item + increment `accessCount` and refresh `last_accessed_at`
  (reconsolidation analogue; recency reset prevents premature decay).
- `evict(item_id)`: remove and dispatch to `consolidation.py`.
- `compute_eviction_priority(item, current_query_embedding)`: returns compound score per
  `capacity.config.json` weights — used by `write` and exposed for testing.
- `list_active()`: return all items sorted by `importanceScore` descending.

**`loader.py`** — retrieval-augmented context assembler:
- Accepts `session_id`, `query`, optional `capacity_override`.
- Queries each configured source collection via `endogenai_vector_store`.
- Merges results: deduplicate by content hash; sort by `importanceScore`; trim to `maxItems` and `tokenBudget`.
- Applies affective boost if a `RewardSignal` was attached to a co-occurring item in this session.
- Returns `ContextPayload` (Pydantic model).

**`consolidation.py`** — eviction dispatcher:
- On evict, calls the short-term-memory module's A2A endpoint with task type `consolidate_item`.
- If item has `sessionId + sourceTaskId + createdAt`, routes to episodic; otherwise to long-term.

### 4.7 MCP Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `working_memory.assemble_context` | `(session_id: str, query: str, capacity_override?: int) → ContextPayload` | Retrieve and rank items into an active context payload |
| `working_memory.write_item` | `(item: MemoryItem) → str` | Write an item to working memory; returns item_id |
| `working_memory.update_item` | `(item_id: str, delta: dict) → MemoryItem` | Patch metadata fields (importanceScore, content); triggers reconsolidation |
| `working_memory.evict_item` | `(item_id: str) → None` | Explicit eviction; dispatches to consolidation |
| `working_memory.list_active` | `(session_id: str) → list[MemoryItem]` | Returns all active items for a session |

### 4.8 A2A Task Handlers

| Task type | Input | Output | Notes |
|-----------|-------|--------|-------|
| `assemble_context` | `{session_id, query}` | `ContextPayload` | Primary task; called by reasoning module |
| `consolidate_session` | `{session_id}` | `ConsolidationReport` | Flushes all active session items downstream |
| `apply_affective_boost` | `{item_id, reward_value}` | `MemoryItem` | Called by affective module on reward signal |

---

## 5. §5.2 — Short-Term Memory

### 5.1 Biological Basis

| Region | Mapping |
|--------|---------|
| Hippocampus CA1 | Novelty detection: compare expected vs. retrieved; flag new items |
| Dentate Gyrus | Pattern separation: near-duplicate detection before write |
| Systems consolidation | TTL expiry → background scoring/promotion job |

Source: [resources/neuroanatomy/hippocampus.md](../../resources/neuroanatomy/hippocampus.md)

### 5.2 `agent-card.json`

```json
{
  "name": "short-term-memory",
  "description": "Session-scoped transient memory store. Records recent experience with TTL governance; consolidates important items into long-term or episodic memory when the session ends or the buffer threshold is reached.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8052",
    "mcp": "http://localhost:8152"
  }
}
```

### 5.3 Config Files

**`ttl.config.json`**:
```json
{
  "defaultTTLSeconds": 1800,
  "maxItemsBeforeConsolidation": 500,
  "consolidationTrigger": "ttl-or-threshold",
  "sessionKeyPrefix": "session:"
}
```

**`vector-store.config.json`**:
```json
{
  "backend": "chromadb",
  "collection": "brain.short-term-memory",
  "host": "localhost",
  "port": 8000
}
```

**`embedding.config.json`**:
```json
{
  "provider": "ollama",
  "model": "nomic-embed-text",
  "baseUrl": "http://localhost:11434",
  "dimensions": 768
}
```

### 5.4 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-short-term-memory"
version = "0.1.0"
description = "Short-term memory module — session-scoped TTL store with consolidation pipeline."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",
  "redis>=5.0",
  "pydantic>=2.7",
  "structlog>=24.1",
  "httpx>=0.27",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[redis]>=4.7",
  "testcontainers[chromadb]>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 5.5 Core Implementation Notes

**`store.py`** — Redis backend:
- All session items stored as Redis lists: `session:<session_id>` → list of serialised `MemoryItem` JSON.
- Each item also written to `brain.short-term-memory` ChromaDB collection for semantic search.
- `write(item)`: novelty check; if novel → write to Redis + ChromaDB; if duplicate → update existing.
- `expire_session(session_id)`: called on session end; triggers `consolidation.py`.
- TTL set on Redis keys via `EXPIRE session:<session_id> <ttl_seconds>`.

**`novelty.py`** — DG pattern separation analogue:
- Query `brain.short-term-memory` for nearest neighbours of new content.
- If cosine similarity of top-1 result > `NOVELTY_THRESHOLD` (default 0.9): not novel → update.
- Else: novel → create new item.

**`consolidation.py`** — SCAN→SCORE→GATE→EMBED→PRUNE:
```
SCAN:  Retrieve all items for session from Redis
SCORE: finalScore = importanceScore + (accessCount × 0.1) + (affectiveValence × 0.2)
GATE:  if finalScore ≥ 0.5 AND has (sessionId + sourceTaskId + createdAt):
           → promote to brain.episodic-memory
       elif finalScore ≥ 0.5:
           → promote to brain.long-term-memory
       else:
           → delete
EMBED: Re-embed promoted items via nomic-embed-text before writing to target collection
PRUNE: Delete all processed items from brain.short-term-memory and Redis list
```

### 5.6 MCP Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `stm.write` | `(item: MemoryItem) → str` | Write session record; novelty check applied |
| `stm.search` | `(session_id: str, query: str, top_k: int) → list[MemoryItem]` | Semantic search over current session |
| `stm.expire_session` | `(session_id: str) → ConsolidationReport` | End session; run consolidation pipeline |
| `stm.get_by_session` | `(session_id: str) → list[MemoryItem]` | Return all items for a session (ordered) |

### 5.7 A2A Task Handlers

| Task type | Input | Output |
|-----------|-------|--------|
| `write_record` | `{item: MemoryItem}` | `{item_id: str}` |
| `search_session` | `{session_id, query, top_k}` | `{items: list[MemoryItem]}` |
| `consolidate_item` | `{item: MemoryItem}` | `{promoted_to: str | "deleted"}` |
| `consolidate_session` | `{session_id}` | `ConsolidationReport` |

---

## 6. §5.3 — Long-Term Memory

### 6.1 Biological Basis

| Region | Mapping |
|--------|---------|
| Distributed neocortex | Persistent semantic store; decontextualised facts |
| Systems consolidation (Standard Model) | Promotion from STM after importance threshold crossed |
| LTP reconsolidation | Each retrieval → increment `accessCount` + re-embed if content updated |

Source: [resources/neuroanatomy/hippocampus.md](../../resources/neuroanatomy/hippocampus.md)

### 6.2 `agent-card.json`

```json
{
  "name": "long-term-memory",
  "description": "Persistent semantic world model. Stores consolidated facts, learned associations, and decontextualised knowledge indexed by semantic similarity. Primary retrieval source for the working memory loader and reasoning module.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8053",
    "mcp": "http://localhost:8153"
  }
}
```

### 6.3 Config Files

**`vector-store.config.json`**:
```json
{
  "backend": "chromadb",
  "collection": "brain.long-term-memory",
  "host": "localhost",
  "port": 8000,
  "productionBackend": "qdrant"
}
```

**`indexing.config.json`**:
```json
{
  "importanceThreshold": 0.5,
  "chunkingStrategy": "frontmatter-aware",
  "chunkOverlapTokens": 50,
  "maxChunkTokens": 512,
  "seedDocuments": "resources/static/knowledge/",
  "graphBackend": "kuzu",
  "sqlBackend": "sqlite"
}
```

### 6.4 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-long-term-memory"
version = "0.1.0"
description = "Long-term memory module — persistent semantic storage with graph and SQL adapters."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",
  "kuzu>=0.8",
  "llama-index-core>=0.11",
  "llama-index-readers-file>=0.2",
  "pydantic>=2.7",
  "structlog>=24.1",
  "httpx>=0.27",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[chromadb]>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 6.5 Core Implementation Notes

**`vector_store.py`** — ChromaDB/Qdrant via adapter:
- `write(item)`: validate `importanceScore ≥ 0.5`; embed via Ollama; write to `brain.long-term-memory`.
- `query(query_text, top_k)`: embed query; vector search; return top-k `MemoryItem`s.
- `update(item_id, delta)`: reconsolidation — update metadata; re-embed if `content` changed.

**`graph_store.py`** — Kuzu (dev) / Neo4j (prod):
- Entity nodes represent facts with unique `entity_id`.
- Edges represent relationships (predicate, strength, source_item_id).
- `write_edge(src, predicate, dst, importance)`: create edge if not exists; update strength.
- `query_neighbours(entity_id, depth)`: return sub-graph for working memory injection.

**`sql_store.py`** — SQLite (dev) / PostgreSQL (prod):
- Facts table: `(entity_id, predicate, object, importance, source_item_id, created_at)`.
- `write_fact(fact)`: upsert; update importance if predicate+object already present.
- `query_facts(entity_id)`: exact-match lookup; returns ordered by importance.

**`seed_pipeline.py`** — boot-time LlamaIndex ingest:
- Called once at module startup if `brain.long-term-memory` is empty.
- Uses LlamaIndex `SimpleDirectoryReader` to load `resources/static/knowledge/`.
- Frontmatter-aware splitter: parse YAML frontmatter; attach `maps-to-modules` as filter metadata.
- Embeds each chunk via Ollama `nomic-embed-text`; writes to `brain.long-term-memory` via adapter.

### 6.6 MCP Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ltm.write` | `(item: MemoryItem) → str` | Write consolidated item; importance gate enforced |
| `ltm.query` | `(query: str, top_k: int, filters?: dict) → list[MemoryItem]` | Semantic + optional hybrid search |
| `ltm.write_fact` | `(fact: SemanticFact) → str` | Write structured fact to SQL store |
| `ltm.query_facts` | `(entity_id: str) → list[SemanticFact]` | Exact-match structured lookup |
| `ltm.write_edge` | `(src: str, predicate: str, dst: str) → str` | Create graph edge |
| `ltm.query_graph` | `(entity_id: str, depth: int) → SubGraph` | Graph neighbourhood query |
| `ltm.run_seed_pipeline` | `() → SeedReport` | Trigger seed ingest (idempotent) |

### 6.7 A2A Task Handlers

| Task type | Input | Output |
|-----------|-------|--------|
| `write_item` | `{item: MemoryItem}` | `{item_id: str}` |
| `query` | `{query, top_k, filters?}` | `{items: list[MemoryItem]}` |
| `write_fact` | `{fact: SemanticFact}` | `{fact_id: str}` |
| `seed` | `{}` | `SeedReport` |

---

## 7. §5.4 — Episodic Memory

### 7.1 Biological Basis

| Region | Mapping |
|--------|---------|
| MTL + hippocampus CA1/CA3 | What-where-when event records |
| Tulving 9 properties | Append-only ordered event log; each item = one discrete event |
| BLA emotional boost | `affectiveValence` required on all episodic items |
| Semantic distillation | Background job: recurring patterns → `brain.long-term-memory` |

Source: [resources/neuroanatomy/hippocampus.md](../../resources/neuroanatomy/hippocampus.md)

### 7.2 `agent-card.json`

```json
{
  "name": "episodic-memory",
  "description": "Autobiographical event log. Records discrete, temporally ordered events carrying full what-where-when context. Supports semantic episode search, timeline reconstruction, and periodic distillation of recurring patterns into long-term memory.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8054",
    "mcp": "http://localhost:8154"
  }
}
```

### 7.3 Config Files

**`retention.config.json`**:
```json
{
  "maxEpisodesPerSession": 10000,
  "distillationMinClusterSize": 3,
  "distillationScheduleCron": "0 * * * *",
  "retentionDays": 90
}
```

### 7.4 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-episodic-memory"
version = "0.1.0"
description = "Episodic memory module — autobiographical event log with temporal indexing and semantic distillation."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",
  "pydantic>=2.7",
  "structlog>=24.1",
  "httpx>=0.27",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[chromadb]>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 7.5 Core Implementation Notes

**`indexer.py`** — what-where-when enforcer:
- Pydantic validator on every incoming `MemoryItem` of type `episodic`:
  - REQUIRED: `sessionId` (where), `sourceTaskId` (what), `createdAt` ISO-8601 (when)
  - REQUIRED: `affectiveValence` (float, -1.0 to 1.0)
- Raises `ValidationError` if any required filed is missing or malformed.

**`store.py`** — append-only log:
- All writes go to `brain.episodic-memory` ChromaDB collection via adapter.
- Items are NEVER updated after initial write (immutable event log).
- On reconsolidation (retrieval), only metadata fields `accessCount` and `importanceScore`
  are updated via `chroma.update()` — content is preserved.

**`retrieval.py`** — composite queries:
- `semantic_search(query, top_k, session_id?, time_window?)`: embed query; filter by
  `sessionId` + `createdAt` range if provided; re-rank by `importance × affectiveValence`.
- `timeline_query(session_id)`: retrieve all events for a session; return ordered by `createdAt`.

**`distillation.py`** — episodic → semantic LTM:
- Runs on schedule (cron) or on explicit trigger.
- Clusters episodic items by cosine similarity (threshold-based); clusters ≥ `minClusterSize`
  are summarised into a new `MemoryItem(type="long-term", ...)` and written to the LTM module
  via A2A task `write_item`.
- Increments `accessCount` on all source items after distillation (reconsolidation analogue).

### 7.6 MCP Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `em.write_event` | `(event: MemoryItem) → str` | Append event; what-where-when validation enforced |
| `em.search` | `(query: str, session_id?: str, time_window?: tuple) → list[MemoryItem]` | Composite semantic + temporal search |
| `em.get_timeline` | `(session_id: str) → list[MemoryItem]` | Ordered timeline for a session |
| `em.run_distillation` | `() → DistillationReport` | Trigger distillation job (idempotent) |

### 7.7 A2A Task Handlers

| Task type | Input | Output |
|-----------|-------|--------|
| `write_event` | `{event: MemoryItem}` | `{event_id: str}` |
| `search_episodes` | `{query, session_id?, time_window?}` | `{items: list[MemoryItem]}` |
| `get_timeline` | `{session_id}` | `{events: list[MemoryItem]}` |
| `run_distillation` | `{}` | `DistillationReport` |

---

## 8. §5.5 — Affective / Motivational Layer

### 8.1 Biological Basis

| Region | Mapping |
|--------|---------|
| VTA dopamine neurons | RPE signal: phasic burst (positive), dip (negative) |
| Nucleus accumbens | Incentive salience / urgency drive variable |
| Basolateral amygdala | Emotional tagging → hippocampal amplification (importanceScore boost) |
| Hypothalamus | Drive variables: urgency, novelty, curiosity |
| ACC | Conflict detection → `frustration` / `confidence-drop` signals |

Source: [resources/neuroanatomy/limbic-system.md](../../resources/neuroanatomy/limbic-system.md)

### 8.2 `agent-card.json`

```json
{
  "name": "affective",
  "description": "Limbic affective and motivational layer. Computes reward prediction errors from incoming signals, maintains drive state (urgency, novelty, curiosity), dispatches RewardSignals to the memory stack, and modulates working memory importanceScore weights.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8055",
    "mcp": "http://localhost:8155"
  }
}
```

### 8.3 Config Files

**`drive.config.json`**:
```json
{
  "urgencyThreshold": 0.7,
  "noveltyThreshold": 0.6,
  "curiosityThreshold": 0.5,
  "signalWeights": {
    "urgency": 1.0,
    "novelty": 0.8,
    "curiosity": 0.6,
    "reward": 0.7,
    "penalty": 0.7
  },
  "arbitrationStrategy": "normalised-resultant",
  "affectiveWeight": 0.3,
  "driveDecayRatePerTurn": 0.05,
  "drivePersistedAcrossSessions": false
}
```

### 8.4 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-affective"
version = "0.1.0"
description = "Affective / motivational module — RPE computation, drive state, and reward signal dispatch."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",
  "pydantic>=2.7",
  "structlog>=24.1",
  "httpx>=0.27",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[chromadb]>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 8.5 Core Implementation Notes

**`rpe.py`** — reward prediction error:
- `compute_rpe(signal, expected_value) → RewardSignal`:
  - `rpe_value = signal.actual_value - expected_value` (clamped to [-1.0, 1.0])
  - Positive → `type="reward"` (or `"novelty"` if expected was zero)
  - Negative → `type="penalty"` (or `"frustration"` if from reasoning conflict signal)
  - Zero → `type="neutral"`
- All `RewardSignal` instances use `shared/types/reward-signal.schema.json`. No external APIs.

**`drive.py`** — drive state machine:
```python
@dataclass
class DriveState:
    urgency: float = 0.0    # [0, 1]
    novelty: float = 0.0    # [0, 1]
    curiosity: float = 0.0  # [0, 1]

    def update(self, signal: RewardSignal) -> None:
        if signal.type == "urgency":
            self.urgency = min(1.0, self.urgency + signal.value * 0.3)
        elif signal.type == "novelty":
            self.novelty = min(1.0, self.novelty + signal.value * 0.2)
        elif signal.type == "curiosity":
            self.curiosity = min(1.0, self.curiosity + signal.value * 0.2)

    def decay(self) -> None:
        self.urgency = max(0.0, self.urgency - DECAY_RATE)
        self.novelty = max(0.0, self.novelty - DECAY_RATE)
        self.curiosity = max(0.0, self.curiosity - DECAY_RATE)


def combine_signals(
    signals: list[RewardSignal],
    weights: dict[str, float],
) -> float:
    """Normalised-resultant arbitration for conflicting reward signals.

    Each signal contributes a signed weighted value. The raw sum is then
    normalised back to [-1, 1] by dividing by max(1.0, |raw_sum|), preserving
    directionality and allowing opposing drives to cancel toward 0 (ambivalence)
    rather than compounding past the scale boundary.

    Two strong opposing signals cancel toward 0 (biological ambivalence).
    Two same-direction signals reinforce but never exceed ±1.
    """
    raw = sum(s.value * weights.get(s.type, 1.0) for s in signals)
    return raw / max(1.0, abs(raw))
```

`combine_signals` is called by `weighting.py` whenever multiple `RewardSignal`s arrive
in the same processing cycle before the `importanceScore` boost is dispatched to working
memory. The normalised net value is used as the boost magnitude.

**`weighting.py`** — importanceScore boost dispatcher:
- On each incoming `RewardSignal` with `value > 0`:
  - Fetch co-occurring `MemoryItem`s (same `sessionId` within the last N seconds).
  - Call working memory A2A `apply_affective_boost` with `{item_id, reward_value}` for each.
  - Write `RewardSignal` to `brain.affective` collection with `triggering_item_ids` metadata.

### 8.6 MCP Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `affective.score_signal` | `(signal: Signal) → RewardSignal` | Compute RPE for an incoming signal |
| `affective.get_drive_state` | `() → DriveState` | Return current drive variable values |
| `affective.emit_reward` | `(reward: RewardSignal) → None` | Store signal + dispatch importanceScore boosts |

### 8.7 A2A Task Handlers

| Task type | Input | Output |
|-----------|-------|--------|
| `score_signal` | `{signal: Signal, expected_value?: float}` | `{reward: RewardSignal}` |
| `get_drive_state` | `{}` | `DriveState` |
| `emit_reward` | `{reward: RewardSignal}` | `{stored_id: str}` |

---

## 9. §5.6 — Decision-Making & Reasoning

### 9.1 Biological Basis

| Region | Mapping |
|--------|---------|
| DLPFC | `dspy.ChainOfThought` — abstract logical inference |
| vmPFC | `dspy.ProgramOfThought` — causal modelling under uncertainty |
| ACC | Conflict detection → `frustration` RewardSignal to affective module |
| OFC | `dspy.MultiChainComparison` — option evaluation |
| IFG | Guidance constrained generation — inhibitory control |

Source: [resources/neuroanatomy/prefrontal-cortex.md](../../resources/neuroanatomy/prefrontal-cortex.md)

### 9.2 `agent-card.json`

```json
{
  "name": "reasoning",
  "description": "Prefrontal reasoning and planning layer. Performs logical inference, causal planning, uncertainty-aware deliberation, and conflict resolution via DSPy. All LLM calls route through LiteLLM. Inference traces are stored in brain.reasoning for audit and caching.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8056",
    "mcp": "http://localhost:8156"
  }
}
```

### 9.3 Config Files

**`strategy.config.json`**:
```json
{
  "defaultLiteLLMModel": "ollama/llama3.2",
  "liteLLMApiBase": "http://localhost:11434",
  "inferenceTraceStorage": "brain.reasoning",
  "reusableTraceMinConfidence": 0.85,
  "planMaxSteps": 10,
  "conflictResolutionMaxChains": 3,
  "tracesPerRequestGranularity": "per-request"
}
```

### 9.4 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-reasoning"
version = "0.1.0"
description = "Reasoning module — DSPy logical inference, causal planning, and conflict resolution via LiteLLM."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",
  "dspy-ai>=2.5",
  "litellm>=1.40",
  "guidance>=0.1",
  "pydantic>=2.7",
  "structlog>=24.1",
  "httpx>=0.27",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[chromadb]>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 9.5 `lm_config.py` — LiteLLM Wiring (Mandatory Pattern)

```python
"""
lm_config.py — Configure DSPy to route all LLM calls through LiteLLM.

NEVER call openai, anthropic, or ollama SDKs directly.
All inference must route through dspy.LM configured with a LiteLLM endpoint.
"""
import dspy
from typing import Any


def configure_lm(model: str, api_base: str, **kwargs: Any) -> dspy.LM:
    lm = dspy.LM(model=model, api_base=api_base, **kwargs)
    dspy.configure(lm=lm)
    return lm
```

### 9.6 `signatures.py` — DSPy Typed Signatures

```python
import dspy


class LogicalInference(dspy.Signature):
    """Given a set of premises, derive a logical conclusion with a confidence score."""
    premises: list[str] = dspy.InputField(desc="List of known facts or observations")
    conclusion: str = dspy.OutputField(desc="Derived logical conclusion")
    confidence: float = dspy.OutputField(desc="Confidence score in range [0, 1]")


class CausalPlan(dspy.Signature):
    """Given a goal and current state, produce a step-by-step causal plan."""
    goal: str = dspy.InputField(desc="The desired outcome state")
    current_state: str = dspy.InputField(desc="The current system or world state")
    context: list[str] = dspy.InputField(desc="Retrieved relevant memory items")
    steps: list[str] = dspy.OutputField(desc="Ordered list of causal action steps")
    uncertainty: float = dspy.OutputField(desc="Estimated uncertainty [0, 1]")


class PlanUnderUncertainty(dspy.Signature):
    """Reason-and-act loop for plans where information is incomplete."""
    goal: str = dspy.InputField(desc="The desired outcome")
    partial_info: str = dspy.InputField(desc="Available (possibly incomplete) information")
    thought: str = dspy.OutputField(desc="Step-by-step reasoning trace")
    action: str = dspy.OutputField(desc="Next concrete action to take")


class ConflictResolution(dspy.Signature):
    """Evaluate multiple reasoning chains and select the most coherent conclusion."""
    chains: list[str] = dspy.InputField(desc="Alternative reasoning chains")
    selected: str = dspy.OutputField(desc="The most internally consistent conclusion")
    rationale: str = dspy.OutputField(desc="Why this chain was selected over others")
```

### 9.7 Inference Trace Storage Pattern

Every DSPy call result is stored to `brain.reasoning`:
```python
trace = MemoryItem(
    id=str(uuid4()),
    type="working",
    collectionName="brain.reasoning",
    content=result.conclusion,         # or result.steps, result.action etc.
    structuredData={
        "signature": "LogicalInference",
        "inputs": {"premises": premises},
        "outputs": result.toDict(),
        "confidence": result.confidence
    },
    importanceScore=result.confidence,  # reuse confidence as importance
)
vector_store.write("brain.reasoning", trace)
```

### 9.8 MCP Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `reasoning.infer` | `(premises: list[str]) → InferenceResult` | Logical inference via ChainOfThought |
| `reasoning.plan` | `(goal: str, current_state: str, context: list[str]) → CausalPlan` | Causal action plan |
| `reasoning.deliberate` | `(goal: str, partial_info: str) → DeliberationResult` | ReAct loop for incomplete info |
| `reasoning.resolve_conflict` | `(chains: list[str]) → ConflictResult` | MultiChainComparison |
| `reasoning.get_trace` | `(trace_id: str) → InferenceTrace` | Retrieve stored trace |

### 9.9 A2A Task Handlers

| Task type | Input | Output |
|-----------|-------|--------|
| `infer` | `{premises: list[str], session_id}` | `InferenceResult` |
| `plan` | `{goal, current_state, session_id}` | `CausalPlan` |
| `deliberate` | `{goal, partial_info, session_id}` | `DeliberationResult` |
| `resolve_conflict` | `{chains: list[str]}` | `ConflictResult` |

---

## 10. Cross-Cutting: Consolidation Pipeline

The consolidation pipeline spans §5.1 and §5.2. It is triggered three ways:

| Trigger | Source | Handler |
|---------|--------|---------|
| Session end | Working memory `consolidate_session` A2A task | STM runs SCAN→SCORE→GATE→EMBED→PRUNE |
| STM threshold breach | `brain.short-term-memory` item count > 500 | STM self-trigger |
| Scheduled job | Cron: every 60 minutes | STM dedicated background task |

After STM consolidation promotes items to `brain.episodic-memory`:
- Episodic distillation job runs on its own schedule (every 60 minutes by default).
- Recurring patterns distilled to `brain.long-term-memory`.

The Working Memory module is the **coordinator**. It dispatches to STM via A2A. STM
dispatches to Episodic Memory and LTM via A2A. No direct collection writes between
modules — all cross-module data flows through
[infrastructure/adapters/bridge.ts](../../infrastructure/adapters/src/bridge.ts).

---

## 11. Cross-Cutting: Docker Compose Services

The following services must be added to or verified in `docker-compose.yml`. All
existed after Phase 1/2 except `redis`:

| Service | Image | Port | Required by |
|---------|-------|------|-------------|
| `chromadb` | `chromadb/chroma:latest` | 8000 | All vector store modules |
| `redis` | `redis:7-alpine` | 6379 | §5.2 Short-Term Memory |
| `ollama` | `ollama/ollama:latest` | 11434 | All embedding operations |
| `otel-collector` | as configured | 4318 | Telemetry |

**Action required**: If `redis` is not in `docker-compose.yml`, add it before §5.2
implementation begins. This must be committed as `chore(docker): add redis service for
short-term memory` before §5.2 code is written.

---

## 12. Phase 5 Completion Gate

All of the following must be true before Phase 5 is declared complete:

### 12.1 File Presence

```bash
# Each module has the mandatory contract files
ls modules/group-ii-cognitive-processing/memory/working-memory/{README.md,agent-card.json,pyproject.toml,src/,tests/}
ls modules/group-ii-cognitive-processing/memory/short-term-memory/{README.md,agent-card.json,pyproject.toml,src/,tests/}
ls modules/group-ii-cognitive-processing/memory/long-term-memory/{README.md,agent-card.json,pyproject.toml,src/,tests/}
ls modules/group-ii-cognitive-processing/memory/episodic-memory/{README.md,agent-card.json,pyproject.toml,src/,tests/}
ls modules/group-ii-cognitive-processing/affective/{README.md,agent-card.json,pyproject.toml,src/,tests/}
ls modules/group-ii-cognitive-processing/reasoning/{README.md,agent-card.json,pyproject.toml,src/,tests/}
```

### 12.2 Python Quality Gates (per module)

```bash
# Run from each module directory after uv sync
uv sync && uv run ruff check . && uv run mypy src/ && uv run pytest
```

All must exit 0.

### 12.3 Repo-Wide Gates

```bash
pnpm run lint && pnpm run typecheck
pre-commit run validate-frontmatter --all-files
```

### 12.4 End-to-End Verification

Five integration tests must pass end-to-end:

1. **Consolidation pipeline**: Write item to STM → expire session → verify item promoted
   to `brain.long-term-memory` or `brain.episodic-memory`.
2. **Working memory assembly**: Write 25 items to STM → call `assemble_context` on WM
   → verify returned payload respects `maxItems` cap and `importanceScore` ordering.
3. **Affective boost propagation**: Write item to WM → affective module emits high-value
   `RewardSignal` in same session → verify item's `importanceScore` increased.
4. **Reasoning trace storage**: Call `reasoning.infer` with test premises → verify
   `InferenceTrace` written to `brain.reasoning`.
5. **Seed pipeline**: Clear `brain.long-term-memory` → run `ltm.run_seed_pipeline` →
   verify `brain.long-term-memory` has > 0 items.

### 12.5 Checklist Synchronisation

All §§5.1–5.6 items in `docs/Workplan.md` must be marked `[x]`.

---

## 13. Open Questions Requiring Owner Decision

The following items cannot be resolved without owner input. **Do not implement until
decided.** Record decision in a commit message body or inline code comment.

| # | Question | Options | Blocking |
|---|----------|---------|----------|
| OQ-1 | **Redis vs. Valkey for STM backend** | ✅ **DECIDED**: Redis 7. BSL licence not a concern for this project; simpler Docker setup. | ~~§5.2 start~~ |
| OQ-2 | **Working memory token budget source** | ✅ **DECIDED**: Option (a) — WM counts tokens internally via `tiktoken` for proactive capacity control. | ~~§5.1 start~~ |
| OQ-3 | **Working memory eviction policy** | ✅ **DECIDED**: Compound priority score — exponential decay (half-life 300 s, configurable) + contextual relevance (cosine similarity to current query, weight 0.4) + inverse importanceScore (weight 0.6). No hard timer; eviction only fires on capacity breach. Both weights and half-life in `capacity.config.json`. | ~~§5.1 impl~~ |
| OQ-4 | **Episodic item immutability** | ✅ **DECIDED**: YES — content is frozen at write time. Only `accessCount` and `importanceScore` metadata fields are ever updated post-write. Append-only for full audit trail. | ~~§5.4 start~~ |
| OQ-5 | **Episode granularity** | ✅ **DECIDED**: Option (b) — one A2A task step = one episode. A full multi-step task produces N episodic items bound by `sourceTaskId`. | ~~§5.4 start~~ |
| OQ-6 | **Drive state persistence across sessions** | ✅ **DECIDED**: Stateless — resets to zero at session start for Phase 5. Phase 7 adaptive systems may introduce homeostatic persistence. | ~~§5.5 start~~ |
| OQ-7 | **Conflicting reward signal arbitration** | ✅ **DECIDED**: Normalised-resultant combination — each signal contributes a signed weighted value; raw sum divided by `max(1.0, \|raw_sum\|)` to preserve directionality and allow cancellation. Opposing drives cancel toward 0 (ambivalence); same-direction drives reinforce without exceeding ±1. Per-type weights in `drive.config.json` under `signalWeights`. | ~~§5.5 impl~~ |
| OQ-8 | **DSPy optimiser for Phase 5** | ✅ **DECIDED**: Raw predict only — no DSPy optimiser in Phase 5. Deferred to Phase 7 adaptive systems where labelled data will be available. | ~~§5.6 start~~ |
| OQ-9 | **Reasoning trace granularity** | ✅ **DECIDED**: Per-request default. Configurable via `debugPerStepTraces: true` in `strategy.config.json` to enable per-step traces for debugging without changing code. | ~~§5.6 impl~~ |

---

*All open questions resolved. Implementation underway on `feat/phase-5-cognitive-processing`.*
