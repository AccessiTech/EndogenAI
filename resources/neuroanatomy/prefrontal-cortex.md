---
id: neuroanatomy-prefrontal-cortex
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-ii-cognitive-processing/reasoning
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - prefrontal-cortex
  - reasoning
  - decision-making
  - planning
  - group-ii
---

# Prefrontal Cortex

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-ii-cognitive-processing/reasoning`

The **Prefrontal Cortex** provides the neuroanatomical reference for the brAIn **Decision-Making & Reasoning Layer** —
the site of logical inference, causal reasoning, planning, and conflict resolution.

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

- **LLM routing mandatory**: all inference in the Decision-Making & Reasoning Layer routes through LiteLLM — no direct
  SDK calls.
- **DSPy for structured reasoning**: use DSPy for logical, causal, and planning pipelines; Guidance for
  constrained/structured generation.
- **Inference traces**: embed all reasoning traces, plans, and causal models into `brain.reasoning` for auditability and
  long-term learning.
- **Uncertainty quantification**: the layer must produce not just decisions but confidence estimates and alternative
  hypotheses.
- **Top-down constraints from Executive**: the Executive / Agent Layer supplies goals, values, and policy constraints
  that bound reasoning — analogous to prefrontal top-down control.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
