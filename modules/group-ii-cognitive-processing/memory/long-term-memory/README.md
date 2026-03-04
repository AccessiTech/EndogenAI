# Long-Term Memory

Persistent semantic world model for the EndogenAI cognitive processing stack.

## Purpose

The Long-Term Memory (LTM) module provides durable, importance-gated storage across three complementary backends:

- **Vector store** (`brain.long-term-memory` via ChromaDB/Qdrant) — semantic similarity retrieval.
- **Knowledge graph** (Kuzu/Neo4j) — entity-relationship traversal.
- **SQL store** (SQLite/PostgreSQL) — exact-match structured fact lookup.

### Key Behaviours

- **Importance gate**: only items with `importanceScore ≥ 0.5` are admitted.
- **Reconsolidation**: every retrieval increments `accessCount`, boosts `importanceScore`, and re-embeds if content changed.
- **Boot-time seed pipeline**: if `brain.long-term-memory` is empty at startup, LlamaIndex ingests `resources/static/knowledge/` via frontmatter-aware chunking.

## Interface

### MCP Tools

| Tool | Input | Output |
|------|-------|--------|
| `ltm.write` | `{item: MemoryItem}` | `{item_id: str}` |
| `ltm.query` | `{query, top_k, filters?}` | `{items: list[MemoryItem]}` |
| `ltm.write_fact` | `{fact: SemanticFact}` | `{fact_id: str}` |
| `ltm.query_facts` | `{entity_id}` | `{facts: list[SemanticFact]}` |
| `ltm.write_edge` | `{src, predicate, dst, strength?}` | `{status: "ok"}` |
| `ltm.query_graph` | `{entity_id, depth?}` | `{edges: list[GraphEdge]}` |
| `ltm.run_seed_pipeline` | `{}` | `SeedReport` |

### A2A Task Types

| Task | Input | Output |
|------|-------|--------|
| `write_item` | `{item: MemoryItem}` | `{item_id: str}` |
| `query` | `{query, top_k, filters?}` | `{items: list[MemoryItem]}` |
| `write_fact` | `{fact: SemanticFact}` | `{fact_id: str}` |
| `seed` | `{}` | `SeedReport` |

## Configuration

| File | Purpose |
|------|---------|
| `vector-store.config.json` | ChromaDB connection + production Qdrant override |
| `embedding.config.json` | Ollama embedding model |
| `indexing.config.json` | Importance threshold, chunking strategy, seed path |

## Deployment

```bash
docker compose up -d chromadb ollama
cd modules/group-ii-cognitive-processing/memory/long-term-memory
uv sync
uv run python -m long_term_memory
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
cd modules/group-ii-cognitive-processing/memory/long-term-memory

# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Skip integration tests that require ChromaDB, Qdrant, and Ollama:
SKIP_INTEGRATION_TESTS=1 uv run pytest tests/ -m "not integration" -q
SKIP_CHROMA_TESTS=1 uv run pytest tests/ -m "not integration" -q
SKIP_QDRANT_TESTS=1 uv run pytest tests/ -m "not integration" -q
```

Actual coverage: **81%** (above threshold, 2026-03-03 sweep — see
[workplan §7](../../../../docs/test-upgrade-workplan.md)).

Skip variables:

| Variable | Effect |
|----------|--------|
| `SKIP_INTEGRATION_TESTS=1` | Skips all integration tests (coarse monorepo-wide override) |
| `SKIP_CHROMA_TESTS=1` | Skips ChromaDB-dependent tests |
| `SKIP_QDRANT_TESTS=1` | Skips Qdrant-dependent tests |

Known gaps: `src/reconsolidation.py` (0%, P19), `src/a2a_handler.py` (P09), `src/mcp_tools.py` (P10) — see workplan.
