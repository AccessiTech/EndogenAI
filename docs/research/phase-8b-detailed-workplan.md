# Phase 8B — Detailed Workplan: Browser Client

> **Status**: ⬜ NOT STARTED — Can begin once Phase 8 Gate 2 is cleared (gateway SSE + /api/input passing).
> **Scope**: §8.3 Browser Client — Chat tab + Internals tab + Auth flow
> **Milestone**: Phase 8 Gate 4 (browser chat functional; SSE stream received)
> **Prerequisite**: Phase 8 Gate 2 (Hono gateway operational); D4 Gate 1 (auth stub complete)
> **Research references**:
> - [phase-8-neuroscience-interface-layer.md](phase-8-neuroscience-interface-layer.md) (D1) — §iii
> - [phase-8-technologies-interface-layer.md](phase-8-technologies-interface-layer.md) (D2) — §iii
> - [phase-8-synthesis-workplan.md](phase-8-synthesis-workplan.md) (D3) — §iii
> - [phase-8-overview.md](phase-8-overview.md) (D7) — Gates, env vars, workspace registration

---

## Contents

1. [Design Discussion — Baseline Frontend Features](#1-design-discussion--baseline-frontend-features)
2. [Pre-Implementation Checklist](#2-pre-implementation-checklist)
3. [Build Sequence and Gate Definitions](#3-build-sequence-and-gate-definitions)
4. [Directory Structure Overview](#4-directory-structure-overview)
5. [Auth Flow Implementation](#5-auth-flow-implementation)
6. [SSE Client Implementation](#6-sse-client-implementation)
7. [Chat Tab](#7-chat-tab)
8. [Internals Tab](#8-internals-tab)
9. [Layout Shell and Accessibility](#9-layout-shell-and-accessibility)
10. [Build Configuration and Bundle Size](#10-build-configuration-and-bundle-size)
11. [Testing Strategy](#11-testing-strategy)
12. [Phase 8B Completion Gate (Gate 4)](#12-phase-8b-completion-gate-gate-4)
13. [Decisions Recorded](#13-decisions-recorded)

---

## 1. Design Discussion — Baseline Frontend Features

> **Purpose**: Before the implementation checklist is written in detail, this section establishes the agreed feature scope for the Phase 8B browser client. The Phase Executive must review and sign off on this section before §§5–11 work begins. Items marked **[DECISION REQUIRED]** need explicit sign-off.

### 1.1 Biological Framing (from D1 §iii)

The browser client embodies two distinct cortical systems operating simultaneously via the same session:

- **Chat tab → Global Workspace Theory (GWT)**: The chat interface is the brain's global workspace — a "theatre" where the cognitive system's current output is broadcast to conscious (user-visible) attention. Messages in the chat panel correspond to signals that have achieved global broadcast status. The streamed token output mirrors the moment-by-moment construction of language in Broca's/Wernicke's areas.

- **Internals tab → Default Mode Network (DMN)**: The Internals panel is activated during reflection — when the system turns attention inward to observe its own state rather than outputting to the world. The four sub-panels map directly to DMN nodes: medial PFC (agent cards — self-schema), posterior cingulate cortex (signal trace — autobiographical continuity), hippocampus (memory inspector — episodic access), angular gyrus (collections viewer — semantic integration).

This framing means the two tabs are architecturally equivalent: both are subscribers to the same SSE event stream, differentiated only by the event types they respond to, not by separate network connections.

### 1.2 Feature Scope — Chat Tab

**In scope for Phase 8B (MVP)**:

| Feature | Description | Priority |
|---|---|---|
| Text input form | Single-line or multiline text input; Enter sends, Shift+Enter newlines | P0 |
| POST to `/api/input` | Submit message; receive `{ sessionId, streamPath }` | P0 |
| SSE token streaming | Open SSE connection; append tokens to response area in real time | P0 |
| Message history | Scrollable list of prior user turns and assistant responses | P0 |
| Loading state | Visual indicator while awaiting first token | P0 |
| Error state | Inline error message on network/stream failure | P0 |
| Reconnection notice | Toast or status line when SSE auto-reconnects | P1 |
| Markdown rendering | Render code blocks, bold, lists in assistant responses | P1 |
| Copy to clipboard | Copy button on assistant messages | P2 — defer post-MVP |
| Voice input | Microphone STT input | P3 — defer Phase 9+ |

**D5-A — RESOLVED ✅**: **Markdown rendering at P1** (resolved 2026-03-03). Raw text output at P0; `marked`/`markdown-it` added at P1 once SSE streaming is functional. Keeps the P0 bundle lean (~20 kB saved) and avoids a dependency on an unverified streaming-markdown interaction.

**Out of scope for Phase 8B**:
- Multi-conversation management / conversation history persistence
- File/image uploads
- Streaming cancellation (cancel mid-response)
- Custom system prompt editing

### 1.3 Feature Scope — Internals Tab

**In scope for Phase 8B (MVP)**:

| Panel | Feature | MCP resource URI | Priority |
|---|---|---|---|
| Agent Card Browser | Fetch and display `agent-card.json` from each registered module | `GET /.well-known/agent-card.json` on each module | P0 |
| Collections Viewer | Display vector store collections from registry; show count, embedding model, description | `GET /api/resources?group=...` | P0 |
| Signal Trace Feed | Live feed of recent MCPContext events; last N events with module, type, traceparent | `brain://group-ii/working-memory/context/current` (subscribe) | P1 |
| Working Memory Inspector | Display current context window content; structured JSON view | `brain://group-ii/working-memory/context/current` (read) | P1 |
| Confidence Scores | Display metacognition confidence per goal class | `brain://group-iv/metacognition/confidence/current` (read/subscribe) | P1 |

**D5-B — RESOLVED ✅**: **Option A — placeholder panels** (resolved 2026-03-03). Signal Trace Feed, Working Memory Inspector, and Confidence Scores render a "subscription not yet available" state with static mock data if `resources/subscribe` is not yet functional on `infrastructure/mcp`. Panels activate automatically when §8.5 subscribe lands — no code change required in the client.

**D5-C — RESOLVED ✅**: **Option B — gateway `GET /api/agents`** (resolved 2026-03-03). The gateway reads module base URLs from a `MODULE_URLS` environment variable and returns them as JSON. The client fetches this once on mount. Adding or removing a module is a config change, not a code change. Requires a small addition to Phase 8A `routes/api.ts` — noted in D4 §5.

**D5-D — RESOLVED ✅**: **Agent Card Browser as default panel** (resolved 2026-03-03). Always available at P0 — no subscription or MCP resource read required. Self-explanatory for a first-time user; other panels requiring live data are reachable via the panel switcher.

**Out of scope for Phase 8B**:
- Grafana dashboard embed (belongs to §8.4 / D6)
- Live Prometheus metric charts
- Full trace waterfall (requires Tempo — see D6)
- Agent A2A call graph visualisation

### 1.4 Feature Scope — Layout and Navigation

**In scope for Phase 8B**:

| Feature | Description |
|---|---|
| Two-tab navigation | `<nav role="tablist">` with Chat and Internals tabs |
| Header | App title ("frankenbrAIn"), tab nav, connection status indicator |
| Mobile responsive | Single-column < 768 px; touch targets ≥ 44 × 44 px |
| Dark/light mode | System `prefers-color-scheme` only; no manual toggle | 
| WCAG 2.1 AA | Full compliance — see §9 |
| Keyboard navigation | All interactive controls keyboard-operable |

**D5-E — RESOLVED ✅**: **System `prefers-color-scheme` only — no toggle** (resolved 2026-03-03). App defers entirely to OS/browser default. CSS custom properties are authored to make a user toggle easy to add as a P2 feature without architectural changes.

**D5-F — RESOLVED ✅**: **Configurable via `VITE_APP_TITLE` env var, default "frankenbrAIn"** (resolved 2026-03-03). Used in `<title>`, `<h1>` header, and any other title surface. Zero cost over hardcoding; deployments can customise without a code change.

### 1.5 Feature Scope — Auth UX

**In scope for Phase 8B**:

| Feature | Description |
|---|---|
| PKCE login redirect | Redirect to `/auth/authorize` on unauthenticated request |
| Auth callback handler | `/auth/callback` route in SPA; exchange code for token |
| Token refresh | Automatic silent refresh when access token nears expiry |
| Session expiry notice | Soft notification when refresh fails (session expired) |
| Logout button | Calls `DELETE /auth/session`; clears in-memory token; redirect to login |

**D5-G — RESOLVED ✅**: **Include `<LoginPage>` stub** (resolved 2026-03-03). A minimal component with a "Log in" button that triggers the PKCE redirect. With the Phase 8A auto-approve stub the flow completes instantly; with Keycloak enabled it navigates to the Keycloak login screen. Provides a recoverable surface if the auth redirect fails and is the correct foundation for Keycloak opt-in.

### 1.6 Design Decisions — All Resolved ✅

| ID | Decision | Resolution | Date |
|---|---|---|---|
| D5-A | Markdown rendering — P0 or P1? | **P1** — raw text at P0; markdown added post-SSE | 2026-03-03 |
| D5-B | Subscribe placeholder vs polling vs block? | **Option A — placeholder** | 2026-03-03 |
| D5-C | Agent URL discovery method? | **Option B — gateway `GET /api/agents`** | 2026-03-03 |
| D5-D | Internals default panel? | **Agent Card Browser** | 2026-03-03 |
| D5-E | Dark/light mode toggle? | **System preference only** — no toggle in Phase 8B | 2026-03-03 |
| D5-F | App title configurable? | **`VITE_APP_TITLE` env var**, default "frankenbrAIn" | 2026-03-03 |
| D5-G | Login page stub? | **Yes** — minimal `<LoginPage>` triggering PKCE redirect | 2026-03-03 |

---

## 2. Pre-Implementation Checklist

### 2.1 Gate 2 Verified

```bash
# Gateway health
curl -s http://localhost:3001/api/health | grep '"status":"ok"'

# Auth round-trip (requires JWT stub from §8.2)
# 1. PKCE authorize -> get code
# 2. Exchange code -> access token
# 3. POST /api/input with token -> 202
# 4. GET /api/stream with session -> SSE events

# Gateway CORS from localhost:5173
curl -s -H "Origin: http://localhost:5173" \
  -H "Authorization: Bearer <token>" \
  http://localhost:3001/api/health | grep '"status"'
```

### 2.2 Design Discussion Signed Off

- [ ] All D5-A through D5-G decisions resolved (§1.6)
- [ ] D5-C gateway `/api/agents` endpoint added to Phase 8A scope (if Option B chosen)

### 2.3 Scaffold Dependencies

```bash
# Node.js >= 20
node --version

# Create Vite scaffold
npm create vite@latest apps/default/client -- --template react-ts
cd apps/default/client

# Install additional dependencies (after scaffold)
pnpm add -D vitest @vitest/coverage-v8 \
  @testing-library/react @testing-library/user-event \
  @playwright/test \
  @vitejs/plugin-react

# Verify scaffold compiles
pnpm build
```

### 2.4 Accessibility Tooling Bootstrap

```bash
cd apps/default/client

# Lighthouse CI (run from monorepo root or client dir)
pnpm add -D @lhci/cli

# axe-core for automated a11y unit tests
pnpm add -D @axe-core/react

# eslint-plugin-jsx-a11y for programmatic build-time a11y linting
pnpm add -D eslint-plugin-jsx-a11y
```

`eslint-plugin-jsx-a11y` must be added to `eslint.config.js` in `apps/default/client/`:

```js
// eslint.config.js
import jsxA11y from 'eslint-plugin-jsx-a11y'

export default [
  // ... existing config ...
  {
    plugins: { 'jsx-a11y': jsxA11y },
    rules: { ...jsxA11y.configs.recommended.rules },
  },
]
```

This catches aria, role, interactive-element, and label violations at lint time — before Lighthouse runs. `pnpm lint` must exit 0 (no a11y violations) as part of the Gate 4 checklist.

---

## 3. Build Sequence and Gate Definitions

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 8B Build Sequence                                                 │
│                                                                          │
│  0.  Design discussion signed off (§1)                                  │
│  0a. Vite + React scaffold created                                       │
│  0b. Gate 2 verified (gateway operational)                               │
│                                                                          │
│  ─── GATE B0: scaffold compiles; proxy config points to gateway ──────── │
│                                                                          │
│  1.  Auth flow (PKCE redirect, callback, token memory, refresh timer)   │
│                                                                          │
│  ─── GATE B1: silent login works; token stored in-memory; refresh fires ─│
│                                                                          │
│  2.  SSE client hook `useSSEStream`                                     │
│      (connects, receives events, reconnects, surfaces last-event-ID)     │
│                                                                          │
│  ─── GATE B2: SSE events appear in browser console from gateway ──────── │
│                                                                          │
│  3.  Chat tab                                                            │
│      (layout, form, streaming area, history, loading/error states)       │
│                                                                          │
│  ─── GATE B3: type message → submit → tokens stream to screen ────────── │
│                                                                          │
│  4.  Internals tab (P0 panels: agent cards + collections)               │
│                                                                          │
│  ─── GATE B4: Internals tab renders with real agent card data ─────────  │
│                                                                          │
│  5.  Internals tab (P1 panels: signal trace, memory inspector, confidence│
│      — with placeholder fallback per D5-B)                              │
│                                                                          │
│  6.  WCAG 2.1 AA pass + mobile responsive + bundle size gate            │
│                                                                          │
│  ─── GATE B5 (Gate 4): full smoke test; Lighthouse ≥ 90; bundle < 200kB─│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Directory Structure Overview

```
apps/default/client/
├── src/
│   ├── main.tsx                    # React root render
│   ├── App.tsx                     # Top-level: route handler for /auth/callback vs shell
│   ├── auth/
│   │   ├── pkce.ts                 # generateCodeVerifier, generateCodeChallenge (browser Web Crypto)
│   │   ├── useAuth.ts              # Auth state hook: token, login(), logout(), refreshToken()
│   │   ├── AuthProvider.tsx        # Context provider wrapping whole app
│   │   ├── AuthCallback.tsx        # /auth/callback: exchange code, redirect to /
│   │   └── LoginPage.tsx           # Minimal login page with PKCE redirect button
│   ├── sse/
│   │   └── useSSEStream.ts         # Core SSE client hook (see §6)
│   ├── tabs/
│   │   ├── Chat/
│   │   │   ├── index.tsx           # Chat tab root
│   │   │   ├── MessageList.tsx     # Scrollable history: role="log"
│   │   │   ├── MessageItem.tsx     # Individual message bubble
│   │   │   ├── StreamingArea.tsx   # aria-live="polite" token accumulator
│   │   │   └── InputForm.tsx       # Enter sends, Shift+Enter newlines
│   │   └── Internals/
│   │       ├── index.tsx           # Internals tab root + sub-panel nav
│   │       ├── AgentCardBrowser.tsx # Fetches + displays agent-card.json per module
│   │       ├── CollectionsViewer.tsx # Resource registry group/collection display
│   │       ├── SignalTraceFeed.tsx  # Live MCPContext event feed (subscribe/placeholder)
│   │       ├── MemoryInspector.tsx  # Working memory context viewer (read/placeholder)
│   │       └── ConfidencePanel.tsx  # Metacognition confidence scores (read/placeholder)
│   ├── shell/
│   │   ├── AppShell.tsx            # Header + tablist + main area
│   │   ├── TabBar.tsx              # role="tablist" nav
│   │   └── StatusBar.tsx           # Connection status, session info
│   ├── api/
│   │   └── gateway.ts             # Typed API client for gateway routes
│   └── styles/
│       ├── global.css              # CSS custom properties, reset, base
│       ├── shell.css               # Layout shell
│       └── tokens.css              # Design tokens (colours, spacing, type)
├── tests/
│   ├── unit/                       # Vitest + Testing Library
│   │   ├── Auth.test.tsx
│   │   ├── Chat.test.tsx
│   │   ├── Internals.test.tsx
│   │   └── useSSEStream.test.ts
│   └── e2e/                        # Playwright
│       ├── smoke.spec.ts           # Login → chat → internals
│       └── a11y.spec.ts            # Lighthouse CI + axe scan
├── public/
│   └── favicon.svg
├── index.html
├── vite.config.ts
├── tsconfig.json
├── lighthouserc.json
├── playwright.config.ts
├── package.json
└── README.md
```

---

## 5. Auth Flow Implementation

### 5.1 `auth/pkce.ts` — Browser-side PKCE (Web Crypto API)

```typescript
// Uses Web Crypto API (browser-native) — no Node.js crypto import
export async function generateCodeVerifier(): Promise<string> {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

export async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(verifier)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}
```

### 5.2 `auth/useAuth.ts` — Auth State Hook

```typescript
interface AuthState {
  token: string | null          // Access token — memory-only
  isAuthenticated: boolean
  login: () => Promise<void>    // Initiates PKCE redirect
  logout: () => Promise<void>   // DELETE /auth/session + clear token
  refreshToken: () => Promise<void>
}

// Token stored in useRef (not state — avoids re-render on silent refresh)
// Refresh fires 60s before token expiry (computed from JWT exp claim)
// On refresh failure: token = null, redirect to login
```

### 5.3 `auth/AuthProvider.tsx`

Wraps the full app providing `AuthContext`. On mount:
1. Check URL for `?code=` (callback case → handled by `AuthCallback`)
2. Attempt silent refresh via `POST /auth/refresh` (HttpOnly cookie provides token)
3. If refresh succeeds: store access token in-memory
4. If refresh fails: user is unauthenticated → show `<LoginPage>`

### 5.4 `auth/AuthCallback.tsx`

Handles `/auth/callback?code=<code>&state=<state>`:
1. Read `code_verifier` from `sessionStorage` (stored before redirect)
2. POST to `/auth/token` with code + verifier
3. Store access token in memory
4. Clear `sessionStorage` verifier
5. Navigate to `'/'`

**Security note**: `code_verifier` is stored in `sessionStorage` (not `localStorage`) — cleared on tab close, and not accessible cross-origin. Access token is never stored in storage.

---

## 6. SSE Client Implementation

### 6.1 Q1 Resolution Applied Here

The EventSource auth approach (Q1 from D4 §1.2 / D7 §9) determines the implementation of this hook. Both options are specified:

**Option A — Session token in query string (simpler)**:
```typescript
// After POST /api/input returns { sessionId, streamPath }
const url = `/api/stream?sessionId=${sessionId}&t=${shortLivedSseToken}`
const source = new EventSource(url, { withCredentials: true })
```
Where `shortLivedSseToken` is a separate 5-min SSE-scoped JWT issued alongside the `202` response from `/api/input`.

**Option B — `fetch()`-based SSE client (recommended)**:
```typescript
export function useSSEStream(sessionId: string, token: string) {
  useEffect(() => {
    let controller = new AbortController()
    let lastEventId: string | undefined

    async function connect() {
      const res = await fetch(`/api/stream?sessionId=${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
          ...(lastEventId ? { 'Last-Event-ID': lastEventId } : {}),
        },
        signal: controller.signal,
      })

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        // Parse SSE frames from buffer, extract id/event/data
        // Call onEvent(parsedEvent)
        // Update lastEventId
      }
    }

    connect().catch(() => {
      // Reconnect after 3s on error (mirrors EventSource behaviour)
      setTimeout(connect, 3000)
    })

    return () => controller.abort()
  }, [sessionId, token])
}
```

The `fetch()`-based client (Option B) sends `Authorization: Bearer` correctly and supports `Last-Event-ID` resumability — both required by the MCP transport spec.

### 6.2 SSE Event Types

The hook dispatches to the correct tab/handler based on the SSE event type:

| Event type | Handler | Tab |
|---|---|---|
| `mcp-push` | `onToken(data.token)` | Chat — append to streaming area |
| `mcp-complete` | `onComplete()` | Chat — close streaming area |
| `resources/updated` | `onResourceUpdate(uri, data)` | Internals — update subscribed panel |
| `heartbeat` | (ignored) | — |
| `error` | `onStreamError(data)` | Both — surface error state |

---

## 7. Chat Tab

### 7.1 `Chat/InputForm.tsx`

```tsx
function InputForm({ onSubmit, disabled }: { onSubmit: (msg: string) => void, disabled: boolean }) {
  const [value, setValue] = useState('')

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim()) { onSubmit(value.trim()); setValue('') }
    }
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(value.trim()); setValue('') }}>
      <label htmlFor="chat-input" className="sr-only">Message</label>
      <textarea
        id="chat-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message…"
        aria-label="Message input"
        disabled={disabled}
        rows={1}
      />
      <button type="submit" disabled={disabled || !value.trim()} aria-label="Send message">
        Send
      </button>
    </form>
  )
}
```

**WCAG notes**:
- `<label>` with `htmlFor` OR `aria-label` on `<textarea>`
- `disabled` state reflected on both input and button
- Visible focus ring on all interactive elements (CSS `:focus-visible`)
- Touch target for Send button: min `44 × 44 px`

### 7.2 `Chat/StreamingArea.tsx`

```tsx
function StreamingArea({ content, isStreaming }: { content: string, isStreaming: boolean }) {
  return (
    <div
      role="log"
      aria-live="polite"
      aria-atomic="false"
      aria-relevant="additions text"
      aria-label="Assistant response"
      className="streaming-area"
    >
      {content}
      {isStreaming && <span aria-hidden="true" className="cursor-blink">▌</span>}
    </div>
  )
}
```

**WCAG 4.1.3 compliance**: `aria-live="polite"` announces new tokens without interrupting current screen reader speech. `aria-atomic="false"` + `aria-relevant="additions"` ensures only new tokens are announced, not the full response re-read on each token.

### 7.3 `Chat/MessageList.tsx`

```tsx
<ul role="log" aria-live="polite" aria-label="Conversation history">
  {messages.map(msg => (
    <li key={msg.id}>
      <MessageItem message={msg} />
    </li>
  ))}
</ul>
```

Messages are structured as:
```typescript
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean    // true while tokens are accumulating
  error?: string
  timestamp: Date
}
```

### 7.4 Loading and Error States

- **Loading**: `<div aria-live="polite" role="status">Thinking…</div>` displayed between POST `/api/input` and first SSE token.
- **Error**: Inline `<div role="alert" aria-live="assertive">` shown when SSE stream closes with error event. `role="alert"` ensures immediate announcement.

---

## 8. Internals Tab

### 8.1 Sub-panel Navigation

```tsx
// Internals tab uses a secondary tablist for its sub-panels
<nav role="tablist" aria-label="Internals panels">
  <button role="tab" aria-selected={active === 'agents'}>Agent Cards</button>
  <button role="tab" aria-selected={active === 'collections'}>Collections</button>
  <button role="tab" aria-selected={active === 'signal-trace'}>Signal Trace</button>
  <button role="tab" aria-selected={active === 'memory'}>Working Memory</button>
  <button role="tab" aria-selected={active === 'confidence'}>Confidence</button>
</nav>
```

### 8.2 `AgentCardBrowser.tsx` (P0)

Data flow (per D5-C decision — Option B recommended):
1. On mount: `GET /api/agents` → list of `{ name, url }` entries
2. For each agent: `GET {url}/.well-known/agent-card.json` → `AgentCard`
3. Render cards in a grid: name, description, version, neuroanatomical analogue, capabilities

```typescript
interface AgentCard {
  name: string
  version: string
  description: string
  url: string
  capabilities: { mcp: boolean; a2a: boolean; sse?: boolean }
  neuroanatomicalAnalogue?: string
}
```

Accessibility: each card is an `<article>` with `aria-labelledby` pointing to the module name heading.

### 8.3 `CollectionsViewer.tsx` (P0)

Data flow:
1. `GET /api/resources` → full registry
2. Group by `group` field
3. For each group: display card with list of resources (uri, mimeType, description, accessControl)

This is a read-only display component — no interaction required beyond the tab/panel navigation.

### 8.4 `SignalTraceFeed.tsx` (P1 — with placeholder per D5-B)

```tsx
function SignalTraceFeed() {
  const { events, status } = useResourceSubscription('brain://group-ii/working-memory/context/current')

  if (status === 'unavailable') {
    return <Placeholder message="Signal trace subscription not yet available." />
  }

  return (
    <ul role="log" aria-live="polite" aria-label="Signal trace">
      {events.map(ev => <SignalTraceItem key={ev.id} event={ev} />)}
    </ul>
  )
}
```

`useResourceSubscription` hook wraps the SSE `resources/updated` event handler. When the subscribed URI emits an update, it appends the new event to the local list.

### 8.5 `MemoryInspector.tsx` (P1 — with placeholder per D5-B)

```tsx
function MemoryInspector() {
  const { data, status } = useResourceRead('brain://group-ii/working-memory/context/current')

  if (status === 'unavailable') {
    return <Placeholder message="Working memory inspector not yet available." />
  }

  return (
    <section aria-label="Working memory context">
      <pre><code>{JSON.stringify(data, null, 2)}</code></pre>
    </section>
  )
}
```

### 8.6 `ConfidencePanel.tsx` (P1 — with placeholder per D5-B)

Displays the metacognition confidence scores from `brain://group-iv/metacognition/confidence/current`:

```tsx
function ConfidencePanel() {
  const { data, status } = useResourceRead('brain://group-iv/metacognition/confidence/current')

  if (status === 'unavailable') {
    return <Placeholder message="Confidence scores not yet available." />
  }

  // data: { per_goal_class: { [goalClass: string]: number } }
  return (
    <table aria-label="Metacognition confidence scores">
      <thead><tr><th>Goal Class</th><th>Confidence</th></tr></thead>
      <tbody>
        {Object.entries(data.per_goal_class).map(([cls, score]) => (
          <tr key={cls}>
            <td>{cls}</td>
            <td>
              <meter min={0} max={1} value={score}
                aria-label={`${cls} confidence: ${(score * 100).toFixed(0)}%`} />
              {(score * 100).toFixed(0)}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

**WCAG note**: `<meter>` element provides semantic progress representation. `aria-label` on each meter gives screen readers a full description. `<table>` with `<th>` headers satisfies 1.3.1.

---

## 9. Layout Shell and Accessibility

### 9.1 HTML Landmarks

```tsx
<body>
  <div id="root">
    <header role="banner">
      <h1>{import.meta.env.VITE_APP_TITLE ?? 'frankenbrAIn'}</h1>
      <nav role="tablist" aria-label="Main navigation">
        <button role="tab" aria-controls="panel-chat">Chat</button>
        <button role="tab" aria-controls="panel-internals">Internals</button>
      </nav>
      <StatusBar />
    </header>
    <main>
      <section id="panel-chat" role="tabpanel" aria-labelledby="tab-chat">
        <Chat />
      </section>
      <section id="panel-internals" role="tabpanel" aria-labelledby="tab-internals">
        <Internals />
      </section>
    </main>
  </div>
</body>
```

### 9.2 WCAG 2.1 AA Checklist

| Criterion | Implementation |
|---|---|
| 1.1.1 Non-text Content | Icons: `aria-hidden="true"` + adjacent visible text, OR `aria-label` |
| 1.3.1 Info and Relationships | Semantic landmarks (header, main, nav); `role="log"` for message list |
| 1.3.4 Orientation | No CSS restricting orientation |
| 1.4.3 Contrast Minimum | Text ≥ 4.5:1; large text ≥ 3:1 (design token enforcement) |
| 1.4.4 Resize Text | Relative units (`rem`, `em`) only; no fixed `px` font sizes |
| 1.4.10 Reflow | No horizontal scroll at 320 px viewport |
| 1.4.13 Content on Hover/Focus | Tooltips: dismissable with Escape; content does not disappear on mouse move |
| 2.1.1 Keyboard | Tab/Shift+Tab navigation through all controls; arrow keys within `role="tablist"` |
| 2.4.3 Focus Order | DOM order matches visual order; no programmatic focus traps |
| 2.4.7 Focus Visible | `:focus-visible` ring on all interactive elements (CSS) |
| 3.2.2 On Input | No automatic context change on input (form only submits on Enter/button) |
| 4.1.2 Name, Role, Value | All interactive elements: explicit `aria-label` or `<label>` association |
| 4.1.3 Status Messages | `aria-live` regions for streaming, loading, errors |

### 9.3 Mobile Responsive CSS

```css
/* apps/default/client/src/styles/shell.css */
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

.tab-bar button {
  min-width: 44px;
  min-height: 44px;     /* WCAG 2.5.5 touch target */
  padding: 8px 16px;
}

@media (max-width: 768px) {
  .internals-grid { grid-template-columns: 1fr; }
  .chat-panel { padding: 8px; }
}

/* No horizontal scroll at 320px */
* { box-sizing: border-box; max-width: 100%; }
```

---

## 10. Build Configuration and Bundle Size

### 10.1 `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:3001', changeOrigin: true },
      '/auth': { target: 'http://localhost:3001', changeOrigin: true },
      '/.well-known': { target: 'http://localhost:3001', changeOrigin: true },
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

### 10.2 Bundle Size Gate

Target: initial gzipped JS bundle < 200 kB.

Budget allocation:
| Chunk | Estimated gzip size |
|---|---|
| `vendor` (react + react-dom) | ~45 kB |
| App code (auth + SSE + Chat + Internals) | ~80–100 kB |
| CSS | ~10 kB |
| **Total** | **< 155 kB** (well within 200 kB gate) |

If markdown rendering (D5-A) is included (`marked` or `markdown-it`): +~20 kB. Still within budget.
If a third-party component library is added: re-evaluate bundle. Current recommendation: no component library.

Verify:
```bash
cd apps/default/client
pnpm build
gzip -c dist/assets/index.*.js | wc -c
# Must be < 204800
```

---

## 11. Testing Strategy

### 11.1 Unit Tests (Vitest + Testing Library)

| Test file | Coverage |
|---|---|
| `Auth.test.tsx` | PKCE code challenge/verifier; silent refresh; logout; unauthenticated redirect |
| `Chat.test.tsx` | Form submission; token accumulation in StreamingArea; `aria-live` region updates; error state |
| `Internals.test.tsx` | Agent card render from mock data; placeholder rendered when status=unavailable |
| `useSSEStream.test.ts` | SSE message parsing; reconnect after abort; `Last-Event-ID` sent on reconnect |

```bash
cd apps/default/client
pnpm test              # Vitest unit tests
pnpm test -- --coverage  # Coverage report
```

### 11.2 End-to-End Tests (Playwright)

**`smoke.spec.ts`**:
1. Navigate to `http://localhost:5173`
2. Redirect to `/auth/authorize` (unauthenticated)
3. Complete PKCE flow (mocked in E2E — stub returns code immediately)
4. Land on Chat tab
5. Type "hello" + Enter
6. Assert streaming response appears in `[aria-live="polite"]`
7. Switch to Internals tab
8. Assert Agent Card Browser shows at least one agent card

**`a11y.spec.ts`**:
```typescript
import { checkA11y } from 'axe-playwright'

test('Chat tab accessibility', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await checkA11y(page, '#panel-chat', {
    detailedReport: true,
    detailedReportOptions: { html: true },
  })
})
```

```bash
cd apps/default/client
pnpm test:e2e
```

### 11.3 Lighthouse CI

```json
// lighthouserc.json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:5173"],
      "startServerCommand": "pnpm preview",
      "numberOfRuns": 1
    },
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", {"minScore": 0.9}],
        "categories:performance": ["warn", {"minScore": 0.8}]
      }
    }
  }
}
```

```bash
pnpm dlx lhci autorun --config=lighthouserc.json
```

**Phase 8 gate**: accessibility ≥ 90 (WCAG 2.1 AA baseline).
**Phase 9 target**: strive for 95–100%. Remaining gaps after Phase 8 will be surfaced by `eslint-plugin-jsx-a11y` and Lighthouse audit reports — use these as the Phase 9 a11y backlog.

### 11.4 ESLint Accessibility Linting (`eslint-plugin-jsx-a11y`)

Static analysis catches a11y violations at build time, before any browser or Lighthouse run:

```bash
# Run standalone a11y lint check
cd apps/default/client && pnpm lint

# Common violations caught by jsx-a11y:
# - Missing alt text on <img>
# - Interactive elements without accessible names
# - Invalid aria-* attribute values
# - Non-interactive elements with click handlers (no keyboard equivalent)
# - Form inputs without associated <label>
```

All `eslint-plugin-jsx-a11y` errors must resolve to zero before Gate B5. Warnings are tracked as Phase 9 backlog items.

---

## 12. Phase 8B Completion Gate (Gate 4)

```bash
# Unit tests pass
cd apps/default/client && pnpm test

# E2E smoke test passes
cd apps/default/client && pnpm test:e2e smoke

# Accessibility: Lighthouse >= 90 (Phase 8 gate; Phase 9 target: 95–100%)
pnpm dlx lhci autorun --config=lighthouserc.json

# ESLint a11y: zero violations (eslint-plugin-jsx-a11y)
# TypeScript clean
cd apps/default/client && pnpm typecheck

# Lint clean (includes jsx-a11y rules)
cd apps/default/client && pnpm lint

# Bundle size gate
pnpm build && gzip -c dist/assets/index.*.js | wc -c
# Must be < 204800 bytes

# Manual gate: Chat tab functional
# 1. Start full stack (docker compose up -d)
# 2. Start gateway (cd apps/default/server && pnpm dev)
# 3. Start client (cd apps/default/client && pnpm dev)
# 4. Navigate to http://localhost:5173
# 5. Complete login flow
# 6. Type message → assert SSE tokens appear on screen
# 7. Switch to Internals → assert Agent Cards load

# Mobile responsive gate (manual or Playwright viewport)
# 8. Set viewport to 320px width → assert no horizontal scroll
# 9. Set viewport to 375px (iPhone SE) → assert tab bar touch targets ≥ 44px
```

---

## 13. Decisions Recorded

| ID | Decision | Rationale |
|---|---|---|
| D8B-1 | `fetch()`-based SSE (Option B) confirmed ✅ | Correct per MCP spec; `Authorization` header supported; `Last-Event-ID` works natively (D2 §iii). Option A (query-string token) noted as a future configurable feature — not in Phase 8B boilerplate. |
| D8B-2 | Access token in `useRef` (not `useState`) | Prevents re-render cascade on silent refresh; security hygiene |
| D8B-3 | `code_verifier` in `sessionStorage` | Tab-scoped; cleared on close; not accessible cross-origin (D2 §ii) |
| D8B-4 | `aria-live="polite"`, `aria-atomic="false"`, `aria-relevant="additions"` | New tokens announced without re-reading full response (WCAG 4.1.3) |
| D8B-5 | `<meter>` element for confidence scores | Semantic progress representation; screen-reader accessible |
| D8B-6 | No third-party component library | Bundle size gate; extension point documented (D3 §iii) |
| D8B-7 | Markdown rendering at P1 | Keeps P0 bundle smaller; swap in after SSE streaming is functional (D5-A default) |
| D8B-8 | `VITE_APP_TITLE` for app title | Configurable without code changes (D5-F default) |
| Q8 | `useState`/`useEffect` only — no global store in Phase 8B boilerplate ✅ | Zustand/Jotai is the documented natural extension point when inter-panel state sharing is needed (resolved 2026-03-03) |
| D5-A | Markdown at P1 — raw text at P0 ✅ | Resolved 2026-03-03 |
| D5-B | Placeholder panels when `resources/subscribe` unavailable ✅ | Option A confirmed — no polling fallback (resolved 2026-03-03) |
| D5-C | Gateway `GET /api/agents` for module URL discovery ✅ | Option B confirmed — server-side config; client needs no build-time knowledge of module URLs (resolved 2026-03-03) |
| D5-D | Agent Card Browser as default Internals panel ✅ | Resolved 2026-03-03 |
| D5-E | System `prefers-color-scheme` only — no toggle ✅ | Defers to OS/browser default; toggle deferred to P2 (resolved 2026-03-03) |
| D5-F | `VITE_APP_TITLE` env var, default "frankenbrAIn" ✅ | Resolved 2026-03-03 |
| D5-G | `<LoginPage>` stub included ✅ | Enables Keycloak opt-in readiness; recoverable auth failure surface (resolved 2026-03-03) |
