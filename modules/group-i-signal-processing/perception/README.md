---
id: module-perception
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-02-28
maps-to-modules:
  - modules/group-i-signal-processing/perception
---

# Perception Layer

> **Neuroanatomy analogy**: [Association Cortices](../../../resources/neuroanatomy/association-cortices.md)

Feature extraction, pattern recognition, language understanding, multimodal
fusion, and `brain.perception` vector embedding for the brAIn framework.
Analogous to the association cortices — the site where raw signals become
structured semantic representations.

---

## Purpose

The Perception Layer receives **FilteredSignal** envelopes from the Attention &
Filtering Layer and produces **PerceptionResult** objects containing:

- Extracted perceptual features (entities, intent, summary, language)
- A vector embedding stored in the `brain.perception` ChromaDB collection

This is the first layer that assigns **semantic meaning** to incoming signals.
All language understanding is routed through LiteLLM (no direct LLM SDK calls).

---

## Pipeline

```
FilteredSignal
     │
     ▼
Feature Extraction (LiteLLM for text; heuristics for media/sensor)
     │
     ▼
Embedding Text Construction
     │
     ▼
brain.perception ← (upsert via endogenai_vector_store)
     │
     ▼
PerceptionResult
```

---

## Interface

### Python

```python
from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig
from endogenai_perception import PerceptionPipeline

adapter = ChromaAdapter(
    config=ChromaConfig(mode="http", host="localhost", port=8000),
    embedding_config=EmbeddingConfig(
        provider="ollama",
        model="nomic-embed-text",
        base_url="http://localhost:11434",
        dimensions=768,
    ),
)

pipeline = PerceptionPipeline(
    vector_store=adapter,
    llm_model="ollama/llama3.2",
)

result = await pipeline.process(filtered_signal)
print(result.features.intent, result.embedding_id)
```

---

## Configuration

### `pipeline.config.json`

| Key | Default | Description |
|-----|---------|-------------|
| `llm.model` | `ollama/llama3.2` | LiteLLM model string for feature extraction |
| `llm.temperature` | `0.0` | Inference temperature |
| `embed.model` | `ollama/nomic-embed-text` | Embedding model |
| `collection` | `brain.perception` | Vector store collection name |
| `max_payload_chars` | `2000` | Max characters sent to the LLM |

### `vector-store.config.json`

See `shared/vector-store/chroma.config.schema.json` for the full schema.

---

## External Dependencies

| Service | Default address | Required |
|---------|----------------|---------|
| ChromaDB | `http://localhost:8000` | ✅ |
| Ollama | `http://localhost:11434` | ✅ |
| LiteLLM model (`llama3.2`) | via Ollama | ✅ |

Start the full local stack with `docker compose up -d` from the repo root.

---

## MCP + A2A

- **A2A endpoint**: `http://localhost:8104` (`agent-card.json`)
- **MCP endpoint**: `http://localhost:8105`
- Registers capabilities: `mcp-context`, `a2a-task`
- Writes to vector collection: `brain.perception`
- All cross-module communication routes through `infrastructure/adapters/bridge.ts`

---

## Development

```bash
cd modules/group-i-signal-processing/perception
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
```

Tests mock both LiteLLM (`litellm.acompletion`) and the vector store adapter,
so no running services are required for the unit test suite.
