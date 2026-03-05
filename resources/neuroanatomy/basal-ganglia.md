---
id: neuroanatomy-basal-ganglia
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-03-02
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-iii-executive-output/executive-agent
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - basal-ganglia
  - executive-agent
  - goal-stack
  - action-selection
  - group-iii
---

# Basal Ganglia

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-iii-executive-output/executive-agent`

The **Basal Ganglia** (striatum, globus pallidus, subthalamic nucleus, substantia nigra) provides the neuroanatomical
reference for the **goal commitment, capacity enforcement, and abort mechanisms** within the frankenbrAIn Executive / Agent
Layer — specifically the `goal_stack.py` lifecycle transitions driven by the direct, indirect, and hyperdirect
corticobasal pathways.

## Function

The basal ganglia are a group of subcortical nuclei involved in action selection, reinforcement learning, and habit
vs. goal-directed behaviour gating. The canonical model describes three competing inhibitory pathways:

- **Direct pathway** (Go): striatum D1 neurons → GPi inhibition lifted → thalamus disinhibited → cortex executes
  action. Net effect: facilitates the selected action (positive selection).
- **Indirect pathway** (NoGo): striatum D2 neurons → GPe → STN → GPi → thalamus inhibited → action suppressed.
  Net effect: suppresses competing actions (surround inhibition).
- **Hyperdirect pathway** (Stop): cortex → STN → GPi directly; fastest pathway; can abort an executing action
  before it completes. Net effect: broad suppression, allowing reassessment.

Additional structures:

- **Striatum (caudate + putamen)**: input nucleus; receives dopaminergic RPE signal from substantia nigra pars
  compacta (SNc). Caudate = cognitive/goal loop; putamen = motor loop.
- **Nucleus accumbens (ventral striatum)**: reward and motivation processing; value-based filtering of goal
  candidates.
- **Substantia nigra pars compacta (SNc)**: dopamine RPE source; trains both direct and indirect pathways via
  temporal difference learning.
- **Subthalamic nucleus (STN)**: receives hyperdirect cortical input; sole excitatory nucleus in the BG; mediates
  the reactive stop signal.

## Inputs From

- Prefrontal and premotor cortex (cognitive and motor loops)
- Limbic system / ventral tegmental area (reward and motivation signals)
- Thalamus (centromedian and parafascicular nuclei)
- Somatosensory and parietal cortex

## Outputs To

- Thalamus (ventroantero-lateral complex → cortex; action selection relay)
- Superior colliculus (motor execution gating)
- Brainstem motor centres

## Key Design Notes

- **Direct pathway → `commit_intention`**: when a goal is selected by the BDI deliberation loop and OPA policy
  returns `allow: true`, `goal_stack.commit(goal_id)` transitions the goal `EVALUATING → COMMITTED` and pushes it
  to `agent-runtime` via A2A `execute_intention`. This is the disinhibition signal — cortex executes the selected
  goal because the inhibitory gate has been lifted.

- **Indirect pathway → `enforce_capacity`**: when `len(COMMITTED + EXECUTING) >= maxActiveGoals`,
  `goal_stack.enforce_capacity()` defers the lowest-priority PENDING goal — surround inhibition preventing
  competing goals from executing simultaneously.

- **Hyperdirect pathway → `abort_goal`**: the `abort_goal` A2A task handler and `goal_stack.abort(goal_id, reason)`
  immediately transition any state → `DEFERRED` and send Temporal Signal("abort") to the running Workflow. This is
  the fastest pathway — it acts before committed goals complete, analogous to the STN-mediated reactive Stop signal.

- **Dopamine RPE → priority update**: `feedback.py` receives `MotorFeedback.reward_signal` and calls
  `goal_stack.update_score(goal_id, reward_delta)`, adjusting goal `priority` (float 0–1) and re-sorting the stack.
  This implements a temporal difference learning analogue: better-than-expected outcomes increase the priority of
  similar future goals.

- **Caudate cognitive loop** (goal-directed): the `brain.executive-agent` ChromaDB collection stores past goal
  outcomes and BDI plan templates; `identity.py` retrieves relevant plans semantically — analogous to caudate
  learning goal-directed action sequences.

- **BG circuit is not a vector store**: the basal ganglia perform competitive evaluation and selection — not storage.
  In Phase 6, this maps exclusively to the FSM transition logic in `goal_stack.py` and the deliberation engine in
  `deliberation.py`.

## Phase 6 Implementation References

| Pathway / Structure | Phase 6 construct | File |
|---|---|---|
| Direct pathway (Go) | `commit_intention` — EVALUATING → COMMITTED | `goal_stack.py` |
| Indirect pathway (NoGo) | `enforce_capacity` — defer lowest-priority PENDING | `goal_stack.py` |
| Hyperdirect (Stop) | `abort_goal` — immediate Temporal Signal("abort") | `goal_stack.py`, `a2a_handler.py` |
| SNc dopamine RPE | `update_score(reward_delta)` after `MotorFeedback` | `feedback.py`, `goal_stack.py` |
| Nucleus accumbens | Value scoring of goal candidates in option generation | `deliberation.py` |
| Caudate cognitive loop | Semantic retrieval of past BDI plan templates | `identity.py`, `store.py` |

See `docs/research/phase-6-neuroscience-executive-output.md §2` for full derivation.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
