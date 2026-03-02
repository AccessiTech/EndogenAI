# Phase 5 Research Brief: MCP Solutions and Programmatic Techniques

> **Audience**: Phase 5 implementation agents and reviewers.  
> **Purpose**: Survey the programmatic landscape — context management protocols,
> memory architectures, retrieval patterns, and reasoning frameworks — that map onto
> the Phase 5 Group II cognitive modules. All techniques are evaluated for fit against
> the EndogenAI constraints: local compute first, no direct LLM SDK calls, shared
> adapter for vector stores, and reward signals via the canonical schema.

---

## 1. Context Window Management (Working Memory Analogue)

### 1.1 The Context Window as Working Memory

An LLM's context window is its working memory: a finite-capacity
active-context buffer that holds the current task state, retrieved facts, tool
call history, and ongoing reasoning chain. Like biological working memory, it:

- Has a hard capacity limit (tokens ≈ Baddeley's ~4 chunks).
- Exhibits recency bias — items near the end of the context have stronger influence.
- Degrades under noise — irrelevant tokens reduce the signal of relevant ones.
- Is not persistent — it is wiped between invocations (unless managed externally).

**Management strategies**:

| Strategy | Description | Biological analogue |
|----------|-------------|---------------------|
| Prompt stuffing / selective injection | Retrieve only the most relevant items and inject at query time | CA3 pattern-completion retrieval feeding working context |
| Sliding window | Drop oldest turns, keep recent N turns | Attentional decay / capacity eviction |
| Summarisation | Compress older context into a summary before eviction | Semantic abstraction (episodic → semantic) |
| Retrieval-augmented assembly | Query vector + KV stores and inject top-K results | EC two-way gateway + CA3 recall |
| Priority-based eviction | Evict lowest-importance items first when at capacity | BLA importance gating — emotional/goal salience |

The working-memory module (`modules/group-ii-cognitive-processing/memory/working-memory/`)
must implement these strategies explicitly. It is the orchestrator that assembles
the context payload delivered to other modules and ultimately to LiteLLM-routed LLM calls.

### 1.2 Capacity Enforcement

Working memory capacity should be enforced at two levels:

1. **Item count**: maintain a maximum number of MemoryItems in the active context
   (e.g. 20 items for the `brain.working-memory` collection).
2. **Token budget**: track cumulative token count of items in context; evict when
   approaching a configurable budget threshold.

Eviction policy: evict the item with the lowest `importanceScore` first. On tie,
evict the oldest by `createdAt`.

---

## 2. Retrieval-Augmented Generation (RAG)

### 2.1 Core Process

RAG enhances LLM generation by retrieving relevant documents from an external
knowledge base before generating a response. The standard pipeline:

```
user query
  → embed query (nomic-embed-text via Ollama)
  → vector similarity search in collection (ChromaDB / Qdrant)
  → retrieve top-K documents
  → inject into context window
  → route to LLM via LiteLLM
  → generate response
```

This is the primary mechanism for the working memory module to assemble context
from short-term, long-term, and episodic collections.

### 2.2 RAG Variants Relevant to Phase 5

| Variant | Description | Use in Phase 5 |
|---------|-------------|----------------|
| **Naive RAG** | Single-stage embed + retrieve + generate | Baseline retrieval for all memory modules |
| **Hybrid RAG** | Vector search + sparse (BM25/keyword) combined | Episodic memory retrieval: semantic similarity + exact `sessionId/taskId` filter |
| **Self-RAG / FLARE** | Model decides when to retrieve and what to retrieve | Working memory loader: retrieve-on-demand when context confidence is low |
| **Corrective RAG** | Retrieved documents are evaluated for relevance; irrelevant ones trigger re-query | Gate for long-term memory retrieval to reduce noise injection |
| **Recursive / multi-hop RAG** | Iterative retrieval — each retrieval stage informs the next query | Causal reasoning in the reasoning module: chain of retrieved evidence |

### 2.3 Chunking Strategies

Chunking strategy determines the granularity of what the vector store can retrieve.
For Phase 5 seed ingestion (LlamaIndex, `resources/static/knowledge/`):

- **Semantic chunking** (LlamaIndex default): splits on natural sentence/paragraph
  boundaries. Best for narrative knowledge base documents.
- **Frontmatter-aware chunking**: the project's seed docs contain YAML frontmatter
  (`id`, `version`, `status`, `maps-to-modules`). The ingest pipeline must parse and
  preserve this as metadata on each chunk, enabling collection routing.
- **Module-scoped chunking**: route chunks based on `maps-to-modules` frontmatter
  to the correct collection (e.g. hippocampus stubs → `brain.long-term-memory`).

---

## 3. Tiered Memory Store Architecture

### 3.1 The Three-Tier Model

Phase 5 implements a tiered store that mirrors the brain's CLS dual-system:

```
Tier 1: Short-term buffer (Redis / Valkey)
  - Scope:   session-scoped, TTL-governed
  - Purpose: Transient working context; rapid read/write; key-value pairs
  - Eviction: TTL expiry → triggers consolidation pipeline

Tier 2: Episodic + Long-term vector store (ChromaDB default, Qdrant production)
  - Scope:   persistent, content-addressable
  - Purpose: Semantic similarity retrieval; embedding-based recall
  - Eviction: importanceScore threshold + manual archival

Tier 3: Structured facts (SQLite default, PostgreSQL production)
  - Scope:   persistent, schema-constrained
  - Purpose: Exact-match lookup; entity-relationship facts; metadata registry
  - Eviction: explicit deletion / archival policy
```

### 3.2 Collection Routing Rules

Every memory write must be routed to the correct collection based on:

| Condition | Target collection |
|-----------|------------------|
| New item in active session, no consolidation decision yet | `brain.short-term-memory` |
| Item from working context (assembled context payload) | `brain.working-memory` |
| Item after consolidation gate: `importanceScore ≥ 0.5` | `brain.long-term-memory` |
| Item has `sessionId + taskId + timestamp` (what-where-when triple) | `brain.episodic-memory` |
| Item is a `RewardSignal` or carries affective tags | `brain.affective` |
| Item is an inference trace, plan, or causal model | `brain.reasoning` |

### 3.3 Vector + KV Hybrid Access Pattern

For the working memory loader:

```python
# 1. Exact match: retrieve by sessionId from Redis
session_items = redis.lrange(f"session:{session_id}", 0, -1)

# 2. Semantic match: retrieve nearest neighbours from ChromaDB
relevant = chroma.query(
    query_embeddings=[embed(query)],
    n_results=10,
    where={"collectionName": {"$in": ["brain.long-term-memory", "brain.episodic-memory"]}}
)

# 3. Structured match: retrieve entity facts from SQLite
facts = sqlite.execute("SELECT * FROM facts WHERE entity_id = ?", [entity_id])

# 4. Merge, deduplicate, sort by importanceScore desc, trim to capacity
context = merge_and_rank(session_items, relevant, facts, capacity=20)
```

This mirrors the entorhinal cortex's two-way gateway: it collects inputs from both
the fast (hippocampal/Redis) and slow (neocortical/ChromaDB+SQLite) systems.

---

## 4. Episodic Memory Access Patterns

### 4.1 What–Where–When Indexing

Every episodic memory item must carry the full Tulving triple as metadata:

```json
{
  "id": "<uuid>",
  "type": "episodic",
  "collectionName": "brain.episodic-memory",
  "content": "...",
  "sessionId": "<session-uuid>",      // WHERE: session context = spatial analogue
  "sourceTaskId": "<task-uuid>",      // WHAT: the task or action
  "createdAt": "<iso8601-timestamp>", // WHEN: temporal anchor
  "affectiveValence": 0.8             // emotional salience (BLA analogue)
}
```

### 4.2 Composite Query Strategy

Episodic retrieval requires both semantic similarity and temporal/contextual filters:

```python
# Semantic similarity + temporal/contextual filter
results = chroma.query(
    query_embeddings=[embed(query)],
    n_results=20,
    where={
        "$and": [
            {"sessionId": session_id},
            {"createdAt": {"$gte": window_start_iso}}
        ]
    }
)
# Re-rank by combined score: similarity * importanceScore * recency_decay
```

### 4.3 Timeline Query

For episodic replay (consolidation pipeline simulation):

```python
# Retrieve all events in a session ordered by time
episodes = chroma.get(
    where={"sessionId": session_id},
    include=["documents", "metadatas"],
)
episodes.sort(key=lambda x: x.metadata["createdAt"])
```

---

## 5. Consolidation Pipeline Design

### 5.1 Pipeline Stages

The consolidation pipeline runs as a background task. Its biological analogue is
slow-wave sleep replay. It should be triggered:

- On session end.
- When `brain.short-term-memory` exceeds a configurable item threshold.
- On a scheduled interval (e.g. every N minutes).

```
Stage 1: SCAN
  Read all items from brain.short-term-memory with TTL < threshold

Stage 2: SCORE
  For each item: compute final importanceScore
    = base_score
    + accessCount * access_weight
    + affectiveValence * affective_weight
    + novelty_score (from DG pattern-separation analogue)

Stage 3: GATE
  if importanceScore >= 0.5:
    promote to brain.long-term-memory (or brain.episodic-memory if has sessionId)
  else:
    expire / delete

Stage 4: EMBED
  Re-embed promoted items using nomic-embed-text
  Write to ChromaDB with updated metadata

Stage 5: PRUNE
  Remove promoted/expired items from brain.short-term-memory
```

### 5.2 Novelty Detection (DG Analogue)

Before writing a new item to short-term memory, query for near-duplicates:

```python
existing = chroma.query(
    query_embeddings=[embed(content)],
    n_results=1,
    where={"collectionName": "brain.short-term-memory"}
)
cosine_sim = existing["distances"][0][0]  # ChromaDB returns L2 or cosine
if cosine_sim > NOVELTY_THRESHOLD:
    # Not novel — update existing item's importanceScore instead of creating new
    chroma.update(existing_id, metadata={"importanceScore": updated_score})
else:
    # Novel — create new item with initial importanceScore
    chroma.add(new_item)
```

---

## 6. LlamaIndex Memory Modules

LlamaIndex provides composable memory abstractions used in the Phase 5 seed
pipeline and optionally in the working memory loader:

| Module | Description | Phase 5 Use |
|--------|-------------|-------------|
| `ChatMemoryBuffer` | Stores recent chat turns; trim based on token budget | Working memory TTL buffer — session-scoped turn history |
| `VectorMemory` | Embeds and stores all turns; queries by semantic similarity | Long-term memory retrieval — populate context from ChromaDB |
| `SimpleComposableMemory` | Chains multiple memory types; primary = ChatMemoryBuffer, secondary = VectorMemory | Working memory loader — primary Redis + secondary ChromaDB |

The `SimpleComposableMemory` pattern is the closest LlamaIndex equivalent to the
working memory module's retrieval-augmented assembly function.

**Note**: LlamaIndex is used for the seed ingestion pipeline and as an architectural
reference. In Phase 5, the actual memory module implementations are custom Python
(adhering to the `endogenai_vector_store` shared adapter), not LlamaIndex wrappers.
Use LlamaIndex patterns as design templates, not as direct dependencies.

---

## 7. Affective Context Propagation

### 7.1 Reward Signals as MCP Payloads

The `RewardSignal` schema (`shared/types/reward-signal.schema.json`) defines the
canonical affective payload propagated between modules. Every reward signal must:

- Carry a `value` in `[-1.0, 1.0]` (dopamine RPE analogue: -1 = strong penalty,
  0 = neutral, +1 = strong reward).
- Specify a `type` from the allowed enum (reward, penalty, neutral, novelty,
  urgency, curiosity, satisfaction, frustration, confidence-boost, confidence-drop).
- Identify the `sourceModule` that generated it.
- Be stored in `brain.affective` with the triggering event IDs as metadata.

### 7.2 Affective Propagation Through the Memory Stack

```
Event (from Group I signal processing)
  → Affective module scores event (→ RewardSignal)
  → Working memory receives signal alongside the event
  → Working memory adjusts importanceScore of co-occurring items:
      item.importanceScore += reward_signal.value * AFFECTIVE_WEIGHT
  → Consolidation pipeline inherits the boosted importanceScore
  → High-valence items promoted preferentially to long-term / episodic stores
```

This mirrors the BLA → hippocampus projection: emotional arousal at encoding
boosts long-term retention.

### 7.3 Urgency Scoring

The `urgency` reward signal type maps to the nucleus accumbens motivational drive
variable. When the affective module emits a high-urgency signal:

- The working memory module should prioritise retrieval of items related to the
  urgent context (re-rank by a combined `importanceScore * urgency_factor`).
- The reasoning module should receive the urgency level as a constraint on its
  search depth and response time budget.

---

## 8. DSPy for Structured Reasoning

### 8.1 What DSPy Provides

DSPy (Declarative Self-improving Python) is a framework for programmatic LLM
pipelines with:

- **Typed signatures**: define input/output types for each reasoning step.
- **Modules**: `dspy.Predict`, `dspy.ChainOfThought`, `dspy.ReAct`, `dspy.ProgramOfThought`.
- **Optimisers**: compile and improve prompts against a metric, without manual
  prompt engineering.
- All LLM calls route through DSPy's `dspy.settings.lm` — this must be configured
  as a LiteLLM-compatible endpoint.

### 8.2 Reasoning Module Design

The reasoning module (`modules/group-ii-cognitive-processing/reasoning/`) implements
four reasoning capabilities via DSPy:

| Capability | DSPy module | PFC analogue |
|-----------|-------------|-------------|
| Logical inference | `dspy.ChainOfThought` | DLPFC abstract reasoning |
| Causal reasoning | `dspy.ProgramOfThought` | vmPFC causal modelling |
| Planning under uncertainty | `dspy.ReAct` (Reason+Act loop) | ACC conflict monitoring + DLPFC plan generation |
| Conflict resolution | `dspy.MultiChainComparison` | ACC error detection + OFC option comparison |

### 8.3 LiteLLM Configuration (Mandatory)

All reasoning calls must route through LiteLLM:

```python
import dspy
import litellm

# Configure DSPy to use LiteLLM
lm = dspy.LM(
    model="ollama/llama3.2",           # or "openai/gpt-4o" etc
    api_base="http://localhost:11434",  # Ollama local
    cache=False
)
dspy.configure(lm=lm)

# All subsequent dspy.Predict / dspy.ChainOfThought calls use LiteLLM
```

**Never** call `openai.chat.completions.create()`, `anthropic.messages.create()`, or
`ollama.chat()` directly. All inference routes through LiteLLM.

### 8.4 Inference Trace Storage

Every DSPy reasoning call should produce a structured trace stored in `brain.reasoning`:

```python
trace = {
    "id": str(uuid4()),
    "type": "working",                  # or "reusable" for cached plans
    "collectionName": "brain.reasoning",
    "content": json.dumps(dspy_result.toDict()),
    "structuredData": {
        "module": "ChainOfThought",
        "signature": "premise -> conclusion",
        "confidence": dspy_result.confidence
    },
    "importanceScore": confidence_to_importance(dspy_result.confidence)
}
vector_store.add("brain.reasoning", trace)
```

---

## 9. Guidance for Constrained Generation

### 9.1 What Guidance Provides

Guidance is a constrained generation library that enforces output schemas at the
token level, preventing hallucination of invalid structures. Use cases in Phase 5:

- **Structured memory items**: force LLM output to conform to `MemoryItem` JSON schema.
- **Reward signal generation**: constrain affective module output to valid `RewardSignal` types.
- **Plan output**: force the reasoning module to produce plans in a machine-parseable format.

### 9.2 Inhibitory Control Analogue

Guidance implements the inferior frontal gyrus (IFG) inhibitory control function:
just as the IFG suppresses prepotent (automatic but incorrect) responses, Guidance
suppresses out-of-schema token sequences. This is the programmatic analogue of
executive inhibition.

---

## 10. Shared Vector Store Adapter (Mandatory Pattern)

All five Phase 5 collections must be accessed exclusively through
`endogenai_vector_store` — never via the underlying ChromaDB or Qdrant clients
directly. The adapter provides:

- Backend-agnostic interface: same code works with ChromaDB (dev) and Qdrant (prod).
- Automatic embedding model selection (defaults to Ollama `nomic-embed-text`).
- Collection schema validation against `shared/vector-store/collection-registry.json`.
- Consistent metadata fields (`collectionName`, `type`, `importanceScore`, etc.).

```python
# Correct
from endogenai_vector_store import VectorStoreAdapter
store = VectorStoreAdapter(backend="chromadb", config=chroma_config)
store.add("brain.short-term-memory", item)

# Wrong — never do this
import chromadb
client = chromadb.Client()
collection = client.get_collection("brain.short-term-memory")
collection.add(...)
```

---

## 11. Closing References

- [shared/types/memory-item.schema.json](../../shared/types/memory-item.schema.json) — canonical memory item schema
- [shared/types/reward-signal.schema.json](../../shared/types/reward-signal.schema.json) — canonical reward signal schema
- [shared/vector-store/collection-registry.json](../../shared/vector-store/collection-registry.json) — all Phase 5 collections and their constraints
- [shared/vector-store/README.md](../../shared/vector-store/README.md) — adapter pattern and collection registry guide
- [docs/research/phase-5-neuroscience-of-organic-memory.md](phase-5-neuroscience-of-organic-memory.md) — neuroscience companion brief
- [docs/research/phase-5-synthesis-workplan.md](phase-5-synthesis-workplan.md) — module-level synthesis and implementation guidance
- [docs/Workplan.md](../Workplan.md) — Phase 5 checklist (§§5.1–5.6)
- [infrastructure/adapters/src/bridge.ts](../../infrastructure/adapters/src/bridge.ts) — MCP/A2A bridge for cross-module communication
