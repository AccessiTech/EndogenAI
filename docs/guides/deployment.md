---
id: guide-deployment
version: 0.1.0
status: stub
last-reviewed: 2026-02-24
---

# Deployment

> **Status: stub** — This document will be expanded during Phase 8 (Deployment).

Containerization, Kubernetes, and scaling guidance for the EndogenAI framework.

## Local Development

Use Docker Compose to run the full local stack:

```bash
docker compose up -d
```

See `docker-compose.yml` for service definitions: ChromaDB, Ollama, Redis, and the observability stack.

## Docker

_Per-module Dockerfile definitions to be added in Phase 8 (`deploy/`)._

## Kubernetes

_Kubernetes manifests and HPA configurations to be added in Phase 8._

## Scaling

_Scaling guidance to be added in Phase 8._

## References

- [Getting Started](getting-started.md)
- [Observability Guide](observability.md)
- [Workplan — Phase 8](../Workplan.md#phase-8--cross-cutting-security-deployment--documentation)
