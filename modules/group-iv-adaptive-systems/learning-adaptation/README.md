# learning-adaptation

**Phase 7 — §7.1 Learning & Adaptation Layer**
**Port:** 8170
**Group:** `group-iv-adaptive-systems`

---

## Purpose

The Learning & Adaptation Layer implements reinforcement learning–driven goal-priority adaptation for the EndogenAI cognitive architecture. It:

1. **Wraps the `MotorFeedback` stream** as a `gymnasium.Env` (`BrainEnv`)
2. **Trains a PPO policy** (Stable-Baselines3) to adjust `ExecutiveGoal.priority_weight` values
3. **Stores experience** in a ChromaDB-backed `ReplayBuffer` with priority sampling
4. **Promotes stable policies** to habit checkpoints via `HabitManager`

### Neuroanatomical Analogues

| Component | Analogue |
|-----------|----------|
| `BrainEnv` + `PolicyTrainer` (PPO) | Basal ganglia actor-critic — dopamine-gated direct/indirect pathway balance |
| `SkillFeedbackCallback` | Cerebellum — supervised error correction on deviation-heavy transitions |
| `ReplayBuffer` (ChromaDB) | Hippocampus — episodic memory replay driving offline policy improvement |
| `HabitManager` | Dorsolateral striatum — consolidation of well-practised sequences into automatic routines |

---

## Interface

This module exposes both an **A2A** (task delegation) interface and an **MCP** (context resource) interface.

### A2A Interface

**Endpoint:** `POST http://localhost:8170/tasks` (JSON-RPC 2.0)

### Inbound Tasks

| Task | Description |
|------|-------------|
| `adapt_policy` | Accept `MotorFeedback` (single or batch), add to replay buffer, trigger training |
| `replay_episode` | Accept `list[MotorFeedback]`, store in replay buffer for deferred training |

### Outbound Tasks

| Task | Destination | Trigger |
|------|-------------|---------|
| `habit_promoted` | `executive-agent` (port 8161) | When `HabitManager` promotes a stable policy |
| `adaptation_failed` | `metacognition` (port 8171) | When a training step errors critically |

---

### MCP Interface

**Resources:**

| URI | Description |
|-----|-------------|
| `resource://brain.learning-adaptation/policy/current` | Active PPO policy summary |
| `resource://brain.learning-adaptation/replay-buffer/stats` | Replay buffer statistics |
| `resource://brain.learning-adaptation/habits/catalog` | All promoted habit checkpoints |

**Tools:**

| Tool | Input | Output |
|------|-------|--------|
| `train` | `{motor_feedback: list}` | `TrainingResult` |
| `predict` | `{observation: list[float]}` | `ActionPrediction` |
| `promote-habit` | `{task_type: string}` | `HabitRecord` |

---

## Observation & Action Space (Decision 2 Option A)

**Observation** (12 floats with K=4 goal classes):
```
[success_rate, mean_deviation, escalation_rate,
 task_type_onehot[default, query, action, planning],
 channel_success_rate[http, a2a, file, render, control-signal]]
```

**Action:** `Box(4 floats, clip=[-0.2, +0.2])` — signed delta per goal class applied to `ExecutiveGoal.priority_weight`

**Episode boundary:** one BDI planning cycle (goal COMPLETED or goal escalated/FAILED)

**Reward:** `MotorFeedback.reward_signal.value`

---

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `algorithm` | `"PPO"` | RL algorithm (currently only PPO supported) |
| `total_timesteps_per_run` | `10000` | PPO `learn()` timesteps per training call |
| `replay_buffer_size` | `1000` | Max episodes in ChromaDB replay buffer |
| `habit_threshold_success_rate` | `0.95` | Min consecutive success rate for habit promotion |
| `habit_threshold_episode_count` | `20` | Number of consecutive episodes required |
| `shadow_policy_enabled` | `true` | Maintain an offline shadow policy |
| `shadow_promotion_eval_episodes` | `5` | Consecutive evals above threshold before promotion |
| `shadow_promotion_threshold` | `0.8` | Mean reward threshold for shadow promotion |
| `async_replay_interval_seconds` | `30` | Background replay training loop interval |
| `goal_classes` | `["default","query","action","planning"]` | K goal classes for onehot encoding |
| `observation_window_size` | `20` | Rolling window size for observation state aggregation |
| `chromadb_url` | `"http://localhost:8000"` | ChromaDB endpoint for replay buffer |
| `metacognition_url` | `"http://localhost:8171"` | metacognition A2A endpoint for failure notifications |
| `executive_agent_url` | `"http://localhost:8161"` | executive-agent A2A endpoint for habit promotion |

---

## Training Loop

1. `MotorFeedback` arrives via A2A `adapt_policy`
2. Episode is persisted to ChromaDB (`brain.learning-adaptation`)
3. `BrainEnv.push_feedback()` updates rolling observation state
4. Shadow policy is trained via SB3 PPO `.learn()`
5. `SkillFeedbackCallback._on_rollout_end()` samples high-deviation episodes for cerebellar correction
6. Shadow policy is evaluated every training step
7. After N consecutive above-threshold evaluations, shadow is promoted to active
8. `HabitManager` tracks per-task success streaks; promotes stable policies to habit checkpoints
9. Background loop (every `async_replay_interval_seconds`) samples from buffer and retrains

---

## Deployment

```bash
cd modules/group-iv-adaptive-systems/learning-adaptation
uv sync
uv run python -m learning_adaptation.server
```

**Dependencies:** ChromaDB at `http://localhost:8000`, Ollama at `http://localhost:11434` (for embeddings)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LEARNING_ADAPTATION_PORT` | `8170` | Server port |
| `CHROMADB_URL` | `http://localhost:8000` | ChromaDB endpoint |
| `EXECUTIVE_AGENT_URL` | `http://localhost:8161` | executive-agent A2A endpoint |
| `METACOGNITION_URL` | `http://localhost:8171` | metacognition A2A endpoint |

---

## Development

```bash
# Install
cd modules/group-iv-adaptive-systems/learning-adaptation
uv sync

# Lint
uv run ruff check .

# Type-check
uv run mypy src/

# Test (no live services required)
uv run pytest
```

## Testing

Framework: **pytest**. Coverage threshold: **80%** (enforce with `pytest-cov` once installed — see P05).

```bash
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# No external services required for unit tests
SKIP_INTEGRATION_TESTS=1 uv run pytest -m "not integration" -q
```

Estimated coverage: ~50% (HIGH gap). Known gaps — no tests yet for:
- `src/training/skill_feedback_callback.py` (0%) — see [workplan](../../../docs/test-upgrade-workplan.md) P21
- `src/a2a_handler.py` — see P09
- `src/mcp_tools.py` — see P10

Note: existing test suite (`test_brain_env`, `test_habit_manager`, `test_replay_buffer`, `test_trainer`) uses
correct `async` patterns and is a canonical example for the codebase.
