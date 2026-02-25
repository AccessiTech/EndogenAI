---
id: neuroanatomy-hippocampus
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-ii-cognitive-processing/memory/working-memory
  - modules/group-ii-cognitive-processing/memory/short-term-memory
  - modules/group-ii-cognitive-processing/memory/long-term-memory
  - modules/group-ii-cognitive-processing/memory/episodic-memory
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - hippocampus
  - memory
  - temporal-lobe
  - limbic
  - group-ii
---

# Hippocampus

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to:

- `modules/group-ii-cognitive-processing/memory/working-memory`
- `modules/group-ii-cognitive-processing/memory/short-term-memory`
- `modules/group-ii-cognitive-processing/memory/long-term-memory`
- `modules/group-ii-cognitive-processing/memory/episodic-memory`

The **Hippocampus** provides the neuroanatomical reference for the entire brAIn **Memory Layer** — the substrate for
encoding, consolidating, and retrieving information across all timescales.

## Function

The hippocampus is a curved, seahorse-shaped structure located in the medial temporal lobe, critical for:

- **Declarative memory formation**: encoding new episodic (event-based) and semantic (fact-based) memories from
  short-term representations
- **Spatial navigation and cognitive maps**: constructing and using spatial and conceptual "maps" (place cells, grid
  cells)
- **Memory consolidation**: transferring memories from short-term to long-term storage, especially during sleep
  (sharp-wave ripples)
- **Pattern completion vs. pattern separation**: CA3 completes partial patterns (retrieval); dentate gyrus separates
  similar patterns (discrimination)
- **Episodic replay**: temporally-ordered re-activation of memory sequences supporting learning and planning

Key subregions:

- **CA1**: output relay; comparison of expected vs. retrieved
- **CA3**: associative memory completion (recurrent connections)
- **Dentate Gyrus (DG)**: pattern separation; novelty detection; neurogenesis
- **Entorhinal Cortex (EC)**: primary cortical interface; receives processed sensory data; two-way gateway to neocortex

## Inputs From

- Entorhinal cortex (multimodal sensory integration)
- Septal nuclei (cholinergic modulation, attention, arousal)
- Prefrontal cortex (goal-directed memory retrieval)
- Amygdala (emotional tagging of memories)

## Outputs To

- Entorhinal cortex → neocortex (consolidation pathway)
- Prefrontal cortex (retrieved context for planning)
- Amygdala (emotional context)

## Key Design Notes

- **Timescale stratification**: the brAIn Memory Layer mirrors the hippocampal pipeline across four timescales — working
  (immediate), short-term (session), long-term (persistent), episodic (ordered events).
- **Retrieval-augmented assembly**: working memory loads relevant context from short-term and long-term stores per turn,
  respecting token budgets — analogous to hippocampal pattern completion feeding prefrontal working memory.
- **Consolidation pipeline**: items evicted from working/short-term memory trigger encoding into episodic and long-term
  stores — mirroring hippocampal consolidation.
- **Vector store backend**: all memory collections use ChromaDB (default) or Qdrant (production) via the shared vector
  store adapter.
- **Embedding model**: `nomic-embed-text` via Ollama for all local embeddings.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
