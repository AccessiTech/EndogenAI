---
id: guide-getting-started
version: 0.1.0
status: in-progress
last-reviewed: 2026-02-24
---

# Getting Started

> **Note**: End-to-end first-run walkthrough (with live modules) will be added in Phase 8. This guide covers environment
> setup and bringing up the local service stack.

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

### 5. Verify Services

```bash
# All containers running?
docker compose ps

# Prometheus healthy?
curl -f http://localhost:9090/-/healthy

# Grafana healthy?
curl -f http://localhost:3000/api/health

# OTel Collector reachable (404 is expected — no root handler)?
curl -o /dev/null -w "%{http_code}" http://localhost:4318
```

---

## First Run

_End-to-end walkthrough (Sensory Input → Perception → Memory → Executive → Motor Output) will be added in Phase 8, once
the module stack is operational._

---

## References

- [Toolchain Guide](toolchain.md) — linting, type-checking, pre-commit, buf, commitlint
- [Architecture Overview](../architecture.md)
- [Observability Guide](observability.md) — Grafana dashboards and telemetry
- [Deployment Guide](deployment.md)
- [Workplan](../Workplan.md)
