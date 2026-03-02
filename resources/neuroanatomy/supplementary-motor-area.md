---
id: neuroanatomy-supplementary-motor-area
version: 0.1.0
status: stub
authority: descriptive
last-reviewed: 2026-03-02
seed-collection: brain.long-term-memory
chunking: section-boundary
maps-to-modules:
  - modules/group-iii-executive-output/agent-runtime
source: raw_data_dumps/Human_Brain__wiki.md
tags:
  - supplementary-motor-area
  - pre-sma
  - agent-runtime
  - decomposition
  - sequencing
  - group-iii
---

# Supplementary Motor Area

> **Status**: Stub — enrich from `raw_data_dumps/Human_Brain__wiki.md`

## Module Analogy

Maps to: `modules/group-iii-executive-output/agent-runtime`

The **Supplementary Motor Area** (SMA proper and pre-SMA) provides the neuroanatomical reference for the **task
decomposition and pre-execution planning phase** of the brAIn Agent Execution (Runtime) Layer — specifically the
separation of the decomposition Activity from execution Activities in the Temporal `IntentionWorkflow`, and the
Bereitschaftspotential analogue of pre-fetching tool dependencies before execution begins.

## Function

The SMA occupies the medial surface of the superior frontal gyrus (BA 6) and is divided into two functionally
distinct regions:

- **SMA proper**: programs and initiates voluntary internally-driven movement sequences. Active before and during
  movement execution. Receives direct input from basal ganglia (via thalamus). Responsible for multi-step action
  programs that unfold from memory, without requiring continuous external cues.
- **Pre-SMA** (rostral SMA): higher-order sequencing and switching. Evaluates and selects between competing action
  sequences. Crucially: pre-SMA is active before SMA proper — it represents the planning phase that precedes
  execution.

Key functional principles:

- **Internally-driven sequencing**: unlike premotor cortex (which requires external cues), SMA sequences are
  generated internally from stored programmes — analogous to `decomposer.py` constructing a `SkillPipeline` from
  memory/context rather than reactive to real-time input.
- **Bereitschaftspotential (readiness potential)**: a slow negative EEG deflection beginning ~550ms before voluntary
  movement. It originates in the SMA and reflects neural preparation — the brain begins "loading" motor programs
  well before execution. Module analogue: `tool_registry.py` pre-fetches agent-card metadata for all likely tools
  during the decomposition Activity, before any dispatch Activity begins.
- **Sequence switching**: pre-SMA is especially active when an agent must switch between ongoing sequences — e.g.,
  if a mid-execution plan revision is required. Module analogue: the Temporal `Update("revise_plan")` handler in
  `workflow.py`, which replaces the remaining pipeline steps in-flight.
- **Bimanual coordination**: SMA proper coordinates both hands simultaneously. Module analogue:
  `dispatch_concurrent` in `motor-output/dispatcher.py`, which runs multiple `ActionSpec` items from the same
  pipeline step in parallel via `asyncio.gather`.

## Inputs From

- Prefrontal cortex (goal intentions and top-down sequence selection)
- Basal ganglia via thalamus (strongly connected; habit vs. goal-directed sequence gating)
- Cingulate motor area (motivation and effort allocation)
- Somatosensory and parietal cortex (proprio-feedback for sequence correction)

## Outputs To

- Primary motor cortex M1 (executes the prepared sequence)
- Spinal cord (some direct corticospinal projections)
- Contralateral SMA (bimanual coordination)
- Basal ganglia (feedback loop)

## Key Design Notes

- **Decomposition before execution** (pre-SMA principle): the `decompose_goal` Activity in `activities.py` runs as
  the first Activity of every `IntentionWorkflow`, constructing the full `SkillPipeline` before any dispatch
  Activity begins. This mirrors pre-SMA's planning phase preceding SMA proper's execution phase.

- **Bereitschaftspotential → agent-card pre-fetch**: `tool_registry.py` fetches `/.well-known/agent-card.json`
  from all `discoveryTargets` at startup and on periodic health check, so tool availability is known before the
  first `decompose_goal` call. No blocking discovery during execution.

- **Temporal `Update("revise_plan")`** (pre-SMA sequence switching): the `revise_plan` Update handler in
  `workflow.py` allows in-flight plan revision if `executive-agent` determines a reconsideration is needed (e.g.,
  deviation_score > reconsiderationThreshold). This is the pre-SMA switch signal injected mid-sequence.

- **`workflow.py` determinism rule** (SMA proper → committed sequence): once execution begins, the workflow must
  replay deterministically from Event History after any Worker crash — exactly as SMA proper executes its stored
  motor programme to completion without re-evaluating the plan. All non-deterministic work is in Activities.

- **No vector store**: like the biological SMA, `agent-runtime` is a coordinator and sequencer — it does not
  maintain its own memory store. Context is assembled by calling upstream memory modules (working-memory MCP tool)
  inside the `decompose_goal` Activity.

## Phase 6 Implementation References

| Region | Phase 6 construct | File |
|---|---|---|
| pre-SMA (planning phase) | `decompose_goal` Activity runs before any dispatch | `decomposer.py`, `activities.py` |
| SMA proper (execution) | `IntentionWorkflow` post-decomposition step loop | `workflow.py` |
| Bereitschaftspotential | Agent-card pre-fetch during registry startup | `tool_registry.py` |
| Sequence switching | `Update("revise_plan")` in-flight plan revision | `workflow.py` |
| Bimanual coordination | `dispatch_concurrent` parallel `asyncio.gather` | `motor-output/dispatcher.py` |
| Prefect fallback | Circuit-breaker when SMA (Temporal) unavailable | `prefect_fallback.py` |

See `docs/research/phase-6-neuroscience-executive-output.md §3` for full derivation.

## References

<!-- Populate from raw_data_dumps/Human_Brain__wiki.md -->
