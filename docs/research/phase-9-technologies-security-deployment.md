# Phase 9 — D2: Technologies for Security, Deployment & Documentation

_Generated: 2026-03-04 by Docs Executive Researcher_

> **Scope**: Technology survey for Phase 9 sub-phases — Security, Deployment & Documentation.
> This document audits available tools, specs, and frameworks for each Phase 9 sub-component.
> Sub-phases: 9.0 Deferred Phase 8 Items · 9.1 Security & Sandboxing · 9.2 Deployment · 9.3 Documentation Completion

**Sources fetched**: `docs/research/sources/phase-9/tech-*.md` (12 files, fetched 2026-03-04); OWASP Container Security guidelines sourced from domain knowledge (project page unavailable)

---

## Overview

Phase 9 is the production-hardening phase of EndogenAI. The technology landscape spans four domains:

1. **Deferred completions** (9.0): closing the last Phase 8 stubs — live SSE notifications, agent-card discovery, Lighthouse CI, and schema promotion.
2. **Security** (9.1): policy-as-code for capability isolation (OPA/Rego), container sandboxing (gVisor), workload identity (SPIFFE/SPIRE), and network isolation (Kubernetes NetworkPolicy).
3. **Deployment** (9.2): container packaging (Docker multi-stage), Kubernetes orchestration (Deployments, Services, HPA), and local stack validation (Docker Compose).
4. **Documentation** (9.3): completing remaining cross-linked docs, guided by tooling for broken-link detection and async API specification.

---

## §9.0 — Deferred Phase 8 Completions: Technology Approaches

### `/api/agents` — Live Agent-Card Discovery

The Internals panel currently falls back to `/api/resources` for module listing. The full implementation requires a `/api/agents` endpoint that:

1. Reads each module's `/.well-known/agent-card.json` at runtime
2. Aggregates results into an agents array
3. Returns `{ agents: AgentCard[] }` to the browser Internals panel

**Implementation pattern**: the gateway can discover module URLs from the `uri-registry.json` or from a static environment variable list. For each module URL, it issues a `GET /.well-known/agent-card.json` using the Node.js `fetch` API (available natively in Node 18+), with a short timeout (2s) and graceful degradation on failure.

```typescript
// Sketch: apps/default/server/src/routes/agents.ts
import { Hono } from 'hono'

const MODULE_URLS = process.env.MODULE_URLS?.split(',') ?? []

export const agentsRouter = new Hono()

agentsRouter.get('/api/agents', async (c) => {
  const results = await Promise.allSettled(
    MODULE_URLS.map(url =>
      fetch(`${url}/.well-known/agent-card.json`, { signal: AbortSignal.timeout(2000) })
        .then(r => r.json())
    )
  )
  const agents = results
    .filter(r => r.status === 'fulfilled')
    .map(r => (r as PromiseFulfilledResult<unknown>).value)
  return c.json({ agents })
})
```

**Design decisions**: `Promise.allSettled` ensures a single unresponsive module does not block the entire response. Timeout via `AbortSignal.timeout(2000)` uses the native Node 18 API without external dependencies. Failed fetches are omitted from the result (graceful degradation matches the biological analogue of synaptic pruning — silent failures, not crashes).

---

### `resources/subscribe` — Live SSE Notifications

The MCP spec (2025-06-18) defines `resources/subscribe` as a JSON-RPC method that, when invoked, registers the client to receive `notifications/resources/updated` push events when a resource changes.

**Server-sent events subscription pattern** (MDN, fetched 2026-03-04): SSE uses the `text/event-stream` content type. Each event is a block of `field: value` lines separated by blank lines. Key fields: `data`, `event`, `id`, `retry`. The browser's `EventSource` API auto-reconnects on connection drop, sending `Last-Event-ID` header on reconnect — this is the resume mechanism.

**Working Memory implementation**: the `modules/group-ii-cognitive-processing/working-memory` module currently returns stub responses for `resources/subscribe`. Full implementation requires:

1. An in-memory subscriber registry (Map from `sessionId` to `AbortController`)
2. On resource write/update, iterating subscribers and emitting `notifications/resources/updated` via the existing A2A event bus
3. The MCP server (`infrastructure/mcp`) routing these notifications back to connected SSE clients

**MCP Streamable HTTP transport** defines how server-initiated messages reach clients: the `GET /mcp` SSE channel (opened by the client) carries `notifications/*` events. The gateway's `GET /api/stream` relay propagates them to the browser `EventSource`.

```typescript
// Pattern: Working Memory emits on write
import { sendA2AEvent } from 'endogenai-a2a'

async function writeResource(id: string, content: unknown): Promise<void> {
  await store.set(id, content)
  // Emit MCP notification via A2A event bus
  await sendA2AEvent({
    method: 'notifications/resources/updated',
    params: { uri: `brain://working-memory/${id}` }
  })
}
```

---

### Lighthouse CI — Automated Auditing

**Lighthouse** (Google Chrome, fetched 2026-03-04) is an open-source automated auditing tool for web performance, accessibility, best practices, and SEO. It can be run:

- As a Chrome DevTools panel audit
- Via `lighthouse` CLI against a running URL: `npx lighthouse http://localhost:5173 --output json --quiet`
- Via **Lighthouse CI** (`@lhci/cli`) — wraps Lighthouse in a CI pipeline, compares scores against configured thresholds, and can store results in a Lighthouse CI server or local file system

**Target**: ≥ 90 across Performance, Accessibility, Best Practices, and SEO.

The Lighthouse CI configuration (`lighthouserc.json`) specifies assertions:
```json
{
  "ci": {
    "collect": { "url": ["http://localhost:5173"], "numberOfRuns": 3 },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["error", { "minScore": 0.9 }]
      }
    }
  }
}
```

Run sequence: start the app, run `npx lhci autorun`, record the JSON report. Integrate into the existing `pnpm run test` pipeline as a separate `pnpm run lighthouse` script in `apps/default/client/package.json`.

---

### `traceparent` Promotion to Required

The W3C Trace Context specification (Level 1, W3C Recommendation, fetched 2026-03-04) defines the `traceparent` header format:

```
traceparent: {version}-{trace-id}-{parent-id}-{trace-flags}
00-4bf92f3577b34da6-00f067aa0ba902b7-01
```

- **version**: `00` (current)
- **trace-id**: 16-byte random hex, unique per trace
- **parent-id**: 8-byte random hex, unique per span
- **trace-flags**: `01` = sampled

**Schema promotion**: `shared/schemas/mcp-context.schema.json` currently has `traceparent` as an optional string property. Promoting it to `required` is a breaking schema change that requires:

1. Verifying all Phase 7 modules bootstrap OTel and always populate `traceparent` before emitting MCPContext
2. Updating the schema: remove `traceparent` from optional, add to `required` array
3. Running all 153 existing tests to confirm no test fixture omits `traceparent`
4. Updating all module test fixtures that construct MCPContext objects manually

This is a prerequisite-gated change — it cannot land until Phase 7 OTel bootstrap is confirmed across all modules. The M8 milestone note confirms this prerequisite is met.

---

## §9.1 — Security: Technology Stack

### Open Policy Agent (OPA) — Policy-as-Code

**OPA** (CNCF graduated project, fetched 2026-03-04) is a general-purpose policy engine that evaluates authorization decisions against structured data using the **Rego** policy language. Key properties:

- **Decoupled policy from application**: policies stored in `.rego` files, loaded at runtime. Application code calls OPA's REST API or uses the Go/WASM library — it does not embed authorization logic.
- **Input-based evaluation**: OPA receives a JSON `input` document (the authorization request) and a JSON `data` document (policy data, including the requesting module's agent card). It evaluates the policy and returns a JSON `result`.
- **Deployment modes**:
  - **Sidecar**: one OPA instance per module pod, receiving policy-check requests via loopback HTTP
  - **Standalone server**: shared OPA policy server, called by all modules over the cluster network
  - **SDK embed**: OPA WASM bundle compiled into a TypeScript/Go service for zero-latency inline evaluation
- **Rego language**: a Datalog-inspired logic language designed for hierarchical JSON data evaluation. Rego rules are **declarative**: they define conditions under which a property is `true`, not imperative steps.

**Rego example for EndogenAI capability isolation**:
```rego
# security/policies/module-capabilities.rego
package endogenai.module_capabilities

import future.keywords.in

# Allow if the requested capability is declared in the module's agent-card
default allow = false

allow {
  input.requested_capability in data.modules[input.module_id].capabilities
}

# Audit: flag if request is allowed but at capability boundary
audit_flag {
  allow
  count(data.modules[input.module_id].capabilities) - 1 ==
    indexof(data.modules[input.module_id].capabilities, input.requested_capability)
}
```

**OPA and agent-card.json**: each module's `agent-card.json` `capabilities` array becomes the OPA data document for that module. This grounds policy entirely in the endogenous system knowledge — OPA policy divergence from `agent-card.json` is caught immediately by schema validation.

---

### gVisor — Container Sandboxing

**gVisor** (Google open source, fetched 2026-03-04) is a user-space application kernel that implements the Linux system call surface in Go. It acts as a guest OS between the container process and the host kernel, intercepting all syscalls before they reach the host:

- **runsc runtime**: gVisor's OCI-compatible runtime shim. Containers run with `--runtime=runsc` in Docker, or via `runtimeClassName: gvisor` in Kubernetes (requires the `RuntimeClass` resource).
- **Two sandbox modes**:
  - **KVM mode** (`--platform=kvm`): hardware virtualization; near-native performance; requires KVM access on the host
  - **ptrace mode** (`--platform=ptrace`): uses Linux `ptrace`; no hardware requirements; ~2× performance penalty; good for development environments
- **Compatibility**: gVisor supports most Linux syscalls but has known gaps — notably incomplete support for some `/proc` filesystem paths, some network namespacing, and some perf-related syscalls. The **gVisor compatibility matrix** should be consulted before deployment.
- **Docker Compose integration**: set `runtime: runsc` in the container definition in `docker-compose.yml` after installing gVisor on the host.
- **Kubernetes integration**: create a `RuntimeClass` named `gvisor`, annotate applicable pod specs with `runtimeClassName: gvisor`.

**EndogenAI applicability**: Python ML modules (Group I–IV) are good gVisor candidates — they use standard Python syscalls and do not require `/proc` inspection or raw socket access. The `infrastructure/mcp` Node.js server should be tested for compatibility before mandating gVisor.

---

### SPIFFE/SPIRE — Workload Identity

**SPIFFE** (Secure Production Identity Framework For Everyone, CNCF, fetched 2026-03-04) defines a standard for workload identity in distributed systems:

- **SVID (SPIFFE Verifiable Identity Document)**: an X.509 certificate or JWT asserting a workload's identity via a SPIFFE ID (`spiffe://trust-domain/path`)
- **SPIRE** (SPIFFE Runtime Environment): the reference implementation — a server issues SVIDs; agents on each node attest workloads and distribute SVIDs

For EndogenAI inter-module mTLS:
1. Each module pod gets a SPIFFE SVID via the SPIRE agent (injected as a Unix domain socket mounted into the pod)
2. Modules use their SVID as a client certificate when making outbound MCP/A2A calls
3. The receiving module verifies the client certificate against the SPIRE trust bundle
4. OPA policy can inspect the verified SPIFFE ID to enforce per-identity authorization

SPIFFE/SPIRE adds strong workload identity without requiring a PKI team — it handles certificate rotation automatically. However, SPIRE adds operational complexity (a server + per-node agent DaemonSet). For Phase 9, **mTLS with self-signed certificates** and a shared CA secret is a simpler starting point that can be upgraded to SPIFFE later.

---

### Trivy — Container Image Scanning

**Trivy** (Aqua Security, open source) scans container images for:
- OS package vulnerabilities (CVE database)
- Application dependency vulnerabilities (pip packages, npm packages)
- Misconfigurations (Dockerfile, Kubernetes manifests)
- Secrets accidentally embedded in images

```bash
trivy image endogenai/working-memory:latest
trivy config deploy/k8s/
```

**Integration**: add a `trivy image` scan step to the Docker build CI pipeline. Fail the build on HIGH or CRITICAL vulnerabilities. Configure `.trivyignore` for false positives with documented rationale.

---

### Kubernetes NetworkPolicy

Kubernetes **NetworkPolicy** resources define pod-level firewall rules using label selectors (fetched 2026-03-04). Key design for EndogenAI:

- **Default deny**: apply a default-deny NetworkPolicy in each module namespace to block all ingress/egress not explicitly allowed
- **Allow MCP**: each module pod allows ingress on its MCP port from the `infrastructure/mcp` gateway only
- **Allow A2A**: each module pod allows egress to `infrastructure/a2a` on the A2A port only
- **Deny cross-module direct**: module pods must not be able to reach each other directly — all inter-module communication routes through the MCP server or A2A broker

```yaml
# Example: default deny all
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: endogenai-modules
spec:
  podSelector: {}  # matches all pods in namespace
  policyTypes: [Ingress, Egress]
```

NetworkPolicy requires a **CNI plugin** that supports it: Calico, Cilium, or Weave Net. The default `kubenet` does not enforce NetworkPolicy.

---

### seccomp and AppArmor Profiles

Container syscall filtering provides an additional security layer:

- **seccomp** (secure computing mode): Linux kernel mechanism for filtering syscalls. Docker/Kubernetes support custom seccomp profiles that whitelist allowed syscalls and kill/log processes that attempt disallowed syscalls. The `RuntimeDefault` profile (recommended) blocks ~50 dangerous syscalls.
- **AppArmor**: Linux security module for path-based access control. Kubernetes supports AppArmor profiles via pod annotations. Complementary to seccomp (seccomp filters by syscall; AppArmor by path/operation).

For Python ML modules, the `RuntimeDefault` seccomp profile is typically sufficient. Custom profiles can be generated using **seccomp-profile-builder** or by recording syscalls during a test run with `strace`.

---

## §9.2 — Deployment: Technology Stack

### Docker Multi-Stage Builds

Docker **multi-stage builds** (Docker docs, fetched 2026-03-04) allow multiple `FROM` instructions in a single Dockerfile, with only the final stage included in the produced image:

**Python module pattern** (using `uv`):
```dockerfile
# Stage 1: build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: production runtime (smaller base)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
USER nobody
CMD ["python", "-m", "src.module"]
```

**Node.js module pattern** (TypeScript → compiled JS):
```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY tsconfig.json src/ ./
RUN pnpm build

FROM node:22-slim AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER node
CMD ["node", "dist/index.js"]
```

Key best practices from Docker docs:
- Run as non-root (`USER nobody` / `USER node`)
- Use specific digest-pinned base images in production (`FROM python:3.12.2-slim@sha256:...`)
- Copy only what is needed into the runtime stage
- Set `WORKDIR` before `COPY` to avoid root-owned files
- Use `.dockerignore` to exclude `.venv/`, `node_modules/`, `__pycache__/`, `.git/`

**Base image**: define `FROM endogenai/base-python:3.12-slim` as a shared base for all Python modules that pre-installs common system packages (build-essential, libssl-dev) to speed up per-module builds. Similarly `endogenai/base-node:22-slim` for TypeScript modules.

---

### Kubernetes Manifests

**Deployment** (Kubernetes docs, fetched 2026-03-04): the primary workload resource for stateless module pods.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: working-memory
  namespace: endogenai-modules
  labels:
    app: working-memory
    phase: "5"
    group: group-ii
spec:
  replicas: 2
  selector:
    matchLabels:
      app: working-memory
  template:
    metadata:
      labels:
        app: working-memory
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      runtimeClassName: gvisor          # Phase 9.1 sandbox
      serviceAccountName: working-memory
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
      containers:
        - name: working-memory
          image: endogenai/working-memory:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 30
            failureThreshold: 3
          envFrom:
            - configMapRef:
                name: working-memory-config
            - secretRef:
                name: working-memory-secrets
```

**Horizontal Pod Autoscaler** (Kubernetes docs, fetched 2026-03-04): scales replicas based on CPU, memory, or custom metrics.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: working-memory-hpa
  namespace: endogenai-modules
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: working-memory
  minReplicas: 1
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue
          averageValue: 800Mi
```

For ML workloads, CPU utilization at 70% is a reasonable HPA trigger. Custom Prometheus metrics (inference latency, queue depth) provide more semantically meaningful scaling signals but require the **Prometheus Adapter** (`k8s-prometheus-adapter`) — add to Phase 9.2 scope only if time permits.

---

### Helm Charts

**Helm** (CNCF) is the Kubernetes package manager. A Helm chart bundles related Kubernetes resources (Deployments + Services + ConfigMaps + HPAs) into a versioned, parameterizable unit. For EndogenAI:

- One chart per module group (`chart/group-i/`, `chart/group-ii/`, etc.) or one umbrella chart with per-module sub-charts
- Values files per environment: `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`
- Enables `helm upgrade --install` for atomic, rollback-capable deployments

However, Helm adds complexity. For an initial Phase 9.2 implementation, **raw manifests** in `deploy/k8s/` are simpler and meet the workplan requirement. Helm can be added as a Phase 10 improvement.

---

### Docker Compose Validation

The existing `docker-compose.yml` must be extended to cover the full local development stack. Validation checklist:

1. All module services defined (or can be added as profiles for opt-in)
2. `infrastructure/mcp` and `infrastructure/a2a` services are included
3. `observability/` services (ChromaDB, Ollama, OTel Collector, Prometheus, Grafana, Tempo) are included
4. Volume mounts and port mappings are consistent with module env vars
5. Health check definitions use `test:` with curl/wget against `/health` endpoint
6. Override file `docker-compose.override.yml` for local dev (hot-reload volumes, debug ports)

Run `docker compose config` to validate the final merged compose file for syntax errors.

---

### Skaffold — Local Kubernetes Development

**Skaffold** (Google) provides a `skaffold dev` workflow for local Kubernetes development: detects source changes, rebuilds images, and re-applies manifests automatically. Useful for Phase 9 testing of the full Kubernetes stack locally (via `kind` or `minikube`).

This is optional for Phase 9.2 — the primary deliverable is working manifests in `deploy/k8s/`. Skaffold setup can be documented as a developer productivity enhancement.

---

## §9.3 — Documentation Completion: Technology Approaches

### Outstanding Documentation Items

The Phase 9.3 workplan checklist confirms these items are already `[x]` complete:
- `docs/architecture.md`
- `docs/guides/getting-started.md`
- `docs/guides/adding-a-module.md`
- `docs/guides/observability.md`
- `README.md` quick-start
- `docs/guides/deployment.md`

**Outstanding items requiring Phase 9.3 work**:
- `docs/guides/security.md` — not yet authored
- `README.md` for the `security/` directory
- Cross-linking audit: verify all docs reference each other correctly
- `observability/README.md` update (noted in the M8 deferred list)
- Remaining module-level `README.md` files if gaps exist

---

### AsyncAPI for `resources/subscribe`

**AsyncAPI v3** (fetched 2026-03-04) provides a machine-readable specification format for event-driven APIs — the async equivalent of OpenAPI. For the `resources/subscribe` / `notifications/resources/updated` notification channel, AsyncAPI can formalize:

- Channel: `brain://working-memory/{resourceId}/notifications`
- Message schema: `{ method: "notifications/resources/updated", params: { uri: string } }`
- Bindings: server-sent events over HTTP

An AsyncAPI spec provides auto-generated documentation (via `@asyncapi/html-template`) and validates that notification schema matches `shared/schemas/`.

```yaml
asyncapi: 3.0.0
info:
  title: EndogenAI Resource Notifications
  version: 1.0.0
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
```

---

### Cross-Linking Strategy

A documentation cross-linking audit should verify every doc has appropriate outbound links:

| Doc | Must link to |
|---|---|
| `README.md` | `docs/guides/getting-started.md`, `docs/architecture.md` |
| `docs/architecture.md` | All module READMEs, `docs/guides/adding-a-module.md`, `docs/protocols/` |
| `docs/guides/security.md` | `security/README.md`, `docs/architecture.md`, OPA/gVisor external refs |
| `docs/guides/deployment.md` | `deploy/k8s/README.md`, `docker-compose.yml`, `docs/guides/getting-started.md` |
| Module READMEs | `shared/schemas/` (for consumed schemas), `docs/architecture.md` |

A broken-link checker (e.g. `markdown-link-check`) can automate this:
```bash
find docs/ -name "*.md" | xargs npx markdown-link-check --config .markdown-link-check.json
```

---

### MkDocs Material — Future Docs Site

**MkDocs Material** (fetched 2026-03-04) is a static site generator purpose-built for documentation: Markdown-in, beautiful searchable HTML-out. For Phase 9.3, **a `mkdocs.yml` configuration file** can be added to the repo root without requiring deployment — the existing Markdown files are already in the correct structure. Publishing to GitHub Pages (or a Netlify static site) becomes a single `mkdocs build` + `mkdocs gh-deploy`. This is low-effort and high-value for the Phase 9 documentation completion milestone.

---

## Technology Selection Rationale

| Technology | Reason for selection | EndogenAI fit |
|---|---|---|
| **OPA/Rego** | CNCF graduated; language-agnostic; decoupled policy from code; rich ecosystem | Supports Python and TypeScript module policy enforcement from a single policy store; maps to agent-card.json capabilities |
| **gVisor** | Google-backed; strong syscall isolation without full VM overhead; OCI-compatible | Appropriate for Python ML modules; reduces blast radius of any module-level vulnerability |
| **SPIFFE/SPIRE** | CNCF standard; automatic cert rotation; zero-PKI-team deployment | Phase 9 simplification: start with self-signed mTLS CA; SPIRE as a Phase 10 upgrade path |
| **Trivy** | Free, OSS, covers CVEs + misconfigs + secrets; integrates with CI | Catches supply-chain vulnerabilities in Python/Node deps before they reach production |
| **Kubernetes Deployments + HPA** | Industry standard; matches neurovascular coupling analogy for autoscaling | Per-module deployments match the cortical column modular architecture |
| **Docker multi-stage** | Required to produce production-grade images from development-heavy Python/Node services | `uv sync --frozen` in builder + minimal runtime stage matches myelination analogy |
| **AsyncAPI v3** | OpenAPI for event-driven APIs; machine-readable notifications spec | Formalizes `resources/subscribe` channel before implementation |
| **Lighthouse CI** | Official Google web audit tool; CI integration available; targets Phase 9.0 ≥90 threshold | Already partially verified in Phase 8 test suite; live browser audit requires running instance |
| **NetworkPolicy** | Kubernetes-native; no sidecar required for L3/L4 isolation | Enforces the no-direct-cross-module communication architectural constraint |

---

## Sources

| Topic | Source | Saved file |
|---|---|---|
| SSE subscription patterns | MDN: Using server-sent events | `docs/research/sources/phase-9/tech-sse-subscriptions.md` |
| W3C Trace Context / traceparent | W3C TR: Trace Context | `docs/research/sources/phase-9/tech-w3c-trace-context.md` |
| Lighthouse CI | Chrome Developers: Lighthouse overview | `docs/research/sources/phase-9/tech-lighthouse.md` |
| Open Policy Agent | OPA docs (openpolicyagent.org) | `docs/research/sources/phase-9/tech-opa-overview.md` |
| gVisor | gVisor docs (gvisor.dev) | `docs/research/sources/phase-9/tech-gvisor-overview.md` |
| SPIFFE/SPIRE | SPIFFE overview (spiffe.io) | `docs/research/sources/phase-9/tech-spiffe-spire.md` |
| Docker multi-stage builds | Docker docs: multi-stage builds | `docs/research/sources/phase-9/tech-docker-multistage.md` |
| Kubernetes Deployment | Kubernetes docs: Deployment | `docs/research/sources/phase-9/tech-k8s-deployment.md` |
| Kubernetes HPA | Kubernetes docs: HPA | `docs/research/sources/phase-9/tech-k8s-hpa.md` |
| Kubernetes NetworkPolicy | Kubernetes docs: NetworkPolicy | `docs/research/sources/phase-9/tech-k8s-network-policy.md` |
| MkDocs Material | MkDocs Material site | `docs/research/sources/phase-9/tech-mkdocs-material.md` |
| AsyncAPI v3 | AsyncAPI specification | `docs/research/sources/phase-9/tech-asyncapi.md` |
| OWASP Container Security | OWASP Container Security project (page unavailable; guidelines sourced from domain knowledge) | _not saved_ |
