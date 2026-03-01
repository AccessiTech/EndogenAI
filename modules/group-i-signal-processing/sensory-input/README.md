# sensory-input

**Group I — Signal Processing** | Port `8100`

## Purpose

The `sensory-input` module is the entry point for all external stimuli into the EndogenAI
cognitive pipeline. It accepts raw data across five modalities — **text**, **image**, **audio**,
**api-event**, and **sensor stream** — validates, normalises, timestamps, and wraps each datum
in the canonical [`Signal`](../../../shared/types/signal.schema.json) envelope before dispatching
it upward to the `attention-filtering` layer.

## Interfaces

| Endpoint | Method | Description |
|---|---|---|
| `POST /ingest` | JSON | Direct signal ingestion (IngestRequest → Signal) |
| `POST /mcp` | JSON | Receive MCPContext, extract and emit Signal |
| `POST /a2a` | JSON | Receive A2AMessage, extract and emit Signal |
| `GET /health` | — | Liveness probe |
| `GET /.well-known/agent-card.json` | — | Agent capability card |

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `ENDOGEN_MAX_PAYLOAD_BYTES` | `1048576` (1 MB) | Hard size limit for all inbound payloads |
| `ENDOGEN_MODULE_ID` | `sensory-input` | Module identifier stamped on every Signal |
| `SENSORY_INPUT_PORT` | `8100` | HTTP server listen port |
| `SENSORY_INPUT_HOST` | `0.0.0.0` | HTTP server listen host |

## Signal envelope

Every outbound message is a `Signal` object conforming to
[`signal.schema.json`](../../../shared/types/signal.schema.json):

```json
{
  "id": "<uuid>",
  "type": "text.input",
  "modality": "text",
  "source": { "moduleId": "sensory-input", "layer": "sensory-input" },
  "timestamp": "<iso8601>",
  "ingestedAt": "<iso8601>",
  "payload": "Hello world",
  "priority": 5
}
```

## Running locally

```bash
cd modules/group-i-signal-processing/sensory-input
uv sync
uv run uvicorn sensory_input.server:app --port 8100
```

## Running tests

```bash
uv run pytest
```

## Linting & type-checking

```bash
uv run ruff check .
uv run mypy src/
```
