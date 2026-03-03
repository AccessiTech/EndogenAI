# Phase 6 — Detailed Implementation Workplan

> **Status**: ✅ RESEARCH COMPLETE — all open questions resolved (2026-03-02). Ready for implementation gating.  
> **Scope**: Group III: Executive & Output Modules — §§6.1–6.3  
> **Milestone**: M6 — End-to-End Decision-to-Action Pipeline Live (agent can receive a goal,
> deliberate, orchestrate, and produce a measurable environmental output with upward feedback)  
> **Prerequisite**: Phase 5 (Group II: Cognitive Processing) memory stack operational (§§5.1–5.4
> sufficient; §5.5 affective recommended; §5.6 reasoning stub acceptable).  
> **Research references**:
> - [phase-6-neuroscience-executive-output.md](phase-6-neuroscience-executive-output.md) (D1)
> - [phase-6-technologies-executive-output.md](phase-6-technologies-executive-output.md) (D2)
> - [phase-6-synthesis-workplan.md](phase-6-synthesis-workplan.md) (D3)

---

## Contents

1. [Pre-Implementation Checklist](#1-pre-implementation-checklist)
2. [Build Sequence and Gate Definitions](#2-build-sequence-and-gate-definitions)
3. [Directory Structure Overview](#3-directory-structure-overview)
4. [§6.1 — Executive / Agent Layer](#4-61--executive--agent-layer)
5. [§6.2 — Agent Execution (Runtime) Layer](#5-62--agent-execution-runtime-layer)
6. [§6.3 — Motor / Output / Effector Layer](#6-63--motor--output--effector-layer)
7. [Cross-Cutting: Shared Schemas](#7-cross-cutting-shared-schemas)
8. [Cross-Cutting: Temporal vs. Prefect Spike](#8-cross-cutting-temporal-vs-prefect-spike)
9. [Cross-Cutting: Docker Compose Services](#9-cross-cutting-docker-compose-services)
10. [Cross-Cutting: Architecture.md Post-Gate Updates](#10-cross-cutting-architecturemd-post-gate-updates)
11. [Phase 6 Completion Gate](#11-phase-6-completion-gate)
12. [Decisions Recorded](#12-decisions-recorded)

---

## 1. Pre-Implementation Checklist

All items below must be confirmed before any Phase 6 code is written.

### 1.1 Phase 5 Gate

```bash
# Minimum: §§5.1–5.4 memory modules operational
ls modules/group-ii-cognitive-processing/memory/{working-memory,short-term-memory,long-term-memory,episodic-memory}/{README.md,agent-card.json}
cd modules/group-ii-cognitive-processing/memory/working-memory && uv run pytest
cd modules/group-ii-cognitive-processing/memory/short-term-memory && uv run pytest

# Recommended: affective module operational (closes actor-critic loop from day 1)
ls modules/group-ii-cognitive-processing/affective/{README.md,agent-card.json}
cd modules/group-ii-cognitive-processing/affective && uv run pytest

# Stub acceptable: reasoning module assemble_context MCP tool available
# (agent-runtime can implement its own decomposition Activity as fallback if not ready)
```

If memory modules are not yet operational, raise with Phase 5 Executive before proceeding.

### 1.2 Shared Schema Pre-Landing (Schemas-First Gate)

The following schemas are **cross-module contracts** for Phase 6 and must be landed in
`shared/schemas/` before implementation of any Phase 6 module begins. Each schema must
pass `buf lint` and `scripts/schema/validate_all_schemas.py`.

| File | Purpose | Block for |
|---|---|---|
| `executive-goal.schema.json` | Goal item: id, description, priority, lifecycle_state, deadline, constraints | §6.1, §6.2 |
| `skill-pipeline.schema.json` | Ordered SkillStep list: tool_id, params, expected_output | §6.2, §6.3 |
| `action-spec.schema.json` | Single parameterised action: type, channel, params, idempotency_key | §6.2, §6.3 |
| `motor-feedback.schema.json` | Action outcome: action_id, predicted vs actual, deviation_score, reward_signal | §6.3, §6.1 |
| `policy-decision.schema.json` | OPA evaluation result: allow, violations[], explanation | §6.1 internal |

Land order: `executive-goal` → `policy-decision` → `skill-pipeline` → `action-spec` → `motor-feedback`.

### 1.3 Temporal vs. Prefect Spike

**The spike must complete before §6.2 implementation begins** (see §8 for full spike spec).
The default configuration is `primary: temporal, fallback: prefect`. The orchestrator choice
is **user-configurable** via `orchestrator.config.json` — any combination of `"temporal"`,
`"prefect"`, or `"none"` (disable a tier) is valid. See §5.3 for all configurable fields.
Record the spike result in `docs/research/temporal-prefect-spike.md` before opening the
§6.2 implementation PR.

### 1.4 OPA Deployment

**Resolved: Option B — standalone HTTP server.** OPA runs as a Docker Compose service at
`localhost:8181` (see §9). `policy.py` uses `httpx` to `POST` to the OPA REST API
(`/v1/data/{package}/{rule}`). Benefits: Decision Log, Prometheus metrics at `/metrics`,
hot-reload of Rego bundles without module restart. The loopback overhead is negligible
(sub-millisecond on the same host). Add the `opa` service to `docker-compose.yml` before
§6.1 implementation begins.

### 1.5 Collection Registry

Add the `brain.executive-agent` collection to
`shared/vector-store/collection-registry.json` before §6.1 implementation:

| Collection | Layer | memoryType | Notes |
|---|---|---|---|
| `brain.executive-agent` | prefrontal | long-term | Goals, values, policies, identity state; BDI plan templates |

Append the following object to the `"collections"` array in `shared/vector-store/collection-registry.json`
(after the `brain.reasoning` entry, maintaining brain-layer order):

```json
    {
      "name": "brain.executive-agent",
      "moduleId": "executive-agent",
      "layer": "prefrontal",
      "description": "Agent identity state, persistent goal records with lifecycle history, OPA policy evaluation cache, and BDI plan templates. Semantically indexed for plan retrieval during option-generation phase.",
      "memoryType": "long-term",
      "notes": "Append-only writes only — never overwrite existing items (reconsolidation analogue). Goal records must carry lifecycle_state and goal_id in metadata. BDI plan templates should include goal_class tag for similarity retrieval."
    }
```

Also bump `"updatedAt"` to the current date and increment `"version"` to `"0.2.0"`.

Verify after adding:

```bash
uv run python scripts/schema/validate_all_schemas.py
cd shared/vector-store/python && uv run python -c "
from endogenai_vector_store import VectorStoreAdapter
print([c['name'] for c in VectorStoreAdapter.list_collections()])
"
```

No collections are required for §6.2 or §6.3 — `agent-runtime` and `motor-output` do not
maintain their own vector stores; they route through `executive-agent` and upstream modules.

### 1.6 Docker Compose Services Required

```bash
docker compose config --services | grep -E "chromadb|ollama|temporal|opa"
```

Expected: `chromadb`, `ollama`. Additions required: `temporal` (or `prefect` per spike
result), `opa` (if Option B selected). See §9.

### 1.7 A2A Python SDK

The `a2a-sdk` package must be available in each Phase 6 sub-module's `uv` environment:

```bash
# Verify current version available
uv pip show a2a-sdk 2>/dev/null || echo "not installed"
# Install if missing (in each sub-module dir)
uv add a2a-sdk
```

### 1.8 Directory Scaffold

The `modules/group-iii-executive-output/` tree does not yet exist. Run the following
before any implementation begins (after Gate 0 schemas are landed):

```bash
# Create module root
mkdir -p modules/group-iii-executive-output

# executive-agent skeleton
mkdir -p modules/group-iii-executive-output/executive-agent/{src/executive_agent,tests,policies}
touch modules/group-iii-executive-output/executive-agent/src/executive_agent/{__init__.py,py.typed}
touch modules/group-iii-executive-output/executive-agent/tests/__init__.py

# agent-runtime skeleton
mkdir -p modules/group-iii-executive-output/agent-runtime/{src/agent_runtime,tests}
touch modules/group-iii-executive-output/agent-runtime/src/agent_runtime/{__init__.py,py.typed}
touch modules/group-iii-executive-output/agent-runtime/tests/__init__.py

# motor-output skeleton
mkdir -p modules/group-iii-executive-output/motor-output/{src/motor_output/channels,tests}
touch modules/group-iii-executive-output/motor-output/src/motor_output/{__init__.py,py.typed}
touch modules/group-iii-executive-output/motor-output/src/motor_output/channels/__init__.py
touch modules/group-iii-executive-output/motor-output/tests/__init__.py

# Verify
find modules/group-iii-executive-output -type d | sort
```

Each module's `pyproject.toml`, `agent-card.json`, config files, and source files are then
created per §§4–6. Do not run `uv sync` until each module's `pyproject.toml` is in place.

---

## 2. Build Sequence and Gate Definitions

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 6 Build Sequence                                         │
│                                                                 │
│  0. Land shared schemas (§1.2)                                  │
│  0. Run Temporal vs. Prefect spike (§8)                         │
│                                                                 │
│  ── GATE 0: schemas pass buf lint + spike decision recorded ──  │
│                                                                 │
│  1. §6.1 executive-agent   ←── BDI loop + OPA; no runtime dep  │
│                                                                 │
│  ── GATE 1: executive-agent passes tests + serves agent-card ─  │
│                                                                 │
│  2. §6.2 agent-runtime     ←── depends on executive-agent A2A  │
│                                                                 │
│  ── GATE 2: agent-runtime passes tests + serves agent-card ──  │
│                                                                 │
│  3. §6.3 motor-output      ←── depends on agent-runtime A2A    │
│                                                                 │
│  ── GATE 3: full pipeline integration test passes ─────────────│
└─────────────────────────────────────────────────────────────────┘
```

**Within each module**, follow this sub-sequence:
1. `pyproject.toml` + `uv sync` + `agent-card.json`
2. Core Pydantic models
3. Config files
4. Core logic (deliberation / orchestration / dispatch)
5. MCP interface
6. A2A interface
7. Unit tests (mocked dependencies)
8. Integration tests (Testcontainers)
9. `README.md`
10. Commit: `feat(<scope>): implement <module>`

**Gate 0 check** (run before any Phase 6 implementation):
```bash
cd shared && buf lint
uv run python scripts/schema/validate_all_schemas.py
cat docs/research/temporal-prefect-spike.md   # must exist and have a decision recorded
```

**Gate 1 check** (run before §6.2):
```bash
ls modules/group-iii-executive-output/executive-agent/{README.md,agent-card.json}
curl -sf http://localhost:8161/.well-known/agent-card.json | python -m json.tool
cd modules/group-iii-executive-output/executive-agent && uv run pytest
```

**Gate 2 check** (run before §6.3):
```bash
ls modules/group-iii-executive-output/agent-runtime/{README.md,agent-card.json}
curl -sf http://localhost:8162/.well-known/agent-card.json | python -m json.tool
cd modules/group-iii-executive-output/agent-runtime && uv run pytest
```

**Gate 3 check** (Phase 6 completion — see §11 for full spec).

---

## 3. Directory Structure Overview

```
modules/group-iii-executive-output/
├── executive-agent/
│   ├── README.md
│   ├── agent-card.json
│   ├── pyproject.toml
│   ├── pyrightconfig.json
│   ├── uv.lock
│   ├── identity.config.json
│   ├── vector-store.config.json
│   ├── embedding.config.json
│   ├── policies/
│   │   ├── identity.rego             (OPA: identity integrity + value constraints)
│   │   ├── goals.rego                (OPA: goal feasibility + conflict constraints)
│   │   └── actions.rego              (OPA: action permission + scope constraints)
│   ├── src/
│   │   └── executive_agent/
│   │       ├── __init__.py
│   │       ├── py.typed
│   │       ├── models.py             (GoalItem, SelfModel, PolicyDecision, BDIPlan)
│   │       ├── goal_stack.py         (priority queue + lifecycle management)
│   │       ├── deliberation.py       (BDI interpreter loop: option-gen → deliberate → commit)
│   │       ├── policy.py             (OPA client: evaluate_policy, load_bundles)
│   │       ├── identity.py           (self-model: load identity.config.json + vector store)
│   │       ├── feedback.py           (receive MotorFeedback → update goal score + emit RewardSignal)
│   │       ├── store.py              (brain.executive-agent via endogenai_vector_store)
│   │       ├── mcp_tools.py
│   │       └── a2a_handler.py
│   └── tests/
│       ├── __init__.py
│       ├── test_goal_stack.py
│       ├── test_deliberation.py
│       ├── test_policy.py
│       ├── test_identity.py
│       ├── test_feedback.py
│       └── test_integration_bdi_loop.py    (Testcontainers: ChromaDB + OPA)
├── agent-runtime/
│   ├── README.md
│   ├── agent-card.json
│   ├── pyproject.toml
│   ├── pyrightconfig.json
│   ├── uv.lock
│   ├── orchestrator.config.json
│   ├── tool-registry.config.json
│   ├── src/
│   │   └── agent_runtime/
│   │       ├── __init__.py
│   │       ├── py.typed
│   │       ├── models.py             (SkillStep, SkillPipeline, ExecutionStatus, SkillEntry)
│   │       ├── decomposer.py         (goal → SkillPipeline via LiteLLM Activity)
│   │       ├── tool_registry.py      (in-memory + config registry; A2A agent-card discovery)
│   │       ├── workflow.py           (Temporal IntentionWorkflow definition)
│   │       ├── activities.py         (Temporal Activity implementations: LLM, tool dispatch)
│   │       ├── worker.py             (Temporal Worker startup + queue registration)
│   │       ├── prefect_fallback.py   (Prefect @flow/@task circuit-breaker implementation)
│   │       ├── orchestrator.py       (primary/fallback selector; exposes unified interface)
│   │       ├── mcp_tools.py
│   │       └── a2a_handler.py
│   └── tests/
│       ├── __init__.py
│       ├── test_decomposer.py
│       ├── test_tool_registry.py
│       ├── test_workflow.py
│       ├── test_activities.py
│       ├── test_orchestrator.py
│       └── test_integration_intention_workflow.py  (Testcontainers: Temporal)
└── motor-output/
    ├── README.md
    ├── agent-card.json
    ├── pyproject.toml
    ├── pyrightconfig.json
    ├── uv.lock
    ├── channels.config.json
    ├── error-policy.config.json
    ├── src/
    │   └── motor_output/
    │       ├── __init__.py
    │       ├── py.typed
    │       ├── models.py             (ActionSpec, ActionReceipt, MotorFeedback, ChannelEntry)
    │       ├── channel_selector.py   (PMd analogue: choose correct interface/transport)
    │       ├── dispatcher.py         (M1 analogue: execute the action; corollary discharge)
    │       ├── channels/
    │       │   ├── __init__.py
    │       │   ├── http_channel.py   (httpx + retry)
    │       │   ├── a2a_channel.py    (A2A Python SDK dispatch)
    │       │   ├── file_channel.py   (pathlib writes)
    │       │   └── render_channel.py (LiteLLM text/media rendering)
    │       ├── error_policy.py       (three-tier: retry / circuit-breaker / escalate)
    │       ├── feedback.py           (spinocerebellum: observe outcome → MotorFeedback)
    │       ├── mcp_tools.py
    │       └── a2a_handler.py
    └── tests/
        ├── __init__.py
        ├── test_channel_selector.py
        ├── test_dispatcher.py
        ├── test_error_policy.py
        ├── test_feedback.py
        └── test_integration_dispatch_pipeline.py  (Testcontainers: mock HTTP server)
```

---

## 4. §6.1 — Executive / Agent Layer

### 4.1 Biological Basis

| Region | Mapping |
|---|---|
| DLPFC (BA 9/46) | Goal stack: active maintenance, capacity-constrained, priority-ordered |
| OFC (BA 11–14) | Value scoring: goal candidates scored against current `RewardSignal` |
| vmPFC (BA 10–12) | Fast heuristic pre-filter before full OPA deliberation |
| ACC (BA 24/32) | Policy violation detection: OPA `violations[]` set triggers escalation |
| BG direct pathway | Commit intention: push to `agent-runtime` execution queue (disinhibition) |
| BG indirect pathway | Suppress competing goals: only one intention per goal-class active |
| BG hyperdirect pathway | Abort: stop signal cancels full execution queue immediately |
| Dopamine RPE actor-critic | `MotorFeedback.reward_signal` updates goal priority weights |

Sources: [D1 §2](phase-6-neuroscience-executive-output.md), [D2 §2](phase-6-technologies-executive-output.md)

### 4.2 `agent-card.json`

```json
{
  "name": "executive-agent",
  "description": "Prefrontal executive layer. Maintains agent identity, manages a priority-ordered goal stack, and enforces policy constraints via OPA Rego rules. Runs a BDI interpreter loop: option generation → deliberation → intention commitment → feedback integration. Delegates committed intentions to agent-runtime for execution.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8061",
    "mcp": "http://localhost:8161"
  }
}
```

### 4.3 `identity.config.json`

```json
{
  "agentName": "brAIn",
  "agentVersion": "0.1.0",
  "coreValues": [
    "helpfulness",
    "honesty",
    "safety",
    "curiosity"
  ],
  "maxActiveGoals": 5,
  "reconsiderationThreshold": 0.6,
  "goalLifecycleStates": ["PENDING", "EVALUATING", "COMMITTED", "EXECUTING", "DEFERRED", "COMPLETED", "FAILED"],
  "persistenceStrategy": "bold",
  "workingMemoryModule": "http://localhost:8151"
}
```

**Lifecycle state transitions**:
```
PENDING → EVALUATING  (option-generator picks it up)
EVALUATING → COMMITTED (OPA allow; BDI deliberation selects it)
EVALUATING → PENDING   (OPA allow; not selected this cycle)
EVALUATING → FAILED    (OPA deny; unresolvable policy violation)
COMMITTED → EXECUTING  (pushed to agent-runtime execution queue)
EXECUTING → COMPLETED  (MotorFeedback: success)
EXECUTING → FAILED     (MotorFeedback: escalate=true)
EXECUTING → DEFERRED   (stop signal; BG hyperdirect abort)
DEFERRED → EVALUATING  (re-queued on next deliberation cycle)
```

### 4.4 `vector-store.config.json`

```json
{
  "backend": "chromadb",
  "collection": "brain.executive-agent",
  "host": "localhost",
  "port": 8000
}
```

### 4.5 `embedding.config.json`

```json
{
  "provider": "ollama",
  "model": "nomic-embed-text",
  "baseUrl": "http://localhost:11434",
  "dimensions": 768
}
```

### 4.6 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-executive-agent"
version = "0.1.0"
description = "Executive agent layer — BDI deliberation loop, goal stack, OPA policy engine, identity management."
requires-python = ">=3.11"

dependencies = [
  "endogenai-vector-store",       # shared adapter — local path dep
  "a2a-sdk>=0.3",                 # A2A Python SDK
  "httpx>=0.27",                  # OPA HTTP client (standalone mode)
  "pydantic>=2.7",
  "structlog>=24.1",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "testcontainers[chromadb]>=4.7",
  "respx>=0.21",                  # mock OPA HTTP responses
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 4.7 OPA Policy Files (`policies/`)

**`policies/identity.rego`**:
```rego
package endogenai.identity

default allow = false

# Allow if action is consistent with core values
allow {
    not violates_value
}

violates_value {
    input.action.type == "dispatch"
    input.action.channel == "external"
    not input.context.safety_check_passed
}

violations[msg] {
    violates_value
    msg := sprintf("Action '%v' failed safety check", [input.action.type])
}
```

**`policies/goals.rego`**:
```rego
package endogenai.goals

default allow = false

allow {
    not conflicting_goal_exists
    not exceeds_capacity
}

conflicting_goal_exists {
    some i
    data.active_goals[i].goal_class == input.candidate.goal_class
    data.active_goals[i].lifecycle_state == "EXECUTING"
}

exceeds_capacity {
    count(data.active_goals) >= data.config.maxActiveGoals
}

violations[msg] {
    conflicting_goal_exists
    msg := sprintf("Goal class '%v' already executing", [input.candidate.goal_class])
}

violations[msg] {
    exceeds_capacity
    msg := sprintf("Goal stack at capacity (%v)", [data.config.maxActiveGoals])
}
```

**`policies/actions.rego`**:
```rego
package endogenai.actions

default allow = false

allow {
    input.action.channel in data.permitted_channels
    not rate_limited
}

rate_limited {
    data.channel_calls[input.action.channel] >= data.rate_limits[input.action.channel]
}

violations[msg] {
    not input.action.channel in data.permitted_channels
    msg := sprintf("Channel '%v' not in permitted list", [input.action.channel])
}
```

### 4.8 Core Implementation Notes

**`goal_stack.py`** — priority queue + lifecycle:
- Backed by a `list[GoalItem]` sorted by `priority` (float, 0-1) descending.
- `push(goal)`: validate schema; set state `PENDING`; append to stack; re-sort.
- `pop_for_evaluation(n)`: return top-`n` goals in `PENDING` state for the deliberation loop.
- `commit(goal_id)`: transition `EVALUATING → COMMITTED`; call `agent-runtime` A2A `execute_intention`.
- `abort(goal_id, reason)`: transition any state → `DEFERRED` or `FAILED`; send Temporal Signal "abort".
- `update_score(goal_id, reward_delta)`: adjust `priority` by `reward_delta`; re-sort stack.
- `enforce_capacity()`: if `len(COMMITTED + EXECUTING) >= maxActiveGoals`, defer lowest-priority
  `PENDING` goal.

**`deliberation.py`** — BDI interpreter loop:
```
Loop (runs every deliberation_cycle_ms, configurable):
  1. option_generation:
     - Pop top maxActiveGoals PENDING goals
     - For each: assemble context via working_memory MCP call
     - Score each against current RewardSignal (value_score from OFC analogue)

  2. deliberation:
     - For each candidate (sorted by value_score desc):
       - Call policy.evaluate_policy(action=candidate, context)
       - If PolicyDecision.allow: add to intentions list
       - If PolicyDecision.deny: log violations; leave in PENDING or transition to FAILED

  3. commit_intentions:
     - For each approved intention:
       - Transition EVALUATING → COMMITTED
       - Push to agent-runtime via A2A execute_intention task

  4. integrate_feedback:
     - Process any queued MotorFeedback messages
     - Update goal scores; emit RewardSignal to affective module

  5. reconsideration_check:
     - If any EXECUTING goal has feedback deviation_score > reconsiderationThreshold:
       - Re-evaluate: send Signal("revise") to Temporal Workflow
```

**`policy.py`** — OPA HTTP client:
- `evaluate_policy(package, rule, input_data) → PolicyDecision`:
  - `POST http://localhost:8181/v1/data/{package}/{rule}` with `{"input": input_data}`
  - Parse JSON response into `PolicyDecision(allow, violations, explanation)`
  - Cache allow decisions for identical inputs within the same deliberation cycle (LRU, max 100)
- `load_bundle(bundle_path)`: `PUT` bundle to OPA; used at startup and on policy hot-reload.
- `health_check()`: `GET http://localhost:8181/health`; raises if OPA unreachable.

**`identity.py`** — self-model:
- Load `identity.config.json` at startup.
- `get_self_model() → SelfModel`: return current identity state including `coreValues`,
  `agentName`, and recently achieved goals (from `brain.executive-agent` semantic retrieval).
- `update_self_model(delta)`: write delta to `brain.executive-agent` collection as a new item
  with `type="executive"`; never overwrite — append only (reconsolidation analogue).

**`feedback.py`** — MotorFeedback handler:
- `receive_feedback(feedback: MotorFeedback)`:
  1. Update goal lifecycle state (EXECUTING → COMPLETED or FAILED)
  2. `goal_stack.update_score(feedback.goal_id, feedback.reward_signal.value)`
  3. Emit `RewardSignal` to affective module A2A `emit_reward` task (closes actor-critic loop)
  4. If `feedback.escalate`: log `goal.failed` event; notify upstream via A2A if wired

### 4.9 MCP Tools

| Tool | Signature | Description |
|---|---|---|
| `executive_agent.push_goal` | `(description: str, priority: float, deadline?: str, constraints?: dict) → GoalItem` | Add a goal to the stack |
| `executive_agent.get_goal_stack` | `(filter?: dict) → list[GoalItem]` | Return ranked active goals |
| `executive_agent.evaluate_policy` | `(action: dict, context: dict) → PolicyDecision` | Run OPA evaluation; return allow + violations |
| `executive_agent.update_identity` | `(delta: dict) → SelfModel` | Append identity delta to self-model |
| `executive_agent.abort_goal` | `(goal_id: str, reason: str) → GoalItem` | Transition goal to DEFERRED/FAILED; cancel Workflow |
| `executive_agent.get_drive_state` | `() → DriveState` | Return current drive variable state from affective module |

### 4.10 A2A Task Handlers

| Task type | Input | Output | Notes |
|---|---|---|---|
| `commit_intention` | `{goal_id, context_payload}` | `GoalItem` with `workflow_id` | Pushes to agent-runtime |
| `receive_feedback` | `{motor_feedback: MotorFeedback}` | `{goal_id, new_state, reward_signal}` | Closes actor-critic loop |
| `abort_goal` | `{goal_id, reason}` | `GoalItem` with state=DEFERRED | BG hyperdirect analogue |
| `get_identity` | `{}` | `SelfModel` | Used by agent-runtime for context |

---

## 5. §6.2 — Agent Execution (Runtime) Layer

### 5.1 Biological Basis

| Region | Mapping |
|---|---|
| Cerebrocerebellum | Task decomposition + skill pipeline execution; inverse model (goal → pipeline) |
| Cerebellar forward model | Pre-stage tool parameters before execute signal (Bereitschaftspotential) |
| Marr-Albus climbing fibre | Execution error signal → `skill_feedback` log for Phase 7 skill refinement |
| pre-SMA | Decomposition phase separate from execution phase; sequence switching |
| Bereitschaftspotential | Pre-fetch dependencies; prepare Activity inputs during decomposition |
| BG cognitive loop (caudate) | Goal priority updates from executive-agent received in-flight via Temporal Signal |

Sources: [D1 §3](phase-6-neuroscience-executive-output.md), [D2 §3](phase-6-technologies-executive-output.md)

### 5.2 `agent-card.json`

```json
{
  "name": "agent-runtime",
  "description": "Motor planning and task execution layer. Decomposes committed intentions into ordered skill pipelines, selects and registers tools via A2A agent-card discovery, and orchestrates durable execution via Temporal (primary) or Prefect (fallback). Pre-stages tool parameters before execution begins.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8062",
    "mcp": "http://localhost:8162"
  }
}
```

### 5.3 `orchestrator.config.json`

```json
{
  "primary": "temporal",
  "fallback": "prefect",
  "temporalServerUrl": "localhost:7233",
  "temporalNamespace": "endogenai",
  "temporalTaskQueue": "brain-runtime",
  "prefectApiUrl": "http://localhost:4200",
  "workflowIdStrategy": "goal_id_with_attempt",
  "fallbackTrigger": {
    "strategy": "circuit-breaker",
    "maxTemporalConnectRetries": 3,
    "fallbackCooldownSeconds": 60
  }
}
```

**Configurable fields:**

| Field | Valid values | Notes |
|---|---|---|
| `primary` | `"temporal"`, `"prefect"`, `"none"` | `"none"` disables execution (dry-run / test mode) |
| `fallback` | `"temporal"`, `"prefect"`, `"none"` | `"none"` disables fallback (fail hard if primary down) |
| `workflowIdStrategy` | `"goal_id_with_attempt"`, `"goal_id"` | `"goal_id_with_attempt"` produces `"{goal_id}-{n}"` IDs (retry-safe, **recommended**); `"goal_id"` uses UUID directly (simpler but breaks on retry) |
| `fallbackTrigger.strategy` | `"circuit-breaker"`, `"immediate"` | `"immediate"` switches to fallback on first Temporal error, no retry |

**`workflowIdStrategy` detail**: `"goal_id_with_attempt"` generates Temporal Workflow IDs of
the form `"3f8a1d2e-...-001"` (UUID padded attempt suffix), making cross-system log
correlation trivial while safely supporting goal retry without ID collision. The attempt
counter is stored in the `GoalItem.workflow_id` field as `"{goal_id}-{n}"`.

### 5.4 `tool-registry.config.json`

```json
{
  "discoveryStrategy": "well-known-uri",
  "discoveryTargets": [
    "http://localhost:8061",
    "http://localhost:8063",
    "http://localhost:8151",
    "http://localhost:8152",
    "http://localhost:8153",
    "http://localhost:8154"
  ],
  "healthCheckIntervalSeconds": 30,
  "registryPersistencePath": ".tool-registry.json"
}
```

### 5.5 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-agent-runtime"
version = "0.1.0"
description = "Agent runtime layer — durable task orchestration via Temporal/Prefect, skill pipeline decomposition, tool registry."
requires-python = ">=3.11"

dependencies = [
  "a2a-sdk>=0.3",
  "temporalio>=1.7",              # Temporal Python SDK
  "litellm>=1.40",                # LLM routing (decomposition Activities)
  "prefect>=3.0",                 # Prefect fallback
  "httpx>=0.27",
  "pydantic>=2.7",
  "structlog>=24.1",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "temporalio[testing]>=1.7",     # Temporal test env
  "testcontainers>=4.7",
  "respx>=0.21",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 5.6 Core Implementation Notes

**`workflow.py`** — Temporal `IntentionWorkflow`:

```python
"""
workflow.py — Temporal IntentionWorkflow

DETERMINISM RULE: No I/O, no LLM calls, no timestamps inside Workflow logic.
All non-deterministic operations are delegated to Activities.
"""
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class IntentionWorkflow:
    def __init__(self) -> None:
        self._abort_requested = False
        self._revision: dict | None = None

    @workflow.run
    async def run(self, goal_id: str, context_payload: dict) -> dict:
        # Phase 1: Decomposition (pre-SMA analogue — plan before execute)
        pipeline = await workflow.execute_activity(
            "decompose_goal",
            args=[goal_id, context_payload],
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Execute each SkillStep as an Activity
        results = []
        for step in pipeline["steps"]:
            if self._abort_requested:
                return {"status": "aborted", "goal_id": goal_id}

            if self._revision:
                pipeline = self._revision
                self._revision = None

            result = await workflow.execute_activity(
                "dispatch_to_motor_output",
                args=[step, goal_id],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy={"maximum_attempts": 3},
            )
            results.append(result)

            # Partial feedback after each step if deviation significant
            if result.get("deviation_score", 0) > 0.5:
                await workflow.execute_activity(
                    "emit_partial_feedback",
                    args=[goal_id, result],
                    start_to_close_timeout=timedelta(seconds=10),
                )

        return {"status": "completed", "goal_id": goal_id, "results": results}

    @workflow.signal
    def abort(self) -> None:
        self._abort_requested = True

    @workflow.update
    def revise_plan(self, revised_pipeline: dict) -> str:
        self._revision = revised_pipeline
        return f"revision_accepted:{workflow.info().workflow_id}"

    @workflow.query
    def get_status(self) -> dict:
        return {
            "abort_requested": self._abort_requested,
            "has_pending_revision": self._revision is not None,
        }
```

**`activities.py`** — Temporal Activities (non-determinism boundary):
- `decompose_goal(goal_id, context_payload) → SkillPipeline`:
  - Call `working_memory.assemble_context` MCP tool for context
  - **Phase 5 stub (confirmed)**: Phase 5 reasoning module is confirmed not yet operational.
    Call LiteLLM directly (`litellm.completion`) to decompose into a `SkillPipeline` JSON
    structure. Do NOT attempt to call Phase 5 reasoning A2A or MCP endpoints.
    When Phase 5 reasoning becomes available, swap the LiteLLM call for a delegation to
    `reasoning.decompose_goal` MCP tool, keeping LiteLLM as fallback.
  - Validate pipeline against tool registry (skip unavailable tools)
  - Return `SkillPipeline` (JSON-serialisable Pydantic model)

- `dispatch_to_motor_output(step: SkillStep, goal_id: str) → dict`:
  - Build `ActionSpec` from `SkillStep`
  - Call `motor_output` A2A `dispatch_action` task
  - Return `MotorFeedback` dict

- `emit_partial_feedback(goal_id, result) → None`:
  - Call `executive_agent` A2A `receive_feedback` with partial `MotorFeedback`

**`tool_registry.py`** — discovery + health:
- On startup: for each URL in `discoveryTargets`, fetch `/.well-known/agent-card.json`.
- Parse `AgentCard.skills` → register each as a `SkillEntry`.
- Periodic health check: ping each registered skill's `a2a` endpoint; mark unavailable skills.
- `get_skills_for_goal(goal_description: str) → list[SkillEntry]`:
  - Embed `goal_description`; cosine-rank registered skill descriptions.
  - Filter to health-checked available skills.

**`prefect_fallback.py`** — circuit-breaker implementation:
```python
from prefect import flow, task
from prefect.states import Failed

@task(retries=3, retry_delay_seconds=10, name="execute-skill-step")
async def execute_skill_step(step: dict, goal_id: str) -> dict:
    """Prefect task: single skill step execution."""
    # Same logic as Temporal dispatch_to_motor_output Activity
    ...

@flow(name="intention-workflow")
async def intention_flow(goal_id: str, context_payload: dict) -> dict:
    """Prefect fallback flow — mirrors IntentionWorkflow logic."""
    pipeline = await decompose_goal_task(goal_id, context_payload)
    results = []
    for step in pipeline["steps"]:
        result = await execute_skill_step(step, goal_id)
        results.append(result)
    return {"status": "completed", "goal_id": goal_id, "results": results}
```

**`orchestrator.py`** — unified interface:
- `execute_intention(goal_id, context_payload)`:
  1. Compute Workflow ID using `workflowIdStrategy`:
     - `"goal_id_with_attempt"` (default, **recommended**): `f"{goal_id}-{attempt_number:03d}"`
       (e.g. `"{uuid}-001"`). Retry-safe; stores generated ID on `GoalItem.workflow_id`.
     - `"goal_id"`: use UUID directly (simpler; breaks on retry — avoid in production).
  2. If `primary != "none"`: attempt primary orchestrator via
     `temporal_client.start_workflow(IntentionWorkflow, id=workflow_id, ...)`
  3. On `ConnectError` after `maxTemporalConnectRetries` retries:
     - If `fallback != "none"`: log warning; execute via fallback orchestrator.
     - If `fallback == "none"`: raise `OrchestrationError`.
  4. Return `{"workflow_id": ..., "orchestrator": "temporal" | "prefect"}`

### 5.7 MCP Tools

| Tool | Signature | Description |
|---|---|---|
| `agent_runtime.decompose` | `(goal_id: str, context_payload: dict) → SkillPipeline` | Decompose goal into skill pipeline (does not execute) |
| `agent_runtime.get_execution_status` | `(goal_id: str) → ExecutionStatus` | Query Temporal Workflow or Prefect flow state |
| `agent_runtime.register_tool` | `(skill_id: str, config: dict) → SkillEntry` | Manually register a tool |
| `agent_runtime.list_tools` | `(capability_filter?: str) → list[SkillEntry]` | List available tools; optionally filter by capability |
| `agent_runtime.abort_execution` | `(goal_id: str) → str` | Send Temporal Signal("abort") to running Workflow |

### 5.8 A2A Task Handlers

| Task type | Input | Output | Notes |
|---|---|---|---|
| `execute_intention` | `{goal_id, skill_pipeline}` | `{workflow_id, orchestrator}` | Starts Temporal Workflow (or Prefect fallback) |
| `abort_execution` | `{goal_id}` | `{status: "aborted"}` | Sends Temporal Signal("abort") |
| `revise_plan` | `{goal_id, revised_pipeline}` | `{status: "revision_accepted"}` | Sends Temporal Update("revise_plan") |
| `get_status` | `{goal_id}` | `ExecutionStatus` | Temporal Query("get_status") |

---

## 6. §6.3 — Motor / Output / Effector Layer

### 6.1 Biological Basis

| Region | Mapping |
|---|---|
| M1 (BA 4): population coding | Action dispatcher: parallel dispatch; distributed handler routing |
| PMd: context-dependent channel selection | `channel_selector.py`: choose API/transport based on `ActionSpec.channel` + context |
| PMv (F5): corollary discharge | Before executing, emit predicted `ActionSpec` back to `agent-runtime` (pre-action signal) |
| SMA proper: parallel sequences | Concurrent dispatch of multiple `ActionSpec` items in the same pipeline step |
| OFC principle: minimal correction | Three-tier error policy: local retry → circuit-breaker → escalate |
| Dynamical systems: pre-configured trajectory | `ActionPipeline` fully built by `agent-runtime` before `motor-output` begins |
| Spinocerebellum: real-time correction | `feedback.py`: observe actual outcome → emit `MotorFeedback` after every dispatch |

Sources: [D1 §4](phase-6-neuroscience-executive-output.md), [D2 §4](phase-6-technologies-executive-output.md)

### 6.2 `agent-card.json`

```json
{
  "name": "motor-output",
  "description": "Motor cortex and effector layer. Dispatches parameterised actions to external APIs, A2A agents, file systems, and rendered output channels. Implements a three-tier error policy (retry / circuit-breaker / escalate) and emits structured MotorFeedback to the executive-agent after every dispatch.",
  "version": "0.1.0",
  "capabilities": ["mcp-context", "a2a-task"],
  "endpoints": {
    "a2a": "http://localhost:8063",
    "mcp": "http://localhost:8163"
  }
}
```

### 6.3 `channels.config.json`

```json
{
  "permitted": ["http", "a2a", "file", "render", "control-signal"],
  "http": {
    "defaultTimeoutSeconds": 30,
    "maxRetries": 3,
    "backoffMultiplier": 2.0
  },
  "a2a": {
    "defaultTimeoutSeconds": 60
  },
  "file": {
    "basePath": "/tmp/endogenai-output",
    "createDirs": true
  },
  "render": {
    "liteLLMModel": "ollama/llama3.2",
    "liteLLMApiBase": "http://localhost:11434"
  }
}
```

### 6.4 `error-policy.config.json`

```json
{
  "tier1": {
    "name": "transient-retry",
    "conditions": ["ConnectionError", "TimeoutError", "HTTPStatusError_5xx"],
    "maxRetries": 3,
    "backoffBaseSeconds": 1.0
  },
  "tier2": {
    "name": "circuit-breaker",
    "conditions": ["HTTPStatusError_429", "ServiceUnavailable"],
    "openThreshold": 5,
    "halfOpenAfterSeconds": 30,
    "fallbackBehaviour": "log_and_skip"
  },
  "tier3": {
    "name": "escalate",
    "conditions": ["HTTPStatusError_401", "HTTPStatusError_403", "ChannelNotFound", "SchemaValidationError"],
    "escalateTo": "executive-agent",
    "escalateVia": "a2a"
  }
}
```

### 6.5 `pyproject.toml` Dependencies

```toml
[project]
name = "endogenai-motor-output"
version = "0.1.0"
description = "Motor output layer — action dispatch, channel selection, three-tier error policy, MotorFeedback emission."
requires-python = ">=3.11"

dependencies = [
  "a2a-sdk>=0.3",
  "httpx>=0.27",                  # HTTP channel
  "litellm>=1.40",                # render channel
  "pydantic>=2.7",
  "structlog>=24.1",
]

[dependency-groups]
dev = [
  "pytest>=8.2",
  "pytest-asyncio>=0.23",
  "respx>=0.21",                  # mock HTTP responses
  "testcontainers>=4.7",
  "ruff>=0.4",
  "mypy>=1.10",
]
```

### 6.6 Core Implementation Notes

**`models.py`** — key types:
```python
from pydantic import BaseModel, Field
from typing import Literal
from uuid import uuid4

class ActionSpec(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    goal_id: str
    workflow_id: str
    type: Literal["http", "a2a", "file", "render", "control-signal"]
    channel: str            # destination URL / path / agent endpoint
    params: dict            # channel-specific parameters
    idempotency_key: str    # for safe retries; default = action_id
    predicted_outcome: dict | None = None   # corollary discharge payload

class MotorFeedback(BaseModel):
    action_id: str
    goal_id: str
    workflow_id: str
    dispatched_at: str      # ISO-8601
    completed_at: str       # ISO-8601
    channel: str
    predicted_outcome: dict | None
    actual_outcome: dict
    deviation_score: float = 0.0    # 0.0 = perfect match
    error_tier: Literal["tier1", "tier2", "tier3"] | None = None
    escalate: bool = False
    reward_signal: dict     # RewardSignal-compatible dict
```

**`dispatcher.py`** — M1 analogue:
- `dispatch(action_spec: ActionSpec) → MotorFeedback`:
  1. **Corollary discharge**: if `action_spec.predicted_outcome` is set, emit a
     `pre_action_event` log entry (same schema as `MotorFeedback` but `type="predicted"`)
  2. Select channel handler via `channel_selector.py`
  3. Execute via channel (wrapped in `error_policy.py` tier evaluation)
  4. Compute `deviation_score`: if `predicted_outcome` was set, cosine-compare serialised
     predicted vs. actual; otherwise 0.0
  5. Build and return `MotorFeedback`

- `dispatch_concurrent(specs: list[ActionSpec]) → list[MotorFeedback]`:
  - `asyncio.gather(*[dispatch(s) for s in specs])` — bimanual coordination analogue

**`error_policy.py`** — three-tier policy:
```python
async def execute_with_policy(fn, action_spec: ActionSpec, config: dict):
    """
    Tier 1: transient errors → retry with exponential backoff
    Tier 2: circuit-open → log + skip (return degraded MotorFeedback)
    Tier 3: fatal/permission errors → build escalation MotorFeedback (escalate=True)
    """
    for attempt in range(config["tier1"]["maxRetries"]):
        try:
            return await fn(action_spec)
        except TIER1_EXCEPTIONS as e:
            if attempt == config["tier1"]["maxRetries"] - 1:
                raise
            await asyncio.sleep(config["tier1"]["backoffBaseSeconds"] * (2 ** attempt))
        except TIER2_EXCEPTIONS:
            # Circuit breaker: open → return degraded result
            return _degraded_feedback(action_spec, tier="tier2")
        except TIER3_EXCEPTIONS as e:
            # Fatal: build escalation feedback
            return _escalation_feedback(action_spec, error=str(e), tier="tier3")
```

**`feedback.py`** — spinocerebellar upward loop:
- After every `dispatch()`, call `executive_agent` A2A `receive_feedback` task with the
  `MotorFeedback` payload.
- For `escalate=True` feedbacks, call immediately and synchronously (blocking).
- For normal completions, call asynchronously (fire-and-forget acceptable).
- Attach `reward_signal = {"value": 1.0 if not escalate else -0.5, "source": "motor-output",
  "task_id": action_id}` to every `MotorFeedback`.

### 6.7 MCP Tools

| Tool | Signature | Description |
|---|---|---|
| `motor_output.dispatch` | `(action_spec: ActionSpec) → ActionReceipt` | Dispatch a single action; returns receipt with `action_id` |
| `motor_output.dispatch_pipeline` | `(specs: list[ActionSpec]) → list[ActionReceipt]` | Concurrent batch dispatch |
| `motor_output.get_action_status` | `(action_id: str) → MotorFeedback | None` | Retrieve feedback for a completed action |
| `motor_output.cancel_action` | `(action_id: str) → str` | Cancel an in-flight action (if channel supports it) |
| `motor_output.register_channel` | `(config: ChannelEntry) → str` | Dynamically register a new output channel |

### 6.8 A2A Task Handlers

| Task type | Input | Output | Notes |
|---|---|---|---|
| `dispatch_action` | `{action_spec: ActionSpec}` | `MotorFeedback` artifact | Called by `agent-runtime` Activities |
| `dispatch_pipeline` | `{specs: list[ActionSpec]}` | `list[MotorFeedback]` | Concurrent batch |
| `get_feedback` | `{action_id}` | `MotorFeedback | null` | Retrieve historical feedback |

---

## 7. Cross-Cutting: Shared Schemas

Land these in `shared/schemas/` in this order before Phase 6 implementation begins.
Each must pass `cd shared && buf lint` and `uv run python scripts/schema/validate_all_schemas.py`.

### 7.1 `executive-goal.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "executive-goal.schema.json",
  "title": "ExecutiveGoal",
  "type": "object",
  "required": ["id", "description", "priority", "lifecycle_state", "created_at"],
  "properties": {
    "id":              { "type": "string", "format": "uuid" },
    "description":     { "type": "string", "minLength": 1 },
    "goal_class":      { "type": "string" },
    "priority":        { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "value_score":     { "type": "number", "minimum": -1.0, "maximum": 1.0 },
    "lifecycle_state": { "type": "string", "enum": ["PENDING","EVALUATING","COMMITTED","EXECUTING","DEFERRED","COMPLETED","FAILED"] },
    "deadline":        { "type": ["string", "null"], "format": "date-time" },
    "constraints":     { "type": "object" },
    "workflow_id":     { "type": ["string", "null"] },
    "created_at":      { "type": "string", "format": "date-time" },
    "updated_at":      { "type": "string", "format": "date-time" }
  }
}
```

### 7.2 `action-spec.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "action-spec.schema.json",
  "title": "ActionSpec",
  "type": "object",
  "required": ["action_id", "goal_id", "workflow_id", "type", "channel", "params", "idempotency_key"],
  "properties": {
    "action_id":          { "type": "string", "format": "uuid" },
    "goal_id":            { "type": "string", "format": "uuid" },
    "workflow_id":        { "type": "string" },
    "type":               { "type": "string", "enum": ["http", "a2a", "file", "render", "control-signal"] },
    "channel":            { "type": "string" },
    "params":             { "type": "object" },
    "idempotency_key":    { "type": "string" },
    "predicted_outcome":  { "type": ["object", "null"] }
  }
}
```

### 7.3 `motor-feedback.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "motor-feedback.schema.json",
  "title": "MotorFeedback",
  "type": "object",
  "required": ["action_id", "goal_id", "workflow_id", "dispatched_at", "completed_at", "channel", "actual_outcome", "reward_signal"],
  "properties": {
    "action_id":          { "type": "string", "format": "uuid" },
    "goal_id":            { "type": "string", "format": "uuid" },
    "workflow_id":        { "type": "string" },
    "dispatched_at":      { "type": "string", "format": "date-time" },
    "completed_at":       { "type": "string", "format": "date-time" },
    "channel":            { "type": "string" },
    "predicted_outcome":  { "type": ["object", "null"] },
    "actual_outcome":     { "type": "object" },
    "deviation_score":    { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "error_tier":         { "type": ["string", "null"], "enum": ["tier1", "tier2", "tier3", null] },
    "escalate":           { "type": "boolean" },
    "reward_signal":      { "$ref": "../types/reward-signal.schema.json" }
  }
}
```

### 7.4 `skill-pipeline.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "skill-pipeline.schema.json",
  "title": "SkillPipeline",
  "type": "object",
  "required": ["pipeline_id", "goal_id", "steps"],
  "properties": {
    "pipeline_id":   { "type": "string", "format": "uuid" },
    "goal_id":       { "type": "string", "format": "uuid" },
    "workflow_id":   { "type": ["string", "null"] },
    "name":          { "type": "string" },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["step_id", "tool_id", "params"],
        "properties": {
          "step_id":         { "type": "string" },
          "tool_id":         { "type": "string" },
          "skill_name":      { "type": "string" },
          "params":          { "type": "object" },
          "expected_output": { "type": ["object", "null"] },
          "depends_on":      { "type": "array", "items": { "type": "string" } },
          "can_run_parallel": { "type": "boolean", "default": false }
        }
      }
    },
    "created_at":    { "type": "string", "format": "date-time" }
  }
}
```

### 7.5 `policy-decision.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "policy-decision.schema.json",
  "title": "PolicyDecision",
  "type": "object",
  "required": ["allow", "violations", "package", "rule", "evaluated_at"],
  "properties": {
    "allow":        { "type": "boolean" },
    "violations":   {
      "type": "array",
      "items": { "type": "string" }
    },
    "explanation":  { "type": ["string", "null"] },
    "package":      { "type": "string", "description": "OPA package path e.g. endogenai.goals" },
    "rule":         { "type": "string", "description": "OPA rule evaluated e.g. allow" },
    "evaluated_at": { "type": "string", "format": "date-time" },
    "cached":       { "type": "boolean", "default": false }
  }
}
```

---

## 8. Cross-Cutting: Temporal vs. Prefect Spike

This spike must be completed and its result committed to `docs/research/temporal-prefect-spike.md`
before `agent-runtime` implementation begins.

### 8.1 Spike Scope

Build a minimal Temporal Workflow and Prefect flow that both:
1. Execute a 3-step pipeline with one simulated LLM call (mocked LiteLLM)
2. Survive a simulated Worker crash mid-execution
3. Resume from the crash point and complete successfully

### 8.2 Pass/Fail Criteria

| Criterion | Temporal | Prefect |
|---|---|---|
| Deterministic replay after crash | Must replay from exact crash point with no data loss | Acceptable if last completed task is not re-executed |
| Startup time (cold `docker compose up`) | Pass if < 30 seconds to first Worker poll | N/A (no server required) |
| LLM Activity idempotency | Pass if replayed LLM call uses cached result from Event History | Pass if `@task` result is checkpointed |
| Local dev experience | Pass if `docker compose up temporal` is a single command | N/A |

**Decision rule**: Temporal is primary if it passes all four criteria. Prefect is primary only if
Temporal fails cold-start ≤ 30 second criterion AND Prefect passes replay criterion.

### 8.3 Spike Output

Create `docs/research/temporal-prefect-spike.md` with:
- Decision: `primary: temporal | prefect`
- Evidence: crash-recovery test output
- Any limitations discovered

### 8.4 Post-Spike Configuration

After the spike, update `orchestrator.config.json` to reflect the chosen primary. The
default shipped config is `primary: temporal, fallback: prefect`. If the spike shows
Temporal fails the cold-start criterion, change to `primary: prefect, fallback: none`.

For local development without a Temporal server running, the config can be temporarily
set to `primary: prefect, fallback: none` without changing any source code — this is the
value of the configurable approach. Revert to `primary: temporal` before running
integration tests.

Valid runtime modes enabled by `orchestrator.config.json`:

| `primary` | `fallback` | Runtime behaviour |
|---|---|---|
| `temporal` | `prefect` | **Default.** Temporal with Prefect circuit-breaker |
| `temporal` | `none` | Temporal only; hard-fail if server down |
| `prefect` | `none` | Prefect only; no Temporal server required |
| `temporal` | `temporal` | Invalid (same orchestrator twice; raises `ConfigError`) |
| `none` | `none` | Dry-run / test mode; records intent but does not execute |

---

## 9. Cross-Cutting: Docker Compose Services

The following services must be added to or verified in `docker-compose.yml`.
Services already present from Phase 1/2 are marked ✅.

| Service | Image | Port(s) | Required by | Status |
|---|---|---|---|---|
| `chromadb` | `chromadb/chroma:latest` | 8000 | `executive-agent` (brain.executive-agent) | ✅ existing |
| `ollama` | `ollama/ollama:latest` | 11434 | All embedding calls | ✅ existing |
| `temporal` | `temporalio/auto-setup:latest` | 7233 (gRPC), 8233 (UI) | `agent-runtime` | ➕ add |
| `temporal-ui` | included in `auto-setup` | 8233 | developer visibility | ➕ add |
| `opa` | `openpolicyagent/opa:latest` | 8181 | `executive-agent` policy engine | ➕ add |

Minimal additions for `docker-compose.yml`:

```yaml
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
      - "8233:8233"
    environment:
      - DB=sqlite

  opa:
    image: openpolicyagent/opa:latest
    command: ["run", "--server", "--addr=0.0.0.0:8181"]
    ports:
      - "8181:8181"
    volumes:
      - ./modules/group-iii-executive-output/executive-agent/policies:/policies:ro
```

Verify the full local stack comes up cleanly after adding these services:

```bash
docker compose up -d
docker compose ps            # all services should show "running" or "healthy"

# Temporal: first Worker poll within 30 seconds (spike criterion)
docker compose logs temporal | grep -i "poll" | head -3

# OPA: server ready
curl -sf http://localhost:8181/health | python -m json.tool

# ChromaDB + Ollama: previously passing — confirm still healthy
curl -sf http://localhost:8000/api/v1/heartbeat
curl -sf http://localhost:11434/api/tags | python -m json.tool
```

---

## 10. Cross-Cutting: Architecture.md Post-Gate Updates

The following additions to `docs/architecture.md` are deferred until **after Gate 3 passes**
(all three modules live and integration test green). They are documented here so the
implementing agent knows exactly what to update, and the Review Agent can gate the PR on
them being present.

> **Constraint**: Do not edit `docs/architecture.md` before Gate 3. The table stub currently
> reads _"will be added as subsequent phases deliver live modules"_ — this is intentional and
> correct until implementation is complete.

### 10.1 Group III Row in Module Table

Add three rows to the Group III section of the module architecture table:

| Module | Path | Ports (A2A / MCP) | Dependencies |
|---|---|---|---|
| `executive-agent` | `modules/group-iii-executive-output/executive-agent/` | 8061 / 8161 | ChromaDB (`brain.executive-agent`), OPA (`localhost:8181`), working-memory (MCP 8151) |
| `agent-runtime` | `modules/group-iii-executive-output/agent-runtime/` | 8062 / 8162 | Temporal (`localhost:7233`), LiteLLM, executive-agent (A2A 8061) |
| `motor-output` | `modules/group-iii-executive-output/motor-output/` | 8063 / 8163 | executive-agent (A2A 8061), httpx, A2A SDK, LiteLLM (render channel) |

### 10.2 Signal-Flow Diagram Extension

Add an Executive Output column to the existing signal-flow diagram (after the Cognitive
Processing column). The addition should show:

```
[executive-agent]  →  goal committed  →  [agent-runtime]
       ↑                                        ↓
  MotorFeedback                          ActionSpec dispatched
       ↑                                        ↓
       └──────────── [motor-output] ────────────┘
                     (channel dispatch)
```

### 10.3 Technology Stack Table

Add the following rows to the Technology Stack section of `docs/architecture.md`:

| Component | Technology | Used by |
|---|---|---|
| Durable workflow orchestration | Temporal (`temporalio/auto-setup:latest`) | `agent-runtime` |
| Circuit-breaker fallback | Prefect 3.x | `agent-runtime` (fallback path) |
| Policy engine | Open Policy Agent (OPA) | `executive-agent` |
| BDI deliberation | Custom Python (`deliberation.py`) | `executive-agent` |

### 10.4 Neuroanatomy Cross-Reference

Update the neuroanatomy cross-reference section (if present) to note that the following
stubs now have Phase 6 module mappings:
- `resources/neuroanatomy/frontal-lobe.md` → `executive-agent`
- `resources/neuroanatomy/prefrontal-cortex.md` → `executive-agent` (Phase 6) + `reasoning` (Phase 5)
- `resources/neuroanatomy/cerebellum.md` → `agent-runtime` + `motor-output`
- `resources/neuroanatomy/motor-cortex.md` → `motor-output` _(new stub)_
- `resources/neuroanatomy/basal-ganglia.md` → `executive-agent` _(new stub)_
- `resources/neuroanatomy/supplementary-motor-area.md` → `agent-runtime` _(new stub)_

---

## 11. Phase 6 Completion Gate

Run all of the following before declaring Phase 6 complete:

```bash
# 1. All three modules have required files
ls modules/group-iii-executive-output/{executive-agent,agent-runtime,motor-output}/{README.md,agent-card.json,pyproject.toml}

# 2. All agent-cards are served and valid
curl -sf http://localhost:8161/.well-known/agent-card.json | python -m json.tool
curl -sf http://localhost:8162/.well-known/agent-card.json | python -m json.tool
curl -sf http://localhost:8163/.well-known/agent-card.json | python -m json.tool

# 3. Unit tests pass for all three modules
cd modules/group-iii-executive-output/executive-agent && uv run pytest
cd modules/group-iii-executive-output/agent-runtime && uv run pytest
cd modules/group-iii-executive-output/motor-output && uv run pytest

# 4. Linting and type-checking pass
cd modules/group-iii-executive-output/executive-agent && uv run ruff check . && uv run mypy src/
cd modules/group-iii-executive-output/agent-runtime && uv run ruff check . && uv run mypy src/
cd modules/group-iii-executive-output/motor-output && uv run ruff check . && uv run mypy src/

# 5. Shared schemas pass validation
cd shared && buf lint
uv run python scripts/schema/validate_all_schemas.py

# 6. End-to-end integration test: goal → pipeline → dispatch → feedback
# This test sends a GoalItem to executive-agent A2A and asserts:
#   - Temporal Workflow is created and transitions to COMPLETED
#   - motor-output dispatches at least one ActionSpec
#   - MotorFeedback is received by executive-agent
#   - goal transitions to COMPLETED lifecycle state
uv run pytest modules/group-iii-executive-output/ -k "test_integration_full_pipeline"

# 7. pnpm root checks pass
pnpm run lint && pnpm run typecheck
```

**Milestone M6 success criteria** (from `docs/Workplan.md`):
> End-to-end decision-to-action pipeline verified; agent can receive a goal, reason about it,
> and produce a measurable environmental output.

---

## 12. Decisions Recorded

All open questions from the research phase have been resolved by the owner (2026-03-02).
No further approvals are required before implementation begins, subject to Gate 0 passing.

| # | Question | Decision | Implications |
|---|---|---|---|
| 1 | OPA deployment model | **Option B — standalone HTTP** (`localhost:8181`) | Add `opa` service to `docker-compose.yml` (§9); `policy.py` uses `httpx`; Decision Log and hot-reload enabled |
| 2 | BDI plan library storage | **Option B — `brain.executive-agent` ChromaDB** | `identity.py` writes plan templates to the vector store at goal completion; `deliberation.py` retrieves closest plan by semantic similarity during option generation; no `plans/` JSON files |
| 3 | Temporal vs. Prefect spike | **Spike by default; orchestrator is user-configurable** | Default: `primary: temporal, fallback: prefect`; configurable to any combination via `orchestrator.config.json` (see §5.3); spike result recorded in `docs/research/temporal-prefect-spike.md` |
| 4 | Temporal Workflow ID strategy | **`goal_id_with_attempt`** (`"{goal_id}-{n}"`) | Zero-padded attempt suffix (e.g. `"{uuid}-001"`); retry-safe; stored on `GoalItem.workflow_id`; correlation trivial in logs |
| 5 | `MotorFeedback` delivery | **Active push** | `motor-output/feedback.py` calls `executive-agent` A2A `receive_feedback` after every dispatch; blocking for `escalate=True`, fire-and-forget with 3-retry backoff for normal completions |
| 6 | Phase 5 reasoning stub | **Local LiteLLM fallback in `agent-runtime`** | Phase 5 reasoning module confirmed not yet operational; `decompose_goal` Activity calls LiteLLM directly (see §5.6); do NOT call Phase 5 A2A/MCP endpoints; replace when Phase 5 reasoning becomes available |

## Copilot Review

PR #21 was reviewed by GitHub Copilot (review `3879547061`, 2026-03-02). Copilot flagged
15 concerns across 99 of 109 changed files (10 visible in the review UI + 5 initially
hidden). All 15 are genuine implementation bugs — none should be dismissed. Each is
categorised below with the required remediation.

---

### Concerns to Address

#### 1. Dockerfile COPY paths are outside the build context

**File**: `modules/group-iii-executive-output/executive-agent/Dockerfile` (lines 11–13)

**Issue**: `COPY ../../../shared/vector-store/python` and
`COPY ../../../shared/a2a/python` use paths relative to the Dockerfile, but
`docker-compose.yml` sets the build context to the repo root. Docker COPY paths must be
relative to the build context, so these paths will be rejected at build time.

**Fix**: Change both COPY lines to be relative to the repo root:
```dockerfile
COPY shared/vector-store/python /shared/vector-store/python
COPY shared/a2a/python /shared/a2a/python
```
Apply the same correction to the equivalent Dockerfiles in `agent-runtime/` and
`motor-output/` if present.

---

#### 2. `FileChannel` initialised with empty `allowed_base_paths`

**File**: `modules/group-iii-executive-output/motor-output/src/motor_output/dispatcher.py`
(lines 50–55)

**Issue**: The `Dispatcher` passes `allowed_file_paths or []` to `FileChannel`. When
`allowed_file_paths` is `None` (the common default), the channel receives an empty list and
`_is_allowed()` always returns `False`, silently disabling all file writes.

**Fix**: Pass `None` directly (or omit the argument) so `FileChannel` falls back to its
own `_ALLOWED_BASE_PATHS` default:
```python
ChannelType.FILE: FileChannel(allowed_base_paths=allowed_file_paths),
```

---

#### 3. `_is_allowed()` vulnerable to path-prefix trick

**File**: `modules/group-iii-executive-output/motor-output/src/motor_output/channels/file_channel.py`
(lines 28–33)

**Issue**: The allowed-path guard uses `str(resolved).startswith(str(allowed_base))`.
A path like `/tmp-not-allowed/evil` would pass an `/tmp` base check because the string
prefix matches. This is a path-traversal security issue.

**Fix**: Use `Path.relative_to()` (raises `ValueError` if the target is outside the base)
or `os.path.commonpath()`:
```python
def _is_allowed(self, target: Path) -> bool:
    resolved = target.resolve()
    for base in self._allowed_base_paths:
        try:
            resolved.relative_to(base.resolve())
            return True
        except ValueError:
            continue
    return False
```

---

#### 4. OPA policy cache described as LRU but implemented as unbounded dict

**File**: `modules/group-iii-executive-output/executive-agent/src/executive_agent/policy.py`
(lines 53–57)

**Issue**: The docstring says "LRU, max 100" but the cache is a plain `dict`. Once it
reaches 100 entries it stops caching new decisions (but never evicts old ones), so
long-running processes silently degrade to no caching without error.

**Fix**: Use `functools.lru_cache`, `cachetools.LRUCache`, or a manual `collections.OrderedDict`
eviction, and update the docstring to match whichever approach is chosen.

---

#### 5. `docker-compose.yml` env var names don't match what `motor-output/server.py` reads

**File**: `docker-compose.yml` (lines 380–381)

**Issue**: The `motor-output` service is given `EXECUTIVE_AGENT_A2A_URL` and
`AGENT_RUNTIME_A2A_URL`, but `server.py` reads `EXECUTIVE_AGENT_URL` and
`AGENT_RUNTIME_URL`. The configured container-DNS URLs are ignored; the server falls back
to `localhost` defaults and cannot reach co-located services.

**Fix** (accept Copilot's suggested change):
```yaml
- EXECUTIVE_AGENT_URL=http://executive-agent:8161
- AGENT_RUNTIME_URL=http://agent-runtime:8162
```
Alternatively, update `server.py` to read the `*_A2A_URL` names — pick one convention and
apply it consistently across all three modules.

---

#### 6. `workflow.py` returns `status="completed"` when aborted during plan revision

**File**: `modules/group-iii-executive-output/agent-runtime/src/agent_runtime/workflow.py`
(lines 72–85)

**Issue**: When an abort signal arrives while the inner revision loop is running, the loop
breaks but execution falls through to `return {"status": "completed", ...}`. The caller
receives a false success signal for an aborted workflow.

**Fix**: Check `self._abort_requested` after the revision loop and return an aborted result:
```python
if self._abort_requested:
    return {"status": "aborted", "goal_id": goal_id, "results": results}
```
This check should also be present at the top of the main loop for consistency.

---

#### 7. `tool_registry.py` reads capabilities from the wrong JSON field

**File**: `modules/group-iii-executive-output/agent-runtime/src/agent_runtime/tool_registry.py`
(lines 93–96)

**Issue**: `SkillEntry.capabilities` is populated from the agent-card top-level
`"capabilities"` field instead of the per-skill `"capabilities"` field. All skills
registered from the same agent-card inherit identical capability lists, breaking
capability-based filtering and losing skill-specific metadata.

**Fix** (accept Copilot's suggested change):
```python
capabilities=skill_data.get("capabilities", []),
```

---

#### 8. `policy.py` "Fail open" comment contradicts fail-closed behaviour

**File**: `modules/group-iii-executive-output/executive-agent/src/executive_agent/policy.py`

**Issue**: The comment inside the OPA exception handler says something to the effect of
"fail open" but the implementation returns `allow=False` on OPA communication errors
(fail-closed). This misalignment will mislead reviewers and future maintainers; it is also
a potential security decision that should be explicit.

**Fix**: Decide on the intended behaviour and align code and comment:
- **Fail-closed** (recommended for safety): remove the "fail open" comment; document
  that OPA unavailability blocks goal execution.
- **Fail-open** (if desired): set `allow=True` on communication errors and document the
  risk explicitly with a `# nosec` or equivalent annotation.

---

#### 9. `load_bundle()` calls the wrong OPA endpoint and uses the wrong content-type

**File**: `modules/group-iii-executive-output/executive-agent/src/executive_agent/policy.py`
(lines 121–130)

**Issue**: `load_bundle()` sends a `PUT` to `/v1/policies/endogenai` with
`Content-Type: application/x-tar` and claims to upload a `.tar.gz` bundle. The OPA
`/v1/policies/{id}` endpoint expects raw Rego source text (`text/plain`); bundles are
configured via the OPA server's `bundle` plugin (not a runtime HTTP push). Using the wrong
endpoint with the wrong content-type will result in a silent failure or an OPA parse error.

**Fix** — choose one:
- **Single Rego policy**: send `PUT /v1/policies/endogenai` with the `.rego` file contents
  as `text/plain`.
- **Bundle (preferred for production)**: remove `load_bundle()` entirely; configure OPA's
  `--bundle /policies` flag (already wired via the `docker-compose.yml` volume mount) so
  OPA loads Rego files at startup without a runtime push call.

The `docker-compose.yml` already mounts `./modules/group-iii-executive-output/executive-agent/policies`
at `/policies` with the `--bundle /policies` flag pattern — use that and remove the HTTP
bundle upload machinery.

---

#### 10. `error-policy.config.json` key names don't match what `server.py` reads

**File**: `modules/group-iii-executive-output/motor-output/src/motor_output/server.py`
(lines 56–60)

**Issue**: `error-policy.config.json` uses top-level keys `"tier1"`, `"tier2"`, `"tier3"`
(as specified in §6.4 of this workplan), but `server.py` reads with `raw.get("retry", {})`
and `raw.get("circuitBreaker", {})`. The configured retry and circuit-breaker settings are
silently ignored and defaults are always used.

**Fix**: Update `server.py` to read the tier-based structure that matches the config file:
```python
error_policy_config = {
    "tier1": raw.get("tier1", {}),
    "tier2": raw.get("tier2", {}),
    "tier3": raw.get("tier3", {}),
}
```
The `error-policy.config.json` schema in §6.4 of this workplan is the source of truth —
do not change the config file format.

---

#### 11. `docker-compose.yml` — agent-runtime env var names don't match server.py

**File**: `docker-compose.yml` (lines 361–362)

**Issue**: The `agent-runtime` service is given `EXECUTIVE_AGENT_A2A_URL` and
`MOTOR_OUTPUT_A2A_URL`, but `agent_runtime/server.py` reads `EXECUTIVE_AGENT_URL` and
`MOTOR_OUTPUT_URL`. The container-DNS URLs for both peers are ignored; the server defaults
to `localhost` and cannot reach either service inside the Docker network.

**Fix**: Rename to match the server:
```yaml
- EXECUTIVE_AGENT_URL=http://executive-agent:8161
- MOTOR_OUTPUT_URL=http://motor-output:8163
```

---

#### 12. `feedback.py` — `goal_id` silently defaults to empty string

**File**: `modules/group-iii-executive-output/motor-output/src/motor_output/feedback.py`
(line ~88)

**Issue**: `build_feedback()` uses `action_spec.goal_id or ""`. An empty `goal_id` in
`MotorFeedback` violates the `motor-feedback.schema.json` `format: uuid` constraint,
will cause a `KeyError` (or silent miss) in executive-agent's goal FSM lookup, and
breaks log correlation. The schema requires goal_id to be present.

**Fix**: Raise `ValueError` when `goal_id` is absent, so the failure surfaces at call
site rather than propagating as malformed feedback:
```python
if not action_spec.goal_id:
    raise ValueError("ActionSpec.goal_id is required to build MotorFeedback — cannot dispatch without a goal context.")
```

---

#### 13. `mcp_tools.py` — `"nullable": True` is not valid JSON Schema draft-07

**File**: `modules/group-iii-executive-output/motor-output/src/motor_output/mcp_tools.py`
(line 36)

**Issue**: `"nullable"` is an OpenAPI 3.0 extension, not a JSON Schema draft-07 keyword.
MCP clients (and `buf lint` / schema validators) that strictly parse draft-07 will reject
the schema or silently ignore the nullability intent.

**Fix**: Express nullability via a union type array:
```python
"channel": {"type": ["string", "null"]},
```

---

#### 14. `docker-compose.yml` — `TEMPORAL_URL` env var is set but never consumed

**File**: `docker-compose.yml` (line 359) and
`modules/group-iii-executive-output/agent-runtime/src/agent_runtime/server.py`

**Issue**: The agent-runtime service declares `TEMPORAL_URL=temporal:7233` as an env var,
but `server.py` never reads it. `OrchestratorConfig.temporal_server_url` is populated
only from the static `orchestrator.config.json` file (default `localhost:7233`). Inside
the Docker network the Temporal server hostname is `temporal`, not `localhost`, so the
worker will fail to connect even though the env var is correctly set.

**Fix**: In `server.py`, after loading `OrchestratorConfig` from the config file, apply
an env-var override for `temporal_server_url`:
```python
temporal_url_override = os.getenv("TEMPORAL_URL")
if temporal_url_override:
    config.temporal_server_url = temporal_url_override
```

---

#### 15. `motor-output/Dockerfile` — shared path-dependency packages never copied

**File**: `modules/group-iii-executive-output/motor-output/Dockerfile` (line 10)

**Issue**: `pyproject.toml` declares `endogenai-vector-store` and `endogenai-a2a` as local
path dependencies (`path = "../../../shared/..."`, editable). The Dockerfile only copies
`pyproject.toml` and `src/` — the shared packages are never present in the image, so
`uv sync` will fail with a dependency resolution error at build time.

**Fix**: Add COPY instructions for the shared packages before `uv sync`, using
build-context-relative paths (build context = repo root):
```dockerfile
COPY shared/vector-store/python /shared/vector-store/python
COPY shared/a2a/python /shared/a2a/python
```

---

### Summary

| # | File | Severity | Action |
|---|------|----------|--------|
| 1 | `executive-agent/Dockerfile` | High — blocks Docker build | Fix COPY paths to be relative to repo root build context |
| 2 | `motor-output/dispatcher.py` | High — disables file channel | Pass `None` to `FileChannel` instead of empty list |
| 3 | `motor-output/channels/file_channel.py` | High — security (path traversal) | Replace `startswith()` with `Path.relative_to()` |
| 4 | `executive-agent/policy.py` (cache) | Medium — silent perf degradation | Use `OrderedDict` or `lru_cache` for actual LRU eviction |
| 5 | `docker-compose.yml` env vars (motor-output) | High — motor-output cannot reach peers | Rename to `EXECUTIVE_AGENT_URL` / `AGENT_RUNTIME_URL` |
| 6 | `agent-runtime/workflow.py` | High — false success on abort | Return `status="aborted"` when `_abort_requested` after revision loop |
| 7 | `agent-runtime/tool_registry.py` | Medium — broken capability filtering | Read `skill_data.get("capabilities", [])` not top-level card field |
| 8 | `executive-agent/policy.py` (comment) | Medium — misleading comment / security ambiguity | Align comment with fail-closed behaviour |
| 9 | `executive-agent/policy.py` (bundle) | High — OPA bundle upload broken | Use startup bundle mount or fix endpoint + content-type |
| 10 | `motor-output/server.py` | High — error policy config ignored | Read `tier1`/`tier2`/`tier3` keys matching config schema |
| 11 | `docker-compose.yml` env vars (agent-runtime) | High — agent-runtime cannot reach peers | Rename to `EXECUTIVE_AGENT_URL` / `MOTOR_OUTPUT_URL` |
| 12 | `motor-output/feedback.py` | High — malformed feedback / schema violation | Raise `ValueError` when `goal_id` is absent |
| 13 | `motor-output/mcp_tools.py` | Medium — invalid JSON Schema draft-07 | Replace `"nullable": True` with `"type": ["string", "null"]` |
| 14 | `docker-compose.yml` + `agent-runtime/server.py` | High — Temporal unreachable in Docker | Wire `TEMPORAL_URL` env override into orchestrator config loading |
| 15 | `motor-output/Dockerfile` | High — Docker build fails (uv sync) | COPY shared packages before `uv sync` |

All 15 concerns are genuine bugs. None should be ignored. Items 1, 2, 3, 5, 6, 9, 10, 11, 12, 14, 15 are
blockers for a functioning stack; items 4, 7, 8, 13 are correctness/quality issues that should be
resolved in the same pass before merge.

---

### Resolutions (2026-03-02)

All 10 issues were addressed in 6 sequential commits on `feature/phase-6-executive`
immediately following the review. The changes are ready for re-review.

| # | Commit | Resolution |
|---|--------|------------|
| 1 | `b28a7ec` | `executive-agent/Dockerfile`: COPY paths changed to repo-root-relative (`shared/vector-store/python`, `shared/a2a/python`) |
| 4 | `5ff507a` | `policy.py`: `_cache` type changed to `collections.OrderedDict`; `move_to_end()` on hit; oldest entry evicted (`popitem(last=False)`) when at capacity |
| 8 | `5ff507a` | `policy.py`: "Fail open" comment corrected to "Fail-closed" with explicit rationale — OPA unavailability blocks goal execution by design |
| 9 | `5ff507a` + `e4c3420` | `policy.py`: `load_bundle()` deprecated (no-op + warning); `load_policy()` added — PUTs a single `.rego` file as `text/plain` to `/v1/policies/{id}`. `docker-compose.yml`: OPA service augmented with `--bundle /policies` flag and a read-only volume mount of `executive-agent/policies/` so all Rego files load at startup without any HTTP push |
| 6 | `523c610` | `workflow.py`: `_abort_requested` check added after the revision inner loop; returns `{"status": "aborted", ...}` before the outer `break` |
| 7 | `e6db417` | `tool_registry.py`: `SkillEntry.capabilities` now reads `skill_data.get("capabilities", [])` (per-skill field) instead of `card.get("capabilities", [])` (agent-card root field) |
| 2 | `905853e` | `dispatcher.py`: `allowed_file_paths or []` replaced with `allowed_file_paths` (passes `None` through so `FileChannel` uses `_ALLOWED_BASE_PATHS`) |
| 3 | `905853e` | `file_channel.py`: `_is_allowed()` rewritten using `Path.relative_to()` (raises `ValueError` outside base) replacing `str.startswith()` prefix check |
| 10 | `8cbb49b` | `server.py`: `raw.get("retry", {})` corrected to `raw.get("retryPolicy", {})` to match `error-policy.config.json` top-level key |
| 5 | `e4c3420` | `docker-compose.yml` motor-output service: `EXECUTIVE_AGENT_A2A_URL` renamed to `EXECUTIVE_AGENT_URL`; unused `AGENT_RUNTIME_A2A_URL` removed |

Issues 11–15 (5 hidden comment threads) were subsequently identified and resolved:

| # | Commit | Resolution |
|---|--------|------------|
| 11 | `fdf74bb` | `docker-compose.yml` agent-runtime service: `EXECUTIVE_AGENT_A2A_URL` → `EXECUTIVE_AGENT_URL`, `MOTOR_OUTPUT_A2A_URL` → `MOTOR_OUTPUT_URL` |
| 12 | `fc39e36` | `feedback.py`: `action_spec.goal_id or ""` replaced with a `ValueError` guard — missing `goal_id` surfaces immediately at call site |
| 13 | `fc39e36` | `mcp_tools.py`: `"nullable": True` (OpenAPI extension) replaced with `"type": ["string", "null"]` (valid JSON Schema draft-07 union) |
| 14 | `6ea5ef3` | `server.py`: `TEMPORAL_URL` env var override applied to `OrchestratorConfig.temporal_server_url` after config file load |
| 15 | `824887b` | `motor-output/Dockerfile`: `COPY shared/vector-store/python` and `COPY shared/a2a/python` added before `uv sync` |

