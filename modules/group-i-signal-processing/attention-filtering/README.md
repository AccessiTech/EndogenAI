# attention-filtering

**Group I — Signal Processing** | Port `8101`

## Purpose

The `attention-filtering` module acts as the brain's gating mechanism.  Every
`Signal` emitted by `sensory-input` passes through here before reaching the
higher cognitive layers.  The module performs three core functions:

1. **Salience scoring** — assigns a float score `[0.0, 1.0]` to each signal
   based on its `priority`, `modality`, and `type`.
2. **Relevance filtering** — drops signals whose score falls below a
   configurable threshold (default `0.3`).
3. **Signal routing** — forwards accepted signals to downstream module URLs
   based on routing rules keyed by `(modality, type_prefix)`.

A fourth operation — **top-down attention modulation** — allows higher layers
to send `attention.directive` control signals that update the scoring weights,
threshold, and routing table at runtime, without a service restart.

## Interfaces

| Endpoint | Method | Description |
|---|---|---|
| `POST /filter` | JSON | Score, filter, and route a Signal |
| `POST /mcp` | JSON | Receive MCPContext wrapping a Signal |
| `POST /a2a` | JSON | Receive A2AMessage with signal data |
| `GET  /state` | JSON | Inspect current threshold and routing table |
| `GET  /health` | — | Liveness probe |
| `GET  /.well-known/agent-card.json` | — | Agent capability card |

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `ENDOGEN_MAX_PAYLOAD_BYTES` | `1048576` | Hard payload size limit |
| `ENDOGEN_MODULE_ID` | `attention-filtering` | Module identifier |
| `ATTENTION_FILTERING_PORT` | `8101` | HTTP listen port |
| `ATTENTION_FILTERING_HOST` | `0.0.0.0` | HTTP listen host |
| `ATTENTION_THRESHOLD` | `0.3` | Minimum salience score to pass |

## Salience scoring

```
score = 0.4 * (priority / 10.0)
      + 0.3 * modality_weight[modality]
      + 0.3 * type_weight[type_prefix]
```

Modality weights: `control=1.0`, `text=0.8`, `image=0.7`, `audio=0.7`,
`api-event=0.6`, `sensor=0.5`, `internal=0.4`.

## Attention directives

Send a `Signal` with `type="attention.directive"` and `payload` as a JSON
object to update the module state:

```json
{
  "threshold": 0.5,
  "modality_weights": { "text": 0.9 },
  "routing": { "text": "http://my-perception:8102/ingest" }
}
```

## Running locally

```bash
cd modules/group-i-signal-processing/attention-filtering
uv sync
uv run uvicorn attention_filtering.server:app --port 8101
```

## Running tests

```bash
uv run pytest
```
