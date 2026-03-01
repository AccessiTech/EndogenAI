---
id: guide-adding-a-module
version: 0.2.0
status: active
last-reviewed: 2026-02-28
---

# Adding a Module

> **Status: active** — Phase 1 contracts, Phase 2 MCP/A2A infrastructure, and the first Phase 4 Group I modules are
> live. This guide reflects the full end-to-end module development workflow as of Phase 4.

Step-by-step guide for creating a new cognitive module within the EndogenAI framework.

## Overview

Each cognitive module follows a consistent structure and must implement the MCP and A2A interfaces. Modules are
organized under `modules/` grouped by cognitive layer.

## Module Structure

```
modules/<group>/<module-name>/
├── src/                  # Module source code
├── tests/                # Unit and integration tests
├── docs/
│   └── README.md         # Module overview, inputs/outputs, config reference
├── agent-card.json       # A2A agent identity and capability advertisement
├── package.json          # TypeScript package (or pyproject.toml for Python)
└── ...
```

## Steps

### 1. Identify the cognitive group and module analogy

Consult [`brain-structure.md`](../../resources/static/knowledge/brain-structure.md) and the
[Architecture Overview](../architecture.md) to confirm:

- Which **architectural group** the module belongs to (I–V).
- The **neuroanatomical analogy** the module embodies.
- The cognitive layer enum value (used in `source.layer` of all outbound messages).

### 2. Scaffold the module directory

Create the directory under the appropriate group path. Python modules get a `pyproject.toml`; TypeScript modules get a
`package.json` named `@accessitech/<module-name>`.

### 3. Author `agent-card.json`

Every module acts as an autonomous agent and MUST expose an `agent-card.json`. Minimum required fields (see
[A2A Protocol Guide](../protocols/a2a.md#agent-identity)):

```json
{
  "id": "<module-name>",
  "name": "<Human-readable name>",
  "version": "0.1.0",
  "description": "<One-sentence description of the module's cognitive function>",
  "url": "http://<module-name>:<port>",
  "skills": [],
  "mcp": {
    "accepts": ["<contentType>"],
    "emits": ["<contentType>"],
    "version": "0.1.0"
  }
}
```

### 4. Implement the shared contract interfaces

All modules MUST:

#### Validate inbound messages

Validate every inbound JSON payload against the relevant shared schema **before processing**. See
[Validation Spec](../../shared/utils/validation.md) for language-specific patterns and the boundary validation
checklist.

| Payload type  | Schema to validate against                                                  |
| ------------- | --------------------------------------------------------------------------- |
| MCP envelope  | [`mcp-context.schema.json`](../../shared/schemas/mcp-context.schema.json)   |
| A2A message   | [`a2a-message.schema.json`](../../shared/schemas/a2a-message.schema.json)   |
| A2A task      | [`a2a-task.schema.json`](../../shared/schemas/a2a-task.schema.json)         |
| Signal        | [`signal.schema.json`](../../shared/types/signal.schema.json)               |
| Memory item   | [`memory-item.schema.json`](../../shared/types/memory-item.schema.json)     |
| Reward signal | [`reward-signal.schema.json`](../../shared/types/reward-signal.schema.json) |

#### Emit structured logs

Every log entry MUST be a single JSON object to `stdout` following the canonical format in
[Logging Spec](../../shared/utils/logging.md). Required fields: `timestamp`, `level`, `message`, `service`, `version`.

#### Propagate trace context

Extract `traceparent` from every inbound message, create a child span, and inject the updated `traceparent` into every
outbound message. See [Tracing Spec](../../shared/utils/tracing.md).

#### Emit typed signals (Group I modules)

Inter-layer data transfer MUST use the `Signal` envelope defined in
[`signal.schema.json`](../../shared/types/signal.schema.json). Assign `traceContext` and `timestamp` at ingestion.

#### Use memory items (memory modules)

All memory records MUST conform to [`memory-item.schema.json`](../../shared/types/memory-item.schema.json). The
`collectionName` field MUST use the `brain.<module-name>` naming convention.

### 5. Wire the vector store adapter

The vector store adapter (`shared/vector-store/`) is live as of Phase 1.4. Every module that persists state to a vector
collection **must** use it — never call ChromaDB, Qdrant, or any backend SDK directly.

#### Python modules

```toml
# pyproject.toml — add as a path dependency during local development
[tool.uv.sources]
endogenai-vector-store = { path = "../../../shared/vector-store/python", editable = true }
```

```python
from endogenai_vector_store.chroma import ChromaAdapter
from endogenai_vector_store.models import UpsertRequest, MemoryItem

adapter = ChromaAdapter(host="localhost", port=8000, collection="brain.perception")
await adapter.connect()
await adapter.upsert(UpsertRequest(collection_name="brain.perception", items=[...]))
```

The `collection_name` value **must** match an entry in
[`shared/vector-store/collection-registry.json`](../../shared/vector-store/collection-registry.json). Add new
collections there before implementing — schemas-first rule applies.

#### Embedding

All embedding is handled internally by the adapter via Ollama (`nomic-embed-text` by default). Do not compute vectors
manually. Embedding configuration lives in `vector-store.config.json` at the module root:

```json
{
  "collection": "brain.<module-name>",
  "backend": "chroma",
  "embedding": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "base_url": "http://localhost:11434"
  }
}
```

Override `base_url` via the `EMBEDDING_BASE_URL` environment variable in CI or containerised environments.

### 6. Wire MCP + A2A interfaces

The MCP context backbone and A2A coordination layer are live as of Phase 2 (`infrastructure/mcp/`,
`infrastructure/a2a/`, `infrastructure/adapters/`).

#### Group I (Python-only signal-processing modules)

Group I modules self-host a lightweight **FastAPI + Uvicorn** service. The service exposes two routes:

| Route                          | Method | Description                    |
| ------------------------------ | ------ | ------------------------------ |
| `/.well-known/agent-card.json` | `GET`  | Static `agent-card.json`       |
| `/`                            | `POST` | JSON-RPC 2.0 A2A task endpoint |

The module connects to the MCP broker as an HTTP client (via `httpx`) to publish `MCPContext` messages. It does not
embed the MCP server — the broker runs independently at `infrastructure/mcp/`.

**Minimal FastAPI pattern:**

```python
# src/<module_pkg>/server.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json, pathlib

app = FastAPI()
_AGENT_CARD = json.loads(
    (pathlib.Path(__file__).parent.parent.parent / "agent-card.json").read_text()
)

@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    return JSONResponse(_AGENT_CARD)

@app.post("/")
async def a2a_task(request: dict) -> dict:
    # Validate against a2a-task.schema.json, process, publish MCPContext
    ...
```

**Run locally:**

```bash
cd modules/group-i-signal-processing/<module-name>
uv sync
uv run uvicorn <module_pkg>.server:app --host 0.0.0.0 --port <port> --reload
```

#### MCP registration

On startup, publish a `register_capability` tool call to the MCP broker:

```python
import httpx

async def register_with_mcp(mcp_url: str, module_id: str, layer: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(f"{mcp_url}/tools/call", json={
            "name": "register_capability",
            "arguments": {
                "moduleId": module_id,
                "layer": layer,
                "accepts": ["signal/v1"],
                "emits": ["signal/v1"],
                "version": "0.1.0",
                "url": f"http://{module_id}:<port>"
            }
        })
```

Call this once at application startup (e.g. in a FastAPI `lifespan` context manager).

#### MCP signal dispatch

All outbound signals are published as `MCPContext` envelopes via the broker:

```python
async def publish_signal(broker_url: str, signal: dict, source_module_id: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(f"{broker_url}/tools/call", json={
            "name": "publish_context",
            "arguments": {
                "id": str(uuid.uuid4()),
                "version": "0.1.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": {"moduleId": source_module_id, "layer": "sensory-input"},
                "contentType": "signal/v1",
                "payload": signal
            }
        })
```

See [MCP Protocol Guide](../protocols/mcp.md) and [A2A Protocol Guide](../protocols/a2a.md) for full schemas.

### 7. Provide inference configuration _(modules that call LLMs)_

Modules that require LLM inference (e.g. the Perception Layer's feature extractor) **must** route all inference through
[LiteLLM](https://docs.litellm.ai/). Never call `openai`, `anthropic`, or `ollama` SDKs directly.

All inference is configured via `inference.config.json` at the module root:

```json
{
  "provider": "ollama",
  "model": "llama3.2",
  "base_url": "http://localhost:11434",
  "embedding_model": "nomic-embed-text",
  "embedding_base_url": "http://localhost:11434"
}
```

Override any field via environment variables (`INFERENCE_BASE_URL`, `INFERENCE_MODEL`). The production code should
always read config from file + env — never hardcode model names or URLs.

For testability, implement inference behind a `Protocol`:

```python
from typing import Protocol

class InferencePort(Protocol):
    async def complete(self, prompt: str, system: str = "") -> str: ...

class LiteLLMAdapter:
    def __init__(self, model: str, base_url: str) -> None: ...
    async def complete(self, prompt: str, system: str = "") -> str:
        import litellm
        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
            api_base=self.base_url,
        )
        return response.choices[0].message.content

class StubInferenceAdapter:
    """Use in unit tests — no live service required."""
    async def complete(self, prompt: str, system: str = "") -> str:
        return '{"entities": [], "intent": "test", "topics": ["stub"]}'
```

Inject `InferencePort` into service classes at construction time. Tests pass `StubInferenceAdapter`; production wires
`LiteLLMAdapter` from config.

### 8. Add a `docker-compose` service entry

Every runnable module gets a service entry in [`docker-compose.yml`](../../docker-compose.yml) under the `modules`
profile. This keeps module services opt-in — plain `docker compose up -d` starts only the backing services (ChromaDB,
Ollama, Redis, observability). Module services start only when the profile is requested.

```yaml
# docker-compose.yml — add under services:
<module-name>:
  build:
    context: modules/group-i-signal-processing/<module-name>
    dockerfile: Dockerfile
  restart: unless-stopped
  profiles:
    - modules
  ports:
    - "<port>:<port>"
  environment:
    - MCP_BROKER_URL=http://host.docker.internal:3001
    - CHROMA_HOST=chromadb
    - CHROMA_PORT=8000
    - INFERENCE_BASE_URL=http://ollama:11434
    - INFERENCE_MODEL=llama3.2
    - EMBEDDING_BASE_URL=http://ollama:11434
  depends_on:
    chromadb:
      condition: service_healthy
    ollama:
      condition: service_healthy
```

**Start all module services:**

```bash
docker compose --profile modules up -d
```

See [Deployment Guide](deployment.md) for the full port assignment table and environment variable reference.

### 9. Write unit and integration tests

Follow the two-tier strategy:

| Tier        | Location             | Vector store              | Inference              | Runs always?       |
| ----------- | -------------------- | ------------------------- | ---------------------- | ------------------ |
| Unit        | `tests/unit/`        | Mock `VectorStoreAdapter` | `StubInferenceAdapter` | ✅ yes             |
| Integration | `tests/integration/` | Testcontainers (ChromaDB) | `StubInferenceAdapter` | ✅ requires Docker |

- Unit tests must never require a running service.
- Integration tests use `testcontainers[chromadb]` to spin up a real ChromaDB container (see
  `shared/vector-store/python/pyproject.toml` for the Testcontainers dependency pattern).
- Integration tests for inference **always** use `StubInferenceAdapter` — never call a live model in CI.
- All components MUST have unit tests.
- Integration tests MUST cover at least: valid input, missing required field, trace context propagation, and validation
  rejection.
- Python modules use `pytest`; TypeScript modules use the test runner configured in `turbo.json`.

```bash
# Run all tests for a Python module
cd modules/group-i-signal-processing/<module-name>
uv sync
uv run pytest

# Unit tests only (no Docker required)
uv run pytest tests/unit/

# Integration tests (Docker required)
uv run pytest tests/integration/
```

### 10. Author `docs/README.md`

Every module MUST have a `README.md` that documents:

- Purpose and neuroanatomical analogy
- Inputs (accepted `contentType` values and schemas)
- Outputs (emitted `contentType` values and schemas)
- Vector store collections used
- Configuration reference
- How to run locally
- Links to relevant shared specs

## Boundary Validation Checklist

Before a module is merged, verify:

- [ ] All inbound message types validated against their JSON Schemas
- [ ] Semantic validation rules documented in `README.md`
- [ ] `ENDOGEN_MAX_PAYLOAD_BYTES` limit enforced
- [ ] Prompt injection mitigation applied to all user-originated text fields
- [ ] Validation error logs include `traceId` and structured `error` object
- [ ] No raw validation error details leaked to external callers
- [ ] Unit tests cover: valid input, missing required field, oversized payload, invalid enum

## References

- [Architecture Overview](../architecture.md)
- [MCP Protocol Guide](../protocols/mcp.md)
- [A2A Protocol Guide](../protocols/a2a.md)
- [Logging Spec](../../shared/utils/logging.md)
- [Tracing Spec](../../shared/utils/tracing.md)
- [Validation Spec](../../shared/utils/validation.md)
- [Brain Structure](../../resources/static/knowledge/brain-structure.md)
- [Workplan](../Workplan.md)
