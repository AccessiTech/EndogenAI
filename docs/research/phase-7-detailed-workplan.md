# Phase 7 — Detailed Implementation Workplan

> **Status**: ✅ RESEARCH COMPLETE — All decisions resolved. Ready for Gate 0 (schema commits + Phase 6 OTel instrumentation).
> **Scope**: Group IV: Adaptive Systems — §§7.1–7.2
> **Milestone**: M7 — Adaptive Systems Active (error detection escalates to executive; reinforcement signals registered)
> **Prerequisite**: Phase 6 (Group III: Executive & Output) complete — `executive-agent`, `agent-runtime`, `motor-output` operational and serving `agent-card.json`.
> **Research references**:
> - [phase-7-neuroscience-adaptive-systems.md](phase-7-neuroscience-adaptive-systems.md) (D1)
> - [phase-7-technologies-adaptive-systems.md](phase-7-technologies-adaptive-systems.md) (D2)
> - [phase-7-synthesis-workplan.md](phase-7-synthesis-workplan.md) (D3)
> - [phase-7-metacognition-scope-research.md](phase-7-metacognition-scope-research.md) (Decision 3 deep-dive)

---

## Contents

1. [Pre-Implementation Checklist](#1-pre-implementation-checklist)
2. [Build Sequence and Gate Definitions](#2-build-sequence-and-gate-definitions)
3. [Directory Structure Overview](#3-directory-structure-overview)
4. [§7.1 — Learning & Adaptation](#4-71--learning--adaptation)
5. [§7.2 — Metacognition & Monitoring](#5-72--metacognition--monitoring)
6. [Cross-Cutting: Phase 6 Instrumentation Additions](#6-cross-cutting-phase-6-instrumentation-additions)
7. [Cross-Cutting: Shared Schemas](#7-cross-cutting-shared-schemas)
8. [Cross-Cutting: Collection Registry](#8-cross-cutting-collection-registry)
9. [Cross-Cutting: Docker Compose Services](#9-cross-cutting-docker-compose-services)
10. [Phase 7 Completion Gate (M7)](#10-phase-7-completion-gate-m7)
11. [Decisions Recorded](#11-decisions-recorded)

---

## 1. Pre-Implementation Checklist

All items below must be confirmed before any Phase 7 code is written.

### 1.1 Phase 6 Gate

```bash
# Verify all three Phase 6 modules are operational
ls modules/group-iii-executive-output/executive-agent/{agent-card.json,README.md,pyproject.toml}
ls modules/group-iii-executive-output/agent-runtime/{agent-card.json,README.md,pyproject.toml}
ls modules/group-iii-executive-output/motor-output/{agent-card.json,README.md,pyproject.toml}

# All Phase 6 tests must pass
cd modules/group-iii-executive-output && uv run pytest tests/ -v

# Verify motor-output emits MotorFeedback with reward_signal.value populated
# (Inspect motor_output/feedback.py FeedbackEmitter.build_feedback — confirmed in research)
grep "reward_signal" modules/group-iii-executive-output/motor-output/src/motor_output/feedback.py

# Verify executive-agent computes reward_delta from incoming MotorFeedback
grep "_compute_reward_delta" modules/group-iii-executive-output/executive-agent/src/executive_agent/feedback.py
```

If Phase 6 tests fail, raise with Phase 6 Executive before proceeding.

### 1.2 Decision 2 — Resolved ✅

**`BrainEnv` observation/action space: Option A selected** — RL policy adjusts `ExecutiveGoal.priority_weight`.

| Field | Value |
|---|---|
| RL policy adjusts | `ExecutiveGoal.priority_weight` per goal class |
| Observation | ~20 floats: `[success_rate, mean_deviation, escalation_rate, task_type_onehot[K], channel_success_rate[5]]` |
| Action space | `Box(~K floats)` — signed delta per goal class, clipped to `[-0.2, +0.2]` |
| Episode boundary | One BDI planning cycle |
| Schema key field | `goal_priority_deltas: list[float]` |
| Biological analogue | Basal ganglia dopamine-modulated direct/indirect pathway balance |

Decision rationale: goal-priority adaptation creates a tighter cortex–basal-ganglia loop than
channel selection; reward signals from `executive-agent` `reward_delta` map directly to
priority weight updates without additional proxy mediator. See `phase-7-synthesis-workplan.md §7 item 1`.

### 1.3 Shared Schema Pre-Landing (Schemas-First Gate)

The following schemas must be present in `shared/schemas/` before Phase 7 modules begin:

| File | Status | Action |
|---|---|---|
| `motor-feedback.schema.json` | ✅ Present (106 lines) | None required |
| `reward-signal.schema.json` (in `shared/schemas/`) | ⚠️ Exists in `shared/types/` as full form; inline subset in `motor-feedback.schema.json` | Refactor: update `motor-feedback.schema.json` to `$ref shared/types/reward-signal.schema.json` |
| `learning-adaptation-episode.schema.json` | ❌ Absent | Create — Option A shape: `action: goal_priority_deltas: list[float]`, `episode_boundary: bdi_cycle` |
| `metacognitive-evaluation.schema.json` | ❌ Absent | Create as part of Phase 7 schema commit |

Land order: `reward-signal.schema.json` refactor → `learning-adaptation-episode` (Option A shape) → `metacognitive-evaluation` → begin code.

### 1.4 Collection Registry Pre-Landing

Add two new collections to `shared/vector-store/collection-registry.json` before implementation:

```json
{
  "name": "brain.learning-adaptation",
  "moduleId": "learning-adaptation",
  "layer": "basal-ganglia",
  "description": "Episode replay buffer for RL policy training. Stores state-action-reward-next_state tuples from Phase 6 MotorFeedback. Prioritised by |reward_value| for replay.",
  "memoryType": "working",
  "notes": "Rolling eviction by lowest priority. task_type metadata enables per-class habit detection. Async background training loop reads from this collection."
},
{
  "name": "brain.metacognition",
  "moduleId": "metacognition",
  "layer": "prefrontal",
  "description": "Per-episode metacognitive evaluation events: confidence scores, deviation z-scores, error flags, escalation events from Phase 6 monitoring.",
  "memoryType": "short-term",
  "notes": "Append-only. Used for trend queries: 'has task_confidence for goal_class X been declining?' and session-level reporting."
}
```

Verify after adding:
```bash
uv run python scripts/schema/validate_all_schemas.py
```

### 1.5 OTel Collector Namespace

Verify the existing `otel-collector.yaml` passes Phase 7 service namespaces through the pipeline.
The `service.namespace = "brain"` resource attribute is set globally (confirmed in `otel-collector.yaml`),
so all `brain_metacognition_*` metrics will flow through to Prometheus without config changes.

```bash
# Confirm collector is running and Prometheus scrapes it
docker compose ps otel-collector
curl -s http://localhost:8889/metrics | head -20
```

### 1.6 Python Environment Bootstrap

```bash
# After scaffold: sync each new module
cd modules/group-iv-adaptive-systems/learning-adaptation && uv sync
cd modules/group-iv-adaptive-systems/metacognition && uv sync

# Verify key dependencies
cd modules/group-iv-adaptive-systems/learning-adaptation
uv run python -c "import stable_baselines3; import gymnasium; print('SB3 ok')"

cd modules/group-iv-adaptive-systems/metacognition
uv run python -c "import opentelemetry; print('OTel ok')"
```

### 1.7 Directory Scaffold

`modules/group-iv-adaptive-systems/` does not yet exist. Run before implementation:

```bash
# Create group root
mkdir -p modules/group-iv-adaptive-systems

# learning-adaptation skeleton
mkdir -p modules/group-iv-adaptive-systems/learning-adaptation/src/learning_adaptation/{env,training,replay,habits,interfaces}
mkdir -p modules/group-iv-adaptive-systems/learning-adaptation/tests
touch modules/group-iv-adaptive-systems/learning-adaptation/src/learning_adaptation/{__init__.py,py.typed}

# metacognition skeleton
mkdir -p modules/group-iv-adaptive-systems/metacognition/src/metacognition/{evaluation,instrumentation,store,interfaces}
mkdir -p modules/group-iv-adaptive-systems/metacognition/tests
mkdir -p modules/group-iv-adaptive-systems/metacognition/observability/prometheus-rules
touch modules/group-iv-adaptive-systems/metacognition/src/metacognition/{__init__.py,py.typed}

# Verify
find modules/group-iv-adaptive-systems -type d | sort
```

---

## 2. Build Sequence and Gate Definitions

```
┌──────────────────────────────────────────────────────────────────┐
│  Phase 7 Build Sequence                                          │
│                                                                  │
│  0a. Decision 2 resolved ✅ Option A (goal-priority adaptation)  │
│  0b. Land shared schemas (§7)                                    │
│  0c. Land collection registry entries (§8)                       │
│  0d. Add Phase 6 OTel instrumentation (§6)                       │
│                                                                  │
│  ─── GATE 0: schemas pass buf lint; Phase 6 OTel emits spans ──  │
│                                                                  │
│  1.  §7.2 metacognition   ← observe Phase 6 first; no ML dep    │
│                                                                  │
│  ─── GATE 1: metacognition passes tests; Prometheus metrics    ─ │
│  ───          visible; alert rules evaluate correctly            │
│                                                                  │
│  2.  §7.1 learning-adaptation  ← depends on metacognition A2A   │
│                             and Phase 6 MotorFeedback stream     │
│                                                                  │
│  ─── GATE 2: learning-adaptation passes tests; policy trains;  ─ │
│  ───          replay buffer populated; habit promotion works     │
│                                                                  │
│  3.  Integration + M7 gate                                       │
│                                                                  │
│  ─── GATE 3 (M7): escalation detected → executive notified;   ─ │
│  ───          reward signal registered; confidence dashboard live │
└──────────────────────────────────────────────────────────────────┘
```

**Why metacognition builds before learning-adaptation**: metacognition has no ML dependencies
(only OTel + ChromaDB) and lower implementation risk. Building it first gives a working
observability layer that learning-adaptation can emit into from day one. Phase 6 OTel
instrumentation (§6) is a pre-requisite for both and must land in Gate 0.

---

## 3. Directory Structure Overview

```
modules/group-iv-adaptive-systems/
├── learning-adaptation/
│   ├── src/learning_adaptation/
│   │   ├── __init__.py
│   │   ├── py.typed
│   │   ├── env/
│   │   │   └── brain_env.py              # gymnasium.Env wrapping Phase 6 signals
│   │   ├── training/
│   │   │   ├── trainer.py                # SB3 PPO training loop
│   │   │   └── skill_feedback_callback.py # cerebellar supervised loss callback
│   │   ├── replay/
│   │   │   └── buffer.py                 # ChromaDB-backed ReplayBuffer, priority sampling
│   │   ├── habits/
│   │   │   └── manager.py                # habit detection + policy checkpoint promotion
│   │   └── interfaces/
│   │       ├── mcp_server.py             # MCP resource + tool registration
│   │       └── a2a_handler.py            # A2A task routing
│   ├── tests/
│   │   ├── test_brain_env.py
│   │   ├── test_replay_buffer.py
│   │   ├── test_trainer.py
│   │   └── test_habit_manager.py
│   ├── agent-card.json
│   ├── learning.config.json
│   ├── pyproject.toml
│   ├── README.md
│   └── uv.lock
│
├── metacognition/
│   ├── src/metacognition/
│   │   ├── __init__.py
│   │   ├── py.typed
│   │   ├── evaluation/
│   │   │   └── evaluator.py              # confidence + z-score computation
│   │   ├── instrumentation/
│   │   │   ├── otel_setup.py             # TracerProvider + MeterProvider config
│   │   │   └── metrics.py                # metric instrument definitions
│   │   ├── store/
│   │   │   └── monitoring_store.py       # ChromaDB brain.metacognition adapter
│   │   └── interfaces/
│   │       ├── mcp_server.py
│   │       └── a2a_handler.py
│   ├── tests/
│   │   ├── test_evaluator.py
│   │   ├── test_metrics.py
│   │   └── test_monitoring_store.py
│   ├── observability/
│   │   └── prometheus-rules/
│   │       └── metacognition.yml
│   ├── agent-card.json
│   ├── monitoring.config.json
│   ├── pyproject.toml
│   ├── README.md
│   └── uv.lock
```

---

## 4. §7.1 — Learning & Adaptation

### 4.1 Dependencies (`pyproject.toml`)

```toml
[project]
name = "learning-adaptation"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "stable-baselines3>=2.3.0",
    "gymnasium>=0.29.0",
    "torch>=2.2.0",
    "opentelemetry-api>=1.24.0",
    "opentelemetry-sdk>=1.24.0",
    "opentelemetry-exporter-otlp-proto-grpc>=1.24.0",
    "chromadb>=0.5.0",
    "structlog>=24.1.0",
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "endogenai-a2a>=0.1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "mypy>=1.10.0", "ruff>=0.4.0"]
```

### 4.2 `agent-card.json`

```json
{
  "name": "learning-adaptation",
  "version": "0.1.0",
  "description": "Reinforcement learning policy training from Phase 6 MotorFeedback. Implements the basal ganglia actor-critic loop and cerebellar supervised correction track. Maintains an episodic replay buffer and promotes stable policies to habit checkpoints.",
  "url": "http://localhost:8170",
  "capabilities": {
    "mcp": true,
    "a2a": true
  },
  "neuroanatomicalAnalogue": "Basal ganglia (actor-critic) + Cerebellum (supervised correction) + Hippocampus (episodic replay)"
}
```

### 4.3 `learning.config.json`

```json
{
  "algorithm": "PPO",
  "total_timesteps_per_run": 50000,
  "replay_buffer_size": 100000,
  "cerebellar_loss_weight": 0.1,
  "habit_threshold_consecutive_episodes": 20,
  "habit_threshold_success_rate": 0.95,
  "motivation_weight_scaling": true,
  "async_replay_interval_seconds": 300,
  "shadow_policy_enabled": true,
  "shadow_promotion_eval_episodes": 10,
  "metacognition_url": null,
  "vector_store": {
    "collection": "brain.learning-adaptation",
    "embedding_model": "nomic-embed-text",
    "chroma_host": "localhost",
    "chroma_port": 8000
  }
}
```

### 4.4 `brain_env.py` — gymnasium.Env Adapter

**Decision 2 resolved: Option A — goal-priority adaptation.** ✅

```python
class BrainEnv(gymnasium.Env):
    """
    Wraps Phase 6 MotorFeedback stream as a gymnasium environment.

    Decision 2 — Option A: RL policy adjusts ExecutiveGoal.priority_weight per goal class.

    Observation: rolling window of MotorFeedback fields per goal_class —
      [success_rate, mean_deviation, escalation_rate, task_type_onehot[K], channel_success_rate[5]]
    Action: signed delta per goal class, clipped to [-0.2, +0.2], applied as
      ExecutiveGoal.priority_weight += action[i] for each goal class i.
    Episode boundary: one BDI planning cycle.

    Biological analogue: basal ganglia adjusting motor programme selection
    via dopamine-modulated direct/indirect pathway balance.
    """
    def __init__(self, config: LearningConfig, n_goal_classes: int = 5):
        super().__init__()
        # Observation: [success_rate, mean_deviation, escalation_rate,
        #               task_type_onehot[K], channel_success_rate[5]]
        obs_dim = 3 + n_goal_classes + 5
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(obs_dim,), dtype=np.float32
        )
        # Action: signed delta per goal class, clipped to [-0.2, +0.2]
        self.action_space = spaces.Box(
            low=-0.2, high=0.2, shape=(n_goal_classes,), dtype=np.float32
        )
```

**Key `BrainEnv` methods to implement:**

| Method | Responsibility |
|---|---|
| `reset()` | Zero-initialise rolling window arrays; return initial observation |
| `step(action)` | Consume next `MotorFeedback` from queue; compute reward; update observation; check episode boundary |
| `_update_observation()` | Recompute the obs vector from the rolling window after each feedback |
| `_episode_boundary()` | One BDI planning cycle (executive-agent processes one goal commit) |
| `close()` | Clear replay buffer connection |

### 4.5 `buffer.py` — ChromaDB ReplayBuffer

```python
class ReplayBuffer:
    """
    ChromaDB-backed episodic replay buffer.
    Documents: state vector, action, reward, next_state, task_type.
    Metadata: priority (|reward_value|), timestamp, task_type, habit_eligible.
    Sampling: prioritised descending by priority.
    Eviction: drop lowest-priority when size > replay_buffer_size.
    """
    def add(self, episode: LearningAdaptationEpisode) -> None: ...
    def sample(self, n: int, task_type: str | None = None) -> list[LearningAdaptationEpisode]: ...
    def stats(self) -> ReplayBufferStats: ...
    def evict_lowest(self, n: int) -> None: ...
```

**Schema**: `learning-adaptation-episode.schema.json` must be landed before this class is implemented.

### 4.6 `trainer.py` — SB3 Training Loop

```python
class PolicyTrainer:
    """
    SB3 PPO training loop with dual-track learning:
      Track 1 (BG / actor-critic): standard PPO value + policy loss
      Track 2 (cerebellar): SkillFeedbackCallback adds supervised correction loss

    Shadow policy: trains a shadow copy; promotes to active only after
    shadow_promotion_eval_episodes consecutive above-threshold evaluations.
    This models habit consolidation during sleep (offline) rather than waking.
    """
    def train_step(self, episodes: list[LearningAdaptationEpisode]) -> TrainingResult: ...
    def evaluate_shadow(self) -> EvaluationResult: ...
    def promote_shadow_to_active(self) -> PolicyPromotion: ...
```

### 4.7 `SkillFeedbackCallback`

```python
class SkillFeedbackCallback(BaseCallback):
    """
    SB3 callback that adds cerebellar supervised correction loss.

    On each rollout end: compute skill_feedback_loss =
      MSE(predicted_outcome, actual_outcome) from episode batch.
    Scales by cerebellar_loss_weight (default 0.1).
    Biological analogue: climbing fibre error signal → Purkinje cell LTD.
    """
```

### 4.8 `manager.py` — Habit Manager

```python
class HabitManager:
    """
    Detects stable policies eligible for habit promotion.
    Criteria: success_rate >= habit_threshold_success_rate over
              habit_threshold_consecutive_episodes episodes.
    Promoted habits: policy checkpoint stored in brain.learning-adaptation
    with habit_eligible=True metadata. Bypasses RL training loop at inference.
    Biological analogue: dorsolateral striatum habit system.
    """
    def check_promotion_eligibility(self, task_type: str) -> bool: ...
    def promote(self, task_type: str) -> HabitPromotion: ...
    def list_habits(self) -> list[HabitRecord]: ...
```

### 4.9 MCP Interface

**Resources:**
```
resource://brain.learning-adaptation/policy/current       → PolicySummary
resource://brain.learning-adaptation/replay-buffer/stats  → ReplayBufferStats
resource://brain.learning-adaptation/performance/history  → list[EpisodePerformance]
resource://brain.learning-adaptation/habits/catalog       → list[HabitRecord]
```

**Tools:**
```
tool://learning-adaptation/train
  input:  { motor_feedback: MotorFeedback | list[MotorFeedback] }
  output: TrainingResult

tool://learning-adaptation/predict
  input:  { observation: list[float] }
  output: ActionPrediction

tool://learning-adaptation/promote-habit
  input:  { task_type: str }
  output: HabitPromotion
```

### 4.10 A2A Interface

**Inbound tasks:**
```
adapt_policy      sender: executive-agent    payload: MotorFeedback (batch)
replay_episode    sender: motor-output       payload: list[MotorFeedback]
```

**Outbound tasks:**
```
habit_promoted    target: executive-agent    payload: { task_type, policy_path, eval_score }
adaptation_failed target: metacognition      payload: { reason, episode_id, error }
```

### 4.11 Async Replay Loop

```python
async def _async_replay_loop(self) -> None:
    """
    Background coroutine: fires every async_replay_interval_seconds.
    Samples from brain.learning-adaptation, calls trainer.train_step().
    Separate from real-time inference — shadow policy trained here,
    promoted to active after evaluation.
    """
    while self._running:
        await asyncio.sleep(self._config.async_replay_interval_seconds)
        episodes = self._buffer.sample(n=256)
        if episodes:
            result = await self._trainer.train_step(episodes)
            logger.info("replay.train_step", result=result)
```

### 4.12 Test Specifications

| Test file | What to test |
|---|---|
| `test_brain_env.py` | `reset()` returns correct obs shape; `step()` updates obs from mock `MotorFeedback`; episode boundary triggers done; reward extraction |
| `test_replay_buffer.py` | `add()` persists to ChromaDB; `sample(n)` returns n records sorted by priority; `evict_lowest()` removes correct records; stats are accurate |
| `test_trainer.py` | `train_step()` with mock episodes completes without error; shadow policy promoted after N consecutive evals; `SkillFeedbackCallback` computes loss |
| `test_habit_manager.py` | Promotion blocked below threshold; triggered above threshold; `list_habits()` reflects promoted state |

Integration test:
```python
# test_integration.py
# 1. Create mock MotorFeedback batch (10 episodes)
# 2. Call learning-adaptation A2A: adapt_policy
# 3. Assert replay buffer has 10 entries
# 4. Trigger async replay step
# 5. Assert training result returned with positive total_timesteps
```

---

## 5. §7.2 — Metacognition & Monitoring

### 5.1 Dependencies (`pyproject.toml`)

```toml
[project]
name = "metacognition"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "opentelemetry-api>=1.24.0",
    "opentelemetry-sdk>=1.24.0",
    "opentelemetry-exporter-otlp-proto-grpc>=1.24.0",
    "opentelemetry-exporter-prometheus>=0.45b0",
    "chromadb>=0.5.0",
    "structlog>=24.1.0",
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "endogenai-a2a>=0.1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "mypy>=1.10.0", "ruff>=0.4.0"]
```

### 5.2 `agent-card.json`

```json
{
  "name": "metacognition",
  "version": "0.1.0",
  "description": "Meta-level monitoring of Phase 6 executive-agent and motor-output. Computes task confidence, deviation z-scores, and escalation rates. Emits OTel metrics to the brain observability stack and fires Prometheus alerts on sustained degradation.",
  "url": "http://localhost:8171",
  "capabilities": {
    "mcp": true,
    "a2a": true
  },
  "neuroanatomicalAnalogue": "Anterior cingulate cortex (error detection) + Prefrontal cortex BA10 (confidence estimation) + Nelson & Narens meta-level"
}
```

### 5.3 `monitoring.config.json`

```json
{
  "confidence_threshold": 0.7,
  "anomaly_zscore_threshold": 2.0,
  "alert_window_minutes": 5,
  "rolling_window_size": 100,
  "deviation_error_threshold": 0.6,
  "escalation_rate_per_minute_threshold": 0.1,
  "escalation_enabled": true,
  "shadow_training_confidence_floor": 0.5,
  "metrics_export": {
    "otlp_endpoint": "http://localhost:4317",
    "prometheus_port": 9464
  },
  "vector_store": {
    "collection": "brain.metacognition",
    "embedding_model": "nomic-embed-text",
    "chroma_host": "localhost",
    "chroma_port": 8000
  }
}
```

### 5.4 `otel_setup.py` — Provider Configuration

```python
"""
OTel provider setup for metacognition.
Connects to the existing OTel Collector at otlp_endpoint.
Prometheus exporter runs on prometheus_port for direct Prometheus scraping.

service.name = "metacognition"
service.namespace = "brain"   (matches otel-collector.yaml resource attribute)
"""
def configure_telemetry(config: MonitoringConfig) -> tuple[Tracer, Meter]:
    resource = Resource.create({
        SERVICE_NAME: "metacognition",
        "service.namespace": "brain",
        "service.version": "0.1.0",
    })
    # Tracer: exports to OTel Collector via OTLP gRPC
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=config.metrics_export.otlp_endpoint))
    )
    # Meter: exports to Prometheus (scraped by prometheus.yml otel-collector job)
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PrometheusMetricReader(port=config.metrics_export.prometheus_port)]
    )
    return tracer_provider.get_tracer(__name__), meter_provider.get_meter(__name__)
```

### 5.5 `metrics.py` — Prometheus Metric Definitions

All metrics use the `brain_metacognition_` prefix to pass the `brain_.*` Prometheus relabel filter.

```python
# Tier 1 metrics (from FastAPI auto-instrumentation — populated automatically)
# brain_executive_agent_request_duration_seconds  (Histogram)
# brain_motor_output_request_duration_seconds      (Histogram)
# brain_http_errors_total                          (Counter)

# Tier 2 metrics (computed in evaluator.py, recorded here)

task_confidence = meter.create_gauge(
    name="brain_metacognition_task_confidence",
    description="Rolling task confidence per goal_class [0,1]. Falls as error rate rises.",
    unit="1",
)
deviation_score = meter.create_gauge(
    name="brain_metacognition_deviation_score",
    description="Latest deviation_score from MotorFeedback [0,1].",
    unit="1",
)
reward_delta = meter.create_histogram(
    name="brain_metacognition_reward_delta",
    description="reward_delta distribution per episode [-0.15, 0.15].",
    unit="1",
)
task_success_rate = meter.create_gauge(
    name="brain_metacognition_task_success_rate",
    description="Rolling success rate per task_type [0,1].",
    unit="1",
)
escalation_total = meter.create_counter(
    name="brain_metacognition_escalation_total",
    description="Cumulative count of escalate=true MotorFeedback events.",
    unit="{event}",
)
retry_count = meter.create_histogram(
    name="brain_metacognition_retry_count",
    description="retry_count distribution per episode.",
    unit="{retry}",
)
policy_denial_rate = meter.create_gauge(
    name="brain_metacognition_policy_denial_rate",
    description="Rolling policy denial rate from BDI deliberation.",
    unit="1",
)
deviation_zscore = meter.create_gauge(
    name="brain_metacognition_deviation_zscore",
    description="z-score of deviation_score vs rolling mean. >2 = anomaly.",
    unit="1",
)
```

### 5.6 `evaluator.py` — Core Confidence and Z-Score Computation

```python
class MetacognitionEvaluator:
    """
    Core computation engine for metacognitive evaluation.
    Maintains rolling windows per (source_module, task_type) pair.

    Biological analogue:
      - deviation_zscore → ACC ERN amplitude
      - task_confidence  → anterior PFC BA10 confidence estimate
      - rolling windows  → posterior parietal Bayesian accumulation
    """
    def __init__(self, config: MonitoringConfig) -> None:
        self._window: deque = deque(maxlen=config.rolling_window_size)
        self._config = config

    def evaluate(self, event: EvaluateOutputPayload) -> MetacognitiveEvaluation:
        """
        Compute confidence, z-score, and error flag from a Phase 6 TaskResult.

        Steps:
          1. Add deviation_score to rolling window.
          2. Compute reward_deviation_zscore = (deviation_score - μ) / σ.
          3. Compute task_confidence = rolling_mean_reward_delta × success_rate.
          4. Determine error_detected = deviation_score > deviation_error_threshold.
          5. Persist evaluation to brain.metacognition ChromaDB collection.
          6. Record all OTel metrics.
          7. If task_confidence < confidence_threshold: trigger A2A request_correction.
        """
```

### 5.7 Prometheus Alert Rules

**File**: `modules/group-iv-adaptive-systems/metacognition/observability/prometheus-rules/metacognition.yml`

```yaml
groups:
  - name: metacognition
    interval: 30s
    rules:
      - alert: TaskConfidenceLow
        expr: brain_metacognition_task_confidence < 0.7
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Task confidence below threshold"
          description: "task_type={{ $labels.task_type }} confidence={{ $value | humanize }}"

      - alert: DeviationAnomalyHigh
        expr: brain_metacognition_deviation_zscore > 2.0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Deviation z-score anomaly detected"
          description: "source={{ $labels.source_module }} zscore={{ $value | humanize }}"

      - alert: EscalationRateElevated
        expr: rate(brain_metacognition_escalation_total[5m]) > 0.1
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Elevated escalation rate from motor-output"

      - alert: PolicyDenialRateHigh
        expr: brain_metacognition_policy_denial_rate > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "BDI policy denial rate above threshold"
          description: "ACC conflict-monitoring analogue firing"
```

These rules must be referenced in `prometheus.yml`:
```yaml
rule_files:
  - "prometheus-rules/metacognition.yml"
```

### 5.8 MCP Interface

**Resources:**
```
resource://brain.metacognition/confidence/current    → map[task_type → float]
resource://brain.metacognition/anomalies/recent      → list[MetacognitiveEvaluation]
resource://brain.metacognition/alerts/active         → list[ActiveAlert]
resource://brain.metacognition/report/session        → MetacognitiveSessionReport
```

**Tools:**
```
tool://metacognition/evaluate
  input:  { task_result: EvaluateOutputPayload }
  output: MetacognitiveEvaluation

tool://metacognition/configure-threshold
  input:  { metric: str, value: float }
  output: ConfigUpdate

tool://metacognition/report
  input:  { window: str }   # e.g. "1h", "session"
  output: MetacognitiveSessionReport
```

### 5.9 A2A Interface

**Inbound tasks:**
```
evaluate_output    sender: executive-agent, motor-output    payload: EvaluateOutputPayload
```

**Outbound tasks:**
```
request_correction    target: executive-agent    payload: { anomaly_summary, suggested_action, trace_id }
```

### 5.10 Test Specifications

| Test file | What to test |
|---|---|
| `test_evaluator.py` | `evaluate()` with mock payload: correct z-score computation; confidence falls with failure sequence; `error_detected` set above threshold; `task_confidence` rises with success sequence |
| `test_metrics.py` | All OTel metric instruments created; gauge/counter/histogram record without error; Prometheus exporter returns `brain_metacognition_*` metrics |
| `test_monitoring_store.py` | Evaluation events written to ChromaDB; trend query returns declining confidence sequence in correct order |

Integration test:
```python
# test_integration.py
# 1. Start metacognition server (TestClient or actual uvicorn)
# 2. POST evaluate_output A2A task: deviation_score=0.9, success=False, escalated=True
# 3. Assert MetacognitiveEvaluation: error_detected=True, zscore > 0
# 4. Assert Prometheus /metrics contains brain_metacognition_escalation_total >= 1
# 5. Assert brain.metacognition ChromaDB has 1 document
```

---

## 6. Cross-Cutting: Phase 6 Instrumentation Additions

**Decision**: Hybrid Strategy C — Tier 1 (FastAPI auto-instrumentation) + Tier 2 (A2A observer hook).

These changes are small and non-breaking. They land in Gate 0 alongside schemas.

### 6.1 Tier 1 — FastAPI Auto-Instrumentation

**`executive-agent/pyproject.toml`** and **`motor-output/pyproject.toml`** — add:
```toml
"opentelemetry-instrumentation-fastapi>=0.50b0",
```

**`executive-agent/server.py`** and **`motor-output/server.py`** — add after `app = FastAPI(...)`:
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

### 6.2 Tier 2 — A2A Observer Hook in `executive-agent`

**`executive-agent/feedback.py`** — `FeedbackHandler.__init__()`:
```python
def __init__(
    self,
    goal_stack: GoalStack,
    affective_client: Any | None = None,
    metacognition_client: Any | None = None,   # ← new optional param
) -> None:
    self._metacognition = metacognition_client
```

**`receive_feedback()`** — add after `reward_delta` computation:
```python
if self._metacognition is not None:
    with contextlib.suppress(Exception):
        await self._metacognition.send_task("evaluate_output", {
            "goal_id": goal_id,
            "success": success,
            "deviation_score": feedback.deviation_score,
            "reward_delta": reward_delta,
            "escalated": feedback.escalate,
            "task_type": await self._goal_stack.get_goal_class(goal_id),
            "retry_count": feedback.retry_count,
            "latency_ms": feedback.latency_ms,
        })
```

**`executive-agent/server.py`** — wire `metacognition_client` from `METACOGNITION_URL` env var:
```python
import os
metacognition_url = os.getenv("METACOGNITION_URL")
metacognition_client = A2AClient(url=metacognition_url) if metacognition_url else None
feedback_handler = FeedbackHandler(
    goal_stack=goal_stack,
    affective_client=affective_client,
    metacognition_client=metacognition_client,
)
```

### 6.3 Tier 2 (stretch) — W3C Trace Context in `RewardSignal`

Once Tier 1 is running and OTel spans flow, inject `traceparent` into forwarded `RewardSignal`:
```python
from opentelemetry import trace
from opentelemetry.propagate import inject as otel_inject

def _build_reward_signal(feedback: MotorFeedback) -> dict[str, Any]:
    carrier: dict[str, str] = {}
    otel_inject(carrier)           # injects traceparent into carrier dict
    signal = { ... }
    if carrier:
        signal["traceContext"] = {"traceparent": carrier.get("traceparent", "")}
    return signal
```

This activates the `traceContext.traceparent` field already defined in `shared/types/reward-signal.schema.json`.

---

## 7. Cross-Cutting: Shared Schemas

### Gate 0 schema commits (in order)

**Commit 1**: Refactor `shared/schemas/motor-feedback.schema.json`
- Update `reward_signal` property to `$ref: "../types/reward-signal.schema.json"` (or copy the full definition if cross-directory `$ref` is not supported by `buf lint`)
- Decision 1B: no new file needed; `shared/types/reward-signal.schema.json` already exists

**Commit 2**: Land `shared/schemas/metacognitive-evaluation.schema.json`

Key fields (from Decision 3 scope research §9.2):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://endogenai.accessitech.com/shared/schemas/metacognitive-evaluation.schema.json",
  "title": "MetacognitiveEvaluation",
  "required": ["event_id", "goal_id", "task_type", "deviation_score", "reward_delta",
               "escalated", "success", "retry_count", "task_confidence",
               "reward_deviation_zscore", "error_detected", "source_module", "timestamp"],
  "properties": {
    "event_id":               { "type": "string", "format": "uuid" },
    "goal_id":                { "type": "string", "format": "uuid" },
    "task_type":              { "type": "string" },
    "deviation_score":        { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "reward_delta":           { "type": "number", "minimum": -0.15, "maximum": 0.15 },
    "escalated":              { "type": "boolean" },
    "success":                { "type": "boolean" },
    "retry_count":            { "type": "integer", "minimum": 0 },
    "task_confidence":        { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "reward_deviation_zscore":{ "type": "number" },
    "error_detected":         { "type": "boolean" },
    "source_module":          { "type": "string", "enum": ["executive-agent", "motor-output"] },
    "timestamp":              { "type": "string", "format": "date-time" },
    "trace_context":          { "type": "object", "properties": { "traceparent": { "type": "string" } } }
  }
}
```

**Commit 3**: Land `shared/schemas/learning-adaptation-episode.schema.json`
- **Decision 2 resolved (Option A)** — shape confirmed: `action` is `goal_priority_deltas: list[float]`; `episode_boundary` is `bdi_cycle`
- Key fields: `state: list[float]` (obs vector), `action: list[float]` (priority deltas), `reward: float`, `next_state: list[float]`, `task_type: str`, `episode_boundary: "bdi_cycle"`, `goal_class_count: int`

After each schema commit:
```bash
cd shared && buf lint
uv run python scripts/schema/validate_all_schemas.py
```

---

## 8. Cross-Cutting: Collection Registry

Add both collections to `shared/vector-store/collection-registry.json` (see §1.4 for full JSON).

```bash
# After adding collections, verify
cd shared/vector-store/python && uv run python -c "
from endogenai_vector_store import VectorStoreAdapter
names = [c['name'] for c in VectorStoreAdapter.list_collections()]
assert 'brain.learning-adaptation' in names
assert 'brain.metacognition' in names
print('Collections verified:', names)
"
```

---

## 9. Cross-Cutting: Docker Compose Services

Phase 7 requires no new Docker services. All required services are already in `docker-compose.yml`:

| Service | Required by | Status |
|---|---|---|
| `chromadb` | Both modules (vector store) | ✅ Existing |
| `ollama` | Both modules (nomic-embed-text) | ✅ Existing |
| `otel-collector` | metacognition (OTLP endpoint) | ✅ Existing |
| `prometheus` | metacognition (alert rules) | ✅ Existing |
| `grafana` | metacognition (dashboard) | ✅ Existing |

**One config change required**: add Prometheus alert rule files to `prometheus.yml`:
```yaml
rule_files:
  - "/etc/prometheus/rules/*.yml"
```
And mount the rules directory in `docker-compose.yml`:
```yaml
prometheus:
  volumes:
    - ./observability/prometheus-rules:/etc/prometheus/rules:ro   # ← add this line
```

Then copy the alert rules file:
```bash
mkdir -p observability/prometheus-rules
cp modules/group-iv-adaptive-systems/metacognition/observability/prometheus-rules/metacognition.yml \
   observability/prometheus-rules/metacognition.yml
# Or symlink if preferred
```

Verify Prometheus loads the rules after `docker compose restart prometheus`:
```bash
curl -s http://localhost:9090/api/v1/rules | python3 -m json.tool | grep "metacognition"
```

---

## 10. Phase 7 Completion Gate (M7)

**Milestone**: M7 — Adaptive Systems Active

M7 is complete when all of the following are verified:

### Gate 3 Checklist

```bash
# 1. Both module tests pass
cd modules/group-iv-adaptive-systems/learning-adaptation && uv run pytest -v
cd modules/group-iv-adaptive-systems/metacognition && uv run pytest -v

# 2. Both modules serve agent-card.json
curl http://localhost:8170/.well-known/agent-card.json | python3 -m json.tool
curl http://localhost:8171/.well-known/agent-card.json | python3 -m json.tool

# 3. Metacognition metrics flow to Prometheus
curl -s http://localhost:9464/metrics | grep brain_metacognition_
curl -s http://localhost:9090/api/v1/query?query=brain_metacognition_task_confidence

# 4. Alert rules loaded
curl -s http://localhost:9090/api/v1/rules | grep TaskConfidenceLow

# 5. Escalation propagates from Phase 6 to metacognition
# Send mock MotorFeedback with escalate=True to executive-agent
# Assert metacognition logs escalation_total counter increment
# Assert executive-agent receives A2A request_correction from metacognition

# 6. Reward signal registered in learning-adaptation
# Send mock MotorFeedback batch (>0 reward) to learning-adaptation
# Assert brain.learning-adaptation ChromaDB has episodes
# Assert trainer.train_step() completes without error
# Assert replay buffer stats show populated buffer

# 7. Schema validation passes
cd shared && buf lint
uv run python scripts/schema/validate_all_schemas.py
```

**M7 success signal** (from Workplan.md):
> "Error detection escalates to executive; reinforcement signals registered"

Mapped to specific assertions:
- **Error detection**: `DevationAnomalyHigh` or `TaskConfidenceLow` alert evaluates to `FIRING` in Prometheus when deviation_score > 2σ
- **Escalates to executive**: metacognition sends `request_correction` A2A task to `executive-agent` and it is acknowledged
- **Reinforcement signals registered**: `brain.learning-adaptation` ChromaDB collection has at least one episode document with `reward` field populated

---

## 11. Decisions Recorded

| # | Decision | Resolution | Recorded in |
|---|---|---|---|
| 1 | `reward-signal.schema.json` standalone extraction | **Option B** — refactor `motor-feedback.schema.json` to `$ref shared/types/reward-signal.schema.json` | D3 §6, this doc §7 |
| 2 | `BrainEnv` observation/action space framing | **Option A** — goal-priority weight adaptation; `Box(K floats)` action; `goal_priority_deltas` schema field; BDI-cycle episode boundary | D3 §7 item 1, this doc §4.4, §1.2 |
| 3 | Metacognition monitoring scope | **Option A** — Phase 6 outputs only (`executive-agent` + `motor-output`) | D3 §7 item 5, scope research doc §10 |
| 3a | Observation strategy | **Strategy C — Hybrid** (FastAPI auto-instrument + A2A observer hook) | Scope research doc §10, this doc §6 |
| 3b | metacognition client URL config | **`METACOGNITION_URL` env var**, default `None` | Scope research doc §10, this doc §6.2 |
| 3c | structlog → OTel bridge | **Stretch goal** — implement after Tier 1/2 stable | Scope research doc §10, this doc §6 |
| 3d | W3C trace context propagation | **In scope for Phase 7 Tier 1 stretch** | Scope research doc §10, this doc §6.3 |
