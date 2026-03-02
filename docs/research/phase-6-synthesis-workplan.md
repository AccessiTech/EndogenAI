# Phase 6 Research Brief: Synthesis — Brain-Inspired Architecture and Implementation Guidance

> **Audience**: Phase 6 implementation agents (executive-agent → agent-runtime → motor-output).  
> **Purpose**: Synthesise the neuroscience research (D1) and technology research (D2) into a
> module-by-module implementation guide for Phase 6 Group III. Each section maps biological
> findings to concrete design decisions, collection routing rules, technology choices, and
> open questions. This document is the primary pre-implementation reference; the actual
> phase checklist lives in [docs/Workplan.md](../Workplan.md) §§6.1–6.3.

---

## 1. Guiding Architectural Principles

The following principles are derived directly from the D1 and D2 research briefs and govern every
Phase 6 module:

| Principle | Biological origin | Implementation rule |
|---|---|---|
| **Deliberation separated from execution** | PFC deliberates; BG/cerebellum executes | `executive-agent` handles goal deliberation and intention commitment; `agent-runtime` handles skill sequencing and execution; never merge these responsibilities into one module |
| **Policy gates every intention** | ACC conflict detection + BG direct/indirect gating | Every candidate goal must pass OPA policy evaluation before being committed to the execution queue; fail-closed by default (`default allow = false`) |
| **Durable execution for long-horizon goals** | PFC persistent goal maintenance; hippocampal encoding | Task orchestration uses Temporal Workflows; goal state must survive process restarts via Event History replay |
| **Actions are Activities, not Workflows** | Single cerebellar error-correctable movements | Each tool call and LLM inference call is a Temporal Activity (idempotent, retryable, non-deterministic allowed); Workflows are the orchestration envelope only |
| **Feedforward over pure feedback** | Cerebellar predictive/forward models | `agent-runtime` pre-stages tool parameters and fetches dependencies before the execute signal arrives; do not wait for the execution phase to begin preparation |
| **Correct only task-relevant deviations** | Optimal Feedback Control (Todorov & Jordan 2002) | `motor-output` handles minor/recoverable errors locally; only escalates goal-threatening failures to `executive-agent` |
| **Upward feedback closes the actor-critic loop** | Spinocerebellar tract → thalamocortical feedback | `motor-output` must emit a structured `MotorFeedback` signal back to `executive-agent` on every action completion; this feedback carries a `RewardSignal` attachment |
| **LLM calls are never direct** | — | All inference routes through LiteLLM; LLM invocations are Temporal Activities, never embedded in Workflow logic |
| **Adapters, never raw SDKs** | — | `endogenai_vector_store` for all collection access; `infrastructure/adapters/` bridge for cross-module calls |
| **All three sub-modules serve `/.well-known/agent-card.json`** | — | Every Phase 6 module is A2A-discoverable from day one; agent card authored before implementation begins |

---

## 2. Module §6.1 — Executive / Agent Layer (`executive-agent`)

### 2.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|---|---|
| DLPFC: active goal maintenance via recurrent circuits; capacity ~4 goal chunks (Cowan 2001) | Goal stack has a configurable hard cap; evict lowest-priority/oldest goal when at capacity; never unbounded accumulation |
| Miller & Cohen: PFC provides top-down bias signals, does not micro-manage | `executive-agent` dispatches intent + weighted context to `agent-runtime`; does not specify individual tool calls |
| Shimamura: PFC applies select / maintain / update / reroute to working memory | Goal lifecycle has four explicit operations: promote (select), hold (maintain), replace (update), delegate (reroute) |
| OFC (BA 11–14): value/reward expectancy coding; updates in real time | Goals carry a `value_score` derived from the current `RewardSignal`; re-scored on every feedback cycle |
| vmPFC (BA 10–12): somatic marker / fast heuristic value pass | A fast heuristic pass pre-filters candidates before full OPA deliberation (short-circuit for obviously off-policy goals) |
| ACC (BA 24/32): conflict detection, error monitoring, policy violation flagging | OPA policy engine evaluates every candidate intention; violations are logged as structured `PolicyDecision` events |
| BG direct pathway: disinhibits thalamus → releases selected action | Committing an intention = pushing it to the Temporal execution queue (releasing the lock on action) |
| BG indirect pathway: global suppression of competing actions | Only one intention active per goal-class at a time; competing candidates are suspended until queue clears or priority changes |
| BG hyperdirect pathway: rapid broad cancellation via STN | A stop signal (any upstream module) must cancel the full execution queue immediately — not just the current step |
| Dopamine RPE actor-critic: striatum = critic (value); frontal = actor (policy) | `MotorFeedback.reward_signal` feeds back into goal scoring; `executive-agent` updates goal priority weights iteratively |
| PFC persistent self-model: autobiographical + current goals = coherent identity | `identity.config.json` holds static identity constraints; `brain.executive-agent` collection holds dynamic self-model state |

### 2.2 Collection: `brain.executive-agent`

- **Layer**: prefrontal
- **Type**: executive
- **Embedding model**: `nomic-embed-text` via Ollama (local compute first)
- **Content**: goals, values, policies (expressed as natural language for semantic retrieval), identity state, BDI plan templates
- **Routing**: used for semantic retrieval of relevant past goals and policy precedents when building the deliberation context
- **Config file**: `vector-store.config.json` (standard module pattern)

### 2.3 Core Interfaces

**MCP (context exchange)**:
- Tool: `executive_agent.push_goal(description, priority, deadline?, constraints?)` → `GoalItem` (id, lifecycle_state)
- Tool: `executive_agent.get_goal_stack(filter?)` → ranked list of active `GoalItem` records
- Tool: `executive_agent.evaluate_policy(action, context)` → `PolicyDecision` (allow, violations[], explanation)
- Tool: `executive_agent.update_identity(delta)` → updated `SelfModel`

**A2A (task delegation)**:
- Accepts task: `{ type: "commit_intention", goal_id, context_payload }` → returns committed `GoalItem` with Temporal Workflow ID
- Accepts task: `{ type: "receive_feedback", motor_feedback }` → processes `MotorFeedback`; updates goal score; emits `RewardSignal`
- Accepts task: `{ type: "abort_goal", goal_id, reason }` → triggers BG hyperdirect-equivalent: cancels Workflow + clears queue for that goal

**Events emitted** (via `shared/utils/` structured log + OTel):
- `goal.committed` — intent promoted to execution queue
- `goal.deferred` — intent suspended (priority dropped below threshold)
- `goal.completed` — feedback confirmed success
- `goal.failed` — feedback confirmed failure; reason attached
- `policy.violation` — OPA returned deny; violations list logged

### 2.4 Key Files

| File | Purpose |
|---|---|
| `identity.config.json` | Static identity constraints; persona; core values |
| `vector-store.config.json` | `brain.executive-agent` collection configuration |
| `policies/identity.rego` | OPA rules: identity integrity constraints |
| `policies/goals.rego` | OPA rules: goal feasibility and conflict constraints |
| `policies/actions.rego` | OPA rules: action permission and scope constraints |
| `agent-card.json` | A2A capability advertisement |

### 2.5 Open Questions (§6.1)

1. Should OPA run **embedded** (WASM / `opa-python`) or as a **standalone HTTP server** at
   `localhost:8181`? Standalone is more observable and hot-reloadable; embedded eliminates a
   network round-trip on every deliberation cycle.
2. What is the right **goal stack capacity** (analogous to PFC ~4-chunk limit)? Recommended
   starting value: `max_active_goals = 5` (configurable via `identity.config.json`).
3. Where is the **BDI plan library** stored? Candidates: (a) embedded JSON in the module, (b)
   `brain.executive-agent` vector collection (semantic retrieval), (c) structured SQL table.
   Option (b) is the most endogenous — query past successful plans by semantic similarity.
4. Should `executive-agent` maintain its own instance of **working memory** or delegate entirely to
   the Phase 5 `working-memory` module for context assembly? Delegation is preferred (no duplication
   of store); `executive-agent` calls `working_memory.assemble_context` before each deliberation cycle.

---

## 3. Module §6.2 — Agent Execution (Runtime) Layer (`agent-runtime`)

### 3.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|---|---|
| Marr-Albus: climbing fibre error signal drives parallel fibre LTD → skill refinement | Temporal Activity execution results (success/failure + deviation from expected) feed a `skill_feedback` log; used by Phase 7 adaptive layer for skill improvement |
| Doya: cerebellum = supervised learning | `agent-runtime` tracks predicted vs. actual execution cost/latency per skill; exposes this as a time-series for supervised refinement |
| Internal forward model: predict sensory outcomes before action | Before dispatching a skill pipeline, `agent-runtime` emits a predicted `MotorFeedback` (expected outcome); actual feedback is compared against it |
| Internal inverse model: given desired outcome, compute required commands | Task decomposition = inverse model: given goal state, compute the ordered skill pipeline that achieves it |
| Cerebrocerebellum: >50% interconnected with association cortices (Buckner 2011) | `agent-runtime` is not just motor — it handles cognitive skill pipelines (reasoning, memory retrieval, synthesis) as well as external tool calls |
| pre-SMA: plans sequences without executing; connects to caudate + PFC | Task decomposition is a separate phase from execution; `agent-runtime` builds the full pipeline plan and validates it before dispatching any Activities |
| pre-SMA: action switching; sequence re-ordering | `agent-runtime` must support mid-execution plan revision (new Temporal Signal → update pipeline order) |
| Bereitschaftspotential: preparation begins ~1000 ms before conscious intent | Tool parameters, memory context, and dependency data are pre-fetched during the decomposition phase, before the Workflow enters its execution phase |
| BG motor loop feeds SMA: caudate updates action values back to pre-SMA | `agent-runtime` receives `GoalItem` priority updates from `executive-agent` during execution and can re-order the in-flight pipeline accordingly |

### 3.2 Temporal Workflow Architecture

Each committed intention from `executive-agent` maps to one **Temporal Workflow Execution**:

```
WorkflowType: "IntentionWorkflow"
WorkflowID:   <goal_id>           # same UUID as A2A task ID for cross-system correlation

Workflow logic:
  1. receive GoalItem + ContextPayload
  2. decompose → ordered list of SkillStep (tool_id, params, expected_output)
  3. for each SkillStep:
     a. execute Activity(tool_id, params)           # actual dispatch
     b. receive ActivityResult
     c. if ActivityResult.deviation > threshold:
          → send MotorFeedback(partial) to executive-agent via A2A
          → await Signal("continue" | "abort" | "revise")
  4. aggregate results → final MotorFeedback
  5. emit to executive-agent
```

**Temporal message passing rules** (per D2 §3.1 decision matrix):
- **Signal** for: stop/abort from `executive-agent`; priority change; goal context update (fire-and-forget)
- **Update** for: mid-execution plan revision where `agent-runtime` must acknowledge receipt
- **Query** for: status checks from upstream monitoring

**LLM Activities** (all LiteLLM-routed):
- `reasoning.decompose_goal(goal, context)` → `SkillPipeline`
- `reasoning.evaluate_plan(pipeline, constraints)` → validated or revised `SkillPipeline`
- `reasoning.synthesize_result(activity_results[])` → `AggregatedResult`

### 3.3 Tool Registry

| Property | Spec |
|---|---|
| Storage | In-memory map + `tool-registry.config.json` for persistence |
| Entry | `{ skill_id, worker_queue, input_schema, output_schema, health_endpoint, a2a_agent_card_url }` |
| Dynamic registration | On startup, query well-known URIs of co-located modules; register any `AgentCard` skill as a tool |
| Health checking | Before including a skill in a decomposition plan, ping its `health_endpoint`; skip unavailable tools |
| Fallback | Temporal primary; Prefect circuit-breaker if Temporal server unreachable at registration time |

### 3.4 Core Interfaces

**MCP (context exchange)**:
- Tool: `agent_runtime.decompose(goal_id, context_payload)` → `SkillPipeline`
- Tool: `agent_runtime.get_execution_status(goal_id)` → Temporal Workflow state + current step
- Tool: `agent_runtime.register_tool(skill_id, config)` → registered tool entry
- Tool: `agent_runtime.list_tools(capability_filter?)` → available `SkillEntry[]`

**A2A (task delegation)**:
- Accepts task: `{ type: "execute_intention", goal_id, skill_pipeline }` → starts Temporal Workflow; returns Workflow ID
- Accepts task: `{ type: "abort_execution", goal_id }` → sends Temporal Signal("abort") to running Workflow
- Accepts task: `{ type: "revise_plan", goal_id, revised_pipeline }` → sends Temporal Update("revise") to Workflow
- Emits task to `motor-output`: `{ type: "dispatch_action", action_spec }` per Activity

### 3.5 Open Questions (§6.2)

1. **Temporal vs. Prefect spike pass/fail criteria**: Temporal passes if it demonstrates deterministic
   replay after a simulated Worker crash with zero data loss. Prefect wins if Temporal server cold-start
   time (in `docker compose up`) exceeds 30 seconds on local dev hardware.
2. **Decomposition model**: should `reasoning.decompose_goal` use a fixed prompt template or a DSPy
   module? DSPy is preferred (Phase 5 §5.6 Reasoning module) but adds a dependency on the Phase 5
   reasoning module being operational.
3. **Skill pipeline schema**: `SkillPipeline` needs a formal JSON Schema in `shared/schemas/` before
   implementation begins — this is a cross-module contract (`executive-agent` → `agent-runtime` → `motor-output`).
4. **Feedback granularity**: should `agent-runtime` emit a `MotorFeedback` after every Activity, or only
   at the end of the Workflow? Per the OFC principle, emit only when deviation is task-relevant.

---

## 4. Module §6.3 — Motor / Output / Effector Layer (`motor-output`)

### 4.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|---|---|
| M1 (BA 4): population coding; corticospinal tract; distributed dispatch | Output actions are dispatched in parallel where possible (no sequential-only constraint); dispatcher uses population-style routing (multiple handlers can process the same action class) |
| PMd (dorsal premotor): space/context-dependent channel selection | An `OutputChannelSelector` chooses the correct API/interface/transport before dispatch, based on `ActionSpec.channel` and current context |
| PMv (F5, mirror neurons): same circuit for observation and execution | Corollary discharge: before executing an action, `motor-output` sends a predicted `ActionSpec` representation back to `agent-runtime` (observable pre-action event); the actual execution uses the same schema |
| SMA proper: internally generated sequences; bimanual coordination | Concurrent parallel dispatch (two or more `ActionSpec` instances in the same pipeline step) is supported via async execution |
| SMA proper: direct corticospinal projection (bypasses M1 for some sequences) | Well-known, pre-validated action sequences (e.g., standard acknowledgment messages) can be dispatched via a fast path without full validation overhead |
| Optimal Feedback Control: correct only task-relevant deviations | A three-tier error policy: (1) transient errors → retry locally; (2) recoverable errors → local circuit breaker + fallback; (3) goal-threatening errors → emit `MotorFeedback(escalate=true)` to `executive-agent` |
| Dynamical systems view: pre-configured state-space trajectory unrolls during execution | `ActionPipeline` (ordered list of `ActionSpec`) is fully built during the `agent-runtime` decomposition phase and handed to `motor-output` as a complete plan; no ad-hoc per-step decisions |
| Spinocerebellum: real-time error correction; mossy fibres → deep nuclei → M1 | After each dispatched action, `motor-output` observes the actual outcome and emits a `MotorFeedback` event; this feedback is **synchronous** for blocking actions, **event-driven** for async actions |

### 4.2 Output Channel Registry

| Channel type | Example target | Transport | Error handling tier |
|---|---|---|---|
| HTTP API call | External REST endpoint | `httpx` with retry | Tier 1 (transient) → Tier 2 (circuit breaker) |
| A2A task delegation | Downstream A2A agent | A2A Python SDK | Tier 1 → Tier 3 (if agent card disappears) |
| Message delivery | Chat platform, notification service | Platform-specific SDK | Tier 1 → Tier 2 |
| File write | Local filesystem, cloud object store | `pathlib` / boto3 | Tier 2 (idempotent overwrite) |
| Rendered output | LiteLLM → formatted text | LiteLLM Activity | Tier 1 → Tier 3 (if LLM unavailable) |
| Control signal | Upstream modules via A2A | A2A Python SDK | Tier 3 (always escalate control signal failures) |

### 4.3 Motor Feedback Schema

Every action completion must emit a `MotorFeedback` record:

```json
{
  "action_id": "<uuid>",
  "goal_id": "<uuid>",
  "workflow_id": "<temporal-workflow-id>",
  "dispatched_at": "<ISO8601>",
  "completed_at": "<ISO8601>",
  "channel": "<channel_type>",
  "predicted_outcome": { ... },
  "actual_outcome": { ... },
  "deviation_score": 0.0,
  "error_tier": null,
  "escalate": false,
  "reward_signal": {
    "value": 1.0,
    "source": "motor-output",
    "task_id": "<uuid>"
  }
}
```

`motor-feedback.schema.json` must be landed in `shared/schemas/` before implementation.

### 4.4 Core Interfaces

**MCP (context exchange)**:
- Tool: `motor_output.dispatch(action_spec)` → `ActionReceipt` (action_id, estimated_completion)
- Tool: `motor_output.get_action_status(action_id)` → current state + partial `MotorFeedback`
- Tool: `motor_output.cancel_action(action_id)` → cancellation confirmation
- Tool: `motor_output.register_channel(channel_config)` → registered `OutputChannel`

**A2A (task delegation)**:
- Accepts task from `agent-runtime`: `{ type: "dispatch_action", action_spec }` → executes; returns `MotorFeedback` artifact
- Accepts task: `{ type: "dispatch_pipeline", action_pipeline[] }` → concurrent/sequential batch; returns aggregated `MotorFeedback[]`
- Emits task back to `executive-agent`: `{ type: "receive_feedback", motor_feedback }` on completion

### 4.5 Open Questions (§6.3)

1. **`MotorFeedback` delivery mechanism**: should `motor-output` push feedback to `executive-agent`
   via an A2A task (active push) or have `executive-agent` poll the Temporal Workflow history (passive
   pull)? Active push is preferred — it mirrors the synchronous spinocerebellar feedback loop and avoids
   polling latency.
2. **Rendered output rendering model**: where does text/media rendering occur — inside `motor-output`
   as a LiteLLM Activity, or upstream in `agent-runtime`? Recommendation: `motor-output` handles
   final formatting (like M1's role in fine motor output), but the content is generated by `agent-runtime`
   reasoning Activities.
3. **Concurrency model for parallel dispatch**: should concurrent `ActionSpec` items be dispatched
   as Temporal parallel Activity fan-out, or as independent Temporal Child Workflows? Fan-out is
   simpler; Child Workflows provide better isolation and independent failure handling.
4. **Output channel health checking frequency**: how often should `motor-output` ping channel
   health endpoints? If a channel is unavailable, `agent-runtime` needs to know before decomposing
   a plan that depends on it.

---

## 5. Cross-Module Signal Flow (Phase 6)

```
Phase 5 modules (working-memory, reasoning, affective)
         │  context_payload + RewardSignal
         ▼
  ┌─────────────────────────────────────┐
  │          executive-agent            │
  │  self-model │ goal-stack │ OPA      │
  │  BDI deliberation loop              │
  │  brain.executive-agent (ChromaDB)   │
  └────────────────┬────────────────────┘
                   │ A2A: commit_intention(goal_id, context)
                   ▼
  ┌─────────────────────────────────────┐
  │           agent-runtime             │
  │  decomposition │ tool-registry      │
  │  Temporal Workflow (IntentionWF)    │
  │  pre-stage → execute Activities     │
  └────────────────┬────────────────────┘
                   │ A2A: dispatch_action(action_spec)
                   ▼
  ┌─────────────────────────────────────┐
  │           motor-output              │
  │  channel-selector │ dispatcher      │
  │  error-policy │ feedback-emitter    │
  └────────────────┬────────────────────┘
                   │ external call
                   ▼
         [environment / external system]
                   │ actual outcome
                   ▲
  ┌─────────────────────────────────────┐
  │  MotorFeedback(deviation, reward)   │
  │    → motor-output → executive-agent │
  │    → executive-agent updates goal   │
  │      stack + RewardSignal           │
  └─────────────────────────────────────┘
```

---

## 6. Schemas to Land Before Implementation

These must be authored in `shared/schemas/` before Phase 6 implementation begins. They are
cross-module contracts.

| Schema file | Purpose | Upstream | Downstream |
|---|---|---|---|
| `executive-goal.schema.json` | Goal item: id, description, priority, lifecycle_state, deadline, constraints | `executive-agent` | `agent-runtime` |
| `skill-pipeline.schema.json` | Ordered list of SkillStep: tool_id, params, expected_output | `agent-runtime` | `motor-output` |
| `action-spec.schema.json` | Single parameterised action: type, channel, params, idempotency_key | `agent-runtime` | `motor-output` |
| `motor-feedback.schema.json` | Action outcome: action_id, predicted vs actual, deviation_score, reward_signal | `motor-output` | `executive-agent` |
| `policy-decision.schema.json` | OPA evaluation result: allow, violations[], explanation | `executive-agent` internal | Observability |

---

## 7. Phase Gate Conditions (from Workplan §6)

Phase 6 has an implicit gate requirement: **Phase 5 modules must be sufficiently operational** for
`executive-agent` to call `working_memory.assemble_context` and receive `RewardSignal` from the
affective module. The minimum viable Phase 5 state required:

- `working-memory` module: must accept `assemble_context` MCP call and return a `ContextPayload`
- `affective` module: must emit a `RewardSignal` that `executive-agent` can consume
- `reasoning` module: must expose a `decompose_goal` function (or `agent-runtime` must implement
  its own decomposition Activity as a fallback)

If Phase 5 is not yet operational, Phase 6 can begin with stub implementations of these interfaces.

---

## 8. Recommended Workplan Refinements

The following items are absent from the current `docs/Workplan.md` §6 checklist and are recommended
additions (require user approval before Executive Planner edits the canonical workplan):

- [ ] Land `executive-goal.schema.json`, `skill-pipeline.schema.json`, `action-spec.schema.json`,
      `motor-feedback.schema.json`, `policy-decision.schema.json` in `shared/schemas/` before
      implementation of any Phase 6 module
- [ ] Run Temporal vs. Prefect comparative spike; document pass/fail result and commit decision to
      `docs/research/` before implementing `agent-runtime`
- [ ] Implement OPA policy engine in `executive-agent` with three policy tiers: identity, goals, actions
- [ ] Implement BDI interpreter loop in `executive-agent`; expose reconsideration threshold as config
- [ ] Implement `brain.executive-agent` ChromaDB collection with `identity.config.json` and
      `vector-store.config.json`
- [ ] Implement `MotorFeedback` -> `RewardSignal` attachment and upward push from `motor-output` to
      `executive-agent` (closes the actor-critic loop)
- [ ] Implement tool registry in `agent-runtime` with A2A agent card auto-discovery at startup
- [ ] Implement three-tier error policy in `motor-output` (local retry / circuit-breaker / escalate)
- [ ] Implement parallel `ActionSpec` dispatch (bimanual coordination analogue) in `motor-output`
- [ ] All three sub-modules must serve `/.well-known/agent-card.json` before integration testing
