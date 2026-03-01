---
id: module-sensory-input
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-02-28
maps-to-modules:
  - modules/group-i-signal-processing/sensory-input
---

# Sensory / Input Layer

> **Neuroanatomy analogy**: [Sensory Cortex](../../../resources/neuroanatomy/sensory-cortex.md)

Multi-modal signal ingestion, normalisation, timestamping, and upward dispatch
for the brAIn framework.  This is the system's boundary with the external
environment — the analogue of the sensory cortex.

---

## Purpose

The Sensory / Input Layer receives raw inputs in any supported modality and
produces canonical **Signal** envelopes (conforming to
`shared/types/signal.schema.json`) for consumption by the Attention & Filtering
Layer.

**What this layer does NOT do:**
- Assign semantic meaning (that is the Perception Layer's job)
- Gate or filter signals by salience (that is the Attention & Filtering Layer)
- Call any LLM or embedding model

---

## Supported Modalities

| Modality | `Signal.type` prefix | Normalisation |
|----------|----------------------|---------------|
| `text` | `text.input` | Coerced to `str`, whitespace-stripped |
| `image` | `image.frame` | `bytes` → base64-encoded string |
| `audio` | `audio.chunk` | `bytes` → base64-encoded string |
| `sensor` | `sensor.reading` | Scalars wrapped in `{"value": …}` |
| `api-event` | `api.event` | Scalars wrapped in `{"value": …}`; dicts passed through |
| `internal` | `internal.signal` | Passed through unchanged |
| `control` | `control.directive` | Passed through unchanged |

---

## Interface

### Python

```python
from endogenai_sensory_input import SignalIngestor, RawInput, Modality

ingestor = SignalIngestor(module_id="sensory-input", instance_id="node-0")
signal = ingestor.ingest(RawInput(modality=Modality.TEXT, payload="Hello world"))
print(signal.id, signal.timestamp, signal.payload)
```

### Signal envelope

All output conforms to `shared/types/signal.schema.json`.  Key fields:

| Field | Description |
|-------|-------------|
| `id` | UUID v4 — globally unique |
| `type` | Modality-derived type string (e.g. `text.input`) |
| `modality` | One of the supported modality enum values |
| `source.moduleId` | `"sensory-input"` |
| `source.layer` | `"sensory-input"` |
| `timestamp` | ISO 8601 UTC — assigned at ingestion |
| `ingestedAt` | ISO 8601 UTC — same as `timestamp` for raw ingestion |
| `payload` | Normalised content |
| `priority` | Integer 0–10 (default 5) |

---

## Configuration

No external service dependencies.  The module runs fully in-process.

| Variable | Default | Description |
|----------|---------|-------------|
| `module_id` | `"sensory-input"` | Canonical module identifier |
| `instance_id` | `None` | Optional multi-instance tag |

---

## MCP + A2A

- **A2A endpoint**: `http://localhost:8100` (`agent-card.json`)
- **MCP endpoint**: `http://localhost:8101`
- Registers capabilities: `mcp-context`, `a2a-task`
- All cross-module communication routes through `infrastructure/adapters/bridge.ts`

---

## Development

```bash
cd modules/group-i-signal-processing/sensory-input
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
```

---

## Deployment

The module is Python-only and runs as a standalone process.  In the local
development stack it is started via `docker compose` alongside the MCP and A2A
infrastructure.

See [docs/guides/adding-a-module.md](../../../docs/guides/adding-a-module.md) for
the full module lifecycle.
