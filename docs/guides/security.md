---
id: guide-security
version: 0.2.0
status: current
last-reviewed: 2026-03-04
---

# Security

> **Status: current** — Boundary validation patterns (Phase 1) and OAuth 2.1 authentication layer (Phase 8.2) are
> documented. Module sandboxing and container security are Phase 9 items (§9.1).

Security model, boundary validation, sandboxing policies, and least-privilege patterns.

## Principles

- **Security & Privacy by Design** — security is a first-class concern at every layer boundary
- **Least Privilege** — each module operates with the minimum permissions required
- **Module Sandboxing** — modules are isolated via container-level policies
- **Validate at Every Boundary** — never trust data that crosses a module boundary (see below)

## Boundary Validation (Phase 1)

The canonical input validation and sanitization patterns are defined in
[`shared/utils/validation.md`](../../shared/utils/validation.md).

Key rules that apply to every module:

1. **Schema validation first** — validate all inbound JSON against the shared schemas in `shared/schemas/` and
   `shared/types/` before any processing.
2. **Content sanitization** — strip prompt injection tokens from user-supplied text; sanitize HTML output; validate URL
   schemes; use parameterized queries only.
3. **Size limits** — reject payloads exceeding `ENDOGEN_MAX_PAYLOAD_BYTES` (default: 1 MB) before parsing.
4. **LLM output validation** — all LLM inference routes through LiteLLM; always validate structured LLM output against
   the expected schema.
5. **Error handling** — log full detail internally (with `traceId`); return only generic error messages to callers.

See [Validation Spec](../../shared/utils/validation.md) for the full language-specific patterns and the per-module
boundary-hardening checklist.

## OAuth 2.1 Authentication

The Hono API gateway (`apps/default/server`) implements an OAuth 2.1 authorization server with PKCE. All
protected API routes (`/api/input`, `/api/stream`, `/api/resources`, `/api/agents`) require a valid JWT
Bearer token; unauthenticated requests receive `HTTP 401` with a `WWW-Authenticate` header pointing to the
protected resource metadata URL.

### PKCE Flow

1. **Client generates** a random 32-byte `code_verifier` (base64url-encoded).
2. Client computes `code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))`
   (`code_challenge_method: S256`).
3. Client redirects to `GET /auth/authorize?response_type=code&client_id=apps-default-browser
   &redirect_uri=<uri>&code_challenge=<challenge>&code_challenge_method=S256&state=<opaque>`.
4. Server stores the challenge + metadata; issues a short-lived `code` (60 s TTL); redirects to
   `redirect_uri?code=<code>&state=<state>`.
5. Client exchanges `POST /auth/token` with `grant_type=authorization_code`, `code`, `code_verifier`,
   `redirect_uri`, and `client_id`.
6. Server verifies `SHA-256(code_verifier) == stored_code_challenge`; returns access token + sets refresh
   cookie.

### JWT Access Tokens

- **Algorithm**: HS256 (secret from `JWT_SECRET` env var; default `dev-secret-change-me` — **must be
  overridden in production**).
- **Expiry**: 900 s default (`JWT_EXPIRY_SECONDS`).
- **`aud` claim**: set to `MCP_SERVER_URI` env var (default `http://localhost:8000`).
- **Storage**: access tokens are held **in memory only** on the browser client — never in `localStorage` or
  cookies (mitigates XSS token theft).

### Refresh Tokens

- Stored exclusively in an `HttpOnly; SameSite=Strict` cookie on the `/auth` path.
- **Rotated on every use**: each call to `POST /auth/refresh` invalidates the old token and issues a new
  one atomically. Replay of a previously used token returns `HTTP 401 invalid_grant`.
- Expiry: 86 400 s default (`REFRESH_TOKEN_EXPIRY_SECONDS`).
- A `DELETE /auth/session` call revokes the active refresh token and clears the cookie.

### OAuth Metadata Endpoints

| Endpoint | RFC | Description |
| --- | --- | --- |
| `GET /.well-known/oauth-authorization-server` | RFC 8414 | Authorization server metadata — `authorization_endpoint`, `token_endpoint`, `code_challenge_methods_supported` |
| `/.well-known/oauth-protected-resource` | RFC 9728 | Referenced in `WWW-Authenticate` `resource_metadata` on 401 responses |

### Keycloak (optional production OIDC)

A Keycloak instance is available as an optional `keycloak` Docker Compose profile
(`apps/default/server/src/auth/keycloak/`) as a reference swap for the built-in authorization server in
production OIDC environments:

```bash
docker compose --profile keycloak up -d
```

Set `ISSUER_URL` and `JWT_SECRET` to match the Keycloak realm configuration.

## Module Sandboxing

Module sandboxing (OPA policies and gVisor sandbox templates) and the inter-module interface security review
are Phase 9 items (§9.1).

## Inter-Module Interface Review

Security review of all inter-module interfaces will be conducted in Phase 9 (§9.1).

## References

- [Validation Spec](../../shared/utils/validation.md)
- [Architecture Overview](../architecture.md)
- [Workplan — Phase 8](../Workplan.md#phase-8--cross-cutting-security-deployment--documentation)
