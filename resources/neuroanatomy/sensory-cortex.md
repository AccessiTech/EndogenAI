---
id: neuroanatomy-sensory-cortex
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-i-signal-processing/sensory-input
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - sensory
  - cortex
  - signal-processing
  - group-i
---

# Sensory Cortex

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-i-signal-processing/sensory-input`

The **Sensory Cortex** provides the neuroanatomical reference for the brAIn **Sensory / Input Layer** — the system's
interface with the external environment.

## Function

The sensory cortex comprises all cortical regions dedicated to receiving and performing initial processing of sensory
signals from the body and environment:

- **Somatosensory Cortex** (postcentral gyrus, parietal lobe): touch, pressure, pain, vibration, temperature,
  proprioception
- **Visual Cortex** (occipital lobe): processes retinal signals into spatial and feature representations
- **Auditory Cortex** (temporal lobe / insular cortex): processes sound frequency, rhythm, and speech
- **Gustatory Cortex**: taste signals relayed via thalamus
- **Olfactory Cortex**: processes smell via olfactory bulb

## Inputs From

- Peripheral sensory receptors (via thalamic relay — except olfaction)
- Thalamus (relay for all modalities except olfaction)
- Olfactory bulb (direct, bypasses thalamus)

## Outputs To

- Association cortices (higher-order feature integration)
- Thalamus (feedback modulation)
- Frontal lobe (voluntary attention direction)

## Key Design Notes

- **No semantic interpretation at this layer**: the Sensory / Input Layer normalizes, timestamps, and forwards signals —
  it does not assign meaning.
- **Modality-agnostic interface**: support text, image, audio, API events, and sensor streams via a unified signal
  envelope (see `shared/schemas/signal.schema.json`).
- **Receptive field mapping**: signals should carry metadata about their source modality and channel.
- **Low-level filtering only**: salience scoring and gating happen in the Attention & Filtering Layer (thalamus analogy)
  — not here.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
