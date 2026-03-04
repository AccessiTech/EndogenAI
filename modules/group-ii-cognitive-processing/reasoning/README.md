# reasoning

**Decision-Making & Reasoning Layer** — `modules/group-ii-cognitive-processing/reasoning`

Prefrontal cortex analogue. Implements logical inference, causal planning, conflict resolution, and
structured generation. All LLM calls route through **LiteLLM**; no direct SDK imports.

---

## Purpose

The Reasoning module provides EndogenAI's structured inference and planning capabilities. It receives a query and optional context (typically assembled by Working Memory) and applies one of three inference strategies — `chain-of-thought`, `deductive`, or `abductive` — routing the underlying LLM call through LiteLLM. In addition to single-step inference it can generate multi-step causal plans with uncertainty estimates, and it persists every reasoning trace to the `brain.reasoning` vector collection for later semantic recall. The module sits between the Memory Layer (which provides context) and the Executive Agent (which consumes decisions), implementing the deliberative layer of the cognitive loop.

---

## Brain Analogy

Maps to `resources/neuroanatomy/prefrontal-cortex.md`:

| PFC Region | Function | Implementation |
|---|---|---|
| Dorsolateral PFC | Abstract reasoning, planning, cognitive flexibility | `InferencePipeline`, `CausalPlanner` |
| Anterior Cingulate Cortex | Conflict detection, uncertainty processing | `ConflictResolutionPolicy` in `models.py` |
| Orbitofrontal Cortex | Value computation under uncertainty | `uncertainty` field in `CausalPlan` |

---

## Interface

### A2A tasks (`http://localhost:8206`)

| Task type | Payload fields | Description |
|---|---|---|
| `run_inference` | `query`, `context[]`, `strategy`, `model` | Run a single inference step |
| `create_plan` | `goal`, `context[]` | Generate a causal plan |
| `query_traces` | `query`, `n_results` | Semantic search over stored traces |
| `run_full_reasoning` | `query`, `context[]`, `strategy`, `include_plan`, `model` | Inference + optional plan in one call |

### MCP tools (`http://localhost:8306`)

| Tool name | Params | Description |
|---|---|---|
| `reasoning.run_inference` | `query`, `context[]`, `strategy`, `include_plan`, `model` | Inference + optional plan |
| `reasoning.create_plan` | `goal`, `context[]` | Causal plan |
| `reasoning.query_traces` | `query`, `n_results` | Semantic search |

---

## Configuration

### `inference.config.json`

```json
{
  "defaultModel": "ollama/mistral",
  "litellmApiBase": "http://localhost:11434",
  "maxTokens": 1024,
  "temperature": 0.2,
  "traceRetentionHours": 24
}
```

### `vector-store.config.json`

```json
{
  "backend": "chromadb",
  "collection": "brain.reasoning",
  "host": "localhost",
  "port": 8000
}
```

---

## Cross-module Read Dependencies

| Collection | Source module | Purpose |
|---|---|---|
| `brain.long-term-memory` | long-term-memory | Background knowledge retrieval for reasoning context |
| `brain.affective` | affective | Prioritisation cues from the motivational layer |

All cross-module reads must be declared here and wired via `infrastructure/adapters/bridge.ts` —
no direct HTTP between modules.

---

## Deployment

Port **8206** (A2A) / **8306** (MCP).

```bash
cd modules/group-ii-cognitive-processing/reasoning
uv sync
uv run python -m reasoning  # TODO: add server entrypoint in Phase 6
```

---

## Running Checks

```bash
cd modules/group-ii-cognitive-processing/reasoning
uv sync
uv run ruff check .
uv run mypy src/
uv run pytest tests/ -m "not integration" -q

# Integration (requires Ollama + ChromaDB)
uv run pytest tests/ -m integration -q
```

## Testing

Framework: **pytest**. Coverage threshold: **80%** (enforce with `pytest-cov` once installed — see P05).

```bash
uv run pytest tests/ -m "not integration" --cov=src --cov-report=term-missing --cov-fail-under=80

# Skip integration tests:
SKIP_INTEGRATION_TESTS=1 uv run pytest tests/ -m "not integration" -q
SKIP_CHROMA_TESTS=1 uv run pytest tests/ -m "not integration" -q
```

Estimated coverage: ~65% (MEDIUM gap). Note: 4 integration tests are **permanently skipped** in current CI
because they require a live LiteLLM + Ollama + ChromaDB stack — dedicated integration CI job planned (see P24, T4).

Known gaps — no tests yet for:
- `src/a2a_handler.py` — see [workplan](../../../docs/test-upgrade-workplan.md) P09
- `src/mcp_tools.py` — see P10
