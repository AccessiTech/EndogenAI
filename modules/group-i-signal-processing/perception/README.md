# perception

**Group I — Signal Processing** | Port `8102`

## Purpose

The `perception` module transforms raw `Signal` envelopes into rich perceptual
representations, ready for higher cognitive layers (memory, decision-making).
It sits between `attention-filtering` and the working-memory layer.

### Pipeline stages

| Stage | Description |
|---|---|
| **Feature extraction** | Text: named entities, intent, key phrases via LiteLLM. Image/Audio: pass-through with metadata. |
| **Pattern recognition** | Classifies the signal into a semantic pattern (`question`, `command`, `greeting`, …). |
| **Language understanding** | LiteLLM-driven NLP for the `text` modality. |
| **Multimodal fusion** | Merges concurrent signals from different modalities into a unified `PerceptionResult`. |
| **Embedding** | Upserts the extracted representation into `brain.perception` via `endogenai_vector_store.ChromaAdapter`. |

## Interfaces

| Endpoint | Method | Description |
|---|---|---|
| `POST /perceive` | JSON | Process a Signal, return PerceptionResult |
| `POST /mcp` | JSON | Receive MCPContext wrapping a Signal |
| `POST /a2a` | JSON | Receive A2AMessage with signal data |
| `GET  /health` | — | Liveness probe |
| `GET  /.well-known/agent-card.json` | — | Agent capability card |

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `ENDOGEN_MAX_PAYLOAD_BYTES` | `1048576` | Hard payload size limit |
| `ENDOGEN_MODULE_ID` | `perception` | Module identifier |
| `PERCEPTION_PORT` | `8102` | HTTP listen port |
| `PERCEPTION_HOST` | `0.0.0.0` | HTTP listen host |
| `PERCEPTION_LLM_MODEL` | `ollama/llama3.2` | LiteLLM model string for NLP |
| `PERCEPTION_ENABLE_EMBEDDING` | `false` | Enable ChromaDB embedding (requires ChromaDB + Ollama) |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `OLLAMA_ENDPOINT` | `http://localhost:11434` | Ollama embedding endpoint |

## Running locally

```bash
cd modules/group-i-signal-processing/perception
uv sync
uv run uvicorn perception.server:app --port 8102
```

To enable embedding (requires ChromaDB and Ollama):

```bash
PERCEPTION_ENABLE_EMBEDDING=true uv run uvicorn perception.server:app --port 8102
```

## Running tests

```bash
uv run pytest
```

Tests mock all LiteLLM calls and do not require any external services.
