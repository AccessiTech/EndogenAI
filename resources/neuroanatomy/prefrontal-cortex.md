---
id: neuroanatomy-prefrontal-cortex
version: 0.2.0
status: stub
authority: descriptive
last-reviewed: 2026-03-02
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-ii-cognitive-processing/reasoning
  - modules/group-iii-executive-output/executive-agent
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - prefrontal-cortex
  - reasoning
  - decision-making
  - planning
  - executive
  - bdi
  - group-ii
  - group-iii
---

# Prefrontal Cortex

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to:

- `modules/group-ii-cognitive-processing/reasoning` (Phase 5 — inference, causal planning, DSPy)
- `modules/group-iii-executive-output/executive-agent` (Phase 6 — BDI loop, OPA policy engine, identity)

The **Prefrontal Cortex** provides the neuroanatomical reference for two frankenbrAIn layers:

1. **Decision-Making & Reasoning Layer** (Phase 5): the site of logical inference, causal reasoning, planning, and
   conflict resolution — implemented via DSPy + LiteLLM in `modules/group-ii-cognitive-processing/reasoning`.
2. **Executive / Agent Layer** (Phase 6): identity, goal management, value-based deliberation, and policy enforcement
   — implemented via BDI loop + OPA in `modules/group-iii-executive-output/executive-agent`.

## Function

The prefrontal cortex (PFC) is the anterior portion of the frontal lobe, the most evolutionarily recent region of the
brain. It is responsible for the highest levels of cognitive control:

- **Dorsolateral PFC (DLPFC)**: working memory manipulation, abstract reasoning, planning, cognitive flexibility
- **Orbitofrontal Cortex (OFC)**: reward-based decision-making, impulse control, value computation under uncertainty
- **Ventromedial PFC (vmPFC)**: emotional decision-making, risk assessment, self-referential processing
- **Anterior Cingulate Cortex (ACC)**: conflict detection, error monitoring, attentional control, uncertainty processing
- **Inferior Frontal Gyrus (IFG)**: inhibitory control, language production (Broca's area), response suppression

Key functional capabilities:

- **Logical and causal reasoning**: deductive, inductive, abductive inference
- **Planning under uncertainty**: forward simulation, probabilistic reasoning, scenario evaluation
- **Conflict resolution**: weighing competing hypotheses, goals, or action plans
- **Cognitive flexibility**: switching between strategies, updating beliefs in light of new evidence

## Inputs From

- Thalamus (mediodorsal nucleus — integration relay)
- Hippocampus (retrieved memory context)
- Sensory and association cortices (perceptual representations)
- Limbic system (affective prioritization cues)
- Basal ganglia (action selection and habit suppression)

## Outputs To

- Premotor and motor cortex (action initiation)
- Thalamus (top-down attention modulation)
- Hippocampus (directing retrieval and encoding)
- Anterior cingulate cortex (performance monitoring)

## Key Design Notes

### Phase 5 — Reasoning Layer (`brain.reasoning`)

- **LLM routing mandatory**: all inference routes through LiteLLM — no direct SDK calls.
- **DSPy for structured reasoning**: use DSPy for logical, causal, and planning pipelines; Guidance for
  constrained/structured generation.
- **Inference traces**: embed all reasoning traces, plans, and causal models into `brain.reasoning` for auditability and
  long-term learning.
- **Uncertainty quantification**: produce not just decisions but confidence estimates and alternative hypotheses.
- **Top-down constraints from Executive**: goals, values, and policy constraints from executive-agent bound reasoning.

### Phase 6 — Executive / Agent Layer (`brain.executive-agent`)

- **DLPFC → goal stack**: active maintenance of committed goals; capacity constraint (`maxActiveGoals`)
  mirrors DLPFC working memory limits. Implemented in `goal_stack.py`.
- **OFC → value scoring**: goal candidates scored against current `RewardSignal` (value_score); implemented in
  `deliberation.py` option-generation phase.
- **vmPFC → fast heuristic pre-filter**: before full OPA deliberation, fast value-consistent check. Implemented
  in `deliberation.py`.
- **ACC → OPA violations**: `policy.py` maps OPA `violations[]` array to ACC conflict-detection signal; triggers
  escalation if unresolvable.
- **OPA policy engine**: standalone HTTP server at `localhost:8181`; three Rego policies (`identity.rego`,
  `goals.rego`, `actions.rego`). Hot-reload and Decision Log for observability.
- **BDI interpreter loop**: `deliberation.py` runs option-generation → deliberation → commit cycle per
  `deliberation_cycle_ms`.
- **Identity persistence**: `identity.py` holds `SelfModel`; append-only writes to `brain.executive-agent`
  (reconsolidation analogue).

## Phase 6 Implementation References

| Region | Phase 6 construct | File |
|---|---|---|
| DLPFC | Goal stack capacity + active maintenance | `goal_stack.py` |
| OFC | Value scoring in option generation | `deliberation.py` |
| vmPFC | Fast heuristic pre-filter | `deliberation.py` |
| ACC | OPA `violations[]` → conflict escalation | `policy.py` |
| IFG | Inhibitory control via `policy-decision.schema.json` | `policy.py` |

See `docs/research/phase-6-neuroscience-executive-output.md §2` for full derivation.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
