---
id: neuroanatomy-motor-cortex
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-03-02
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-iii-executive-output/motor-output
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - motor-cortex
  - motor-output
  - action-dispatch
  - corollary-discharge
  - group-iii
---

# Motor Cortex

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-iii-executive-output/motor-output`

The **Motor Cortex** (primary motor cortex M1, premotor cortex PMd/PMv, and supplementary motor area SMA) provides
the neuroanatomical reference for the frankenbrAIn **Motor / Output / Effector Layer** — the module responsible for
dispatching parameterised actions into the environment, selecting the correct output channel, and emitting structured
feedback after every action.

## Function

The motor cortex occupies the posterior portion of the frontal lobe (precentral gyrus and adjacent areas) and is the
primary substrate for voluntary movement generation:

- **Primary Motor Cortex (M1, BA 4)**: generates the final motor commands sent to muscles via the corticospinal tract.
  Uses population coding — many neurons each contribute a weighted vote to the final movement direction and force.
- **Dorsal Premotor Cortex (PMd)**: context-dependent movement preparation; selects the appropriate movement based on
  external cues and stored rules. Evaluates which motor program to execute given the current context.
- **Ventral Premotor Cortex (PMv / area F5)**: object-affordance matching; canonical neurons encode graspable
  properties of objects. Corollary discharge origin: PMv sends a copy of the intended action command to the cerebellum
  before M1 executes.
- **Supplementary Motor Area (SMA proper)**: internally-driven movement sequences; programs complex multi-step actions
  that proceed without external cues. Bereitschaftspotential (readiness potential) originates here.

Key functional principles:

- **Population coding** (M1): no single neuron commands an action; the population vector averages across many neurons'
  preferred directions. Module analogue: `dispatch_concurrent` in `dispatcher.py` — multiple channel handlers
  contribute in parallel.
- **Corollary discharge** (PMv): the brain sends a copy of the outgoing motor command back internally, before the
  movement executes, to allow comparison with predicted sensory consequences. Module analogue: `predicted_outcome`
  field in `ActionSpec` emitted before dispatch.
- **Forward model** (cerebellum paired with M1): M1 sends efference copy to cerebellar forward model, which predicts
  proprioceptive feedback. Module analogue: `MotorFeedback.deviation_score` computed from predicted vs. actual.

## Inputs From

- Premotor and supplementary motor areas (planning and sequencing)
- Prefrontal cortex (goal-directed top-down modulation)
- Thalamus (ventrolateral nucleus — relay from basal ganglia and cerebellum)
- Somatosensory cortex (proprioceptive feedback — loop back)
- Basal ganglia via thalamus (action selection, gating)

## Outputs To

- Spinal cord (corticospinal tract — direct muscle activation)
- Brainstem motor nuclei
- Cerebellum (efference copy for forward model prediction)
- Basal ganglia (internal monitoring loop)

## Key Design Notes

- **`dispatcher.py`** (M1 analogue): executes the final action; implements population-coding parallel dispatch via
  `asyncio.gather`; wraps every execution in three-tier error policy.
- **`channel_selector.py`** (PMd analogue): context-dependent channel routing — selects `http`, `a2a`, `file`,
  `render`, or `control-signal` based on `ActionSpec.type` and current context state.
- **Corollary discharge** (PMv analogue): before executing, `dispatcher.py` emits a `pre_action_event` log entry
  carrying `predicted_outcome`; this enables downstream deviation scoring.
- **`feedback.py`** (spinocerebellum / real-time correction): after every dispatch, `feedback.py` computes
  `deviation_score` (cosine similarity of predicted vs. actual) and pushes `MotorFeedback` to executive-agent
  A2A `receive_feedback` immediately — active push, not poll.
- **Three-tier error policy** (`error_policy.py`): tier 1 = transient retry (backoff); tier 2 = circuit-breaker
  (degrade gracefully); tier 3 = escalate (push `MotorFeedback { escalate: true }` to executive-agent).
- **No vector store**: `motor-output` does not maintain its own ChromaDB collection — it is a pure effector.
  Historical feedback is retrievable via executive-agent's `brain.executive-agent` collection.
- **LiteLLM for render channel**: text/media rendering dispatches through LiteLLM (Ollama local default); no direct
  SDK calls.

## Phase 6 Implementation References

| Region | Phase 6 construct | File |
|---|---|---|
| M1 population coding | Concurrent `asyncio.gather` dispatch | `dispatcher.py` |
| PMd context selection | Channel routing by `ActionSpec.type` | `channel_selector.py` |
| PMv corollary discharge | `predicted_outcome` pre-action log event | `dispatcher.py` |
| SMA multi-step sequences | `dispatch_pipeline` batch method | `dispatcher.py` |
| Corticospinal tract | HTTP / A2A / file / render channel handlers | `channels/` |
| Spinocerebellum feedback | `deviation_score` + A2A push to executive | `feedback.py` |
| Tier 1–3 error policy | Retry / circuit-breaker / escalate | `error_policy.py` |

See `docs/research/phase-6-neuroscience-executive-output.md §4` for full derivation.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
