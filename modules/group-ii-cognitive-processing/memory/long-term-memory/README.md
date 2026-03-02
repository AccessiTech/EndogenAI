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
