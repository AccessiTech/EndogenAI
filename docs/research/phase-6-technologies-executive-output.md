# Phase 6 — Technologies for Executive & Output Systems

_Generated: 2026-03-02 by Docs Executive Researcher_  
_Sources: `docs/research/sources/phase-6/tech-*.md` (fetched 2026-03-02)_

> **Audience**: Phase 6 implementation agents and the Phase 6 Synthesis Workplan.  
> **Purpose**: Map upstream technology documentation onto the three Phase 6 sub-modules:
> `executive-agent` (identity, goal stack, policy engine), `agent-runtime` (task orchestration,
> skill pipelines), and `motor-output` (action dispatch, feedback, agent discovery).

---

## 1. Technology Stack Map

| Sub-module | Technologies | Role |
|---|---|---|
| `executive-agent` | BDI model, OPA (Open Policy Agent), Intelligent Agent theory | Identity/self-model, goal deliberation, policy constraint evaluation |
| `agent-runtime` | Temporal (primary), Prefect (fallback) | Durable task orchestration, skill pipeline execution, tool registry |
| `motor-output` | A2A protocol (`a2a-protocol.org` v0.3.0), A2A Python SDK | Action dispatch, agent card publication, agent discovery |

---

## 2. `executive-agent` — BDI Model, OPA & Agent Theory

### 2.1 BDI (Belief–Desire–Intention) Software Model

**Source**: `tech-bdi-model.md` (Wikipedia: Belief–desire–intention software model)

The BDI model (Bratman 1987; Rao & Georgeff 1991) provides the canonical architecture for practical
reasoning agents. The three core mental attitudes:

| Attitude | Description | `executive-agent` mapping |
|---|---|---|
| **Beliefs** | The agent's representation of the world; may be incomplete or incorrect | `identity.self-model` + current context assembled by working memory (Phase 5) |
| **Desires** | All objectives the agent would like to achieve; may be contradictory | Full goal backlog: all candidate goals regardless of current feasibility |
| **Intentions** | Committed plans: a filtered, consistent subset of desires currently being pursued | Active goal stack: goals that have passed deliberation and policy gating |

The critical distinction between Desires and Intentions is that **intentions constrain future practical
reasoning** — once committed, the agent should not abandon an intention without cause (persistence principle).
This maps to the goal lifecycle: a goal in the `COMMITTED` state must not be silently dropped; it must
be explicitly `DEFERRED`, `FAILED`, or `COMPLETED`.

#### BDI Interpreter Loop

```
initialise-state
LOOP:
  options   = option-generator(beliefs, desires, intentions)
  intentions = deliberate(options, intentions)           # which desires become intentions
  execute(intentions)                                    # advance current plan
  get-new-external-events()                              # update beliefs from environment
  drop-unsuccessful(intentions)                          # clean up failed plans
  drop-impossible(intentions)                            # clean up infeasible desires
END LOOP
```

This loop maps directly to the `executive-agent` run loop:
1. `option-generator` → scan goal backlog, score against current belief state and reward signal
2. `deliberate` → pass candidates through OPA policy engine; select winner(s) for commitment
3. `execute` → push committed intentions to `agent-runtime` execution queue
4. `get-new-external-events` → receive `MotorFeedback` signals and upstream context updates
5. `drop-unsuccessful / drop-impossible` → lifecycle management on the goal stack

#### Key BDI Properties for Implementation

- **Goal consistency**: the BDI model enforces that no two committed intentions are contradictory.
  The `executive-agent` must check for conflicts before committing a new goal to the stack.
- **Reconsideration strategy**: the agent must decide when to reconsider current intentions vs.
  persist with them. Two poles: **bold agent** (never reconsider while executing) vs.
  **cautious agent** (reconsider at every cycle). The system should implement a configurable
  `reconsideration_threshold` — triggering reconsideration only when `MotorFeedback` deviation_score
  exceeds a threshold.
- **Practical reasoning vs. theoretical reasoning**: BDI is about what to *do*, not what to *believe*.
  The executive agent focuses on action selection, not on building a world model — the world model
  is maintained by Phase 5 memory modules.
- **Hierarchical task decomposition**: plan libraries in BDI contain both high-level plans (which
  decompose into sub-plans) and primitive actions. High-level plans route to `agent-runtime` for
  further decomposition; primitive actions route directly to `motor-output`.

### 2.2 OPA — Open Policy Agent

**Source**: `tech-opa.md` (openpolicyagent.org/docs/latest)

OPA is a general-purpose, domain-agnostic policy engine that decouples policy decisions from policy
enforcement. It evaluates **Rego policy rules** against query-time `input` data and static `data` documents.

#### Rego Language Patterns

| Pattern | Syntax | `executive-agent` use case |
|---|---|---|
| Complete rule | `allow { condition_a; condition_b }` | Binary allow/deny for a candidate intention |
| Partial rule (set) | `violations[msg] { condition }` | Collect all active policy violations for a proposed action |
| Logical OR | Multiple rule heads with same name | Any one of several conditions can trigger a violation |
| Default fallback | `default allow = false` | Fail-closed: deny unless explicitly permitted |
| Arbitrary JSON output | `decision := { "allow": allow, "violations": violations }` | Return structured explanation, not just boolean |

#### OPA HTTP Server Integration

```
POST http://localhost:8181/v1/data/<package>/<rule>
Content-Type: application/json

{ "input": { "action": "...", "context": {...}, "agent_identity": {...} } }
```

Returns arbitrary JSON — the `executive-agent` should query for a `policy_decision` document that
includes both the boolean decision and a violations list (`violations[]`) for logging and explanation.

#### Policy Architecture for `executive-agent`

Three tiers of policy evaluation:

1. **Identity constraints** (`package identity`): rules that enforce consistency with the agent's
   self-model — prohibit actions that contradict the agent's stated values or identity
2. **Goal constraints** (`package goals`): rules that check candidate goals for feasibility,
   priority conflicts, and resource availability
3. **Action constraints** (`package actions`): rules that gate individual tool calls — permissions,
   rate limits, scope boundaries

OPA's **Bundle API** allows policies to be distributed and hot-reloaded without restarting the
`executive-agent`, enabling runtime policy updates.

OPA's **Decision Log** provides a full audit trail of every policy evaluation — essential for
observability and post-hoc analysis of why a goal was accepted or rejected.

### 2.3 Intelligent Agent Theory (Russell & Norvig)

**Source**: `tech-intelligent-agent.md` (Wikipedia: Intelligent agent)

Russell and Norvig define five agent types along a capability axis:

| Type | Description | Limitation |
|---|---|---|
| Simple reflex | Acts on current percept only | No memory; cannot handle partial observability |
| Model-based reflex | Maintains internal state | No goals; cannot plan |
| Goal-based | Acts to achieve stated goals | No preference ordering between equally achievable goals |
| **Utility-based** | Maximises expected utility (value-weighted goals) | **← `executive-agent` type** |
| Learning | Improves performance over time | Requires Phase 7 adaptive layer |

The `executive-agent` is a **utility-based agent**: it selects actions that maximise a utility function
defined over goal achievement and value alignment. The utility function is operationalised through the
BDI deliberation + OPA policy architecture.

#### Layered Architecture

Effective agent architectures separate reactive from deliberative processing:

| Layer | Speed | `executive-agent` mapping |
|---|---|---|
| Reactive | Fast; stimulus → response | Goal interrupt handling; hyperdirect-equivalent abort |
| Deliberative | Slow; planning and reasoning | BDI interpreter loop; OPA evaluation |
| Meta-cognitive | Reflective | Phase 7 (out of scope for Phase 6) |

The deliberative layer must not block reactive processing — interrupt signals (stop, abort, priority
escalation) must pre-empt the deliberation loop immediately.

---

## 3. `agent-runtime` — Temporal & Prefect

### 3.1 Temporal — Durable Workflow Orchestration

**Sources**: `tech-temporal-workflows.md`, `tech-temporal-activities.md`, `tech-temporal-message-passing.md`

Temporal provides durable, fault-tolerant workflow execution via automatic replay from an **Event
History** stored by the Temporal Server.

#### Workflows

A Temporal Workflow is a **durable function** that persists its state as an append-only Event History:

- **Definition** (code) → **Type** (registered name) → **Execution** (running instance)
- Executions survive process restarts, network partitions, and server failures via deterministic replay
- Workflows can run for **years** — appropriate for long-horizon agent goals
- Workflow code must be **deterministic** (same inputs → same Event History replay); non-deterministic
  operations (API calls, LLM inference, timestamps) must be wrapped in Activities

For Phase 6 mapping:
- One Temporal Workflow per **committed intention** from `executive-agent`
- The Workflow encodes the full task decomposition plan from `agent-runtime`
- Goal lifecycle transitions (PENDING → RUNNING → COMPLETED/FAILED) map to Workflow Execution states

#### Activities

Activities are the **units of work** within a Workflow — the individual skill invocations:

- Each Activity runs on a **Worker** (a process polling the Task Queue)
- Activities support **automatic retries** with configurable policy (max attempts, backoff)
- Activities are explicitly cited in Temporal docs as the appropriate place for **LLM inference calls**
  (due to non-determinism)
- An Activity's successful result is recorded as an `ActivityTaskCompleted` event in the Workflow History,
  making it automatically idempotent on replay

For Phase 6 mapping:
- Each tool call in `motor-output` is a Temporal Activity
- LiteLLM inference calls within `agent-runtime` are Temporal Activities
- Vector store operations (Phase 5 memory retrieval) called from `agent-runtime` are Activities

#### Signals, Queries, Updates — Decision Matrix

| Mechanism | Direction | Sync? | Recorded? | Use case |
|---|---|---|---|---|
| **Signal** | Client → Workflow | Async (fire-and-forget) | Yes (history) | Stop/abort interrupts; priority escalation from executive-agent |
| **Query** | Client → Workflow | Sync (read-only) | No | Goal status checks; current execution state inspection |
| **Update** | Client → Workflow | Sync (validated write) | Yes (history) | Modifying a running goal's parameters; returning acknowledgment |

Design rule: **Signals for control flow** (can't block); **Updates for mutations with acknowledgment**
(must confirm receipt); **Queries for read-only introspection**.

#### Child Workflows

For hierarchical task decomposition:
- A top-level Workflow (committed intention) can spawn Child Workflows (sub-tasks)
- Child Workflows have independent Event Histories but are linked to parent lifecycle
- Maps to the BDI plan hierarchy: high-level intentions decompose into sub-plans, each executed as
  a Child Workflow

### 3.2 Prefect — Fallback Orchestration

**Source**: `tech-prefect-workflows.md` (docs.prefect.io/v3/develop/write-workflows)

Prefect is a Python-native workflow orchestration platform. It serves as the **fallback** when Temporal
is unavailable (as noted in `docs/Workplan.md` §709 — "run a comparative spike during Phase 6"):

#### Structural Mapping to Temporal

| Temporal concept | Prefect equivalent | Notes |
|---|---|---|
| Workflow | `@flow` decorated function | Similar durable execution semantics |
| Activity | `@task` decorated function | `@task(retries=3, retry_delay_seconds=10)` |
| Child Workflow | Subflow (flow called within flow) | Same hierarchical decomposition |
| Event History | Prefect API state machine | Less granular than Temporal; not fully deterministic replay |
| Signal (stop) | `flow.cancel()` via Prefect API | Less integrated; no Update equivalent |

#### Prefect Limitations vs. Temporal

- Prefect does not support **deterministic replay** from Event History — if a Worker crashes mid-execution,
  tasks already completed are not automatically replayed; they must be checkpointed manually
- Prefect has weaker support for **long-running** (multi-day) executions — Temporal is preferred for
  goal-horizon tasks
- Prefect's state machine (Pending → Running → Completed/Failed/Crashed/Cancelled) is less expressive
  than Temporal's Event History for debugging

**Recommendation from spike**: Temporal should be the default. Prefect should be the fallback only for
scenarios where Temporal infrastructure is unavailable (e.g., local dev without Docker Compose services
running). The circuit-breaker pattern: attempt Temporal registration; if Temporal server is unreachable
after N retries, fall back to Prefect.

### 3.3 Tool Registry Architecture

The `agent-runtime` tool registry must:
- Maintain a map of `skill_id → Temporal Activity function + Worker queue`
- Support dynamic registration (new tools discovered via A2A agent cards — see §4.2)
- Support capability filtering (given a goal, return the ranked list of applicable skills)
- Support health checking (skip unavailable Workers from the dispatch plan)

---

## 4. `motor-output` — A2A Protocol

**Sources**: `tech-a2a-spec.md` (a2a-protocol.org/latest/topics/what-is-a2a), `tech-a2a-discovery.md` (a2a-protocol.org/latest/topics/agent-discovery)

The A2A protocol (v0.3.0, Linux Foundation / Apache 2.0) provides standardised agent-to-agent
communication over JSON-RPC 2.0 + HTTP(S), with optional SSE streaming.

### 4.1 Agent Card

The `AgentCard` is a JSON document served at `/.well-known/agent-card.json` that forms the
agent's public identity and capability advertisement:

```json
{
  "name": "motor-output",
  "description": "...",
  "url": "http://localhost:<port>",
  "provider": { "organization": "EndogenAI" },
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "authentication": { "schemes": ["Bearer"] },
  "skills": [
    {
      "id": "dispatch_action",
      "name": "Dispatch Action",
      "description": "...",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ]
}
```

All three Phase 6 sub-modules must publish an `AgentCard` at their well-known URI.

### 4.2 Discovery Strategies

| Strategy | Mechanism | Phase 6 use case |
|---|---|---|
| **Well-Known URI** | `GET /.well-known/agent-card.json` | All three sub-modules auto-discoverable within the local stack |
| **Direct Configuration** | Hardcoded URL / env var | Dev/test environments; avoids registry dependency |
| **Curated Registry** | Central repository of `AgentCards`; query by skill/tag | Phase 8+ (application layer); not required for Phase 6 |

The `agent-runtime` tool registry can **auto-discover** new tools by querying the well-known URIs of
co-located modules. Any module that serves a valid `AgentCard` with a matching skill can be added to
the tool registry dynamically.

### 4.3 Task Lifecycle

The A2A task lifecycle governs how `motor-output` receives and acknowledges action requests:

```
message/send (or tasks/send)
  → task created (id, state=submitted)
  → task running (state=working)
  → [SSE stream of intermediate events if streaming=true]
  → task completed (state=completed, artifacts=[...])
     OR task failed (state=failed, error={...})

tasks/get      → poll current state (sync)
tasks/cancel   → abort a running task
```

For Phase 6, `motor-output` is an **A2A server**:
- It receives tasks from `agent-runtime` via `message/send`
- Each task corresponds to one `ActionSpec` (a parameterised action to dispatch)
- On completion, it returns a result artifact containing the `MotorFeedback` payload
- It may stream intermediate status events for long-running dispatches (e.g., waiting for external API response)

### 4.4 A2A + MCP Relationship

From A2A's own documentation ("A2A and MCP"):
- **MCP** is for tool/resource access from a single agent to its tools (agent → tool)
- **A2A** is for agent-to-agent delegation (agent → agent)

In Phase 6:
- `executive-agent` ↔ `agent-runtime`: A2A (peer orchestration delegation)
- `agent-runtime` ↔ `motor-output`: A2A (task delegation)
- `agent-runtime` → tool functions (actual tool call execution): MCP
- `motor-output` → external APIs: direct HTTP (not MCP — MCP is intra-system)

### 4.5 Security Considerations

- Agent Cards containing sensitive URL or skill descriptions should be served behind authentication
  (mTLS, OAuth 2.0, or network restriction)
- The Phase 6 stack is local-only (no external exposure) — Bearer token authentication with a
  shared secret is sufficient for Phase 6; OAuth 2.0 / mTLS for production (Phase 8+)
- OPA can govern which A2A task types `executive-agent` is permitted to delegate

---

## 5. Temporal vs. Prefect Comparison (Pre-Spike Reference)

| Dimension | Temporal | Prefect |
|---|---|---|
| Durability | Full Event History replay; deterministic | State machine; manual checkpointing |
| Long-running tasks | Native (years-long Workflows) | Limited; not designed for multi-day goals |
| Non-determinism handling | Activities isolate non-determinism | Tasks have limited isolation |
| LLM call support | Explicit Activity pattern; idempotency via history | `@task(retries=...)` with manual idempotency |
| Visibility/debugging | Temporal UI + Event History | Prefect UI + run history |
| Local setup | `docker compose` (Temporal server) | Lightweight; runs without external server |
| Python SDK | `temporalio` | `prefect` |
| Fallback role | Primary orchestrator | Circuit-breaker fallback |

The comparative spike (per `docs/Workplan.md` §709) should evaluate: Temporal task queue startup
time, Worker registration latency, and failure recovery behaviour under simulated crashes.

---

## 6. Required Dependencies

| Package | Purpose | Sub-module |
|---|---|---|
| `temporalio` | Temporal Python SDK | `agent-runtime` |
| `prefect` | Prefect Python SDK (fallback) | `agent-runtime` |
| `a2a-sdk` (`pip install a2a-sdk`) | A2A Python SDK | all three sub-modules |
| `opa` (OPA binary or `opa-python`) | Policy evaluation | `executive-agent` |
| `litellm` | LLM inference routing | `agent-runtime` (reasoning Activities) |
| `endogenai_vector_store` | Vector store adapter | `executive-agent` (brain.executive-agent collection) |

---

## 7. Open Questions

1. **Temporal vs. Prefect spike scope**: what constitutes a pass/fail criterion for the spike?
   Recommendation: Temporal passes if it can demonstrate deterministic replay after a simulated
   Worker crash; Prefect wins if Temporal setup time blocks local development.

2. **OPA deployment model**: embedded in-process (Go WASM / `opa-python`) vs. standalone HTTP
   server (`localhost:8181`)? Standalone is more observable and hot-reloadable; embedded eliminates
   a network call on every deliberation cycle.

3. **A2A task ID and Temporal Workflow ID relationship**: should they be the same UUID? Using the
   same ID across both systems would simplify correlation in logs and traces.

4. **BDI plan library storage**: where are the BDI plan templates stored? Candidates: embedded JSON,
   `brain.executive-agent` vector collection (for semantic retrieval), or a structured plans table.
