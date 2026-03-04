# EndogenAI Kubernetes Manifests

This directory contains all Kubernetes manifests for deploying the EndogenAI system.

## Directory Structure

```
deploy/k8s/
  namespace.yaml                        # endogenai-modules + endogenai-infra namespaces
  network-policy-default-deny.yaml      # default deny-all NetworkPolicies
  runtime-class-gvisor.yaml             # gVisor RuntimeClass (§9.1)
  group-i-signal-processing/            # Group I modules
  group-ii-cognitive-processing/        # Group II modules
  group-iii-executive-output/           # Group III modules
  group-iv-adaptive-systems/            # Group IV modules
  infrastructure/                       # MCP server
  apps/                                 # Gateway + Ingress
```

## Prerequisites

- Kubernetes cluster with a **NetworkPolicy-compatible CNI** (e.g. Calico, Cilium)
- **gVisor** (`runsc`) installed on cluster nodes ([gVisor install guide](https://gvisor.dev/docs/user_guide/install/))
- `kubectl` configured and pointing at the target cluster
- Container images built and pushed (see `scripts/build_images.sh`)

## Quick Deploy

```bash
# 1. Create namespaces first
kubectl apply -f deploy/k8s/namespace.yaml

# 2. Apply all manifests recursively
kubectl apply -R -f deploy/k8s/
```

To verify without applying:
```bash
kubectl apply --dry-run=client -R -f deploy/k8s/
```

## Local Testing with kind

```bash
# Create a kind cluster with gVisor support
kind create cluster --config deploy/k8s/kind-config.yaml

# Load images into kind
kind load docker-image endogenai/gateway:latest
# (repeat for each image)

# Apply manifests
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -R -f deploy/k8s/
```

## Environment Variables and Kubernetes Secrets

Sensitive configuration (API keys, DB credentials, JWT secrets) must be stored as
Kubernetes Secrets and mounted as environment variables:

```bash
# Example: Create a secret for LiteLLM API key
kubectl create secret generic litellm-credentials \
  --namespace endogenai-modules \
  --from-literal=LITELLM_API_KEY=<your-key>
```

Reference the secret in your Deployment under `env`:

```yaml
env:
- name: LITELLM_API_KEY
  valueFrom:
    secretKeyRef:
      name: litellm-credentials
      key: LITELLM_API_KEY
```

Required secrets per namespace:

| Secret name | Namespace | Keys |
|-------------|-----------|------|
| `litellm-credentials` | endogenai-modules | `LITELLM_API_KEY` |
| `chromadb-credentials` | endogenai-modules | `CHROMADB_URL` |
| `gateway-secrets` | endogenai-infra | `JWT_SECRET`, `SESSION_SECRET` |

## HPA — Scaling

Check HPA status:
```bash
kubectl get hpa -n endogenai-modules
kubectl get hpa -n endogenai-infra
```

Describe a specific HPA for current metrics:
```bash
kubectl describe hpa working-memory -n endogenai-modules
```

To temporarily adjust thresholds (not persistent — update the YAML for permanent change):
```bash
kubectl patch hpa working-memory -n endogenai-modules \
  --patch '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":80}}}]}}'
```

## Troubleshooting gVisor

If pods fail with `RuntimeClass not found` or sandbox errors:

1. Verify gVisor is installed on nodes:
   ```bash
   kubectl get nodes -o wide
   # SSH to a node and check: runsc --version
   ```

2. Verify the RuntimeClass exists:
   ```bash
   kubectl get runtimeclass gvisor
   ```

3. Check pod events for sandbox errors:
   ```bash
   kubectl describe pod <pod-name> -n endogenai-modules
   ```

4. To run without gVisor for local testing, remove `runtimeClassName: gvisor` from
   the deployment spec (do not commit this change).

## Networking

The `network-policy-default-deny.yaml` enforces a default-deny posture in both namespaces.
Modules that need to communicate must have explicit allow NetworkPolicies added.

To allow a module to reach the MCP server:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-mcp-egress
  namespace: endogenai-modules
spec:
  podSelector:
    matchLabels:
      app: working-memory
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: endogenai-infra
    ports:
    - protocol: TCP
      port: 8000
```
