# shared

Shared schemas, types, and utilities consumed by all EndogenAI modules and infrastructure packages.

## Structure

```
shared/
├── buf.yaml           # buf module definition (Protobuf/JSON Schema management)
├── buf.gen.yaml       # buf code generation config
├── schemas/           # JSON Schema definitions for MCP and A2A contracts
├── types/             # Shared type schemas (signal, memory-item, reward-signal)
├── utils/             # Specification documents for logging, tracing, validation
└── vector-store/      # Vector store adapter interface and configuration schemas
```

## Toolchain

- **buf** — Protobuf and JSON Schema management; run `buf lint` and `buf generate` from this directory
- **TypeScript** — shared type packages consumed by infrastructure and application packages
- **Python** — generated Python types consumed by ML/cognitive modules

## Usage

```bash
# Lint Protobuf definitions
buf lint

# Generate code from Protobuf definitions
buf generate

# TypeScript build (available in Phase 1 once codegen is wired up)
# pnpm build
```

## Schemas (`shared/schemas/`)

Canonical contracts for all backbone messages. Every module MUST validate inbound payloads against these schemas.

| File                                                         | Description                                                |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| [`mcp-context.schema.json`](schemas/mcp-context.schema.json) | MCP context envelope — all inter-module messages           |
| [`a2a-message.schema.json`](schemas/a2a-message.schema.json) | A2A message parts (text, data, file, function call/result) |
| [`a2a-task.schema.json`](schemas/a2a-task.schema.json)       | A2A task lifecycle, artifacts, state machine, and errors   |

## Types (`shared/types/`)

Shared data structures consumed by every cognitive module.

| File                                                           | Description                                                    |
| -------------------------------------------------------------- | -------------------------------------------------------------- |
| [`signal.schema.json`](types/signal.schema.json)               | Universal inter-layer signal envelope                          |
| [`memory-item.schema.json`](types/memory-item.schema.json)     | Unified memory record (all timescales, all vector collections) |
| [`reward-signal.schema.json`](types/reward-signal.schema.json) | Affective / motivational reward signal                         |

## Utils (`shared/utils/`)

Specification documents that define system-wide conventions all modules must follow.

| File                                   | Description                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------------ |
| [`logging.md`](utils/logging.md)       | Structured JSON log format, required fields, severity levels, library guidance |
| [`tracing.md`](utils/tracing.md)       | W3C TraceContext propagation, span lifecycle, sampling policy                  |
| [`validation.md`](utils/validation.md) | Boundary validation, sanitization patterns, LLM output validation, size limits |

## Vector Store (`shared/vector-store/`)

_Phase 1.4 — adapter interface, configuration schemas, and ChromaDB/Qdrant implementations coming next._

## Phase Status

| Section                  | Status         |
| ------------------------ | -------------- |
| 1.1 Shared Schemas       | ✅ Complete    |
| 1.2 Shared Types         | ✅ Complete    |
| 1.3 Shared Utils         | ✅ Complete    |
| 1.4 Vector Store Adapter | 🔲 In progress |

See [Workplan — Phase 1](../docs/Workplan.md#phase-1--shared-contracts--vector-store-adapter) for full detail.
