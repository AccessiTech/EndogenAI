# Phase 6 — Neuroscience of Executive & Output Systems

_Generated: 2026-03-02 by Docs Executive Researcher_  
_Sources: `docs/research/sources/phase-6/bio-*.md` (fetched 2026-03-02)_

> **Audience**: Phase 6 implementation agents and the Phase 6 Synthesis Workplan.  
> **Purpose**: Map the neuroscience of the frontal lobe, prefrontal cortex, basal ganglia,
> cerebellum, supplementary motor area, and motor cortex onto the three Phase 6
> sub-modules: `executive-agent`, `agent-runtime`, and `motor-output`.

---

## 1. Module Map

| Sub-module | Primary brain regions | Analogy |
|---|---|---|
| `executive-agent` | Prefrontal cortex (DLPFC, OFC, vmPFC, ACC), frontal lobe, basal ganglia | Identity, goal stack, value evaluation, policy gating |
| `agent-runtime` | Cerebrocerebellum, pre-SMA, supplementary motor area | Task decomposition, sequential planning, skill pipeline execution |
| `motor-output` | Primary motor cortex (M1), premotor cortex (PMd/PMv), SMA proper, spinocerebellum | Action dispatch, output generation, upward feedback |

---

## 2. `executive-agent` — Prefrontal Cortex, Frontal Lobe & Basal Ganglia

### 2.1 Prefrontal Cortex: Active Goal Maintenance & Policy Gating

The prefrontal cortex (PFC) is the neuroanatomical substrate for the executive identity and goal management
layer. Miller & Cohen's (2001) integrative theory establishes the PFC not as a passive memory store but as an
**active gating structure**: it maintains representations of goals and means and provides **top-down bias signals**
that route activity through neural pathways in a context-appropriate manner. This is the biological basis for
three core `executive-agent` responsibilities:

1. **Goal stack maintenance** — DLPFC (BA 9/46) actively holds and refreshes goal representations via
   recurrent circuits. PFC cells fire persistently across delay periods, sustaining goals even when
   environmental cues are absent. The capacity constraint (~4 goal chunks in working memory; Cowan 2001)
   implies a prioritised stack with explicit eviction rules rather than unbounded accumulation.

2. **Value and policy evaluation** — The OFC (BA 11–14) encodes reward expectancy and updates value
   representations in real time. The vmPFC (BA 10–12) integrates somatic/emotional signals (Damasio's
   somatic marker hypothesis) to bias decisions toward value-aligned choices even before deliberate
   reasoning completes. These dual valuation streams map to two distinct evaluation passes: a fast
   heuristic pass (vmPFC-style emotional weighting) and a slower deliberative pass (OFC reward modelling).

3. **Conflict detection and policy enforcement** — The ACC (BA 24/32) monitors for goal conflicts, policy
   violations, and prediction errors. When the ACC detects a violation it escalates a control signal to
   DLPFC, which then modulates downstream processing. This maps directly to the OPA policy engine: the
   ACC's role is to flag that a proposed intention conflicts with held values, triggering re-evaluation
   before commitment.

Shimamura's Dynamic Filtering Theory extends Miller & Cohen: the PFC applies **four operations** to
information in working memory — select (gate in relevant), maintain (hold active), update (replace with
new), and reroute (redirect processing to alternative representations). All four operations are required
in an executive-agent goal lifecycle.

### 2.2 Sub-Region Implementation Map

| PFC Sub-region | BA | Biological role | `executive-agent` mapping |
|---|---|---|---|
| DLPFC | 9, 46 | Working memory, cognitive flexibility, goal sequencing | Goal stack (push/pop/prioritise), context window management |
| OFC | 11–14 | Reward evaluation, expected value coding | Value function: score candidate goals against current reward signal |
| vmPFC | 10–12 | Somatic marker, emotional bias in decisions | Fast heuristic value pass; affective weighting of goal selection |
| ACC | 24, 32 | Conflict detection, error monitoring, response selection | Policy violation detector; escalation trigger to OPA engine |
| LPFC (broad) | 8, 44–47 | Rule-based reasoning, prospective memory | Rule engine input; prospective goal scheduling |

### 2.3 Basal Ganglia: Action Selection & Habit / Goal-Directed Gating

The basal ganglia (BG) implement a cortico-striato-thalamo-cortical circuit that gates which motor or
cognitive actions are released for execution. Three pathways operate in parallel:

- **Direct pathway** (D1 receptors, striatum → GPi/SNr → thalamus → cortex): **facilitates** the
  currently selected action by disinhibiting the thalamus. Maps to: releasing a committed intention
  to the `agent-runtime` execution queue.

- **Indirect pathway** (D2 receptors, striatum → GPe → STN → GPi/SNr → thalamus): **suppresses**
  competing actions via global inhibition. Maps to: rejecting or deferring lower-priority candidate
  goals when a higher-priority intention is executing.

- **Hyperdirect pathway** (cortex → STN direct): **rapidly cancels** the entire selection process
  when a stop signal arrives. Maps to: interrupt/abort handling — clearing the execution queue on
  high-priority stop signals from upstream modules.

#### Five Parallel Cortico-BG Loops

| Loop | Cortical origin | Functional role | Phase 6 relevance |
|---|---|---|---|
| Motor | M1, SMA | Voluntary movement selection | Feeds `motor-output` |
| Oculomotor | FEF, SEF | Saccade/attention direction | Feeds attention modules (Phase 4) |
| DLPFC-Executive | DLPFC (BA 46) | Goal-directed working memory update | Goal stack promotion/demotion |
| OFC-Limbic | OFC, vmPFC | Reward-guided behaviour | Value evaluation in goal selection |
| vmPFC-Limbic | ACC, vmPFC | Emotional/motivational bias | Affect-weighted policy decisions |

#### Dopamine & Reward Prediction Error

Dopaminergic neurons in the substantia nigra pars compacta (SNc) and VTA encode **reward prediction
error (RPE)**: they fire above baseline on unexpected reward (`δ > 0`), below baseline on reward
omission (`δ < 0`), and are silent on expected reward (`δ = 0`). This is the biological actor-critic
signal:

- **Critic** (striatum): learns value function V(s) — used by `executive-agent` to score goals
- **Actor** (frontal cortex): learns policy π(a|s) — used by `agent-runtime` to select skill pipelines

The D1/D2 receptor ratio in the striatum determines whether the direct (go) or indirect (no-go) pathway
dominates, implementing a gating mechanism that transitions behaviour between **goal-directed** (PFC-led)
and **habitual** (striatum-led). In the Phase 6 context, this implies a configurable threshold: when a
task has been executed successfully many times, the `agent-runtime` can route it as a habit (fast,
low-deliberation) rather than requiring full `executive-agent` deliberation each time.

### 2.4 Identity & Self-Model

The frontal lobe supports a **persistent self-model**: autobiographical memory (from hippocampus) is
integrated with current goal states by the PFC to form a coherent agent identity that persists across
time. Key properties:

- The self-model is not static — it is updated from episodic memory via replayed experience
- Theory of mind (MPFC, TPJ) enables social reasoning: the agent models the goals and beliefs of
  external agents, informing how it plans interactions
- Behavioural inhibition (right IFG): suppresses contextually inappropriate responses before they are
  executed — the biological basis for the "guard" that prevents the agent from executing actions that
  violate its identity constraints

---

## 3. `agent-runtime` — Cerebrocerebellum & Supplementary Motor Area

### 3.1 Cerebellum: Supervised Learning, Internal Models & Predictive Control

The cerebellum contains ~80% of the brain's neurons in only ~10% of brain volume. Despite its name
("little brain"), its computational contribution to skilled execution is profound. Marr (1969) and
Albus (1971) established the foundational model:

- **Climbing fibre** (from inferior olive): encodes **teaching/error signal** — the difference between
  expected and actual sensory outcome
- **Parallel fibres** (hundreds of thousands per Purkinje cell): encode contextual features of the
  current state
- **Long-term depression (LTD)** at the parallel fibre → Purkinje cell synapse: the error signal
  drives synaptic weakening, refining the Purkinje cell's output over time to predict and pre-correct
  future errors

Doya (1999) formalised the canonical division of labour across the brain's learning systems:

| System | Learning algorithm | Phase 6 module |
|---|---|---|
| Cerebellum | Supervised learning (error correction) | `agent-runtime` — skill refinement via execution feedback |
| Basal Ganglia | Reinforcement learning (reward prediction) | `executive-agent` — goal/policy improvement via RPE |
| Neocortex (unsupervised) | Hebbian / predictive | Phase 7 adaptive layer |

### 3.2 Internal Forward and Inverse Models

The cerebrocerebellum (lateral hemispheres) maintains **internal models** for every learned motor skill:

- **Forward model**: given an efference copy of the motor command, predict the expected sensory
  outcome. This enables **predictive control** — corrections begin before errors are detected by
  peripheral feedback (which is ~50–100 ms delayed).

- **Inverse model**: given a desired outcome state, compute the required motor command. This is the
  basis for skilled goal-to-action transformation.

In the `agent-runtime` context:
- The **forward model** maps to: given a task description and current context, predict which tool
  calls will be required and pre-stage them (prefetch data, prepare parameters)
- The **inverse model** maps to: given a goal state (what the executive-agent wants achieved),
  compute the required skill pipeline (which tools, in what sequence, with what parameters)

Buckner (2011) demonstrated that more than 50% of the cerebellar cortex is interconnected with
cortical association zones (including prefrontal, parietal, and temporal), not just motor areas.
This underscores that the cerebellum supports **cognitive** skill learning — task decomposition
and execution strategy refinement — not just motor coordination.

### 3.3 Pre-SMA and Supplementary Motor Area: Sequential Planning

The SMA complex (medial BA 6) consists of two functionally distinct regions:

| Region | Connectivity | Functional role |
|---|---|---|
| SMA proper | Connects directly to M1 and spinal cord; receives input from putamen | **Executes** internally generated sequences; Bereitschaftspotential (readiness potential) originates here; bimanual coordination |
| pre-SMA | Connects to DLPFC, caudate, premotor; no direct corticospinal projections | **Plans** action sequences abstractly, without immediate execution; switches between sequences; gatekeeping |

The **pre-SMA** is the critical mapping for `agent-runtime`:
- It selects and sequences actions without directly triggering them (gatekeeping role)
- It is active during **preparation** phases: planning which skill to execute next
- It connects to the caudate nucleus (BG cognitive loop): the caudate feeds back action values to
  pre-SMA, allowing the planned sequence to be updated based on current reward predictions

This maps to the `agent-runtime`'s role as the sequencer that structures task pipelines but
delegates actual execution to individual Activities/tools.

The **Bereitschaftspotential** (readiness potential) — the slow, negative EEG deflection that begins
~500–1000 ms before conscious awareness of intention to act — implies that motor preparation is a
gradual, pre-conscious process. The `agent-runtime` analogy is that task decomposition and tool
pre-staging should begin before the explicit execution command arrives.

---

## 4. `motor-output` — Motor Cortex, Premotor Cortex & Spinocerebellum

### 4.1 Primary Motor Cortex (M1)

M1 (BA 4) is the origin of the corticospinal tract — the primary descending pathway for voluntary
movement. Key properties:

- **Betz cells** (giant pyramidal neurons in layer V): project directly to alpha motor neurons in
  the spinal cord, enabling fast, precise voluntary movement
- **Somatotopic organisation** (motor homunculus): discrete body regions mapped topographically,
  with disproportionately large representation for hands and face (high dexterity)
- **Population coding**: individual movements are encoded by distributed populations of M1 neurons,
  not single cells — mapping to distributed tool dispatch rather than monolithic output calls

In Phase 6, M1 maps to the actual **execution dispatcher** in `motor-output`: the component that
translates an action specification into a concrete external call (API, message, file write, signal
emission).

### 4.2 Premotor Cortex (PMd / PMv)

| Region | Key property | `motor-output` mapping |
|---|---|---|
| PMd (dorsal premotor, BA 6 lat.) | Reach planning; space-dependent action selection; receives parietal input | Output channel selection: which interface/API/channel to use for a given action |
| PMv (ventral premotor, F5) | Mirror neurons: fire on both action observation and execution; corollary discharge | Corollary discharge: the output module sends a representation of the about-to-be-dispatched action back to executive-agent before execution (prediction) |
| PMv (F5/Broca) | Action-language link: same circuit governs tool use and speech production | Rendered text/language output dispatch |

Mirror neurons in PMv have a critical implication: the same circuit handles both **observing** and
**executing** actions. For `motor-output`, this suggests the feedback loop (confirming that the
dispatched action was received and interpreted as intended) should use the same schema and interface
as the dispatch itself — making it trivial to replay, inspect, or simulate.

### 4.3 SMA Proper: Internally Generated Output Sequences

The SMA proper (BA 6 medial) drives:
- **Internally generated** sequential actions: not triggered by external cues, but by internally
  maintained plans (from `agent-runtime`)
- **Bimanual coordination**: synchronising two parallel execution streams (maps to concurrent
  parallel tool dispatch)
- **Direct corticospinal projections**: the SMA proper has its own direct M1-bypassing output pathway,
  implying that some output sequences can be dispatched without re-entering the deliberative loop

### 4.4 Optimal Feedback Control (OFC Principle)

Scott (2004) and Todorov & Jordan (2002) established **Optimal Feedback Control (OFC)** as the
governing principle of motor execution:

> Only correct deviations that interfere with the task goal; ignore deviations that do not affect outcome.

This principle has a direct implementation implication for `motor-output`:
- Not every API error requires an interrupt to the full deliberation chain
- Minor, recoverable errors (transient network failures, rate limiting) should be handled locally
  within `motor-output` via retries/circuit breakers
- Only errors that fundamentally change the achievability of the goal (tool unavailable, permission
  denied, state inconsistency) should propagate upward as a `MotorFeedback` failure to `executive-agent`

### 4.5 Dynamical Systems View of Motor Cortex

Shenoy, Sahani & Churchland (2013) proposed that M1 operates as a **dynamical system** whose state-space
trajectories generate movement, rather than as a command encoder for individual muscle activations. The
trajectory through state space is pre-configured during preparation (analogous to pre-SMA activity) and
then **unrolls** during execution.

For `motor-output`, this corresponds to: output sequences are pre-staged as a full pipeline (an ordered
list of Actions with parameters) during the planning phase, and the runtime simply advances through the
pipeline state machine — rather than making ad-hoc per-step decisions.

### 4.6 Spinocerebellum: Real-Time Error Correction

The spinocerebellum (medial vermis and intermediate hemispheres) receives real-time proprioceptive and
tactile feedback from the ongoing movement via the spinocerebellar tracts, sending corrective signals
via the deep cerebellar nuclei → red nucleus / thalamus → M1.

For `motor-output`, this maps to the **upward feedback confirmation loop**:
- After each action dispatch, the module must observe the actual outcome
- If the outcome deviates from the predicted outcome (forward model from `agent-runtime`), the deviation
  must be encoded as a `MotorFeedback` signal and propagated back to `executive-agent`
- This feedback must be **real-time** (synchronous or near-synchronous), not batched — delays in
  error correction are as costly in software as they are in biology

---

## 5. Cross-Module Signal Flow

```
external-percept
      │
  [Group I signal processing — attention filtering, sensory input]
      │
  [Group II cognitive processing — memory consolidation, affective weighting, reasoning]
      │
  executive-agent
  ├── identity.self-model  (who am I, what do I value)
  ├── goal-stack           (what am I trying to achieve)
  ├── policy-engine (OPA)  (what am I permitted to do)
  └── deliberation         (which intention to commit → sends to agent-runtime)
             │
        agent-runtime
        ├── task-decomposition   (what steps → which tools)
        ├── tool-registry        (what skills are available)
        ├── sequence-planner     (pre-SMA: plan before execute)
        └── execution-pipeline   (Temporal Workflow → Activities)
                   │
              motor-output
              ├── action-dispatcher   (M1: send the actual call)
              ├── channel-selector    (PMd: which interface/API)
              ├── output-renderer     (PMv/Broca: text/structured output)
              └── feedback-emitter    (spinocerebellum: outcome → executive-agent)
                         │
              [external environment]
                         │
              [MotorFeedback signal → back to executive-agent]
```

---

## 6. Key Neuroscience Principles for Implementation

| # | Principle | Source | Implementation implication |
|---|---|---|---|
| 1 | PFC provides top-down bias, not direct command | Miller & Cohen 2001 | `executive-agent` sends weighted goal/context to `agent-runtime`; does not micro-manage individual tool calls |
| 2 | Cerebellar supervised learning needs an error signal | Marr-Albus; Doya 1999 | `motor-output` must emit structured `MotorFeedback` (predicted vs actual); `agent-runtime` must expose this to skill refinement |
| 3 | BG direct pathway releases; indirect suppresses | Alexander et al. 1986 | A committed intention is "released" to the queue; competing candidates are suppressed until the queue is clear or prioritisation changes |
| 4 | pre-SMA plans sequences without executing | Nachev et al. 2008 | Task decomposition in `agent-runtime` is a separate phase from execution — decompose-then-execute, never interleave |
| 5 | OFC: correct only task-relevant deviations | Todorov & Jordan 2002 | `motor-output` handles minor errors locally; only escalates goal-threatening failures to `executive-agent` |
| 6 | Bereitschaftspotential: preparation precedes intent | Kornhuber & Deecke 1965 | `agent-runtime` pre-stages tool parameters and fetches dependencies before the formal execute signal arrives |
| 7 | Dopamine RPE closes the actor-critic loop | Schultz et al. 1997 | `MotorFeedback` success/failure attaches a `RewardSignal` to the completed task; feeds back to executive-agent for goal and policy scoring |
| 8 | BG hyperdirect pathway: rapid global cancel | Aron & Poldrack 2006 | A stop signal (high-priority interrupt from any upstream module) must cancel the full execution queue — not just the current step |

---

## 7. Schemas Required by Phase 6

The following new shared-contract types are implied by the biological analysis:

| Schema | Purpose | Derives from |
|---|---|---|
| `executive-goal.schema.json` | Goal item: id, description, priority, lifecycle state, deadline, policy constraints | PFC goal stack; BG direct/indirect gating |
| `motor-feedback.schema.json` | Action outcome: action_id, predicted_state, actual_state, deviation_score, escalate_flag | Spinocerebellar feedback loop; OFC minimal correction principle |
| `policy-decision.schema.json` | OPA evaluation result: decision (allow/deny), violations[], explanation | ACC conflict detection; BG hyperdirect abort |
| `action-spec.schema.json` | Parameterised action for dispatch: type, channel, params, idempotency_key | M1 corticospinal command; dynamical systems pre-staging |

These must be landed in `shared/schemas/` before Phase 6 implementation begins.
