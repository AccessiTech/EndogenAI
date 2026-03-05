# Phase 8A — Detailed Workplan: Gateway, Auth, and Resource Registry

> **Status**: ⬜ NOT STARTED — Prerequisite: Phase 8 Gate 0 verified (see [phase-8-overview.md](phase-8-overview.md)).
> **Scope**: §8.1 Hono API Gateway · §8.2 MCP OAuth 2.1 · §8.5 MCP Resource Registry
> **Milestone**: Phase 8 Gates 1–3 (feeds into M8 via Gates 4 and 5)
> **Prerequisite**: Phase 8 Gate 0 — Phase 7 complete; schemas pre-landed; infrastructure verified.
> **Research references**:
> - [phase-8-neuroscience-interface-layer.md](phase-8-neuroscience-interface-layer.md) (D1) — §§i, ii, v
> - [phase-8-technologies-interface-layer.md](phase-8-technologies-interface-layer.md) (D2) — §§i, ii, v
> - [phase-8-synthesis-workplan.md](phase-8-synthesis-workplan.md) (D3) — §§i, ii, v
> - [phase-8-overview.md](phase-8-overview.md) (D7) — Gates, schema pre-landing, Docker Compose

---

## Contents

1. [Pre-Implementation Checklist](#1-pre-implementation-checklist)
2. [Build Sequence and Gate Definitions](#2-build-sequence-and-gate-definitions)
3. [Directory Structure Overview](#3-directory-structure-overview)
4. [§8.2 — MCP OAuth 2.1 Auth Layer](#4-82--mcp-oauth-21-auth-layer)
5. [§8.1 — Hono API Gateway](#5-81--hono-api-gateway)
6. [Gate 2 — D5 + D6 Verification](#6-gate-2--d5--d6-verification)
7. [§8.5 — MCP Resource Registry](#7-85--mcp-resource-registry)
8. [Cross-Cutting: `infrastructure/mcp` Changes](#8-cross-cutting-infrastructuremcp-changes)
9. [Phase 8A Completion Gate (Gate 3)](#9-phase-8a-completion-gate-gate-3)
10. [Decisions Recorded](#10-decisions-recorded)

---

## 1. Pre-Implementation Checklist

All items below must be confirmed before any Phase 8A code is written.

### 1.1 Phase 8 Gate 0

```bash
# Phase 7 complete
ls modules/group-iv-adaptive-systems/learning-adaptation/agent-card.json
ls modules/group-iv-adaptive-systems/metacognition/agent-card.json
cd modules/group-iv-adaptive-systems && uv run pytest tests/ -v

# infrastructure/mcp accepting Streamable HTTP
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' \
  | python3 -m json.tool

# Schemas pre-landed
ls shared/schemas/mcp-context.schema.json
ls shared/schemas/uri-registry.schema.json
cd shared && buf lint
```

### 1.2 Decision Q1 — EventSource Auth Approach (resolve before §8.1)

**Open question from D3**: The browser's `EventSource` API cannot send `Authorization: Bearer` headers. Two options:

| Option | Approach | Trade-off |
|---|---|---|
| **A — Session token in query string** | After login, gateway issues a short-lived (`exp: now+5min`) SSE-only token; client opens `EventSource('/api/stream?t=<token>')` | Simpler client; token momentarily in URL (logs, history) — mitigated by 5-min TTL and SSE-only scope |
| **B — `fetch()`-based SSE client** | Client uses `fetch('/api/stream', { headers: { Authorization: '...' } })` + `ReadableStream` + manual reconnect | Correct per MCP spec; no URI token; more complex client implementation |

**Recommendation from D2 §iii**: Option B is more correct. Option A is pragmatic for the boilerplate. **Phase Executive must resolve this question before §8.1 implementation begins** (Gate 1 prerequisite, Q1 in D7 §9).

Record decision here: **Option B — `fetch()`-based SSE client** ✅ (resolved 2026-03-03). Option A (query-string session token) reserved as a future configurable feature; not in Phase 8 boilerplate.

### 1.3 Decision Q3 — `/.well-known/oauth-protected-resource` on `infrastructure/mcp`

RFC 9728 requires the Protected Resource metadata endpoint to be served by the MCP server, not the gateway. Verify whether `infrastructure/mcp` already has this route:

```bash
curl -s http://localhost:8000/.well-known/oauth-protected-resource
# If 404: must add route to infrastructure/mcp/src/ — see §8 Cross-Cutting
```

Record result: **Option A confirmed** ✅ (resolved 2026-03-03) — add `/.well-known/oauth-protected-resource` route to `infrastructure/mcp/src/`. RFC 9728 requires it on the resource server. Implementation spec in §8.

### 1.4 TypeScript Workspace Bootstrap

```bash
# Register new packages
pnpm install   # picks up new workspace entries after package.json files are created

# Verify turbo can see new packages
pnpm run typecheck --filter @endogenai/gateway
pnpm run typecheck --filter @endogenai/client
```

### 1.5 Node.js and pnpm Version Requirements

```bash
# Node.js >= 20.x required for Hono @hono/node-server
node --version   # should be >= 20.0.0

# pnpm >= 9.x
pnpm --version
```

---

## 2. Build Sequence and Gate Definitions

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 8A Build Sequence                                                 │
│                                                                          │
│  0.  Phase 8 Gate 0 verified (see D7)                                   │
│  0a. Schemas pre-landed: mcp-context traceparent + uri-registry.schema   │
│  0b. Q1 (EventSource auth) and Q3 (well-known on MCP) resolved          │
│                                                                          │
│  ─── GATE 0: buf lint passes; infrastructure verified ───────────────── │
│                                                                          │
│  1.  §8.2 MCP OAuth auth stub                                           │
│      JWT utilities, PKCE endpoints, authMiddleware                       │
│                                                                          │
│  ─── GATE 1: JWT round-trip passing; PKCE flow tests pass ────────────  │
│  ───         infrastructure/mcp /.well-known/oauth-protected-resource OK │
│                                                                          │
│  2.  §8.1 Hono API Gateway                                              │
│      SSE relay, /api/input, /api/health, CORS, MCP client, static serve │
│                                                                          │
│  ─── GATE 2: gateway integration tests pass ──────────────────────────  │
│  ───         D5 (Browser Client workplan) STARTED OR COMPLETE            │
│  ───         D6 (Observability workplan) STARTED OR COMPLETE             │
│                                                                          │
│  3.  §8.5 MCP Resource Registry                                         │
│      uri-registry.json, /api/resources, resources/list handler          │
│                                                                          │
│  ─── GATE 3: uri-registry.json populated; resources/list responding ─── │
└──────────────────────────────────────────────────────────────────────────┘
```

**Why §8.2 (auth) builds before §8.1 (gateway)**: The `authMiddleware` is mounted on `app.use('/api/*')` inside the gateway. Auth cannot be retrofitted cleanly after routes are defined. Building auth first also surfaces OAuth endpoint requirements (RFC 9728/8414/7591) that inform gateway architecture decisions.

**Why §8.5 (registry) builds last in 8A**: The registry populates resources for the browser Internals panel (§8.3) and observability (§8.4). Without those workplans active, the registry is under-specified. Gate 2 enforces that D5 and D6 are at minimum underway before the registry is finalised.

---

## 3. Directory Structure Overview

```
apps/
├── default/
│   ├── server/
│   │   ├── src/
│   │   │   ├── index.ts                   # Entrypoint: NodeSDK telemetry init + serve()
│   │   │   ├── app.ts                     # Hono app factory: routes + middleware composition
│   │   │   ├── telemetry.ts               # OTel NodeSDK init (see D6 for full spec)
│   │   │   ├── mcp-client.ts              # MCP Streamable HTTP client
│   │   │   ├── auth/
│   │   │   │   ├── index.ts               # Auth router: mounts all /auth/* routes
│   │   │   │   ├── middleware.ts           # authMiddleware: JWT validate + WWW-Authenticate
│   │   │   │   ├── jwt.ts                 # jose JWT sign/verify/refresh utilities
│   │   │   │   ├── pkce.ts                # PKCE code_challenge + code_verifier helpers
│   │   │   │   ├── sessions.ts            # In-memory auth code + session store
│   │   │   │   └── keycloak/
│   │   │   │       └── realm.json         # Keycloak realm import (keycloak Docker profile)
│   │   │   └── routes/
│   │   │       ├── api.ts                 # /api/health, /api/input, /api/stream, /api/resources
│   │   │       └── wellknown.ts           # /.well-known/oauth-authorization-server
│   │   ├── tests/
│   │   │   ├── auth.test.ts              # JWT round-trip, PKCE flow, authMiddleware, 401
│   │   │   ├── gateway.test.ts           # CORS, health, input→stream (mocked MCP), origin rejection
│   │   │   ├── mcp-client.test.ts        # MCP client: session init, SSE relay, reconnect
│   │   │   └── resources.test.ts         # /api/resources, query param filter
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   └── README.md
│
resources/
│   ├── uri-registry.json                  # Consolidated resource URI registry
│   ├── uri-registry.schema.json           # Copy/symlink from shared/schemas/ (optional)
│   ├── access-control.md                  # Access control taxonomy + JWT scope mapping
│   ├── group-i-resources.json             # Group I (Signal Processing) resources
│   ├── group-ii-resources.json            # Group II (Cognitive Processing) resources
│   ├── group-iii-resources.json           # Group III (Executive & Output) resources
│   ├── group-iv-resources.json            # Group IV (Adaptive Systems) resources
│   └── README.md                          # brain:// URI scheme, registry format, how-to-add
```

---

## 4. §8.2 — MCP OAuth 2.1 Auth Layer

### Biological Analogue (D1 §ii)

The auth layer is the Blood–Brain Barrier: a tiered access control system where public metabolites (well-known endpoints) cross freely, authenticated signals (Bearer tokens) pass via active transport, and unauthenticated requests are refused like pathogens at the tight junctions. The `HttpOnly` cookie for refresh tokens is the BBB's immune privilege — the sensitive credential never enters the neuronal (JavaScript) compartment directly.

### 4.1 Dependencies (`package.json`)

```json
{
  "name": "@endogenai/gateway",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc -p tsconfig.json",
    "start": "node dist/index.js",
    "test": "vitest run",
    "lint": "eslint src tests",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "hono": "^4.4.0",
    "@hono/node-server": "^1.12.0",
    "jose": "^5.6.0",
    "pino": "^9.3.0",
    "@opentelemetry/sdk-node": "^0.52.0",
    "@opentelemetry/exporter-trace-otlp-http": "^0.52.0",
    "@opentelemetry/auto-instrumentations-node": "^0.48.0",
    "@opentelemetry/propagator-w3c-trace-context": "^1.25.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "tsx": "^4.16.0",
    "vitest": "^1.6.0",
    "@vitest/coverage-v8": "^1.6.0",
    "eslint": "^9.7.0"
  }
}
```

### 4.2 `jwt.ts` — JWT Utilities with `jose`

```typescript
import { SignJWT, jwtVerify, type JWTPayload } from 'jose'

const secret = new TextEncoder().encode(process.env.JWT_SECRET!)
const EXPIRY = Number(process.env.JWT_EXPIRY_SECONDS ?? 900)    // 15 min
const CLOCK_SKEW = 30                                            // 30 s tolerance

export async function signAccessToken(payload: {
  sub: string
  scope: string
  aud: string            // MCP_SERVER_URI (RFC 8707)
}): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${EXPIRY}s`)
    .sign(secret)
}

export async function verifyAccessToken(token: string): Promise<JWTPayload> {
  const { payload } = await jwtVerify(token, secret, {
    audience: process.env.MCP_SERVER_URI!,
    clockTolerance: CLOCK_SKEW,
  })
  return payload
}

export async function signRefreshToken(sub: string): Promise<string> {
  return new SignJWT({ sub, type: 'refresh' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${process.env.REFRESH_TOKEN_EXPIRY_SECONDS ?? 86400}s`)
    .sign(secret)
}
```

**Key decisions encoded**:
- `aud` claim set to `MCP_SERVER_URI` — RFC 8707 resource indicator
- `clockTolerance: 30` — 30-second clock skew window
- `jose` async API — never synchronous
- `JWT_SECRET` loaded from env — never hardcoded

### 4.3 `pkce.ts` — PKCE Helpers

```typescript
import { createHash, randomBytes } from 'crypto'

export function generateCodeVerifier(): string {
  return randomBytes(32).toString('base64url')
}

export function generateCodeChallenge(verifier: string): string {
  return createHash('sha256').update(verifier).digest('base64url')
}

export function verifyCodeChallenge(verifier: string, challenge: string): boolean {
  return generateCodeChallenge(verifier) === challenge
}
```

### 4.4 `sessions.ts` — In-Memory Auth Code Store

```typescript
interface AuthCodeEntry {
  clientId: string
  redirectUri: string
  codeChallenge: string
  codeChallengeMethod: 'S256'
  sub: string
  expiresAt: number   // Date.now() + 60_000 (1-min TTL)
}

// In-memory only — single process. Redis for horizontal scaling (documented extension point).
const codes = new Map<string, AuthCodeEntry>()

export function storeAuthCode(code: string, entry: AuthCodeEntry) { codes.set(code, entry) }
export function consumeAuthCode(code: string): AuthCodeEntry | undefined {
  const entry = codes.get(code)
  if (!entry || entry.expiresAt < Date.now()) return undefined
  codes.delete(code)   // single-use
  return entry
}
```

### 4.5 Auth Endpoints (`auth/index.ts`)

**`GET /auth/authorize`** — PKCE authorization endpoint:
```
Query params: response_type, client_id, redirect_uri, code_challenge, code_challenge_method, state, resource
Validates: client_id === 'apps-default-browser', redirect_uri exact match, code_challenge_method === 'S256'
On success: stores auth code (1-min TTL), redirects to redirect_uri?code=<code>&state=<state>
```

**`POST /auth/token`** — Token endpoint:
```
Body: { grant_type: 'authorization_code', code, redirect_uri, code_verifier, client_id, resource }
Validates: consumeAuthCode(code), verifyCodeChallenge(code_verifier, stored.codeChallenge)
On success: issues access token (JWT) + sets HttpOnly refresh cookie + returns { access_token, token_type: 'Bearer', expires_in }
```

**`POST /auth/refresh`** — Refresh token rotation:
```
Reads: HttpOnly 'refresh_token' cookie
Validates: verifyAccessToken on refresh token (type: 'refresh'), not expired
On success: issues new access token + rotates refresh cookie (new token, same TTL)
```

**`DELETE /auth/session`** — Session termination:
```
Clears: HttpOnly refresh cookie (max-age=0)
Returns: 204 No Content
```

**`GET /.well-known/oauth-authorization-server`** — RFC 8414 metadata:
```json
{
  "issuer": "http://localhost:3001",
  "authorization_endpoint": "http://localhost:3001/auth/authorize",
  "token_endpoint": "http://localhost:3001/auth/token",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["none"]
}
```

### 4.6 `middleware.ts` — `authMiddleware`

```typescript
import { createMiddleware } from 'hono/factory'
import { verifyAccessToken } from './jwt.js'

export const authMiddleware = createMiddleware(async (c, next) => {
  const authHeader = c.req.header('Authorization')
  const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : undefined

  if (!token) {
    return c.json({ error: 'unauthorized' }, 401, {
      'WWW-Authenticate':
        `Bearer realm="${process.env.MCP_SERVER_URI}", ` +
        `resource_metadata="${new URL('/.well-known/oauth-protected-resource', process.env.MCP_SERVER_URL).href}"`,
    })
  }

  try {
    const payload = await verifyAccessToken(token)
    c.set('jwtPayload', payload)
    await next()
  } catch {
    return c.json({ error: 'invalid_token' }, 401, {
      'WWW-Authenticate': `Bearer error="invalid_token"`,
    })
  }
})
```

### 4.7 Test Specifications (§8.2)

| Test | Scenario | Assertion |
|---|---|---|
| `auth.test.ts` — PKCE round-trip | Authorize → get code → exchange → access token | Token verifies; `aud` === `MCP_SERVER_URI` |
| `auth.test.ts` — bad code_verifier | Exchange with wrong `code_verifier` | `400 Bad Request` |
| `auth.test.ts` — refresh rotation | POST `/auth/refresh` with valid cookie | New access token; new refresh cookie set |
| `auth.test.ts` — auth code single-use | Exchange same code twice | Second request: `400` |
| `auth.test.ts` — expired auth code | Exchange code after 1-min TTL | `400` |
| `auth.test.ts` — clock skew tolerance | Token with `exp` 20 s in past | Accepted (within 30 s window) |
| `auth.test.ts` — clock skew rejection | Token with `exp` 60 s in past | `401 invalid_token` |
| `auth.test.ts` — audience mismatch | Token with wrong `aud` | `401 invalid_token` |
| `auth.test.ts` — missing token | Request to `/api/input` with no `Authorization` | `401` + `WWW-Authenticate` header present |
| `auth.test.ts` — session deletion | `DELETE /auth/session` | `204`; subsequent refresh fails |

---

## 5. §8.1 — Hono API Gateway

### Biological Analogue (D1 §i)

The gateway is the thalamus: all sensory input passes through it, but it is not a passive relay. It applies CORS-based origin gating (thalamocortical filtering), routes modality-specific streams to the correct handlers (thalamic nuclei → cortical areas), and actively shapes signals through the `authMiddleware` (analogous to the Thalamic Reticular Nucleus's GABA-mediated inhibition). The gateway's `MCP-Session-Id` session management mirrors thalamocortical loop synchronisation.

### 5.1 `app.ts` — Hono Application Factory

```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { secureHeaders } from 'hono/secure-headers'
import { serveStatic } from '@hono/node-server/serve-static'
import { authMiddleware } from './auth/middleware.js'
import { apiRouter } from './routes/api.js'
import { wellknownRouter } from './routes/wellknown.js'
import { authRouter } from './auth/index.js'

export function createApp() {
  const app = new Hono()

  // Middleware (global)
  app.use('*', logger())
  app.use('*', secureHeaders())
  app.use('/api/*', cors({
    origin: (origin) => {
      const allowed = (process.env.ALLOWED_ORIGINS ?? 'http://localhost:5173').split(',')
      return allowed.includes(origin) ? origin : null
    },
    credentials: true,
    allowHeaders: ['Content-Type', 'Authorization', 'Mcp-Session-Id'],
    allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  }))

  // Public routes (no auth)
  app.route('/.well-known', wellknownRouter)
  app.route('/auth', authRouter)

  // Protected routes
  app.use('/api/input', authMiddleware)
  app.use('/api/stream', authMiddleware)
  app.use('/api/resources', authMiddleware)
  app.route('/api', apiRouter)

  // Static SPA (production)
  app.use('*', serveStatic({ root: './dist' }))

  return app
}
```

### 5.2 `mcp-client.ts` — MCP Streamable HTTP Client

```typescript
/**
 * MCP Streamable HTTP client for the Hono gateway.
 * Implements the MCP 2025-06-18 Streamable HTTP transport:
 *   - POST for client→server JSON-RPC messages
 *   - GET for server-initiated SSE push
 *   - Mcp-Session-Id management
 *   - Last-Event-ID resumability
 *
 * Biological analogue: thalamocortical relay loop — bidirectional,
 * session-persistent, with active reconnection on disruption.
 */
export class McpClient {
  private sessionId: string | undefined
  private serverUrl: string

  constructor(serverUrl: string) {
    this.serverUrl = serverUrl
  }

  async initialize(): Promise<void> {
    const res = await this.post({ jsonrpc: '2.0', id: 1, method: 'initialize',
      params: { protocolVersion: '2025-06-18', capabilities: {} }
    })
    this.sessionId = res.headers.get('Mcp-Session-Id') ?? undefined
  }

  async send(message: object): Promise<Response> {
    return this.post(message)
  }

  async *subscribe(lastEventId?: string): AsyncGenerator<MessageEvent> {
    // Opens GET SSE stream; yields events; reconnects on error
    // sends Last-Event-ID on reconnect
  }

  async terminate(): Promise<void> {
    if (!this.sessionId) return
    await fetch(this.serverUrl, {
      method: 'DELETE',
      headers: this.buildHeaders(),
    })
  }

  private async post(body: object): Promise<Response> {
    return fetch(this.serverUrl, {
      method: 'POST',
      headers: { ...this.buildHeaders(), 'Content-Type': 'application/json',
                 'Accept': 'application/json, text/event-stream' },
      body: JSON.stringify(body),
    })
  }

  private buildHeaders(): Record<string, string> {
    const h: Record<string, string> = { 'MCP-Protocol-Version': '2025-06-18' }
    if (this.sessionId) h['Mcp-Session-Id'] = this.sessionId
    return h
  }
}
```

### 5.3 API Routes (`routes/api.ts`)

**`GET /api/health`** — No auth required:
```typescript
app.get('/health', (c) => c.json({ status: 'ok', version: pkg.version, ts: new Date().toISOString() }))
```

**`POST /api/input`** — Accepts user message, forwards to MCP:
```typescript
app.post('/input', async (c) => {
  const { message } = await c.req.json<{ message: string }>()
  const sessionId = crypto.randomUUID()
  // Store sessionId → MCP correlation in session map
  // Forward to MCP client
  await mcpClient.send({ jsonrpc: '2.0', id: sessionId, method: 'tools/call',
    params: { name: 'chat', arguments: { message } }
  })
  return c.json({ sessionId, streamPath: '/api/stream' }, 202)
})
```

**`GET /api/stream`** — SSE relay:
```typescript
import { streamSSE } from 'hono/streaming'

app.get('/stream', (c) => {
  // Q1 resolution applied here: session token from query/header (see §1.2 decision)
  return streamSSE(c, async (stream) => {
    for await (const event of mcpClient.subscribe()) {
      await stream.writeSSE({
        data: event.data,
        event: event.type ?? 'mcp-push',
        id: event.lastEventId ?? undefined,
      })
    }
  })
})
```

**`GET /api/resources`** — Serves URI registry with optional filtering:
```typescript
app.get('/resources', async (c) => {
  const registry = await loadRegistry()  // reads resources/uri-registry.json
  const group = c.req.query('group')
  const module = c.req.query('module')
  const filtered = registry.resources.filter(r =>
    (!group || r.group === group) &&
    (!module || r.module === module)
  )
  return c.json({ resources: filtered, total: filtered.length })
})
```

### 5.4 `Dockerfile`

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
EXPOSE 3001
CMD ["node", "dist/index.js"]
```

### 5.5 `agent-card.json`

```json
{
  "name": "hono-gateway",
  "version": "0.1.0",
  "description": "Backend-for-Frontend API gateway. Relays browser SSE streams to the MCP backbone, enforces OAuth 2.1 auth, manages CORS origin gating, and serves the React SPA. Implements the thalamic relay model.",
  "url": "http://localhost:3001",
  "wellKnownPath": "/.well-known/agent-card.json",
  "capabilities": {
    "mcp": false,
    "a2a": false,
    "sse": true
  },
  "neuroanatomicalAnalogue": "Thalamus — sensory relay, gating, and active shaping of cortex-bound signals"
}
```

### 5.6 Test Specifications (§8.1)

| Test | Scenario | Assertion |
|---|---|---|
| `gateway.test.ts` — health | `GET /api/health` | `200 { status: 'ok' }` |
| `gateway.test.ts` — CORS allowed origin | Request from `http://localhost:5173` | `Access-Control-Allow-Origin: http://localhost:5173` |
| `gateway.test.ts` — CORS rejected origin | Request from `http://evil.example.com` | No `Access-Control-Allow-Origin` header; `403` |
| `gateway.test.ts` — unauthenticated input | `POST /api/input` without token | `401` + `WWW-Authenticate` |
| `gateway.test.ts` — authenticated input | `POST /api/input` with valid JWT | `202` + `{ sessionId, streamPath }` |
| `gateway.test.ts` — SSE stream opens | `GET /api/stream` with valid JWT (Option A or B per Q1) | `Content-Type: text/event-stream`; heartbeat received |
| `gateway.test.ts` — MCP client session | `McpClient.initialize()` with mock MCP server | `Mcp-Session-Id` stored; reused on subsequent POSTs |
| `mcp-client.test.ts` — reconnect | Drop mock MCP SSE; reconnect | `Last-Event-ID` sent on reconnect |
| `mcp-client.test.ts` — terminate | `McpClient.terminate()` | `DELETE` sent to MCP with `Mcp-Session-Id` |

---

## 6. Gate 2 — D5 + D6 Verification

Before §8.5 implementation begins, the Phase Executive must verify:

```
☐  D5 (phase-8b-detailed-workplan.md) — status is STARTED or COMPLETE
   At minimum: design discussion section resolved; feature list confirmed.
   Verify: resource subscriptions required by Internals panel are identified.
   Specifically: which brain:// URIs does the Signal Trace feed and Working Memory
   inspector require? These must be registered in §8.5.

☐  D6 (phase-8c-detailed-workplan.md) — status is STARTED or COMPLETE
   At minimum: OTel gateway instrumentation design confirmed.
   Verify: which Prometheus metrics does the Internals panel surface?
   These must be accessible via the gateway's /api/* routes in §8.5.
```

**If this gate cannot be cleared** (D5/D6 not yet started): pause §8.5, continue §8.3 and §8.4 work in parallel, return to §8.5 once the required resource URIs are confirmed.

---

## 7. §8.5 — MCP Resource Registry

### Biological Analogue (D1 §v)

The resource registry is a topographic cortical map: every module's capabilities are projected onto an addressable URI namespace that preserves topology (related resources have adjacent prefixes) and over-represents high-priority resources (more URIs, richer metadata). Like the somatotopic or retinotopic map, the registry is not a flat list — it has hierarchy, structure, and a reflection of the system's priorities embedded in its organisation.

### 7.1 `shared/schemas/uri-registry.schema.json`

Must be landed as part of Phase 8 Gate 0 (see D7 §4.2 for the full schema).

Verify post-creation:
```bash
cd shared && buf lint
uv run python scripts/schema/validate_all_schemas.py
```

### 7.2 `resources/access-control.md` — Access Control Taxonomy

Define the access control taxonomy before authoring resource files:

```markdown
# MCP Resource Access Control

## Scopes

| Scope | Description | JWT claim |
|---|---|---|
| `read:public` | No authentication required | — |
| `read:authenticated` | Valid Bearer token required | `scope` contains `read` |
| `subscribe:authenticated` | Valid token + SSE session required | `scope` contains `subscribe` |
| `write:admin` | Admin scope (reserved for future use) | `scope` contains `admin` |

## Application

All entries in `uri-registry.json` carry an `accessControl` array.
The gateway's `authMiddleware` validates scope claims from the JWT payload.
Public resources (`read:public`) are served without auth middleware.
```

### 7.3 `brain://` URI Scheme

The `brain://` URI scheme is the canonical addressing scheme for all MCP resources in the frankenbrAIn system. It is consistent with the vector store collection naming convention (`brain.<module-name>`) established in Phase 1.

Format: `brain://<group-or-layer>/<module>/<resource-path>[/{id}]`

Examples:
```
brain://group-ii/working-memory/context/current     → current context window
brain://group-ii/episodic-memory/episode/{id}       → specific memory episode
brain://group-i/attention/filter/current            → current attention weights
brain://group-iv/metacognition/confidence/current   → current confidence scores
```

Document in `resources/README.md`.

### 7.4 Per-Layer Resource Files

**`resources/group-i-resources.json`** — Signal Processing:
```json
[
  {
    "uri": "brain://group-i/perception/signal/current",
    "module": "perception",
    "group": "group-i-signal-processing",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Current sensory input signal vector",
    "accessControl": ["read:authenticated"]
  },
  {
    "uri": "brain://group-i/attention/filter/current",
    "module": "attention-filtering",
    "group": "group-i-signal-processing",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Current attention weight vector",
    "accessControl": ["read:authenticated", "subscribe:authenticated"]
  }
]
```

**`resources/group-ii-resources.json`** — Cognitive Processing (priority resources):
```json
[
  {
    "uri": "brain://group-ii/working-memory/context/current",
    "module": "working-memory",
    "group": "group-ii-cognitive-processing",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Current context window assembled by Working Memory — primary Internals panel resource",
    "accessControl": ["read:authenticated", "subscribe:authenticated"]
  },
  {
    "uri": "brain://group-ii/episodic-memory/episode/{id}",
    "module": "episodic-memory",
    "group": "group-ii-cognitive-processing",
    "type": "template",
    "parameters": [{"name":"id","type":"string","description":"Episode UUID"}],
    "mimeType": "application/json",
    "description": "Specific memory episode by ID",
    "accessControl": ["read:authenticated"]
  },
  {
    "uri": "brain://group-ii/reasoning/plan/current",
    "module": "reasoning",
    "group": "group-ii-cognitive-processing",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Current DSPy reasoning plan",
    "accessControl": ["read:authenticated", "subscribe:authenticated"]
  }
]
```

**`resources/group-iii-resources.json`** — Executive & Output:
```json
[
  {
    "uri": "brain://group-iii/executive-agent/status",
    "module": "executive-agent",
    "group": "group-iii-executive-output",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Executive agent operational status and current goal stack",
    "accessControl": ["read:authenticated"]
  },
  {
    "uri": "brain://group-iii/motor-output/queue",
    "module": "motor-output",
    "group": "group-iii-executive-output",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Pending motor action queue",
    "accessControl": ["read:authenticated"]
  }
]
```

**`resources/group-iv-resources.json`** — Adaptive Systems:
```json
[
  {
    "uri": "brain://group-iv/metacognition/confidence/current",
    "module": "metacognition",
    "group": "group-iv-adaptive-systems",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Current task confidence scores per goal class — key Internals panel metric",
    "accessControl": ["read:authenticated", "subscribe:authenticated"]
  },
  {
    "uri": "brain://group-iv/learning-adaptation/habits/catalog",
    "module": "learning-adaptation",
    "group": "group-iv-adaptive-systems",
    "type": "direct",
    "mimeType": "application/json",
    "description": "Catalogue of promoted habit policies",
    "accessControl": ["read:authenticated"]
  }
]
```

### 7.5 `resources/list` and `resources/read` on `infrastructure/mcp`

The gateway's `GET /api/resources` serves the URI registry JSON. But the MCP-protocol `resources/list` and `resources/read` operations must be handled by `infrastructure/mcp` (per the MCP spec — these are JSON-RPC methods on the MCP server).

**`resources/list`** implementation on `infrastructure/mcp`:
- Reads `resources/uri-registry.json` at startup (cached)
- Returns MCP `ListResourcesResult` format: `{ resources: [{ uri, name, description, mimeType }] }`
- Supports MCP cursor-based pagination

**`resources/read`** implementation on `infrastructure/mcp`:
- Dispatches to the owning module via A2A (`resource_read` task to the module identified by `module` field in registry)
- Returns `ReadResourceResult`: `{ contents: [{ uri, mimeType, text | blob }] }`
- Modules must implement a `resource_read` A2A handler

**`resources/subscribe`** implementation:
- Subscribe to `brain://group-ii/working-memory/context/current` — working memory module emits `notifications/resources/updated` via MCP when context changes
- Subscribe to `brain://group-iv/metacognition/confidence/current` — metacognition module emits `notifications/resources/updated` when confidence scores change
- Both subscriptions are required by the D5 Internals panel (§8.3)

### 7.6 Test Specifications (§8.5)

| Test | Scenario | Assertion |
|---|---|---|
| `resources.test.ts` — list all | `GET /api/resources` with valid JWT | Returns all resources; schema validates against `uri-registry.schema.json` |
| `resources.test.ts` — group filter | `GET /api/resources?group=group-ii-cognitive-processing` | Only Group II resources returned |
| `resources.test.ts` — module filter | `GET /api/resources?module=working-memory` | Only working-memory resources returned |
| `resources.test.ts` — unauthenticated | `GET /api/resources` without JWT | `401` |
| MCP `resources/list` | JSON-RPC `resources/list` to `infrastructure/mcp` | Returns all URIs in MCP format |
| MCP `resources/read` | JSON-RPC `resources/read` `brain://group-iv/metacognition/confidence/current` | Returns confidence JSON |

---

## 8. Cross-Cutting: `infrastructure/mcp` Changes

Phase 8A requires two changes to `infrastructure/mcp` that are **not** part of the gateway package:

### 8.1 `/.well-known/oauth-protected-resource` (RFC 9728)

Add this route to `infrastructure/mcp/src/`:

```typescript
// In infrastructure/mcp/src/routes/wellknown.ts (create if absent)
app.get('/.well-known/oauth-protected-resource', (c) => {
  return c.json({
    resource: process.env.MCP_SERVER_URI ?? 'http://localhost:8000',
    authorization_servers: [
      process.env.AUTH_SERVER_URL ?? 'http://localhost:3001',
    ],
    bearer_methods_supported: ['header'],
    resource_documentation: 'http://localhost:3001/docs',
  })
})
```

**Verification**: `curl -s http://localhost:8000/.well-known/oauth-protected-resource | python3 -m json.tool`

### 8.2 `resources/list`, `resources/read`, `resources/subscribe` Handlers

Add MCP resource method handlers to `infrastructure/mcp/src/`. These delegate to module A2A endpoints for `resources/read` and dispatch `notifications/resources/updated` for subscriptions.

The exact implementation depends on the current `infrastructure/mcp` dispatch architecture — inspect `infrastructure/mcp/src/` before implementing.

---

## 9. Phase 8A Completion Gate (Gate 3)

All of the following must pass before Phase 8A is declared complete and Gate 3 is cleared:

```bash
# §8.2 Auth tests
cd apps/default/server && pnpm test --filter auth

# §8.1 Gateway tests
cd apps/default/server && pnpm test --filter gateway

# TypeScript clean
cd apps/default/server && pnpm typecheck

# Lint clean
cd apps/default/server && pnpm lint

# Well-known endpoints
curl -s http://localhost:3001/.well-known/oauth-authorization-server | python3 -m json.tool
curl -s http://localhost:8000/.well-known/oauth-protected-resource | python3 -m json.tool

# Gateway health
curl -s http://localhost:3001/api/health | grep '"status":"ok"'

# Resource registry
curl -s http://localhost:3001/api/resources \
  -H "Authorization: Bearer <token>" | python3 -m json.tool | grep "brain://"

# MCP resources/list
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}' \
  | python3 -m json.tool

# D5 verification
# ☐ phase-8b-detailed-workplan.md status is STARTED or COMPLETE

# D6 verification
# ☐ phase-8c-detailed-workplan.md status is STARTED or COMPLETE
```

---

## 10. Decisions Recorded

| ID | Decision | Rationale |
|---|---|---|
| D8A-1 | Auth (§8.2) builds before gateway (§8.1) | `authMiddleware` must exist before routes are protected; avoids retrofit |
| D8A-2 | `jose` for JWT | Async, JOSE standard, used by MCP reference implementations (D2 §ii) |
| D8A-3 | `HttpOnly` cookie for refresh token | XSS protection; access token in memory only (D1 §ii Blood-Brain Barrier) |
| D8A-4 | PKCE mandatory, no `client_secret` | Browser is a public client; MCP spec requires PKCE (D2 §ii) |
| D8A-5 | 30-second clock skew tolerance | Consistent inter-service tolerance; prevents spurious 401s on NTP drift |
| D8A-6 | Auth code TTL: 1 minute | Standard PKCE auth code TTL; single-use enforced via `consumeAuthCode()` |
| D8A-7 | In-memory session store | Sufficient for single-process dev; documented extension point for Redis (D3 §i) |
| D8A-8 | `brain://` URI scheme for all MCP resources | Consistent with Phase 1 collection naming; topology-preserving (D1 §v) |
| D8A-9 | `/.well-known/oauth-protected-resource` on `infrastructure/mcp` | RFC 9728 requires it on the resource server, not the AS (D2 §ii) |
| D8A-10 | Per-layer group resource files merged to `uri-registry.json` | Group-level authorship; central consolidated registry (D3 §v) |
| Q1 | `fetch()`-based SSE (Option B) ✅ | Resolved 2026-03-03 — `fetch()` + `ReadableStream` + `Authorization` header. Option A (query-string token) reserved as a future configurable feature; not in Phase 8 boilerplate. |
