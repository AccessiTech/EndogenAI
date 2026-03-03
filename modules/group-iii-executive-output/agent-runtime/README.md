# agent-runtime

**EndogenAI Group III — Agent Execution (Runtime) Module**

Neuroanatomical analogue: **Cerebellum** — decomposes high-level intentions into
choreographed, error-corrected skill pipelines and orchestrates their execution
via deterministic workflows.

---

## Purpose

`agent-runtime` receives committed intentions from `executive-agent`, decomposes them
into ordered `SkillPipeline` sequences, and orchestrates dispatch to `motor-output`
via Temporal Workflows (primary) or Prefect (fallback). Partial feedback is emitted
back to `executive-agent` after each step, completing the corollary-discharge loop.

---

## Interface

### A2A (JSON-RPC 2.0) — `http://localhost:8162/tasks`

| `method` | Payload | Returns |
|---|---|---|
| `execute_intention` | `{goal_id, context_payload?}` | `{workflow_id, orchestrator}` |
| `abort_execution` | `{goal_id}` | `{status, goal_id}` |
| `revise_plan` | `{goal_id, revised_pipeline}` | `{status, ack?}` |
| `get_status` | `{goal_id}` | `ExecutionStatus` |

### MCP Tool Calls — `POST /mcp/tools/call`

| `name` | Parameters |
|---|---|
| `agent_runtime.execute_intention` | `goal_id`, `context_payload?` |
| `agent_runtime.decompose` | `goal_id`, `context_payload?` |
| `agent_runtime.get_execution_status` | `goal_id` |
| `agent_runtime.abort_execution` | `goal_id` |
| `agent_runtime.list_tools` | `capability_filter?` |
| `agent_runtime.register_tool` | `SkillEntry` fields |

### Agent Card — `GET /.well-known/agent-card.json`

### Health — `GET /health`

---

## Configuration

| File | Purpose |
|---|---|
| `orchestrator.config.json` | Temporal/Prefect routing, circuit-breaker tuning |
| `tool-registry.config.json` | Discovery targets, health-check interval |

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `AR_PORT` | `8162` | HTTP listen port |
| `MOTOR_OUTPUT_URL` | `http://localhost:8163` | motor-output A2A endpoint |
| `EXECUTIVE_AGENT_URL` | `http://localhost:8161` | executive-agent A2A endpoint |
| `ORCHESTRATOR_CONFIG` | `orchestrator.config.json` | Config file path |
| `TOOL_REGISTRY_CONFIG` | `tool-registry.config.json` | Registry config path |

---

## Orchestration layers

```
execute_intention(goal_id, ctx)
        │
        ▼
  _build_workflow_id(goal_id)           → "{goal_id}-{attempt:03d}"
        │
        ├─ Temporal available? ──YES──► IntentionWorkflow.run(goal_id, ctx)
        │                                  │  decompose_goal (Activity)
        │                                  │  dispatch_to_motor_output (Activity) × N
        │                                  └  emit_partial_feedback (Activity) × N
        │
        └─ Temporal unavailable ──────► run_intention_flow (Prefect @flow)
                                            └─ Prefect also unavailable?
                                                └─ _run_sequential() (plain asyncio)
```

---

## Neuroscience basis

The cerebellum receives a copy of the motor command (efference copy / corollary
discharge) and compares predicted vs. actual outcomes to build internal models
that improve future predictions. `agent-runtime` mirrors this:

- `decomposer.py` — cerebellar-cortex forward model: given an intention, predict a
  sequence of micro-actions.
- `workflow.py` — granule/Purkinje cell timing: deterministic step ordering with
  retry policy.
- `activities.py` — climbing-fibre error signal: emit partial feedback after each
  step so `executive-agent` can update its world model.
- `tool_registry.py` — mossy-fibre contextual input: maintain a live map of
  available effectors.

---

## Development

```bash
# Install dependencies
cd modules/group-iii-executive-output/agent-runtime
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run mypy src/

# Start server (requires Temporal + motor-output running)
uv run serve
```

---

## Dependencies

- `temporalio>=1.7` — primary workflow orchestration
- `prefect>=3.0` — fallback orchestration
- `litellm>=1.40` — LLM-based goal decomposition (routes via Ollama by default)
- `endogenai-vector-store` — shared ChromaDB adapter
- `endogenai-a2a` — outbound A2A client
