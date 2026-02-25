# @accessitech/endogenAI

An experimental MCP framework for building specialized AGI systems from the inside out — agentic modules modeled on the
known architecture of the human brain, designed to scaffold and extend themselves from a morphogenetic seed.

## Guiding Principles

#### Foundational

- **Neuromorphic Design**: Every design decision in this framework is grounded in the structures and functions of the
  mammalian brain — modularity, parallel processing, hierarchical organization, and adaptive learning. Biological
  organization is the primary design metaphor, not an analogy applied after the fact.

  - Evaluate spiking-neuron and event-driven computation frameworks as candidate substrates for modules where
    biologically-inspired processing patterns are beneficial. Select based on community activity, hardware pathway
    availability, and compatibility with the MCP communication layer:
    - [**Nengo**](#neuromorphic-optional--pluggable)
    - [**Intel Lava**](#neuromorphic-optional--pluggable) (for Loihi)
    - [**SpiNNaker/PyNN**](#neuromorphic-optional--pluggable)
    - [**NEST**](#neuromorphic-optional--pluggable)
    - [**Brian2**](#neuromorphic-optional--pluggable)
    - [**BindsNET**](#neuromorphic-optional--pluggable)

- **Agentic Modularity**: Each module embodies a single, well-defined cognitive function — perception, memory,
  decision-making, motor control — mirroring the functional specialization of brain regions. Modules are developed
  independently and integrated seamlessly across the framework.

  - Modules may be implemented in different programming languages; all communicate through the standardized protocols
    defined by the MCP framework.
  - Minimize inter-module dependencies: modules exchange only the context required for their defined function,
    preserving independence and replaceability.

- **Endogenetic Growth**: The framework is designed to generate and extend itself from within — like a seed that carries
  the blueprint for the organism it will become. The repository structure, module scaffolding, and knowledge base are
  not assembled top-down by a human architect alone; they emerge from the system's own encoded patterns, conventions,
  and self-referential documentation. This principle is modelled on **autopoiesis** — the biological property of systems
  that continuously produce the components necessary for their own continuity.
  - Model the repository lifecycle on autopoiesis: every component that enters the system should contribute to the
    system's capacity to produce further components.
  - Treat `resources/static/knowledge/` and `brain-structure.md` as the **morphogenetic seed** — the initial encoding
    from which all module analogies, interfaces, and conventions are derived.
  - Prefer **endogenous scaffolding**: new module templates, schemas, and stubs should be generatable from existing
    system knowledge, not authored from scratch in isolation.
  - The framework should be capable of reasoning about its own architecture and proposing its own extensions — a
    necessary precondition for any system that aspires to general intelligence.

#### Architectural

- **Local Compute First**: Prioritize local computation and data storage within modules, minimizing dependence on
  external APIs or cloud services. Like the brain, the system should maximize useful cognition per unit of energy by
  keeping processing close to where signals originate.

  - Enforce a **local-first execution policy**: perform inference, retrieval, planning, and orchestration on-device or
    host-local by default; escalate to remote services only when a capability is genuinely unavailable locally or
    explicitly required by policy.
  - Evaluate **WebMCP** for browser-native, UI-facing modules that benefit from low-latency local context handling and
    reduced round trips.
  - Treat external services as **augmentations, not dependencies**: when cloud APIs are required (specialized models,
    heavy batch workloads), integrate through explicit interfaces, policy gates, and auditable fallback behavior.
  - Optimize for **latency, privacy, resilience, and power efficiency**: local processing reduces network bottlenecks,
    limits data exposure, and preserves graceful degradation when remote systems are unavailable.
  - Apply **caching, load balancing, and parallel processing** to maximize throughput and maintain responsiveness as the
    system scales in complexity.

- **Scalability and Extensibility**: The architecture accommodates growing complexity and supports the continuous
  integration of new modules and capabilities. New modules can be added without requiring significant changes to
  existing ones.
  - Use microservices architecture, containerization, and orchestration (e.g., Kubernetes) to support distributed
    deployment and horizontal scaling.
  - Design module interfaces to be versioned and backward-compatible, enabling incremental upgrades without system-wide
    disruption.

#### Technical

- **Standardized Communication Protocols**: All inter-module communication follows the standards defined by the MCP and
  A2A frameworks. See [Module Context Protocol (MCP) Framework](#module-context-protocol-mcp-framework) and
  [Agent to Agent Protocol (A2A) Framework](#agent-to-agent-protocol-a2a-framework).

  - Use [`mdn-mcp`](#communication--protocols) as the primary communication backbone; layer
    [A2A](#communication--protocols) on top for agent-to-agent task coordination and delegation.
  - Support both synchronous and asynchronous communication patterns to accommodate the full range of inter-module
    interaction types.

- **Robustness and Fault Tolerance**: Handle failures gracefully at every layer, with mechanisms for error detection,
  recovery, and redundancy.
  - Implement structured logging, distributed tracing, and real-time monitoring at module boundaries to detect and
    diagnose failures promptly.
  - Replicate critical modules and define explicit fallback behaviors to ensure continued operation when individual
    modules or dependencies fail.

#### Cross-Cutting

- **Security & Privacy by Design**: Security and privacy are embedded in the architecture from the outset, not
  retrofitted. Each module interface is treated as a potential attack surface and hardened accordingly.

  - Enforce module sandboxing, strict capability isolation, and least-privilege access control: no module should access
    resources or context beyond what its defined function requires.
  - Validate and sanitize all inputs at layer boundaries; harden inter-module interfaces against prompt injection, data
    exfiltration, and context poisoning.
  - Minimize handling of personal and sensitive data: prefer on-device processing, anonymize where feasible, and apply
    explicit data retention and deletion policies.

- **Observability by Design**: The system exposes the information needed to understand, debug, and improve its own
  behavior at runtime — a first-class architectural requirement, not an afterthought. This principle reinforces the
  [Meta-cognition & Monitoring Layer](#group-iv-adaptive-systems-cross-cutting).

  - Emit structured telemetry (logs, metrics, traces) from all modules through a consistent, queryable interface.
  - Instrument inter-layer signal flow to enable end-to-end tracing of decisions from sensory input through to effector
    output.
  - Maintain auditable records of agent decisions, context state, and tool invocations to support debugging, post-hoc
    analysis, and accountability.

- **Ethical Considerations**: The development and deployment of AGI systems must be guided by transparency,
  accountability, and respect for human values.
  - Document the system's architecture, decision-making processes, and data usage policies clearly and keep them
    accessible to all stakeholders.
  - Implement auditing and oversight mechanisms so that stakeholders can review actions, challenge outcomes, and hold
    the system accountable.
  - Assess potential societal impacts proactively; include provisions for mitigating harms and ensuring the technology
    serves the benefit of humanity.

## Architectural Overview

The architecture is organized into layered groups that mirror the brain's bottom-up signal processing, bidirectional
cognitive feedback, and adaptive learning. MCP and A2A are **cross-cutting infrastructure** — they are not sequential
layers but rather a communication backbone that spans all groups. See
[Module Context Protocol (MCP) Framework](#module-context-protocol-mcp-framework) and
[Agent to Agent Protocol (A2A) Framework](#agent-to-agent-protocol-a2a-framework).

Information flows **bottom-up** (Input → Perception → Cognition → Action) for stimulus-driven processing, and
**top-down** (Executive → Decision-Making → Attention → Sensory) for goal-directed modulation — mirroring how the brain
uses both pathways simultaneously and continuously.

### Group I: Signal Processing

- **Sensory / Input Layer**: Ingests raw input from the environment — text, images, audio, API events, and sensor
  streams. Analogous to the sensory cortices (visual, auditory, somatosensory). Modules at this layer perform no
  semantic interpretation; they normalize, timestamp, and forward signals upward.

- **Attention & Filtering Layer**: Gates and routes incoming signals based on salience, relevance, and current goals.
  Analogous to the thalamus and attentional networks. Prevents lower-level noise from saturating higher processing and
  supports top-down attention modulation from the Executive / Agent Layer.

- **Perception Layer**: Extracts meaningful features and patterns from filtered signals — object recognition, language
  understanding, scene parsing, and multimodal fusion. Analogous to the association cortices. Feeds upward into Memory
  and Decision-Making, and receives top-down priors from higher layers.

### Group II: Cognitive Processing

- **Memory Layer**: Stores and retrieves information across multiple timescales — working memory (immediate context),
  short-term memory (session state), long-term memory (persistent knowledge), and episodic memory (event sequences).
  Analogous to the hippocampus and related structures. Bidirectionally coupled with Perception (encoding) and
  Decision-Making (retrieval).

- **Affective / Motivational Layer**: Assigns emotional weight, urgency, and drive to information and goals. Produces
  reward signals and prioritization cues that modulate memory consolidation and decision-making. Analogous to the limbic
  system (amygdala, hypothalamus, nucleus accumbens). Critical for realistic goal-directed behavior and often absent in
  purely logical architectures.

- **Decision-Making & Reasoning Layer**: Integrates signals from Memory, Affective, and Perception layers to produce
  choices, plans, and judgments. Covers logical reasoning, causal inference, planning under uncertainty, and conflict
  resolution. Analogous to the prefrontal cortex. Receives top-down constraints from the Executive / Agent Layer.

### Group III: Executive & Output

- **Executive / Agent Layer**: Holds the agent's identity, persistent goals, values, policies, and high-level reasoning
  strategy. Directs attention and modulates lower layers in a top-down fashion. Covers self-awareness, social cognition,
  and meta-level goal management. Analogous to the frontal lobes.

- **Agent Execution (Runtime) Layer**: Orchestrates and executes capabilities in response to decisions — function calls,
  tool use, skill pipelines, and automated workflows. Handles task decomposition, tool/function selection, sequencing,
  and inter-module coordination. A focused execution-and-orchestration layer, distinct from the goal-setting and policy
  concerns of the Executive / Agent Layer above it.

- **Motor / Output / Effector Layer**: Delivers actions into the environment — API calls, message dispatch, file writes,
  rendered outputs, and control signals. Analogous to the motor cortex and cerebellum. Responsible for reliable,
  low-latency action execution and feedback confirmation back up the stack.

### Group IV: Adaptive Systems _(cross-cutting)_

These layers operate across all groups, providing continuous feedback and self-improvement not bound to any single
processing stage.

- **Learning & Adaptation Layer**: Processes feedback signals (errors, rewards, outcomes) to refine module behavior over
  time. Covers reinforcement signals, parameter updates, behavioral conditioning, and skill acquisition. Analogous to
  the basal ganglia and cerebellum.

- **Meta-cognition & Monitoring Layer**: Observes the system's own processing — tracking confidence, detecting errors,
  evaluating performance, and triggering corrective action. Analogous to the anterior cingulate cortex and prefrontal
  monitoring circuits. Feeds into the Learning & Adaptation Layer and can escalate anomalies directly to the Executive /
  Agent Layer.

### Group V: Interface

- **Application Layer**: The surface through which end users or external systems interact — chatbots, APIs, dashboards,
  and domain-specific applications. Routes requests into the Sensory / Input Layer and surfaces outputs from the Motor /
  Output / Effector Layer.

---

> **Infrastructure Note**: MCP and A2A are not cognitive layers. They form the communication backbone and coordination
> protocols that span all groups above. See
> [Module Context Protocol (MCP) Framework](#module-context-protocol-mcp-framework) and
> [Agent to Agent Protocol (A2A) Framework](#agent-to-agent-protocol-a2a-framework).

## Module Context Protocol (MCP) Framework

The MCP framework provides a standardized protocol for communication and interaction between different agentic modules.
It defines the structure and format of messages, as well as the rules for how modules can request and share
information. - **Backbone Standard: [`mdn-mcp`](#communication--protocols)**: The framework should adopt
[**mdn-mcp**](#communication--protocols) as its core communication backbone for all module-to-module context exchange. -
All agentic modules should implement `mdn-mcp`-compatible interfaces for request/response handling, context propagation,
capability discovery, and state synchronization. - Any additional protocols (including A2A patterns) should be layered
on top of `mdn-mcp` to ensure consistent interoperability, easier tooling, and reduced integration complexity across the
system.

## Agent to Agent Protocol (A2A) Framework

The A2A framework should use the [A2A Project specification](https://github.com/a2aproject/A2A) as the standard for
direct agent-to-agent interaction, task delegation, and multi-agent coordination.

- **Primary A2A Standard: `A2A`**: Implement the A2A protocol for structured communication between autonomous modules
  acting as agents.

  - Define clear agent identities, advertised capabilities, and supported task schemas.
  - Use A2A message patterns for discovery, negotiation, delegation, progress updates, and result delivery.
  - Support asynchronous execution and long-running task orchestration across distributed modules.
  - Include standardized error handling, retries, and timeout behavior for robust inter-agent workflows.

- **MCP + A2A Interoperability Model**:

  - Keep [`mdn-mcp`](#communication--protocols) as the shared context backbone and system-wide state exchange layer.
  - Layer A2A interactions on top for agent-centric coordination and collaborative execution.
  - Provide adapter components so each module can participate in both MCP context exchange and A2A task protocols
    without duplicated logic.

- **Implementation Guidance**:
  - Align message formats, lifecycle events, and capability metadata with the upstream A2A reference implementation and
    documentation.
  - Add conformance tests to validate protocol compatibility as A2A evolves.
  - Version-lock and periodically review A2A dependencies to maintain compatibility and security.

## File Directory

An outline of the file directory structure for the project, including descriptions of each file and its purpose within
the overall framework.

### Root

- `README.md` — Project overview, quick-start guide, and links to detailed documentation
- `CONTRIBUTING.md` — Contribution guidelines, coding standards, and PR process
- `CHANGELOG.md` — Version history and release notes
- `LICENSE` — Open-source license
- `.gitignore` — Repository-wide ignore rules
- `docker-compose.yml` — Local multi-service orchestration for development and integration testing

---

### Docs

#### `docs/` — Project-wide documentation

- `architecture.md` — Full architectural overview, layer descriptions, and signal-flow diagrams

##### `protocols/`

- `mcp.md` — MCP (mdn-mcp) integration guide: message formats, context propagation, capability discovery
- `a2a.md` — A2A protocol guide: agent identity, skill schemas, task lifecycle, and interoperability model

##### `guides/`

- `getting-started.md` — Environment setup and first-run walkthrough
- `adding-a-module.md` — Step-by-step guide for creating a new cognitive module
- `deployment.md` — Containerization, Kubernetes, and scaling guidance
- `security.md` — Security model, sandboxing policies, and least-privilege patterns
- `observability.md` — Telemetry setup, tracing, and dashboard usage

---

### Shared

#### `shared/` — Cross-module assets shared across all layer groups

##### `schemas/` — Canonical JSON / Protobuf schemas for MCP context envelopes and A2A message types

- `mcp-context.schema.json` — MCP context object schema
- `a2a-message.schema.json` — A2A message envelope schema
- `a2a-task.schema.json` — A2A task lifecycle schema

##### `types/` — Shared type definitions (language-agnostic IDL or JSON Schema)

- `signal.schema.json` — Common signal envelope passed between layers
- `memory-item.schema.json` — Unified memory record structure
- `reward-signal.schema.json` — Reward / affective weighting structure

##### `utils/` — Language-agnostic utility specs and reference implementations

- `logging.md` — Structured log format specification
- `tracing.md` — Distributed trace context propagation spec
- `validation.md` — Input sanitization and boundary validation patterns

##### `vector-store/` — Backend-agnostic vector store adapter interface _(used by all modules with embedded state)_

- `adapter.interface.json` — Language-agnostic interface contract: `upsert`, `query`, `delete`, `create-collection`,
  `drop-collection`, `list-collections`
- `collection-registry.json` — Canonical registry of all named collections across modules; naming convention
  `brain.<module-name>`; source of truth for collection provisioning at boot
- `chroma.config.schema.json` — [ChromaDB](#vector-stores) adapter configuration schema _(default; embedded local mode,
  zero-infrastructure)_
- `qdrant.config.schema.json` — [Qdrant](#vector-stores) adapter configuration schema _(recommended for production;
  high-performance, filterable)_
- `pgvector.config.schema.json` — [pgvector](#vector-stores) adapter configuration schema _(for Postgres-native
  deployments)_
- `embedding.config.schema.json` — Embedding provider configuration schema: provider, model, base URL, dimensions, and
  fallback policy
- `README.md` — Adapter pattern, collection namespacing conventions, backend selection guide,
  [Ollama](#embeddings-local-first) integration, and local-vs-production recommendations

---

### Infrastructure

#### `infrastructure/` — MCP and A2A communication backbone _(not a cognitive layer; cross-cutting infrastructure)_

##### `mcp/` — mdn-mcp backbone implementation

- `src/` — MCP server, context broker, capability registry, and state synchronization
- `tests/` — Unit and integration tests for MCP context exchange
- `config/` — Environment-specific MCP configuration
- `README.md` — MCP module purpose, interface contract, and usage

##### `a2a/` — A2A protocol implementation

- `src/` — A2A server, request handler, agent card endpoint, and task orchestrator
- `tests/` — Unit and integration tests; A2A conformance test suite
- `config/` — A2A environment configuration and version-lock settings
- `README.md` — A2A module purpose, agent card format, and usage

##### `adapters/` — MCP + A2A interoperability bridge

- `src/` — Adapter components enabling modules to participate in both MCP context exchange and A2A task protocols
  without duplicated logic
- `tests/` — Adapter unit and integration tests
- `README.md` — Adapter architecture and integration patterns

---

### Modules

#### `modules/` — All cognitive modules, organized by architectural layer group

##### `group-i-signal-processing/` — Group I: Signal Processing

###### `sensory-input/` — _Sensory / Input Layer_ — analogous to the sensory cortices (visual, auditory, somatosensory); ingests and normalizes raw environment signals

- `src/` — Signal ingestion, normalization, timestamping, and upward dispatch (text, image, audio, API events, sensor
  streams)
- `tests/` — Unit and integration tests
- `config/` — Input source configuration and signal format mappings
- `docs/` — Layer description, interface contract, and signal schema references
- `agent-card.json` — A2A agent identity and capability declaration (served at `/.well-known/agent-card.json`)
- `README.md` — Module purpose, inputs/outputs, and usage

###### `attention-filtering/` — _Attention & Filtering Layer_ — analogous to the thalamus and attentional networks; gates and routes signals based on salience, relevance, and current goals

- `src/` — Salience scoring, relevance filtering, signal routing, and top-down attention modulation interface
- `tests/` — Unit and integration tests
- `config/` — Threshold and routing policy configuration
- `docs/` — Layer description and attentional gating design notes
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, inputs/outputs, and usage

###### `perception/` — _Perception Layer_ — analogous to the association cortices; extracts features and patterns from filtered signals

- `src/`
  - `feature-extraction/` — Feature extraction, pattern recognition, language understanding, scene parsing, and
    multimodal fusion
  - `vector-store/` — Manages `brain.perception` collection; embeds extracted feature representations for cross-session
    pattern retrieval and similarity search
- `tests/` — Unit and integration tests
- `config/`
  - `pipeline.config.json` — Model references and perception pipeline configuration
  - `vector-store.config.json` — Backend and collection config for `brain.perception`
- `docs/` — Layer description, supported modalities, and fusion strategy
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, inputs/outputs, and usage

##### `group-ii-cognitive-processing/` — Group II: Cognitive Processing

###### `memory/` — _Memory Layer_ — analogous to the hippocampus and related structures; stores and retrieves information across timescales

- **`working-memory/`** — Immediate context buffer; the active LLM context window. Pure in-process key-value store — no
  vector DB (too high-churn, latency-critical). On each turn, queries `brain.short-term-memory` and
  `brain.long-term-memory` via retrieval-augmented lookup to populate the context window with the most relevant session
  and persistent knowledge, keeping token usage minimal. Items consolidate upward to episodic/long-term on eviction.
  - `src/`
    - `context-store/` — In-process KV store: read, write, evict operations
    - `retrieval-augmented-loader/` — Queries short-term and long-term memory collections to assemble context window on
      each turn; manages token budget and relevance ranking
    - `consolidation/` — Promotion pipeline: evicted items dispatched to episodic or long-term memory for persistence
  - `tests/` — Unit and integration tests
  - `config/`
    - `capacity.config.json` — Token budget, max items, and eviction policy
    - `retrieval.config.json` — Short-term and long-term query weights, top-k, and relevance threshold
  - `agent-card.json` — A2A agent identity and capability declaration
  - `README.md` — Module purpose, context window management model, retrieval-augmented loading, and consolidation policy
- **`short-term-memory/`** — Session-scoped state; persists for the duration of an interaction. Lightweight vector index
  (`brain.short-term-memory`) enabling semantic search within the current session — so working memory can retrieve the
  most relevant recent context rather than the most recent N items.
  - `src/`
    - `session-store/` — Session-scoped record store with TTL management
    - `vector-store/` — Manages `brain.short-term-memory` collection; embeds session records via
      [Ollama](#embeddings-local-first) `nomic-embed-text` for intra-session semantic retrieval
    - `retrieval/` — Semantic search over current session; serves working memory loader requests
  - `tests/` — Unit and integration tests
  - `config/`
    - `ttl.config.json` — Session TTL and expiry policy
    - `vector-store.config.json` — Backend and collection config for `brain.short-term-memory`
    - `embedding.config.json` — Inherits [Ollama](#embeddings-local-first) `nomic-embed-text` from
      `shared/vector-store/`
  - `agent-card.json` — A2A agent identity and capability declaration
  - `README.md` — Module purpose, session lifecycle, and semantic retrieval model
- **`long-term-memory/`** — Persistent knowledge store (facts, skills, learned associations). Full configurable vector
  DB (`brain.long-term-memory`); primary destination for consolidated knowledge and the boot-time seed corpus from
  `resources/static/knowledge/`.
  - `src/`
    - `vector-store/` — Configurable vector DB adapter implementing `shared/vector-store/adapter.interface.json`;
      manages `brain.long-term-memory` collection ([ChromaDB](#vector-stores) default, [Qdrant](#vector-stores) for
      production)
    - `graph-store/` — Knowledge graph adapter (e.g., [Neo4j](#memory--state), [Kuzu](#memory--state)) for structured
      relational knowledge
    - `relational-store/` — SQL adapter for structured fact storage
    - `indexing/` — Embedding pipelines with frontmatter-aware section chunking (respects `brain-structure.md` region
      boundaries), overlap configuration, and index management
    - `retrieval/` — Semantic search, hybrid retrieval (vector + keyword), and re-ranking; serves working memory loader
      and reasoning layer
    - `seed/` — Boot-time ingestion pipeline: chunks and embeds all `resources/static/knowledge/` documents (including
      `brain-structure.md` and `neuroanatomy/`) into `brain.long-term-memory` via [Ollama](#embeddings-local-first)
      `nomic-embed-text` _(see [RAG & Document Ingestion](#rag--document-ingestion) —
      [LlamaIndex](#rag--document-ingestion))_
  - `tests/` — Unit and integration tests; per-backend adapter conformance tests
  - `config/`
    - `vector-store.config.json` — Active backend selection ([`chroma`](#vector-stores) \| [`qdrant`](#vector-stores) \|
      [`pgvector`](#vector-stores)) and connection settings
    - `embedding.config.json` — Provider: [`ollama`](#embeddings-local-first), model: `nomic-embed-text`, base URL:
      `http://localhost:11434`, dimensions: 768; explicit-only cloud fallback _(see
      [LiteLLM](#llm-abstraction-provider-agnostic) for LLM calls)_
    - `indexing.config.json` — Chunking strategy, overlap, collection name, and frontmatter-aware section splitting
      rules
  - `agent-card.json` — A2A agent identity and capability declaration
  - `README.md` — Module purpose, backend options, adapter pattern, Ollama setup, and seed pipeline usage
- **`episodic-memory/`** — Event sequence store; ordered records of past interactions and outcomes. Dual-indexed:
  ordered event log for temporal replay + semantic vector index (`brain.episodic-memory`) for content-based episode
  retrieval. Enables queries like "find episodes similar to this situation" as well as "replay what happened in session
  X".
  - `src/`
    - `event-log/` — Ordered event ingestion, storage, and temporal indexing
    - `vector-index/` — Manages `brain.episodic-memory` collection; embeds episode records for semantic and
      temporal+semantic composite queries
    - `retrieval/` — Temporal replay, semantic episode search, and composite time+similarity queries
  - `tests/` — Unit and integration tests
  - `config/`
    - `vector-store.config.json` — Backend and collection config for `brain.episodic-memory`
    - `embedding.config.json` — Inherits [Ollama](#embeddings-local-first) `nomic-embed-text` from
      `shared/vector-store/`
    - `retention.config.json` — Retention window, compression policy, and eviction rules
  - `agent-card.json` — A2A agent identity and capability declaration
  - `README.md` — Module purpose, temporal + semantic retrieval model, and consolidation pipeline
- `docs/` — Memory layer overview: timescale model, encoding/retrieval flow, and hippocampal analogy
- `README.md` — Memory layer entry point and sub-module index

###### `affective/` — _Affective / Motivational Layer_ — analogous to the limbic system (amygdala, hypothalamus, nucleus accumbens); assigns emotional weight, urgency, and drive to information and goals

- `src/`
  - `signal-generation/` — Reward signal generation, emotional weighting, urgency scoring, and prioritization cue
    dispatch
  - `vector-store/` — Manages `brain.affective` collection; embeds reward and emotional state history for pattern-based
    drive modulation and affective memory
- `tests/` — Unit and integration tests
- `config/`
  - `drive.config.json` — Reward shaping and drive parameter configuration
  - `vector-store.config.json` — Backend and collection config for `brain.affective`
- `docs/` — Limbic system analogy, reward model description, and integration with memory/decision-making
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, inputs/outputs, and usage

###### `reasoning/` — _Decision-Making & Reasoning Layer_ — analogous to the prefrontal cortex; integrates memory, affective, and perception signals to produce choices, plans, and judgments

- `src/`
  - `inference/` — Logical reasoning, causal inference, planning under uncertainty, and conflict resolution _(see
    [Reasoning & Planning](#reasoning--planning) — [DSPy](#reasoning--planning), [Guidance](#reasoning--planning))_
  - `vector-store/` — Manages `brain.reasoning` collection; embeds inference traces, plans, and causal models for
    retrieval-augmented reasoning and decision history
- `tests/` — Unit and integration tests
- `config/`
  - `strategy.config.json` — Reasoning strategy and inference engine configuration
  - `vector-store.config.json` — Backend and collection config for `brain.reasoning`
- `docs/` — Prefrontal cortex analogy, reasoning pipeline design, and uncertainty handling
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, inputs/outputs, and usage

##### `group-iii-executive-output/` — Group III: Executive & Output

###### `executive-agent/` — _Executive / Agent Layer_ — analogous to the frontal lobes; holds agent identity, persistent goals, values, policies, and high-level reasoning strategy

- `src/`
  - `identity/` — Agent identity management and self-model
  - `goal-stack/` — Persistent goal management, prioritization, and lifecycle
  - `policy-engine/` — Value and policy evaluation, top-down modulation dispatch, and social cognition interface
  - `vector-store/` — Manages `brain.executive-agent` collection; embeds persistent goals, values, policies, and
    identity state for semantic retrieval and goal similarity search
- `tests/` — Unit and integration tests
- `config/`
  - `identity.config.json` — Agent identity, values, and policy configuration
  - `vector-store.config.json` — Backend and collection config for `brain.executive-agent`
- `docs/` — Frontal lobe analogy, goal and policy model, and self-awareness design notes
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, identity schema, and usage

###### `agent-runtime/` — _Agent Execution (Runtime) Layer_ — orchestrates and executes capabilities in response to decisions _(see [Agent Runtime & Orchestration](#agent-runtime--orchestration) — [Temporal](#agent-runtime--orchestration), [Prefect](#agent-runtime--orchestration))_

- `src/` — Task decomposition, tool/function selection, skill pipeline execution, sequencing, and inter-module
  coordination
- `tests/` — Unit and integration tests
- `config/` — Runtime environment and tool registry configuration
- `docs/` — Execution model, task decomposition strategy, and tool integration patterns
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, orchestration model, and usage

###### `motor-output/` — _Motor / Output / Effector Layer_ — analogous to the motor cortex and cerebellum; delivers actions into the environment

- `src/` — API call dispatch, message delivery, file writes, rendered output generation, control signal emission, and
  upward feedback confirmation
- `tests/` — Unit and integration tests
- `config/` — Output channel and effector configuration
- `docs/` — Motor cortex / cerebellum analogy, output channel descriptions, and feedback model
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, supported output channels, and usage

##### `group-iv-adaptive-systems/` — Group IV: Adaptive Systems _(cross-cutting — operates across all groups)_

###### `learning-adaptation/` — _Learning & Adaptation Layer_ — analogous to the basal ganglia and cerebellum; processes feedback to refine module behaviour over time

- `src/`
  - `reinforcement/` — Reinforcement signal processing, parameter update dispatch, and behavioural conditioning
    pipelines _(see [Learning & Adaptation](#learning--adaptation) — [Stable-Baselines3](#learning--adaptation),
    [RLlib](#learning--adaptation), [TorchRL](#learning--adaptation))_
  - `skill-acquisition/` — Skill learning, generalisation, and capability registration
  - `vector-store/` — Manages `brain.learning-adaptation` collection; embeds feedback logs, behavioural conditioning
    history, and skill acquisition records for pattern-based adaptation
- `tests/` — Unit and integration tests
- `config/`
  - `learning.config.json` — Learning rate, update strategy, and feedback source configuration
  - `vector-store.config.json` — Backend and collection config for `brain.learning-adaptation`
- `docs/` — Basal ganglia / cerebellum analogy, reinforcement model, and adaptation strategy
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, feedback model, and usage

###### `metacognition/` — _Meta-cognition & Monitoring Layer_ — analogous to the anterior cingulate cortex and prefrontal monitoring circuits; observes the system's own processing

- `src/`
  - `monitoring/` — Confidence tracking, error detection, performance evaluation, and anomaly escalation to executive
    layer _(see [Observability](#observability) — [OpenTelemetry](#observability), [Prometheus](#observability),
    [Grafana](#observability))_
  - `corrective-actions/` — Corrective action trigger dispatch and remediation pipelines
  - `vector-store/` — Manages `brain.metacognition` collection; embeds confidence scores, error patterns, and
    performance snapshots for anomaly detection and self-monitoring history
- `tests/` — Unit and integration tests
- `config/`
  - `monitoring.config.json` — Monitoring thresholds and escalation policy configuration
  - `vector-store.config.json` — Backend and collection config for `brain.metacognition`
- `docs/` — Anterior cingulate cortex analogy, self-monitoring model, and escalation design
- `agent-card.json` — A2A agent identity and capability declaration
- `README.md` — Module purpose, monitoring model, and usage

---

> **Vector store architecture**: All module collections share a single configurable backend instance
> ([ChromaDB](#vector-stores) embedded by default; [Qdrant](#vector-stores) for production), namespaced as
> `brain.<module-name>`. Working memory is the sole exception — it is a pure in-process KV store that queries
> `brain.short-term-memory` and `brain.long-term-memory` via retrieval-augmented loading to assemble each context
> window, keeping token usage minimal. The active backend, embedding model (default: [Ollama](#embeddings-local-first) >
> `nomic-embed-text` at `localhost:11434`), and explicit-only cloud fallback policy are defined in
> `shared/vector-store/`. See `shared/vector-store/collection-registry.json` for the full collection index.

---

### Application Layer

#### `apps/` — Group V: Interface — application-layer surfaces for end users and external systems

##### `default/` — Reference application shell (chatbot / API / dashboard entry point)

- `src/` — Request routing into Sensory/Input Layer and output surfacing from Motor/Output/Effector Layer
- `tests/` — Unit and integration tests
- `config/` — Application environment configuration
- `docs/` — Application layer design and integration guide
- `README.md` — Application purpose and usage

---

#### `observability/` — Cross-cutting telemetry infrastructure _(supports Observability by Design principle)_

- `src/` — Structured log emitters, metric collectors, distributed trace context propagation, and queryable telemetry
  interface
- `config/` — Telemetry backend configuration (log aggregation, metrics, tracing)
- `dashboards/` — Pre-built observability dashboards (e.g., [Grafana](#observability) JSON definitions)
- `README.md` — Observability stack overview and instrumentation guide

#### `security/` — Cross-cutting security infrastructure _(supports Security & Privacy by Design principle)_

- `policies/` — Module sandboxing policies, capability isolation rules, and least-privilege access definitions
- `sandboxing/` — Sandbox configuration templates and enforcement tooling
- `README.md` — Security model overview and hardening guide

#### `deploy/` — Deployment and infrastructure-as-code

- `docker/` — Per-module and base `Dockerfile` definitions
- `kubernetes/` — Kubernetes manifests for module deployment, service definitions, and horizontal scaling configuration
- `README.md` — Deployment guide: local, staging, and production targets

---

### Resources

MCP resources are URI-addressed data objects that servers expose to clients. In brAIn, resources are organized at two
levels: a top-level `resources/` directory for shared, cross-module resources (organized by cognitive layer group), and
a per-module `resources/` subdirectory within each cognitive module for module-scoped resource definitions, dynamic
providers, and access-control rules.

#### `resources/` — Cross-cutting MCP resource registry and shared assets

- `uri-registry.json` — Canonical registry of all resource URI patterns across the system; authoritative reference for
  resource discovery
- `access-control.md` — System-wide resource access-control policy: which modules and clients may read or write which
  resource URIs
- `README.md` — Resource system overview, URI naming conventions, and per-module resource authoring guide

##### `static/` — Shared static assets

###### `prompts/` — Prompt templates shared across modules

- `system.md` — Base system prompt and agent identity scaffold
- `reasoning.md` — Chain-of-thought and structured reasoning prompt scaffolds
- `memory-retrieval.md` — Memory query and retrieval prompt templates
- `metacognition.md` — Self-monitoring and confidence-assessment prompt templates

###### `knowledge/` — Seed knowledge and reference fixtures; all documents carry YAML frontmatter (`id`, `version`, `status`, `maps-to-modules`) and are chunked into `brain.long-term-memory` at boot via the seed pipeline

- `brain-structure.md` — **Authoritative** human brain structural reference. YAML-frontmattered with `maps-to-modules`
  declarations linking each region to its corresponding module. Each region section uses a consistent structure:
  function, inputs-from, outputs-to, module analogy, and key design notes. Primary seed document for
  `brain.long-term-memory`. _(descriptive — drives analogy and module mapping, not implementation)_
- `brain-architecture.md` — Framework-facing architectural overview: how brAIn's cognitive layers map to brain regions;
  references `brain-structure.md` as its source of truth
- `cognitive-models.md` — Cognitive science reference material informing module design decisions
- `signal-taxonomy.md` — Taxonomy of signal types, modalities, and encoding conventions used throughout the system

##### `neuroanatomy/` — Expanded human brain wiki; region-by-region reference pages, each YAML-frontmattered and chunked into `brain.long-term-memory` at boot alongside `brain-structure.md`

- `cortex.md` — Cerebral cortex: lobes, functional areas, and layer analogies
- `limbic-system.md` — Amygdala, hypothalamus, nucleus accumbens: affective and motivational analogies
- `basal-ganglia.md` — Basal ganglia: learning, habit formation, and reward circuit analogies
- `cerebellum.md` — Cerebellum: timing, coordination, and fine-tuning analogies
- `thalamus.md` — Thalamus: attentional gating and signal routing analogies
- `hippocampus.md` — Hippocampus: memory encoding, retrieval, consolidation, and timescale analogies
- `prefrontal-cortex.md` — Prefrontal cortex: reasoning, planning, and executive control analogies
- `anterior-cingulate.md` — Anterior cingulate cortex: error detection and metacognitive monitoring analogies

###### `fixtures/` — Seed and test data

- `signal-samples/` — Sample input signals for each modality (text, image, audio, API event) for development and
  integration testing
- `memory-seeds/` — Seed records for working, short-term, long-term, and episodic memory stores
- `reward-signals/` — Reference reward and affective weighting examples for learning and adaptation testing

##### `external/` — Professional-grade reference documentation

- `mcp-spec/` — MCP protocol specification references, capability examples, and conformance notes
- `a2a-spec/` — A2A protocol specification references, agent card examples, and task lifecycle references
- `mdn/` — Relevant MDN Web documentation references for browser-native and Web API-adjacent modules
- `README.md` — Source provenance, versioning policy, and update cadence for all external references

##### `schemas/` — Resource type contracts

- `resource-envelope.schema.json` — Common wrapper schema for all MCP resource response payloads
- `uri-pattern.schema.json` — Schema for defining and validating resource URI patterns
- `access-policy.schema.json` — Schema for per-module and system-wide resource access-control policy documents

##### `group-i-signal-processing/` — Signal Processing layer resource definitions

- `sensory-input.resources.json` — URI patterns and resource schemas for raw and normalized signal resources
- `attention-filtering.resources.json` — URI patterns and schemas for salience scores, routing state, and filter
  configuration resources
- `perception.resources.json` — URI patterns and schemas for extracted features, scene representations, and perception
  model output resources

##### `group-ii-cognitive-processing/` — Cognitive Processing layer resource definitions

- `memory.resources.json` — URI patterns and schemas for all memory sub-module resources (working, short-term,
  long-term, episodic)
- `affective.resources.json` — URI patterns and schemas for reward signals, emotional weights, and drive state resources
- `reasoning.resources.json` — URI patterns and schemas for inference traces, plans, and causal model resources

##### `group-iii-executive-output/` — Executive & Output layer resource definitions

- `executive-agent.resources.json` — URI patterns and schemas for agent identity, goal stack, policy state, and values
  resources
- `agent-runtime.resources.json` — URI patterns and schemas for active task state, tool registry, and execution trace
  resources
- `motor-output.resources.json` — URI patterns and schemas for output channel state, pending actions, and delivery
  confirmation resources

##### `group-iv-adaptive-systems/` — Adaptive Systems layer resource definitions

- `learning-adaptation.resources.json` — URI patterns and schemas for feedback logs, parameter update history, and skill
  acquisition state resources
- `metacognition.resources.json` — URI patterns and schemas for confidence scores, error detection logs, and performance
  evaluation resources

---

> **Per-module resources**: Each cognitive module also contains a `resources/` subdirectory providing module-scoped MCP
> resource definitions, dynamic resource providers (serving real-time state via MCP endpoints), module-local static
> templates, and access-control rules. See the per-module `README.md` for the resource catalog and URI patterns specific
> to that module.

## Relevant Technologies

### Language Strategy

This repository is **polyglot with clear conventions** — not language-agnostic in the sense of no code, but with a
defined role for each language across the stack.

| Layer                                                      | Language                                       | Rationale                                                       |
| ---------------------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------- |
| `shared/` schemas, contracts, IDL                          | **Language-agnostic** (JSON Schema / Protobuf) | Consumed by all modules regardless of implementation language   |
| Memory, Perception, Reasoning, Affective, Learning modules | **Python**                                     | ML/AI ecosystem is Python-native                                |
| MCP/A2A infrastructure, adapters                           | **TypeScript**                                 | Official MCP SDK is TypeScript-first; strong async/JSON tooling |
| Application layer (UI/API surfaces)                        | **TypeScript**                                 | Hono / Next.js for browser-native and API entry points          |
| Deployment, configuration                                  | **Language-agnostic**                          | YAML / JSON                                                     |

> **LLM abstraction**: Use **LiteLLM** as the provider-agnostic LLM layer. A single Python interface routes identically
> to Ollama, OpenAI, Anthropic, HuggingFace Inference, and 100+ others. No module should call an LLM provider SDK
> directly — all LLM calls go through LiteLLM.

---

### Communication & Protocols

| Technology                                                                            | Lang                | Role                                                                                      |
| ------------------------------------------------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------- |
| [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk) | TypeScript          | Official MCP SDK — use for all `infrastructure/mcp/` and TypeScript module MCP interfaces |
| [`mcp`](https://github.com/modelcontextprotocol/python-sdk)                           | Python              | Official Python MCP SDK — use for all Python module MCP interfaces                        |
| [`a2aproject/a2a`](https://github.com/a2aproject/A2A)                                 | Python / TypeScript | Reference A2A implementation — base for `infrastructure/a2a/`                             |

---

### LLM Abstraction (Provider-Agnostic)

| Technology                                      | Lang   | Role                                                                                                                                             |
| ----------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`LiteLLM`](https://github.com/BerriAI/litellm) | Python | Single interface to Ollama, OpenAI, Anthropic, HuggingFace, Bedrock, and 100+ providers. The provider-agnostic LLM layer for all Python modules. |

---

### Embeddings (Local-First)

| Technology                                                                 | Lang   | Role                                                                                                |
| -------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------- |
| [Ollama](https://github.com/ollama/ollama) + `nomic-embed-text`            | —      | Zero-infrastructure local embeddings; primary embedding backend (default: `http://localhost:11434`) |
| [`fastembed`](https://github.com/qdrant/fastembed)                         | Python | Lightweight Python embedding library — no model server required; native Qdrant integration          |
| [`sentence-transformers`](https://github.com/UKPLab/sentence-transformers) | Python | HuggingFace-backed; broader model selection for specialized embedding tasks                         |

---

### Vector Stores

| Technology                                        | Role                                   | When to Use                                                                         |
| ------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------- |
| [ChromaDB](https://github.com/chroma-core/chroma) | Embedded, zero-infra vector DB         | **Default** — local development and single-node deployments                         |
| [Qdrant](https://github.com/qdrant/qdrant)        | High-performance, filterable vector DB | **Recommended for production** — Rust server, excellent Python + TypeScript clients |
| [pgvector](https://github.com/pgvector/pgvector)  | PostgreSQL extension for vector search | Postgres-native deployments only                                                    |

All collections share a single configurable backend instance, namespaced as `brain.<module-name>`. See
`shared/vector-store/` for the adapter interface and `shared/vector-store/collection-registry.json` for the full
collection index.

---

### RAG & Document Ingestion

| Technology                                             | Lang   | Role                                                                                                                                                   |
| ------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [LlamaIndex](https://github.com/run-llama/llama_index) | Python | Ingestion, chunking, indexing, and retrieval pipelines — primary tool for `long-term-memory/seed/` and the `resources/static/knowledge/` boot pipeline |
| [Haystack](https://github.com/deepset-ai/haystack)     | Python | Alternative pipeline-oriented RAG framework                                                                                                            |

---

### Memory & State

| Technology                                                                              | Lang                | Role                                                                               |
| --------------------------------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------- |
| [Redis](https://github.com/redis/redis) / [Valkey](https://github.com/valkey-io/valkey) | —                   | Working memory KV store and session TTL management (`short-term-memory`)           |
| [SQLite](https://www.sqlite.org)                                                        | —                   | Local relational store for structured facts (`long-term-memory/relational-store/`) |
| [PostgreSQL](https://www.postgresql.org)                                                | —                   | Production relational store                                                        |
| [Kuzu](https://github.com/kuzudb/kuzu)                                                  | Python / TypeScript | Embedded graph DB — local-first choice for `long-term-memory/graph-store/`         |
| [Neo4j](https://github.com/neo4j/neo4j)                                                 | —                   | Production graph store                                                             |

---

### Reasoning & Planning

| Technology                                          | Lang   | Role                                                                                                   |
| --------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------ |
| [DSPy](https://github.com/stanfordnlp/dspy)         | Python | Structured prompting, self-optimization, and program synthesis over LLMs — fits `reasoning/inference/` |
| [Guidance](https://github.com/guidance-ai/guidance) | Python | Constrained / structured generation — useful for policy-following in `executive-agent/policy-engine/`  |

---

### Agent Runtime & Orchestration

| Technology                                         | Lang                | Role                                                                                                                        |
| -------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [Temporal](https://github.com/temporalio/temporal) | Python / TypeScript | Durable workflow execution with built-in retries, timeouts, and async task orchestration — primary fit for `agent-runtime/` |
| [Prefect](https://github.com/PrefectHQ/prefect)    | Python              | Lighter workflow orchestration alternative                                                                                  |

---

### Learning & Adaptation

| Technology                                                       | Lang   | Role                                                                 |
| ---------------------------------------------------------------- | ------ | -------------------------------------------------------------------- |
| [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) | Python | Battle-tested RL algorithms for `learning-adaptation/reinforcement/` |
| [RLlib (Ray)](https://github.com/ray-project/ray)                | Python | Distributed RL — scales well for production                          |
| [TorchRL](https://github.com/pytorch/rl)                         | Python | PyTorch-native RL toolkit                                            |

---

### Neuromorphic (Optional / Pluggable)

For modules where biologically-inspired spiking computation is beneficial. Implement as optional, independently
deployable modules; do not couple to the core signal path.

| Technology                                                               | Lang   | Notes                                                    |
| ------------------------------------------------------------------------ | ------ | -------------------------------------------------------- |
| [BindsNET](https://github.com/BindsNET/bindsnet)                         | Python | PyTorch-native; most approachable entry point            |
| [Brian2](https://github.com/brian-team/brian2)                           | Python | Well-maintained, research-grade                          |
| [Nengo](https://github.com/nengo/nengo)                                  | Python | Broadest hardware support pathway (Loihi via NengoLoihi) |
| [Intel Lava](https://github.com/lava-nc/lava)                            | Python | Loihi neuromorphic hardware target                       |
| [SpiNNaker / PyNN](https://github.com/SpiNNakerManchester/PyNN8Examples) | Python | SpiNNaker hardware target                                |
| [NEST](https://github.com/nest/nest-simulator)                           | Python | Large-scale biological neural network simulation         |

---

### Observability

| Technology                                                              | Lang                | Role                                                                                                                                  |
| ----------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [OpenTelemetry](https://github.com/open-telemetry/opentelemetry-python) | Python / TypeScript | Logs, metrics, and distributed traces via a single standard — spans all modules; primary implementation for `shared/utils/tracing.md` |
| [structlog](https://github.com/hynek/structlog)                         | Python              | Structured logging for Python modules                                                                                                 |
| [pino](https://github.com/pinojs/pino)                                  | TypeScript          | Structured logging for TypeScript modules                                                                                             |
| [Prometheus](https://github.com/prometheus/prometheus)                  | —                   | Metrics collection                                                                                                                    |
| [Grafana](https://github.com/grafana/grafana)                           | —                   | Dashboards — backs `observability/dashboards/`                                                                                        |
| [Grafana Tempo](https://github.com/grafana/tempo)                       | —                   | Distributed trace backend (pairs with OpenTelemetry)                                                                                  |

---

### Validation & Schemas

| Technology                                          | Lang       | Role                                                                               |
| --------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| [Pydantic v2](https://github.com/pydantic/pydantic) | Python     | Data validation, settings management, and JSON Schema generation from Python types |
| [Zod](https://github.com/colinhacks/zod)            | TypeScript | Schema declaration and validation — pairs with `shared/schemas/`                   |
| [buf](https://github.com/bufbuild/buf)              | —          | Protobuf toolchain for language-agnostic IDL in `shared/`                          |

---

### Security & Sandboxing

| Technology                                                          | Role                                                                   |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [OPA (Open Policy Agent)](https://github.com/open-policy-agent/opa) | Declarative policy enforcement — maps directly to `security/policies/` |
| [gVisor](https://github.com/google/gvisor)                          | Kernel-level container sandboxing for module isolation                 |

---

### Testing

| Technology                                                                                                      | Lang                | Role                                                     |
| --------------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------------------------------- |
| [pytest](https://github.com/pytest-dev/pytest) + [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | Python              | Standard Python test stack                               |
| [Vitest](https://github.com/vitest-dev/vitest)                                                                  | TypeScript          | Fast, native ESM TypeScript test runner                  |
| [Testcontainers](https://github.com/testcontainers/testcontainers-python)                                       | Python / TypeScript | Spins up real ChromaDB, Qdrant, Redis instances in tests |

---

### Monorepo Tooling

| Technology                                       | Lang       | Role                                                                         |
| ------------------------------------------------ | ---------- | ---------------------------------------------------------------------------- |
| [uv](https://github.com/astral-sh/uv)            | Python     | Modern Python package and environment management — replaces pip/poetry/pyenv |
| [pnpm](https://github.com/pnpm/pnpm)             | TypeScript | TypeScript package management                                                |
| [Turborepo](https://github.com/vercel/turborepo) | —          | Monorepo task runner for the polyglot structure                              |
