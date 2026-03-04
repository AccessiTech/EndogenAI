# Phase 8 — D3: Synthesis Workplan — Application Layer & Observability

_Generated: 2026-03-03 by Docs Executive Researcher_

> **Scope**: Synthesis of D1 (neuroscience) and D2 (technologies) into concrete implementation guidance for Phase 8.
> This document is a pre-workplan recommendation brief — the Phase Executive must review and approve before any implementation begins.
> Sub-phases: i. Hono API Gateway · ii. MCP OAuth · iii. Browser Clients · iv. Observability · v. MCP Resource Registry

---

## 1. Phase Overview

Phase 8 instantiates the interface layer of the brAIn system — the boundary between the cognitive backbone (Groups I–IV) and the outside world. The five sub-phases are:

| Sub-phase | Brain Analogue (D1) | Technology (D2) | Deliverable |
|---|---|---|---|
| 8.1 Hono API Gateway | Thalamus — sensory relay & gating | Hono on Node.js, MCP Streamable HTTP client, SSE relay | `apps/default/server/` |
| 8.2 MCP OAuth 2.1 | Blood–Brain Barrier — tiered access control | MCP Auth spec 2025-06-18, JWT stub, `jose`, Keycloak opt-in | `apps/default/server/auth/` |
| 8.3 Browser Client | Global Workspace + DMN (Chat tab), Interoceptive readout (Internals tab) | Vite + React, EventSource API, WCAG 2.1 AA | `apps/default/client/` |
| 8.4 Observability | Interoception — systemic self-monitoring | OTel JS SDK, Hono instrumentation, Grafana/Prometheus | `observability/` extension |
| 8.5 Resource Registry | Topographic maps — structured URI namespace | MCP Resources spec 2025-06-18, `uri-registry.json` | `resources/` |

**Gate condition**: Phase 8 requires completion of Phase 7 (Group IV Adaptive Systems). Key upstream artifacts consumed by Phase 8:
- MCPContext envelopes emitted by Groups I–IV (schema: `shared/schemas/mcp-context.schema.json`)
- `infrastructure/mcp` — HTTP MCP server accepting Streamable HTTP POST/GET
- `infrastructure/a2a` — A2A broker for inter-agent coordination
- Prometheus + Grafana stack (`docker-compose.yml`) — must be running
- OTel Collector (`observability/otel-collector.yaml`) — must accept OTLP over HTTP

---

## 2. Sub-phase Synthesis

### i. Hono API Gateway (8.1)

**Design intent (thalamic relay)**:
The gateway should not be a transparent proxy. Like the thalamus, it actively shapes what passes through — applying CORS gating, auth validation, session management, and rate shaping before forwarding to the MCP backbone. The gateway should enforce origin-level access control (per MCP spec §2.0.1 Origin Validation) as a hard security boundary.

**Recommended implementation sequence**:
1. Scaffold `apps/default/server/` with `pnpm create hono@latest` (or `npm create hono@latest`) specifying `nodejs` template.
2. Add `@hono/node-server`, configure `serve({ fetch: app.fetch, port: 3001 })`.
3. Implement CORS middleware with allowlist from `ALLOWED_ORIGINS` env var.
4. Implement `GET /api/health` returning `{ status: "ok", version }`.
5. Implement `GET /api/stream` using `streamSSE()` — initially returning heartbeat events; wire to MCP client in step 7.
6. Implement `POST /api/input` accepting `{ message: string }` — return `202 Accepted` with `{ sessionId, streamPath: "/api/stream" }`.
7. Implement `src/mcp-client.ts` — MCP Streamable HTTP client that:
   - POSTs JSON-RPC messages to `infrastructure/mcp` (env: `MCP_SERVER_URL`)
   - Opens a long-lived `GET` SSE stream on `infrastructure/mcp` for server-initiated push
   - Manages session (`Mcp-Session-Id` header) and reconnection (`Last-Event-ID`)
8. Wire `POST /api/input` → `mcp-client.send(message)` and `GET /api/stream` → `mcp-client.subscribe()`.
9. Add `serveStatic` for the Vite `dist/` output.
10. Write integration tests in `apps/default/server/tests/`: CORS preflight, health, input→stream round-trip (mocked MCP), origin rejection.

**Implementation decisions**:
- `Mcp-Session-Id` is passed as a query param `?sessionId=<uuid>` on `GET /api/stream` (since `EventSource` cannot send custom headers). The gateway maps the query param to the MCP session. This resolves the `EventSource` auth problem at the session layer.
- Access tokens are validated by the auth middleware before the session lookup. The browser SSE client opens `EventSource('/api/stream?sessionId=<uuid>&token=<jwt>')`. The `token` must be short-lived (5–15 min) and for SSE only, to limit URI exposure. **Document this deviation from the MCP spec's "no tokens in URIs" rule** — it applies to MCP server URIs, not to the gateway's own browser-facing API.

**Schema dependency check**:
- `shared/schemas/mcp-context.schema.json` — verify it has `traceparent` field before 8.1 implementation
- If absent, add `traceparent` (optional string, W3C TraceContext format) before 8.1 lands

---

### ii. MCP OAuth 2.1 Auth Layer (8.2)

**Design intent (blood–brain barrier)**:
The auth layer provides graduated, tiered access — not a simple pass/fail gate. Public endpoints (`/.well-known/*`, `/api/health`) pass without credentials; authenticated endpoints (`/api/input`, `/api/stream`) require a valid Bearer token; admin endpoints (future) would require elevated scope. This mirrors the BBB's selective permeability: essential metabolites cross freely, pathogens are excluded, and certain molecules require active transport (token exchange).

**Recommended implementation sequence**:
1. Create `apps/default/server/src/auth/` directory.
2. Define `jose`-based JWT utilities: `signJwt(payload)`, `verifyJwt(token)`, `createAuthCode()`.
3. Implement `GET /.well-known/oauth-authorization-server` (RFC 8414 metadata response).
4. Implement `GET /.well-known/oauth-protected-resource` — **on `infrastructure/mcp`**, not the gateway. Open a task for the `infrastructure/mcp` package to add this route.
5. Implement `GET /auth/authorize` — PKCE flow: validates `client_id`, `code_challenge`, `redirect_uri`; returns auth code. For the stub, auto-approve without a login UI.
6. Implement `POST /auth/token` — validates `code` + `code_verifier` (PKCE); issues JWT access token + `HttpOnly` refresh cookie.
7. Implement `POST /auth/refresh` — reads `HttpOnly` refresh cookie; issues new access token; rotates refresh token. Returns new access token in JSON body.
8. Implement `DELETE /auth/session` — clears `HttpOnly` refresh cookie; invalidates active MCP session.
9. Write Hono middleware `authMiddleware` that:
   - Checks `Authorization: Bearer <token>` header
   - Verifies JWT signature and expiry (with 30 s clock skew tolerance)
   - Validates `aud` claim matches `MCP_SERVER_URI` (RFC 8707)
   - On failure: returns `401` with `WWW-Authenticate: Bearer realm=..., resource_metadata=<url>`
10. Mount `authMiddleware` on `app.use('/api/*', authMiddleware)`.
11. Create `apps/default/server/auth/keycloak/realm.json` with `apps-default` realm config for the optional Keycloak profile.
12. Document the Keycloak opt-in in `apps/default/server/README.md` under "Authentication Profiles".
13. Write unit tests: PKCE round-trip, token refresh, clock skew, audience mismatch → 401, session deletion.

**Key design decisions locked by D1+D2 research**:
- `HttpOnly` cookie for refresh token — prevents JavaScript access (XSS protection)
- Access token in memory only — not `localStorage`, not cookies
- PKCE mandatory — no `client_secret` for public browser client
- Refresh token rotation on every use — replay attack protection
- 30 s clock skew tolerance on JWT `exp` validation

**Hardcoded client for stub**: `client_id: "apps-default-browser"`, hardcoded redirect URI `http://localhost:5173/auth/callback`. Document as extension point for Dynamic Client Registration (RFC 7591).

---

### iii. Browser Client — Chat + Internals Tabs (8.3)

**Design intent (global workspace + DMN)**:
The Chat tab embodies Global Workspace Theory — a broadcast surface where the cognitive system's current output is made globally available to the user. The Internals tab embodies Default Mode Network activation — a reflective monitoring surface where the system observes its own internal state. The two tabs are not separate apps; they share the same SSE session and observe the same event stream.

**Recommended implementation sequence**:
1. Scaffold `apps/default/client/` with `npm create vite@latest . -- --template react-ts`.
2. Configure `vite.config.ts`: dev proxy to `http://localhost:3001`, `manualChunks: { vendor: ['react', 'react-dom'] }`, `sourcemap: true`.
3. Build the layout shell: `<header>` (app title, tab nav `<nav role="tablist">`), `<main>` (tab panels).
4. Implement `useSSEStream(sessionId)` hook: manages connection lifecycle, auto-reconnect, last-event-ID resumption using the `fetch()`-based SSE pattern (to support custom headers) or the session-token-in-URL approach chosen in 8.1.
5. Implement Chat tab (`src/tabs/Chat.tsx`):
   - Input area (`<form>`) — `POST /api/input` on submit
   - Streaming response div — `aria-live="polite"`, `aria-atomic="false"`, `aria-relevant="additions"`
   - Message history list — `<ul role="log">`
   - Keyboard accessible: Enter sends, Shift+Enter newline
6. Implement Internals tab (`src/tabs/Internals.tsx`) with four sub-panels:
   - Agent card browser — lists `/.well-known/agent-card.json` from each module; fetched once on tab open
   - Collections viewer — calls `GET /api/collections` on the gateway (gateway proxies to vector store); renders per-collection stats
   - Signal trace feed — subscribes to `brain://signal-trace/recent` MCP resource; renders last N MCPContext events
   - Working memory inspector — subscribes to `brain://working-memory/context/current` MCP resource; renders current context window
7. Implement auth flow (`src/auth/`): PKCE `authorize` redirect, callback handler (`/auth/callback`), token storage in `useRef` (memory-only), refresh timer.
8. Apply WCAG 2.1 AA: semantic HTML, colour contrast > 4.5:1, all interactive components keyboard-accessible, focus visible, no horizontal scroll at 320 px.
9. Apply mobile responsive CSS: single-column below 768 px, touch targets ≥ 44 × 44 px.
10. Write tests: Vitest + Testing Library unit tests per component; Playwright E2E smoke test (login → chat → internals panel loads → SSE events appear).
11. Configure `vite build` and verify initial gzipped JS chunk < 200 kB with `build-bundle-size` check in CI.

**Key design decisions**:
- Two-tab layout at MVP; no sidebar navigation — reduces layout complexity and mobile surface
- Internals tab data is MCP resource subscriptions relayed via the same SSE stream as Chat — no separate WebSocket or polling
- No third-party component library in the boilerplate — avoids bundle size bloat; styled with CSS custom properties only; documented as an extension point

**Accessibility note**: Screen reader testing with VoiceOver (macOS) and NVDA (Windows) should be done manually during review. Automated Lighthouse CI catches structure issues but not all ARIA interaction patterns.

---

### iv. Observability (8.4)

**Design intent (interoception)**:
Observability is not an afterthought — it is the system's capacity for self-knowledge. The OTel instrumentation that the gateway injects into MCPContext envelopes enables end-to-end distributed tracing that mirrors the insular cortex's body map: each module is a "region" with a reportable health state, and the gateway is the convergence zone where that state is made legible.

**Recommended implementation sequence**:
1. **Schema change first**: Add `traceparent?: string` (W3C TraceContext) to `shared/schemas/mcp-context.schema.json`. Land this before any 8.4 implementation.
2. Install OTel JS packages: `@opentelemetry/sdk-node`, `@opentelemetry/exporter-trace-otlp-http`, `@opentelemetry/auto-instrumentations-node`, `@opentelemetry/propagator-w3c-trace-context`.
3. Create `apps/default/server/src/telemetry.ts`: `NodeSDK` initialisation with OTLP HTTP exporter (`OTEL_EXPORTER_OTLP_ENDPOINT` env var), W3C TraceContext propagator, resource attributes (`service.name: "hono-gateway"`, `service.version`).
4. Import `telemetry.ts` as the first import in the server entrypoint (before Hono app setup).
5. Add manual Hono tracing middleware (see D2 §iv pattern): extracts incoming `traceparent`, creates span per request, sets status code on span end.
6. Inject `traceparent` into every MCP JSON-RPC message forwarded by `mcp-client.ts`.
7. Verify OTel Collector config (`observability/otel-collector.yaml`) accepts OTLP HTTP on port 4318. If not, add `otlp` receiver with HTTP protocol.
8. Add `pino` structured logging to the gateway (see D2 §iv pattern). Inject `trace_id` and `span_id` into every log record.
9. **Audit Python modules** (Groups I–IV): verify each uses `structlog` and emits `trace_id` in log records. File remediation tasks for any that do not.
10. **Provision Grafana dashboards**:
    - `observability/grafana/dashboards/gateway.json`: request rate, error rate, P99 latency, active SSE connections
    - `observability/grafana/dashboards/signal-flow.json`: per-module latency histograms (from OTel metrics)
    - Consider adding a Tempo service to `docker-compose.yml` for full distributed trace waterfall view (see Risk item in D2)
11. Write observability integration tests: send a message through the system, verify span exists in the OTel Collector output, verify `traceparent` matches across gateway and MCP server logs.

**Distributed trace backend decision**:
The current stack (Prometheus + Grafana) does not store distributed traces. Options:
- **Add Jaeger** (`jaegertracing/all-in-one`): Docker image, minimal config, Grafana datasource exists. Well-established.
- **Add Grafana Tempo**: Native Grafana integration, supports TraceQL. More modern.
- **Recommendation**: Add Grafana Tempo under the optional `observability` Docker Compose profile. Document in `observability/README.md`.

---

### v. MCP Resource Registry (8.5)

**Design intent (topographic maps)**:
The URI registry is a map — a structured projection of the cognitive system's capabilities onto an addressable namespace. Like the somatotopic map, it preserves topology: related resources (from the same module or group) have adjacent URI prefixes. Over-representation (more URIs for high-priority resources) is a design principle, not an accident.

**Recommended implementation sequence**:
1. **Schema first**: Create `shared/schemas/uri-registry.schema.json` defining the registry format (group, module, uri, type, mimeType, accessControl fields). Land this before creating `uri-registry.json`.
2. Create `resources/access-control.md`: document the access control taxonomy (read:public, read:authenticated, subscribe:authenticated, write:admin) and how it maps to JWT scope claims.
3. Create per-layer resource definition files:
   - `resources/group-i-resources.json` (Signal Processing: perception/attention URIs)
   - `resources/group-ii-resources.json` (Cognitive Processing: memory/reasoning URIs)
   - `resources/group-iii-resources.json` (Executive Output: motor/agent-runtime URIs)
   - `resources/group-iv-resources.json` (Adaptive Systems: reward/adaptive URIs)
4. Merge per-layer files into `resources/uri-registry.json` (manual merge is fine for Phase 8; a codegen script can automate this later).
5. Implement `GET /api/resources` on the Hono gateway: reads `uri-registry.json`, supports query params `?group=group-ii-cognitive-processing` and `?module=working-memory` for client-side filtering.
6. Implement the `resources/list` and `resources/read` JSON-RPC handlers on `infrastructure/mcp` — these are MCP-level operations (not gateway-level). The gateway proxies `resources/list` to `infrastructure/mcp`.
7. Implement `resources/subscribe` for the two Internals panel resources: `brain://working-memory/context/current` and `brain://signal-trace/recent`. These require Working Memory module to emit `notifications/resources/updated` events via the MCP backbone.
8. Create `resources/README.md`: document the `brain://` URI scheme, the registry format, the access control model, and how to add a new resource.
9. Write tests: `resources/list` returns expected resources, query param filter works, `resources/read` returns correct content type, `brain://` URIs resolve.

**URI namespace design** (initial):
```
brain://group-i/perception/signal/current        → latest sensory input
brain://group-i/attention/filter/current         → current attention weights
brain://group-ii/working-memory/context/current  → current context window
brain://group-ii/episodic-memory/episode/{id}    → specific memory episode
brain://group-ii/reasoning/plan/current          → current DSPy reasoning plan
brain://group-iii/executive-agent/status         → executive agent health
brain://group-iii/motor-output/queue             → pending motor actions
brain://group-iv/reward/signal/recent            → recent reward signals
brain://group-iv/adaptive/weights/current        → current adaptation weights
```

---

## 3. Prerequisites and Blocking Schema Changes

Before any Phase 8 implementation begins, verify and/or create these schema/contract items:

| Item | Location | Status | Blocking |
|---|---|---|---|
| `mcp-context.schema.json` — `traceparent` field | `shared/schemas/` | Verify existing | 8.4 |
| `uri-registry.schema.json` | `shared/schemas/` | Does not exist — create | 8.5 |
| `/.well-known/oauth-protected-resource` route on `infrastructure/mcp` | `infrastructure/mcp/src/` | Verify existing | 8.2 |
| `shared/schemas/mcp-context.schema.json` — full review | `shared/schemas/` | Verify field completeness | 8.1 |

These should be resolved as the first checklist items in the Phase 8 workplan.

---

## 4. Dependencies Between Sub-phases

```
8.5 (Resource Registry — schema)
    ↓
8.2 (Auth — lands first; 8.1 routes need auth middleware)
    ↓
8.1 (Gateway — core relay; needed by browser client)
    ↓
8.4 (Observability — wires OTel into places that exist)
 ↗          ↘
8.1          8.3 (Browser Client — depends on gateway endpoints)
```

Practical sequencing: **8.5 schema → 8.2 auth stub → 8.1 gateway → 8.3 client → 8.4 observability**

Note: 8.4 can be developed in parallel with 8.3 if there are multiple contributors; the OTel middleware does not block client development.

---

## 5. Open Questions for Phase Executive Resolution

Before authoring the canonical workplan, the following must be decided:

1. **`EventSource` auth approach for SSE** (High priority): The `EventSource` API cannot send `Authorization` headers. D2 recommends passing a short-lived session token in the query string (`/api/stream?sessionId=<uuid>&token=<jwt>`). Is this the accepted design, or should a `fetch()`-based SSE client be implemented instead? The choice affects both gateway (8.1) and client (8.3) implementation.

2. **Distributed trace backend** (Medium priority): Should Grafana Tempo or Jaeger be added to `docker-compose.yml` for Phase 8.4? Without it, only latency histograms are available — no trace waterfall. Recommended: add Tempo under an optional `observability` Compose profile.

3. **`/.well-known/oauth-protected-resource` location** (Medium priority): This RFC 9728 endpoint must be served by the MCP server (`infrastructure/mcp`), not the gateway. Does the current `infrastructure/mcp` package have extensible routing, or does adding this route require a deeper change?

4. **Keycloak opt-in scope** (Low priority): Should the Keycloak Docker profile be in `docker-compose.yml` (main file) or a separate `docker-compose.keycloak.yml`? The Workplan hints at the latter; confirm the design.

5. **`uri-registry.json` schema and location** (Low priority): Confirming that `shared/schemas/uri-registry.schema.json` is the right location (per the AGENTS.md "schemas first" rule). Also, confirm `resources/` is the right location for the registry JSON (not `shared/schemas/`).

6. **`brain://` URI scheme documentation** (Low priority): The `brain://` scheme is used in the vector store collection naming convention but not formally documented. Should a `docs/protocols/brain-uri.md` document be created, or is `resources/README.md` sufficient?

---

## 6. Recommended Phase 8 Checklist Addition Candidates

These are recommended additions to `docs/Workplan.md` §8 — for Phase Executive and user review. **Do not add these to Workplan.md directly; hand off to Executive Planner after user approval.**

### Pre-implementation (gate items)
- [ ] Verify `shared/schemas/mcp-context.schema.json` has `traceparent` field; add if missing
- [ ] Create `shared/schemas/uri-registry.schema.json`
- [ ] Verify `infrastructure/mcp` accepts extensible routing for `/.well-known/oauth-protected-resource`

### Phase 8.1 — Hono API Gateway
- [ ] Scaffold `apps/default/server/` with Hono + Node.js adapter
- [ ] CORS middleware with `ALLOWED_ORIGINS` env-var allowlist
- [ ] `GET /api/health` endpoint
- [ ] `GET /api/stream` SSE relay using `streamSSE()`
- [ ] `POST /api/input` accepting `{ message }` → `202 Accepted` with `{ sessionId, streamPath }`
- [ ] `src/mcp-client.ts` — MCP Streamable HTTP client (POST + GET SSE, session management, reconnection)
- [ ] Wire `/api/input` → MCP client → `/api/stream`
- [ ] `serveStatic` for Vite `dist/`
- [ ] Integration tests: CORS, health, input→stream round-trip (mocked MCP), origin rejection
- [ ] AGENTS.md contract: `/.well-known/agent-card.json` for the gateway

### Phase 8.2 — OAuth 2.1 Auth
- [ ] JWT utilities (`jose`): sign, verify, clock-skew
- [ ] `GET /.well-known/oauth-authorization-server` (RFC 8414)
- [ ] `GET /auth/authorize` (PKCE)
- [ ] `POST /auth/token` (code exchange, issues JWT + `HttpOnly` refresh cookie)
- [ ] `POST /auth/refresh` (refresh rotation)
- [ ] `DELETE /auth/session`
- [ ] `authMiddleware` on `/api/*` routes; 401 + `WWW-Authenticate` on failure
- [ ] RFC 9728 `/.well-known/oauth-protected-resource` route on `infrastructure/mcp`
- [ ] Keycloak optional Docker profile + `keycloak-realm.json` stub
- [ ] Unit tests: PKCE round-trip, token refresh, clock-skew, audience mismatch, session deletion

### Phase 8.3 — Browser Client
- [ ] Scaffold `apps/default/client/` with Vite + React TypeScript
- [ ] `vite.config.ts`: dev proxy, `manualChunks`, `sourcemap`
- [ ] Auth flow: PKCE authorize redirect, `/auth/callback` handler, memory-only token storage, refresh timer
- [ ] `useSSEStream(sessionId)` hook with reconnect + `Last-Event-ID` resumption
- [ ] Chat tab: StreamingResponseArea with `aria-live="polite"`, message history `role="log"`, keyboard-accessible input form
- [ ] Internals tab: agent card browser, collections viewer, signal trace feed, working memory inspector
- [ ] WCAG 2.1 AA: semantic HTML, contrast, keyboard nav, focus visible, no horizontal scroll at 320 px
- [ ] Mobile responsive: single-column < 768 px, touch targets ≥ 44 × 44 px
- [ ] Vitest + Testing Library unit tests per component
- [ ] Playwright E2E smoke: login → chat → Internals tab
- [ ] Lighthouse CI / accessibility score ≥ 90
- [ ] Bundle size check: gzipped initial JS < 200 kB

### Phase 8.4 — Observability
- [ ] `apps/default/server/src/telemetry.ts`: `NodeSDK` + OTLP exporter + W3C propagator
- [ ] Hono manual tracing middleware: span per request, status code, extract `traceparent`
- [ ] Inject `traceparent` into all MCP JSON-RPC messages in `mcp-client.ts`
- [ ] `pino` structured logging with `trace_id` / `span_id` injection
- [ ] Verify OTel Collector YAML accepts OTLP HTTP on port 4318; update if needed
- [ ] Audit Group I–IV Python modules for `structlog` + `trace_id` in log records; remediate gaps
- [ ] Grafana dashboard: `gateway.json` (request rate, error rate, P99 latency, active SSE connections)
- [ ] Grafana dashboard: `signal-flow.json` (per-module latency histograms)
- [ ] Add Tempo (or Jaeger) to `docker-compose.yml` optional profile for distributed trace storage
- [ ] Observability integration test: trace spans present in OTel Collector output

### Phase 8.5 — MCP Resource Registry
- [ ] `shared/schemas/uri-registry.schema.json`
- [ ] `resources/access-control.md`
- [ ] `resources/group-i-resources.json` through `group-iv-resources.json`
- [ ] `resources/uri-registry.json` (merged from group files)
- [ ] `GET /api/resources` on gateway with `?group=` and `?module=` query params
- [ ] `resources/list` + `resources/read` JSON-RPC handlers on `infrastructure/mcp`
- [ ] `resources/subscribe` for `brain://working-memory/context/current` and `brain://signal-trace/recent`
- [ ] `resources/README.md`: `brain://` scheme docs, registry format, access control, how-to-add
- [ ] Tests: list, filter, read, `brain://` resolution

---

## 7. Key Decisions Summary

These decisions emerge from D1 + D2 and should be encoded in READMEs and code comments when implemented:

| Decision | Rationale | Source |
|---|---|---|
| Hono as gateway, not Express | RegExpRouter perf, Web Standards alignment, `streamSSE()` built-in, multi-runtime portability | D2 §i |
| `jose` for JWT auth stub | JOSE standard, async, JWK Set support, used by MCP reference implementations | D2 §ii |
| `fetch()`-based SSE client (recommended) OR session token in query string | `EventSource` API cannot send `Authorization` headers; both approaches documented | D2 §iii, D1 §ii |
| `HttpOnly` cookie for refresh token | XSS protection; access token in memory only | D2 §ii |
| PKCE mandatory (no `client_secret`) | MCP spec requires it; browser is a public client | D2 §ii |
| React + Vite (no third-party component library) | Bundle size < 200 kB target; extend as documented | D2 §iii |
| `aria-live="polite"` on streaming response div | WCAG 2.1 AA 4.1.3 — screen reader accessibility for live content | D2 §iii, D1 §iii |
| OTel JS SDK with manual Hono tracing | Hono not auto-instrumented; manual middleware is straightforward | D2 §iv |
| Grafana Tempo (optional profile) for distributed traces | Prometheus histograms alone cannot produce trace waterfalls | D2 §iv |
| `brain://` URI scheme for all MCP resources | Consistent with vector store collection naming convention | D2 §v |
| Schema-first (`uri-registry.schema.json` before `uri-registry.json`) | AGENTS.md guardrail: land schema in `shared/schemas/` before implementation | AGENTS.md |

---

## 8. Handoff Notes for Phase Executive

This synthesis is based on:
- `docs/Workplan.md` §8.1–8.5 (read 2026-03-03)
- `docs/architecture.md` Group V Interface layer description
- Fetched technology sources: all 11 tech references in `scripts/fetch_manifests/phase-8.json`
- Fetched biological sources: all 9 bio references in `scripts/fetch_manifests/phase-8.json`

**D1**: `docs/research/phase-8-neuroscience-interface-layer.md`  
**D2**: `docs/research/phase-8-technologies-interface-layer.md`  
**D3**: this document

The research brief in the standard format is not written here because D3 is the synthesis; the formal brief structure (§1–§8) is covered by the D1+D2 pair. The Phase Executive should read D1, D2, and D3 sequentially before authoring the updated workplan.

**Recommended first action for Phase Executive**: resolve Open Question #1 (EventSource auth approach) — it is the highest-impact unresolved design decision and affects both 8.1 and 8.3 implementation directly.
