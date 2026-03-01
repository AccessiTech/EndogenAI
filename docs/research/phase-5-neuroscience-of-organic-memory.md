# Phase 5 Research Brief: Neuroscience of Organic Memory

> **Audience**: Phase 5 implementation agents and reviewers.  
> **Purpose**: Ground the six Group II modules in neuroscience literature before implementation begins.
> All descriptions are derived from research gathered for this phase — no content is invented.

---

## 1. Memory System Taxonomy

The brain does not use a single unified memory store. Memory is distributed across
anatomically distinct systems, each specialised for a different timescale,
representational format, and consolidation pathway:

| System | Timescale | Substrate | Key role |
|--------|-----------|-----------|----------|
| Working memory | Seconds | Prefrontal cortex (DLPFC, vlPFC) | Active context; online manipulation |
| Short-term / buffer memory | Minutes | Hippocampus + PFC | Transient retention; gateway to consolidation |
| Long-term memory (semantic) | Years–lifetime | Distributed neocortex | Decontextualised facts; hippocampus-independent after transfer |
| Episodic memory | Days–lifetime | Medial temporal lobe + hippocampus | Event sequences; may always require hippocampus |
| Procedural memory | Lifelong | Basal ganglia + cerebellum | Motor and habit learning — out of Phase 5 scope |

These systems cooperate. Working memory draws from long-term and episodic stores.
Episodic memories accumulate into semantic facts over repeated retrieval. Emotional
salience, computed in the limbic system, modulates consolidation strength across all
four declarative systems.

---

## 2. Working Memory

### 2.1 Baddeley's Multicomponent Model (1974, revised 2000)

The canonical working memory model, which maps directly onto the project's
working-memory module, has four components:

| Component | Function |
|-----------|----------|
| **Central executive** | Directs attention; suppresses irrelevant information; coordinates other subsystems |
| **Phonological loop** | Verbal/acoustic rehearsal buffer; maintains speech-coded representations |
| **Visuospatial sketchpad** | Spatial and visual maintenance; mental rotation and imagery |
| **Episodic buffer** (added 2000) | Integrates multimodal information from all sub-systems; acts as a temporary gateway to long-term memory |

The episodic buffer is the most important component for the system design: it is an
online integration layer that resembles Tulving's episodic memory but is temporary and
capacity-limited. It explains how working memory retrieves from long-term stores and
holds the result alongside current context.

### 2.2 Capacity Constraints

- Miller (1956): ~7 ± 2 items in immediate awareness.
- Cowan (2001): revised to ~4 "chunks" — items bindings processed as units.
- Resource is flexible and continuous, not discrete slots. Items decay without
  active attentional refreshing (time-based resource-sharing model).
- Interference from competing representations reduces effective capacity.
- **Design implication**: Working memory capacity must be enforced by an eviction
  policy. Items not refreshed (accessed) within a decay window should be candidates
  for eviction or consolidation.

### 2.3 Neural Basis

- **DLPFC** (dorsolateral prefrontal cortex): active manipulation of representations
  via recurrent glutamatergic networks.
- **vlPFC** (ventrolateral PFC): passive maintenance of representations.
- **Theta-band oscillations** (4–8 Hz): frequency-band mechanism for binding features
  of a multi-attribute item into a single chunk.
- **Stress**: catecholamines (norepinephrine, dopamine) under stress rapidly weaken
  PFC network recurrent connections, degrading working memory capacity.
- **Key insight**: Working memory is not a separate store — it is an _activated and
  attended_ subset of long-term memory representations (Cowan; Ericsson & Kintsch).
  This means the working memory module must be architecturally integrated with the
  long-term memory module.

---

## 3. Short-Term Memory as a Transitional Buffer

Short-term memory (STM) in the biological literature refers to the hippocampally
mediated holding pattern between first encoding and either forgetting or
consolidation. It is characterised by:

- **Session scope**: memories are tied to the current episode, not yet
  contextually extracted into long-term semantic stores.
- **Decay function**: without consolidation or rehearsal, short-term traces fade.
  In organic systems, this is linked to protein synthesis requirements: molecular
  traces require a ~6-hour window of stability.
- **Gateway role**: the hippocampus CA1 region computes a comparison between
  expected and actually retrieved content. Novelty and prediction errors trigger
  stronger encoding into working and episodic stores.
- **Design implication**: short-term memory should carry a TTL (time-to-live)
  that triggers a consolidation pipeline: evaluate importance → if above threshold,
  encode to long-term; otherwise expire.

---

## 4. Long-Term Memory: Neocortical Traces

### 4.1 Standard Model of Systems Consolidation (Squire & Alvarez, 1995)

New memories are initially encoded in the hippocampus and gradually transferred
to neocortical association areas via repeated replay (slow-wave sleep + sharp-wave
ripples + thalamocortical spindles). After transfer is complete, the neocortical
trace is hippocampus-independent.

- **Semantic facts** (what things are, not when they happened) can become fully
  neocortical over time.
- **Episodic memories** (contextualised personal events) may always require the
  hippocampus for retrieval, even after neocortical consolidation (Multiple Trace
  Theory, Nadel & Moscovitch).
- **Design implication**: long-term memory (ChromaDB default, Qdrant production)
  should store decontextualised semantic embeddings. Episodic memory is a
  separate collection with mandatory context metadata.

### 4.2 Importance Scoring as Consolidation Gate

The brain does not consolidate everything. Factors that increase consolidation
probability:

1. **Emotional salience** — amygdala amplification via basolateral amygdala (BLA).
2. **Rehearsal / retrieval frequency** — each retrieval restabilises and strengthens.
3. **Novelty** — CA1 prediction error detection and DG pattern separation flag novel items.
4. **Goal relevance** — prefrontal top-down gating selects items aligned with current goals.

The project's `importanceScore` field on `MemoryItem` directly operationalises this
biological gate. A threshold of ≥0.5 (as defined in the collection registry for
`brain.long-term-memory`) mirrors the brain's selectivity.

### 4.3 Reconsolidation

A critical finding with direct implementation implications: **whenever a previously
consolidated memory is retrieved, it re-enters a labile (unstable) state** for a
brief window (~hours in biological systems). It requires new protein synthesis to
re-stabilise. This window:

- Allows memories to be updated or strengthened on each retrieval.
- Distinct molecular mechanism from initial consolidation: Zif268 required for
  reconsolidation vs. BDNF for initial consolidation.
- **Design implication**: on retrieval from long-term store, the item's
  `importanceScore` and `accessCount` should be incremented. This is the digital
  analogue of reconsolidation-as-strengthening. The content embedding can be
  re-embedded after modification (content update during labile window).

---

## 5. Episodic Memory

### 5.1 Tulving's Framework (1972)

Episodic memory is the system for remembering autobiographical events with temporal
and spatial context — "remembering" as opposed to mere "knowing" (semantic memory).
Its key properties:

- **Autonoetic consciousness**: subjective sense of self participating in recalled event.
- **Mental time travel**: ability to revisit the past and project into the future.
- **What–Where–When structure**: the core encoding format, demonstrated in
  non-human subjects (Clayton & Dickinson's scrub-jay experiments).

### 5.2 Nine Properties (Tulving)

1. Sensory-perceptual records of experienced events.
2. Retain the activation patterns active at encoding time.
3. Are represented with an imagery/perspective component.
4. Have a point of view (field or observer perspective).
5. Contain short time-slices, not continuous streams.
6. Are organised with a temporal order.
7. Subject to rapid forgetting of peripheral details.
8. Autobiographically specific — tied to a self and situation.
9. Accessed through recollection, not just familiarity recognition.

### 5.3 Semantic vs. Episodic

Episodic memory acts as a **contextual map** that binds semantic items together in
time and space. Accumulated episodic episodes, stripped of contextual detail, become
semantic memories. Together they constitute declarative (explicit) memory.

| Feature | Episodic | Semantic |
|---------|----------|---------|
| Context | Yes — when, where, who | No — atemporal facts |
| Self-reference | Required | Not required |
| Forgetting curve | Rapid for peripheral details | Slower for core facts |
| Hippocampal dependency | High (MTT: always required) | Can transfer to neocortex |
| Collection | `brain.episodic-memory` | `brain.long-term-memory` |

### 5.4 Emotional Boost

The amygdala enhances encoding of emotionally significant events. "Flashbulb
memories" — vivid, detailed memories of emotionally charged events — arise from
strong BLA activation during encoding. The VTA–hippocampus dopamine projection
directly mediates consolidation of reward-related memories.

---

## 6. Hippocampal Architecture

The hippocampus is not a monolithic store. Its subregions perform distinct operations
that directly map onto system design patterns:

| Subregion | Function | System design analogue |
|-----------|----------|------------------------|
| **Dentate Gyrus (DG)** | Pattern separation — distinguishes similar inputs | Hash space partitioning / near-duplicate detection |
| **CA3** | Pattern completion — reconstructs full memory from partial cue via recurrent connections | Approximate nearest-neighbour retrieval on partial query |
| **CA1** | Output relay; compares expected (retrieved via CA3) vs. actual (direct from EC) signals | Retrieval validation / novelty detection |
| **Entorhinal Cortex (EC)** | Two-way gateway between hippocampus and neocortex | API bridge between episodic/STM collections and long-term storage |

### Sharp-Wave Ripples

During rest and sleep, the hippocampus generates high-frequency (~100–200 Hz)
sharp-wave ripples. These drive coordinated replay of recent experiences, enabling
hippocampal→neocortical transfer. The sequence:

```
Slow-wave sleep
  → hippocampal sharp-wave ripples (replay sequence)
  + thalamocortical sleep spindles (12–15 Hz)
  + cortical slow oscillations (<1 Hz)
  → coordinated transfer → neocortical trace formation
```

This is the biological consolidation pipeline. Its computational analogue is the
scheduled background consolidation job (eviction from short-term → scoring →
embedding in long-term).

---

## 7. Memory Consolidation Pipeline

### 7.1 Synaptic Consolidation (Minutes–Hours)

**Mechanism**: Long-Term Potentiation (LTP) — NMDA receptor-dependent synaptic
strengthening. Repeated co-activation of pre- and post-synaptic neurons triggers
calcium influx → AMPA receptor insertion → synapse remodelling. Requires protein
synthesis within ~6 hours; susceptible to disruption (electroconvulsive shock,
translation inhibitors) during this window.

**Analogue**: Initial embedding of a memory item into the vector store — the item
is persisted but vulnerable to eviction before importanceScore accrual.

### 7.2 Systems Consolidation (Weeks–Decades)

**Mechanism**: Hippocampus teaches neocortex via repeated replay. Long-running
background process, not a single event. Neocortical traces are initially
hippocampus-dependent and gradually become independent via structural synaptic
remodelling over months to years.

**Analogue**: The scheduled consolidation pipeline: move items from
`brain.short-term-memory` to `brain.long-term-memory` based on importance and access
frequency. The pipeline is incremental, not a one-shot transfer.

### 7.3 Reconsolidation (Every Retrieval)

**Mechanism**: Retrieved memories are temporarily destabilised (labile state)
requiring new protein synthesis to re-stabilise. Allows modification and
strengthening. Biologically distinct from initial consolidation (different molecular
markers: Zif268 vs. BDNF).

**Analogue**: On every retrieval event, the item's `importanceScore` and
`accessCount` metadata fields are updated, and the item may be re-embedded if its
content was modified during the retrieval-triggered update.

---

## 8. Dopamine and the Reward Prediction Error

### 8.1 The RPE Signal (Montague, Dayan & Sejnowski, 1996)

Dopaminergic neurons in the **ventral tegmental area (VTA)** and **substantia nigra**
fire as a temporal difference reward prediction error signal:

- Unexpected reward → phasic dopamine _burst_ (positive RPE).
- Expected reward arrives → no change in dopamine firing (zero RPE).
- Expected reward withheld → dopamine firing _drops below baseline_ (negative RPE).

This is identical to the temporal difference (TD) learning algorithm used in
reinforcement learning (e.g. DQN). The brain discovered TD learning through evolution.

### 8.2 Dopamine Pathways Relevant to Phase 5

| Pathway | Source | Target | Function |
|---------|--------|--------|----------|
| Mesolimbic | VTA | Nucleus accumbens | Assigns incentive salience ("wanting") to stimuli |
| Mesocortical | VTA | PFC | Updates goal values based on incentive salience |
| VTA → amygdala | VTA | BLA | Mediates consolidation of reward-related memories |
| VTA → hippocampus | VTA | CA1/EC | Tags novel/rewarding items for stronger encoding |

### 8.3 Emotional Modulation via BLA

The basolateral amygdala (BLA) is activated by emotionally arousing stimuli (via
epinephrine/stress hormones). It projects directly to the hippocampus, amplifying
hippocampal encoding of emotional events. This explains why emotional events are
remembered more vividly: the BLA boosts the effective LTP at hippocampal synapses
during encoding.

**Analogue**: The `affectiveValence` field on `MemoryItem` and the reward signal
value in `RewardSignal` implement this amplification. High-valence signals should
boost the `importanceScore` of co-occurring memory items.

---

## 9. Complementary Learning Systems Theory (McClelland, McNaughton & O'Reilly, 1995)

CLS theory formalises the dual-system architecture that underlies the entire Phase 5
module hierarchy:

| System | Biological | Properties | AI analogue |
|--------|-----------|-----------|-------------|
| **Fast hippocampal system** | Hippocampus + MTL | Rapid one-shot learning; sparse, pattern-separated codes; highly context-specific | Short-term memory / episodic memory (Redis + ChromaDB with session-scoped collections) |
| **Slow neocortical system** | Distributed neocortex | Slow, repetition-dependent learning; dense, overlapping codes; context-independent generalisation | Long-term memory (ChromaDB + Qdrant + SQLite; semantic facts) |

The critical insight: these two systems must coexist and cooperate. Learning too fast
in the neocortical system (using only RAG without STM buffering) causes catastrophic
interference — new information overwrites old generalisations. The hippocampal
fast system acts as a temporary buffer that **interleaves** new episodes with
existing knowledge during replay, allowing safe neocortical consolidation.

This is the neuroscientific justification for maintaining separate short-term and
long-term memory collections rather than writing everything to the same vector store.

---

## 10. Brain-Inspired AI Techniques Derived from This Neuroscience

The following programmatic techniques used in Phase 5 have direct biological origin:

| Technique | Biological origin | Phase 5 application |
|-----------|------------------|-------------------|
| **RAG (Retrieval-Augmented Generation)** | CA3 pattern completion retrieval, EC two-way gateway | Long-term and episodic memory retrieval into working context |
| **Tiered memory stores** | CLS dual-system (hippocampal fast + neocortical slow) | Redis (STM TTL) + ChromaDB (LTM) + SQLite (semantic facts) |
| **Experience replay (DQN, Hinton)** | Sharp-wave ripple replay during consolidation | Consolidation pipeline: replay STM items → score → promote to LTM |
| **Importance-weighted replay** | BLA emotional amplification + novelty-driven DG tagging | `importanceScore`-gated promotion from STM to LTM |
| **Episodic controllers (MERLIN)** | Tulving episodic + what-where-when | `brain.episodic-memory` with mandatory `sessionId + taskId + timestamp` metadata |
| **Temporal difference learning** | Dopamine RPE (Schultz, 1997) | `RewardSignal.value` as TD error; reward/penalty types |
| **Differentiable Neural Computer (Graves, 2016)** | Hippocampal indexed external memory | External vector store + content-addressable retrieval via embeddings |

---

## 11. Closing References

- [shared/types/memory-item.schema.json](../../shared/types/memory-item.schema.json) — canonical memory item contract
- [shared/types/reward-signal.schema.json](../../shared/types/reward-signal.schema.json) — canonical reward signal contract
- [shared/vector-store/collection-registry.json](../../shared/vector-store/collection-registry.json) — all Phase 5 collections
- [resources/neuroanatomy/hippocampus.md](../../resources/neuroanatomy/hippocampus.md) — hippocampal architecture stub
- [resources/neuroanatomy/limbic-system.md](../../resources/neuroanatomy/limbic-system.md) — affective/motivational system stub
- [resources/neuroanatomy/prefrontal-cortex.md](../../resources/neuroanatomy/prefrontal-cortex.md) — working memory and reasoning stub
- [docs/Workplan.md](../Workplan.md) — Phase 5 implementation checklist (§§5.1–5.6)
- [docs/research/phase-5-mcp-solutions-and-programmatic-techniques.md](phase-5-mcp-solutions-and-programmatic-techniques.md) — programmatic counterpart to this brief
- [docs/research/phase-5-synthesis-workplan.md](phase-5-synthesis-workplan.md) — module-level synthesis and implementation guidance
