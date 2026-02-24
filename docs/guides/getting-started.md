---
id: guide-getting-started
version: 0.1.0
status: stub
last-reviewed: 2026-02-24
---

# Getting Started

> **Status: stub** — This document will be expanded during Phase 8 (Documentation Completion).

Environment setup and first-run walkthrough for the EndogenAI framework.

## Prerequisites

- **Node.js** >= 20.0.0
- **pnpm** >= 9.0.0
- **Python** >= 3.11
- **Docker** and **Docker Compose**
- **buf** CLI (for Protobuf/schema management)

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
uv sync
```

### 4. Start the Local Stack

```bash
docker compose up -d
```

This brings up ChromaDB, Ollama, Redis, and the observability stack (OpenTelemetry, Prometheus, Grafana).

## First Run

_End-to-end first-run walkthrough to be added in Phase 8._

## References

- [Architecture Overview](../architecture.md)
- [Workplan](../Workplan.md)
- [Deployment Guide](deployment.md)
