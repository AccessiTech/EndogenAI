# Phase 7 — Group IV: Adaptive Systems — Neuroscience Research (D1)

_Generated: 2025-07-14 by Docs Executive Researcher_

_Sources:_
- _docs/research/sources/phase-7/bio-reinforcement-learning.md (Wikipedia: Reinforcement learning)_
- _docs/research/sources/phase-7/bio-temporal-difference-learning.md (Wikipedia: Temporal difference learning)_
- _docs/research/sources/phase-7/bio-synaptic-plasticity.md (Wikipedia: Synaptic plasticity)_
- _docs/research/sources/phase-7/bio-basal-ganglia.md (Wikipedia: Basal ganglia)_
- _docs/research/sources/phase-7/bio-cerebellum.md (Wikipedia: Cerebellum)_
- _docs/research/sources/phase-7/bio-anterior-cingulate-cortex.md (Wikipedia: Anterior cingulate cortex)_
- _docs/research/sources/phase-7/bio-metacognition.md (Wikipedia: Metacognition)_
- _docs/research/sources/phase-7/bio-prefrontal-cortex.md (Wikipedia: Prefrontal cortex)_
- _resources/neuroanatomy/basal-ganglia.md_
- _resources/neuroanatomy/cerebellum.md_
- _resources/neuroanatomy/limbic-system.md_
- _resources/neuroanatomy/hippocampus.md_

---

## 1. Overview

Phase 7 (Group IV: Adaptive Systems) implements the brain's cross-cutting adaptation and
self-monitoring layers. Unlike Phases 1–6, which implement discrete signal-processing,
cognitive, and executive-output circuits, Phase 7 implements the **learning loop** and the
**metacognitive loop** — the mechanisms by which the system improves over time and evaluates
the quality of its own operation.

Two modules are in scope:

| Module | Biological Analogue | Primary Brain Regions |
|---|---|---|
| `learning-adaptation` (§7.1) | Dopaminergic reinforcement / synaptic Hebbian plasticity | Basal ganglia (striatum / SNc), cerebellum (Purkinje / climbing fibre), hippocampus (experience replay) |
| `metacognition` (§7.2) | Prefrontal self-monitoring / cingulate error detection | Prefrontal cortex (BA 10/46), anterior cingulate cortex (BA 24/32), posterior parietal cortex |

Both modules receive signals from earlier phases (Phase 5 memory and affective modules; Phase 6
motor-output and executive-agent modules) and produce feedback that modifies system behaviour
going forward. This is the brain's endogenous training loop.

---

## 2. Module §7.1 — Learning & Adaptation

### 2.1 Biological Basis: Reinforcement Learning as TD Learning

The biological model for machine learning with rewards is the **dopamine prediction error (RPE)**
system, formalised as temporal difference (TD) learning (Schultz, Dayan & Montague 1997;
Sutton 1988).

**Key findings from `bio-temporal-difference-learning.md`:**

- VTA/SNc dopamine neurons produce phasic firing that closely mirrors the **TD error** signal
  $\delta_t = R_{t+1} + \gamma V(S_{t+1}) - V(S_t)$
- When a monkey is initially rewarded by juice: dopamine fires at reward delivery (unexpected).
  After conditioning to a predictive stimulus: dopamine fires at the cue, not the juice.
  When the predicted reward is omitted: dopamine dips below baseline — the negative TD error.
- This maps directly to the actor-critic RL architecture: the **striatum (ventral/dorsal)** forms
  the value estimate (critic), while the **thalamo-cortical circuits** select actions (actor).

**Key findings from `bio-basal-ganglia.md`:**

- **Direct pathway** (D1 receptor): Go signal — action facilitation via disinhibition of thalamus.
- **Indirect pathway** (D2 receptor): NoGo signal — action suppression via GPe → STN → GPi.
- **Hyperdirect pathway**: rapid broad suppression via STN — fast veto mechanism.
- Dopamine modulates the direct/indirect balance as a teaching signal. High dopamine (unexpected
  reward) potentiates direct pathway; low dopamine (omission) potentiates indirect pathway.
- SNc projects to **dorsal striatum** (dorsomedial caudate = goal-directed; dorsolateral putamen =
  habits); VTA projects to **ventral striatum** (nucleus accumbens = motivation/reward).

**Key findings from `bio-reinforcement-learning.md`:**

- RL is formally modelled as a **Markov Decision Process**: agent in state $S$, takes action $A$,
  receives reward $R$, transitions to $S'$. Goal: maximise expected discounted return
  $G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1}$.
- **Actor-critic** algorithms split the policy (actor, parametrised $\pi_\theta$) from the value
  function (critic $V_\phi$): the critic provides $\delta_t$ to update both.
- Modern variants most relevant to EndogenAI:
  - **PPO** (Proximal Policy Optimisation): clips policy update ratio — stable, on-policy,
    widely adopted for continuous action spaces.
  - **SAC** (Soft Actor-Critic): off-policy, entropy-regularised, sample-efficient with
    continuous actions.
  - **DQN** (Deep Q-Network): off-policy, discrete actions, experience replay buffer —
    directly models the TD update.

### 2.2 Biological Basis: Cerebellar Supervised Learning for Skill Consolidation

The cerebellum implements a complementary, supervised learning system that operates in parallel
with the basal ganglia RL loop. Rather than optimising for reward, the cerebellum minimises
**motor/execution error** using an internal forward model.

**Key findings from `bio-cerebellum.md`:**

- **Marr-Albus-Ito model**: climbing fibres (from inferior olivary nucleus) carry the
  **teaching signal** (execution error); parallel fibres carry the **state signal**;
  Purkinje cells compute the corrected output.
- **Cerebellar LTD** (long-term depression at parallel fibre – Purkinje cell synapses) underlies
  skill consolidation: repeated errors weaken the parallel fibre synapses that predicted the
  wrong action, gradually refining the motor program.
- The stub in `resources/neuroanatomy/cerebellum.md` contains an **explicit Phase 7 forward
  reference**: *"Marr-Albus climbing fibre: execution errors logged as `skill_feedback` events;
  structured for Phase 7 skill refinement."*
- Cerebellar learning is **fast** (within seconds to minutes of repetition) and encodes
  **procedural/implicit memory** — distinct from the hippocampal declarative system.

**Phase 7 derivation**: the `learning-adaptation` module should implement a two-track
learning system:
1. **RL track** (basal ganglia analogue): policy improvement via reward signal from
   `MotorFeedback.reward_signal` (Phase 6 output).
2. **Supervised-error track** (cerebellar analogue): skill consolidation via execution
   error feedback from `MotorFeedback.skill_feedback` — direct gradient correction of
   task-specific behaviour, faster than policy gradient.

### 2.3 Biological Basis: Hippocampal Experience Replay

The hippocampus plays a critical role not in real-time adaptation but in **offline consolidation
through replay** — a process that dramatically improves sample efficiency.

**Key findings from `resources/neuroanatomy/hippocampus.md` + `bio-reinforcement-learning.md`:**

- Sharp-wave ripples (SWR) during non-REM sleep produce rapid sequential replay of recently
  experienced state-action trajectories — consolidating them into neocortical long-term memory.
- DQN's **experience replay buffer** is the direct computational analogue: storing transitions
  $(S_t, A_t, R_t, S_{t+1})$ and replaying them randomly to break temporal correlation and
  improve sample efficiency.
- **Prioritised experience replay** (higher sampling probability for transitions with large TD
  error) mirrors how the hippocampus preferentially replays surprising or salient events.

**Phase 7 derivation**: the `learning-adaptation` module must maintain a `ReplayBuffer` collection
in ChromaDB (`brain.learning-adaptation`) storing vectorised episode transitions for offline
training steps.

### 2.4 Biological Basis: Synaptic Plasticity as Weight Update

**Key findings from `bio-synaptic-plasticity.md`:**

- **Hebbian rule**: "cells that fire together, wire together." NMDA receptor-gated Ca²⁺ influx
  is the trigger: large influx → LTP (synapse strengthened); small influx → LTD (synapse weakened).
- **STDP (Spike-Timing-Dependent Plasticity)**: the *precise timing* of pre- vs post-synaptic
  firing determines LTP or LTD. Pre before post → potentiation; post before pre → depression.
  This is a biologically precise Hebbian rule.
- **Homeostatic plasticity (synaptic scaling)**: prevents runaway potentiation — reduces all
  synaptic weights proportionally when a neuron fires too frequently.
- In RL terms: each gradient update to model weights is a batch of Hebbian updates;
  learning-rate scheduling and weight decay correspond to metaplasticity.

### 2.5 Implementation Map for `learning-adaptation`

| Biological finding | Implementation decision |
|---|---|
| SNc/VTA dopamine = TD error signal | `RewardSignal.delta` field provides $\delta_t$ after each environment step |
| Direct/indirect pathways balance | Actor-critic split: PPO actor network + value head |
| Cerebellar LTD = skill consolidation | `skill_feedback` events trigger supervised fine-tuning of task-specific policy head |
| Hippocampal replay = experience replay | `ReplayBuffer` collection in `brain.learning-adaptation`; replay sampled each training step |
| Hebbian LTP/LTD = weight update | PyTorch gradient descent; learning rate schedules as metaplasticity |
| Dorsolateral striatum = habit encoding | Stable, frozen policy checkpoints for recurring task types |
| Nucleus accumbens = motivation weighting | `RewardSignal.magnitude` scales learning rate per episode |

---

## 3. Module §7.2 — Metacognition & Monitoring

### 3.1 Biological Basis: Prefrontal Metacognitive Monitoring

Metacognition — cognition about cognition — has a well-established neural substrate centred on
the **prefrontal cortex (PFC)**, particularly anterior and lateral sub-regions.

**Key findings from `bio-metacognition.md`:**

- **Flavell (1976)**: metacognition is the active monitoring and regulation of one's own cognitive
  processes. Two components: *metacognitive knowledge* (stable beliefs about one's abilities) and
  *metacognitive regulation* (monitoring, evaluating, correcting).
- **Nelson & Narens (1990)**: proposed a hierarchical model with a *meta-level* (monitoring:
  information flows up) and an *object-level* (control: intervention flows down).
- **Neural substrates** (Fleming et al. 2014): **anterior prefrontal cortex (BA 10)** is the
  primary substrate for *perceptual* metacognition (confidence about whether you saw something).
  **Precuneus** (posterior medial parietal) for memory metacognition (confidence about recall).
- Shimamura (2000): PFC implements **dynamic filtering** — the ability to inhibit irrelevant
  signals and selectively amplify metacognitive signals.

**Key findings from `bio-prefrontal-cortex.md`:**

- Miller & Cohen integrative theory: PFC exerts **top-down biasing** on posterior areas,
  actively maintaining task representations that guide behaviour in the face of interference.
- DLPFC (BA 9/46) supports working memory and performance monitoring; OFC (BA 11/47) integrates
  reward value; vmPFC (BA 10/11) tracks uncertainty and expected outcomes.

### 3.2 Biological Basis: ACC Error Detection and Conflict Monitoring

The anterior cingulate cortex is the brain's **real-time performance evaluator**, generating the
error-related negativity (ERN) signal that triggers corrective action.

**Key findings from `bio-anterior-cingulate-cortex.md`:**

- ACC is active during **conflict** (competing action representations), **errors**
  (incorrect response commission), and **violation of expectancy** (unexpected outcomes).
- **Error-Related Negativity (ERN)**: a negative ERP component generated by ACC within 100ms of
  an error. The amplitude grows with the cost/unexpectedness of the error.
- Reinforcement learning ERN theory (Holroyd & Coles 2002): ACC monitors for mismatch between
  actual and expected outcomes — exactly the prediction error signal.
- **Dorsal ACC** (BA 24/32): active during both errors and correct responses when effort is high
  — monitoring function. **Rostral/subgenual ACC** (BA 24): active after errors with affective
  loading — evaluative function. Both activate in response to reward wins/losses.
- Lesions: damage to ACC produces **inability to detect errors**, severe Stroop interference
  difficulty, and akinetic mutism.
- The dACC is connected to DLPFC and parietal cortex (top-down), and to amygdala and nucleus
  accumbens (bottom-up affective) — an interface between cognitive and emotional systems.

### 3.3 Biological Basis: Confidence Estimation in Parietal Cortex

Beyond error detection, the brain maintains **confidence signals** about the quality of its
current outputs.

**Key findings from `bio-metacognition.md` + `bio-prefrontal-cortex.md`:**

- **Posterior parietal cortex** (particularly the precuneus and lateral intraparietal area / LIP)
  encodes decision confidence — how certain the system is about the current action/output.
- Confidence is computed as the *difference between choice evidence and competing evidence*, and
  is updated continuously by ACC error signals.
- When confidence falls below threshold AND no error signal is detected (the "unknown unknown"
  state), the PFC initiates exploratory behaviour — analogous to an anomaly escalation trigger.

### 3.4 Biological Basis: The Metacognitive Control Loop

In the healthy brain, the metacognitive loop operates as:

```
Output produced (Phase 6) →
  ACC detects error/mismatch → ERN generated →
    PFC evaluates severity and confidence →
      If within bounds: adapt via learning signal →
      If out of bounds: escalate (raise alarm, inhibit output, request help)
```

This is the biological basis for the entire `metacognition` module design:

| Stage | Region | Signal | EndogenAI implementation |
|---|---|---|---|
| 1. Output production | Phase 6 execution | `MotorCommand`, `AgentResponse` | Phase 6 output streams |
| 2. Error detection | ACC (dACC) | ERN voltage deflection | OTel span with `error_detected=true` |
| 3. Error evaluation | ACC (rostral) + DLPFC | ERN amplitude / reward deviation | `confidence_score` computed from `RewardSignal.delta` magnitude |
| 4a. Within-bounds correction | Cerebellum / BG | Incremental weight update | Pass delta to `learning-adaptation` module |
| 4b. Out-of-bounds escalation | PFC → amygdala / external | Alarm / inhibition signal | OTel alert → Prometheus alertmanager |

### 3.5 Implementation Map for `metacognition`

| Biological finding | Implementation decision |
|---|---|
| ACC ERN = error detection | Instrument each task execution with OTel spans; flag anomalies as span events |
| ERN amplitude = error severity | `confidence_score` metric tracks deviation from expected performance baseline |
| Dorsal ACC: monitoring | `error_rate_per_task` Prometheus gauge via OTel Prometheus exporter |
| Rostral ACC: affective evaluation | `reward_deviation_zscore` metric — distance from running mean in std dev units |
| PFC confidence threshold | Configurable threshold in `monitoring.config.json`; triggers corrective action |
| Escalation pathway (PFC → external) | Prometheus alertmanager rule fires when `confidence_score < threshold` for N steps |
| Posterior parietal confidence | `task_confidence` histogram tracks per-task confidence distribution |
| Metacognitive regulation (Nelson & Narens) | `metacognition` module acts as meta-level; `learning-adaptation` acts as object-level |

---

## 4. Cross-Phase Biological Context

### 4.1 Continuity from Phase 5 (Memory) and Phase 6 (Executive)

Phase 7 does not operate in isolation — it receives and returns signals to previous phases:

| Source phase | Output (becomes Phase 7 input) | Phase 7 use |
|---|---|---|
| Phase 5 §5.3 Long-Term Memory | `ConsolidationSignal`, `MemoryItem` vectors | Experience replay sampling from episodic store |
| Phase 5 §5.5 Motivation | `RewardSignal.magnitude` | Scales learning rate; gates exploration |
| Phase 6 `motor-output` | `MotorFeedback.reward_signal` | Primary TD error input for `learning-adaptation` |
| Phase 6 `motor-output` | `MotorFeedback.skill_feedback` | Cerebellar-track supervised error signal |
| Phase 6 `executive-agent` | `AgentResponse`, `EthicsViolation` events | Monitor inputs for `metacognition` |

### 4.2 Habit vs. Goal-Directed Behaviour (Dual System)

A key biological insight is the **dual-system** within the basal ganglia:

- **Goal-directed control** (dorsomedial striatum / caudate): sensitive to reward devaluation;
  flexible but computationally expensive. Maps to model-based RL.
- **Habitual control** (dorsolateral striatum / putamen): insensitive to reward devaluation;
  rigid but fast. Maps to model-free RL.

The transition from goal-directed to habitual is driven by **overtraining** and
**practice repetition** — incrementally shifting from dorsomedial to dorsolateral loop engagement.

**Phase 7 derivation**: the `learning-adaptation` module should implement a habit detection
mechanism — when a policy has been stable for N episodes with high confidence, promote it to a
cached "habit" policy stored in the `brain.learning-adaptation` collection. This reduces
inference cost for frequently-exercised task types.

---

## 5. Brain Region Summary

| Region | BA | Phase 7 Role | Maps to |
|---|---|---|---|
| Substantia nigra pars compacta (SNc) | — | Dopamine RPE teacher signal | `RewardSignal.delta` |
| Ventral tegmental area (VTA) | — | Motivational dopamine projection to NA | `RewardSignal.magnitude` × `motivation_weight` |
| Nucleus accumbens | — | Motivation × reward salience signal | Learning-rate modulation |
| Caudate nucleus (dorsomedial) | — | Goal-directed RL (model-based) | PPO/SAC policy actor |
| Putamen (dorsolateral) | — | Habit encoding (model-free) | Cached policy checkpoints |
| Cerebellar cortex (Purkinje cells) | — | Supervised error correction (LTD) | `skill_feedback` supervised loss |
| Inferior olive (climbing fibre) | — | Teaching error signal for cerebellum | `skill_feedback` events |
| Hippocampus (CA1/CA3) | — | Experience replay buffer | `brain.learning-adaptation` ChromaDB collection |
| Anterior PFC | BA 10 | Metacognitive confidence estimation | `task_confidence` metric |
| DLPFC | BA 9/46 | Performance monitoring + working memory | Span attributes in OTel trace |
| Rostral ACC | BA 24/32 | Error detection, ERN generation | OTel span event `error_detected` |
| Dorsal ACC | BA 24 | Conflict monitoring, task evaluation | `error_rate_per_task` gauge |
| Posterior parietal cortex | BA 7 | Decision confidence accumulation | `confidence_score` metric |

---

## 6. Open Questions for Phase Executive

1. **Dual-track learning**: should the cerebellar supervised-error track be implemented as a
   separate loss head on the PPO network, or as a distinct fine-tuned model? The biology
   suggests the former (shared weights, separate update paths).
2. **Hippocampal replay timing**: should replay occur in a background async loop (akin to
   offline sleep consolidation) or synchronously after each episode? The biology strongly
   suggests async/offline, but this has latency implications.
3. **Confidence metric granularity**: should confidence be per-task-type, per-model-call, or
   per-session? The ACC evidence suggests per-execution-step is biologically appropriate.
4. **Metacognition scope**: does the `metacognition` module monitor only Phase 6 outputs, or
   also Phase 5 memory retrieval quality and Phase 4 perception accuracy? The PFC top-down
   model suggests cross-phase monitoring is biologically correct but architecturally complex.
5. **Habit promotion threshold**: what constitutes "stable" enough to promote a policy to
   habit status? Needs a value from the Phase Executive or from empirical observation.
