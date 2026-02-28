# shared/AGENTS.md

> This file narrows the constraints in the root [AGENTS.md](../AGENTS.md).
> It does not contradict any root constraint — it only adds shared-contract authoring rules.

---

## Purpose

This file governs all AI coding agent activity inside the `shared/` directory:
JSON Schema contracts, Protobuf definitions, shared type definitions, utility specs,
and the vector store adapter.

---

## Schemas-First Gate

**No implementation may reference a new shared contract until the contract file exists in
`shared/schemas/` or `shared/types/` and passes all validation.**

Order of operations:
1. Author the JSON Schema or Protobuf in `shared/schemas/` — commit it.
2. Run validation (see below) — it must exit 0.
3. Only then implement consumer code.

Violating this order creates drift between contracts and implementation that is hard to detect or fix.

---

## JSON Schema Requirements

Every `.schema.json` file in `shared/schemas/`, `shared/types/`, and `shared/vector-store/` must include:

| Key | Required | Description | Example |
|-----|----------|-------------|---------|
| `$schema` | yes | JSON Schema draft version | `"https://json-schema.org/draft/2020-12/schema"` |
| `$id` | yes | Unique URI identifying this schema | `"https://endogenai.local/schemas/signal"` |
| `title` | yes | Human-readable name | `"Signal Envelope"` |
| `description` | yes | Purpose of the schema | `"Wraps a signal for routing"` |
| `type` | yes | Root JSON type | `"object"` |

Missing any of these keys will cause a validation error caught by `scripts/schema/validate_all_schemas.py`.

### Protobuf Conventions

- `.proto` files live under `shared/schemas/proto/`.
- `cd shared && buf lint` must exit 0 before any Protobuf change is committed.
- `buf.yaml` and `buf.gen.yaml` govern lint rules and code generation config — do not edit without understanding downstream impact.
- Message names use `PascalCase`; field names use `snake_case`; enum values use `SCREAMING_SNAKE_CASE`.

### Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| JSON Schema files | `kebab-case.schema.json` | `memory-item.schema.json` |
| Protobuf files | `snake_case.proto` | `signal_envelope.proto` |
| Schema `$id` URIs | `https://endogenai.local/schemas/<name>` | `https://endogenai.local/schemas/signal` |
| Collection names | `brain.<module-name>` (lowercase, hyphenated) | `brain.short-term-memory` |

---

## Lockfile Guardrails

- **Never hand-edit `pnpm-lock.yaml` or `uv.lock`** — always use `pnpm install`/`pnpm add` or `uv sync`/`uv add` instead.
- To remove a dependency: `pnpm remove <pkg>` or `uv remove <pkg>` — same rule.

---

## vector-store Constraints

The `shared/vector-store/` adapter is the **only** permitted entry point to vector storage.

- Python: import from `endogenai_vector_store` — never from `chromadb`, `qdrant_client`, or
  `psycopg2` directly in module or infrastructure code.
- TypeScript: import from `@endogenai/vector-store` — never from the backend SDK directly.

---

## Verification Gate

```bash
# JSON Schema validation
uv run python scripts/schema/validate_all_schemas.py

# Protobuf linting
cd shared && buf lint

# Vector store adapters
cd shared/vector-store/python && uv run ruff check . && uv run mypy src/ && uv run pytest
(cd shared/vector-store/typescript && pnpm run test)
```
