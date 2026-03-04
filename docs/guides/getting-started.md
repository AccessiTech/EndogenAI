---
id: guide-getting-started
version: 0.2.0
status: current
last-reviewed: 2026-03-03
---

# Getting Started

> **Contributors**: once the stack is running, see the [Toolchain Guide](toolchain.md) for linting, type-checking,
> pre-commit hooks, and commit conventions.

---

## Prerequisites

| Tool               | Version | Purpose                                            |
| ------------------ | ------- | -------------------------------------------------- |
| **Node.js**        | ≥ 20    | TypeScript modules, MCP/A2A infrastructure         |
| **pnpm**           | ≥ 9     | Package manager and monorepo workspace runner      |
| **Python**         | ≥ 3.11  | ML and cognitive modules                           |
| **uv**             | latest  | Python package management and virtual environments |
| **Docker**         | ≥ 24    | Local service orchestration                        |
| **Docker Compose** | ≥ 2.20  | Multi-service local stack                          |

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AccessiTech/EndogenAI.git
cd EndogenAI
```

### 2. Install Node.js Dependencies

```bash
pnpm install
```

### 3. Install Python Dependencies

```bash
uv sync --dev
```

### 4. Start the Local Stack

```bash
docker compose up -d
```

This brings up the following services:

| Service            | Port(s)    | Purpose                                   |
| ------------------ | ---------- | ----------------------------------------- |
| **ChromaDB**       | 8000       | Vector store (default for all modules)    |
| **Ollama**         | 11434      | Local LLM inference and embeddings        |
| **Redis**          | 6379       | Short-term memory TTL store               |
| **OTel Collector** | 4317, 4318 | Receives OTLP traces, metrics, and logs   |
| **Prometheus**     | 9090       | Metrics storage and querying              |
| **Grafana**        | 3000       | Dashboards (default login: admin / admin) |

**Phase 8 services** (start these after `docker compose up -d`):

| Service | Port | Purpose |
| --- | --- | --- |
| **MCP server** | 8080 | EndogenAI MCP server (`infrastructure/mcp/`); start with `pnpm dev` from that directory |
| **Hono gateway** | 3001 | BFF API gateway (`apps/default/server/`); start with `pnpm dev` from that directory |
| **Vite client** | 5173 | Browser SPA dev server (`apps/default/client/`); start with `pnpm dev` |

### 4b. Start Phase 8 Services

Copy the gateway environment file, then start each service in a separate terminal:

```bash
# 1. Copy gateway env (first time only)
cp apps/default/server/.env.example apps/default/server/.env

# 2. MCP server (port 8080)
cd infrastructure/mcp && pnpm dev

# 3. Hono gateway (port 3001)
cd apps/default/server && pnpm dev

# 4. Vite dev client (port 5173)
cd apps/default/client && pnpm dev
```

Open the app at **http://localhost:5173**.

**Optional profiles:**

```bash
# Start Keycloak (reference OIDC provider — replaces JWT stub)
docker compose --profile keycloak up -d keycloak

# Start Grafana Tempo (distributed trace waterfall)
docker compose --profile observability-full up -d
```

### 5. Verify Services

```bash
# All containers running?
docker compose ps

# ChromaDB healthy? (v2 API)
curl -f http://localhost:8000/api/v2/heartbeat

# Prometheus healthy?
curl -f http://localhost:9090/-/healthy

# Grafana healthy?
curl -f http://localhost:3000/api/health

# OTel Collector reachable (404 is expected — no root handler)?
curl -o /dev/null -w "%{http_code}" http://localhost:4318

# MCP server healthy?
curl -f http://localhost:8080/health

# Gateway healthy?
curl -f http://localhost:3001/api/health
```

---

## First Run

Phase 8 is complete — the full interface layer is live.

1. Open **http://localhost:5173** in your browser.
2. Click **Login** to go through the PKCE auth flow (JWT stub — no password required in dev).
3. Use the **Chat** tab to send input to the cognitive backbone via the gateway.
4. Use the **Internals** tab to browse agent cards, resource collections, and signal traces.

> For a full end-to-end walkthrough (Sensory Input → Perception → Memory → Executive → Motor Output),
> see the Phase 8 section in [docs/Workplan.md](../Workplan.md).

---

## References

- [Toolchain Guide](toolchain.md) — linting, type-checking, pre-commit, buf, commitlint
- [Agent Fleet Guide](agents.md) — VS Code Copilot agents: what each does, when to use it, typical workflows
- [Architecture Overview](../architecture.md)
- [Observability Guide](observability.md) — Grafana dashboards and telemetry
- [Deployment Guide](deployment.md)
- [Workplan](../Workplan.md)
