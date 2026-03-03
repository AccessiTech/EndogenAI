# Phase 8 — D2: Technologies for the Interface Layer

_Generated: 2026-03-03 by Docs Executive Researcher_

> **Scope**: Technology survey for Phase 8 sub-phases — Application Layer & Observability.
> This document audits available tools, specs, and frameworks for each Phase 8 sub-component.
> Sub-phases: i. Hono API Gateway · ii. MCP OAuth · iii. Browser Clients · iv. Observability · v. MCP Resource Registry

**Sources fetched**: `docs/research/sources/phase-8/tech-*.md` (11 files, fetched 2026-03-03)

---

## Overview

Phase 8 spans five technology domains: a TypeScript BFF API gateway, an OAuth 2.1 auth layer, a React/Vite SPA, a full-stack observability plane, and an MCP resource registry. The technology choices are partially resolved by the Workplan (`docs/Workplan.md` §8.1–8.5): Hono on Node.js for the gateway, JWT stub with optional Keycloak, Vite + React for the SPA. This document provides the technical depth needed to implement those choices correctly, surface any open implementation questions, and identify risks.

---

## i. Hono API Gateway (`apps/default/server/`)

### The Hono Framework

**Hono** (flame 🔥 in Japanese) is a TypeScript-first web framework built on Web Standards (Request/Response/Headers from the Fetch API). Its headline properties:

- **Ultrafast routing**: The `RegExpRouter` compiles all routes into a single regex before dispatch — no linear loops. Production benchmarks show ~402k ops/sec vs ~197k for Express equivalents on Cloudflare Workers.
- **Multi-runtime without code changes**: Runs on Cloudflare Workers, Fastly Compute, Deno, Bun, AWS Lambda, Lambda@Edge, Vercel, Netlify, and **Node.js** (via `@hono/node-server` adapter). For Phase 8, Node.js is the target runtime.
- **Zero dependencies**: The `hono/tiny` preset is under 14 kB minified. Full package with all middleware is still much lighter than Express (572 kB).
- **Batteries included** (Phase 8 relevant):
  - `hono/cors` — origin allowlist, credentials, preflight handling
  - `hono/bearer-auth` — Bearer token extraction and validation middleware
  - `hono/jwt` — JWT sign/verify with HS256/RS256, expiry checking
  - `hono/streaming` — `streamSSE()` and `streamText()` helpers for SSE endpoints
  - `hono/logger` — structured request logging
  - `hono/secure-headers` — HSTS, X-Content-Type, Referrer-Policy
- **TypeScript RPC mode** (`hc` client): Allows type-safe client calls from the SPA to the server, sharing route type definitions — directly useful for the `POST /api/input` and `GET /api/stream` interfaces between `apps/default/server/` and `apps/default/client/`.

### Node.js Adapter (`@hono/node-server`)

The `@hono/node-server` package wraps a Hono app in a Node.js `http.Server`. Key notes from the source:

```typescript
import { serve } from '@hono/node-server'
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hello!'))

serve({ fetch: app.fetch, port: 3001 }, (info) => {
  console.log(`Listening on http://localhost:${info.port}`)
})
```

- Static file serving: `serveStatic` from `@hono/node-server/serve-static` — serve Vite-built SPA `dist/` from the gateway without a separate static server.
- The adapter supports `http.createServer` and HTTPS (`https.createServer`) variants.
- Environment variables loaded via `process.env` (standard Node.js) or a `.env` file via `dotenv`.

### SSE with Hono `streamSSE()`

The `streamSSE()` helper in `hono/streaming` directly implements the SSE protocol:

```typescript
import { streamSSE } from 'hono/streaming'

app.get('/api/stream', (c) => {
  return streamSSE(c, async (stream) => {
    // Write events from MCP backbone to the SSE stream
    for await (const event of mcpClient.subscribe()) {
      await stream.writeSSE({
        data: JSON.stringify(event),
        event: 'mcp-push',
        id: event.id,
      })
    }
  })
})
```

Key points:
- Each `writeSSE()` call emits a well-formed `data: ...\n\nid: ...\nevent: ...\n\n` SSE frame.
- The `id` field maps to the `Last-Event-ID` resumability mechanism in the MCP transport spec.
- The helper handles connection abort automatically (via the `AbortSignal`).
- `streamSSE()` sets `Content-Type: text/event-stream` and appropriate cache headers.

### MCP Client Adapter

The gateway must act as an MCP client to `infrastructure/mcp`. The MCP Streamable HTTP transport (spec 2025-06-18) defines the protocol:

**Sending messages (client → MCP server)**:
- Every JSON-RPC message is a new `HTTP POST` to the MCP endpoint.
- `Accept: application/json, text/event-stream` must be included.
- The server returns either `Content-Type: application/json` (single response) or `Content-Type: text/event-stream` (SSE stream of responses).
- If a session has been established, `Mcp-Session-Id` header must be included on all subsequent requests.

**Listening for server-initiated push (MCP server → gateway)**:
- `HTTP GET` to the MCP endpoint opens an SSE stream for server-to-client push.
- `Accept: text/event-stream` must be included.
- `MCP-Protocol-Version: 2025-06-18` must be included on all requests.

**Session management**:
- The MCP server MAY return `Mcp-Session-Id` during initialization; the gateway MUST store and use it.
- Sessions are terminated with `HTTP DELETE` to the MCP endpoint + `Mcp-Session-Id` header.

**Security warning (§2.0.1)**:
- Servers MUST validate the `Origin` header to prevent DNS rebinding.
- MCP servers running locally SHOULD bind to `127.0.0.1` only.
- The gateway mirrors this by validating `Origin` on all incoming browser requests via the CORS middleware.

**Implementation note**: The current `infrastructure/mcp` package is TypeScript (Phase 2). The gateway will need to implement an MCP client that connects to `infrastructure/mcp` over Streamable HTTP. This is a new TypeScript module (`apps/default/server/src/mcp-client.ts`) not yet scaffolded.

### CORS Middleware

The Hono `cors()` middleware configuration for Phase 8:

```typescript
import { cors } from 'hono/cors'

app.use('/api/*', cors({
  origin: (origin) => {
    const allowed = process.env.ALLOWED_ORIGINS?.split(',') ?? ['http://localhost:5173']
    return allowed.includes(origin) ? origin : null
  },
  credentials: true,
  allowHeaders: ['Content-Type', 'Authorization', 'Mcp-Session-Id'],
  allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
}))
```

Returning `null` for unrecognised origins causes Hono to respond with `403 Forbidden` — the correct behaviour per MCP spec §2.0.1.

### Open Questions (8.1)

1. **MCP client adapter library**: Does `infrastructure/mcp` expose a TypeScript client class, or does the gateway need to implement raw `fetch()`-based MCP Streamable HTTP calls? Requires inspection of `infrastructure/mcp/src/`.
2. **Session multiplexing**: The gateway may serve multiple concurrent browser sessions. Each should have its own `Mcp-Session-Id`. The gateway needs a session map (e.g. `Map<string, McpSession>`). Memory-only is acceptable for the boilerplate; Redis would be needed for horizontal scaling.
3. **`POST /api/input` response design**: Should return `202 Accepted` + an SSE session ID. Should the SSE session ID be the `Mcp-Session-Id` or a separately generated gateway session token?

**Sources**: `docs/research/sources/phase-8/tech-mcp-streamable-http-transport.md`, `docs/research/sources/phase-8/tech-hono-overview.md`, `docs/research/sources/phase-8/tech-hono-nodejs.md`, `docs/research/sources/phase-8/tech-hono-streaming.md`, `docs/research/sources/phase-8/tech-hono-cors.md`

---

## ii. MCP OAuth 2.1 Auth Layer (`apps/default/server/auth/`)

### MCP Authorization Spec (2025-06-18)

The MCP authorization spec mandates a specific subset of OAuth 2.1 for HTTP-based transports. Key requirements (all MUST unless noted):

**Standards compliance stack**:
- OAuth 2.1 draft (`draft-ietf-oauth-v2-1-13`): base protocol
- RFC 9728 (OAuth 2.0 Protected Resource Metadata): MCP server exposes `/.well-known/oauth-protected-resource`
- RFC 8414 (OAuth 2.0 Authorization Server Metadata): auth server exposes `/.well-known/oauth-authorization-server`
- RFC 7591 (Dynamic Client Registration): SHOULD be supported
- RFC 8707 (Resource Indicators): `resource` parameter MUST be included in all auth and token requests

**Authorization flow**:
1. Client sends unauthenticated MCP request → server returns `HTTP 401` with `WWW-Authenticate: Bearer realm=..., resource_metadata=<url>`
2. Client fetches `GET /.well-known/oauth-protected-resource` → gets `{ authorization_servers: ["https://..."] }`
3. Client fetches `GET /.well-known/oauth-authorization-server` → gets full AS metadata (endpoints, supported grant types, etc.)
4. Client generates PKCE `code_verifier` + `code_challenge` (S256)
5. Client redirects to `GET /auth/authorize?response_type=code&client_id=...&code_challenge=...&resource=<mcp-server-uri>`
6. User authenticates; auth server redirects to client with `?code=...`
7. Client POSTs to `/auth/token` with `code`, `code_verifier`, `resource`
8. Auth server validates PKCE, issues short-lived JWT access token + refresh token

**Token requirements**:
- Access token: sent as `Authorization: Bearer <token>` on every MCP request
- Access tokens MUST NOT be in URI query strings
- Refresh token: stored in `HttpOnly` cookie (per Workplan §8.2 — never `localStorage`)
- Access token in memory only (not `localStorage`, not cookie)
- Short-lived access tokens (minutes); longer-lived refresh tokens (hours/days)
- Refresh tokens for public clients MUST be rotated on each use

**Security considerations**:
- PKCE is mandatory (protects against auth code interception; prevents code injection)
- All authorization server endpoints MUST be served over HTTPS in production (localhost is exempt for dev)
- Redirect URIs must be pre-registered; exact match validation required
- State parameter SHOULD be used to prevent CSRF
- Token audience binding (RFC 8707): access tokens must be issued for the specific MCP server URI; `aud` claim must match

### JWT Auth Stub Implementation Plan

For the Phase 8 boilerplate JWT stub:

**Endpoints to implement:**
```
POST  /auth/login          — credentials → JWT access token + HttpOnly refresh cookie
GET   /auth/authorize      — PKCE authorize endpoint (redirects to login form)
POST  /auth/token          — exchange auth code + code_verifier → tokens
POST  /auth/refresh        — HttpOnly refresh cookie → new access token
DELETE /auth/session       — explicit session termination (per MCP session management spec)
GET   /.well-known/oauth-protected-resource  — RFC 9728 metadata (on MCP server)
GET   /.well-known/oauth-authorization-server — RFC 8414 metadata (on Hono gateway)
```

**JWT library options** (TypeScript/Node.js):
- `jose` (preferred): JOSE standard implementation, supports RS256/ES256/HS256, JWK Set, JWT Claims Set validation, async API. Used by many MCP reference implementations.
- `jsonwebtoken`: Simpler API, synchronous, widely used but older design.
- Hono built-in `hono/jwt`: Lightweight but minimal — suitable for validation middleware, not full auth server.

**Recommended approach**: Use `jose` for the auth stub, with `hono/jwt` middleware for route-level validation.

### Keycloak Optional Profile

The Workplan specifies an optional `docker-compose.keycloak.yml` profile. Keycloak provides:
- Full OIDC/OAuth 2.1 server with PKCE, Dynamic Client Registration, and RFC 8414/9728 endpoints out-of-the-box
- Admin console for managing clients, users, and roles
- `realm.json` import for reproducible config
- PKCE-native public client profile for SPAs

Phase 8 should include a minimal `keycloak-realm.json` in `apps/default/server/auth/keycloak/` with the `apps-default` realm pre-configured to issue tokens for the MCP server URI.

### Hono Bearer Auth Middleware

```typescript
import { bearerAuth } from 'hono/bearer-auth'
import { createMiddleware } from 'hono/factory'

// Custom JWT validation middleware (validates aud claim etc.)
const jwtMiddleware = createMiddleware(async (c, next) => {
  const token = c.req.header('Authorization')?.replace('Bearer ', '')
  if (!token) {
    return c.json({ error: 'unauthorized' }, 401, {
      'WWW-Authenticate': `Bearer realm="${process.env.MCP_SERVER_URI}", error="unauthorized"`
    })
  }
  // Validate with jose...
  await next()
})

app.use('/api/*', jwtMiddleware)
```

### Open Questions (8.2)

1. **Dynamic Client Registration (RFC 7591)**: The spec says SHOULD. For the boilerplate, is a hardcoded `client_id` sufficient, or should we implement `/auth/register`? Recommendation: hardcoded for stub, documented as extension point.
2. **MCP server `/.well-known/oauth-protected-resource`**: This endpoint must live on the MCP server (`infrastructure/mcp`), not on the Hono gateway. This requires a new route in `infrastructure/mcp/src/`. Does the MCP package currently have a health/well-known route? Requires inspection.
3. **`resource` parameter (RFC 8707)**: The MCP specification mandates that clients include `resource=<mcp-server-uri>` in all auth requests. The auth stub must validate this claim in the token. What URI is the canonical MCP server URI in local dev? Likely `http://localhost:8000` or whatever port `infrastructure/mcp` binds to.
4. **Clock skew tolerance**: JWT validation should accept tokens up to N seconds past their `exp` claim (clock skew between services). Typical value: 30 seconds. The Workplan mentions this in test requirements but does not specify the tolerance.

**Sources**: `docs/research/sources/phase-8/tech-mcp-authorization.md`

---

## iii. Browser Client (`apps/default/client/`)

### Vite + React TypeScript SPA

**Vite** (French for "fast") is the de facto standard build tool for modern TypeScript SPAs. Key properties for Phase 8:

- **Scaffold command**: `npm create vite@latest apps/default/client -- --template react-ts` generates a Vite + React + TypeScript project in seconds.
- **HMR (Hot Module Replacement)**: Near-instant updates in dev (`vite dev`); no full page reload for React component changes.
- **`@vitejs/plugin-react`**: Uses Babel for Fast Refresh. Alternative: `@vitejs/plugin-react-swc` (Rust-based SWC compiler, faster build but larger footprint). Phase 8 should use standard `@vitejs/plugin-react`.
- **Production build**: `vite build` produces a `dist/` directory with:
  - `index.html` (entry point, inlined base64 fonts, hash-stamped asset references)
  - `assets/index.[hash].js` (main bundle, code-split)
  - `assets/index.[hash].css` (extracted CSS)
- **Bundle size management**: The Workplan requires initial gzipped JS chunk < 200 kB. Vite uses Rollup under the hood; `build.rollupOptions.output.manualChunks` can split vendor (React, React-DOM) from application code. React + React-DOM gzip to ~45 kB together; the remaining budget (~155 kB gzip) is sufficient for a minimal two-tab shell.
- **`vite.config.ts` — key options for Phase 8**:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:3001',  // dev proxy → Hono gateway
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
})
```

### EventSource API (SSE in the Browser)

The browser's `EventSource` Web API provides the SSE client for the Chat tab's streaming response:

```typescript
const source = new EventSource('/api/stream', { withCredentials: true })

source.addEventListener('mcp-push', (e) => {
  const payload = JSON.parse(e.data)
  appendToken(payload.token)
})

source.addEventListener('error', () => {
  // Browser auto-reconnects; last event ID is sent automatically
  console.warn('SSE stream error, reconnecting...')
})
```

Key properties:
- **Automatic reconnection**: `EventSource` automatically reconnects after disconnection (default 3 s delay). The browser sends `Last-Event-ID` header on reconnect — matching Hono's `writeSSE({ id })` and the MCP transport resumability mechanism.
- **`withCredentials: true`**: Required to send the `Authorization` cookie (if using cookie-based auth) or to allow CORS with credentials. For Bearer token auth, the token must be injected via a Hono proxy that reads it from memory — `EventSource` does not support custom headers directly in the browser.
- **Limitation — no custom headers**: The standard `EventSource` API does not allow setting custom headers (including `Authorization: Bearer ...`). **This is a significant implementation challenge for Phase 8.** Options:
  1. **Gateway-level session cookie**: After auth, the gateway issues a session cookie that is sent automatically with `withCredentials: true`. The gateway validates the cookie and proxies authenticated events.
  2. **Token in query string** (NOT RECOMMENDED per MCP spec — tokens MUST NOT be in URIs).
  3. **`fetch()`-based SSE** (`ReadableStream` + `TextDecoderStream`): Allows full control of headers, but requires manual stream parsing and reconnection logic.
  4. **Recommended**: Use a short-lived `session_token` generated after `/auth/login`, stored in memory, sent as a non-`Authorization` header via a custom `fetch()`-based SSE client. The gateway maps `X-Session-Token` to the user's JWT for SSE routes.

### WCAG 2.1 AA Implementation Checklist

The W3C WCAG 2.1 standard defines 50 success criteria at three levels (A, AA, AAA). Level AA is the Phase 8 target. Key criteria for the Chat + Internals SPA:

| Criterion | Implementation requirement |
|---|---|
| **1.1.1 Non-text Content** | All icons/images have `alt` text or `aria-hidden="true"` |
| **1.3.1 Info and Relationships** | Semantic HTML landmarks: `<main>`, `<nav>`, `<header>`, `<section>`, `<article>`; table roles for data grids |
| **1.3.4 Orientation** | No restriction to portrait/landscape; layout works in both |
| **1.4.3 Contrast (Minimum)** | Text ≥ 4.5:1 contrast ratio; large text ≥ 3:1 |
| **1.4.4 Resize Text** | No loss of content/functionality at 200% browser zoom |
| **1.4.10 Reflow** | No horizontal scroll at 320 px viewport width |
| **1.4.13 Content on Hover/Focus** | Tooltips dismissable, hoverable, persistent |
| **2.1.1 Keyboard** | All interactive controls reachable and operable via keyboard |
| **2.4.3 Focus Order** | Tab order logical; no focus traps |
| **2.4.7 Focus Visible** | Visible focus indicator on all interactive elements |
| **3.2.2 On Input** | No unexpected context change on input |
| **4.1.2 Name, Role, Value** | All UI components have accessible name, role, state |
| **4.1.3 Status Messages** | Streamed tokens announced via `role="log"` or `aria-live="polite"` ARIA live region |

**Critical for streaming**: The Chat tab's streamed response area MUST have `aria-live="polite"` (or `"assertive"` for high-urgency content) so screen readers announce token updates. Without this, streaming is completely inaccessible to screen reader users.

```tsx
<div aria-live="polite" aria-atomic="false" aria-relevant="additions text">
  {streamedContent}
</div>
```

`aria-atomic="false"` + `aria-relevant="additions"` tells the screen reader to announce only new tokens, not re-read the entire response on each update.

### Mobile Responsive Layout

The Workplan requires:
- Single-column stack below 768 px
- Touch targets ≥ 44 × 44 px
- No horizontal scroll at any width ≥ 320 px

CSS approach using custom properties (no framework lock-in):

```css
:root {
  --tab-bar-height: 48px;
  --input-height: 56px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
}

@media (max-width: 768px) {
  .layout-shell { flex-direction: column; }
  .tab-panel { padding: var(--spacing-sm); }
}
```

### Testing Stack

- **Vitest + Testing Library**: Component unit tests; `@testing-library/react` for render + interaction tests; `@testing-library/user-event` for realistic keyboard/mouse events.
- **Playwright**: E2E smoke test (login → send message → receive streamed response → Internals panel loads).
- **Lighthouse CI** (or `playwright-lighthouse`): Accessibility score ≥ 90.
- **Viewport snapshot assertions** in Playwright: `page.setViewportSize({ width: 320, height: 568 })` etc.

### Open Questions (8.3)

1. **`EventSource` auth workaround**: Which approach to choose (see options above)? The `fetch()`-based SSE client is more complex but correct per the MCP spec. Recommend documenting the decision in `apps/default/client/README.md` with the rationale.
2. **React vs Preact**: Workplan states React is the default; Preact is documented as a drop-in (identical API, ~3 kB vs ~45 kB gzip). For the boilerplate, use React; document the swap in README.
3. **State management**: For the Internals panel (agent cards, collections, signal trace), is React `useState` + `useEffect` sufficient, or should a lightweight store (Zustand, Jotai) be used? Recommendation: `useState` + `useEffect` only, to keep the boilerplate dependency-free. Document as an extension point.
4. **`POST /api/input` response format**: What does the `202 Accepted` body contain? Proposal: `{ "sessionId": "<uuid>", "streamPath": "/api/stream" }`. The `sessionId` is passed as a query parameter or header when opening the `EventSource`.

**Sources**: `docs/research/sources/phase-8/tech-vite-guide.md`, `docs/research/sources/phase-8/tech-eventsource-api.md`, `docs/research/sources/phase-8/tech-wcag21-overview.md`

---

## iv. Observability (`observability/`)

### OpenTelemetry JavaScript SDK

The Phase 8 gateway is TypeScript/Node.js and must emit OTel spans for all `/api/*` routes. The OTel JS SDK covers:

- **`@opentelemetry/sdk-node`**: All-in-one Node.js SDK; includes `NodeSDK` class for one-call setup.
- **`@opentelemetry/auto-instrumentations-node`**: Auto-instruments `http`, `https`, `fetch`, `dns`, `express`/`koa`/`hapi` — but NOT Hono (Hono is not yet auto-instrumented). Manual instrumentation required.
- **OTLP gRPC/HTTP exporters**: `@opentelemetry/exporter-trace-otlp-http` exports spans to the OTel Collector over HTTP. For Phase 8, the OTel Collector is already provisioned in `docker-compose.yml`.
- **W3C TraceContext propagation**: `@opentelemetry/propagator-w3c-trace-context` (included in the default propagator list) reads/writes `traceparent` and `tracestate` HTTP headers. The gateway must:
  1. Extract `traceparent` from incoming browser requests (if present).
  2. Create a new root span if no incoming context.
  3. Propagate `traceparent` **into every MCPContext envelope** forwarded to the MCP backbone.
  4. Ensure all downstream modules read `traceparent` from MCPContext.

**Manual Hono instrumentation pattern**:

```typescript
import { trace, context, propagation } from '@opentelemetry/api'
import { W3CTraceContextPropagator } from '@opentelemetry/core'

app.use('*', async (c, next) => {
  const propagator = new W3CTraceContextPropagator()
  const carrier = Object.fromEntries(c.req.raw.headers)
  const ctx = propagation.extract(context.active(), carrier)
  
  const tracer = trace.getTracer('hono-gateway')
  const span = tracer.startSpan(`${c.req.method} ${c.req.path}`, {}, ctx)
  
  await context.with(trace.setSpan(ctx, span), async () => {
    await next()
  })
  
  span.setStatus({ code: c.res.status < 400 ? 0 : 1 }) // OK or ERROR
  span.end()
})
```

### Structured Logging

The Python modules use `structlog`; the TypeScript gateway should use **`pino`** (the Node.js equivalent):
- JSON output by default to `stdout`
- Supports W3C trace context injection from OTel context (`pino-opentelemetry-transport`)
- Level-based filtering via `PINO_LOG_LEVEL` env var
- Aligns with `shared/utils/logging.md` structured log format requirements

```typescript
import pino from 'pino'
const logger = pino({ level: process.env.LOG_LEVEL ?? 'info' })

app.use('*', async (c, next) => {
  logger.info({ method: c.req.method, path: c.req.path }, 'incoming request')
  await next()
  logger.info({ status: c.res.status }, 'response sent')
})
```

### Grafana Dashboard Scope for Phase 8

The existing `observability/grafana/` directory has datasource config. Phase 8 should provision:

1. **Gateway dashboard** (`grafana/dashboards/gateway.json`):
   - Request rate (`GET /api/stream` opens, `POST /api/input` requests)
   - Error rate (4xx/5xx breakdown)
   - P50/P95/P99 latency for `/api/input` → `202` response time
   - Active SSE connections (gauge)

2. **End-to-end trace dashboard** (`grafana/dashboards/signal-flow.json`):
   - Embedded Tempo/Jaeger trace viewer OR Prometheus-based latency histogram per module hop
   - Since the stack uses Prometheus (not Tempo), this will be a latency-per-hop histogram, not a trace waterfall. A Tempo instance should be considered for Phase 8.4 if full distributed trace visualization is required.

3. **Module health dashboard** (extend existing or create `grafana/dashboards/module-health.json`):
   - Per-module health status (HTTP probe via Prometheus Blackbox Exporter or OTel heartbeat span)

### Finalisng Structured Logging Across All Modules

The Workplan §8.4 requires finalising `structlog` / `pino` emitters across all modules. Survey of current state:
- Group I–IV Python modules: `structlog` is the specified tool per `shared/utils/logging.md`; actual implementation completeness is a risk item (requires verification)
- `infrastructure/mcp` (TypeScript): should use `pino`
- `infrastructure/a2a` (TypeScript): should use `pino`

The Phase 8.4 deliverable is to ensure every module satisfies the structured JSON log format per `shared/utils/logging.md` and emits logs processable by the OTel Collector.

### Open Questions (8.4)

1. **Distributed tracing storage**: The current `docker-compose.yml` has Prometheus + Grafana but no distributed trace backend (Jaeger or Tempo). Prometheus histograms can approximate latency; a proper trace waterfall requires Tempo or Jaeger. Should Phase 8.4 add Tempo to `docker-compose.yml`?
2. **OTel Collector pipeline**: Is the existing `otel-collector.yaml` configured to receive OTLP from TypeScript/Node.js (HTTP) and Python (both HTTP and gRPC)? Requires inspection of `observability/otel-collector.yaml`.
3. **TraceContext in MCPContext envelopes**: The `mcp-context.schema.json` schema in `shared/schemas/` may not have a `traceparent` field. If not, this needs to be added (a schema change → land schema in `shared/schemas/` first per AGENTS.md).

**Sources**: `docs/research/sources/phase-8/tech-otel-js-sdk.md`

---

## v. MCP Resource Registry (`resources/`)

### MCP Resources Spec (2025-06-18)

The MCP Resources spec defines how servers expose data to clients as **resources** — addressable items with stable URIs. Key concepts:

**Resource types**:
- **Direct resources**: Concrete items with a fixed URI (e.g. `brain://working-memory/context/current`)
- **Resource templates**: URI templates (RFC 6570) for parameterised resources (e.g. `brain://episodic-memory/episode/{id}`)

**Resource contents**:
- `TextResourceContents`: UTF-8 text, MIME type (e.g. `application/json+mcp-context`)
- `BlobResourceContents`: Base64-encoded binary data (e.g. embeddings, audio)

**Operations**:
- `resources/list` (JSON-RPC): Returns paginated list of available resources
- `resources/read` (JSON-RPC): Returns current contents of a resource by URI
- `resources/subscribe` + `notifications/resources/updated`: Server pushes notifications when a subscribed resource changes
- `resources/templates/list`: Returns available URI templates

**Access control**: The spec does not define access control at the resource level — this is left to implementations. Phase 8.5's `access-control.md` fills this gap.

### URI Registry Design

The `uri-registry.json` in `resources/` should be a JSON document with the following schema:

```json
{
  "version": "1.0.0",
  "generated": "<ISO date>",
  "resources": [
    {
      "uri": "brain://working-memory/context/current",
      "module": "working-memory",
      "group": "group-ii-cognitive-processing",
      "type": "direct",
      "mimeType": "application/json",
      "description": "Current context window assembled by Working Memory",
      "accessControl": ["read:authenticated", "subscribe:authenticated"]
    },
    {
      "uri": "brain://episodic-memory/episode/{id}",
      "module": "episodic-memory",
      "group": "group-ii-cognitive-processing",
      "type": "template",
      "parameters": [{ "name": "id", "type": "string", "description": "Episode UUID" }],
      "mimeType": "application/json",
      "accessControl": ["read:authenticated"]
    }
  ]
}
```

The `brain://` URI scheme is consistent with the `brain.<module-name>` vector collection naming convention established in Phase 1.

### Per-Layer Resource Definition Files

The Workplan specifies populating per-layer resource definition files. Recommended structure:

```
resources/
  uri-registry.json              ← consolidated registry
  access-control.md              ← access control policy document
  group-i-resources.json         ← Group I (Signal Processing) resources
  group-ii-resources.json        ← Group II (Cognitive Processing) resources
  group-iii-resources.json       ← Group III (Executive & Output) resources
  group-iv-resources.json        ← Group IV (Adaptive Systems) resources
  README.md
```

Each `group-N-resources.json` is a subset of `uri-registry.json` filtered to that group. The consolidated registry is derived by merging the group files — this enables group-level authorship without modifying the central registry directly.

### MCP Resource Subscriptions and the Internals Panel

The Phase 8.3 Internals panel's **Signal trace feed** and **Working memory inspector** naturally map to MCP resource subscriptions:
- `brain://working-memory/context/current` → subscribed by the Internals panel; `notifications/resources/updated` events are forwarded to the browser via SSE
- `brain://signal-trace/recent` → hypothetical resource exposing the last N MCPContext events

This creates a clean architecture: the Internals panel is not a special-case feature; it is a standard MCP resource subscription relayed by the gateway's SSE endpoint. The same `GET /api/stream` endpoint that streams Chat tokens also carries `resources/updated` notifications.

### Open Questions (8.5)

1. **`brain://` URI scheme registration**: Should `brain://` be documented as a custom URI scheme in `resources/README.md`? It is not a standard IANA scheme, so it needs documentation.
2. **Agent card resources**: Should `/.well-known/agent-card.json` endpoints be listed in the URI registry? They are not traditional MCP resources (they are HTTP endpoints, not MCP URIs), but registering them makes the Internals panel's agent card browser more systematic.
3. **`resources/list` pagination**: With 30+ modules (Groups I–IV), the resource list may be large. Should the gateway implement client-side filtering (by module, by group) on top of the MCP `resources/list` API?
4. **Schema location**: Should `uri-registry.json` have a JSON Schema in `shared/schemas/`? Given the AGENTS.md rule "Schemas first — land the JSON Schema before the implementation", a `uri-registry.schema.json` should be created in `shared/schemas/` before authoring the registry.

**Sources**: `docs/research/sources/phase-8/tech-mcp-resources.md`

---

## Technology Risk Summary

| Risk | Severity | Sub-phase | Mitigation |
|---|---|---|---|
| `EventSource` cannot send `Authorization` header in browsers | High | 8.1, 8.3 | Use gateway session cookie OR `fetch()`-based SSE; document chosen approach |
| No distributed trace storage (Tempo/Jaeger) in current `docker-compose.yml` | Medium | 8.4 | Add Tempo service; or accept Prometheus histogram approximation and document limitation |
| MCP `/.well-known/oauth-protected-resource` must live on `infrastructure/mcp` — modification required | Medium | 8.2 | Add route to `infrastructure/mcp/src/` in 8.2; verify no regression on MCP conformance tests |
| `mcp-context.schema.json` may not have `traceparent` field | Medium | 8.4 | Schema change in `shared/schemas/` required first (land before implementation) |
| Hono is not auto-instrumented by OTel | Low | 8.4 | Manual instrumentation middleware is straightforward (see pattern above) |
| `uri-registry.schema.json` not yet in `shared/schemas/` | Low | 8.5 | Create schema before implementation per AGENTS.md guardrails |
| React vs Preact decision documented but not encoded in boilerplate | Low | 8.3 | README note sufficient; no build-time flag needed |

---

## References

| Source | File | Sub-phase |
|---|---|---|
| MCP Streamable HTTP Transport spec 2025-06-18 | `docs/research/sources/phase-8/tech-mcp-streamable-http-transport.md` | 8.1 |
| MCP Authorization spec 2025-06-18 | `docs/research/sources/phase-8/tech-mcp-authorization.md` | 8.2 |
| Hono Overview | `docs/research/sources/phase-8/tech-hono-overview.md` | 8.1 |
| Hono Node.js Adapter | `docs/research/sources/phase-8/tech-hono-nodejs.md` | 8.1 |
| Hono Streaming Helper | `docs/research/sources/phase-8/tech-hono-streaming.md` | 8.1 |
| Hono CORS Middleware | `docs/research/sources/phase-8/tech-hono-cors.md` | 8.1 |
| Vite Guide | `docs/research/sources/phase-8/tech-vite-guide.md` | 8.3 |
| EventSource Web API (MDN) | `docs/research/sources/phase-8/tech-eventsource-api.md` | 8.1, 8.3 |
| WCAG 2.1 Overview | `docs/research/sources/phase-8/tech-wcag21-overview.md` | 8.3 |
| OpenTelemetry JavaScript SDK | `docs/research/sources/phase-8/tech-otel-js-sdk.md` | 8.4 |
| MCP Resources spec 2025-06-18 | `docs/research/sources/phase-8/tech-mcp-resources.md` | 8.5 |
