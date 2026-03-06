# MCP Local Distribution Findings — Issue #35 Priority C

_Researched: 2026-03-06 by Docs Executive Researcher_  
_Sources: MCP spec (modelcontextprotocol.io, fetched 2026-03-06), FastMCP repo (github.com/PrefectHQ/fastmcp, fetched 2026-03-06), AIGNE paper (arxiv.org/html/2512.05470v1, fetched 2026-03-06), FreeCodeCamp multi-agent Docker article (freecodecamp.org, fetched 2026-03-06), issue-32-manifest.md_

---

## Domain B — Open-Source MCP Server Implementations

### Sub-question 1 — What open-source MCP servers exist beyond the reference implementation?

As of March 2026 the MCP ecosystem has four implementable frameworks relevant to EndogenAI:

| # | Framework | Language | Local-first | Stars / Adoption | Notes |
|---|-----------|----------|-------------|------------------|-------|
| 1 | **Official MCP SDK** (`@modelcontextprotocol/sdk` / `mcp` PyPI) | TS + Python | ✅ Both `stdio` and Streamable HTTP | Baseline reference; EndogenAI already uses TS flavour | Protocol version 2025-06-18 |
| 2 | **FastMCP** (`PrefectHQ/fastmcp`) | Python | ✅ Both transports | 23.5 K ⭐, ~1 M downloads/day; powers 70 % of all MCP servers | Started as community project; v1 incorporated into official Python SDK; standalone is more feature-rich; v3.1.0 current |
| 3 | **AIGNE Framework** (`AIGNE-io/aigne-framework`) | TypeScript (Node.js) | ✅ Local + cloud | Active OSS; mountable module pattern | Treats any MCP server as an AFS module; supports Ollama, OpenAI, Claude, Gemini, DeepSeek |
| 4 | **Official MCP TypeScript SDK** (same as #1 TS) | TypeScript | ✅ | Already in EndogenAI `infrastructure/mcp/` | Provides `StdioTransport` and `StreamableHTTPServerTransport` |

Secondary frameworks of interest (not direct MCP):
- **NullClaw** (Zig) — 678 KB agent runtime, 1 MB RAM, ~2 ms boot. Not MCP-native but demonstrates ultra-lean agent runtimes relevant to signal-processing modules.
- **GenerateAgents.md** — Python tool; uses DSPy + LiteLLM to auto-generate `AGENTS.md` from a codebase; supports Ollama endpoints via LiteLLM. Not a server framework but directly relevant to EndogenAI AGENTS.md maintenance.

---

### Sub-question 2 — Which support local-first deployment (no cloud dependency)?

**All four frameworks in the table support fully local deployment.** None require cloud services.

Key distinction between frameworks:

| Deployment mode | Official SDK (TS) | FastMCP (Python) | AIGNE |
|-----------------|-------------------|------------------|-------|
| Same-process (stdio) | ✅ | ✅ | ✅ via stdio subprocess |
| Local HTTP (127.0.0.1) | ✅ `StreamableHTTPServerTransport` | ✅ `mcp.run(transport="http")` | ✅ |
| LAN HTTP (0.0.0.0) | ✅ (with auth) | ✅ (with auth) | ✅ |
| Docker + Ollama | ✅ `host.docker.internal:11434` | ✅ same | ✅ same |
| No internet required | ✅ | ✅ | ✅ |

**EndogenAI already operates in the fully local mode**: `infrastructure/mcp/src/run.ts` uses
`StreamableHTTPServerTransport` on port 8080 with no cloud calls.

---

### Sub-question 3 — Multi-agent routing, tool discovery, and auth (locally)

#### Official MCP SDK (as used in EndogenAI)

- **Routing**: The existing `ContextBroker` routes `MCPContext` messages between modules by
  querying `CapabilityRegistry.findByAcceptedContentType()`. This is endogenous routing — no
  external router needed for the current single-server topology.
- **Tool discovery**: `ListToolsRequestSchema` — clients call `tools/list` on the server.
  Resources available via `ListResourcesRequestSchema` and `brain://` URI registry.
- **Auth**: None currently implemented. The official SDK (v2025-06-18) specifies an **OAuth 2.1
  authorization server** profile for production HTTP deployment (Phase 8 MCP OAuth Executive
  already handles this). For local/LAN use, a shared secret (`Authorization: Bearer <token>`)
  header check in the HTTP layer is the minimum recommended guard.

#### FastMCP (Python)

- Provides **automatic schema generation** from Python function signatures — tools declared as
  decorated functions, validated automatically.
- **Auth**: FastMCP 3.x includes `RemoteAuthProvider` and JWT audience validation (from
  PrefectHQ/fastmcp recent commits). Compatible with the same OAuth 2.1 flow EndogenAI uses.
- **Tool discovery**: same `tools/list` endpoint; FastMCP adds `discover` CLI command for
  service-level browsing.

#### AIGNE

- Treats every MCP server as a **mountable module** in a filesystem abstraction
  (`/modules/<name>/`). Tool calls become `afs_exec()` calls on filesystem paths.
- Supports **multi-LLM routing**: can target Ollama, OpenAI, Claude, Gemini, or DeepSeek per
  request — relevant for the model-tiering goal in Domain C.
- Auth: inherits from the mounted MCP servers; no additional auth layer.

---

### Sub-question 4 — Performance on Apple Silicon (M1 / M4)

| Runtime | M1 notes | M4 notes |
|---------|----------|----------|
| Node.js / TypeScript MCP (existing) | Runs natively (ARM64 binary via `brew`). No Rosetta. 8080 HTTP overhead is <1 ms for local calls. | Same — M4 is faster but no architectural change needed. |
| FastMCP (Python via `uv`) | `uv` produces ARM64 wheels natively. FastMCP startup is ~200–400 ms cold, <5 ms per tool call. | Same + Apple's M4 Neural Engine unused (not BNNS-wired by default). |
| AIGNE (TypeScript) | Same as Node.js MCP. | Same. |
| Ollama (`llama3`, `qwen2.5-coder`) | Uses Metal GPU acceleration on M1/M4 by default. Already in EndogenAI stack. | M4 Max has faster matrix units; 7B models run at ~50–80 t/s vs ~30–50 t/s on M1. |

No performance blockers for any candidate framework on Apple Silicon. All run natively.

---

### Sub-question 5 — State of locally-distributed MCP (multiple servers on a LAN)

**MCP transport spec (2025-06-18) status**: The protocol is fully transport-agnostic. Streamable
HTTP is designed for multi-client networked deployment. A server bound to `0.0.0.0:<port>` is
reachable from any LAN peer.

**Official security guidance (from spec):**
> When running locally, servers SHOULD bind only to localhost (127.0.0.1) rather than all network
> interfaces (0.0.0.0). Validate the `Origin` header on all incoming HTTP connections to prevent
> DNS rebinding attacks. Implement proper authentication for all connections.

**LAN distribution patterns (2026 state of practice):**

1. **Direct HTTP** — each cognitive module exposes a Streamable HTTP MCP server (e.g. `:8080`,
   `:8081`, …). The client (VS Code / gateway) connects directly to each by URL. Simple, no broker
   required. Requires static or discovered server addresses.

2. **Gateway proxy** — a single entry-point HTTP gateway (e.g. EndogenAI's Hono gateway from
   Phase 8) routes requests to upstream MCP servers by capability lookup. Clients see one URL.
   Adds latency ≈ 1 ms for LAN calls. Preferred for production.

3. **Docker Compose mesh** — all MCP servers in a compose file share a named network. Each service
   is addressable by service name (`http://mcp-memory:8080`). Ollama on the host is reachable via
   `host.docker.internal:11434`. Linux requires
   `extra_hosts: ["host.docker.internal:host-gateway"]` for the Ollama bridge.

4. **mDNS / Avahi discovery** — servers broadcast via mDNS (`_mcp._tcp.local`). Clients discover
   without static config. Currently community-experimental; no official MCP mDNS spec exists.
   Not recommended for EndogenAI until a standard emerges.

Pattern 2 (gateway proxy) aligns with what Phase 8 already delivers (`apps/default/server` and
the Hono gateway). Pattern 3 is what the current `docker-compose.yml` implements.

---

## Architecture Patterns for LAN-Distributed MCP

```
                  ┌────────────────────────────────────────────┐
                  │             M1 Mac (primary host)           │
                  │                                             │
                  │   Ollama :11434  ◄──── all MCP servers     │
                  │                                             │
                  │   Hono Gateway :3000 (Phase 8)             │
                  │     │                                       │
                  │     ├─► infrastructure/mcp :8080           │
                  │     │     (CapabilityRegistry, Broker)      │
                  │     │                                       │
                  │     ├─► group-ii module MCP :8081           │
                  │     ├─► group-iii module MCP :8082          │
                  │     └─► group-iv module MCP :8083           │
                  │                                             │
                  └───────────────────┬─────────────────────────┘
                                      │ LAN (same subnet)
                  ┌───────────────────▼─────────────────────────┐
                  │            Sheela's M4 (LAN peer)            │
                  │                                              │
                  │  VS Code Copilot → http://<M1-IP>:3000/mcp  │
                  │  (deferred — same gateway URL, different IP) │
                  └──────────────────────────────────────────────┘
```

**Key design decisions for this topology:**
- The **Hono Gateway** (Phase 8) already proxies MCP calls — it is the correct LAN entry point.
  No separate MCP proxy is needed.
- The `infrastructure/mcp` server remains the **central registry and broker**; per-module MCP
  servers (Phases 5–7) register capabilities with it at startup.
- Ollama stays on the host (not inside a container) for Metal GPU access; containers reach it
  via `host.docker.internal:11434`.
- The `brain://` URI registry at `resources/uri-registry.json` provides static capability
  discovery; dynamic discovery uses `CapabilityRegistry.list()`.

---

## Candidate MCP Frameworks — Local-First Ranking

| Rank | Framework | Verdict | Rationale |
|------|-----------|---------|-----------|
| 1 | **Official TS SDK** (current) | ✅ **Keep** | Already in `infrastructure/mcp/`. Protocol-current (2025-06-18). No migration cost. |
| 2 | **FastMCP** (Python) | ✅ **Adopt for Python modules** | Dominant Python MCP framework. Use for Phases 5–7 Python cognitive modules to expose tools without boilerplate. `uv add fastmcp` in each `pyproject.toml`. |
| 3 | **AIGNE** | ⚠️ **Watch** | Interesting filesystem-as-context model; not yet battle-tested at scale. Revisit for Phase 9+ if the AFS abstraction adds value to cross-module context sharing. |
| 4 | **NullClaw** | ❌ **Defer** | Zig-only; no SDK integration path with existing TS/Python stack. Re-evaluate only if edge/embedded targets emerge. |

---

## Recommended Approach for EndogenAI Phase 9+

### Immediate actions (within current phases)

1. **No change to `infrastructure/mcp/`** — the Streamable HTTP TypeScript server is correct
   and protocol-current. Continue using `@modelcontextprotocol/sdk`.

2. **Adopt FastMCP for Python cognitive modules** (Phases 5–7):

   ```python
   # Example: annotate a Python cognitive module's MCP tools
   from fastmcp import FastMCP

   mcp = FastMCP("memory-module")

   @mcp.tool
   async def store_memory(content: str, tags: list[str]) -> dict:
       """Store a memory item in the working memory store."""
       ...

   if __name__ == "__main__":
       mcp.run(transport="http", port=8081)
   ```

   Each module adds `fastmcp` via `uv add fastmcp` in its `pyproject.toml`.

3. **Docker Compose** — add per-module MCP services alongside the existing stack.
   Ensure `host.docker.internal:11434` (with Linux `extra_hosts`) for Ollama bridging.

### Phase 9+ LAN distribution

1. The **Hono Gateway** (Phase 8) becomes the LAN entry point. Add a capability-discovery
   endpoint (`GET /mcp/capabilities`) that calls `CapabilityRegistry.list()` on the central
   MCP server — giving LAN clients a service catalog without per-module discovery.

2. **Split-server**: per-module MCP servers register with the central `CapabilityRegistry`
   at startup using `register_capability`. This is already the intended design —
   `ContextBroker` routes to the correct module by capability.

3. **Auth for LAN**: add a shared `Authorization: Bearer <token>` check at the Hono gateway
   for all `/mcp` routes before exposing on `0.0.0.0`. The Phase 8 MCP OAuth Executive
   handles JWT auth; reuse the same token for LAN peers.

4. **Sheela's M4** (deferred per research plan): once the gateway is on LAN (`0.0.0.0:3000`),
   VS Code on Sheela's M4 connects by pointing to `http://<M1-IP>:3000` — no topology change
   required on the EndogenAI side.

---

## Integration Notes for `infrastructure/mcp/`

| File | Current state | Integration note |
|------|--------------|-----------------|
| `src/run.ts` | Streamable HTTP on `:8080`, localhost only | To enable LAN, change listen address from implicit localhost to `0.0.0.0` AND add Origin-header validation + Bearer token middleware first. |
| `src/server.ts` | Exposes `register_capability`, `publish_context`, `list_states` | Add `list_capabilities` tool (alias for `list_states` with full capability payload) to serve gateway discovery calls. |
| `src/registry.ts` | `CapabilityRegistry.findByAcceptedContentType()` | Extend with `findByModuleGroup(group: string)` for Phase 9+ group-level routing. |
| `src/broker.ts` | Routes `MCPContext` by accepted content-type | No change needed for Phase 9 single-host topology; add queue-backed delivery for multi-host when needed. |

---

## Open Questions

1. **FastMCP vs. official Python SDK** — FastMCP's standalone v3.x diverges from the Python
   SDK's embedded v1. Are there compatibility issues for modules that import both? Answer:
   FastMCP 3.x has an upgrade guide from the embedded SDK; no breaking protocol changes. Low risk.

2. **Per-module MCP server port allocation** — which ports do Phases 5–7 modules use? No
   formal allocation exists yet in `docker-compose.yml`. Recommend: `8081–8089` block for
   cognitive module MCP servers; `8080` reserved for central `infrastructure/mcp`.

3. **mDNS discovery** — no official MCP mDNS spec as of March 2026. Monitor
   `modelcontextprotocol/specification` for a service-discovery extension. Do not implement
   bespoke mDNS until an official profile lands.

---

_Sources fetched: `docs/research/sources/issue-35/aigne-framework.md`, `docs/research/sources/issue-35/freecodecamp-multiagent-docker.md`, `docs/research/sources/issue-35/generate-agents-md.md`. Transport spec: `https://modelcontextprotocol.io/docs/concepts/transports` (live fetch). FastMCP: `https://github.com/PrefectHQ/fastmcp` (live fetch). Manifest base: `docs/research/sources/issue-32-manifest.md`._
