# @endogenai/gateway

Hono BFF gateway with OAuth 2.1 / PKCE auth stub for EndogenAI Phase 8.

This package forms the **blood–brain barrier analogue**: public endpoints
(`/.well-known/*`, `/auth/*`, `GET /api/health`) pass freely; all other
`/api/*` routes require a valid Bearer JWT issued by this server.

---

## Quick Start

```bash
cp .env.example .env          # copy env template
pnpm install
pnpm dev                      # tsx watch — hot reload on http://localhost:3001
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3001` | HTTP listen port |
| `MCP_SERVER_URL` | `http://localhost:8000` | Upstream MCP server base URL |
| `MCP_SERVER_URI` | `http://localhost:8000` | JWT `aud` claim value (RFC 8707) |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins |
| `ISSUER_URL` | `http://localhost:3001` | OAuth 2.0 issuer base URL |
| `JWT_SECRET` | `change-me-in-production` | HS256 signing secret — **change in prod** |
| `JWT_EXPIRY_SECONDS` | `900` | Access token lifetime (15 min) |
| `REFRESH_TOKEN_EXPIRY_SECONDS` | `86400` | Refresh token lifetime (24 h) |
| `LOG_LEVEL` | `info` | Pino log level |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTel OTLP endpoint |
| `OTEL_SERVICE_NAME` | `hono-gateway` | OTel service name |

---

## Auth Flow (PKCE / OAuth 2.1)

```
Browser                        Gateway (/auth/*)          MCP Server
  │                                │                           │
  │── GET /auth/authorize ────────▶│                           │
  │   ?code_challenge=<S256>       │                           │
  │◀─ 302 redirect ───────────────│                           │
  │   ?code=<opaque>               │                           │
  │                                │                           │
  │── POST /auth/token ───────────▶│                           │
  │   code_verifier=<raw>          │ signAccessToken()         │
  │◀─ { access_token, ... } ──────│ Set-Cookie: refresh_token │
  │   + HttpOnly refresh cookie    │                           │
  │                                │                           │
  │── POST /api/input ────────────────────────────────────────▶│
  │   Authorization: Bearer <JWT>  │ authMiddleware checks JWT │
```

- Access tokens are stored **in memory only** (never `localStorage`).
- Refresh tokens are stored in `HttpOnly; SameSite=Strict` cookies only.
- PKCE code verifiers use `crypto.randomBytes(32)` — never `Math.random()`.
- Auth codes expire after **60 seconds**.
- Refresh token rotation invalidates the previous token on every use
  (replay-attack protection).

---

## Keycloak (Optional — Production OIDC)

The file `src/auth/keycloak/realm.json` is a Keycloak realm import stub for
the `endogenai` realm. To enable:

1. Add the `keycloak` profile to `docker-compose.yml` and mount `realm.json`.
2. Set `ISSUER_URL` to the Keycloak issuer (e.g.
   `http://localhost:8080/realms/endogenai`).
3. Replace `signAccessToken` / `verifyAccessToken` delegates with
   `jose`-based JWKS verification against Keycloak's JWKS endpoint.

The stub client ID `apps-default-browser` matches the Keycloak client
configuration in `realm.json` — no name changes required.

---

## Extension Points

- **§8.1 — Hono Gateway**: full MCP relay routes mounted under `/api/mcp/`.
- **§8.4 — OTel**: replace the `initTelemetry()` stub with the full
  `NodeSDK` setup wired to the OTLP exporter.
- **RFC 7591 Dynamic Client Registration**: `sessions.ts` documents the
  hardcoded `client_id` as the extension point.

---

## Tests

```bash
pnpm test           # vitest run
pnpm typecheck      # tsc --noEmit
```
