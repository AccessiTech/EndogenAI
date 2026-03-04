---
id: guide-security
version: 0.3.0
status: current
last-reviewed: 2026-03-04
---

# Security

> **Status: current** — Boundary validation patterns (Phase 1), OAuth 2.1 authentication layer (Phase 8.2), and
> Phase 9 production-hardening (OPA policy enforcement, gVisor sandboxing, mTLS, Trivy, container security context)
> are all documented here. Phase 9 implementation is in progress (§§9.1–9.2).

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

<!-- Phase 9 addition — 2026-03-04 -->
## Security Architecture — Phase 9 Production Hardening

EndogenAI applies a **multi-layer "immune privilege"** model inspired by the central nervous system's protective
mechanisms. The gateway authentication acts as a blood–brain barrier; OPA policy enforcement mirrors microglial
patrolling; and gVisor container sandboxing provides apoptotic isolation of compromised workloads.

| Layer | Biological analogue | Implementation |
| --- | --- | --- |
| Gateway authentication | Blood–brain barrier | OAuth 2.1 + PKCE JWT (§8.2); all `/api/*` routes require Bearer token |
| Policy enforcement | Microglial patrolling | OPA Rego policies derived endogenously from `agent-card.json` files |
| Container sandboxing | Apoptosis / immune isolation | gVisor `runtimeClassName: gvisor` (CI + production only) |
| Network isolation | Glial scar / CNS immune privilege | Kubernetes `NetworkPolicy` (default-deny; per-module allowlist) |
| Certificate-based identity | MHC-I molecule | mTLS with self-signed CA; module certificates mounted as K8s Secrets |

---

## Prerequisites

| Tool | Version | Install |
| --- | --- | --- |
| OPA | ≥ 0.68 | `docker compose --profile security up opa` |
| gVisor (`runsc`) | `latest` | CI + production only; not required on macOS dev |
| OpenSSL | ≥ 3.0 | `brew install openssl` (macOS) |
| Trivy | ≥ 0.55 | `brew install trivy` (macOS) |

See [Toolchain Guide](toolchain.md) for the full Phase 9 tool command reference.

---

## Open Policy Agent (OPA)

<!-- Phase 9 addition — 2026-03-04 -->

OPA enforces **capability isolation** rules across all 16 EndogenAI services. Rules are generated _endogenously_ —
derived directly from each module's `agent-card.json` — so policy always reflects the declared capabilities of the
live system. This is the endogenous-first principle applied to security.

### Policies

| File | What it controls |
| --- | --- |
| `security/policies/module-capabilities.rego` | Which capabilities each module is allowed to assert (default deny; allow if in `agent-card.json` capabilities array) |
| `security/policies/inter-module-comms.rego` | Which modules may send A2A calls to which other modules (default deny all cross-module calls; allow declared consumers + gateway bypass + mcp-server target) |

### Deployment

OPA runs as a **single shared server** at `http://localhost:8181`. It is gated behind the `security` Compose
profile so local development runs without OPA by default:

```bash
# Start OPA server alongside backing services
docker compose --profile security up -d

# Start all modules + OPA + backing services
docker compose --profile modules --profile security up -d
```

OPA starts in **audit mode** (`OPA_ENFORCE=false`). Violations are logged to OTel but requests are not blocked.
This lets you observe the policy effect before enforcement is turned on.

### Generating OPA data

Policy data is generated endogenously from all `agent-card.json` files:

```bash
# Generate security/data/modules.json from all agent-card.json files
uv run python scripts/gen_opa_data.py
```

Re-run after adding or modifying any module's `agent-card.json`. The output file is loaded by OPA at startup.

### Running policy tests

```bash
# Run OPA unit tests for all policies
opa test security/policies/
```

All tests must pass before promoting from audit mode to enforce mode.

### Audit → enforce promotion

1. Start OPA in audit mode (`OPA_ENFORCE=false`)
2. Run the full test suite: `pnpm run test && uv run pytest`
3. Review OPA decision logs for unexpected denials
4. Remediate any flagged misconfigurations in `agent-card.json` or the Rego policies
5. Set `OPA_ENFORCE=true`; re-run test suite to confirm no regressions
6. Tag the passing state as the enforcement baseline

---

## gVisor Container Sandboxing

<!-- Phase 9 addition — 2026-03-04 -->

[gVisor](https://gvisor.dev/) provides kernel-level isolation by intercepting all system calls from module
containers. It is the **apoptosis analogue** — a hard isolation boundary that limits the blast radius if any module
container is compromised.

### Scope

| Environment | gVisor required? |
| --- | --- |
| macOS development | **No** — Docker Desktop on macOS lacks KVM; use standard `runc` |
| CI (GitHub Actions) | **Yes** — `runsc` runtime applied to all module container jobs |
| Production Kubernetes | **Yes** — `runtimeClassName: gvisor` in all 16 pod specs |

Do not attempt to enable gVisor on macOS — the `runsc` runtime is not supported by Docker Desktop and causes
startup failures.

### Writing gVisor-compatible Dockerfiles

gVisor restricts certain kernel features. These patterns are **required** in all module Dockerfiles:

```dockerfile
# CORRECT — no /proc writes; no raw sockets; non-root user
FROM endogenai/base-python:3.11  # uses nobody UID 65534
WORKDIR /app
COPY --chown=nobody:nobody . .
USER nobody
EXPOSE 8001
CMD ["uv", "run", "uvicorn", "module.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Prohibited patterns** in any EndogenAI Dockerfile:

- Writing to `/proc` — use `emptyDir: { medium: "Memory" }` tmpfs mounts instead
- Creating raw sockets (`AF_PACKET`, `CAP_NET_RAW`) — use standard TCP/UDP only
- Capabilities beyond the default set — all capabilities must be dropped via `securityContext`

### RuntimeClass manifest

The gVisor `RuntimeClass` is declared at `deploy/k8s/runtime-class-gvisor.yaml`. All production Kubernetes
`Deployment` manifests reference it:

```yaml
spec:
  template:
    spec:
      runtimeClassName: gvisor
```

---

## mTLS Inter-Module Communication

<!-- Phase 9 addition — 2026-03-04 -->

All A2A and MCP calls between module services are encrypted and mutually authenticated using **mutual TLS**.
Phase 9 uses a self-signed CA; SPIFFE/SPIRE automatic certificate rotation is deferred to Phase 10.

### Generating certificates

```bash
# Generate self-signed CA + per-module certificates
bash scripts/gen_certs.sh
```

This creates `security/certs/` (gitignored) with:
- `ca.crt` / `ca.key` — root CA
- `<module-name>.crt` / `<module-name>.key` — per-module leaf certificates

### Mounting certificates in Kubernetes

```bash
# Create a TLS Secret for a module
kubectl create secret tls <module>-tls \
  --cert=security/certs/<module>.crt \
  --key=security/certs/<module>.key \
  --namespace=endogenai-modules
```

Each module's `Deployment` manifest references the Secret via `spec.template.spec.volumes[].secret`.

### Phase 10 upgrade path

[SPIFFE/SPIRE](https://spiffe.io/) for automatic certificate rotation and short-lived X.509-SVIDs is planned for
Phase 10. The self-signed CA approach used here is a conscious deferral — not a permanent choice.

---

## Container Security Hardening

<!-- Phase 9 addition — 2026-03-04 -->

All 16 production pod specs apply the following `securityContext`:

```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
  seccompProfile:
    type: RuntimeDefault
```

Where writable scratch space is required (e.g. pip cache, temp files), add an `emptyDir` volume:

```yaml
volumes:
  - name: tmp
    emptyDir: {}
volumeMounts:
  - name: tmp
    mountPath: /tmp
```

### Base images

Non-root base images are defined in `deploy/docker/`:

| File | Purpose |
| --- | --- |
| `deploy/docker/base-python.Dockerfile` | Multi-stage Python 3.11; `nobody` UID 65534; no package caches; gVisor-compatible |
| `deploy/docker/base-node.Dockerfile` | Multi-stage Node.js 20; `nobody` UID 65534; gVisor-compatible |

### Trivy vulnerability scanning

```bash
# Scan a single module image
trivy image endogenai/<module>

# Scan all K8s manifests for misconfigurations
trivy config deploy/k8s/

# Fail CI on HIGH or CRITICAL findings
trivy image --exit-code 1 --severity HIGH,CRITICAL endogenai/<module>
```

Accepted waivers are documented in `.trivyignore` with the CVE ID and written rationale.

---

## Inter-Module Interface Security Review

<!-- Phase 9 addition — 2026-03-04 -->

The Phase 9 security review covers:

- Unauthenticated call paths between modules
- Exposed ports and NetworkPolicy coverage
- Non-root user compliance in all Dockerfiles
- `readOnlyRootFilesystem` compliance
- OPA policy enforcement verification
- mTLS certificate deployment
- Trivy scan findings and accepted waivers

Findings are documented in:

```
security/review/phase-9-security-review.md
```

This file is created during Phase 9 (§9.1) implementation.

---

## Verification Checklist

```bash
# 1. OPA server health check
curl -fsS http://localhost:8181/health

# 2. Run all OPA unit tests
opa test security/policies/

# 3. Confirm gVisor runtime (CI / production)
docker run --rm --runtime=runsc busybox uname -a

# 4. Trivy image scan (fail on HIGH/CRITICAL)
trivy image --exit-code 1 --severity HIGH,CRITICAL endogenai/<module>

# 5. Policy data generation
uv run python scripts/gen_opa_data.py

# 6. mTLS cert generation
bash scripts/gen_certs.sh
```

---

## References

- [Validation Spec](../../shared/utils/validation.md)
- [Architecture Overview](../architecture.md)
- [Deployment Guide](deployment.md) — K8s manifests, NetworkPolicy, Trivy integration
- [Observability Guide](observability.md) — OTel tracing, Prometheus security metrics
- [Toolchain Guide](toolchain.md) — Phase 9 tool commands
- [Workplan — Phase 9](../Workplan.md#phase-9--cross-cutting-security-deployment--documentation)
- [Phase 9 Neuroscience Research](../research/phase-9-neuroscience-security-deployment.md) — immune privilege analogues
- [Phase 9 Technology Research](../research/phase-9-technologies-security-deployment.md) — OPA, gVisor, mTLS technology choices
- [OPA Documentation](https://www.openpolicyagent.org/docs/)
- [gVisor Documentation](https://gvisor.dev/docs/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
