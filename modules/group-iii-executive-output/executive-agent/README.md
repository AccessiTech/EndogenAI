# executive-agent

**Group III — Executive & Output Modules**

The Executive Agent implements the BDI (Belief-Desire-Intention) deliberation loop for the
EndogenAI `brAIn` framework. It models the **prefrontal cortex / basal-ganglia** circuit:
DLPFC-style goal stack with priority ordering, OFC-weighted value scoring, and
striatal pathway analogues for commit (direct), suppress (indirect), and abort (hyperdirect).

---

## Purpose

- Maintain a prioritised **goal stack** (DLPFC model)
- Run a continuous **BDI deliberation cycle**: option generation → value scoring → OPA policy
  gating → intention commitment → capacity enforcement
- Gate all intention commits through **Open Policy Agent** (standalone, localhost:8181)
- Manage **agent identity** and self-model (append-only capability updates, achievement ring buffer)
- Receive **corollary-discharge feedback** from motor-output and adjust reward estimates
  (actor-critic RPE)
- Persist goals, identity deltas, and policies to the `brain.executive-agent` ChromaDB collection

---

## Neuroanatomy Mapping

| Component | Brain Analogue |
|-----------|----------------|
| `GoalStack` | DLPFC goal representation + OFC priority scoring |
| `DeliberationLoop` | BDI deliberation cycle (prefrontal-striatal loop) |
| `PolicyEngine` | Basal-ganglia gating (OPA = striatum policy centre) |
| `IdentityManager` | Default-mode network / frontal-lobe self-model |
| `FeedbackHandler` | Corollary discharge + actor-critic RPE (dopaminergic) |

---

## Interface

### A2A (JSON-RPC 2.0) — port 8161

```
POST /tasks
```

| `task_type` | Payload | Description |
|-------------|---------|-------------|
| `commit_intention` | `{goal_id, workflow_id?}` | Commit a goal and delegate to agent-runtime |
| `receive_feedback` | `MotorFeedback` | Receive corollary-discharge outcome from motor-output |
| `abort_goal` | `{goal_id, reason?}` | Abort a committed/executing goal |
| `get_identity` | `{}` | Return current `SelfModel` |

### MCP (SSE) — port 8261

```
POST /mcp/tools/call     — call a named tool
GET  /sse                — SSE event stream
```

| Tool | Description |
|------|-------------|
| `push_goal` | Add a new goal to the stack |
| `get_goal_stack` | Return all current goals |
| `evaluate_policy` | Evaluate an OPA policy rule |
| `update_identity` | Append an identity capability delta |
| `abort_goal` | Abort a goal by ID |
| `get_drive_state` | Get current motivational drive state |

### Well-known endpoint

```
GET /.well-known/agent-card.json
```

---

## Configuration

| File | Purpose |
|------|---------|
| `identity.config.json` | Agent name, core values, deliberation cadence, max active goals |
| `vector-store.config.json` | ChromaDB host, port, collection name |
| `embedding.config.json` | Ollama host, embedding model, dimensions |

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPA_URL` | `http://localhost:8181` | Open Policy Agent base URL |
| `CHROMADB_HOST` | `localhost` | ChromaDB host |
| `CHROMADB_PORT` | `8000` | ChromaDB port |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama host |
| `AGENT_RUNTIME_URL` | `http://localhost:8162` | agent-runtime A2A endpoint |
| `AFFECTIVE_URL` | `http://localhost:8151` | affective module A2A endpoint |
| `EA_PORT` | `8161` | A2A server port |
| `MCP_PORT` | `8261` | MCP SSE port |

---

## Deployment

### Local (development)

```bash
# From this directory
uv sync
uv run serve
```

### Docker

```bash
docker build -t endogenai/executive-agent:latest .
docker run -p 8161:8161 -p 8261:8261 endogenai/executive-agent:latest
```

### Docker Compose

```bash
# From repo root — starts ChromaDB, OPA, Temporal, and all modules
docker compose --profile modules up -d
```

---

## Development

```bash
# Install dependencies
uv sync

# Run linter
uv run ruff check .

# Run type checker
uv run mypy src/

# Run unit tests
uv run pytest

# Run integration tests (requires Docker)
uv run pytest -m integration tests/test_integration_bdi_loop.py
```

---

## OPA Policies

Rego policy bundles live in `policies/`:

| File | Package | Description |
|------|---------|-------------|
| `goals.rego` | `endogenai.goals` | Goal admission: conflict detection, capacity limits |
| `actions.rego` | `endogenai.actions` | Action dispatch: permitted channels, rate limits |
| `identity.rego` | `endogenai.identity` | Identity mutation: value-safety guard |

Policies are loaded into the standalone OPA server at startup.

---

## Shared Contracts

- Input/output types: `executive-goal.schema.json`, `policy-decision.schema.json`,
  `motor-feedback.schema.json` (all in `shared/schemas/`)
- Reward signals: `shared/types/reward-signal.schema.json`
- Vector store collection: `brain.executive-agent` (long-term, prefrontal layer)

---

## Module Contract

- ✅ Exposes `/.well-known/agent-card.json`
- ✅ A2A communication only via `endogenai-a2a` client
- ✅ Vector store access only via `endogenai-vector-store` adapter
- ✅ All LLM inference routed through LiteLLM
- ✅ OPA policy via standalone HTTP (localhost:8181) — not embedded
- ✅ Structured telemetry via `structlog`
