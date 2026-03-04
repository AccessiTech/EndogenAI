# @endogenai/client

**Phase 8B — Browser Client** for the EndogenAI workspace.

> **Biological framing**: This SPA embodies two cortical systems:
> - **Chat tab** → Global Workspace Theory: the "theatre" where agent output achieves conscious broadcast
> - **Internals tab** → Default Mode Network: turns attention inward to observe the system's own state

---

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | React 18 + TypeScript strict | **Replaceable** — Preact, Solid, Svelte, vanilla all valid swaps |
| Build | Vite 5 | Proxy to gateway in dev; `manualChunks` for vendor split |
| CSS | Custom properties + plain CSS | No framework lock-in; dark mode via `prefers-color-scheme` |
| Tests | Vitest + Testing Library | Unit tests for hooks and components |
| E2E | Playwright | Smoke test: login → chat → internals |

The framework layer is intentionally thin and swappable. If the team prefers Preact (smaller bundle) or Solid
(reactive model), change the Vite plugin and jsx transform — no architectural changes are required.

---

## Quick start

```bash
# From repo root
pnpm install

# Start the gateway first (Phase 8A prerequisite)
cd apps/default/server && pnpm dev

# Start the client dev server
cd apps/default/client && pnpm dev
# → http://localhost:5173
```

The Vite dev server proxies `/api`, `/auth`, and `/.well-known` to `http://localhost:3001`.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `VITE_APP_TITLE` | `brAIn` | App title shown in `<h1>` and `<title>` |
| `VITE_GATEWAY_URL` | `` (empty) | Override gateway base URL (dev uses Vite proxy) |

Copy `.env.example` to `.env.local` for local overrides.

---

## Architecture

### Auth flow (PKCE — Option B / D8B-1)

```
User clicks "Log in"
  → generateCodeVerifier() + generateCodeChallenge()  [Web Crypto API]
  → sessionStorage.setItem('pkce_code_verifier', ...)
  → redirect: GET /auth/authorize?code_challenge=...&state=...
  → server redirects: /auth/callback?code=...&state=...
  → client: POST /auth/token { code, code_verifier }
  → access token stored in React state (memory only, never localStorage)
  → sessionStorage verifier cleared
  → refresh timer scheduled at 80% of expires_in
```

**Security decisions (D8B-2, D8B-3)**:
- Access token: `useRef` (prevents re-render on silent refresh; never persisted)
- Code verifier: `sessionStorage` (tab-scoped; cleared after exchange)
- Refresh token: HttpOnly cookie managed by the server — client never reads it

### SSE client (fetch()-based — D8B-1)

`useSSEStream` uses `fetch()` (not `EventSource`) so the `Authorization: Bearer` header
can be sent with the SSE connection. `EventSource` does not support custom headers.

Features:
- Exponential backoff reconnect (max 5 retries, up to 30 s delay)
- `Last-Event-ID` header sent on reconnect for resumable streams
- `AbortController` cleanup on unmount
- Single instance at app root, shared across both tabs via props

### Two-tab layout

Both tabs receive the same `sseEvents` array from the single `useSSEStream` instance.
They filter events by `event` type — no separate network connections.

```
App
├── useSSEStream (single connection)
├── ChatTab      ← consumes events: mcp-push, mcp-complete, error
└── InternalsTab ← consumes events: resources/updated
```

---

## Accessibility (WCAG 2.1 AA)

- Semantic HTML5 landmarks: `<header>`, `<main>`, `<nav>`, `<section>`
- `role="tablist"` / `role="tab"` + roving `tabIndex` pattern
- `role="log"` + `aria-live="polite"` on conversation history
- `aria-live="assertive"` on error alerts
- `aria-busy` during streaming response
- Visible `:focus-visible` ring on all interactive elements
- Touch targets ≥ 44 × 44 px
- `prefers-reduced-motion` suppresses animations
- `eslint-plugin-jsx-a11y` enforced at lint time

---

## Testing

```bash
# Unit tests (Vitest + Testing Library)
pnpm test

# With coverage (80% threshold)
pnpm test -- --coverage

# Watch mode
pnpm test:watch

# Playwright component integration tests (separate tier — requires Playwright CT setup)
pnpm run test:playwright

# E2E smoke test (requires pnpm build + pnpm preview running)
pnpm test:e2e

# TypeScript check
pnpm typecheck

# Lint (includes jsx-a11y)
pnpm lint
```

Estimated coverage: ~25% (target: 80%)— this is the largest coverage gap in the monorepo. Known gaps:
- `tabs/Internals/` (7 components, 0 tests) — see [workplan](../../docs/test-upgrade-workplan.md) P18
- `api/gateway.ts` (all client→server API calls) — see P16
- `auth/AuthProvider.tsx`, `auth/LoginPage.tsx`, `auth/useAuth.ts`, `auth/AuthContext.ts` — see P17

Playwright CT (`@playwright/experimental-ct-react`) covers integration-level component testing — see
[P27](../../docs/test-upgrade-workplan.md). This is a separate tier from the Vitest unit tests above;
both must pass before merging client-layer changes.

---

## Bundle size gate

Initial gzipped JS chunk must be < 200 kB:

```bash
pnpm build
gzip -c dist/assets/index.*.js | wc -c   # must be < 204800
```

Budget allocation:
| Chunk | Estimated gzip |
|---|---|
| `vendor` (react + react-dom) | ~45 kB |
| App code | ~80–100 kB |
| CSS | ~10 kB |
| **Total** | **< 155 kB** |

---

## Phase 8B decisions

| ID | Decision |
|---|---|
| D8B-1 | `fetch()`-based SSE — `EventSource` cannot send `Authorization` header |
| D8B-2 | Access token in `useRef` — no re-render on silent refresh |
| D8B-3 | Code verifier in `sessionStorage` — tab-scoped, cleared after exchange |
| D8B-6 | No third-party component library — bundle size gate |
| D8B-7 | Markdown rendering at P1 — raw text at P0 |
| D5-B | P1 panels render placeholder when subscription unavailable |
| D5-C | Agent discovery via gateway `GET /api/agents` |
| D5-E | System `prefers-color-scheme` only — no manual toggle |

---

## File directory

```
src/
├── main.tsx                    React 18 createRoot entry
├── App.tsx                     Auth guard + tab shell + single useSSEStream
├── auth/
│   ├── pkce.ts                 generateCodeVerifier, generateCodeChallenge (Web Crypto)
│   ├── AuthContext.ts          React context value type
│   ├── AuthProvider.tsx        PKCE redirect, token exchange, silent refresh
│   ├── useAuth.ts              useAuth() hook
│   └── LoginPage.tsx           Minimal login page with PKCE redirect button
├── sse/
│   └── useSSEStream.ts         fetch()-based SSE client, backoff, Last-Event-ID
├── api/
│   └── gateway.ts              Typed gateway API client
├── shell/
│   ├── AppShell.tsx            Header + main layout landmarks
│   ├── TabBar.tsx              Accessible tablist (roving tabindex, arrow keys)
│   └── StatusBar.tsx           SSE + gateway health indicator
├── tabs/
│   ├── Chat/
│   │   ├── index.tsx           Chat tab root
│   │   ├── types.ts            Message interface
│   │   ├── MessageList.tsx     role="log" conversation history
│   │   ├── MessageItem.tsx     Individual message bubble
│   │   └── InputForm.tsx       Textarea + send button
│   └── Internals/
│       ├── index.tsx           Internals tab root + secondary tablist
│       ├── Placeholder.tsx     Graceful unavailable state (D5-B)
│       ├── AgentCardBrowser.tsx AgentCard display component
│       ├── AgentCardBrowserPanel.tsx P0: fetches + renders agent cards
│       ├── CollectionsViewer.tsx P0: resource registry display
│       ├── SignalTraceFeed.tsx  P1: SSE resources/updated events
│       ├── MemoryInspector.tsx P1: working memory context
│       └── ConfidencePanel.tsx P1: metacognition confidence scores
└── styles/
    ├── tokens.css              CSS custom properties (light + dark)
    ├── global.css              Reset + base styles
    └── app.css                 Component styles
```
