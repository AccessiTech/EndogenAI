# Affective / Motivational Layer

**Brain analogy**: Limbic System (Amygdala · Nucleus Accumbens · Hypothalamus)
**Module ID**: `affective`
**Group**: II — Cognitive Processing
**A2A endpoint**: `http://localhost:8205`
**MCP endpoint**: `http://localhost:8305`
**Vector store collection**: `brain.affective`

## Purpose

The Affective / Motivational Layer generates reward signals, computes emotional weighting, and
emits drive-based urgency scores that modulate memory consolidation and decision-making priorities
throughout the cognitive architecture. It is the EndogenAI analogue of the mammalian limbic
system — encoding dopaminergic reward prediction error (RPE), nucleus accumbens incentive
salience, and hypothalamic drive variables (urgency, novelty, threat).

## Interface

### A2A Tasks

| Task type | Description |
|-----------|-------------|
| `emit_reward_signal` | Generate and store a `RewardSignal`; dispatch boost to working memory |
| `get_drive_state` | Return current urgency / novelty / threat snapshot |
| `update_drive` | Increment or decrement a drive variable |
| `dispatch_boost` | Send importance-score boost for a given `RewardSignal` |
| `compute_rpe` | Compute reward prediction error between observed and expected values |

### MCP Tools

| Tool name | Description |
|-----------|-------------|
| `affective.emit_reward_signal` | Generate, store, and broadcast a reward signal |
| `affective.compute_rpe` | Compute RPE |
| `affective.get_drive_state` | Return drive variable snapshot |
| `affective.update_drive` | Update a drive variable |
| `affective.combine_signals` | Weighted combination of drive signals |

## Configuration

### `drive.config.json`
| Field | Default | Description |
|-------|---------|-------------|
| `urgencyThreshold` | `0.7` | Urgency level above which prioritisation cues are dispatched |
| `noveltyDecayRate` | `0.1` | Exponential decay rate applied to novelty each processing cycle |
| `curiosityBoostFactor` | `1.5` | Multiplier applied to novelty for curiosity-adjusted score |
| `drivePersistedAcrossSessions` | `false` | Whether drive state survives session boundaries |

### `vector-store.config.json`
| Field | Default | Description |
|-------|---------|-------------|
| `backend` | `chromadb` | Vector store backend |
| `collection` | `brain.affective` | Collection name |
| `host` | `localhost` | ChromaDB host |
| `port` | `8000` | ChromaDB port |

## Cross-Module Dependencies

- **working-memory** (`http://localhost:8201`): receives `apply_affective_boost` A2A tasks when
  high-valence reward signals are emitted (routed via `infrastructure/adapters/bridge.ts`).
- **brain.affective** collection in ChromaDB: receives embedded reward signal history and
  emotional state snapshots.

## Neuroscience Derivation

| Biological mechanism | Implementation |
|----------------------|---------------|
| Dopamine RPE (VTA phasic burst) | `compute_rpe(signal_value, expected_value)` — positive = unexpected reward, negative = unexpected penalty |
| Incentive salience (nucleus accumbens) | `urgency` drive type driving priority re-ranking in working-memory loader |
| BLA emotional tagging → hippocampal amplification | `RewardSignal.associatedMemoryItemId` links to co-occurring memory; `WeightingDispatcher` boosts `importanceScore` |
| Hypothalamus drive variables | `DriveState` with urgency, novelty, threat; configurable in `drive.config.json` |

## Deployment

```bash
# Install dependencies
cd modules/group-ii-cognitive-processing/affective && uv sync

# Run checks
uv run ruff check .
uv run mypy src/
uv run pytest tests/ -m "not integration" -q

# Integration tests (requires ChromaDB + Ollama)
uv run pytest tests/ -m integration -q
```
