# Phase 9 — D1: Neuroscience of Security, Deployment & Documentation

_Generated: 2026-03-04 by Docs Executive Researcher_

> **Scope**: Biological analogues for Phase 9 sub-phases — Security, Deployment & Documentation.
> This document maps brain structures and mechanisms to each Phase 9 sub-component.
> Sub-phases: 9.0 Deferred Phase 8 Items · 9.1 Security & Sandboxing · 9.2 Deployment & Scaling · 9.3 Self-Documentation & Schema

**Sources fetched**: `docs/research/sources/phase-9/bio-*.md` (17 files, fetched 2026-03-04)

---

## Overview

Phase 9 addresses how a complex, multi-module cognitive system achieves **safety, operability, and self-knowledge at production scale**. These are not afterthoughts — the biological brain has evolved deeply intertwined solutions to exactly these problems:

- It maintains **immune privilege** and regional isolation to protect neural processing from systemic threats (security/sandboxing).
- It **deploys new neurons** into living circuits without disrupting ongoing function, scaling resources dynamically to metabolic demand (deployment/scaling).
- It models itself via the **default mode network and metacognitive systems**, constructing narrative self-knowledge that guides future behaviour (self-documentation).
- It completes **deferred consolidation** offline — replaying experiences during sleep to finish what real-time processing could not (deferred completions).

Each analogy below directly seeds Phase 9 implementation decisions.

---

## §9.0 — Deferred Process Completion: Brain Analogues

### The Brain's Offline Completion System

During waking hours the brain operates under severe resource constraints — not every experience is fully processed in real time. The brain has evolved an elegant solution: **offline replay and memory consolidation** during sleep and quiet wakefulness.

#### Memory Consolidation and Hippocampal Replay

**Memory consolidation** is the process by which initially labile, hippocampus-dependent memories are progressively stabilized into neocortical long-term storage. Two phases are well-established:

- **Synaptic consolidation** (hours): protein-synthesis-dependent synaptic strengthening at the cellular level, mediated by NMDA receptor activation, AMPA receptor trafficking, and late-phase LTP (L-LTP). This is the rapid, local first pass.
- **Systems consolidation** (weeks to years): the hippocampus acts as a temporary binding site, coordinating reactivation of distributed neocortical representations until cortical circuits become self-sustaining. Over time the hippocampal index becomes redundant.

**Hippocampal sharp-wave ripples (SWRs)** during slow-wave sleep are the mechanistic substrate: brief (50–100 ms), high-frequency (80–120 Hz) oscillations in CA1 that drive coordinated reactivation of recent experiences across the hippocampal–entorhinal–neocortical axis. Crucially, replay is **not random** — the sequences reactivated preferentially correspond to novel or reward-predictive experiences. The brain assigns priority to what matters most.

**Phase 9.0 mapping**: The `/api/agents` endpoint and `resources/subscribe` live notifications were explicitly deferred from the M8 milestone. Like memories not yet consolidated, they are present as traces in the system (stub handlers exist) but have not been fully integrated. Phase 9.0 is the system's **offline consolidation pass** — replaying incomplete wiring to complete integration.

#### Default Mode Network as Background Processor

The **Default Mode Network (DMN)** consists of medial prefrontal cortex (mPFC), posterior cingulate cortex (PCC), angular gyrus, and medial temporal lobe structures. It is active during rest, introspection, and future planning — the brain's "idle state" processing system. Key functions relevant to 9.0:

- **Prospective memory** — maintaining representations of incomplete tasks for future completion ("I still need to do X")
- **Narrative integration** — weaving together disparate experiences into a coherent self-model
- **Temporal bridging** — connecting past states to anticipated future states across gap intervals

The DMN activates most strongly when the brain is *not* actively processing external inputs — it handles exactly the kind of background housekeeping that Phase 9.0 represents.

#### Neurotransmitter Signalling as Event Propagation

The brain's notification system uses **volume transmission** — neurotransmitters released into the extracellular space diffuse broadly to receptors on many downstream cells. Dopamine and norepinephrine in particular operate this way, propagating state-change signals widely across the cortex. The key properties:

- **Broadcast**: a single locus coeruleus neuron can innervate large swaths of cortex
- **Fan-out**: one pre-synaptic terminal releases transmitter; multiple post-synaptic cells may respond
- **Asynchrony**: transmission delay is variable; receivers process at their own rate

This maps directly to the MCP `notifications/resources/updated` event pattern: a single Working Memory change triggers fan-out to all subscribers.

#### Diffusion Tensor Imaging as Traceparent

The brain's white matter **connectome** — the structural wiring diagram of long-range axonal tracts — is measured in vivo using diffusion tensor imaging (DTI), which infers the direction of water diffusion along myelinated axon bundles. The brain literally encodes trace paths in its physical structure. **Tractography** reconstructs end-to-end signal propagation routes from diffusion data, exactly as W3C `traceparent` allows distributed tracing systems to reconstruct cross-service signal paths.

Promoting `traceparent` to required in `mcp-context.schema.json` is the architectural equivalent of the brain ensuring all long-range projections are myelinated and traceable — it is a maturation signal, not merely a cleanup item.

| Brain mechanism | Phase 9.0 equivalent |
|---|---|
| Hippocampal SWR replay completing offline consolidation | Phase 9.0 completing deferred Phase 8 stubs: `/api/agents`, `resources/subscribe` |
| DMN prospective memory maintaining incomplete task representations | Workplan deferred annotations (`<!-- deferred from Phase 8 -->`) |
| Broadcast dopaminergic volume transmission | `notifications/resources/updated` fan-out to all SSE subscribers |
| DTI connectome / myelinated white-matter tracts | W3C `traceparent` propagated through every MCP-context envelope |
| Priority-weighted replay (novel/reward-predictive sequences replayed first) | `/api/agents` (user-visible) deferred before `traceparent` (infrastructure) |

---

## §9.1 — Security & Sandboxing: Brain Analogues

### The Brain's Multi-Layer Immune Architecture

The central nervous system is arguably the most strongly defended tissue in the human body — and it achieves this through a multi-layer, redundant security architecture that is worth studying carefully.

#### Immune Privilege

The CNS is an **immune-privileged site**: peripheral immune cells are largely excluded from neural parenchyma under healthy conditions. This privilege is enforced by:

1. **Blood-brain barrier (BBB)** — endothelial tight junctions, astrocyte end-feet, and pericytes create a physical barrier excluding large molecules and most immune cells. Under normal conditions, no peripheral T cells or B cells enter.
2. **Absence of classical MHC class II antigen presentation** — neurons do not normally express MHC-II, making them invisible to CD4+ T helper cells. Pathogens within neurons are partially shielded from adaptive immune attack.
3. **Immunosuppressive microenvironment** — TGF-β, IL-10, and CD200 ligands in the CNS actively suppress immune activation even when immune cells do enter.
4. **Blood-CSF barrier (choroid plexus)** — a separate, slightly more permeable barrier at the choroid plexus allows selective immune surveillance via CSF circulation.

**Phase 9.1 mapping**: Module sandboxing with gVisor and OPA enforces an analogous multi-layer privilege model. Each module container is an immune-privileged compartment: the gVisor `runsc` application kernel is the BBB (preventing syscall-level escape), OPA policies are the MHC-presentation rules (defining which capabilities each module may exercise), and Kubernetes NetworkPolicy is the physical tissue boundary (controlling which modules may communicate).

#### Microglia as Policy Enforcement Agents

**Microglia** are the brain's resident immune cells — constituting 10–15% of all brain cells. They are derived from yolk-sac macrophages and permanently reside within the CNS parenchyma, distinct from peripheral macrophages. Key properties:

- **Continuous surveillance**: microglia extend and retract fine processes at ~1 µm/min in their "resting" state, sampling their local chemical environment constantly. They are always patrolling, not waiting for alarms.
- **Pattern recognition**: microglia express Toll-like receptors (TLRs, especially TLR2, TLR4, and TLR9), NOD-like receptors (NLRs), and other pattern recognition receptors (PRRs) that detect **pathogen-associated molecular patterns (PAMPs)** and **damage-associated molecular patterns (DAMPs)**.
- **Graduated response**: on detection of threat signals, microglia shift from a ramified (surveillance) state to an amoeboid (activated) state with progressively amplified response levels — phagocytosis, cytokine secretion, or triggering adaptive immune cascade.
- **Synaptic pruning** in development: microglia eliminate weak synapses tagged with complement proteins C1q and C3 — a quality-control function as well as a security one.

**Phase 9.1 mapping**: OPA functions as the microglial layer — always running policy checks on every inter-module request (continuous evaluation), matching request attributes against Rego rules (pattern recognition), and returning graduated responses (allow / deny / audit-log). Like microglia that shift from surveillance to activation, OPA can be configured for dry-run (audit) mode that logs policy violations without blocking, then promoted to enforce mode.

#### Apoptosis as Container Termination Policy

**Apoptosis** (programmed cell death) is the brain's mechanism for eliminating compromised, infected, or developmentally redundant cells without triggering inflammation. The intrinsic mitochondrial pathway activates when a cell's internal state is detected as unrecoverable; the extrinsic pathway activates via Fas ligand / TNF-family death receptors on the cell surface. Both converge on caspase activation and controlled cellular dismemberment:

- DNA is fragmented into nucleosomal units
- Plasma membrane blebs form, packaging cell contents into apoptotic bodies
- Phagocytes clear the bodies without releasing inflammatory signals (unlike necrosis)

This controlled, clean shutdown is exactly the design pattern for container pod eviction: a graceful `SIGTERM` with a termination grace period, allowing the container to finish in-flight requests and flush buffers before `SIGKILL`. gVisor sandboxed containers terminate within their application kernel boundary, ensuring syscall isolation is maintained even during shutdown.

#### Pattern Recognition Receptors and Danger Signalling

The **Danger Hypothesis** (Polly Matzinger, 1994) reframed immune activation: the immune system does not primarily distinguish "self" from "non-self" but rather responds to **danger signals** — molecules released by stressed, dying, or damaged cells (DAMPs: HMGB1, ATP, uric acid, heat shock proteins). This is more nuanced than the classic PAMPs-only model:

- Sterile injury (no pathogen) can trigger full immune response via DAMPs
- Normal cellular contents become danger signals when released into the extracellular space
- The immune system learns "what should not be here" from context

**Phase 9.1 mapping**: OPA policy rules should be written as danger-signal detectors, not just pathogen-pattern matchers. A module requesting capabilities far outside its declared `agent-card.json` scope is a DAMP — the capability is not inherently malicious, but its presence in that context signals a potential compromise or misconfiguration. This motivates capability-bounded OPA rules derived from each module's `agent-card.json` capabilities array.

#### Glial Boundary Enforcement

**Astrocytes** form the structural scaffold of the CNS and play critical roles in boundary enforcement:

- **Glial scar** formation: after injury, reactive astrocytes deposit a dense extracellular matrix (largely chondroitin sulfate proteoglycans) that forms a physical barrier around damaged tissue, containing spread of damage.
- **Astrocytic end-feet** form tight contacts with blood vessel endothelium, contributing to BBB integrity.
- **Gap junctions** between astrocytes create a coupled syncytium that spreads small molecules (including alarm signals like IP3) across tissue compartments.

| Brain mechanism | Phase 9.1 equivalent |
|---|---|
| BBB tight junctions excluding peripheral immune cells | gVisor `runsc` kernel — modules cannot make raw syscalls past the application kernel boundary |
| CNS immune privilege / MHC-II absence | OPA capability isolation rules — modules have no inherent right to access other modules' resources |
| Microglial continuous surveillance + pattern recognition (TLRs, NLRs) | OPA sidecar continuously evaluating Rego policies on every inter-module request |
| Apoptosis — clean, contained cell termination without inflammation | Container pod eviction: graceful SIGTERM → drain → SIGKILL; gVisor sandbox maintains isolation during shutdown |
| Danger hypothesis — DAMP detection, context-sensitive threat signals | Capability-anomaly OPA rules: requests exceeding agent-card declared capabilities trigger audit/block |
| Astrocytic end-feet / glial scar — structural boundary maintenance | Kubernetes NetworkPolicy — static namespace-level egress rules prevent lateral movement between module pods |
| SPIFFE/SVID workload identity | Cell-surface MHC-I antigen presentation — each cell (workload) presents its identity for immune (network) recognition |

---

## §9.2 — Deployment & Scaling: Brain Analogues

### How the Brain Packages, Ships, and Scales Functional Units

The brain solves exactly the engineering problems of deployment and autoscaling through its developmental and operational biology.

#### Adult Neurogenesis — Deploying New Units Into a Live System

**Adult neurogenesis** occurs in two well-established niches in the mammalian brain: the subgranular zone (SGZ) of the hippocampal dentate gyrus, and the subventricular zone (SVZ) of the lateral ventricles (source of olfactory bulb interneurons). Key process:

1. **Radial glia as scaffolding**: Newly born neurons (from neural stem cells) migrate along radial glial fibers — scaffold structures that extend from the ventricular surface to the pial surface. Radial glia are the brain's Kubernetes Nodes — they provide the physical substrate into which new cells are deployed.
2. **Cell migration under chemical guidance**: Migrating neuroblasts follow chemoattractant gradients (netrin, sonic hedgehog, CXCL12) and chemorepellent gradients (semaphorins, slits). Migration takes days to weeks — and during this time the existing circuit continues to operate.
3. **Synaptic integration**: New neurons form synapses progressively — first with inhibitory (GABAergic) inputs (which are initially depolarizing in immature cells due to high intracellular Cl⁻), then gradually integrating excitatory inputs as they mature. New nodes come online incrementally, not all at once.
4. **Activity-dependent survival**: Only ~50% of newborn neurons survive to maturity. Survival is gated by synaptic activity — neurons that successfully connect to the existing circuit survive; those that fail to integrate undergo apoptosis. The brain performs **liveness probes** on new neurons.
5. **Functional role**: Adult-born hippocampal neurons are preferentially recruited during pattern separation tasks (distinguishing similar stimuli)  — suggesting the brain specifically targets new cell deployment at computational bottlenecks.

**Phase 9.2 mapping**: Deploying a new module container into the Kubernetes cluster mirrors neurogenesis precisely. The `Deployment` manifest is the genetic program; the Node is the radial glia scaffold; readiness probes are the synaptic integration check; liveness probes are the activity-dependent survival gate. HPA is the activity-dependent survival rate at scale — pods that receive load survive, idle pods are pruned.

#### Cortical Columns — Modular Self-Contained Functional Units

The **cortical column** (Mountcastle, 1957) is the fundamental repeating modular unit of neocortex. Columns are ~300–600 µm wide, span all six cortical layers, and contain ~80–120 neurons (minicolumn) or ~300–600 minicolumns per hypercolumn. Properties:

- **Vertical organization**: neurons within a column share receptive field properties (location, orientation, ocular dominance). All neurons at the same horizontal position respond to the same feature.
- **Self-contained processing**: a column contains the full laminar circuit — L4 receives thalamic input, L2/3 performs local computation, L5/6 projects output. It is a complete processing unit.
- **Modular specialization**: the barrel cortex is the clearest example — each barrel corresponds precisely to one whisker, with sharp boundaries between adjacent barrels. Damage to a barrel affects only that whisker's representation.
- **Tiling**: columns tile the cortical surface, each with its own interface (receptive field) but with largely identical internal wiring. Like Docker containers from the same image — identical internal structure, different external interface (port, volume).

**Phase 9.2 mapping**: Each EndogenAI module is a cortical column — a self-contained processing unit with defined inputs (`MCP context`) and outputs (`Signal`, `RewardSignal`), identical internal structure (Python + LiteLLM + ChromaDB), but specialized for its domain. The `Dockerfile` is the program that builds the column's internal wiring; the `agent-card.json` is its receptive field specification.

#### Myelination — Performance Optimization at Deployment Time

**Myelination** is the progressive wrapping of axons with myelin (a lipid-rich membrane produced by oligodendrocytes in the CNS) that dramatically increases signal conduction velocity via saltatory conduction (10–100× faster than unmyelinated axons). Key properties:

- Myelination proceeds in a specific spatial and temporal programme during development — sensory and motor pathways myelinate before association areas; primary areas before secondary.
- The process is activity-dependent: axons that fire frequently get myelinated preferentially.
- **Incomplete myelination** in human infants explains many developmental limitations; myelination continues into the mid-20s.
- Myelination effectively **packages** an axon for reliable, high-speed operation — the production-ready state for a white-matter tract.

**Phase 9.2 mapping**: Docker multi-stage builds are the myelination step — taking a development-ready module (the unmyelinated axon, with all its build deps, dev flags, and intermediate artifacts) and producing a production-optimized image (the myelinated axon: smaller, faster, reliable). The final image is the production-ready signal pathway.

#### Cerebral Autoregulation — Autoscaling to Metabolic Demand

**Cerebral autoregulation** maintains relatively constant cerebral blood flow (CBF) (~50 mL/100g/min) across a wide range of perfusion pressures (50–150 mmHg). Under normal conditions a ±30% change in arterial pressure produces only ~5% change in CBF. The mechanism:

- **Myogenic response**: smooth muscle in arteriolar walls directly senses transmural pressure and constricts in response to pressure increases (Bayliss reflex).
- **Metabolic (neurovascular) coupling**: local increases in neural activity → increased metabolic demand → local vasodilation via multiple mediators (nitric oxide, potassium, adenosine, prostaglandins, astrocyte Ca²⁺ signalling). fMRI BOLD signal is a direct readout of this coupling.
- **Regional CBF regulation**: PET and fMRI demonstrate that CBF increases precisely in brain regions actively engaged in a cognitive task — the brain's per-region autoscaling.

**Phase 9.2 mapping**: Kubernetes HPA is cerebral autoregulation — it senses metabolic demand (CPU/memory utilization, custom Prometheus metrics) and scales the vascular supply (pod replicas) to match. The Prometheus custom metrics adapter is the astrocyte Ca²⁺ signalling — translating specific cognitive load signals (request rate, queue depth) into scaling decisions more precise than simple CPU thresholds.

#### Synaptic Pruning — Eliminating Unused Connections

**Synaptic pruning** peaks during human adolescence, eliminating ~40% of synaptic connections present at age 2. Mechanism:
- Complement proteins C1q and C3 tag weak/inactive synapses.
- Microglia recognize the complement tag and phagocytose the labeled synaptic terminals.
- Activity-dependent: active synapses are protected from tagging (BDNF / PSD-95 signalling); silent synapses are vulnerable.

**Phase 9.2 mapping**: Kubernetes resource limits and pod eviction policies are synaptic pruning. A pod with insufficient activity (HPA minimum, idle replicas) is evicted. Liveness probe failures trigger pod restart — complement tagging of a failing synapse. The `terminationGracePeriodSeconds` is the interval between C1q tagging and microglial phagocytosis.

| Brain mechanism | Phase 9.2 equivalent |
|---|---|
| Radial glia scaffolding for neuronal migration | Kubernetes Node as deployment substrate |
| Activity-dependent neuron survival (liveness gate) | Kubernetes liveness/readiness probes on new module pods |
| Cortical column — modular, self-contained, tiled functional unit | Per-module Docker container built from identical Dockerfile template |
| Multi-stage axonal myelination (development → production optimization) | Docker multi-stage build: dev image → production image |
| Neurovascular coupling / CBF autoregulation | Kubernetes HPA: CPU/memory metrics → replica count |
| Synaptic pruning of inactive connections | Pod eviction of idle replicas; liveness-probe-triggered restart |
| Regional specialization within standard laminar circuit | `agent-card.json` declares each module's specialization within a standard container template |

---

## §9.3 — Self-Documentation & Schema: Brain Analogues

### The Brain's Self-Modeling Architecture

Self-documentation is not a filing exercise — it is the brain's core cognitive strategy. The ability to model itself, predict its own future states, and accumulate schema representations of its own structure underpins higher-order cognition.

#### Default Mode Network — The Brain's Documentation System

The **Default Mode Network (DMN)** (Raichle, 2001) — mPFC, PCC, angular gyrus, hippocampus, and medial temporal lobe — is paradoxically most active during unfocused "rest" states and actively deactivated during demanding external tasks. Its known functions:

- **Autobiographical memory construction**: integrating episodic memories into a coherent self-narrative
- **Prospective simulation**: imagining future scenarios ("mental time travel"), drawing on episodic memory structures
- **Social cognition**: theory of mind, understanding others' mental states
- **Self-referential processing**: thinking about oneself, one's traits, values, and identity

The DMN is effectively the brain's **architecture documentation layer** — it maintains a running model of what the system is, what it has done, and what it should do, independent of current task execution.

**Phase 9.3 mapping**: Documentation completion in Phase 9.3 is not an add-on — it is the DMN pass: constructing a coherent, self-referential narrative of the entire system that allows future agents (and developers) to orient quickly. Cross-linked documentation (docs that reference other docs, code that references specs) is the DMN's angular gyrus function — binding disparate memory representations into an integrated self-model.

#### Metacognition — Thinking About Thinking

**Metacognition** (Flavell, 1979; Dunning-Kruger, 1999) is the capacity to monitor and regulate one's own cognitive processes. It has two components:

- **Metacognitive knowledge**: what one knows about how one's cognitive system works (declarative)
- **Metacognitive monitoring**: real-time assessment of the quality and progress of one's own thinking (procedural)
- **Metacognitive control**: adjusting cognitive strategies based on monitoring signals

Neural substrates: the **anterior prefrontal cortex (aPFC)** (Brodmann area 10) is consistently activated in metacognitive tasks; the **anterior anterior insula** tracks prediction errors about one's own performance; the ACC monitors conflict and errors, triggering strategy adjustment.

**Phase 9.3 mapping**: The `docs/guides/` directory is metacognitive knowledge — declarative documentation about how the system works. The `observability/` stack is metacognitive monitoring. Flagging remaining documentation gaps (§9.3 incomplete items) is metacognitive control — the system identifies where its self-model is incomplete and routes attention.

#### Predictive Coding — Documentation as a Generative Model

**Predictive coding** (Rao & Ballard, 1999; Friston's Free Energy Principle, 2010) posits that the brain maintains a hierarchical **generative model** of its environment and its own states. Perception is not bottom-up feature extraction but top-down prediction refinement:

- The brain generates predictions about expected sensory input at each level of the cortical hierarchy.
- Prediction errors (residuals between prediction and actual input) propagate upward.
- The brain updates its generative model to minimize prediction error (free energy minimization).

The key insight for documentation: **documentation is the brain's generative model of the codebase**. When a developer reads the docs and then looks at the code, they are testing predictions. Outdated docs produce large prediction errors (confusion, debugging overhead). Accurate docs produce small prediction errors (the code does what the docs say). Keeping docs synchronized with code is free-energy minimization.

#### Semantic Memory — The Knowledge Graph Interface

**Semantic memory** (Tulving, 1972) is the memory system for general factual and conceptual knowledge, independent of episodic context. It is:

- **Amodal**: stored as abstract propositions, not tied to sensory modality
- **Hierarchically organized**: concepts are organized in taxonomies (IS-A, PART-OF) and semantic networks
- **Accessed rapidly**: semantic priming effects show < 250 ms activation of associated concepts

Neural basis: the **anterior temporal lobe (ATL)** is the semantic hub — lesioned ATL (semantic dementia) produces progressive, modality-general loss of conceptual knowledge while episodic memory for recent events is largely preserved.

**Phase 9.3 mapping**: The `docs/` directory is the system's semantic memory. Cross-linking between docs (`[architecture.md](architecture.md)` from `README.md`, `[adding-a-module.md](guides/adding-a-module.md)` from `architecture.md`) creates the semantic network structure. The remaining outstanding docs items (deployment guides, security guides, cross-linking audit) are gaps in the semantic memory graph that prevent rapid retrieval.

#### Hebbian Learning — Documentation Coactivation Strengthens Schemas

**Hebbian learning** ("neurons that fire together, wire together"; Hebb, 1949) is the foundational synaptic plasticity rule: simultaneous activation of pre- and post-synaptic neurons strengthens the synaptic connection between them (long-term potentiation, LTP). The corollary: neurons that never fire together weaken their connection (long-term depression, LTD).

**Phase 9.3 mapping**: Documentation written **alongside** implementation (not after) is Hebbian coactivation — the mental models that built the code and the words that describe it are simultaneously active, producing strong, accurate associations. Documentation written months later (out-of-sync with the code's current state) is the LTD case: association has weakened. This is the biological argument for the documentation-first constraint in `AGENTS.md`.

| Brain mechanism | Phase 9.3 equivalent |
|---|---|
| DMN autobiographical narrative construction | `docs/architecture.md` — coherent self-referential system narrative |
| DMN angular gyrus binding disparate episodic memories | Cross-linked documentation: README → architecture → guides → protocols |
| Metacognitive knowledge (aPFC declarative self-knowledge) | `docs/guides/` — declarative documentation of system operation |
| Metacognitive monitoring + control (ACC conflict detection) | Broken-link checker; doc coverage audit; gap list in 9.3 workplan |
| Predictive coding generative model — minimize prediction error | Accurate, synchronized docs minimize developer orientation cost |
| Semantic memory ATL hub — amodal, hierarchical concept graph | `docs/` cross-link network as semantic knowledge graph about the system |
| Hebbian LTP — coactivation during writing strengthens doc–code association | Documentation-first mandate: write docs alongside implementation, not after |

---

## Cross-Cutting Biological Themes

Several biological themes span multiple Phase 9 sub-phases and should shape the overall design philosophy:

### 1. Graduated Response, Not Binary Gates

The immune system, cerebral autoregulation, and metacognitive control all exhibit **graduated, proportional responses** — not on/off switches. OPA should have graduated enforcement levels (audit → warn → block); HPA should have fine-grained scaling curves; documentation completeness should be measured as a spectrum, not a binary pass/fail.

### 2. Offline/Background Processing Is Not Optional

The brain devotes substantial neural resources (~60–80% of baseline energy) to DMN and offline consolidation activity. This is not idle time — it is where integration, self-modeling, and deferred completion happen. Phase 9.0 and 9.3 represent the system's first true offline consolidation pass, and should be treated with the same importance as active-processing phases.

### 3. Layered Defence in Depth

No single BBB mechanism prevents all pathogens; no single synaptic gate determines consciousness. The brain uses **defence in depth**: BBB + immune privilege + microglial surveillance + apoptosis + glial scarring. Phase 9.1 should implement security as layers: gVisor + OPA + NetworkPolicy + mTLS + SPIFFE, not pick-one.

### 4. Activity-Dependent Resource Allocation

Myelination, CBF autoregulation, and synaptic pruning are all **activity-dependent** — the brain does not pre-allocate fixed resources. Phase 9.2 should follow the same principle: HPA scaling, readiness-gated traffic, and resource requests/limits tuned to observed workload rather than static over-provisioning.

### 5. Self-Reference Is Structurally Necessary

The DMN, metacognitive systems, and semantic memory are not philosophical luxuries — they are load-bearing components of higher cognition. An AI system without accurate self-documentation loses the ability to orient, debug, and extend itself efficiently. Phase 9.3 documentation completion is structurally necessary for the system's ongoing operation, not cosmetic.

---

## Sources

| Topic | Source | Saved file |
|---|---|---|
| Memory consolidation | Wikipedia: Memory consolidation | `docs/research/sources/phase-9/bio-memory-consolidation.md` |
| Hippocampal replay / SWR | Wikipedia: Hippocampal replay | `docs/research/sources/phase-9/bio-hippocampal-replay.md` |
| Default Mode Network | Wikipedia: Default mode network | `docs/research/sources/phase-9/bio-default-mode-network.md` |
| Immune privilege | Wikipedia: Immune privilege | `docs/research/sources/phase-9/bio-immune-privilege.md` |
| Microglia | Wikipedia: Microglia | `docs/research/sources/phase-9/bio-microglia.md` |
| Blood-brain barrier | Wikipedia: Blood–brain barrier | `docs/research/sources/phase-9/bio-blood-brain-barrier.md` |
| Apoptosis | Wikipedia: Apoptosis | `docs/research/sources/phase-9/bio-apoptosis.md` |
| Pattern recognition receptors / Danger Hypothesis | Wikipedia: Pattern recognition receptor | `docs/research/sources/phase-9/bio-pattern-recognition-receptors.md` |
| Adult neurogenesis | Wikipedia: Adult neurogenesis | `docs/research/sources/phase-9/bio-adult-neurogenesis.md` |
| Cortical columns | Wikipedia: Cortical column | `docs/research/sources/phase-9/bio-cortical-column.md` |
| Myelination | Wikipedia: Myelination | `docs/research/sources/phase-9/bio-myelination.md` |
| Cerebral autoregulation | Wikipedia: Cerebral autoregulation | `docs/research/sources/phase-9/bio-cerebral-autoregulation.md` |
| Synaptic pruning | Wikipedia: Synaptic pruning | `docs/research/sources/phase-9/bio-synaptic-pruning.md` |
| Metacognition | Wikipedia: Metacognition | `docs/research/sources/phase-9/bio-metacognition.md` |
| Semantic memory | Wikipedia: Semantic memory | `docs/research/sources/phase-9/bio-semantic-memory.md` |
| Hebbian learning | Wikipedia: Hebbian theory | `docs/research/sources/phase-9/bio-hebbian-theory.md` |
| Predictive coding | Wikipedia: Predictive coding | `docs/research/sources/phase-9/bio-predictive-coding.md` |
