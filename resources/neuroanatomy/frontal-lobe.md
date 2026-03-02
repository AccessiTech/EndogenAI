---
id: neuroanatomy-frontal-lobe
version: 0.2.0
status: stub
authority: descriptive
last-reviewed: 2026-03-02
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

The **Frontal Lobe** (specifically the prefrontal and anterior regions) provides the neuroanatomical reference for the
brAIn **Executive / Agent Layer** — the seat of identity, persistent goals, values, and high-level reasoning strategy.

## Function

The frontal lobe is the largest lobe of the human brain, occupying the entire anterior portion. It is the primary
substrate for what makes humans distinctively human:

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

- **Agent identity**: the Executive / Agent Layer holds a persistent self-model — the agent's identity, role,
  capabilities, and behavioral constraints. Implemented in `identity.py`; persists append-only to
  `brain.executive-agent` ChromaDB collection.
- **BDI interpreter loop**: the `deliberation.py` module runs the Beliefs-Desires-Intentions loop: option generation
  → value scoring (OFC analogue) → OPA policy evaluation → intention commitment (BG direct pathway analogue) →
  reconsideration check. Cycle period is configurable via `identity.config.json`.
- **OPA policy engine**: three-tier Rego policy set (`policies/identity.rego`, `policies/goals.rego`,
  `policies/actions.rego`) enforces identity integrity, goal capacity, and action permissions. Corresponds to
  frontal inhibitory control (IFG) and ACC conflict detection. Runs as standalone HTTP server at
  `localhost:8181` (add `opa` service to `docker-compose.yml`).
- **Goal stack FSM**: 7-state lifecycle (PENDING → EVALUATING → COMMITTED → EXECUTING → COMPLETED / FAILED /
  DEFERRED) managed by `goal_stack.py`. Capacity constraint (`maxActiveGoals = 5`) mirrors DLPFC working memory
  limits.
- **BG pathway analogues**: BG direct pathway = `commit_intention` (disinhibit execution); indirect pathway =
  `enforce_capacity` (suppress competing goals); hyperdirect pathway = `abort_goal` (stop signal cancels full
  execution queue immediately).
- **Persistent goal stack**: goals survive across sessions; priority ordering with lifecycle management.
- **Policy engine**: value evaluation must gate all actions before dispatch — analogous to frontal inhibitory control.
- **Top-down modulation dispatch**: this layer sends attention directives, goal priors, and policy constraints downward
  to all other layers.
- **Social cognition hooks**: the self-model should include representations of user context and expected interactional
  norms.
- **Vector store**: embed goals, values, policies, and identity state into `brain.executive-agent`.

## Phase 6 Implementation References

| Region | Phase 6 construct | File |
|---|---|---|
| DLPFC (BA 9/46) | Goal stack active maintenance | `goal_stack.py` |
| OFC (BA 11–14) | Value scoring of goal candidates | `deliberation.py` |
| vmPFC (BA 10–12) | Fast heuristic pre-filter | `deliberation.py` |
| ACC (BA 24/32) | OPA `violations[]` → escalation | `policy.py` |
| BG direct | `commit_intention` disinhibition | `goal_stack.py`, `a2a_handler.py` |
| BG indirect | `enforce_capacity` suppression | `goal_stack.py` |
| BG hyperdirect | `abort_goal` stop signal | `goal_stack.py`, `a2a_handler.py` |
| Dopamine RPE | `MotorFeedback.reward_signal` updates priority | `feedback.py` |

See `docs/research/phase-6-neuroscience-executive-output.md §2` for full derivation.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
