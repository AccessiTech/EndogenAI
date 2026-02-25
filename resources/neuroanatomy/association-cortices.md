---
id: neuroanatomy-association-cortices
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-i-signal-processing/perception
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - association-cortex
  - perception
  - feature-extraction
  - multimodal
  - group-i
---

# Association Cortices

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-i-signal-processing/perception`

The **Association Cortices** provide the neuroanatomical reference for the brAIn **Perception Layer** — the site of
meaningful feature extraction and multimodal integration.

## Function

Association cortices occupy the regions of the cerebral cortex that integrate information from multiple primary sensory
and motor areas to produce complex perceptions, representations, and concepts:

- **Unimodal association areas**: immediately adjacent to primary sensory cortices; perform higher-order processing
  within a single modality (e.g., visual object recognition in inferotemporal cortex)
- **Heteromodal (multimodal) association areas**: integrate signals from multiple modalities; support language
  comprehension, spatial awareness, and abstract reasoning
  - **Parietal association cortex**: spatial perception, body schema, attention
  - **Temporal association cortex**: object recognition, semantic memory, language comprehension (Wernicke's area)
  - **Prefrontal association cortex**: executive integration, working memory, decision prep

## Inputs From

- Primary sensory cortices (visual, auditory, somatosensory)
- Thalamic relay nuclei (pulvinar, mediodorsal)
- Hippocampus and entorhinal cortex (memory priors)

## Outputs To

- Prefrontal cortex (decision-making, planning)
- Hippocampus (encoding perceived features into memory)
- Motor cortex (perception-to-action coupling)

## Key Design Notes

- **Feature extraction is semantic**: the Perception Layer assigns meaning — it is where raw signals become structured
  representations (objects, entities, intents, features).
- **Vector embedding target**: extracted perceptual representations should be embedded into the `brain.perception`
  vector collection.
- **Multimodal fusion pipeline**: the layer must merge signals from different modalities into a unified representation,
  not process them in isolation.
- **Priors from memory**: support top-down prior injection from the Long-Term Memory module to bias perception toward
  known patterns.
- **LLM routing**: language understanding pipelines at this layer route all inference through LiteLLM.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
