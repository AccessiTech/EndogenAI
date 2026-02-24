---
id: neuroanatomy-thalamus
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-i-signal-processing/attention-filtering
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - thalamus
  - attention
  - gating
  - relay
  - group-i
---

# Thalamus

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-i-signal-processing/attention-filtering`

The **Thalamus** provides the neuroanatomical reference for the brAIn **Attention & Filtering Layer** — the gating and routing hub for all incoming signals.

## Function

The thalamus is the principal subcortical relay center for nearly all sensory and motor signals traveling to and from the cerebral cortex:

- **Sensory relay**: receives input from all sensory modalities (except olfaction) and routes signals to appropriate cortical areas
- **Attentional gating**: regulates signal transmission based on arousal state and attention — suppresses irrelevant signals and amplifies salient ones
- **Consciousness regulation**: modulates cortical arousal and the sleep–wake cycle
- **Bidirectional coupling**: receives substantial feedback projections from the cortex, enabling top-down modulation of incoming signals

Key nuclei:
- **Lateral Geniculate Nucleus (LGN)**: visual relay
- **Medial Geniculate Nucleus (MGN)**: auditory relay
- **Ventral Posterior Nucleus**: somatosensory relay
- **Pulvinar**: association relay; integrates multimodal signals; involved in attention
- **Reticular Nucleus**: inhibitory shell around thalamus; regulates inter-thalamic gating

## Inputs From

- Sensory periphery (via ascending tracts)
- Cerebral cortex (top-down feedback projections)
- Brainstem (arousal and modulatory signals from reticular formation)
- Cerebellum and basal ganglia (motor coordination feedback)

## Outputs To

- Sensory cortices (primary relayed signals)
- Prefrontal cortex (attention and working memory modulation)
- Anterior cingulate cortex (conflict and error monitoring)

## Key Design Notes

- **Salience scoring**: the Attention & Filtering Layer must score incoming signals for relevance given current goals — analogous to thalamic gating.
- **Top-down modulation interface**: the Executive / Agent Layer dispatches attention directives downward; this layer must expose a control interface for receiving and applying those directives.
- **Noise suppression**: signals that fall below a configurable salience threshold should be discarded or deprioritized before reaching higher layers.
- **Routing table**: like the thalamus's nucleus-specific projections, the layer should route signals to the appropriate downstream module based on modality and content type.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
