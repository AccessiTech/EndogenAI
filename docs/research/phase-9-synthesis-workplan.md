# Phase 9 — D3: Synthesis Workplan — Security, Deployment & Documentation

_Generated: 2026-03-04 by Docs Executive Researcher_

> **Scope**: Synthesis of D1 (neuroscience) and D2 (technologies) into concrete implementation guidance for Phase 9.
> This document is a pre-workplan recommendation brief — the Phase Executive must review and approve before any implementation begins.
> Sub-phases: 9.0 Deferred Phase 8 Items · 9.1 Security & Sandboxing · 9.2 Deployment · 9.3 Documentation Completion

---

## 1. Phase Overview

Phase 9 is the **production-hardening and completion** phase for EndogenAI. It consolidates M8 deferred items, secures the system against exploitation, packages it for production deployment, and ensures all documentation is coherent and cross-linked. It is the system's first full **offline consolidation pass** — analogous to sleep-phase hippocampal replay that cements a day's learning into durable long-term memory.

| Sub-phase | Brain Analogue (D1) | Technology (D2) | Primary Deliverable |
|---|---|---|---|
| 9.0 Deferred completions | Hippocampal SWR replay — finishing deferred consolidation | SSE live notifications, `/api/agents`, Lighthouse CI, `traceparent` required | Fully wired Phase 8 stubs |
| 9.1 Security | CNS immune privilege — BBB, microglia, apoptosis, PRRs | OPA/Rego, gVisor, Kubernetes NetworkPolicy, mTLS, Trivy | `security/` directory + `docs/guides/security.md` |
| 9.2 Deployment | Neurogenesis + myelination + CBF autoregulation | Docker multi-stage, Kubernetes Deployments + HPA + Services | `deploy/k8s/` manifests + validated `docker-compose.yml` |
| 9.3 Documentation | DMN + metacognition + Hebbian LTP | Cross-linking audit, `docs/guides/security.md`, broken-link checker | All documentation complete and cross-linked |

**Gate condition**: Phase 9 follows M8 (declared 2026-03-03). All 153 tests passing. The Phase 7 OTel bootstrap is verified — confirming the prerequisite for promoting `traceparent` to `required`.

**Milestone**: **M9 — Production-Ready**: Kubernetes deploy succeeds; all documentation complete.

---

## 2. Biological → Technical Mapping

### Full Cross-Phase Mapping Table

| Phase 9 concern | Biological analogue | Technical implementation |
|---|---|---|
| Completing Phase 8 deferred items | Hippocampal SWR replay — consolidating deferred experience overnight | Port stubs to full implementations: `/api/agents`, `resources/subscribe` live |
| `traceparent` required in all envelopes | White-matter myelination completes signal path integrity | Promote `traceparent` to `required` in `mcp-context.schema.json` |
| Live resource update notifications | Dopaminergic/noradrenergic volume transmission — broadcast state change | `notifications/resources/updated` A2A events from Working Memory → SSE relay |
| Agent card discovery | MHC-I antigen presentation — every cell announces its identity | `GET /api/agents` aggregating `/.well-known/agent-card.json` from each module |
| Lighthouse ≥ 90 | Myelination of sensory pathways before birth — performance gating | Lighthouse CI `pnpm run lighthouse` as a CI gate for browser release |
| Module capability isolation | CNS immune privilege — neurons invisible to adaptive immune system by default | OPA Rego policies derived from each module's `agent-card.json` capabilities |
| Container sandboxing | gVisor `runsc` application kernel | BBB tight junctions preventing paracellular diffusion |
| Continuous policy evaluation | Microglial continuous surveillance + PRR pattern matching | OPA sidecar in audit mode during development, enforce mode in production |
| Controlled pod termination | Apoptosis — clean, anti-inflammatory cellular self-destruction | SIGTERM + graceful drain + SIGKILL; gVisor isolation maintained during shutdown |
| DAMP-style anomaly detection | Danger hypothesis — capability anomaly as damage signal | OPA rules flagging requests that exceed `agent-card.json` declared capabilities |
| Network namespace isolation | Astrocytic glial scar — containing damage spread | Kubernetes NetworkPolicy default-deny; inter-module traffic via MCP/A2A only |
| Workload identity (mTLS) | MHC-I surface protein identity assay | SPIFFE SVID / self-signed mTLS CA for inter-module authentication |
| Docker multi-stage build | Myelination: axon → production-ready myelinated fiber | Dev image (builder stage) → runtime image (minimal, production-optimized) |
| Per-module Dockerfile | Cortical column — self-contained, modular, standard internal wiring | One Dockerfile per module group; parameterized by module name |
| Kubernetes Deployment | Neuronal deployment along radial glia scaffold | `Deployment` manifest + readiness/liveness probes for integration gate |
| Kubernetes HPA | Cerebral autoregulation — CBF proportional to metabolic demand | HPA at 70% CPU utilization; custom metrics as a Phase 10 extension |
| Resource limits + pod eviction | Synaptic pruning — complement-tagged inactive synapse phagocytosis | `resources.limits` + HPA `minReplicas: 1`; liveness failure → pod restart |
| Cross-linked documentation | DMN angular gyrus binding disparate episodic memories | Every `docs/` file references its upstream and downstream context |
| `docs/guides/security.md` | Metacognitive knowledge — declarative self-documentation | Comprehensive security guide authored as part of 9.3 |
| Broken-link audit | Metacognitive monitoring — ACC conflict detection, error signalling | `markdown-link-check` automated broken-link scan |
| Doc-first authoring order | Hebbian LTP — simultaneous co-activation strengthens association | Documentation authored alongside (not after) implementation, per AGENTS.md |

---

## 3. §9.0 — Deferred Items: Delivery Plan

### 9.0.1 — `/api/agents` Endpoint

**Biological intent**: Agent-card discovery is MHC-I antigen presentation — every module announces its identity. The Internals panel currently lacks this feed.

**Implementation steps**:
1. Create `apps/default/server/src/routes/agents.ts` — `GET /api/agents` handler using `Promise.allSettled` over all module URLs
2. Read module URLs from `MODULE_URLS` environment variable (comma-separated base URLs)
3. For each URL, `GET /.well-known/agent-card.json` with 2 s timeout via `AbortSignal.timeout(2000)`
4. Return `{ agents: AgentCard[], timestamp: ISO8601 }` — failed fetches silently omitted
5. Mount `agentsRouter` in the main Hono app
6. Update `apps/default/client/src/tabs/Internals.tsx` agent-card panel to call `GET /api/agents` instead of `GET /api/resources`
7. Tests: mock module server returning `agent-card.json`, verify aggregation; test timeout handling; test partial failure graceful degradation

**Schema dependency**: `shared/schemas/agent-card.schema.json` (verify it exists; if not, author before Step 1 per schemas-first rule).

---

### 9.0.2 — `resources/subscribe` Live Notifications

**Biological intent**: Dopaminergic volume transmission — a single Working Memory write should fan out `notifications/resources/updated` to all registered SSE subscribers.

**Implementation steps**:
1. **Working Memory module** (`modules/group-ii-cognitive-processing/working-memory`): replace stub `resources/subscribe` handler with live subscription registry (Map from `sessionId` → callback)
2. On any resource write/update, iterate subscriber callbacks and emit `notifications/resources/updated` via the A2A event bus (`endogenai-a2a` client)
3. **MCP server** (`infrastructure/mcp`): wire incoming `notifications/resources/updated` A2A events to the active SSE client stream for the session
4. **Gateway** (`apps/default/server`): the existing SSE relay already propagates all MCP push events — no gateway change required
5. **End-to-end test**: write to `brain://working-memory/context/current` → verify `EventSource` in browser Internals tab receives `notifications/resources/updated` within 500 ms

**AsyncAPI spec**: author `docs/research/sources/phase-9/asyncapi-resource-notifications.yaml` documenting the channel (this can be the foundation of extended docs in 9.3).

---

### 9.0.3 — Lighthouse Live Browser Audit

**Implementation steps**:
1. Install `@lhci/cli` as a dev dependency in `apps/default/client`
2. Author `apps/default/client/lighthouserc.json` with ≥ 90 assertions across all four categories
3. Add `"lighthouse": "pnpm run build && lhci autorun"` to `apps/default/client/package.json` scripts
4. Run the live audit against `localhost:5173` (requires `pnpm run dev` running)
5. Remediate any category below 90 (common issues: image format, render-blocking resources, missing `<meta name="description">`, insufficient contrast)
6. Add `pnpm run lighthouse` to the CI pipeline as a post-build step (it runs against the built artifact served by `pnpm preview`)

**Note**: the existing test suite achieved accessibility compliance via Vitest/Testing Library — the Lighthouse live audit is a separate pass that may surface additional issues (Core Web Vitals, SEO meta tags).

---

### 9.0.4 — Promote `traceparent` to Required

**Prerequisite check** (must confirm before implementation):
- Verify all 14+ modules (Groups I–IV) emit `traceparent` in every MCPContext envelope they produce
- Run the full 153-test suite and grep for any test fixture constructing `MCPContext` without `traceparent`
- Fix all test fixtures that omit `traceparent`

**Implementation steps**:
1. Move `traceparent` from the `properties` optional list to the `required` array in `shared/schemas/mcp-context.schema.json`
2. Run `cd shared && buf lint` and `pnpm run typecheck` to verify no downstream type breakage
3. Re-run all 153 tests — any test constructing MCPContext without `traceparent` will now fail schema validation → fix those fixtures
4. Update `shared/types/` TypeScript definitions if `traceparent` is typed as optional there

**Breaking change**: this is a breaking schema change. All consumers of `MCPContext` must always provide `traceparent`. Confirm the M7 OTel audit confirms this is true for all Groups I–IV before landing.

---

## 4. §9.1 — Security: Delivery Plan

### Design Intent (Multi-Layer Immune Privilege)

Security in Phase 9.1 follows the brain's defence-in-depth model: no single layer is sufficient; the combination of gVisor (BBB) + OPA (microglial surveillance) + NetworkPolicy (glial scar) + mTLS (MHC-I identity) provides a layered security posture in which compromise of any one layer does not expose the entire system.

### 9.1.1 — OPA Module Capability Policies

**Implementation steps**:
1. Create `security/` directory at repo root
2. Create `security/policies/module-capabilities.rego` — rules derived from `agent-card.json` capabilities arrays, enforcing:
   - Deny requests for capabilities not listed in the module's agent card
   - Audit-flag requests at the boundary of declared capabilities
   - Allow all capabilities declared in `agent-card.json`
3. Create `security/data/modules.json` — OPA data document mapping module IDs → agent-card capabilities (auto-generated from `agent-card.json` files via a `scripts/gen_opa_data.py` script)
4. Create `scripts/gen_opa_data.py` — reads all `agent-card.json` files in `modules/`, generates `security/data/modules.json`
5. Create `security/policies/inter-module-comms.rego` — rules restricting which modules may initiate A2A tasks against which targets (based on declared `consumers` relationships in agent cards)
6. Author `security/README.md` documenting the policy architecture, Rego evaluation model, and how to add or modify policies
7. Add OPA evaluation test: `opa test security/policies/` (requires OPA CLI)

**Deployment mode decision**: for Phase 9, OPA as a **sidecar per module** (Docker Compose: additional `opa` service per module container) is simpler than a shared OPA server. The gateway and MCP server each call their local OPA sidecar via loopback (`http://localhost:8181`). Document the shared-server upgrade path for Phase 10.

---

### 9.1.2 — gVisor Container Sandboxing

**Implementation steps**:
1. Document gVisor installation in `docs/guides/deployment.md` — `apt install gvisor` / `brew` (macOS dev note: gVisor requires Linux; local dev uses standard Docker runtime, gVisor is production-only)
2. Add `runtime: runsc` to Python module services in `docker-compose.yml` under the `production` profile (not default dev profile — gVisor is unsuitable for local hot-reload dev)
3. Create Kubernetes `RuntimeClass` manifest at `deploy/k8s/runtime-class-gvisor.yaml`
4. Add `runtimeClassName: gvisor` to Group I–IV module `Deployment` pod specs
5. Test gVisor compatibility for each module: run test suite against a gVisor-sandboxed container to surface any syscall incompatibilities
6. Document any known gVisor incompatibilities in `security/README.md` (commonly: some `/proc` paths, perf counters, certain network syscalls)

**Scope caveat**: gVisor production deployment requires Linux hosts with KVM support. CI pipelines on GitHub Actions can use `--platform=ptrace` (2× performance penalty) or a Linux runner. Document this in `docs/guides/deployment.md`.

---

### 9.1.3 — Security Review and mTLS

**Implementation steps**:
1. Perform a security review of all inter-module interfaces — document findings in `security/review/phase-9-security-review.md`
2. Review checklist:
   - All inter-module calls authenticated (Bearer token or mTLS)?
   - All module ports not exposed outside the cluster namespace?
   - All images scanned with Trivy (`trivy image` for each `endogenai/*` image)?
   - Kubernetes `securityContext.runAsNonRoot: true` and `readOnlyRootFilesystem: true` set on all pod specs?
   - Kubernetes NetworkPolicy default-deny applied to all namespaces?
   - OPA policies in place for all Group I–IV modules?
3. For mTLS: create a simple CA (`scripts/gen_certs.sh`) and per-module certificates; mount as Kubernetes Secrets. Document the SPIFFE/SPIRE upgrade path.
4. Author `docs/guides/security.md` — comprehensive security guide covering: OPA policies, gVisor sandboxing, NetworkPolicy, mTLS, image scanning, how-to-add-a-new-policy, and the biological design rationale

---

## 5. §9.2 — Deployment: Delivery Plan

### Design Intent (Neurogenesis to CBF Autoregulation)

Phase 9.2 packages the cognitive system for reproducible, scalable deployment. Each module is a cortical column — self-contained, standardized internal structure. The Dockerfiles myelinate (optimize) each column for production; the Kubernetes Deployment manifests deploy the columns along the radial glia scaffold.

### 9.2.1 — Dockerfiles

**Implementation steps**:
1. Create `deploy/docker/base-python.Dockerfile` — shared base for all Python modules (Python 3.12 slim + `uv` + system deps + non-root user `nobody`)
2. Create `deploy/docker/base-node.Dockerfile` — shared base for TypeScript services (Node 22 slim + pnpm + non-root user `node`)
3. For each Python module in Groups I–IV, create `modules/<group>/<module>/Dockerfile` — multi-stage: builder installs deps via `uv sync --frozen --no-dev`; runtime copies `.venv` + `src/`; sets `CMD`
4. For TypeScript services, create `apps/default/server/Dockerfile` and `infrastructure/mcp/Dockerfile` — multi-stage TypeScript builds
5. Test each Dockerfile: `docker build -t endogenai/<module>:test .` and verify the test suite passes in the built image
6. Add `.dockerignore` to each module directory: exclude `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `.git/`, `tests/`
7. Add Trivy scan step: `trivy image --exit-code 1 --severity HIGH,CRITICAL endogenai/<module>:test`
8. Create `deploy/docker/README.md` — explains base image strategy, multi-stage pattern, and build commands

**Module count**: Groups I–IV contain approximately 14 modules across 8 cognitive sub-modules per group. Create a `Makefile` or `scripts/build_images.sh` to build all images in sequence.

---

### 9.2.2 — Kubernetes Manifests

**Directory structure**:
```
deploy/
  k8s/
    namespace.yaml                  # endogenai-modules + endogenai-infra namespaces
    runtime-class-gvisor.yaml       # RuntimeClass for gVisor
    network-policy-default-deny.yaml  # Default deny for all namespaces
    infrastructure/
      mcp-deployment.yaml           # infrastructure/mcp server
      mcp-service.yaml
      a2a-deployment.yaml           # infrastructure/a2a broker
      a2a-service.yaml
    group-i-signal-processing/
      perception-deployment.yaml
      perception-service.yaml
      perception-hpa.yaml
      attention-deployment.yaml
      attention-service.yaml
      attention-hpa.yaml
    group-ii-cognitive-processing/
      ... (working-memory, short-term, long-term, episodic, reasoning)
    group-iii-executive-output/
      ... (executive-agent, agent-runtime, motor-output)
    group-iv-adaptive-systems/
      ... (reward, metacognition, learning, habit)
    apps/
      gateway-deployment.yaml       # apps/default/server
      gateway-service.yaml
      gateway-ingress.yaml
    observability/
      chromadb-deployment.yaml
      ollama-deployment.yaml
    README.md
```

**Implementation steps**:
1. Create `deploy/k8s/namespace.yaml` with namespaces `endogenai-modules` and `endogenai-infra`
2. Create `deploy/k8s/network-policy-default-deny.yaml` with default-deny-all NetworkPolicy for both namespaces
3. For each module, create three files: `Deployment`, `Service` (ClusterIP), `HorizontalPodAutoscaler`
4. All Deployment pod specs must include:
   - `runtimeClassName: gvisor` (production profile)
   - `securityContext.runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`
   - `resources.requests` and `resources.limits`
   - `readinessProbe` and `livenessProbe` targeting `/health`
5. Services expose only the module's MCP port (no direct inter-module access)
6. NetworkPolicy per module: allow ingress from `infrastructure/mcp` only; allow egress to `infrastructure/a2a` only
7. Create `deploy/k8s/README.md` — `kubectl apply -k` instructions, prerequisite services (ChromaDB, Ollama), and cluster requirements (CNI with NetworkPolicy support, gVisor runtime)

**Validation method**: `kubectl apply --dry-run=client -f deploy/k8s/` confirms all manifests are valid. `kind` local cluster can be used for smoke-testing without a real cluster.

---

### 9.2.3 — Docker Compose Validation

**Implementation steps**:
1. Run `docker compose config` — verify no syntax errors in `docker-compose.yml`
2. Audit services present vs. modules that exist:
   - Group I–IV module services
   - `infrastructure/mcp`, `infrastructure/a2a`
   - ChromaDB, Ollama, OTel Collector, Prometheus, Grafana, Tempo
   - `apps/default/server` (gateway)
3. Add missing services under profiles (`--profile modules`, `--profile infra`)
4. Verify all `healthcheck:` entries use valid `test:` commands
5. Verify environment variable overrides are documented in `.env.example`
6. Author `docker-compose.override.yml` for local dev: hot-reload volume mounts, debug ports enabled, gVisor runtime disabled (ptrace only on Linux, off on macOS)

---

## 6. §9.3 — Documentation Completion: Delivery Plan

### Design Intent (DMN + Semantic Memory Cross-Linking)

Documentation completion is the system's DMN pass — constructing an integrated self-model that allows any developer (or agent) to orient quickly without prior context. Cross-linking creates the semantic memory graph that enables rapid concept traversal.

### 9.3.1 — Author `docs/guides/security.md`

The security guide must cover:
- EndogenAI's security model (multi-layer immune analogy)
- OPA policies: how to read, test, and extend Rego rules
- gVisor: what it is, when it applies, how to verify container compatibility
- Kubernetes NetworkPolicy: the default-deny model and per-module allow rules
- mTLS: certificate generation, rotation schedule, SPIFFE upgrade path
- Image scanning: how to run Trivy locally and what to do with findings
- Secrets management: no secrets in images; use Kubernetes Secrets + `.env.example` for local dev
- Security review process: how to perform a security review for a new module

---

### 9.3.2 — Author `security/README.md`

Covers: purpose of `security/` directory, policy structure, data generation script, evaluation flow, enforcement levels (audit → enforce), and how to run OPA tests.

---

### 9.3.3 — Update `observability/README.md`

Deferred from Phase 8 M8 note. Update to reflect:
- Tempo added for distributed traces
- Gateway OTel instrumentation (added in Phase 8.4)
- Dashboard locations and access
- How to add a new service to the OTel pipeline

---

### 9.3.4 — Cross-Linking Audit

**Steps**:
1. Run `find docs/ -name "*.md" | xargs npx markdown-link-check --config .markdown-link-check.json` to find broken internal links
2. Author `.markdown-link-check.json` with ignore patterns for external URLs that require auth
3. For each doc, verify outbound links per the cross-linking table (D2 §9.3)
4. Add missing cross-links, especially:
   - `docs/architecture.md` → `docs/guides/security.md`
   - `docs/guides/deployment.md` → `deploy/k8s/README.md`
   - Module READMEs → their consumed MCP schemas in `shared/schemas/`
   - `README.md` → `docs/guides/security.md`

---

### 9.3.5 — Module README Audit

Verify each of the 14+ modules has a `README.md` that covers: purpose, interface, configuration, and deployment. File gaps as sub-issues.

---

## 7. Gate Sequence & Dependencies

```
9.0 Deferred items (parallel, independent; complete first as quick wins)
  ├── 9.0.1 /api/agents endpoint
  ├── 9.0.2 resources/subscribe live notifications
  ├── 9.0.3 Lighthouse live audit → requires dev server running
  └── 9.0.4 traceparent required → prerequisite: verify all modules emit traceparent
          ↓ (gate: all 153 tests pass with traceparent required)
9.1 Security
  ├── 9.1.1 OPA policies → generates security/data/modules.json from agent-card.json files
  ├── 9.1.2 gVisor configuration → Linux host required for KVM mode
  └── 9.1.3 Security review + mTLS + docs/guides/security.md
          ↓ (gate: security review complete; OPA tests pass)
9.2 Deployment
  ├── 9.2.1 Dockerfiles → must precede Kubernetes manifests
  ├── 9.2.2 Kubernetes manifests → uses security context from 9.1
  └── 9.2.3 Docker Compose validation
          ↓ (gate: docker compose up completes full stack; kubectl apply --dry-run passes)
9.3 Documentation
  ├── 9.3.1 docs/guides/security.md → authored after 9.1
  ├── 9.3.2 security/README.md → authored alongside 9.1
  ├── 9.3.3 observability/README.md update
  ├── 9.3.4 Cross-linking audit → run after all docs are authored
  └── 9.3.5 Module README audit → can run in parallel with 9.1–9.2
          ↓
M9 milestone: all checks pass; kubernetes deploy succeeds; documentation complete
```

**Critical path**: `Dockerfiles → Kubernetes manifests → kubectl apply dry-run → full stack docker compose up → M9`

The critical path does **not** block on OPA/gVisor — security hardening can proceed in parallel with deployment work.

---

## 8. Open Questions

> **All five architecture questions resolved by user on 2026-03-04.** See §8.1 Decision Log below.

6. **`agent-card.json` schema status** (Low but blocking for 9.0.1): The `/api/agents` route returns `AgentCard[]`. Verify `shared/schemas/agent-card.schema.json` exists and is current before implementing 9.0.1. _(Unresolved — pre-implementation check required)_

### 8.1 Decision Log — 2026-03-04

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | gVisor scope on macOS | **CI + production only** — standard `runc` locally on macOS | gVisor has no macOS port; Docker Desktop VM does not expose KVM; write gVisor-compatible Dockerfiles (no `/proc` writes, no raw sockets) but do not require gVisor locally |
| 2 | OPA deployment mode | **Single shared OPA server** — start in audit (log-only) mode, promote to enforce after validation | 14 modules × ~30 MB/sidecar = 420 MB overhead unnecessary at Phase 9 scale; consistent with single-server pattern already used for ChromaDB and OTel Collector |
| 3 | mTLS strategy | **Self-signed CA for Phase 9** — SPIFFE/SPIRE deferred to Phase 10/v2 | Self-signed CA + Kubernetes Secret mounts sufficient for v1; SPIFFE adds SPIRE server + agent DaemonSet — not needed until multi-cluster or external-party workload identity is required |
| 4 | Module count | **14 modules confirmed** (Groups I–IV) + infrastructure/mcp + apps/default/server = 16 services total requiring Dockerfiles and manifests | `find modules/ -name agent-card.json` confirmed 14 entries on 2026-03-04 |
| 5 | Docker Compose profiles | **Add `security` profile for OPA server** — keep existing `modules`, `keycloak`, `observability-full` profiles unchanged | Backwards-compatible; OPA is opt-in at development time; `docker compose --profile security up` is the new security-enabled dev mode |

---

## 9. Recommended Phase 9 Checklist (for Executive Planner review)

> Do NOT add to `docs/Workplan.md` directly — hand off to Executive Planner after user approval.

### Pre-implementation gate items
- [x] Inventory all modules in `modules/` — **14 modules confirmed** (2026-03-04)
- [ ] Verify `shared/schemas/agent-card.schema.json` exists; author if missing (schemas-first rule)
- [x] Decide OPA deployment mode — **shared OPA server, audit → enforce** (2026-03-04)
- [x] Decide mTLS strategy — **self-signed CA for Phase 9; SPIFFE deferred to Phase 10** (2026-03-04)
- [x] Decide gVisor scope — **CI + production only; standard runc locally** (2026-03-04)
- [x] Decide Helm vs raw manifests — **raw manifests in `deploy/k8s/` for Phase 9** (2026-03-04)
- [x] Decide Docker Compose profile strategy — **add `security` profile for OPA; keep existing profiles** (2026-03-04)

### §9.0 — Deferred Phase 8 Items
- [ ] Implement `GET /api/agents` in `apps/default/server/src/routes/agents.ts`
- [ ] Wire `/api/agents` in Internals panel agent-card browser (replacing `/api/resources`)
- [ ] Replace Working Memory `resources/subscribe` stub with live subscriber registry + A2A emission
- [ ] Verify MCP server routes `notifications/resources/updated` A2A events to SSE client sessions
- [ ] End-to-end test: write to working memory → Internals panel receives `notifications/resources/updated` within 500 ms
- [ ] Install `@lhci/cli`, author `lighthouserc.json` with ≥ 90 thresholds
- [ ] Run Lighthouse live audit; remediate any category < 90; integrate as `pnpm run lighthouse` CI step
- [ ] Verify all Groups I–IV modules emit `traceparent` in every MCPContext envelope
- [ ] Audit and fix all test fixtures that construct MCPContext without `traceparent`
- [ ] Promote `traceparent` to `required` in `shared/schemas/mcp-context.schema.json`
- [ ] Run full 153-test suite; confirm all pass with `traceparent` required

### §9.1 — Security
- [ ] Create `security/` directory with `README.md`
- [ ] Author `scripts/gen_opa_data.py` — generate `security/data/modules.json` from all `agent-card.json` files
- [ ] Author `security/policies/module-capabilities.rego` — capability isolation rules
- [ ] Author `security/policies/inter-module-comms.rego` — A2A task delegation rules
- [ ] Run `opa test security/policies/` — all policy tests pass
- [ ] Configure gVisor `RuntimeClass` manifest at `deploy/k8s/runtime-class-gvisor.yaml`
- [ ] Add `runtime: runsc` to module services in `docker-compose.yml` production profile
- [ ] Test each module's Docker image under gVisor for syscall compatibility
- [ ] Author `scripts/gen_certs.sh` — generate self-signed mTLS CA and per-module certificates
- [ ] Run Trivy scan on all `endogenai/*` images; remediate HIGH/CRITICAL findings
- [ ] Apply `securityContext.runAsNonRoot: true`, `readOnlyRootFilesystem: true` to all pod specs
- [ ] Perform full inter-module security review; document findings in `security/review/phase-9-security-review.md`
- [ ] Author `docs/guides/security.md`

### §9.2 — Deployment
- [ ] Create `deploy/docker/base-python.Dockerfile` and `deploy/docker/base-node.Dockerfile`
- [ ] Author per-module `Dockerfile` for all Groups I–IV modules (multi-stage, non-root, production-optimized)
- [ ] Test each Dockerfile: build, run test suite in container, Trivy scan
- [ ] Author `Makefile` or `scripts/build_images.sh` for building all module images
- [ ] Create `deploy/k8s/` directory structure with namespace, NetworkPolicy, and RuntimeClass manifests
- [ ] Author Kubernetes `Deployment`, `Service`, and `HPA` manifests for each module
- [ ] All Deployment specs include: gVisor `runtimeClassName`, non-root `securityContext`, resource requests/limits, readiness/liveness probes
- [ ] Apply per-module NetworkPolicy: ingress from mcp-server only; egress to a2a-broker only
- [ ] Author `deploy/k8s/README.md`: prerequisites, CNI requirement, `kubectl apply -k` instructions
- [ ] Validate: `kubectl apply --dry-run=client -f deploy/k8s/` — no errors
- [ ] Run `docker compose config` — no syntax errors in `docker-compose.yml`
- [ ] Audit `docker-compose.yml` against full module inventory; add missing services under profiles
- [ ] Author `docker-compose.override.yml` for local dev (hot-reload mounts, gVisor off)
- [ ] Author `.env.example` with all required env vars documented

### §9.3 — Documentation Completion
- [ ] Author `docs/guides/security.md` (the primary remaining major doc gap)
- [ ] Author `security/README.md`
- [ ] Update `observability/README.md` (deferred from Phase 8)
- [ ] Install `markdown-link-check`; author `.markdown-link-check.json`
- [ ] Run broken-link audit on all `docs/*.md` and correct all broken internal links
- [ ] Cross-linking audit: verify all docs reference their upstream/downstream context per D2 table
- [ ] Audit all 14+ module `README.md` files; author any missing ones
- [ ] Author AsyncAPI spec for `resources/subscribe` notifications channel (optional but recommended)
- [ ] Add `mkdocs.yml` configuration for optional docs-site build (`mkdocs build`)

### M9 milestone declaration gate
- [ ] `kubectl apply --dry-run=client -f deploy/k8s/` — exit 0
- [ ] `docker compose up` (with `--profile full`) brings up the complete local stack
- [ ] All 153+ tests passing (including 9.0 additions)
- [ ] `pnpm run lighthouse` — all four categories ≥ 90
- [ ] `opa test security/policies/` — all policy tests passing
- [ ] `markdown-link-check` — zero broken internal links
- [ ] `docs/guides/security.md` authored and cross-linked
- [ ] `deploy/k8s/README.md` authored

---

## 10. Key Decisions Summary

| Decision | Rationale | Source |
|---|---|---|
| OPA single shared server (audit → enforce rollout) | 14 × sidecar = 420 MB overhead; shared server consistent with ChromaDB/OTel patterns; start audit-only | D2 §9.1; D1 microglial analogy; user decision 2026-03-04 |
| gVisor CI + production only (not local macOS dev) | No macOS port; Docker Desktop VM lacks KVM; write gVisor-compatible images, validate in CI | D2 §9.1; gVisor docs; user decision 2026-03-04 |
| Self-signed mTLS CA (SPIFFE as Phase 10) | Simpler for Phase 9 scope; SPIFFE adds significant operational complexity | D2 §9.1; SPIFFE/SPIRE docs |
| Raw Kubernetes manifests (Helm as Phase 10) | Meets M9 deliverable requirement with lower complexity | D2 §9.2 |
| Docker multi-stage for all modules | Production image optimization (myelination analogy); non-root, minimal base | D2 §9.2; OWASP container security |
| HPA at 70% CPU threshold (custom metrics Phase 10) | Simple, requires no additional Prometheus Adapter setup for Phase 9 | D2 §9.2; K8s HPA docs |
| OPA capability rules derived from agent-card.json | Endogenous-first — policy grounded in existing system knowledge, not authored from scratch | AGENTS.md; D1 danger hypothesis analogy |
| Documentation-first within 9.3 (Hebbian LTP) | AGENTS.md documentation-first mandate; docs co-authored with implementation strengthens accuracy | AGENTS.md; D1 §9.3 |
| schemas-first for agent-card.json verification | AGENTS.md guardrail: verify/land `shared/schemas/agent-card.schema.json` before 9.0.1 | AGENTS.md |

---

## 11. Handoff Notes for Phase Executive

This synthesis is based on:
- `docs/Workplan.md` §9.0–9.3 (read 2026-03-04) — M8 declared 2026-03-03; 153/153 tests passing
- `docs/architecture.md` — Phase 9 cross-cutting concerns layer
- `docs/research/phase-8-synthesis-workplan.md` — format reference and continuity context (Phase 8 deferred items = Phase 9.0)
- Fetched biological sources: 17 sources in `docs/research/sources/phase-9/bio-*.md`
- Fetched technology sources: 13 sources in `docs/research/sources/phase-9/tech-*.md`

**D1**: `docs/research/phase-9-neuroscience-security-deployment.md`
**D2**: `docs/research/phase-9-technologies-security-deployment.md`
**D3**: this document

**Recommended first action**: resolve Open Question #1 (gVisor on macOS dev machines) — this determines whether Phase 9.1 gVisor work can be tested locally or is CI/production-only. It affects every module Dockerfile and the `docker-compose.override.yml` scope.

**Recommended second action**: run the module inventory (`find modules/ -name "agent-card.json" | wc -l`) to confirm the exact module count before authoring Kubernetes manifests. Kubernetes manifest count is proportional to module count — this affects Phase 9.2 effort sizing.
