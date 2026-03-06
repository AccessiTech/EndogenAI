# Phase 9 — Detailed Workplan: Security, Deployment & Documentation

> **Status**: Detailed workplan — 2026-03-04
> **Milestone**: M9 — Production-Ready
> **Prerequisite**: M8 complete (153/153 tests passing, 2026-03-03)
> **Research references**:
> - [phase-9-neuroscience-security-deployment.md](phase-9-neuroscience-security-deployment.md) (D1) — biological analogues per sub-phase
> - [phase-9-technologies-security-deployment.md](phase-9-technologies-security-deployment.md) (D2) — technology stack per sub-phase
> - [phase-9-synthesis-workplan.md](phase-9-synthesis-workplan.md) (D3) — recommended checklist, decision log, gate sequence, open questions

---

## Contents

1. [Phase 9 Architecture Summary](#1-phase-9-architecture-summary)
2. [Prerequisites (Gate 0)](#2-prerequisites-gate-0)
3. [Sub-phase Build Order and Gate Map](#3-sub-phase-build-order-and-gate-map)
4. [§9.0 — Deferred Phase 8 Items (Gate 1)](#4-90--deferred-phase-8-items-gate-1)
5. [§9.1 — Security (Gate 2)](#5-91--security-gate-2)
6. [§9.2 — Deployment (Gate 3)](#6-92--deployment-gate-3)
7. [§9.3 — Documentation Completion (Gate 4)](#7-93--documentation-completion-gate-4)
8. [Environment Variables Catalogue](#8-environment-variables-catalogue)
9. [New Files and Directories Created by Phase 9](#9-new-files-and-directories-created-by-phase-9)
10. [Test Requirements](#10-test-requirements)
11. [M9 Milestone Declaration Gate](#11-m9-milestone-declaration-gate)
12. [Open Questions (Remaining)](#12-open-questions-remaining)
13. [Decisions Recorded](#13-decisions-recorded)

---

## 1. Phase 9 Architecture Summary

Phase 9 is the **production-hardening and completion** layer of EndogenAI. It adds three cross-cutting concerns that were deliberately deferred from the functional build phases (1–8):

| Layer added | What it does | Brain analogue (D1) |
|---|---|---|
| **Security** (`security/`) | Capability-bounded policy enforcement, container sandboxing, network isolation, workload identity | CNS immune privilege — BBB + microglia + MHC-I + glial scar |
| **Deployment** (`deploy/`) | Production-ready container images; Kubernetes manifests for all 16 services; local-stack validation | Neurogenesis + myelination + cerebral autoregulation |
| **Documentation** (existing `docs/`) | Coherent, cross-linked, complete self-description of the system | Default mode network + metacognitive self-model + Hebbian LTP |

### What Phase 9 adds to the existing layers

```
Phases 1–8 built the cognitive architecture:

  Group I  — Signal Processing (sensory-input, perception, attention-filtering)
  Group II — Cognitive Processing (working-memory, short-term, long-term, episodic, reasoning, affective)
  Group III— Executive Output (executive-agent, agent-runtime, motor-output)
  Group IV — Adaptive Systems (learning-adaptation, metacognition)
  Infra    — infrastructure/mcp (MCP server), infrastructure/a2a (A2A broker)
  Apps     — apps/default/server (Hono gateway), apps/default/client (React SPA)

Phase 9 wraps the full system with:

  security/
    policies/         ← OPA Rego rules (derived endogenously from agent-card.json)
    data/             ← Generated OPA data (gen_opa_data.py)
    review/           ← Inter-module security review document
    README.md

  deploy/
    docker/           ← Base Dockerfiles (Python + Node)
    k8s/              ← Kubernetes manifests for all 16 services
    README.md

  docs/guides/security.md   ← Authored in §9.3
  docs/guides/deployment.md ← Already authored [x]; updated if needed
```

Phase 9 does **not** add new cognitive capability — it hardens, packages, and documents what already exists. Treating these concerns as an afterthought is a common failure mode; the biological analogy is the brain's immune privilege and myelination, which are structurally necessary for safe operation — not cosmetic additions.

### Module inventory (confirmed 2026-03-04)

| Group | Module | Service name | Port |
|---|---|---|---|
| Group I | sensory-input | `sensory-input` | 8001 |
| Group I | perception | `perception` | 8002 |
| Group I | attention-filtering | `attention-filtering` | 8003 |
| Group II | working-memory | `working-memory` | 8010 |
| Group II | short-term-memory | `short-term-memory` | 8011 |
| Group II | long-term-memory | `long-term-memory` | 8012 |
| Group II | episodic-memory | `episodic-memory` | 8013 |
| Group II | reasoning | `reasoning` | 8014 |
| Group II | affective | `affective` | 8015 |
| Group III | executive-agent | `executive-agent` | 8020 |
| Group III | agent-runtime | `agent-runtime` | 8021 |
| Group III | motor-output | `motor-output` | 8022 |
| Group IV | learning-adaptation | `learning-adaptation` | 8030 |
| Group IV | metacognition | `metacognition` | 8031 |
| Infra | infrastructure/mcp | `mcp-server` | 8000 |
| Apps | apps/default/server | `gateway` | 3001 |

**Total: 14 modules + 2 infrastructure/app services = 16 Dockerfiles and 16 Kubernetes Deployment manifests.**

---

## 2. Prerequisites (Gate 0)

All items below must be confirmed before any Phase 9 code is written.

### 2.1 M8 Completion Verification

```bash
# Confirm M8 milestone was declared
grep "M8" docs/Workplan.md | grep -i "complete\|✅"

# Run the full test suite — must be 153+ tests passing
pnpm run test
# TypeScript clean
pnpm run typecheck
# Lint clean
pnpm run lint

# Phase 8 services smoke-test
curl -s http://localhost:3001/api/health | grep '"status":"ok"'
curl -s http://localhost:8000/.well-known/oauth-protected-resource | python3 -m json.tool
```

- [x] M8 declared complete (153/153 tests passing, 2026-03-03)
- [x] All architecture decisions resolved (D3 §8.1 Decision Log, 2026-03-04)

### 2.2 Schemas-First Gate — `agent-card.schema.json` (BLOCKING)

> **Confirmed missing** (2026-03-04): `shared/schemas/agent-card.schema.json` does not exist.
> This is the **first task of Phase 9** and blocks all of §9.0.1, §9.1.2, and the OPA data generator.
> The Schema Executive must land this file before any Phase 9 implementation agent proceeds.

**What to author** (`shared/schemas/agent-card.schema.json`):
- `$schema`, `$id`, `title`, `description`, `type: object` (required per `shared/AGENTS.md`)
- Required fields (based on existing `agent-card.json` content across modules): `id`, `name`, `version`, `description`, `a2aEndpoint`, `capabilities`, `mcpTools`
- Reference `docs/architecture.md` and an existing module `agent-card.json` (e.g. `modules/group-iv-adaptive-systems/metacognition/agent-card.json`) to derive the exact shape

```bash
# Verify absence (confirms the task is still needed)
ls shared/schemas/agent-card.schema.json   # should fail with "No such file"

# After authoring — validate:
uv run python scripts/schema/validate_all_schemas.py
cd shared && buf lint
```

- [ ] **[Gate 0 blocker]** Author `shared/schemas/agent-card.schema.json` — derive shape from existing `agent-card.json` files; validate with `validate_all_schemas.py`; delegate to Schema Executive
- [ ] `uv run python scripts/schema/validate_all_schemas.py` exits 0 with new schema included
- [ ] `cd shared && buf lint` exits 0

_The `/api/agents` route (§9.0.1) returns `AgentCard[]`. The OPA data generator (§9.1.2) reads `agent-card.json` files. Both are blocked until the schema exists and validates._

### 2.3 Module Inventory Confirmation

```bash
find modules/ -name "agent-card.json" | sort
# Should yield exactly 14 entries
find modules/ -name "agent-card.json" | wc -l
```

- [x] 14 modules confirmed across Groups I–IV (2026-03-04)
- [x] 16 services total (14 modules + `infrastructure/mcp` + `apps/default/server`)

### 2.4 OTel Coverage Pre-Check (prerequisite for §9.0.4)

```bash
# Grep for MCPContext construction in test fixtures — look for missing traceparent
grep -r "MCPContext\|mcp_context" modules/ --include="*.py" -l
grep -r "traceparent" modules/ --include="*.py" | wc -l
```

- [ ] `traceparent` grep across all module test fixtures confirms OTel emission in all 14 modules before promoting to `required`

---

## 3. Sub-phase Build Order and Gate Map

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Phase 9 — Build Sequence and Gate Map                                       │
│                                                                              │
│  GATE 0: M8 declared complete; agent-card.schema.json AUTHORED (confirmed   │
│          missing 2026-03-04 — Schema Executive first); 14 modules           │
│          confirmed; OTel traceparent coverage pre-checked                   │
│                                                                              │
│  ─── §9.0 Deferred Phase 8 Items (all items parallel, independent) ───────  │
│      9.0.1 /api/agents endpoint + Internals panel wiring                    │
│      9.0.2 resources/subscribe live notifications                           │
│      9.0.3 Lighthouse CI live audit (≥ 90)                                  │
│      9.0.4 traceparent promoted to required                                 │
│                                                                              │
│  GATE 1: All 9.0 items complete; test suite still 153+ passing              │
│                                                                              │
│  ─── §9.1 Security (parallel with §9.2) ───────────────────────────────── │
│  │   9.1.1 OPA shared server + security/ directory                         │
│  │   9.1.2 scripts/gen_opa_data.py                                         │
│  │   9.1.3 module-capabilities.rego                                        │
│  │   9.1.4 inter-module-comms.rego                                         │
│  │   9.1.5 gVisor RuntimeClass + docker-compose security profile           │
│  │   9.1.6 Self-signed mTLS CA + cert generation script                    │
│  │   9.1.7 Trivy integration                                               │
│  │   9.1.8 securityContext hardening                                       │
│  │   9.1.9 Inter-module security review                                    │
│  │   9.1.10 docs/guides/security.md (also counts as 9.3 deliverable)       │
│  │                                                                          │
│  ─── §9.2 Deployment (parallel with §9.1) ────────────────────────────── │
│      9.2.1 Base Dockerfiles (Python + Node)                                │
│      9.2.2 Per-module Dockerfiles (all 16 services)                        │
│      9.2.3 scripts/build_images.sh                                         │
│      9.2.4 deploy/k8s/ directory structure                                 │
│      9.2.5 Namespace + NetworkPolicy manifests                             │
│      9.2.6 Per-module Deployment + Service + HPA manifests                 │
│      9.2.7 gVisor RuntimeClass manifest                                    │
│      9.2.8 docker-compose.yml audit + security profile                     │
│      9.2.9 docker-compose.override.yml                                     │
│      9.2.10 deploy/k8s/README.md                                           │
│                                                                              │
│  GATE 2: opa test passes; trivy scans pass; kubectl dry-run passes          │
│  GATE 3: docker compose up (full stack); kubectl apply dry-run; all tests   │
│                                                                              │
│  ─── §9.3 Documentation Completion (parallel with §§9.1–9.2) ─────────── │
│      9.3.1 docs/guides/security.md — primary remaining doc gap             │
│      9.3.2 security/README.md                                              │
│      9.3.3 observability/README.md update (deferred from M8)              │
│      9.3.4 markdown-link-check setup + broken-link audit                  │
│      9.3.5 Cross-linking audit                                             │
│      9.3.6 Module README audit (14 modules)                               │
│      9.3.7 AsyncAPI spec for resources/subscribe (optional)               │
│      9.3.8 mkdocs.yml configuration (optional)                            │
│                                                                              │
│  GATE 4: markdown-link-check passes; docs/guides/security.md authored      │
│                                                                              │
│  ─── M9 MILESTONE DECLARATION GATE ────────────────────────────────────── │
│      kubectl apply dry-run: exit 0                                         │
│      docker compose up: full stack healthy                                 │
│      153+ tests passing                                                    │
│      pnpm run lighthouse: all ≥ 90                                         │
│      opa test: all policy tests passing                                    │
│      markdown-link-check: zero broken internal links                       │
│      docs/guides/security.md authored                                      │
│      deploy/k8s/README.md authored                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Critical path**: `9.2.1 Dockerfiles → 9.2.2 per-module Dockerfiles → 9.2.6 K8s manifests → kubectl apply dry-run → docker compose up full stack → M9`

**OPA / gVisor / mTLS (§9.1) do not block the critical path** — security hardening proceeds in parallel with deployment work. Gates 2 and 3 converge before M9 declaration.

**Documentation (§9.3) runs in parallel throughout** — docs should be authored alongside their implementation counterparts, not after, per the Hebbian LTP principle in AGENTS.md.

---

## 4. §9.0 — Deferred Phase 8 Items (Gate 1)

_Biological analogue: hippocampal SWR replay completing offline consolidation — these items are present as stubs (memory traces) from Phase 8 but have not been fully integrated into the running system._

All four items are **independent** and can be worked in parallel. Complete all four before closing Gate 1.

---

### 4.1 — 9.0.1: `/api/agents` Endpoint + Internals Panel Wiring

**Biological analogue**: _MHC-I antigen presentation — every module announces its identity; the Internals panel is the immune surveillance layer that aggregates those announcements._

**What**: Implement `GET /api/agents` in the Hono gateway, which fetches `/.well-known/agent-card.json` from each module and returns `{ agents: AgentCard[], timestamp: ISO8601 }`. Wire the browser Internals panel to call `/api/agents` instead of `/api/resources`.

**Why**: The Internals panel currently falls back to `/api/resources` for module listing (Phase 8 placeholder). Live agent-card discovery was deferred from M8.

**Files**:
- `apps/default/server/src/routes/agents.ts` — new route module
- `apps/default/server/src/app.ts` — mount `agentsRouter`
- `apps/default/client/src/tabs/Internals.tsx` — update agent-card panel

**Implementation**:

```typescript
// apps/default/server/src/routes/agents.ts
import { Hono } from 'hono'

const MODULE_URLS = (process.env.MODULE_URLS ?? '').split(',').filter(Boolean)

export const agentsRouter = new Hono()

agentsRouter.get('/agents', async (c) => {
  const results = await Promise.allSettled(
    MODULE_URLS.map(url =>
      fetch(`${url}/.well-known/agent-card.json`, {
        signal: AbortSignal.timeout(2000),
      }).then(r => r.json())
    )
  )
  const agents = results
    .filter(r => r.status === 'fulfilled')
    .map(r => (r as PromiseFulfilledResult<unknown>).value)
  return c.json({ agents, timestamp: new Date().toISOString() })
})
```

**Schema gate**: `shared/schemas/agent-card.schema.json` is **confirmed absent** (2026-03-04). The Schema Executive must author and land it (Gate 0 §2.2) before this route is implemented. Do not proceed with §9.0.1 until `uv run python scripts/schema/validate_all_schemas.py` passes with the new schema included.

**Mount in `app.ts`**:
```typescript
import { agentsRouter } from './routes/agents.js'
// ...
app.use('/api/agents', authMiddleware)
app.route('/api', agentsRouter)
```

**Environment variable**: `MODULE_URLS` — comma-separated base URLs for all 16 services (see §8 env catalogue).

**Test requirement** (`apps/default/server/tests/agents.test.ts`):

| Test | Scenario | Assertion |
|---|---|---|
| Happy path | 3 mock modules return valid agent-cards | `agents` array has 3 entries |
| Partial failure | 1 of 3 mocks times out | Response includes 2 healthy agents; no 500 error |
| Timeout | All modules unreachable | Returns `{ agents: [], timestamp: ... }` with 200 |
| Unauthenticated | Request without JWT | `401` |
| Timestamp format | Valid response | `timestamp` is ISO 8601 |

**Verification**:
```bash
# With all module services running
curl -s http://localhost:3001/api/agents \
  -H "Authorization: Bearer <token>" | python3 -m json.tool
# → agents array with ≥ 1 entries; each has name, version, capabilities
```

---

### 4.2 — 9.0.2: `resources/subscribe` Live Notifications

**Biological analogue**: _Dopaminergic volume transmission — a single Working Memory write fans out `notifications/resources/updated` across all registered SSE subscribers._

**What**: Replace the Working Memory module's stub `resources/subscribe` handler with a live subscriber registry. On any resource write, emit `notifications/resources/updated` via the A2A event bus. Verify end-to-end delivery to the browser Internals panel via SSE.

**Files**:
- `modules/group-ii-cognitive-processing/memory/working-memory/src/` — subscriber registry + write hook
- `infrastructure/mcp/src/` — route `notifications/resources/updated` A2A events to SSE client sessions
- No gateway changes required (existing SSE relay propagates all MCP push events)

**Implementation sketch**:

```python
# modules/group-ii-cognitive-processing/memory/working-memory/src/subscriptions.py
from collections import defaultdict
from typing import Callable

# sessionId → callback
_subscribers: dict[str, Callable[[str], None]] = {}

def subscribe(session_id: str, callback: Callable[[str], None]) -> None:
    _subscribers[session_id] = callback

def unsubscribe(session_id: str) -> None:
    _subscribers.pop(session_id, None)

def notify_all(uri: str) -> None:
    for callback in list(_subscribers.values()):
        try:
            callback(uri)
        except Exception:
            pass  # dead subscriber — prune on next event

async def write_resource(resource_id: str, content: object) -> None:
    await store.set(resource_id, content)
    uri = f"brain://working-memory/{resource_id}"
    notify_all(uri)
    # Emit via A2A event bus for MCP server relay
    await a2a_client.send_event(
        method="notifications/resources/updated",
        params={"uri": uri}
    )
```

**End-to-end flow**:
1. Browser Internals panel subscribes by calling `resources/subscribe` on the MCP server
2. MCP server registers session in working-memory module
3. Any write to `brain://working-memory/*` calls `notify_all(uri)`
4. A2A event propagates to MCP server
5. MCP server emits `notifications/resources/updated` SSE event on the subscribed session channel
6. Gateway relays to browser `EventSource`

**AsyncAPI spec**: author `docs/research/sources/phase-9/asyncapi-resource-notifications.yaml` (optional but recommended — see §9.3.7).

**Test requirement** (`modules/group-ii-cognitive-processing/memory/working-memory/tests/`):

| Test | Scenario | Assertion |
|---|---|---|
| Subscribe + write | Register callback, write resource | Callback called within 50 ms with correct URI |
| Multiple subscribers | 3 callbacks registered | All 3 called on write |
| Unsubscribe | Unsubscribe after registration, write resource | Callback NOT called |
| Dead subscriber | Callback raises exception | Other subscribers still notified; no propagation |
| E2E: browser receives event | Write to working memory → SSE stream | `notifications/resources/updated` event received within 500 ms |

---

### 4.3 — 9.0.3: Lighthouse CI Live Audit (≥ 90)

**Biological analogue**: _Myelination of sensory pathways before birth — performance and accessibility gating before the system is declared production-ready._

**What**: Install `@lhci/cli`, author `lighthouserc.json` with ≥ 90 thresholds across all four categories, run the live audit against `localhost:5173`, remediate any failures, and integrate as `pnpm run lighthouse` in CI.

**Files**:
- `apps/default/client/package.json` — add `@lhci/cli` dev dep + `lighthouse` script
- `apps/default/client/lighthouserc.json` — new Lighthouse CI config

**Lighthouse CI config**:
```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:5173"],
      "numberOfRuns": 3,
      "startServerCommand": "pnpm run preview",
      "startServerReadyPattern": "Local:"
    },
    "assert": {
      "preset": "lighthouse:no-pwa",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["error", { "minScore": 0.9 }]
      }
    },
    "upload": {
      "target": "filesystem",
      "outputDir": ".lighthouseci"
    }
  }
}
```

**`package.json` script**:
```json
{
  "scripts": {
    "lighthouse": "pnpm run build && lhci autorun"
  }
}
```

**Common remediation items** (consult the JSON report under `.lighthouseci/`):
- Performance: use `<img loading="lazy">`, serve WebP, eliminate render-blocking scripts
- Accessibility: add `aria-label` to icon buttons; verify colour contrast ≥ 4.5:1
- Best Practices: HTTPS in production; no deprecated APIs
- SEO: add `<meta name="description">`, verify `<title>` is descriptive

**Verification**:
```bash
cd apps/default/client && pnpm run lighthouse
# lhci autorun exits 0 only when all four categories ≥ 0.9
```

---

### 4.4 — 9.0.4: Promote `traceparent` to `required`

**Biological analogue**: _White-matter myelination completes signal path integrity — all long-range projections are traceable once myelination is finished._

**What**: Move `traceparent` from the `properties` block (optional) to the `required` array in `shared/schemas/mcp-context.schema.json`. Fix any test fixtures that construct `MCPContext` without `traceparent`.

**Files**:
- `shared/schemas/mcp-context.schema.json` — schema change
- `shared/types/` — update TypeScript interface if `traceparent` is typed optional
- All module test fixtures constructing `MCPContext` objects — add `traceparent` field

**Pre-flight check (must run before schema change)**:
```bash
# Confirm all modules emit traceparent in production code paths
grep -r "traceparent" modules/ --include="*.py" | grep -v test | wc -l

# Find test fixtures that construct MCPContext without traceparent
grep -r "MCPContext\|mcp_context" modules/ --include="*.py" -l | \
  xargs grep -L "traceparent"
# Output should be empty (all fixtures include traceparent) before proceeding
```

**Schema change**:
```json
{
  "required": ["session_id", "module_id", "timestamp", "traceparent"],
  "properties": {
    "traceparent": {
      "type": "string",
      "pattern": "^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
      "description": "W3C Trace Context traceparent header value"
    }
  }
}
```

**Post-change verification**:
```bash
cd shared && buf lint
pnpm run typecheck
pnpm run test   # all 153+ tests must pass
```

**Note**: this is a **breaking schema change**. Any consumer that constructs `MCPContext` without `traceparent` will fail schema validation after this change. The pre-flight grep is mandatory — do not land this change until pre-flight confirms zero omissions.

---

## 5. §9.1 — Security (Gate 2)

_Biological analogue: CNS immune privilege — multi-layer defence in depth: BBB (gVisor) + microglial surveillance (OPA) + physical boundary enforcement (NetworkPolicy) + workload identity (mTLS)._

**Architecture decision (confirmed 2026-03-04)**:
- OPA deployed as a **single shared server** (not per-module sidecar); audit mode first, promote to enforce after validation
- gVisor scope: **CI + production only**; standard `runc` on local macOS dev machines (no KVM on macOS Docker Desktop)
- mTLS: **self-signed CA**; SPIFFE/SPIRE deferred to Phase 10

---

### 5.1 — 9.1.1: OPA Shared Server Setup + `security/` Directory Structure

**Biological analogue**: _Microglia as continuous policy enforcement agents — always patrolling, evaluating patterns, logging anomalies._

**What**: Create the `security/` root directory and configure a shared OPA server in Docker Compose under the new `security` profile.

**Directory structure**:
```
security/
  policies/
    module-capabilities.rego   # Capability isolation rules
    inter-module-comms.rego    # A2A task delegation rules
    helpers.rego               # Shared utility rules
  data/
    modules.json               # Generated OPA data (auto-generated by gen_opa_data.py)
  tests/
    module-capabilities_test.rego
    inter-module-comms_test.rego
  review/
    phase-9-security-review.md
  README.md
```

**Docker Compose — `security` profile addition**:
```yaml
# Add to docker-compose.yml under services:
  opa:
    image: openpolicyagent/opa:latest-static
    profiles: [security]
    command: run --server --log-level=info
      --watch /policies /data
    ports:
      - "8181:8181"
    volumes:
      - ./security/policies:/policies:ro
      - ./security/data:/data:ro
    healthcheck:
      test: ["CMD", "wget", "-q", "-O-", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

**Usage**: `docker compose --profile security up -d opa` starts the shared OPA server. All 16 services call `http://opa:8181/v1/data/endogenai` for policy checks.

**Verification**:
```bash
docker compose --profile security up -d opa
curl -s http://localhost:8181/health | grep '"status":"ok"'
curl -s http://localhost:8181/v1/policies | python3 -m json.tool
```

---

### 5.2 — 9.1.2: `scripts/gen_opa_data.py` — Endogenous Policy Data Generation

**Biological analogue**: _Endogenous-first principle — OPA data derived from existing system knowledge (agent-card.json files), not authored in isolation._

**What**: Author a script that reads all `agent-card.json` files in `modules/`, extracts `id`, `capabilities`, and `consumers` fields, and writes `security/data/modules.json`. This ensures OPA policies are always grounded in the declared module capabilities.

**File**: `scripts/gen_opa_data.py`

**Script skeleton**:
```python
#!/usr/bin/env python3
"""
Generate security/data/modules.json from all modules/*/agent-card.json files.

Usage:
    uv run python scripts/gen_opa_data.py
    uv run python scripts/gen_opa_data.py --dry-run

Output:
    security/data/modules.json — OPA data document for capability policies.
    Format: { "modules": { "<module_id>": { "capabilities": [...], "consumers": [...] } } }
"""
import argparse
import json
import pathlib


def collect_agent_cards(modules_root: pathlib.Path) -> dict:
    modules = {}
    for card_path in sorted(modules_root.rglob("agent-card.json")):
        card = json.loads(card_path.read_text())
        module_id = card.get("name") or card_path.parent.name
        modules[module_id] = {
            "capabilities": card.get("capabilities", []),
            "consumers": card.get("consumers", []),
            "url": card.get("url", ""),
        }
    return {"modules": modules}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).parent.parent
    data = collect_agent_cards(repo_root / "modules")

    output_path = repo_root / "security" / "data" / "modules.json"
    if args.dry_run:
        print(json.dumps(data, indent=2))
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2))
        print(f"Written: {output_path} ({len(data['modules'])} modules)")


if __name__ == "__main__":
    main()
```

**Run and commit the generated data**:
```bash
uv run python scripts/gen_opa_data.py
# Confirm 14 module entries
python3 -c "import json; d=json.load(open('security/data/modules.json')); print(len(d['modules']))"
```

**Note**: re-run `gen_opa_data.py` whenever a module's `agent-card.json` capabilities change. Add this run to the CI pipeline as a pre-commit hook or a `pnpm run generate:opa-data` script.

---

### 5.3 — 9.1.3: Rego Capability Isolation Policies

**Biological analogue**: _MHC-II absence — neurons have no inherent right to access other modules' resources; access must be explicitly declared._

**File**: `security/policies/module-capabilities.rego`

```rego
# security/policies/module-capabilities.rego
package endogenai.module_capabilities

import future.keywords.in

# Default: deny unless explicitly allowed
default allow = false

# Allow if requested capability is declared in the module's agent-card data
allow {
    input.requested_capability in data.modules[input.module_id].capabilities
}

# Audit flag: request is allowed but at the edge of declared capabilities (last entry)
audit_boundary {
    allow
    last_idx := count(data.modules[input.module_id].capabilities) - 1
    data.modules[input.module_id].capabilities[last_idx] == input.requested_capability
}

# DAMP signal: module requests capability NOT in agent-card (possible compromise/misconfiguration)
anomaly {
    not allow
    data.modules[input.module_id]  # module exists in data
}
```

**OPA test** (`security/tests/module-capabilities_test.rego`):
```rego
package endogenai.module_capabilities_test

test_allow_declared_capability {
    allow with input as {"module_id": "sensory-input", "requested_capability": "signal:read"}
         with data as {"modules": {"sensory-input": {"capabilities": ["signal:read"]}}}
}

test_deny_undeclared_capability {
    not allow with input as {"module_id": "sensory-input", "requested_capability": "llm:generate"}
              with data as {"modules": {"sensory-input": {"capabilities": ["signal:read"]}}}
}

test_anomaly_on_undeclared {
    anomaly with input as {"module_id": "sensory-input", "requested_capability": "llm:generate"}
            with data as {"modules": {"sensory-input": {"capabilities": ["signal:read"]}}}
}
```

---

### 5.4 — 9.1.4: Rego Inter-Module Communications Policies

**Biological analogue**: _Astrocytic glial scar — containing lateral movement between modules; all inter-module traffic must route through defined pathways._

**File**: `security/policies/inter-module-comms.rego`

```rego
# security/policies/inter-module-comms.rego
package endogenai.inter_module_comms

import future.keywords.in

default allow_a2a_task = false

# Allow A2A task if the caller is a declared consumer of the target
allow_a2a_task {
    input.caller_module in data.modules[input.target_module].consumers
}

# Allow if target is the MCP server (infrastructure — all modules may call it)
allow_a2a_task {
    input.target_module == "mcp-server"
}

# Allow if caller is the gateway (apps gateway may call any module)
allow_a2a_task {
    input.caller_module == "gateway"
}

# Deny direct cross-module access where caller is not a declared consumer
deny_direct {
    not allow_a2a_task
    data.modules[input.caller_module]  # caller exists
    data.modules[input.target_module]  # target exists
}
```

**Test**: add `security/tests/inter-module-comms_test.rego` with cases for allowed consumer, disallowed direct access, and gateway bypass.

---

### 5.5 — 9.1.5: gVisor RuntimeClass Manifest + `runsc`-Compatible Dockerfiles

**Biological analogue**: _BBB tight junctions — modules cannot make raw syscalls past the application kernel boundary._

**What**: Create a Kubernetes `RuntimeClass` for gVisor. Add `runtime: runsc` to module services in the `docker-compose.yml` under the `security` profile (not the default `modules` profile). Ensure no Dockerfile uses `/proc` writes or raw sockets.

**File**: `deploy/k8s/runtime-class-gvisor.yaml`
```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
```

**Docker Compose integration** (under `security` profile services override):
```yaml
# docker-compose.override.yml (security profile extension)
services:
  working-memory:
    profiles: [security]
    runtime: runsc   # applied only when --profile security is active
```

**gVisor compatibility checklist for Python modules**:
- No raw socket creation (`socket.AF_PACKET`)
- No `/proc/self/mem` writes
- No `ptrace` syscalls
- No `perf_event_open` calls
- Standard `epoll`, `futex`, `mmap` are fully supported

**Verification**:
```bash
# CI/production Linux host with gVisor installed
docker run --runtime=runsc endogenai/working-memory:test python -c "import chromadb; print('gvisor-ok')"
# On macOS: skip gVisor test; document in deploy/k8s/README.md
```

---

### 5.6 — 9.1.6: Self-Signed mTLS CA + Kubernetes Secret Mounts

**Biological analogue**: _MHC-I surface protein identity assay — each module presents its identity for mutual authentication._

**What**: Create `scripts/gen_certs.sh` that generates a self-signed root CA and per-module TLS certificates. Mount certificates as Kubernetes Secrets into each module pod.

**File**: `scripts/gen_certs.sh`
```bash
#!/usr/bin/env bash
# gen_certs.sh — Generate self-signed mTLS CA and per-module certificates.
# Usage: bash scripts/gen_certs.sh [--modules "module1 module2"]
# Output: security/certs/{ca,<module>}.{crt,key}
#
# NOTE: SPIFFE/SPIRE is the recommended Phase 10 upgrade for automatic rotation.
set -eu

CERTS_DIR="security/certs"
mkdir -p "$CERTS_DIR"

# Generate root CA
openssl req -x509 -newkey rsa:4096 -keyout "$CERTS_DIR/ca.key" \
  -out "$CERTS_DIR/ca.crt" -days 365 -nodes \
  -subj "/CN=endogenai-ca/O=EndogenAI"

# Generate per-module certificates
MODULES="${1:-sensory-input perception attention-filtering working-memory \
  short-term-memory long-term-memory episodic-memory reasoning affective \
  executive-agent agent-runtime motor-output learning-adaptation metacognition \
  mcp-server gateway}"

for MODULE in $MODULES; do
  openssl req -newkey rsa:2048 -keyout "$CERTS_DIR/$MODULE.key" \
    -out "$CERTS_DIR/$MODULE.csr" -nodes \
    -subj "/CN=$MODULE/O=EndogenAI"
  openssl x509 -req -in "$CERTS_DIR/$MODULE.csr" \
    -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" \
    -CAcreateserial -out "$CERTS_DIR/$MODULE.crt" -days 365
  echo "Generated: $CERTS_DIR/$MODULE.{crt,key}"
done
```

**Kubernetes Secret mount** (example for `working-memory` Deployment):
```yaml
volumes:
  - name: mtls-certs
    secret:
      secretName: working-memory-mtls-certs
containers:
  - name: working-memory
    volumeMounts:
      - name: mtls-certs
        mountPath: /etc/certs
        readOnly: true
    env:
      - name: TLS_CERT_PATH
        value: /etc/certs/working-memory.crt
      - name: TLS_KEY_PATH
        value: /etc/certs/working-memory.key
      - name: TLS_CA_PATH
        value: /etc/certs/ca.crt
```

**Note**: `security/certs/` must be added to `.gitignore`. Never commit private keys.

---

### 5.7 — 9.1.7: Trivy Scanning Integration

**Biological analogue**: _PRR pattern recognition — detecting PAMP/DAMP patterns (known CVEs, embedded secrets) before they enter the system._

**What**: Add Trivy scan steps to the Docker build pipeline. Fail on HIGH or CRITICAL vulnerabilities. Scan Kubernetes manifests for misconfigurations.

```bash
# Per-image scan
trivy image --exit-code 1 --severity HIGH,CRITICAL endogenai/working-memory:test

# K8s manifest misconfiguration scan
trivy config deploy/k8s/

# Full scan script (add to scripts/build_images.sh post-build step)
for IMAGE in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep endogenai/); do
  echo "Scanning $IMAGE ..."
  trivy image --exit-code 1 --severity HIGH,CRITICAL "$IMAGE"
done
```

**`.trivyignore`**: create at repo root; document any accepted false positives with rationale and CVE ID.

---

### 5.8 — 9.1.8: `securityContext` Hardening

**Biological analogue**: _Complement-tagged inactive synapse elimination — disabled capabilities cannot be re-enabled unless explicitly granted._

**What**: Apply the following `securityContext` to all Kubernetes pod specs. This applies to all 16 service Deployments.

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 65534          # nobody
  runAsGroup: 65534
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  seccompProfile:
    type: RuntimeDefault    # blocks ~50 high-risk syscalls
  capabilities:
    drop: [ALL]
```

**Dockerfile requirement** (for `readOnlyRootFilesystem` compatibility):
- Use `TMPDIR=/tmp` for any writes needed at runtime
- Mount a `tmpfs` emptyDir for writable scratch space if needed:
  ```yaml
  volumes:
    - name: tmp
      emptyDir:
        medium: Memory
        sizeLimit: 64Mi
  containers:
    - volumeMounts:
        - name: tmp
          mountPath: /tmp
  ```

---

### 5.9 — 9.1.9: Inter-Module Security Review

**Biological analogue**: _Metacognitive monitoring — the ACC conflict-detection system flagging inconsistencies between intended and actual system boundaries._

**What**: Perform a systematic review of all inter-module communication paths and document findings in `security/review/phase-9-security-review.md`.

**Review checklist**:

| Check | Tool / Method | Pass criterion |
|---|---|---|
| All inter-module calls authenticated | Grep for raw HTTP calls without auth headers | Zero unauthenticated inter-module calls |
| Module ports not exposed outside cluster | Review all `ports:` in docker-compose.yml and Service manifests | Only gateway (3001) and MCP server (8000) exposed externally |
| All images scanned | `trivy image endogenai/*` | Zero HIGH/CRITICAL (or documented waivers in `.trivyignore`) |
| Non-root user in all containers | `docker inspect --format '{{.Config.User}}'` | All containers report non-root user |
| ReadOnlyRootFilesystem set | Review deployment specs | All pod specs include `readOnlyRootFilesystem: true` |
| NetworkPolicy default-deny | `kubectl get networkpolicy -A` | Default-deny NetworkPolicy in all namespaces |
| OPA policies present for all modules | `opa test security/policies/` | All tests pass; 14 module entries in `modules.json` |
| mTLS certs generated and mounted | File check + env var check | All 16 services have cert paths configured |

**Document findings** in `security/review/phase-9-security-review.md` with:
- Summary of findings (counts per severity)
- Remediation notes for any failing checklist items
- Accepted risks (with documented rationale)
- SPIFFE/SPIRE upgrade path for Phase 10

---

### 5.10 — 9.1.10: `docs/guides/security.md` Authoring

See §7.1 — this item is shared between §9.1 and §9.3 and is captured under documentation completion.

**Gate 2 verification commands**:
```bash
# OPA policy tests
opa test security/policies/ -v
# → All tests pass (zero failures)

# Trivy: all images clean
bash scripts/build_images.sh && bash -c 'for i in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep endogenai/); do trivy image --exit-code 1 --severity HIGH,CRITICAL $i; done'

# Kubernetes dry-run
kubectl apply --dry-run=client -f deploy/k8s/ --recursive
# → exit 0

# security/review document authored
ls security/review/phase-9-security-review.md
```

---

## 6. §9.2 — Deployment (Gate 3)

_Biological analogue: neurogenesis + myelination + cerebral autoregulation — packaging each cortical column (module) for production; deploying along the radial glia scaffold (Kubernetes Nodes); autoscaling to metabolic demand (HPA)._

---

### 6.1 — 9.2.1: Base Dockerfiles

**What**: Create shared base images that pre-install common system packages, reducing per-module build times.

**File**: `deploy/docker/base-python.Dockerfile`
```dockerfile
# Base Python image for all EndogenAI Group I–IV modules.
# Pre-installs: uv, system dependencies (libssl, libffi, libgomp for numpy/torch).
# Usage: FROM endogenai/base-python:3.12-slim
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libssl-dev libffi-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.4.0

# Non-root user
RUN useradd --uid 65534 --no-create-home --shell /usr/sbin/nologin nobody || true
```

**File**: `deploy/docker/base-node.Dockerfile`
```dockerfile
# Base Node image for TypeScript services (gateway, infrastructure/mcp).
# Pre-installs: pnpm, tini (init process).
FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate
```

---

### 6.2 — 9.2.2: Per-Module Dockerfiles

**What**: Author a multi-stage Dockerfile for each of the 16 services. Python modules use `base-python`; TypeScript services use `base-node`.

**Python module Dockerfile template** (example: `working-memory`):
```dockerfile
# modules/group-ii-cognitive-processing/memory/working-memory/Dockerfile
FROM endogenai/base-python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM endogenai/base-python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8010
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -sf http://localhost:8010/health || exit 1
USER nobody
CMD ["python", "-m", "src.working_memory"]
```

**All 16 service Dockerfiles** — location, base image, and exposed port:

| Service | Dockerfile location | Base image | Port |
|---|---|---|---|
| sensory-input | `modules/group-i-signal-processing/sensory-input/Dockerfile` | base-python | 8001 |
| perception | `modules/group-i-signal-processing/perception/Dockerfile` | base-python | 8002 |
| attention-filtering | `modules/group-i-signal-processing/attention-filtering/Dockerfile` | base-python | 8003 |
| working-memory | `modules/group-ii-cognitive-processing/memory/working-memory/Dockerfile` | base-python | 8010 |
| short-term-memory | `modules/group-ii-cognitive-processing/memory/short-term-memory/Dockerfile` | base-python | 8011 |
| long-term-memory | `modules/group-ii-cognitive-processing/memory/long-term-memory/Dockerfile` | base-python | 8012 |
| episodic-memory | `modules/group-ii-cognitive-processing/memory/episodic-memory/Dockerfile` | base-python | 8013 |
| reasoning | `modules/group-ii-cognitive-processing/reasoning/Dockerfile` | base-python | 8014 |
| affective | `modules/group-ii-cognitive-processing/affective/Dockerfile` | base-python | 8015 |
| executive-agent | `modules/group-iii-executive-output/executive-agent/Dockerfile` | base-python | 8020 |
| agent-runtime | `modules/group-iii-executive-output/agent-runtime/Dockerfile` | base-python | 8021 |
| motor-output | `modules/group-iii-executive-output/motor-output/Dockerfile` | base-python | 8022 |
| learning-adaptation | `modules/group-iv-adaptive-systems/learning-adaptation/Dockerfile` | base-python | 8030 |
| metacognition | `modules/group-iv-adaptive-systems/metacognition/Dockerfile` | base-python | 8031 |
| mcp-server | `infrastructure/mcp/Dockerfile` | base-node | 8000 |
| gateway | `apps/default/server/Dockerfile` | base-node | 3001 |

**`.dockerignore` template** (add to each module root):
```
.venv/
node_modules/
__pycache__/
*.pyc
*.pyo
.git/
.pytest_cache/
.ruff_cache/
dist/
*.egg-info/
tests/
```

---

### 6.3 — 9.2.3: `scripts/build_images.sh`

**File**: `scripts/build_images.sh`
```bash
#!/usr/bin/env bash
# Build all EndogenAI module Docker images in dependency order.
# Usage: bash scripts/build_images.sh [--push] [--skip-base]
# Requires: docker buildx (multi-platform support)
set -eu

PUSH=${1:-""}
TAG="${IMAGE_TAG:-latest}"

# Build base images first
if [[ "$*" != *"--skip-base"* ]]; then
  docker build -t endogenai/base-python:3.12-slim -f deploy/docker/base-python.Dockerfile .
  docker build -t endogenai/base-node:22-slim -f deploy/docker/base-node.Dockerfile .
fi

# Build per-module images
MODULES=(
  "modules/group-i-signal-processing/sensory-input:sensory-input:8001"
  "modules/group-i-signal-processing/perception:perception:8002"
  # ... (all 14 modules)
)

for ENTRY in "${MODULES[@]}"; do
  CONTEXT=$(echo "$ENTRY" | cut -d: -f1)
  NAME=$(echo "$ENTRY" | cut -d: -f2)
  docker build -t "endogenai/$NAME:$TAG" "$CONTEXT"
  echo "Built: endogenai/$NAME:$TAG"
  [[ "$PUSH" == "--push" ]] && docker push "endogenai/$NAME:$TAG"
done

echo "Build complete: $(date)"
```

---

### 6.4 — 9.2.4–9.2.6: `deploy/k8s/` Directory Structure and Manifests

**Directory structure**:
```
deploy/
  docker/
    base-python.Dockerfile
    base-node.Dockerfile
    README.md
  k8s/
    namespace.yaml                       # endogenai-modules + endogenai-infra
    runtime-class-gvisor.yaml            # RuntimeClass: gvisor
    network-policy-default-deny.yaml     # Default deny all in both namespaces
    infrastructure/
      mcp-deployment.yaml
      mcp-service.yaml
    group-i-signal-processing/
      sensory-input-deployment.yaml
      sensory-input-service.yaml
      sensory-input-hpa.yaml
      perception-deployment.yaml
      perception-service.yaml
      perception-hpa.yaml
      attention-filtering-deployment.yaml
      attention-filtering-service.yaml
      attention-filtering-hpa.yaml
    group-ii-cognitive-processing/
      working-memory-{deployment,service,hpa}.yaml
      short-term-memory-{deployment,service,hpa}.yaml
      long-term-memory-{deployment,service,hpa}.yaml
      episodic-memory-{deployment,service,hpa}.yaml
      reasoning-{deployment,service,hpa}.yaml
      affective-{deployment,service,hpa}.yaml
    group-iii-executive-output/
      executive-agent-{deployment,service,hpa}.yaml
      agent-runtime-{deployment,service,hpa}.yaml
      motor-output-{deployment,service,hpa}.yaml
    group-iv-adaptive-systems/
      learning-adaptation-{deployment,service,hpa}.yaml
      metacognition-{deployment,service,hpa}.yaml
    apps/
      gateway-deployment.yaml
      gateway-service.yaml
      gateway-ingress.yaml
    observability/
      chromadb-deployment.yaml
      ollama-deployment.yaml
    README.md
```

**Namespace manifest** (`deploy/k8s/namespace.yaml`):
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: endogenai-modules
  labels:
    app.kubernetes.io/part-of: endogenai
---
apiVersion: v1
kind: Namespace
metadata:
  name: endogenai-infra
  labels:
    app.kubernetes.io/part-of: endogenai
```

**Default-deny NetworkPolicy** (`deploy/k8s/network-policy-default-deny.yaml`):
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: endogenai-modules
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: endogenai-infra
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

**Per-module NetworkPolicy** (example: allow ingress from `mcp-server` only):
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-mcp-ingress
  namespace: endogenai-modules
spec:
  podSelector:
    matchLabels:
      app: working-memory
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              app.kubernetes.io/part-of: endogenai
          podSelector:
            matchLabels:
              app: mcp-server
      ports:
        - port: 8010
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              app.kubernetes.io/part-of: endogenai
          podSelector:
            matchLabels:
              app: a2a-broker
```

**Per-module HPA parameters** (all 14 modules + gateway + mcp-server):

| Service | Port | CPU threshold | Min replicas | Max replicas |
|---|---|---|---|---|
| sensory-input | 8001 | 70% | 1 | 4 |
| perception | 8002 | 70% | 1 | 4 |
| attention-filtering | 8003 | 70% | 1 | 4 |
| working-memory | 8010 | 70% | 2 | 8 |
| short-term-memory | 8011 | 70% | 1 | 4 |
| long-term-memory | 8012 | 60% | 1 | 6 |
| episodic-memory | 8013 | 60% | 1 | 6 |
| reasoning | 8014 | 60% | 1 | 6 |
| affective | 8015 | 70% | 1 | 4 |
| executive-agent | 8020 | 70% | 2 | 8 |
| agent-runtime | 8021 | 70% | 2 | 8 |
| motor-output | 8022 | 70% | 1 | 4 |
| learning-adaptation | 8030 | 60% | 1 | 4 |
| metacognition | 8031 | 60% | 1 | 4 |
| mcp-server | 8000 | 60% | 2 | 10 |
| gateway | 3001 | 70% | 2 | 8 |

_Working memory, executive-agent, agent-runtime, and gateway have `minReplicas: 2` for HA — these are high-traffic services._

---

### 6.5 — 9.2.7: gVisor RuntimeClass + `runtimeClassName` in All Deployments

All 14 Python module Deployment pod specs include:
```yaml
spec:
  runtimeClassName: gvisor
```

TypeScript services (`mcp-server`, `gateway`) must be tested for gVisor compatibility before this annotation is applied. Document any incompatibility in `deploy/k8s/README.md`.

---

### 6.6 — 9.2.8: `docker-compose.yml` Audit + `security` Profile Addition

**What**: Audit that all 16 services and backing services are present with correct health checks. Add the `security` profile for the OPA server.

**Audit checklist**:
- [ ] All 14 Group I–IV module services defined (under `modules` profile)
- [ ] `infrastructure/mcp` and `infrastructure/a2a` defined (under `infra` profile or default)
- [ ] ChromaDB, Ollama, OTel Collector, Prometheus, Grafana, Tempo defined (under `observability-full` profile)
- [ ] `apps/default/server` (gateway) defined
- [ ] OPA server added under `security` profile (see §5.1)
- [ ] All `healthcheck:` entries use `curl -sf http://localhost:<port>/health`
- [ ] All services export env vars as documented in `.env.example`

**Validation**:
```bash
docker compose config      # no syntax errors
docker compose config --profiles modules,security,infra,observability-full --quiet
```

---

### 6.7 — 9.2.9: `docker-compose.override.yml` for Local Dev

**File**: `docker-compose.override.yml`
```yaml
# Local development overrides. NOT for production use.
# Provides:
#   - Hot-reload volume mounts for all services
#   - gVisor disabled (no KVM on macOS Docker Desktop)
#   - Debug ports exposed
#
# Usage: docker compose up (automatically loads this file)
# Production: docker compose -f docker-compose.yml up (skips this file)

services:
  working-memory:
    volumes:
      - ./modules/group-ii-cognitive-processing/memory/working-memory/src:/app/src:ro
    environment:
      - DEBUG=1
    # No runtime: runsc — use standard runc for local dev on macOS

  gateway:
    volumes:
      - ./apps/default/server/src:/app/src:ro
    command: ["tsx", "watch", "src/index.ts"]
    ports:
      - "9229:9229"   # Node.js inspector port for debugging
```

---

### 6.8 — 9.2.10: `deploy/k8s/README.md`

**Content outline**:
1. Prerequisites: cluster with NetworkPolicy-compatible CNI (Calico/Cilium), gVisor runtime installed on nodes, `kubectl` configured
2. Quick deploy: `kubectl apply -f deploy/k8s/namespace.yaml && kubectl apply -R -f deploy/k8s/`
3. Verify: `kubectl get pods -n endogenai-modules` — all pods Running
4. Local test with `kind`: include `kind` cluster config that enables NetworkPolicy + gVisor
5. Environment variables: point to `.env.example`; how to create Kubernetes Secrets
6. Scaling: how to adjust HPA parameters; how to check HPA status
7. Troubleshooting: common gVisor incompatabilities; NetworkPolicy debugging with `kubectl exec`

**Gate 3 verification commands**:
```bash
# Kubernetes dry-run — all manifests valid
kubectl apply --dry-run=client -R -f deploy/k8s/
# → exit 0

# Full docker-compose stack
docker compose --profile modules --profile infra --profile observability-full up -d
docker compose ps | grep -v "Exit"

# Verify all services healthy
docker compose --profile modules ps --format json | \
  python3 -c "import json,sys; [print(s['Name'], s['Health']) for s in json.load(sys.stdin)]"
```

---

## 7. §9.3 — Documentation Completion (Gate 4)

_Biological analogue: Default Mode Network pass — constructing the integrated self-model; semantic memory cross-linking; Hebbian LTP (write docs alongside implementation)._

---

### 7.1 — 9.3.1: `docs/guides/security.md`

**Status**: Not yet authored — primary remaining major documentation gap.

**Content outline** (must cover all of the following):

1. **EndogenAI security model** — the multi-layer immune analogy (BBB/gVisor, microglia/OPA, glial scar/NetworkPolicy, MHC-I/mTLS); why defence in depth matters
2. **OPA policies**
   - How to read Rego rules
   - How to run OPA tests: `opa test security/policies/ -v`
   - How to add a new capability to an existing module's policy: edit `agent-card.json` → re-run `gen_opa_data.py` → no Rego edit needed
   - How to write a new Rego rule for a new policy requirement
   - Audit mode vs. enforce mode: `docker compose --profile security up opa` vs. setting `OPA_ENFORCE=true`
3. **gVisor sandboxing**
   - What gVisor is and why it applies to EndogenAI
   - Platform scope: production and CI only, not local macOS dev
   - How to verify a container is gVisor-compatible: `docker run --runtime=runsc <image> <cmd>`
   - Known incompatibilities and the `.trivyignore` convention
4. **Kubernetes NetworkPolicy**
   - The default-deny model
   - How to open a new inter-module communication path (requires Workplan approval + NetworkPolicy update)
   - How to debug NetworkPolicy with `kubectl exec` + `curl`
5. **mTLS certificates**
   - How to generate certs: `bash scripts/gen_certs.sh`
   - How to mount into pods (Kubernetes Secret + volume mount)
   - Rotation schedule: 365-day certs; set a calendar reminder; SPIFFE/SPIRE for automatic rotation (Phase 10 upgrade path)
6. **Image scanning**
   - How to run Trivy locally: `trivy image endogenai/<module>:latest`
   - How to scan Kubernetes manifests: `trivy config deploy/k8s/`
   - How to add a `.trivyignore` waiver with documentation
7. **Secrets management**
   - No secrets in Docker images — use `.env` locally, Kubernetes Secrets in cluster
   - `.env.example` as the canonical record of all required env vars
8. **Security review process** — how to perform a review for a new module; reference `security/review/phase-9-security-review.md` as a template

---

### 7.2 — 9.3.2: `security/README.md`

**Content outline**:
1. Purpose of the `security/` directory
2. `policies/` — Rego rules and how they are evaluated
3. `data/` — generated from `agent-card.json`; how to regenerate
4. `tests/` — how to run: `opa test security/policies/ -v`
5. `review/` — security review documents
6. Enforcement levels: audit → enforce migration path
7. OPA server configuration and the Docker Compose `security` profile

---

### 7.3 — 9.3.3: `observability/README.md` Update

**What**: Update `observability/README.md` to reflect Phase 8 additions. **Deferred from M8.**

**Additions to existing README**:
- Add Tempo to the services table (distributed traces, added Phase 8.4)
- Document gateway OTel instrumentation (added Phase 8.4): `OTEL_SERVICE_NAME=gateway`, trace exporter endpoint
- Add "How to add a new service to the OTel pipeline" section (update `otel-collector.yaml` receivers + exporters)
- Add dashboard locations: Grafana port 3000, Prometheus port 9090, Tempo in Grafana data source
- Add trace query example: "Find traces for a specific `tools/call` invocation"

---

### 7.4 — 9.3.4: `markdown-link-check` Setup + Broken-Link Audit

**What**: Install `markdown-link-check`, author configuration, run audit on all `docs/*.md`, fix all broken internal links.

**Setup**:
```bash
pnpm add -D markdown-link-check   # or npx markdown-link-check
```

**Config file** (`.markdown-link-check.json`):
```json
{
  "ignorePatterns": [
    { "pattern": "^https://" },
    { "pattern": "^http://localhost" }
  ],
  "retryOn429": true,
  "retryCount": 3,
  "aliveStatusCodes": [200, 206]
}
```

**Run audit**:
```bash
find docs/ -name "*.md" | xargs npx markdown-link-check \
  --config .markdown-link-check.json
# Fix all errors before Gate 4
```

**Integration**: add as `pnpm run linkcheck` script in root `package.json`; add to CI pipeline.

---

### 7.5 — 9.3.5: Cross-Linking Audit

Verify that every major doc links to its upstream and downstream context:

| Document | Must link to |
|---|---|
| `README.md` | `docs/guides/getting-started.md`, `docs/architecture.md`, `docs/guides/security.md` |
| `docs/architecture.md` | All module READMEs, `docs/guides/adding-a-module.md`, `docs/protocols/mcp.md`, `docs/protocols/a2a.md` |
| `docs/guides/security.md` | `security/README.md`, `deploy/k8s/README.md`, `docs/architecture.md` |
| `docs/guides/deployment.md` | `deploy/k8s/README.md`, `docker-compose.yml`, `docs/guides/getting-started.md` |
| `docs/guides/observability.md` | `observability/README.md`, Grafana/Prometheus configuration files |
| Module READMEs | `shared/schemas/` (consumed schemas), `docs/architecture.md`, `docs/guides/adding-a-module.md` |
| `security/README.md` | `docs/guides/security.md`, `security/policies/*.rego` files |
| `deploy/k8s/README.md` | `docs/guides/deployment.md`, `deploy/docker/README.md` |

---

### 7.6 — 9.3.6: Module README Audit

**What**: Verify each of the 14 modules has a `README.md` covering the four mandatory sections per AGENTS.md: **Purpose, Interface, Configuration, Deployment**.

```bash
for CARD in $(find modules/ -name "agent-card.json"); do
  MODULE_DIR=$(dirname "$CARD")
  if [[ ! -f "$MODULE_DIR/README.md" ]]; then
    echo "MISSING README: $MODULE_DIR"
  fi
done
```

For each missing or incomplete README, author it following the template in `docs/guides/adding-a-module.md`.

---

### 7.7 — 9.3.7: AsyncAPI Spec for `resources/subscribe` (Optional)

**File**: `docs/research/sources/phase-9/asyncapi-resource-notifications.yaml`

```yaml
asyncapi: 3.0.0
info:
  title: EndogenAI Resource Notifications
  version: 1.0.0
  description: >
    Server-sent event channel for MCP resources/subscribe notifications.
    Clients subscribe via JSON-RPC resources/subscribe method; server emits
    notifications/resources/updated when any brain:// URI changes.
channels:
  resourceUpdated:
    address: notifications/resources/updated
    messages:
      ResourceUpdatedNotification:
        payload:
          type: object
          required: [method, params]
          properties:
            method:
              const: notifications/resources/updated
            params:
              type: object
              required: [uri]
              properties:
                uri:
                  type: string
                  pattern: '^brain://'
                  description: The brain:// URI of the changed resource
```

---

### 7.8 — 9.3.8: MkDocs Site Config (Optional)

**File**: `mkdocs.yml` (repo root)
```yaml
site_name: EndogenAI Documentation
site_url: https://endogenai.github.io/
repo_url: https://github.com/EndogenAI/EndogenAI
docs_dir: docs
theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
nav:
  - Home: ../README.md
  - Architecture: architecture.md
  - Guides:
      - Getting Started: guides/getting-started.md
      - Adding a Module: guides/adding-a-module.md
      - Security: guides/security.md
      - Deployment: guides/deployment.md
      - Observability: guides/observability.md
      - Toolchain: guides/toolchain.md
  - Protocols:
      - MCP: protocols/mcp.md
      - A2A: protocols/a2a.md
```

**Verification**: `mkdocs build --strict` exits 0 (no broken internal links).

**Gate 4 verification commands**:
```bash
# Broken link check
pnpm run linkcheck
# → zero broken internal links

# Docs completeness
ls docs/guides/security.md
ls security/README.md
ls deploy/k8s/README.md

# Module README audit
for CARD in $(find modules/ -name "agent-card.json"); do
  MODULE_DIR=$(dirname "$CARD")
  [[ -f "$MODULE_DIR/README.md" ]] && echo "OK: $MODULE_DIR" || echo "MISSING: $MODULE_DIR"
done
```

---

## 8. Environment Variables Catalogue

All new environment variables required by Phase 9 (in addition to Phase 8 variables documented in `apps/default/server/.env.example`):

| Variable | Service(s) | Description | Example |
|---|---|---|---|
| `MODULE_URLS` | gateway | Comma-separated base URLs for all 16 services (used by `/api/agents`) | `http://localhost:8001,http://localhost:8002,...` |
| `OPA_SERVER_URL` | all 16 services | URL of the shared OPA server | `http://localhost:8181` (dev) / `http://opa:8181` (k8s) |
| `OPA_ENFORCE` | all 16 services | `true` = enforce mode; `false` = audit/log-only | `false` (dev default) |
| `TLS_CERT_PATH` | all 16 services | Path to the module's mTLS certificate | `/etc/certs/<module>.crt` |
| `TLS_KEY_PATH` | all 16 services | Path to the module's mTLS private key | `/etc/certs/<module>.key` |
| `TLS_CA_PATH` | all 16 services | Path to the shared CA certificate | `/etc/certs/ca.crt` |
| `MTLS_ENABLED` | all 16 services | `true` = require mTLS on outbound calls | `false` (dev default) |
| `GVISOR_ENABLED` | `docker-compose.yml` | Build flag to enable `runtime: runsc` in compose | `false` (local macOS dev) |
| `IMAGE_TAG` | `scripts/build_images.sh` | Docker image tag for built images | `latest` / `v1.0.0` |

**`.env.example` update**: add all variables above with placeholder values and inline comments.

---

## 9. New Files and Directories Created by Phase 9

| Path | Purpose | Owner sub-phase |
|---|---|---|
| `security/` | Root security directory | §9.1.1 |
| `security/policies/module-capabilities.rego` | OPA capability isolation rules | §9.1.3 |
| `security/policies/inter-module-comms.rego` | OPA A2A task delegation rules | §9.1.4 |
| `security/policies/helpers.rego` | Shared Rego utility rules | §9.1.3 |
| `security/data/modules.json` | Generated OPA data from agent-card.json files | §9.1.2 |
| `security/tests/module-capabilities_test.rego` | OPA policy tests | §9.1.3 |
| `security/tests/inter-module-comms_test.rego` | OPA policy tests | §9.1.4 |
| `security/review/phase-9-security-review.md` | Inter-module security review document | §9.1.9 |
| `security/README.md` | Security directory guide | §9.3.2 |
| `security/certs/` | Generated mTLS certificates (gitignored) | §9.1.6 |
| `scripts/gen_opa_data.py` | Generate OPA data from agent-card.json files | §9.1.2 |
| `scripts/gen_certs.sh` | Generate self-signed mTLS CA and module certs | §9.1.6 |
| `scripts/build_images.sh` | Build all 16 Docker images | §9.2.3 |
| `deploy/` | Root deployment directory | §9.2.4 |
| `deploy/docker/base-python.Dockerfile` | Shared Python base image | §9.2.1 |
| `deploy/docker/base-node.Dockerfile` | Shared Node.js base image | §9.2.1 |
| `deploy/docker/README.md` | Base image usage and multi-stage pattern guide | §9.2.1 |
| `deploy/k8s/namespace.yaml` | Kubernetes namespace definitions | §9.2.5 |
| `deploy/k8s/network-policy-default-deny.yaml` | Default-deny NetworkPolicy | §9.2.5 |
| `deploy/k8s/runtime-class-gvisor.yaml` | Kubernetes gVisor RuntimeClass | §9.1.5 |
| `deploy/k8s/group-i-signal-processing/` | Group I Deployment + Service + HPA manifests | §9.2.6 |
| `deploy/k8s/group-ii-cognitive-processing/` | Group II Deployment + Service + HPA manifests | §9.2.6 |
| `deploy/k8s/group-iii-executive-output/` | Group III Deployment + Service + HPA manifests | §9.2.6 |
| `deploy/k8s/group-iv-adaptive-systems/` | Group IV Deployment + Service + HPA manifests | §9.2.6 |
| `deploy/k8s/infrastructure/` | MCP server Deployment + Service manifests | §9.2.6 |
| `deploy/k8s/apps/` | Gateway Deployment + Service + Ingress manifests | §9.2.6 |
| `deploy/k8s/observability/` | ChromaDB + Ollama Deployment manifests | §9.2.6 |
| `deploy/k8s/README.md` | Kubernetes deployment guide | §9.2.10 |
| `docker-compose.override.yml` | Local dev overrides (hot-reload, no gVisor) | §9.2.9 |
| `.env.example` update | New Phase 9 env vars documented | §8 |
| `.markdown-link-check.json` | Broken-link checker configuration | §9.3.4 |
| `mkdocs.yml` | MkDocs configuration (optional) | §9.3.8 |
| `apps/default/server/src/routes/agents.ts` | `/api/agents` route | §9.0.1 |
| `apps/default/server/tests/agents.test.ts` | Agents route tests | §9.0.1 |
| `apps/default/client/lighthouserc.json` | Lighthouse CI config | §9.0.3 |
| `docs/guides/security.md` | Comprehensive security guide | §9.1.10 / §9.3.1 |
| Per-module `Dockerfile` (×14) | Production Dockerfiles for all modules | §9.2.2 |
| Per-module `.dockerignore` (×14) | Docker build ignores | §9.2.2 |
| `docs/research/sources/phase-9/asyncapi-resource-notifications.yaml` | AsyncAPI spec (optional) | §9.3.7 |

---

## 10. Test Requirements

| Gate | Sub-phase item | Required tests | Pass criterion |
|---|---|---|---|
| Gate 0 | M8 verified | Existing 153-test suite | All 153 pass |
| Gate 1 | 9.0.1 `/api/agents` | `agents.test.ts` (5 cases) | All pass; TypeScript clean |
| Gate 1 | 9.0.2 `resources/subscribe` | Working memory subscription tests (5 cases) | All pass; E2E < 500 ms |
| Gate 1 | 9.0.3 Lighthouse | `pnpm run lighthouse` | All 4 categories ≥ 0.9 |
| Gate 1 | 9.0.4 `traceparent` required | Full suite re-run post schema change | All 153+ pass with traceparent required |
| Gate 2 | 9.1.3 OPA capability policies | `opa test security/policies/ -v` | All policy tests pass |
| Gate 2 | 9.1.4 OPA comms policies | `opa test security/policies/ -v` | All policy tests pass |
| Gate 2 | 9.1.7 Trivy scanning | `trivy image endogenai/*` | Zero HIGH/CRITICAL (or waived) |
| Gate 3 | 9.2.2 Dockerfiles | Build + run test suite in container | `docker run endogenai/<module>:test pytest` passes |
| Gate 3 | 9.2.5–9.2.6 K8s manifests | `kubectl apply --dry-run=client` | Exit 0 |
| Gate 3 | 9.2.8 Docker Compose | `docker compose config` | No syntax errors |
| Gate 4 | 9.3.4 Link check | `pnpm run linkcheck` | Zero broken internal links |
| M9 | All | Full suite + lighthouse + opa test + linkcheck | All pass |

**Coverage requirement**: per AGENTS.md, all new functionality must be at 80%+ coverage.

```bash
# TypeScript coverage (agents.test.ts)
cd apps/default/server && pnpm run test -- --coverage
# Python coverage (working-memory subscriptions)
cd modules/group-ii-cognitive-processing/memory/working-memory && \
  uv run pytest --cov=src --cov-fail-under=80
```

---

## 11. M9 Milestone Declaration Gate

All of the following must pass before M9 is declared complete and the milestone is recorded in `docs/Workplan.md`:

```bash
# ─── GATE 1: Deferred Phase 8 items ─────────────────────────────────────────
# /api/agents tests
cd apps/default/server && pnpm run test -- agents
# Working memory subscription tests
cd modules/group-ii-cognitive-processing/memory/working-memory && uv run pytest tests/ -v
# Lighthouse live audit
cd apps/default/client && pnpm run lighthouse
# traceparent schema promotion + full suite
pnpm run test

# ─── GATE 2: Security ────────────────────────────────────────────────────────
# OPA policy tests
opa test security/policies/ -v
# Trivy image scans
for IMG in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep endogenai/); do
  trivy image --exit-code 1 --severity HIGH,CRITICAL "$IMG"
done
# Security review doc authored
ls security/review/phase-9-security-review.md

# ─── GATE 3: Deployment ──────────────────────────────────────────────────────
# Kubernetes dry-run
kubectl apply --dry-run=client -R -f deploy/k8s/
# Full stack docker compose
docker compose --profile modules --profile infra --profile observability-full up -d
sleep 30  # allow health checks to settle
docker compose ps | grep -v "healthy\|running\|Ready" | grep -v "NAME"
# → empty output (all services healthy)

# ─── GATE 4: Documentation ───────────────────────────────────────────────────
# Broken-link check
pnpm run linkcheck
# Core docs authored
ls docs/guides/security.md
ls security/README.md
ls deploy/k8s/README.md
# Module README audit
MISSING=$(for CARD in $(find modules/ -name "agent-card.json"); do
  DIR=$(dirname "$CARD"); [[ ! -f "$DIR/README.md" ]] && echo "$DIR"; done)
[[ -z "$MISSING" ]] && echo "All module READMEs present" || echo "MISSING: $MISSING"

# ─── FINAL: All gates converge ─────────────────────────────────────────────
pnpm run test               # 153+ tests passing
pnpm run typecheck          # TypeScript clean
pnpm run lint               # Lint clean
opa test security/policies/ # All OPA policy tests pass
pnpm run linkcheck          # Zero broken internal links
```

M9 milestone declaration checklist:

- [ ] `kubectl apply --dry-run=client -R -f deploy/k8s/` — exit 0
- [ ] `docker compose up` (full stack: modules + infra + observability-full) — all services healthy within 60 s
- [ ] All 153+ tests passing (including §9.0 additions)
- [ ] `pnpm run lighthouse` — all four categories ≥ 90
- [ ] `opa test security/policies/` — all policy tests passing
- [ ] `pnpm run linkcheck` — zero broken internal links
- [ ] `docs/guides/security.md` authored and cross-linked
- [ ] `deploy/k8s/README.md` authored
- [ ] `security/review/phase-9-security-review.md` authored
- [ ] `shared/schemas/agent-card.schema.json` verified or authored
- [ ] `traceparent` promoted to `required` in `mcp-context.schema.json`
- [ ] All 14+ module `README.md` files present and complete
- [ ] Trivy scans: zero unwaived HIGH/CRITICAL findings across all images
- [ ] `scripts/gen_opa_data.py`, `scripts/gen_certs.sh`, `scripts/build_images.sh` — all authored and functional

---

## 12. Open Questions (Remaining)

Only one question remains unresolved from the D3 §8 open questions section:

### Q1 — `agent-card.schema.json` Status

**Status**: Unresolved — pre-implementation check required before §9.0.1.

**Question**: Does `shared/schemas/agent-card.schema.json` already exist and accurately describe the `AgentCard` structure returned by `/.well-known/agent-card.json` endpoints?

**Check**:
```bash
ls shared/schemas/agent-card.schema.json
cd shared && buf lint
```

**If it exists**: verify the schema covers `name`, `version`, `description`, `url`, `wellKnownPath`, `capabilities`, `consumers`. If any field is missing, update the schema and re-run `buf lint` before proceeding to 9.0.1.

**If it does not exist**: author `shared/schemas/agent-card.schema.json` first (schemas-first constraint from AGENTS.md). Use one of the existing `agent-card.json` files as the ground truth for the schema. Obtain a `buf lint` pass before any `/api/agents` implementation code is written.

**Impact**: blocks §9.0.1 only. All other Phase 9 sub-phases may proceed in parallel while this is resolved.

---

## 13. Decisions Recorded

| ID | Decision | Rationale | Source |
|---|---|---|---|
| D9-1 | OPA: single shared server, audit → enforce rollout | 14 × sidecar = 420 MB overhead; shared server consistent with ChromaDB/OTel patterns; start audit-only to avoid false positives | D2 §9.1; D1 microglial analogy; user decision 2026-03-04 |
| D9-2 | gVisor: CI + production only, not local macOS dev | No macOS port; Docker Desktop VM lacks KVM; write gVisor-compatible images, validate in CI; set `runtime: runsc` under `security` profile only | D2 §9.1; gVisor docs; user decision 2026-03-04 |
| D9-3 | mTLS: self-signed CA for Phase 9; SPIFFE/SPIRE deferred to Phase 10 | Self-signed CA sufficient for v1 inter-module auth; SPIFFE adds SPIRE server + DaemonSet — not needed until multi-cluster | D2 §9.1; SPIFFE/SPIRE docs; user decision 2026-03-04 |
| D9-4 | Raw Kubernetes manifests in `deploy/k8s/`; Helm deferred to Phase 10 | Meets M9 deliverable with lower complexity; Helm adds chart versioning overhead not needed for single-cluster Phase 9 | D2 §9.2; user decision 2026-03-04 |
| D9-5 | Module count: 14 confirmed + 2 = 16 total services | `find modules/ -name "agent-card.json" | wc -l` = 14 on 2026-03-04 | Codebase audit 2026-03-04 |
| D9-6 | Docker Compose `security` profile for OPA | Backwards-compatible; OPA is opt-in at dev time; `docker compose --profile security up` enables security-enhanced dev mode | D3 §8.1; user decision 2026-03-04 |
| D9-7 | HPA threshold: 70% CPU (custom Prometheus metrics deferred to Phase 10) | Simple, no Prometheus Adapter required for Phase 9; working memory, executive-agent, agent-runtime, gateway at `minReplicas: 2` for HA | D2 §9.2; K8s HPA docs |
| D9-8 | OPA capability rules derived from `agent-card.json` via `gen_opa_data.py` | Endogenous-first principle (AGENTS.md); policy grounded in existing system knowledge; divergence caught by schema validation | AGENTS.md; D1 danger hypothesis analogy |
| D9-9 | `/api/agents` uses `MODULE_URLS` env var (comma-separated) | Simpler than reading `uri-registry.json` at runtime; allows per-environment override; consistent with existing gateway env-var pattern | D2 §9.0; D3 §3 |
| D9-10 | `Promise.allSettled` in `/api/agents` (graceful degradation) | Single unresponsive module must not block the response; matches synaptic pruning analogy — silent failures, not crashes | D1 §9.0; D2 §9.0 |
