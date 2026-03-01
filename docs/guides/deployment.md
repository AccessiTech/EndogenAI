---
id: guide-deployment
version: 0.2.0
status: active
last-reviewed: 2026-02-28
---

# Deployment

> **Status: active** — Local development stack and Group I module services are documented as of Phase 4. Production
> containerization (Dockerfiles), Kubernetes manifests, and scaling guidance will be expanded in Phase 8.

Containerization, local orchestration, and environment configuration for the EndogenAI framework.

## Local Development — Backing Services

Use Docker Compose to start the backing services (ChromaDB, Ollama, Redis, observability stack):

```bash
docker compose up -d
```

This starts all services that do **not** carry the `modules` profile:

| Service          | Port        | Purpose                      |
| ---------------- | ----------- | ---------------------------- |
| `chromadb`       | 8000        | Vector store (local default) |
| `ollama`         | 11434       | LLM + embedding inference    |
| `redis`          | 6379        | Session / KV store           |
| `otel-collector` | 4317 / 4318 | OpenTelemetry OTLP receiver  |
| `prometheus`     | 9090        | Metrics scraping             |
| `grafana`        | 3000        | Observability dashboards     |

Check service health:

```bash
docker compose ps
curl -f http://localhost:8000/api/v1/heartbeat   # ChromaDB
curl -f http://localhost:11434/api/version       # Ollama
```

---

## Local Development — Module Services (Phase 4+)

Cognitive module services are opt-in via the `modules` compose profile. They are deliberately kept separate from the
backing services so that CI and basic development flows do not require running Python FastAPI processes.

### Start all Group I module services

```bash
docker compose --profile modules up -d
```

### Start a single module service

```bash
docker compose --profile modules up -d sensory-input
```

### Group I port assignments

| Module                | Service name          | Port     | Package               |
| --------------------- | --------------------- | -------- | --------------------- |
| Sensory / Input       | `sensory-input`       | **8101** | `sensory_input`       |
| Attention & Filtering | `attention-filtering` | **8102** | `attention_filtering` |
| Perception            | `perception`          | **8103** | `perception`          |

### Run a module without Docker (local development)

```bash
cd modules/group-i-signal-processing/<module-name>
uv sync
uv run uvicorn <module_pkg>.server:app --host 0.0.0.0 --port <port> --reload
```

---

## Environment Variables

All configurable values are read from environment variables (with `inference.config.json` and `vector-store.config.json`
as file-based defaults that env vars always override).

### Inference

| Variable             | Default                  | Description                                             |
| -------------------- | ------------------------ | ------------------------------------------------------- |
| `INFERENCE_MODEL`    | `llama3.2`               | LiteLLM model string (e.g. `ollama/llama3.2`, `gpt-4o`) |
| `INFERENCE_BASE_URL` | `http://localhost:11434` | Base URL for the inference provider                     |
| `EMBEDDING_MODEL`    | `nomic-embed-text`       | Embedding model name (Ollama default)                   |
| `EMBEDDING_BASE_URL` | `http://localhost:11434` | Base URL for the embedding provider                     |

To switch from local Ollama to a cloud provider, set:

```bash
export INFERENCE_MODEL="gpt-4o"
export INFERENCE_BASE_URL=""   # LiteLLM uses OpenAI defaults when base_url is unset
export OPENAI_API_KEY="sk-..."
```

No code changes are required — all inference routes through LiteLLM.

### Vector store

| Variable      | Default     | Description   |
| ------------- | ----------- | ------------- |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000`      | ChromaDB port |

### MCP / A2A infrastructure

| Variable         | Default                 | Description                      |
| ---------------- | ----------------------- | -------------------------------- |
| `MCP_BROKER_URL` | `http://localhost:3001` | MCP context broker base URL      |
| `A2A_SERVER_URL` | `http://localhost:3002` | A2A task coordination server URL |

---

## Docker

Per-module `Dockerfile` definitions will be added in Phase 8 (`deploy/`). For now, module services in
`docker-compose.yml` use a `build: context:` pointing to the module directory — add a minimal `Dockerfile` alongside the
module's `pyproject.toml`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev
COPY src/ src/
EXPOSE <port>
CMD ["uv", "run", "uvicorn", "<module_pkg>.server:app", "--host", "0.0.0.0", "--port", "<port>"]
```

## Kubernetes

_Kubernetes manifests and HPA configurations to be added in Phase 8._

## Scaling

_Scaling guidance to be added in Phase 8._

## References

- [Getting Started](getting-started.md)
- [Observability Guide](observability.md)
- [Architecture — Module Networking Topology](../architecture.md#module-networking-topology-phase-4)
- [Adding a Module — Step 8](adding-a-module.md#8-add-a-docker-compose-service-entry)
- [Workplan — Phase 8](../Workplan.md#phase-8--application-layer--observability)
