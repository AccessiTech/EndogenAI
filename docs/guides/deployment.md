---
id: guide-deployment
version: 0.4.0
status: active
last-reviewed: 2026-03-04
---

# Deployment

> **Status: active** — Local development stack (Phase 4), Phase 8 application services, and Phase 9 production
> deployment (Docker base images, Kubernetes manifests, `security` Compose profile) are all documented here.
> Phase 9 deployment implementation is in progress (§§9.1–9.2).

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
curl -f http://localhost:8000/api/v2/heartbeat   # ChromaDB
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

| Module                | Service name          | Port     | Package                           |
| --------------------- | --------------------- | -------- | --------------------------------- |
| Sensory / Input       | `sensory-input`       | **8101** | `endogenai_sensory_input`         |
| Attention & Filtering | `attention-filtering` | **8102** | `endogenai_attention_filtering`   |
| Perception            | `perception`          | **8103** | `endogenai_perception`            |

### Run a module without Docker (local development)

```bash
cd modules/group-i-signal-processing/<module-name>
uv sync
uv run uvicorn <module_pkg>.server:app --host 0.0.0.0 --port <port> --reload
```

---

## Phase 8 Application Services

The Phase 8 application layer adds two TypeScript services that sit in front of the MCP infrastructure:

| Service            | Package                   | Port | Start command         |
| ------------------ | ------------------------- | ---- | --------------------- |
| Hono API Gateway   | `apps/default/server`     | 3001 | `pnpm run dev` (dev)  |
| Vite browser client | `apps/default/client`    | 5173 | `pnpm run dev` (dev)  |

### Development

```bash
# From repo root — starts both services via Turborepo
pnpm run dev
```

The gateway at `http://localhost:3001` proxies MCP context requests, serves authenticated SSE streams, and exposes
the `brain://` resource registry at `GET /api/resources`. The Vite client at `http://localhost:5173` provides the
browser shell with OAuth 2.1 + PKCE authentication against the gateway.

### Production build

```bash
pnpm run build
# Gateway: apps/default/server/dist/
# Client:  apps/default/client/dist/ (static assets served by the gateway via Hono serveStatic)
```

The gateway serves the compiled client bundle from `apps/default/client/dist/` at the root path (`/`); no
separate static file server is required in production.

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

<!-- Phase 9 addition — 2026-03-04 -->
## Phase 9 Production Deployment

Phase 9 adds production-grade container images, Kubernetes manifests, and OPA security enforcement. The Phase 9
deployment layer packages all 16 services for production without changing any cognitive module behaviour.

### Service inventory (16 services)

| Service name | Group | Port | Compose profile | K8s namespace |
| --- | --- | --- | --- | --- |
| `sensory-input` | Group I | 8001 | `modules` | `endogenai-modules` |
| `perception` | Group I | 8002 | `modules` | `endogenai-modules` |
| `attention-filtering` | Group I | 8003 | `modules` | `endogenai-modules` |
| `working-memory` | Group II | 8010 | `modules` | `endogenai-modules` |
| `short-term-memory` | Group II | 8011 | `modules` | `endogenai-modules` |
| `long-term-memory` | Group II | 8012 | `modules` | `endogenai-modules` |
| `episodic-memory` | Group II | 8013 | `modules` | `endogenai-modules` |
| `reasoning` | Group II | 8014 | `modules` | `endogenai-modules` |
| `affective` | Group II | 8015 | `modules` | `endogenai-modules` |
| `executive-agent` | Group III | 8020 | `modules` | `endogenai-modules` |
| `agent-runtime` | Group III | 8021 | `modules` | `endogenai-modules` |
| `motor-output` | Group III | 8022 | `modules` | `endogenai-modules` |
| `learning-adaptation` | Group IV | 8030 | `modules` | `endogenai-modules` |
| `metacognition` | Group IV | 8031 | `modules` | `endogenai-modules` |
| `mcp-server` | Infra | 8000 | _(default)_ | `endogenai-infra` |
| `gateway` | Apps | 3001 | _(default)_ | `endogenai-infra` |

### Docker — base images and multi-stage builds

Base Dockerfiles are at `deploy/docker/`:

| File | Purpose |
| --- | --- |
| `deploy/docker/base-python.Dockerfile` | Multi-stage Python 3.11; `nobody` UID 65534; gVisor-compatible (no raw sockets, no `/proc` writes) |
| `deploy/docker/base-node.Dockerfile` | Multi-stage Node.js 20; `nobody` UID 65534; gVisor-compatible |

Each of the 16 services has its own `Dockerfile` referencing the appropriate base image. Build all images in
dependency order:

```bash
bash scripts/build_images.sh
```

Supported flags:

| Flag | Purpose |
| --- | --- |
| `--push` | Push all built images to the registry |
| `--skip-base` | Skip rebuilding base images (faster incremental builds) |
| `IMAGE_TAG=<tag>` | Override the image tag (default: `latest`) |

### Compose — OPA security profile

OPA policy enforcement is opt-in via the `security` profile (backwards-compatible; existing profiles unchanged):

```bash
# Start all modules + OPA policy server
docker compose --profile modules --profile security up -d

# Start OPA alone (for policy development)
docker compose --profile security up -d opa

# Verify Compose config (no syntax errors)
docker compose config
```

A `docker-compose.override.yml` is provided for local development (hot-reload volumes; `runtimeClassName: runsc`
disabled for macOS Docker Desktop).

### Kubernetes prerequisites

Before applying manifests to a cluster:

| Prerequisite | Notes |
| --- | --- |
| NetworkPolicy-compatible CNI | Calico or Cilium required (Flannel does not enforce `NetworkPolicy`) |
| gVisor node pool (production) | Nodes must have `runsc` installed; `RuntimeClass` applied from `deploy/k8s/runtime-class-gvisor.yaml` |
| gVisor not required (macOS dev) | Use `kind` or `minikube` with standard `runc` for local cluster testing |

### Kubernetes manifests (`deploy/k8s/`)

```
deploy/k8s/
  namespace.yaml                      # endogenai-modules + endogenai-infra namespaces
  runtime-class-gvisor.yaml           # gVisor RuntimeClass (production)
  network-policy-default-deny.yaml    # Default-deny NetworkPolicy backdrop
  <module>/
    deployment.yaml                   # Non-root securityContext, runtimeClassName, resource limits
    service.yaml                      # ClusterIP service
    hpa.yaml                          # HPA (70% CPU threshold)
    network-policy.yaml               # Per-module allow-list
```

All pod specs include:
- `securityContext.runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`
- `capabilities.drop: [ALL]`, `seccompProfile.type: RuntimeDefault`
- `runtimeClassName: gvisor` (production; omit for macOS dev)

High-availability services with `minReplicas: 2`: `working-memory`, `executive-agent`, `agent-runtime`, `gateway`.
All others default to `minReplicas: 1` with HPA at 70% CPU.

### M9 deployment verification

```bash
# Dry-run all K8s manifests (requires kubectl)
kubectl apply --dry-run=client -R -f deploy/k8s/

# Validate Compose config
docker compose config

# Start full local stack (modules + security profile)
docker compose --profile modules --profile security up -d

# Health check all services
bash scripts/healthcheck.sh
```

---

## Docker

Per-module `Dockerfile` files follow the multi-stage, non-root pattern defined in `deploy/docker/` (Phase 9 §9.2).
Each service's `Dockerfile` lives alongside its `pyproject.toml` (Python) or `package.json` (TypeScript) and
references the shared base image:

```dockerfile
# Python module (14 modules)
FROM endogenai/base-python:3.11
WORKDIR /app
COPY --chown=nobody:nobody pyproject.toml uv.lock ./
RUN uv sync --no-dev
COPY --chown=nobody:nobody src/ src/
USER nobody
EXPOSE <port>
CMD ["uv", "run", "uvicorn", "<module_pkg>.server:app", "--host", "0.0.0.0", "--port", "<port>"]
```

Key constraints (gVisor compatibility and security hardening):
- Non-root user (`nobody` UID 65534)
- No writes to `/proc`; use `emptyDir` tmpfs for scratch space
- No raw socket creation (`AF_PACKET`, `CAP_NET_RAW`)
- `readOnlyRootFilesystem`-compatible

Add a `.dockerignore` to each module root excluding `.venv/`, `__pycache__/`, `node_modules/`, `dist/`, and `*.pyc`.

## Kubernetes

Kubernetes manifests for all 16 services live in `deploy/k8s/` (Phase 9 §9.2). Each service directory contains
four files: `deployment.yaml`, `service.yaml`, `hpa.yaml`, and `network-policy.yaml`.

Apply all manifests to a cluster:

```bash
# Verify manifests without applying (requires kubectl)
kubectl apply --dry-run=client -R -f deploy/k8s/

# Apply to a cluster
kubectl apply -R -f deploy/k8s/
```

See the [Phase 9 additions](#phase-9-production-deployment) section above for prerequisites (CNI, gVisor node pool)
and the full service inventory.

> **gVisor note**: `runtimeClassName: gvisor` is applied in all production `Deployment` manifests. For macOS
> local cluster development (e.g. `kind`, `minikube`), remove or comment out `runtimeClassName` from pod specs
> — the `RuntimeClass` is not available on macOS Docker Desktop.

## Scaling

All 16 services have Kubernetes `HorizontalPodAutoscaler` (HPA) manifests in `deploy/k8s/<service>/hpa.yaml`
(Phase 9 §9.2). The scaling policy is:

| Service | `minReplicas` | `maxReplicas` | CPU target |
| --- | --- | --- | --- |
| `working-memory` | 2 | 8 | 70% |
| `executive-agent` | 2 | 6 | 70% |
| `agent-runtime` | 2 | 8 | 70% |
| `gateway` | 2 | 10 | 70% |
| All other services | 1 | 4 | 70% |

All services respect `resources.requests` and `resources.limits` in their `Deployment` spec; see individual
manifests for values. Anti-affinity rules are applied to high-availability services to spread replicas across nodes.

## References

- [Getting Started](getting-started.md)
- [Security Guide](security.md) — OPA, gVisor, mTLS, Trivy
- [Observability Guide](observability.md)
- [Toolchain Guide](toolchain.md) — `build_images.sh`, `gen_certs.sh`, `gen_opa_data.py` commands
- [Architecture — Module Networking Topology](../architecture.md#module-networking-topology-phase-4)
- [Adding a Module — Step 8](adding-a-module.md#8-add-a-docker-compose-service-entry)
- [Workplan — Phase 9](../Workplan.md#phase-9--cross-cutting-security-deployment--documentation)
