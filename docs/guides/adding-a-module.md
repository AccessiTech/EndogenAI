---
id: guide-adding-a-module
version: 0.1.0
status: stub
last-reviewed: 2026-02-24
---

# Adding a Module

> **Status: stub** — This document will be expanded during Phase 8 (Documentation Completion).

Step-by-step guide for creating a new cognitive module within the EndogenAI framework.

## Overview

Each cognitive module follows a consistent structure and must implement the MCP and A2A interfaces. Modules are organized under `modules/` grouped by cognitive layer.

## Module Structure

```
modules/<group>/<module-name>/
├── src/                  # Module source code
├── tests/                # Unit and integration tests
├── docs/                 # Module-specific documentation
│   ├── README.md         # Module overview
│   └── ...
├── agent-card.json       # A2A agent card (capability advertisement)
├── package.json          # TypeScript package (or pyproject.toml for Python)
└── ...
```

## Steps

_Detailed steps to be added in Phase 8._

1. Identify the cognitive group and module analogy from `brain-structure.md`
2. Scaffold the module directory
3. Author `agent-card.json`
4. Implement MCP + A2A interfaces
5. Wire the vector store adapter
6. Write unit and integration tests
7. Author `docs/README.md`

## References

- [Architecture Overview](../architecture.md)
- [Workplan](../Workplan.md)
- [Brain Structure](../../resources/static/knowledge/brain-structure.md)
