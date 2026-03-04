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
The gateway's `authMiddleware` validates scope claims from the JWT payload.
Public resources (`read:public`) are served without auth middleware.

## brain:// URI Priority Resources (Internals Panel)

The following resources are surfaced in the browser Internals panel (§8.3):

- `brain://group-ii/working-memory/context/current` — working memory context window
- `brain://group-iv/metacognition/confidence/current` — confidence scores
- `brain://group-ii/reasoning/plan/current` — active reasoning plan

These resources require the `subscribe:authenticated` scope for SSE subscription.
