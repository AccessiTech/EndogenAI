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

| Package | Directo| Package | Directo| Package | Directo| Package | Directo| Package | Direcnf| Package | Directo| PP serv| Package | Directo| Package | Directo| Package | Directo| Package | Direuc| Package | Directo| Package | Directo| Package | Directo| Package | Directo| Package | Dpters| | `| Prastructu| Package | Directo| Package | Directo| Package | Directo| Package | Directo| Packagess| Package | Directo| Package | Directo| Package | Directo| Package | Directo| Pack
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOs the singOOOOOOOOOOOOOOOOOOOOOOOOO---

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

AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAArmance
tttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttDetttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttanctttttttttttttttttttttancttttttttp/` or `a2a/` package.
3. Add the3. Add the3. Add the3. Add the3. Add the3. Add the3te tests: u3. Add the3. Add the3. Add theintegration in `adapters/`.
5. Update the relevant `README.md` and `docs/protocols/` spec.

---

## Dependency Management

- Use `pnpm` for all TypeScript package management — never `npm` or `yarn`.
- Do not edit `pnpm-lock.yaml` by hand — always use `pnpm install` or `pnpm add`.
- Pin dependency versions in `package.json` with exact versions for protocol libraries
  (e.g. `@modelcontextprotocol/sdk`).
