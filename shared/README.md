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

# TypeScript build
pnpm build
```

## Phase 1 Deliverables

See [Workplan — Phase 1](../docs/Workplan.md#phase-1--shared-contracts--vector-store-adapter) for the full list of schemas and types to be authored here.
