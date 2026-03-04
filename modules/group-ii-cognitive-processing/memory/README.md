---
id: module-memory
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-03-02
maps-to-modules:
  - modules/group-ii-cognitive-processing/memory/working-memory
  - modules/group-ii-cognitive-processing/memory/short-term-memory
  - modules/group-ii-cognitive-processing/memory/long-term-memory
  - modules/group-ii-cognitive-processing/memory/episodic-memory
---

# Memory Layer

> **Neuroanatomy analogy**: [Hippocampus](../../../resources/neuroanatomy/hippocampus.md)

The Memory Layer is the complete multi-timescale storage and retrieval stack for EndogenAI. Modelled on the hippocampus and its relationships with the prefrontal cortex and neocortex, it provides four complementary memory sub-modules that handle everything from active in-context state to durable autobiographical records.

---

## Purpose

The Memory Layer encodes, consolidates, and retrieves information across four timescales, mirroring the hippocampal distinctions between working state, session-bound experience, persistent world-knowledge, and autobiographical sequence:

- **Working Memory** maintains the minimal active context required for the current reasoning step and enforces inference-budget limits.
- **Short-Term Memory** holds session-scoped recent experience with novelty-gated writes and runs a consolidation pipeline on session expiry.
- **Long-Term Memory** stores importance-gated facts durably across sessions with vector, knowledge-graph, and SQL backends.
- **Episodic Memory** provides a Tulving-validated, temporally ordered autobiographical event log with periodic semantic distillation back to long-term storage.

Together these sub-modules implement the full hippocampal cycle: encode → consolidate → retrieve → reconsolidate.

---

## Sub-modules

| Sub-module | Brain Region Analogy | A2A Port | MCP Port | ChromaDB Collection | README |
|---|---|---|---|---|---|
| `working-memory` | Dorsolateral PFC — active context maintenance | 8051 | 8151 | `brain.working-memory` | [README](working-memory/README.md) |
| `short-term-memory` | Hippocampus CA1/CA3 — session buffer, novelty detection | 8052 | 8152 | `brain.short-term-memory` | [README](short-term-memory/README.md) |
| `long-term-memory` | Neocortex + Hippocampus — semantic world model | 8053 | 8153 | `brain.long-term-memory` | [README](long-term-memory/README.md) |
| `episodic-memory` | Hippocampus + Entorhinal Cortex — event log | 8054 | 8154 | `brain.episodic-memory` | [README](episodic-memory/README.md) |

---

## Consolidation Flow

Memory items flow through the stack in one direction (encode → consolidate) and are retrieved up through it:

```
External signal / Working Memory write
        │
        ▼
Short-Term Memory  ──(session expiry consolidation)──►  Long-Term Memory
        │                                                      ▲
        └──────────────(episodic events)──────────►  Episodic Memory
                                                           │
                                            (semantic distillation)
                                                           │
                                                           ▼
                                                  Long-Term Memory
```

- **STM → LTM**: Items with `importanceScore ≥ 0.5` are promoted on session expiry.
- **STM → Episodic**: All session events are logged as ordered episodes.
- **Episodic → LTM**: Periodic distillation clusters recurring patterns into decontextualised facts.
- **Working Memory** reads from STM, LTM, and Episodic via a three-source hybrid retrieval pattern.

---

## Shared Contract

All sub-modules read and write the canonical `MemoryItem` schema:

```
shared/types/memory-item.schema.json
```

Embeddings use `nomic-embed-text` via Ollama (local) or the shared vector-store adapter's configured backend. No sub-module calls ChromaDB or Qdrant directly — all access routes through `endogenai_vector_store`.

---

## Development

Each sub-module manages its own `uv`-based virtual environment:

```bash
# Working Memory
cd modules/group-ii-cognitive-processing/memory/working-memory
uv sync && uv run pytest

# Short-Term Memory
cd modules/group-ii-cognitive-processing/memory/short-term-memory
uv sync && uv run pytest

# Long-Term Memory
cd modules/group-ii-cognitive-processing/memory/long-term-memory
uv sync && uv run pytest

# Episodic Memory
cd modules/group-ii-cognitive-processing/memory/episodic-memory
uv sync && uv run pytest
```

Integration tests require ChromaDB and Ollama to be running:

```bash
docker compose up -d
ollama pull nomic-embed-text
uv run pytest tests/ -m integration -q
```

## Testing

Framework: **pytest**. Coverage threshold: **80%** (enforce with `pytest-cov` per sub-module — see P05).

```bash
# With coverage (run from the specific sub-module directory)
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Skip integration tests:
SKIP_INTEGRATION_TESTS=1 uv run pytest tests/ -m "not integration" -q
```

Estimated coverage by sub-module (all MEDIUM gap, target 80%):
- `working-memory` ~75% — missing `instrumentation/otel_setup.py` (P11)
- `short-term-memory` ~65% — missing `a2a_handler.py` (P09), `mcp_tools.py` (P10)
- `long-term-memory` ~60% — missing `reconsolidation.py` (0%, P19), `a2a_handler.py` (P09), `mcp_tools.py` (P10)
- `episodic-memory` ~65% — missing `a2a_handler.py` (P09), `mcp_tools.py` (P10)

See [`docs/test-upgrade-workplan.md`](../../../docs/test-upgrade-workplan.md) for full detail.

---

## See Also

- [Hippocampus neuroanatomy stub](../../../resources/neuroanatomy/hippocampus.md)
- [Shared `MemoryItem` schema](../../../shared/types/memory-item.schema.json)
- [Vector store adapter](../../../shared/vector-store/README.md)
- [Phase 5 workplan](../../../docs/Workplan.md)
