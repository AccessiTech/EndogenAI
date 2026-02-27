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

| Key || Key || Key || K Ex| Key || Key || Key || K Ex| Key || Key || Key || K Ex| Key || Key || aft U| Key || Key || Key || K Ex| Key || Key || Key || K Ex| Key || Key || Key || K Ex| Key |identifying this schema || Key || Key || Key || K Ex| Key || Key || Key || K Ex| Key || Key || Key ||  s| Key || Key || Key || K Ex| Key || Key || Key || K Ex| Key || Key || Keject"` |

MisMisMisMisMisMisMisMisMisMisMvalMdation error caught by `scrMisMisMisMisMisMisMisMisMisMisMvalMdation error caught by `scrMisMisMisMisMisMisMisMisto` files live under `shared/schemas/proto/`.
- `cd shared && buf lint` must exit 0 before any Protobuf change is committed.
- `buf.yaml` and `buf.gen.yaml` govern li- `buf.yaml` and `buf.gen.yaml` govern li- `bufm w- `buf.yaml` and `buf.gen.yaml` gt` and- `buf.yaml` and `buf.gen.yaml` govern li- `buf.yaml` and `buf.gen.yaml` govern li- `bufm w- `buf.s use `Pasc- `buf.yaml` and `buf.genConv- `buf.yaml` and `buf.gen.yaml` govern li- `buf.yaml` and `buf.gen.yaml` govern li- `bufm w- `buf.yaml`kebab-case.schema.json` | `memory-item.schema.json` |
| Protobuf files | `snake_case.proto` | `signal_envelope.proto` |
| Schema `$id` URIs | `https://endogenai.local/schemas/<name>` | `https://endogenai.local/schemas/signal` |
| Collection names | `brain.<module-name>` (lowercase, hyphenated) | `brain.short-term-memory` |

---

## Lockfile Guardrails

- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never h commit - **Never hand-edit `pnpm- **Never hand-edit `pnpm- **Never hand-edit `pnpm-: `pnpm remove <pkg>` or `uv remove <pkg>` — same rule.

---

## vector-store Constraints

The `shared/vector-store/` adapter is the **only** permitted entry point to vector storage.

- Python: import from `endogenai_vector_store` — never from `chromadb`, `qdrant_client`, or
  `psycopg2` directly in module or infrastructure code.
- TypeScript: import from `@endogenai/vector-store` — never from the backend SDK directly.- TypeScript: import from `@endogenai/vector-store` — nevg.schem- TypeScript: import from `@endogenai/vector-store` — never from the backend SDK directly.- TypeScripd (4)- TypeScript: import from `@endogenai/vector-store` — never from the backend SDK directly.ema validat- TypeScript: imporcripts/schema/validate_all_schemas.py

# Protobuf linting
cd shared && buf lint

# Vector store adapters
cd shared/vector-store/python && uv run ruff check . && uv run mypy src/ && uv run pytest
(cd shared/vector-store/typescript && pnpm run test)
```
