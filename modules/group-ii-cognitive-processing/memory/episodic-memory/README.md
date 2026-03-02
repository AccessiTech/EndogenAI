# Episodic Memory

Autobiographical event log for the EndogenAI cognitive processing stack.

## Purpose

The Episodic Memory module implements a hippocampal-inspired ordered event log that:

- Records discrete, temporally ordered events with mandatory **Tulving triple** validation (sessionId, sourceTaskId, createdAt).
- Supports **semantic episode search** with optional session and time-window filters, re-ranked by `importanceScore × |affectiveValence|`.
- Provides **timeline reconstruction** — session-ordered replay of all events.
- Runs periodic **semantic distillation** — clusters recurring episodic patterns and writes decontextualised facts to `brain.long-term-memory`.

## Interface

### MCP Tools

| Tool | Input | Output |
|------|-------|--------|
| `em.write_event` | `{event: MemoryItem}` | `{event_id: str}` |
| `em.search` | `{query, session_id?, time_window_start?, time_window_end?, top_k?}` | `{items: list[MemoryItem]}` |
| `em.get_timeline` | `{session_id}` | `{events: list[MemoryItem]}` |
| `em.run_distillation` | `{}` | `DistillationReport` |

### A2A Task Types

| Task | Input | Output |
|------|-------|--------|
| `write_event` | `{event: MemoryItem}` | `{event_id: str}` |
| `search_episodes` | `{query, session_id?, time_window?}` | `{items: list[MemoryItem]}` |
| `get_timeline` | `{session_id}` | `{events: list[MemoryItem]}` |
| `run_distillation` | `{}` | `DistillationReport` |

## Configuration

| File | Purpose |
|------|---------|
| `vector-store.config.json` | ChromaDB connection |
| `embedding.config.json` | Ollama embedding model |
| `retention.config.json` | Distillation and retention settings |

## Key Behaviours

### Tulving Triple Requirement

Every episodic item **must** carry in `metadata`:
- `session_id` (where)
- `source_task_id` (what)
- `created_at` ISO-8601 (when)

Missing any field raises `ValueError` at write time.

### Immutable Event Log

Events are NEVER modified after initial write. On reconsolidation (retrieval), only `accessCount` and `importanceScore` metadata are updated.

### Semantic Distillation

On `em.run_distillation`: clusters episodic items by similarity, and for clusters ≥ `minClusterSize`, writes a summary `MemoryItem` to `brain.long-term-memory` via LTM's A2A endpoint.

## Deployment

```bash
docker compose up -d chromadb ollama
cd modules/group-ii-cognitive-processing/memory/episodic-memory
uv sync
uv run python -m episodic_memory
```

## Development

```bash
uv run ruff check .
uv run mypy src/
uv run pytest
```
