---
id: neuroanatomy-limbic-system
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-ii-cognitive-processing/affective
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - limbic-system
  - amygdala
  - affective
  - motivation
  - reward
  - group-ii
---

# Limbic System

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-ii-cognitive-processing/affective`

The **Limbic System** provides the neuroanatomical reference for the brAIn **Affective / Motivational Layer** — the
generator of reward signals, emotional weighting, and drive modulation.

## Function

The limbic system is a set of brain structures that support emotion, behavior, motivation, and long-term memory. Its key
constituents and functions include:

- **Amygdala**: emotional processing (especially fear and reward); rapid threat detection; emotional tagging of
  memories; modulates hippocampal encoding strength
- **Hypothalamus**: homeostasis, circadian rhythm, autonomic regulation, endocrine control — the "drive generator"
  (hunger, thirst, arousal, sex)
- **Nucleus Accumbens** (ventral striatum): reward, motivation, reinforcement learning — the "pleasure center"
- **Anterior Cingulate Cortex (ACC)**: error detection, conflict monitoring, emotional regulation, pain processing
- **Orbitofrontal Cortex (OFC)**: reward evaluation, decision-making under uncertainty, impulse control
- **Cingulate Cortex (broadly)**: emotion regulation, learning, memory

## Inputs From

- Sensory cortices and thalamus (raw affective-relevant stimuli)
- Hippocampus (contextual and episodic memory for emotional valuation)
- Prefrontal cortex (top-down emotional regulation)
- Brainstem (autonomic and neuromodulatory inputs: dopamine, serotonin, norepinephrine)

## Outputs To

- Prefrontal cortex (prioritization cues, urgency signals)
- Hippocampus (emotional tagging strength — strong emotions → stronger encoding)
- Hypothalamus (endocrine / autonomic response initiation)
- Striatum (reinforcement signal dispatch)

## Key Design Notes

- **Reward signal generation**: the Affective / Motivational Layer must generate reward signals and urgency scores that
  modulate memory consolidation and decision-making — analogous to dopaminergic reward prediction error.
- **Emotional weighting**: all memory items and reasoning steps should carry an affective valence score so they can be
  prioritized appropriately.
- **Drive-based prioritization**: implement configurable "drive" variables (urgency, novelty, threat) that bias goal
  selection in the Executive Layer.
- **Top-down regulation interface**: the Executive / Agent Layer should be able to attenuate or amplify affective
  signals (emotional self-regulation).
- **Vector store**: embed reward signal history and emotional state snapshots into `brain.affective`.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
