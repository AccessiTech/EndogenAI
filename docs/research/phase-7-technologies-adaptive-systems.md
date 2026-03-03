# Phase 7 — Group IV: Adaptive Systems — Technologies Research (D2)

_Generated: 2025-07-14 by Docs Executive Researcher_

_Sources:_
- _docs/research/sources/phase-7/tech-stable-baselines3.md (stable-baselines3.readthedocs.io)_
- _docs/research/sources/phase-7/tech-rllib.md (docs.ray.io/en/latest/rllib)_
- _docs/research/sources/phase-7/tech-opentelemetry-python.md (opentelemetry.io/docs/languages/python)_
- _docs/research/sources/phase-7/tech-prometheus.md (prometheus.io/docs/introduction/overview)_
- _shared/schemas/ (existing Phase 5–6 contract schemas)_
- _modules/group-iii-executive-output/ (Phase 6 implementation for MotorFeedback reference)_

---

## 1. Technology Stack Map

| Module | Primary Technology | Scale Path | Monitoring |
|---|---|---|---|
| `learning-adaptation` (§7.1) | Stable-Baselines3 (PyTorch) | RLlib (Ray) | OTel + Prometheus |
| `metacognition` (§7.2) | OpenTelemetry Python SDK | — | Prometheus + Grafana (existing observability stack) |

Both modules are Python. They consume signals from Phase 6 schemas (`MotorFeedback`,
`RewardSignal` — confirm presence in `shared/schemas/`) and produce updated policies /
monitoring metrics.

---

## 2. §7.1 Learning & Adaptation — Technology Deep Dives

### 2.1 Stable-Baselines3 (Primary RL Library)

**Source**: `tech-stable-baselines3.md` (stable-baselines3.readthedocs.io/en/master)

Stable-Baselines3 (SB3) is a set of reliable, production-quality RL algorithm implementations
in PyTorch, published in JMLR (Raffin et al. 2021). It is the correct primary choice for Phase
7 because:

- Algorithms available (all PyTorch): PPO, SAC, A2C, DQN, HER, TD3, DDPG.
- Provides a **unified API** for all algorithms: `model.learn(total_timesteps=N)`,
  `model.predict(obs)`, `model.save(path)`, `model.load(path)`.
- Supports **vectorised environments** (`DummyVecEnv`, `SubprocVecEnv`) for parallel episode
  collection.
- **Callbacks** allow integration hooks at each training step — critical for:
  - `skill_feedback` supervised-error injection at each callback step
  - OTel span creation on training step start/end
  - Early stopping when confidence metric degrades
- **TensorBoard** and **W&B** integrations built-in.
- **Custom environments**: any Python class implementing `gymnasium.Env` works directly.

**Key API pattern for `learning-adaptation`**:

```python
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

class SkillFeedbackCallback(BaseCallback):
    """Injects cerebellar-track supervised error at each training step."""
    def _on_step(self) -> bool:
        skill_error = self.locals["infos"][0].get("skill_feedback", 0.0)
        self.logger.record("train/skill_error", skill_error)
        return True

model = PPO(
    "MlpPolicy",
    env=BrainEnv(config_path="learning.config.json"),
    verbose=1,
    tensorboard_log="./logs/",
)
model.learn(total_timesteps=50_000, callback=SkillFeedbackCallback())
model.save("brain.learning-adaptation/policy")
```

**Algorithm selection guidance** (from SB3 docs §"Which algorithm should I use?"):

| Scenario | Recommended algorithm |
|---|---|
| Continuous action spaces (most agent tasks) | PPO (stable, on-policy) or SAC (sample-efficient, off-policy) |
| Discrete actions (classification-style outputs) | DQN or A2C |
| Goal-conditioned tasks with sparse reward | HER (Hindsight Experience Replay) |
| Habit consolidation / evaluation | Deploy frozen policy from SAC or PPO checkpoint |

**Constraints mapping**:
- SB3 uses PyTorch — consistent with AGENTS.md ("Python for ML/cognitive modules").
- No direct LLM SDK calls: training inputs come from the `BrainEnv` environment adapter that
  reads from the vector store / Phase 6 signal streams; all LLM inference still routes via
  LiteLLM in other modules.
- Local compute first: SB3 runs entirely locally; no cloud dependency.

### 2.2 RLlib (Scale Path)

**Source**: `tech-rllib.md` (docs.ray.io/en/latest/rllib)

RLlib (Liang et al., NeurIPS 2021) is the distributed, production-scale RL library built on
Ray. It is the **Phase 7 scale path**, not the primary starting point.

**Key characteristics**:
- **Distributed sample collection**: `EnvRunner` actors run episodes in parallel across CPUs/GPUs.
- **Multi-agent RL (MARL)**: supports multiple agents sharing experience — relevant when
  `learning-adaptation` needs to train across multiple A2A agent instances concurrently.
- **Offline RL and behavior cloning**: can train from a static dataset without environment
  interaction — useful for supervised replay of historical `ReplayBuffer` data.
- **Fault-tolerant**: built on Ray's actor model — individual `EnvRunner` failures do not crash
  training.
- **PPOConfig / SACConfig API** is analogous to SB3's constructor interface, but with
  distributed configuration:

```python
from ray.rllib.algorithms.ppo import PPOConfig

config = (
    PPOConfig()
    .environment("BrainEnv-v0")
    .env_runners(num_env_runners=4)
    .evaluation(evaluation_num_env_runners=1)
)
algo = config.build_algo()
algo.train()
```

**When to escalate from SB3 to RLlib**:
- Episode throughput requirement exceeds single-process SB3 capacity.
- Need to train multiple agent policies simultaneously (MARL).
- Need distributed experience replay across multiple hosts.
- Total timesteps exceeds ~10M (practical threshold where Ray's overhead becomes worthwhile).

**Migration path**: SB3 and RLlib both implement the same underlying algorithms (PPO, SAC).
Policies trained in SB3 can be exported via ONNX and imported into RLlib `RLModule` with
minimal modification.

### 2.3 Input Schemas — Phase 6 Signal Contracts

The `learning-adaptation` module consumes two Phase 6 output schemas. Their exact JSON Schema
definitions need to be verified in `shared/schemas/`, but the following fields are confirmed
from `modules/group-iii-executive-output/`:

**`MotorFeedback` schema** (from Phase 6 `motor-output`):

```json
{
  "reward_signal": {
    "delta": <float>,          // TD error approximation
    "magnitude": <float>,      // raw reward value
    "source": <string>         // "task_completion" | "user_feedback" | "ethics_check"
  },
  "skill_feedback": {
    "error": <float>,          // cerebellar-track execution error (vs. expected)
    "task_type": <string>,     // identifies which policy/skill head to update
    "trajectory": [...]        // optional: list of (state, action) for HER
  }
}
```

**`RewardSignal` schema** (from Phase 5 §5.5 Motivation):

```json
{
  "magnitude": <float>,        // 0.0–1.0 intrinsic reward
  "valence": "positive|negative|neutral",
  "source_module": <string>,
  "timestamp": <ISO-8601>
}
```

**Action required**: verify `shared/schemas/motor-feedback.schema.json` and
`shared/schemas/reward-signal.schema.json` exist before implementation. If absent, they must be
landed in `shared/schemas/` first (per AGENTS.md "Schemas first" constraint).

### 2.4 Vector Store — `brain.learning-adaptation` Collection

Following AGENTS.md local-compute-first principle, the experience replay buffer will be backed
by ChromaDB (local), using `nomic-embed-text` (Ollama) to embed episode observations.

**Collection spec**:

| Field | Value |
|---|---|
| Collection name | `brain.learning-adaptation` |
| Backend | ChromaDB (local) |
| Embedding model | `nomic-embed-text` (Ollama) |
| Document type | Episode trajectory: `{"state": ..., "action": ..., "reward": ..., "next_state": ...}` |
| Metadata fields | `episode_id`, `task_type`, `reward_delta`, `timestamp`, `priority` |
| Sampling strategy | Prioritised by `reward_delta` magnitude (≈ prioritised experience replay) |

---

## 3. §7.2 Metacognition & Monitoring — Technology Deep Dives

### 3.1 OpenTelemetry Python SDK (Primary Observability Technology)

**Source**: `tech-opentelemetry-python.md` (opentelemetry.io/docs/languages/python)

OpenTelemetry (OTel) is the CNCF standard for distributed tracing, metrics, and logs. The
Workplan explicitly names it for §7.2 anomaly escalation. The Python SDK is the correct
technology because:

- **Status**: Traces=Stable, Metrics=Stable, Logs=Development (as of Jan 2026).
- **Python 3.9+** support — consistent with EndogenAI Python requirements.
- **Three signal types** all relevant to `metacognition`:
  - **Traces (spans)**: each task execution becomes a span; errors become span events with
    `error_detected=true` attribute.
  - **Metrics**: counters and gauges for `error_rate`, `confidence_score`,
    `reward_deviation_zscore`.
  - **Logs**: structured log emission via OTel log appender (feeds into existing OTel collector).

**Install pattern** (per AGENTS.md `uv run` convention):

```toml
# pyproject.toml
[project.dependencies]
opentelemetry-api = ">=1.20"
opentelemetry-sdk = ">=1.20"
opentelemetry-exporter-otlp = ">=1.20"           # sends to OTel collector (existing)
opentelemetry-exporter-prometheus = ">=0.41b0"    # scrape endpoint for Prometheus
```

**Key instrumentation pattern for `metacognition`**:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer("endogenai.metacognition")
meter = metrics.get_meter("endogenai.metacognition")

# Metrics
error_rate = meter.create_gauge("metacognition.error_rate_per_task")
confidence = meter.create_histogram("metacognition.task_confidence")
reward_deviation = meter.create_gauge("metacognition.reward_deviation_zscore")

# Span wrapping a task execution
with tracer.start_as_current_span("task.execute") as span:
    result = execute_task(task)
    delta = compute_reward_delta(result, expected)
    
    if abs(delta) > ANOMALY_THRESHOLD:
        span.set_attribute("error_detected", True)
        span.add_event("anomaly_detected", {"delta": delta, "task": task.id})
    
    confidence.record(compute_confidence(result))
    reward_deviation.set(compute_zscore(delta, rolling_mean, rolling_std))
```

**Export chain (existing infrastructure)**:

```
metacognition module
  → OTel Python SDK
    → OTLP exporter → OTel Collector (observability/otel-collector.yaml)
      → Prometheus remote_write → Prometheus (observability/prometheus.yml)
        → Grafana dashboard (observability/grafana/)
          → AlertManager → escalation trigger
```

The full observability stack is already live (`docker compose up -d` includes it). The
`metacognition` module plugs directly into this existing chain.

### 3.2 Prometheus (Metrics Backend for Alerting)

**Source**: `tech-prometheus.md` (prometheus.io/docs/introduction/overview)

Prometheus is already deployed in the EndogenAI stack (`observability/prometheus.yml`). Its role
in §7.2 is as the **alerting backend** that implements the ACC escalation pathway.

**Key characteristics relevant to `metacognition`**:
- **Multi-dimensional data model**: metrics identified by name + label set
  (e.g. `metacognition_error_rate{task_type="agent_response", module="executive-agent"}`).
- **PromQL**: allows threshold expressions directly in alerting rules
  (`metacognition_confidence_score < 0.7 for 5m`).
- **Alertmanager** integration: when an alerting rule fires, the Alertmanager routes the alert
  — this is the biological ACC "escalation" pathway (PFC → external alarm).
- **Pull model**: Prometheus scrapes the OTel Prometheus exporter endpoint; no push needed from
  the metacognition module.

**Alert rule pattern for `metacognition`**:

```yaml
# observability/prometheus-rules/metacognition.yml (to be created)
groups:
  - name: metacognition
    rules:
      - alert: ConfidenceScoreLow
        expr: metacognition_task_confidence < 0.7
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Task confidence below threshold for 5 minutes"
          
      - alert: AnomalyRateHigh
        expr: rate(metacognition_anomaly_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Anomaly rate exceeding 10% over 5-minute window"
```

### 3.3 Vector Store — `brain.metacognition` Collection

**Collection spec**:

| Field | Value |
|---|---|
| Collection name | `brain.metacognition` |
| Backend | ChromaDB (local) |
| Embedding model | `nomic-embed-text` (Ollama) |
| Document type | Monitoring event: `{"task_id": ..., "confidence": ..., "error_detected": ..., "reward_delta": ...}` |
| Metadata fields | `task_type`, `module_source`, `timestamp`, `alert_fired`, `anomaly_score` |
| Query use | Historical anomaly pattern retrieval for trend analysis |

---

## 4. Interfaces with Shared Infrastructure

### 4.1 MCP (Model Context Protocol) — Context Exchange

Both Phase 7 modules expose MCP resources and tools following the module contract in AGENTS.md:

**`learning-adaptation` MCP resources:**
- `resource://brain.learning-adaptation/policy/current` — current policy checkpoint
- `resource://brain.learning-adaptation/replay-buffer/stats` — replay buffer metrics
- `resource://brain.learning-adaptation/performance/history` — episode reward history

**`learning-adaptation` MCP tools:**
- `tool://learning-adaptation/train` — trigger a training step with provided `MotorFeedback`
- `tool://learning-adaptation/predict` — infer action from current policy given observation
- `tool://learning-adaptation/promote-habit` — freeze current policy checkpoint as habit

**`metacognition` MCP resources:**
- `resource://brain.metacognition/confidence/current` — current system-wide confidence score
- `resource://brain.metacognition/anomalies/recent` — last N anomaly events
- `resource://brain.metacognition/alerts/active` — active Prometheus alert state

**`metacognition` MCP tools:**
- `tool://metacognition/evaluate` — run metacognitive evaluation of a task result
- `tool://metacognition/configure-threshold` — update confidence threshold in `monitoring.config.json`
- `tool://metacognition/report` — generate a metacognitive summary report

### 4.2 A2A (Agent-to-Agent) — Task Delegation

**`learning-adaptation`** may receive A2A task requests from:
- Phase 6 `executive-agent` requesting policy adaptation after a failed execution.
- Phase 6 `motor-output` sending batch `MotorFeedback` for offline replay.

**`metacognition`** may send A2A tasks to:
- Phase 6 `executive-agent` requesting behavioural correction when anomaly threshold exceeded.
- External monitoring/alerting agents (future phases).

### 4.3 Configuration Files

Per the Workplan, each module has a named config file:

| Module | Config file | Key fields |
|---|---|---|
| `learning-adaptation` | `learning.config.json` | `algorithm`, `total_timesteps_per_run`, `replay_buffer_size`, `habit_threshold_episodes`, `cerebellar_loss_weight` |
| `metacognition` | `monitoring.config.json` | `confidence_threshold`, `anomaly_zscore_threshold`, `alert_window_minutes`, `rolling_window_size` |

---

## 5. Dependency Summary

### 5.1 New Python Dependencies (per module `pyproject.toml`)

**`learning-adaptation`**:
```toml
[project.dependencies]
stable-baselines3 = ">=2.3"
gymnasium = ">=0.29"
torch = ">=2.0"                # already required by SB3
opentelemetry-api = ">=1.20"
opentelemetry-sdk = ">=1.20"
opentelemetry-exporter-otlp = ">=1.20"
chromadb = ">=0.5"             # shared vector store adapter
```

**`metacognition`**:
```toml
[project.dependencies]
opentelemetry-api = ">=1.20"
opentelemetry-sdk = ">=1.20"
opentelemetry-exporter-otlp = ">=1.20"
opentelemetry-exporter-prometheus = ">=0.41b0"
chromadb = ">=0.5"             # metacognition collection
```

### 5.2 No New Services Required

Both modules integrate with the existing docker-compose stack:
- ChromaDB: already running.
- Prometheus: already running (`observability/prometheus.yml`).
- OTel Collector: already running (`observability/otel-collector.yaml`).
- Grafana: already running (`observability/grafana/`).
- Ollama: already running (for `nomic-embed-text` embeddings).

RLlib is an optional scale path and requires `ray[rllib]` — this introduces a Ray cluster
dependency if enabled. Defer to Phase 7 implementation if scale is needed.

---

## 6. Open Technical Questions for Phase Executive

1. **Gymnasium environment design**: what is the `observation_space` and `action_space` for the
   `BrainEnv` adapter? The observation must encode the current agent state (working memory
   contents + last Phase 6 output); the action must be a structured output parameter adjustment.
   This is the most architecturally novel part of Phase 7 and needs explicit design decisions.

2. **Policy persistence format**: SB3 saves zip-archives; should policy checkpoints be stored in
   `brain.learning-adaptation` (ChromaDB) or as model files in local storage? The former enables
   semantic retrieval of "best policy for task type X"; the latter is simpler.

3. **OTel Collector routing**: the existing `otel-collector.yaml` may need a new pipeline
   configured for `metacognition` service. Confirm existing pipelines support the
   `endogenai.metacognition` service namespace before implementation.

4. **Schema verification**: `shared/schemas/motor-feedback.schema.json` and
   `reward-signal.schema.json` must exist before Phase 7 implementation begins. If absent,
   block Phase 7 and add schema creation to the workplan as a prerequisite step.

5. **RLlib decision trigger**: at what scale threshold should the Phase Executive choose RLlib
   over SB3? Recommend a measurable criterion (e.g. "if episode collection takes > 10s per
   training step, escalate to RLlib") rather than an upfront architecture choice.
