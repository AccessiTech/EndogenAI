# MCP Resource Access Control

## Scopes

| Scope | Description | JWT claim |
|---|---|---|
| `read:public` | No authentication required | — |
| `read:authenticated` | Valid Bearer token required | `scope` contains `read` |
| `subscribe:authenticated` | Valid token + SSE session required | `scope` contains `subscribe` |
| `write:admin` | Admin scope (reserved) | `scope` contains `admin` |

## Application

All entries in `uri-registry.json` carry an `accessControl` array.
This taxonomy is the **forward-looking specification** for Phase 9 security hardening.

> **Note — scope enforcement is not yet active.**
> Scope claim validation is deferred to **Phase 9 Security Hardening**.
> The current `authMiddleware` implementation verifies JWT **signature and expiry only**; it does
> not inspect the `scope` claim. All authenticated requests (`read:authenticated`,
> `subscribe:authenticated`) are permitted as long as the JWT is valid and unexpired.
> `write:admin` endpoints are not yet exposed.
>
> Do not rely on scope-level isolation in Phase 8 deployments.

Public resources (`read:public`) are served without auth middleware.

## brain:// URI Priority Resources (Internals Panel)

The following resources are surfaced in the browser Internals panel (§8.3):

- `brain://group-ii/working-memory/context/current` — working memory context window
- `brain://group-iv/metacognition/confidence/current` — confidence scores
- `brain://group-ii/reasoning/plan/current` — active reasoning plan

These resources require the `subscribe:authenticated` scope for SSE subscription.
