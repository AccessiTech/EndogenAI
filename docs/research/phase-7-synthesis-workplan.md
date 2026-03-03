# Phase 7 — Group IV: Adaptive Systems — Synthesis Workplan (D3)

_Generated: 2025-07-14 by Docs Executive Researcher_

_Cross-references:_
- _D1: docs/research/phase-7-neuroscience-adaptive-systems.md_
- _D2: docs/research/phase-7-technologies-adaptive-systems.md_
- _D3 Decision 3 deep-dive: docs/research/phase-7-metacognition-scope-research.md_
- _docs/Workplan.md §§7.1–7.2_
- _docs/architecture.md_
- _shared/schemas/ and shared/types/_

---

## 1. Guiding Architectural Principles

| Principle | Biological derivation (D1) | Implementation consequence (D2) |
|---|---|---|
| **Reward is the teacher** | SNc/VTA dopamine RPE = TD error signal | Every output action receives a `MotorFeedback.reward_signal`; no learning occurs without it |
| **Two learning tracks run in parallel** | BG RL + cerebellar supervised error are distinct but coupled systems | PPO/SAC policy gradient + supervised `skill_feedback` loss head — separate optimisers, shared model |
| **Experience must be replayed offline** | Hippocampal sharp-wave ripples consolidate memory during rest | `ReplayBuffer` in ChromaDB; async background training loop distinct from real-time inference |
| **Metacognition is a separate control level** | Nelson & Narens meta-level / object-level hierarchy | `metacognition` module wraps — but does not replace — all Phase 6 execution paths |
| **Errors trigger, anomalies escalate** | ACC ERN fires on errors; PFC escalates severe violations | OTel span events for errors; Prometheus alert for sustained degradation |
| **Habits are frozen policies** | Dorsolateral striatum accumulates fast, rigid response patterns | Stable policies promoted to cached checkpoints, bypassing the RL training loop |
| **Local compute first** | — | SB3 (local PyTorch) before RLlib; ChromaDB before any cloud vector store |
| **Schemas contract behaviour** | — | `motor-feedback.schema.json` ✅ confirmed; `reward-signal.schema.json` to be extracted as standalone `$ref` (Decision 1 — Option B) before implementation begins |

---

## 2. Module §7.1 — Learning & Adaptation

### 2.1 Neuroscience Derivation

| Biological structure | Biological function | Implementation decision |
|---|---|---|
| Basal ganglia direct/indirect pathways + SNc dopamine | TD error signals updating action values via D1/D2 receptor balance | Actor-critic policy (PPO): actor selects actions; critic computes value; δ updates both |
| Cerebellar Purkinje cells + climbing fibre | Supervised error correction for skill consolidation (LTD) | `skill_feedback` supervised loss added to PPO objective; separate learning rate |
| Hippocampal CA1/CA3 + sharp-wave ripples | Episodic experience replay for offline policy consolidation | `ReplayBuffer` ChromaDB collection; async training loop; prioritised sampling by `|reward_delta|` |
| Dorsolateral striatum (habit system) | Model-free, overlearned behaviour cached for speed | Stable policy checkpoints promoted after N consecutive successful episodes |
| Nucleus accumbens (motivation gate) | Reward salience gates whether learning occurs | `RewardSignal.magnitude` scales effective learning rate per episode; zero magnitude = no update |

### 2.2 Collection Specification

**Collection**: `brain.learning-adaptation`

| Property | Value |
|---|---|
| Backend | ChromaDB (local) |
| Embedding model | `nomic-embed-text` (Ollama) |
| Document schema | `{"episode_id": str, "state": list[float], "action": list[float], "reward": float, "next_state": list[float], "task_type": str}` |
| Metadata | `priority` (float), `timestamp` (ISO-8601), `task_type` (str), `habit_eligible` (bool) |
| Retention | Rolling window — evict lowest-priority episodes when capacity exceeds `replay_buffer_size` |
| Query | Prioritised sampling by `priority` descending; filtered by `task_type` for habit detection |

### 2.3 Core Interfaces

**MCP resources:**
```
resource://brain.learning-adaptation/policy/current
resource://brain.learning-adaptation/replay-buffer/stats
resource://brain.learning-adaptation/performance/history
resource://brain.learning-adaptation/habits/catalog
```

**MCP tools:**
```
tool://learning-adaptation/train          → { motor_feedback: MotorFeedback } → TrainingResult
tool://learning-adaptation/predict        → { observation: Observation } → ActionPrediction
tool://learning-adaptation/promote-habit  → { task_type: str } → HabitPromotion
```

**A2A inbound tasks:**
```
task: adapt_policy        sender: executive-agent    payload: MotorFeedback (batch)
task: replay_episode      sender: motor-output        payload: list[MotorFeedback]
```

**A2A outbound tasks:**
```
task: habit_promoted      target: executive-agent     payload: { task_type, policy_path }
task: adaptation_failed   target: metacognition       payload: { reason, episode_id }
```

### 2.4 Key Source Files

```
modules/group-iv-adaptive-systems/learning-adaptation/
  src/
    env/brain_env.py             # gymnasium.Env adapter bridging Phase 6 signal streams
    training/trainer.py          # SB3 PPO/SAC training loop + skill_feedback callback
    replay/buffer.py             # ChromaDB-backed ReplayBuffer with priority sampling
    habits/manager.py            # habit detection and policy checkpoint management
    interfaces/mcp_server.py     # MCP resource + tool registration
    interfaces/a2a_handler.py    # A2A task reception and dispatch
  tests/
    test_brain_env.py
    test_replay_buffer.py
    test_training.py
  agent-card.json
  learning.config.json           # algorithm, timesteps, thresholds
  pyproject.toml
  README.md
```

### 2.5 Configuration Schema (`learning.config.json`)

```json
{
  "algorithm": "PPO",
  "total_timesteps_per_run": 50000,
  "replay_buffer_size": 100000,
  "cerebellar_loss_weight": 0.1,
  "habit_threshold_episodes": 20,
  "habit_threshold_success_rate": 0.95,
  "motivation_weight_scaling": true,
  "async_replay_interval_seconds": 300,
  "vector_store": {
    "collection": "brain.learning-adaptation",
    "embedding_model": "nomic-embed-text"
  }
}
```

---

## 3. Module §7.2 — Metacognition & Monitoring

### 3.1 Neuroscience Derivation

| Biological structure | Biological function | Implementation decision |
|---|---|---|
| ACC (rostral/dorsal) + ERN | Real-time error detection (100ms); conflict monitoring | OTel span `error_detected` attribute + span event on error; instrument every Phase 6 task execution |
| ACC reward-based learning theory | Evaluates severity of error against expected outcome | `reward_deviation_zscore` metric — distance from rolling mean in standard deviations |
| Anterior PFC (BA 10) | Metacognitive confidence estimation | `task_confidence` histogram per task type; falls when error rate rises |
| DLPFC (BA 9/46) | Performance monitoring, working memory | OTel trace spans accumulate task execution history in context window |
| PFC → external escalation pathway | When confidence fails threshold: PFC sends alarm | Prometheus alert rule fires when `task_confidence < threshold` for sustained window |
| Posterior parietal cortex (precuneus) | Decision confidence accumulation | Per-task confidence score accumulates via Bayesian update on `reward_deviation` |
| Nelson & Narens meta-level / object-level | Meta-level monitors and intervenes on object-level | `metacognition` is meta-level; sends corrective signals to `learning-adaptation` (object-level) |

### 3.2 Collection Specification

**Collection**: `brain.metacognition`

| Property | Value |
|---|---|
| Backend | ChromaDB (local) |
| Embedding model | `nomic-embed-text` (Ollama) |
| Document schema | `{"event_id": str, "task_id": str, "task_type": str, "confidence": float, "error_detected": bool, "reward_delta": float, "anomaly_score": float}` |
| Metadata | `timestamp` (ISO-8601), `module_source` (str), `alert_fired` (bool), `severity` (str) |
| Query use | Trend analysis ("has confidence been declining over last N episodes?"), pattern retrieval |

### 3.3 Core Interfaces

**MCP resources:**
```
resource://brain.metacognition/confidence/current
resource://brain.metacognition/anomalies/recent
resource://brain.metacognition/alerts/active
resource://brain.metacognition/report/session
```

**MCP tools:**
```
tool://metacognition/evaluate              → { task_result: TaskResult, expected: Expected } → MetacognitiveEvaluation
tool://metacognition/configure-threshold   → { metric: str, value: float } → ConfigUpdate
tool://metacognition/report                → { window: str } → MetacognitiveReport
```

**A2A outbound tasks:**
```
task: request_correction    target: executive-agent    payload: { anomaly_summary, suggested_action }
task: escalate_anomaly      target: [future alerting]  payload: { alert_type, severity, trace_id }
```

**A2A inbound tasks:**
```
task: evaluate_output    sender: executive-agent, motor-output    payload: TaskResult
```

**OTel → Prometheus → Grafana pipeline** (existing stack, zero new services):
```
metacognition module
  → opentelemetry-sdk
    → OTLP exporter → otel-collector (observability/)
      → Prometheus scrape → prometheus.yml
        → Grafana dashboard
          → Alertmanager → alert rules (observability/prometheus-rules/metacognition.yml)
```

### 3.4 Key Source Files

```
modules/group-iv-adaptive-systems/metacognition/
  src/
    evaluation/evaluator.py          # core confidence and deviation computation
    instrumentation/otel_setup.py    # OTel provider, tracer, meter configuration
    instrumentation/metrics.py       # metric definitions (gauges, histograms, counters)
    store/monitoring_store.py        # ChromaDB metacognition collection adapter
    interfaces/mcp_server.py         # MCP resource + tool registration
    interfaces/a2a_handler.py        # A2A task reception and dispatch
  tests/
    test_evaluator.py
    test_otel_metrics.py
  agent-card.json
  monitoring.config.json             # thresholds, windows, alert config
  observability/
    prometheus-rules/metacognition.yml  # alertmanager rule definitions
  pyproject.toml
  README.md
```

### 3.5 Configuration Schema (`monitoring.config.json`)

```json
{
  "confidence_threshold": 0.7,
  "anomaly_zscore_threshold": 2.0,
  "alert_window_minutes": 5,
  "rolling_window_size": 100,
  "escalation_enabled": true,
  "metrics_export": {
    "otlp_endpoint": "http://localhost:4317",
    "prometheus_port": 9464
  },
  "vector_store": {
    "collection": "brain.metacognition",
    "embedding_model": "nomic-embed-text"
  }
}
```

---

## 4. Cross-Module Integration Points

### 4.1 The Learning Loop (Full Signal Chain)

```
[Phase 6 motor-output]
    ↓  MotorFeedback (reward_signal, skill_feedback)
[learning-adaptation]
    ↓  train() → policy update
    ↓  promote-habit() if stable
    ↑  adapt_policy task (A2A, from executive-agent on failure)

[Phase 6 all modules]
    ↓  TaskResult (any Phase 6 execution)
[metacognition]
    ↓  evaluate() → confidence_score, error_detected, reward_deviation_zscore
    ↓  OTel metrics → Prometheus → Grafana
    ↓  if anomaly: A2A task → executive-agent (request_correction)
    ↓  if alert: Prometheus rule → Alertmanager → escalation
    ↑  evaluate_output task (A2A, from any Phase 6 module)

[metacognition] ←→ [learning-adaptation]
    metacognition sends: adaptation_signal when sustained performance decline detected
    learning-adaptation sends: adaptation_failed when training loop fails
```

### 4.2 Phase Gate Dependencies

Phase 7 depends on the following Phase 6 artefacts being complete and stable:

| Dependency | Required for |
|---|---|
| `shared/schemas/motor-feedback.schema.json` | `learning-adaptation` training loop input |
| `shared/schemas/reward-signal.schema.json` | `learning-adaptation` motivation weighting |
| Phase 6 `motor-output` `MotorFeedback` emission | Live reward signal for training |
| Phase 6 `executive-agent` A2A agent-card | A2A task delegation routing |
| OTel Collector pipeline (existing) | `metacognition` metrics export |
| Prometheus server (existing) | Alert rule evaluation |

**Blocking items** (must land before Phase 7 code begins):
1. Verify `shared/schemas/motor-feedback.schema.json` exists — create if absent.
2. Verify `shared/schemas/reward-signal.schema.json` exists — create if absent.
3. Verify Phase 6 `motor-output` emits `MotorFeedback` with `reward_signal.delta` populated.

---

## 5. Scaffold Checklist for Phase 7 Modules

### §7.1 `learning-adaptation`

- [ ] Scaffold module directory under `modules/group-iv-adaptive-systems/learning-adaptation/`
- [ ] Create `pyproject.toml` with `stable-baselines3`, `gymnasium`, `torch`, `opentelemetry-api/sdk`
- [ ] Implement `agent-card.json` at `/.well-known/agent-card.json`
- [ ] Implement `BrainEnv` gymnasium adapter (observation = Phase 5/6 state; action = output adjustment)
- [ ] Implement `ReplayBuffer` backed by `brain.learning-adaptation` ChromaDB collection
- [ ] Implement PPO training loop with `SkillFeedbackCallback` for cerebellar-track loss
- [ ] Implement async replay loop (background coroutine, fires every `async_replay_interval_seconds`)
- [ ] Implement habit detection and `promote-habit` tool
- [ ] Expose MCP server with all resources and tools listed in §2.3
- [ ] Implement A2A handler for inbound `adapt_policy` and `replay_episode` tasks
- [ ] Create `learning.config.json`
- [ ] Write unit tests: `BrainEnv`, `ReplayBuffer`, training loop (mocked environment)
- [ ] Write integration test: full episode → replay → training step
- [ ] Write `README.md`

### §7.2 `metacognition`

- [ ] Scaffold module directory under `modules/group-iv-adaptive-systems/metacognition/`
- [ ] Create `pyproject.toml` with `opentelemetry-api/sdk`, `opentelemetry-exporter-otlp`, `opentelemetry-exporter-prometheus`, `chromadb`
- [ ] Implement `agent-card.json`
- [ ] Implement OTel provider setup (`otel_setup.py`) — connect to existing OTel Collector endpoint
- [ ] Define all metrics (`task_confidence`, `error_rate_per_task`, `reward_deviation_zscore`, `anomaly_total`)
- [ ] Implement `evaluator.py` — confidence and z-score computation with rolling window
- [ ] Implement `monitoring_store.py` — write evaluation events to `brain.metacognition` collection
- [ ] Expose MCP server with all resources and tools listed in §3.3
- [ ] Implement A2A handler for inbound `evaluate_output` tasks
- [ ] Create `monitoring.config.json`
- [ ] Create Prometheus alert rules `observability/prometheus-rules/metacognition.yml`
- [ ] Write unit tests: `evaluator.py`, metrics recording, ChromaDB store
- [ ] Write integration test: task execution → OTel span → Prometheus metric → alert rule
- [ ] Write `README.md`

---

## 6. Schema Prerequisites

The following JSON Schema files must be present in `shared/schemas/` before Phase 7 implementation:

| Schema file | Status | Action required |
|---|---|---|
| `motor-feedback.schema.json` | ✅ **Confirmed** — exists in `shared/schemas/` (106 lines, complete) | None. Note: field uses `value` not `delta` — terminology in D1/D2 should be updated to match |
| `reward-signal.schema.json` | ✅ **Exists** in `shared/types/reward-signal.schema.json` (123 lines, comprehensive — includes `traceContext.traceparent`, semantic `type` enum, temporal decay). A simpler inline version lives in `MotorFeedback.reward_signal`. Decision 1B: extract the inline version as `shared/schemas/reward-signal.schema.json` and `$ref` it. | Does not block Phase 7 code — schema exists. Action: refactor `motor-feedback.schema.json` to use `$ref` to `shared/types/reward-signal.schema.json`. |
| `learning-adaptation-episode.schema.json` | ❌ Not yet created | Shape depends on Decision 2 (BrainEnv framing — see §7 item 1). Cannot be written until that decision is made. |
| `metacognitive-evaluation.schema.json` | ❌ Not yet created | Create as part of Phase 7 schema step. |

**Schema creation order**:
1. Extract `reward-signal.schema.json` (Decision 1B gate — do this first)
2. After Decision 2 is resolved: land `learning-adaptation-episode.schema.json`
3. Land `metacognitive-evaluation.schema.json` alongside the metacognition module scaffold

---

## 7. Open Questions and Risks

1. **`BrainEnv` observation/action space design** (OPEN — blocking; requires user decision)

   Gymnasium's `Env` contract requires two things to be specified before any training can begin:
   - `observation_space`: what the policy *sees* on each step
   - `action_space`: the set of choices the policy can make

   The question is not technical — it is semantic: **what is this agent learning to optimise?**
   The answer determines every downstream artefact: the `BrainEnv` class, the episode schema, the
   replay buffer document shape, and the MCP `predict` tool response type.

   ---

   #### Option A — Goal-priority adaptation (recommended)

   The RL policy learns to re-weight which `ExecutiveGoal` types the system should prioritise,
   based on recent success/failure history. This closes the loop directly inside Phase 6's
   existing BDI planning cycle.

   **Biological parallel**: basal ganglia modulate goal selection (which action plan to pursue)
   — not the raw motor command itself. The dopamine signal reaches the striatum *before* the
   motor cortex fires. This is goal-selection learning, not motor learning.

   **Observation vector** (~20 floats, derived entirely from `MotorFeedback`):
   ```
   [ success_rate_last_N,          # rolling mean of MotorFeedback.success
     mean_deviation_score,         # rolling mean of MotorFeedback.deviation_score
     escalation_rate,              # proportion of recent episodes where escalate=true
     task_type_one_hot[K],         # which goal type is currently active (K = number of types)
     channel_success_rate[5] ]     # per-channel (http/a2a/file/render/control) recent success
   ```

   **Action space** (continuous Box, ~K floats):
   ```
   delta_priority_weights[K]      # signed adjustment to ExecutiveGoal.priority_weight per type
                                  # clipped to [-0.2, +0.2] per step
   ```

   **Reward**: `MotorFeedback.reward_signal.value` — already in the schema, no new signal needed.

   **Episode boundary**: one full BDI planning cycle of `executive-agent` (goal selected →
   action dispatched → `MotorFeedback` received).

   **Pros**:
   - Observation and action spaces are 100% derivable from existing `MotorFeedback` schema
   - No new Phase 5/6 API surface required
   - Biologically faithful (BG = goal selection, not raw motor)
   - `learning-adaptation-episode.schema.json` can be written immediately after this decision

   **Cons**:
   - Effect of priority changes is indirect — the learned adjustment influences the *next* BDI
     cycle, not the current one. This one-step credit assignment delay is manageable but worth
     noting.

   ---

   #### Option B — Motor-channel selection

   The RL policy learns which dispatch channel (http, a2a, file, render, control-signal) to use
   for a given action type, based on per-channel historical performance.

   **Biological parallel**: cerebellum selects the motor sub-programme most likely to succeed
   for a given context — channel selection maps to cerebellar motor plan selection.

   **Observation vector** (~15 floats):
   ```
   [ channel_success_rate[5],      # recent success per channel
     channel_latency_mean[5],      # mean latency_ms per channel
     action_type_one_hot[K] ]      # which action type is being dispatched
   ```

   **Action space** (Discrete(5)):
   ```
   channel_choice                 # integer index into [http, a2a, file, render, control-signal]
   ```

   **Reward**: `MotorFeedback.reward_signal.value × (1 - deviation_score)` — penalises both
   failure and prediction error.

   **Episode boundary**: one action dispatch (very tight loop, fast learning signal).

   **Pros**:
   - Tiny action space (5 discrete choices) — simple to train
   - Very direct one-step reward signal; credit assignment is trivial
   - Naturally fits cerebellar supervised-correction track

   **Cons**:
   - Channel selection is partially already handled by `motor-output`'s existing routing logic;
     the RL policy could conflict with it or duplicate responsibility
   - Does not change *what* the system tries to do — only *how* it dispatches. Lower strategic
     leverage than Option A.

   ---

   #### Option C — Attention/salience weighting (not recommended for Phase 7)

   The RL policy re-weights `attention_weight` of incoming signal types in Phase 1, based on
   which signals correlated with downstream task success. Most biologically faithful (dorsolateral
   striatum gates sensory gating) but crosses module boundaries from Group IV back into Group I.
   Recommended for a later phase once the adaptive systems layer is proven.

   ---

   **What this decision determines downstream:**

   | If you choose | `observation_space` | `action_space` | Episode boundary | `learning-adaptation-episode.schema.json` key field |
   |---|---|---|---|---|
   | **Option A** | Box(~20 floats) | Box(~K floats) | BDI planning cycle | `goal_priority_deltas: list[float]` |
   | **Option B** | Box(~15 floats) | Discrete(5) | Single action dispatch | `channel_selection: int` |

   **`learning-adaptation-episode.schema.json` cannot be written until this decision is made.**
   This is the single hardest blocker before Phase 7 implementation can begin.

   > **Decision required from user before proceeding.**

2. **`MotorFeedback` schema and reward-signal naming** — ✅ **Decision 1 resolved (Option B)**

   `motor-feedback.schema.json` is confirmed present and complete in `shared/schemas/`. The
   `reward_signal` sub-object uses `value` (not `delta`) as the scalar reward field. Terminology
   in D1 and D2 should be updated to use `reward_signal.value` consistently.

   **Action**: extract `reward_signal` as a standalone `shared/schemas/reward-signal.schema.json`
   and update `motor-feedback.schema.json` to `$ref` it. This is a non-breaking refactor (same
   field names, same validation logic) and should be committed before any Phase 7 module code.

3. **Async training race condition** — shadow-policy approach recommended

   The async replay loop and real-time inference loop both access the policy — this requires either
   model read-locking or a shadow-policy strategy (train shadow, promote on evaluation). The shadow
   approach is recommended: biologically, habit consolidation occurs during sleep (offline), not
   during waking behaviour. Train a shadow copy; promote to active on passing an evaluation episode.

4. **OTel Collector namespace**: the existing `otel-collector.yaml` must accept the
   `endogenai.metacognition` service namespace. Verify the pipeline filter before implementation.

5. **Metacognition scope** — ✅ **Decision 3 resolved (Option A — Phase 6 outputs only)**

   `metacognition` will monitor Phase 6 outputs only (`executive-agent` and `motor-output`).
   See [docs/research/phase-7-metacognition-scope-research.md](phase-7-metacognition-scope-research.md)
   for the full endogenous evidence base, including:
   - Complete Phase 6 observable signal catalog (from source code)
   - Three observation strategies (FastAPI auto-instrument / A2A hook / hybrid)
   - Full signal-to-Prometheus-metric mapping table
   - `metacognitive-evaluation.schema.json` field list
   - Prometheus alert rule templates

   Monitoring is deferred for Phases 1–5 because Phase 6 `MotorFeedback` is the integrated
   downstream product of all upstream processing — failures in Phases 1–5 manifest as elevated
   `deviation_score` or negative `reward_delta` in Phase 6 anyway. Attribution to a specific
   upstream phase is the correct future scope. The biological parallel supports this: the PFC
   monitors at the level of integrated outputs, not individual neuron populations.

6. **RLlib decision**: start with SB3 (local PyTorch, no cluster). Scale to RLlib only if
   episode throughput becomes a measured bottleneck. Adding Ray upfront introduces distributed
   systems complexity without proven necessity.

---

## 8. Recommended Workplan Additions

The following checklist items are proposed for the Phase Executive to consider adding to
`docs/Workplan.md §7`. These are **recommendations only** — user must approve before
Executive Planner makes any changes to the canonical workplan.

```markdown
### Phase 7 Prerequisites (new gate items)
- [x] ~~Verify `shared/schemas/motor-feedback.schema.json` exists~~ — ✅ confirmed present
- [ ] Extract `shared/schemas/reward-signal.schema.json` from inline `MotorFeedback.reward_signal` definition (Decision 1B)
- [ ] Resolve `BrainEnv` observation/action space framing (Decision 2 — user approval required)
- [ ] Confirm Phase 6 `motor-output` emits `MotorFeedback.reward_signal.value` populated
- [ ] Land `shared/schemas/learning-adaptation-episode.schema.json` (after Decision 2)

### §7.1 Learning & Adaptation (additions)
- [ ] Design `BrainEnv` observation_space / action_space (requires explicit architectural decision)
- [ ] Implement `ReplayBuffer` ChromaDB adapter with prioritised episode sampling
- [ ] Implement dual-track training: PPO + `SkillFeedbackCallback` supervised loss
- [ ] Implement async background replay loop (shadow-policy strategy)
- [ ] Implement habit detection and `promote-habit` checkpoint mechanism
- [ ] Land `shared/schemas/learning-adaptation-episode.schema.json`
- [ ] Land `shared/schemas/metacognitive-evaluation.schema.json`

### §7.2 Metacognition & Monitoring (additions)
- [ ] Configure OTel Collector pipeline for `endogenai.metacognition` namespace
- [ ] Create Prometheus alert rules (`observability/prometheus-rules/metacognition.yml`)
- [ ] Implement rolling z-score computation for `reward_deviation_zscore`
- [ ] Write `monitoring.config.json` with configurable thresholds
- [ ] Integration test: task execution → OTel → Prometheus → alert rule fires
```
