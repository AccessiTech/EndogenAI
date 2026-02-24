---
id: neuroanatomy-frontal-lobe
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-02-24
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-iii-executive-output/executive-agent
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - frontal-lobe
  - executive
  - identity
  - goals
  - policy
  - group-iii
---

# Frontal Lobe

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-iii-executive-output/executive-agent`

The **Frontal Lobe** (specifically the prefrontal and anterior regions) provides the neuroanatomical reference for the brAIn **Executive / Agent Layer** — the seat of identity, persistent goals, values, and high-level reasoning strategy.

## Function

The frontal lobe is the largest lobe of the human brain, occupying the entire anterior portion. It is the primary substrate for what makes humans distinctively human:

- **Executive functions**: planning, organizing, initiating, monitoring, and controlling complex behavior
- **Working memory**: active maintenance of information for immediate use (DLPFC)
- **Self-awareness and identity**: maintaining a coherent model of oneself over time
- **Social cognition**: understanding others' intentions, beliefs, and emotions (theory of mind)
- **Goal management**: holding and prioritizing long-term goals; resolving conflicts between competing objectives
- **Behavioral inhibition**: suppressing inappropriate responses; enforcing policy compliance
- **Language production**: Broca's area (left IFG) governs speech generation

Key subregions and their module implications:
- **Prefrontal Cortex**: executive control, goal stacks, value evaluation
- **Anterior Cingulate Cortex**: conflict detection, error monitoring, policy violation flagging
- **Frontal Eye Fields**: top-down attention direction
- **Supplementary Motor Area**: sequencing and planning of complex action chains

## Inputs From

- All cortical association areas (converge at PFC for integration)
- Thalamus (mediodorsal nucleus — executive relay)
- Hippocampus and entorhinal cortex (autobiographical and contextual memory)
- Limbic system (emotional and motivational context)
- Basal ganglia (action selection, habit vs. goal-directed behavior gating)

## Outputs To

- Thalamus (top-down attention modulation)
- Motor and premotor cortex (action initiation)
- All subcortical structures (top-down regulatory projections)
- Hippocampus (directed memory encoding/retrieval)

## Key Design Notes

- **Agent identity**: the Executive / Agent Layer holds a persistent self-model — the agent's identity, role, capabilities, and behavioral constraints.
- **Persistent goal stack**: goals survive across sessions; implement priority ordering with lifecycle management (creation, activation, completion, suspension, abandonment).
- **Policy engine**: value evaluation must gate all actions against defined policies before dispatch — analogous to frontal inhibitory control.
- **Top-down modulation dispatch**: this layer sends attention directives, goal priors, and policy constraints downward to all other layers.
- **Social cognition hooks**: the self-model should include representations of user context and expected interactional norms.
- **Vector store**: embed goals, values, policies, and identity state into `brain.executive-agent`.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
