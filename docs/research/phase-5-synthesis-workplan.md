# Phase 5 Research Brief: Synthesis — Brain-Inspired Architecture and Implementation Guidance

> **Audience**: Phase 5 implementation agents (Memory → Motivation → Reasoning domain executives).  
> **Purpose**: Synthesise the neuroscience research and programmatic techniques into a
> module-by-module implementation guide for Phase 5 Group II. Each section maps biological
> findings to concrete design decisions, collection routing rules, technology choices, and
> open questions. This document is the primary pre-implementation reference; the actual
> phase checklist lives in [docs/Workplan.md](../Workplan.md) §§5.1–5.6.

---

## 1. Guiding Architectural Principles

The following principles are derived directly from the research briefs and govern every
Phase 5 module:

| Principle | Biological origin | Implementation rule |
|-----------|-----------------|---------------------|
| **Tiered memory, never flat** | CLS dual-system (fast hippocampal + slow neocortical) | Maintain separate Redis (STM), ChromaDB (LTM/episodic), and SQLite (semantic facts) stores; never collapse them |
| **Episodic always carries what-where-when** | Tulving's three properties | `sessionId + sourceTaskId + createdAt` are required on every `episodic` type item |
| **Consolidation is a pipeline, not a copy** | Systems consolidation via replay | A background scoring/promotion job gates every STM→LTM transition via `importanceScore ≥ 0.5` |
| **Retrieval reconsolidates** | Reconsolidation on every retrieval | Every retrieval event must increment `accessCount` and re-evaluate `importanceScore` |
| **Affect modulates memory** | BLA → hippocampus projection | `affectiveValence` on `MemoryItem` boosts `importanceScore` during scoring; all reward signals attach to co-occurring memory items |
| **LLM calls are never direct** | — | All inference routes through LiteLLM; DSPy `lm` is configured with a LiteLLM endpoint |
| **Adapters, never raw SDKs** | — | `endogenai_vector_store` for all collection access; `infrastructure/adapters/bridge.ts` for all cross-module calls |
| **Novel inputs fork new items** | DG pattern separation | Near-duplicate detection before write; update existing item if cosine similarity > threshold |

---

## 2. Module §5.1 — Working Memory

### 2.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|-------------------|------------------------|
| DLPFC: active manipulation of representations via recurrent networks | The working memory module is the **assembler** — it pulls from other stores, holds active context, and delivers a ranked context payload |
| Capacity ~4 chunks (Cowan 2001) | Hard cap on item count + token budget; evict lowest-`importanceScore` item when at capacity |
| Baddeley's episodic buffer: integrates multimodal info, bridges to LTM | The assembled context payload must include items from STM, LTM, and episodic stores — multi-source integration |
| Central executive: suppresses irrelevant info | Retrieval must score and filter; do not blindly include all retrieved items |
| WM = activated subset of LTM | Working memory is not a new store — it is a view over other collections, materialised into `brain.working-memory` for the current turn |
| Theta-band oscillations bind features into chunks | Items with multiple related attributes should be stored as structured `MemoryItem.structuredData` rather than flat text |

### 2.2 Collection: `brain.working-memory`

- Layer: prefrontal
- Type: working
- Capacity: max 20 items (configurable)
- Eviction: lowest `importanceScore` first; on tie, oldest `createdAt`
- TTL: session-scoped; cleared on session end

### 2.3 Core Interfaces

**MCP (context exchange)**:
- Tool: `working_memory.assemble_context(session_id, query, capacity_override?)` → assembled context payload
- Tool: `working_memory.update_item(item_id, delta)` → update importanceScore / content
- Tool: `working_memory.evict(item_id)` → remove item; trigger consolidation check

**A2A (task delegation)**:
- Accepts task: `{type: "assemble_context", session_id, query}` → returns `ContextPayload`
- Accepts task: `{type: "consolidate_session", session_id}` → triggers consolidation pipeline

### 2.4 Open Questions (§5.1)

- Should the working memory module maintain its own token-counting budget, or rely on
  the calling LLM's context length limit?
- What is the right decay window for a working memory item before it is deprioritised
  (biological analogue: ~30 seconds without attentional refresh)?

---

## 3. Module §5.2 — Short-Term Memory

### 3.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|-------------------|------------------------|
| STM is hippocampally mediated, session-scoped | Redis / Valkey with session-keyed lists; TTL = session expiry policy |
| Decay without consolidation | Every item has a TTL; on expiry, the consolidation pipeline is triggered (score → promote or discard) |
| CA1 novelty detection: compare expected vs. retrieved | Before write, query for near-duplicates; if cosine similarity > 0.9 → update existing, else create new |
| Strong encoding from emotional arousal | `affectiveValence` from co-occurring RewardSignal boosts initial `importanceScore` at write time |
| Pattern separation in DG prevents interference | Near-duplicate detection + sparse tagging ensures distinct episodes don't overwrite each other |

### 3.2 Collection: `brain.short-term-memory`

- Layer: memory
- Type: short-term
- TTL policy: session-scoped + configurable absolute TTL (e.g. 30 minutes)
- Consolidation trigger: TTL expiry OR item count threshold (e.g. 500 items)
- Embedding: `nomic-embed-text` via Ollama

### 3.3 Consolidation Pipeline (STM → LTM)

```
On TTL expiry or threshold trigger:
  For each item in brain.short-term-memory:
    1. Compute finalScore = importanceScore + (accessCount * 0.1) + (affectiveValence * 0.2)
    2. if finalScore >= 0.5 AND has sessionId+taskId+timestamp:
         promote → brain.episodic-memory
    3. elif finalScore >= 0.5:
         promote → brain.long-term-memory
    4. else:
         delete
    5. Remove from brain.short-term-memory
```

### 3.4 Open Questions (§5.2)

- Should near-duplicate detection use L2 distance or cosine similarity? ChromaDB
  defaults to L2; the biological pattern separation analogy favours cosine for
  semantic overlap detection.
- What is the right base TTL? 30 minutes maps roughly to the biological ~30-minute
  consolidation window for freshly encoded memories.

---

## 4. Module §5.3 — Long-Term Memory

### 4.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|-------------------|------------------------|
| Standard Model: neocortical traces are hippocampus-independent after transfer | Long-term memory collection holds semantic/decontextualised facts; retrieval does not require session context |
| LTP as importanceScore accumulation | Each retrieval increments `accessCount`; reconsolidation pipeline recalculates `importanceScore` |
| Multiple Trace Theory: episodic stays hippocampus-dependent | Episodic items with strong contextual metadata stay in `brain.episodic-memory`; decontextualised distillations migrate to `brain.long-term-memory` |
| Sleep consolidation = scheduled background job | Consolidation pipeline should run on a configurable schedule (cron / background task) |

### 4.2 Collection: `brain.long-term-memory`

- Layer: memory
- Type: long-term
- Embedding: `nomic-embed-text` via Ollama
- Importance threshold: `importanceScore ≥ 0.5` at promotion time
- Graph store: Kuzu (default) / Neo4j (production) for entity-relationship facts
- Structured facts: SQLite (default) / PostgreSQL (production)

### 4.3 Retrieval Pattern

```python
# Dual retrieval: semantic + structured
semantic = vector_store.query(
    "brain.long-term-memory",
    query_embeddings=embed(query),
    n_results=10
)
structured = sqlite.execute(
    "SELECT * FROM facts WHERE entity = ? ORDER BY importance DESC LIMIT 10",
    [entity_id]
)
merged = rank_and_merge(semantic, structured, top_k=15)
```

### 4.4 Open Questions (§5.3)

- What is the appropriate schema for the SQLite facts table? At minimum: `entity_id`,
  `predicate`, `object`, `importance`, `source_item_id`, `created_at`.
- Should the graph store (Kuzu) use the same importance-gated promotion pipeline as
  the vector store, or a separate edge-creation policy?

---

## 5. Module §5.4 — Episodic Memory

### 5.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|-------------------|------------------------|
| Tulving what-where-when triple | Required metadata: `sessionId` (where), `sourceTaskId` (what), `createdAt` (when) |
| Autonoetic re-experience = reconstructive retrieval | Episodic retrieval should reconstruct the full event sequence, not just the nearest item |
| Nine properties: temporal order, short time-slices | Timeline query must return items ordered by `createdAt`; each item should represent one discrete event, not an aggregated summary |
| Emotional boost from BLA | `affectiveValence` required on all episodic items; high-valence items get priority in timeline reconstruction |
| Semantic memory distilled from episodic | A background distillation job should periodically extract recurring patterns from episodic store and write decontextualised facts to long-term memory |

### 5.2 Collection: `brain.episodic-memory`

- Layer: memory
- Type: episodic
- Required metadata: `sessionId`, `sourceTaskId`, `createdAt` (all three mandatory)
- Embedding: `nomic-embed-text` via Ollama
- Composite query: semantic similarity + temporal/contextual filters

### 5.3 Semantic Distillation (Episodic → Long-Term)

```
Periodically (or on session end):
  For each session in brain.episodic-memory:
    1. Retrieve all items ordered by createdAt
    2. Identify recurring content patterns (cosine similarity clustering)
    3. For each cluster with ≥ 3 occurrences:
         create new MemoryItem(type=long-term, content=centroid_summary)
         write to brain.long-term-memory
    4. Increment accessCount on source episodic items (reconsolidation analogue)
```

### 5.4 Open Questions (§5.4)

- Should episodic items be immutable (append-only) once written, with only metadata
  updated on reconsolidation? Biological episodic reconsolidation is constructive
  (memories can be distorted on retrieval), but for auditability, immutable items
  with versioned updates may be preferable.
- What granularity should one "episode" represent — a single tool call, a task step,
  or a full task?

---

## 6. Module §5.5 — Affective / Motivational

### 6.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|-------------------|------------------------|
| Dopamine RPE: VTA phasic burst = unexpected reward | `RewardSignal.value > 0` = positive RPE; `value < 0` = negative RPE; magnitude encodes surprise |
| Incentive salience (nucleus accumbens) | `urgency` signal type drives priority re-ranking in working memory loader |
| BLA emotional tagging → hippocampal amplification | All `RewardSignal` items are linked to co-occurring memory items; the affective module writes to `brain.affective` and triggers `importanceScore` boost |
| Hypothalamus drive variables | Drive variables (urgency, novelty, threat) are computed from the stream of incoming signals and emitted as urgency-type RewardSignals |
| ACC conflict monitoring | `frustration` and `confidence-drop` signal types are emitted when reasoning detects conflict or uncertainty |

### 6.2 Collection: `brain.affective`

- Layer: limbic
- Type: short-term (short-lived context; medium-lived if `importanceScore` is high)
- Required metadata: triggering event IDs
- Churn: high; most items expire after session end

### 6.3 Reward Signal Flow

```
Group I signal (from sensory-input / attention-filtering / perception)
  → Affective module receives signal
  → Compute RPE: compare expected value with actual signal content
  → Emit RewardSignal(value, type, trigger, sourceModule="affective")
  → Write RewardSignal to brain.affective
  → Notify working memory: attach signal to co-occurring MemoryItems
  → Working memory: importanceScore += signal.value * AFFECTIVE_WEIGHT
```

### 6.4 Drive Variable Computation

The affective module maintains a lightweight drive state:

```python
drives = {
    "urgency": 0.0,    # [0, 1] — time-pressure / threat level
    "novelty": 0.0,    # [0, 1] — information gain signal
    "curiosity": 0.0,  # [0, 1] — exploration incentive
}
# Updated on each incoming signal; emitted as urgency/novelty/curiosity RewardSignals
# when drive values cross configurable thresholds
```

### 6.5 Open Questions (§5.5)

- Should drive state persist across sessions (homeostatic baseline), or reset on
  each session start (stateless)?
- How should conflicting reward signals (e.g. simultaneous high urgency + high
  novelty) be arbitrated? Additive? Max? Weighted priority?

---

## 7. Module §5.6 — Decision-Making and Reasoning

### 7.1 Neuroscience Derivation

| Biological finding | Implementation decision |
|-------------------|------------------------|
| DLPFC: abstract reasoning, working memory manipulation | `dspy.ChainOfThought` for logical/abstract inference; all CoT steps stored as traces |
| vmPFC: causal modelling, reward under uncertainty | `dspy.ProgramOfThought` for causal chains; uncertainty quantified via confidence score |
| ACC: conflict monitoring, error detection | `frustration` and `confidence-drop` RewardSignals emitted when DSPy detects inconsistency |
| OFC: comparing reward of alternative options | `dspy.MultiChainComparison` for option evaluation; stores option evaluations in `brain.reasoning` |
| IFG: inhibitory control of prepotent responses | Guidance constrained generation to suppress invalid output structures |
| PFC top-down gating of memory retrieval | Reasoning module passes query + context constraints to working memory loader for targeted context assembly |

### 7.2 Collection: `brain.reasoning`

- Layer: prefrontal
- Type: working (high churn)
- Reusable flag: items can be flagged `reusable=true` and cached for repeated queries
- Embedding: `nomic-embed-text` via Ollama
- Structured traces stored in `structuredData` field

### 7.3 DSPy Signature Examples

```python
import dspy

class LogicalInference(dspy.Signature):
    """Given premises, derive a logical conclusion with confidence."""
    premises: list[str] = dspy.InputField(desc="List of known facts")
    conclusion: str = dspy.OutputField(desc="Logical conclusion")
    confidence: float = dspy.OutputField(desc="Confidence score [0, 1]")

class CausalPlan(dspy.Signature):
    """Given a goal and current state, produce a causal action plan."""
    goal: str = dspy.InputField(desc="Desired outcome")
    current_state: str = dspy.InputField(desc="Current system state")
    context: list[str] = dspy.InputField(desc="Retrieved memory context")
    steps: list[str] = dspy.OutputField(desc="Ordered action steps")
    uncertainty: float = dspy.OutputField(desc="Uncertainty estimate [0, 1]")
```

### 7.4 Open Questions (§5.6)

- DSPy optimisers require labelled training data. For Phase 5, which optimiser is
  appropriate without labelled data? `dspy.BootstrapFewShot` with a self-consistency
  metric may be the correct starting point.
- Should reasoning traces be stored per-step (granular) or per-request (aggregated)?
  Granular traces enable better debugging but increase storage volume.

---

## 8. Cross-Module Integration Design

### 8.1 Signal Flow Across Phase 5

```
[Group I Output]
      ↓
[Affective Module §5.5]
 - Scores signal → RewardSignal
 - Writes to brain.affective
 - Notifies working memory of reward event
      ↓
[Working Memory §5.1]
 - Receives signal + reward notification
 - Queries STM, LTM, episodic for relevant context
 - Assembles capacity-constrained context payload
 - Applies affective importanceScore boost
 - Writes active items to brain.working-memory
      ↓
[Reasoning Module §5.6]
 - Receives assembled context + reward context
 - Routes to appropriate DSPy signature
 - Stores trace to brain.reasoning
 - Emits confidence-based reward signals back to affective
      ↓
[Group III Executive Output (Phase 6)]
```

### 8.2 Consolidation Loop (Background)

```
[STM Expiry / Session End trigger]
      ↓
[Short-Term Memory §5.2] — consolidation pipeline
 - Score items: importanceScore + affectiveValence + accessCount
 - Promote to brain.long-term-memory (semantic) or brain.episodic-memory (contextual)
 - Delete below-threshold items
      ↓
[Episodic Distillation §5.4] — periodic background job
 - Cluster recurring episodic events
 - Distil high-frequency patterns → brain.long-term-memory
```

---

## 9. Recommended Implementation Sequence

Implement in strict dependency order within the Memory domain:

```
1. Working Memory (§5.1) — depends on: all other memory modules (retrieval targets)
   BUT: can implement scaffold + interfaces first, then wire up retrieval
2. Short-Term Memory (§5.2) — simplest module; Redis + consolidation pipeline
3. Long-Term Memory (§5.3) — ChromaDB + SQLite + Kuzu; semantic retrieval
4. Episodic Memory (§5.4) — ChromaDB with composite queries; distillation job
   [Gate 1: all four memory modules pass tests before Motivation]
5. Affective / Motivational (§5.5) — depends on working memory for importanceScore boost
   [Gate 2: affective module passes tests before Reasoning]
6. Reasoning (§5.6) — depends on working memory context assembly + affective signals
```

**Within each module**, implement in this order:
1. `pyproject.toml` + package scaffold + `agent-card.json` (from neuroanatomy stubs)
2. Core data types (extend `MemoryItem` schema if needed — land in `shared/schemas/` first)
3. Vector store integration (via `endogenai_vector_store` adapter only)
4. Core logic (consolidation pipeline, DSPy signatures, scoring functions)
5. MCP interface (tools exposed over MCP)
6. A2A interface (task handlers)
7. Unit tests + integration tests (Testcontainers for ChromaDB/Redis)
8. `README.md`

---

## 10. Technology Stack Summary

| Component | Development | Production |
|-----------|------------|-----------|
| Short-term buffer | Redis (or in-process dict for tests) | Valkey |
| Vector store | ChromaDB (local) | Qdrant |
| Graph store | Kuzu (local) | Neo4j |
| Structured facts | SQLite | PostgreSQL |
| Embeddings | Ollama `nomic-embed-text` | Ollama `nomic-embed-text` (local-first) |
| Reasoning | DSPy + LiteLLM → Ollama (local) | DSPy + LiteLLM → configurable |
| Constrained generation | Guidance | Guidance |
| Test containers | Testcontainers (Python) | — |
| Seed ingestion | LlamaIndex + scripts/ingest_seed.py | Same |

---

## 11. Phase 5 Completion Signal

Phase 5 is complete when:

1. All six modules have `README.md`, `agent-card.json`, `pyproject.toml`, `src/`, `tests/`.
2. All five Phase 5 collections receive embeddings end-to-end:
   - `brain.short-term-memory`
   - `brain.long-term-memory`
   - `brain.episodic-memory`
   - `brain.affective`
   - `brain.reasoning`
3. The consolidation pipeline runs successfully in integration tests (STM item → score → LTM promotion).
4. A reward signal propagates from the affective module to a working memory `importanceScore` boost.
5. A DSPy reasoning call produces a stored trace in `brain.reasoning`.
6. All §§5.1–5.6 workplan checklist items are `[x]`.
7. `pnpm run lint && pnpm run typecheck` pass (no TypeScript under Group II, but infrastructure
   adapters that wire Group II must pass).
8. `uv run ruff check . && uv run mypy src/ && uv run pytest` pass in each module.

---

## 12. Closing References

- [docs/research/phase-5-neuroscience-of-organic-memory.md](phase-5-neuroscience-of-organic-memory.md) — neuroscience foundations
- [docs/research/phase-5-mcp-solutions-and-programmatic-techniques.md](phase-5-mcp-solutions-and-programmatic-techniques.md) — programmatic techniques
- [docs/Workplan.md](../Workplan.md) — canonical Phase 5 checklist (§§5.1–5.6)
- [modules/AGENTS.md](../../modules/AGENTS.md) — mandatory module contract (agent-card.json, MCP/A2A, tests)
- [shared/types/memory-item.schema.json](../../shared/types/memory-item.schema.json)
- [shared/types/reward-signal.schema.json](../../shared/types/reward-signal.schema.json)
- [shared/vector-store/collection-registry.json](../../shared/vector-store/collection-registry.json)
- [resources/neuroanatomy/hippocampus.md](../../resources/neuroanatomy/hippocampus.md)
- [resources/neuroanatomy/limbic-system.md](../../resources/neuroanatomy/limbic-system.md)
- [resources/neuroanatomy/prefrontal-cortex.md](../../resources/neuroanatomy/prefrontal-cortex.md)
- [infrastructure/adapters/src/bridge.ts](../../infrastructure/adapters/src/bridge.ts) — MCP/A2A bridge
