# infrastructure/AGENTS.md

> This file narrows the constraints in the root [AGENTS.md](../AGENTS.md).
> It does not contradict any root constraint — it only adds infrastructure-specific rules.

---

## Purpose

This file governs all AI coding agent activity inside the `infrastructure/` directory:
the MCP context backbone (`mcp/`), A2A coordination layer (`a2a/`), and the adapter
bridge (`adapters/`) that lets modules participate in both protocols.

---

## TypeScript-Only Constraint

**All source code in `infrastructure/` is TypeScript.** No Python files belong here.

- Runtime: Node.js via `pnpm`
- Type checking: `pnpm run typecheck` (runs `tsc --noEmit` per package)
- Linting: `pnpm run lint` (runs ESLint with the root `eslint.config.js`)
- Tests: `pnpm run test` (runs Vitest per package)

If a task requires Python glue, it belongs in `shared/` or a `modules/` package — not here.

---

## Package Boundaries

| Package | Directory | Responsibility |
|---------|-----------|----------------|
| `mcp` | `infrastructure/mcp/` | MCP server — context exchange backbone |
| `a2a` | `infrastructure/a2a/` | A2A coordination — task delegation between agents |
| `adapters` | `infrastructure/adapters/` | Bridge layer — adapts modules to MCP/A2A protocols |

Each package is an independent `pnpm` workspace member with its own `package.json`, `tsconfig.json`,
and test suite. Changes to one package must not silently break another.

---

## MCP/A2A Conformance Gates

Before any change to `infrastructure/` is committed:

```bash
# Per-package conformance checks
(cd infrastructure/mcp && pnpm run test)
(cd infrastructure/a2a && pnpm run test)
(cd infrastructure/adapters && pnpm run test)

# Full repo checks
pnpm run lint && pnpm run typecheck
```

When adding a new protocol feature or adapter, follow this workflow:

1. Author the schema contract in `shared/schemas/` and land it first.
2. Implement the change in the `mcp/` or `a2a/` package.
3. Add integration tests in `adapters/`.
4. Run all conformance gates (see above) — they must exit 0.
5. Update the relevant `README.md` and `docs/protocols/` spec.

---

## Dependency Management

- Use `pnpm` for all TypeScript package management — never `npm` or `yarn`.
- Do not edit `pnpm-lock.yaml` by hand — always use `pnpm install` or `pnpm add`.
- Pin dependency versions in `package.json` with exact versions for protocol libraries
  (e.g. `@modelcontextprotocol/sdk`).
