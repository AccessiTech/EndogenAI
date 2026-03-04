# endogenai-vector-store

Backend-agnostic vector store adapter for EndogenAI. Provides a unified interface over ChromaDB and Qdrant,
plus an Ollama-backed embedding wrapper (`src/embedding.py`). All cognitive modules that need vector storage
use this adapter — no module calls ChromaDB or Qdrant SDKs directly.

---

## Install

```bash
cd shared/vector-store/python
uv sync
```

---

## Usage

```python
from endogenai_vector_store import get_vector_store

store = get_vector_store()  # uses VECTOR_STORE_BACKEND env var; defaults to chromadb
store.upsert(collection="brain.working-memory", items=[...])
results = store.query(collection="brain.working-memory", query_embedding=[...], top_k=10)
```

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `VECTOR_STORE_BACKEND` | `chromadb` | `chromadb` or `qdrant` |
| `CHROMADB_URL` | `http://localhost:8000` | ChromaDB server URL |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama embedding server URL |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Ollama model for embeddings |
| `SKIP_CHROMA_TESTS` | unset | Set to skip ChromaDB integration tests |
| `SKIP_QDRANT_TESTS` | unset | Set to skip Qdrant integration tests |
| `SKIP_INTEGRATION_TESTS` | unset | Coarse override — skips all integration tests |

---

## Testing

Framework: **pytest**. Coverage threshold: **80%**.

```bash
cd shared/vector-store/python

# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Skip ChromaDB integration tests (no live ChromaDB required)
SKIP_CHROMA_TESTS=1 uv run pytest -m "not integration" -q

# Skip Qdrant integration tests
SKIP_QDRANT_TESTS=1 uv run pytest -m "not integration" -q

# Skip all integration tests (coarse monorepo-wide override)
SKIP_INTEGRATION_TESTS=1 uv run pytest -m "not integration" -q
```

Actual coverage: **89%** (above threshold, 2026-03-03 sweep — see
[workplan §7](../../../docs/test-upgrade-workplan.md)).

Skip variables:

| Variable | Effect |
|----------|--------|
| `SKIP_INTEGRATION_TESTS=1` | Skips all integration tests (coarse monorepo-wide override) |
| `SKIP_CHROMA_TESTS=1` | Skips ChromaDB-dependent tests (`tests/test_chroma.py`) |
| `SKIP_QDRANT_TESTS=1` | Skips Qdrant-dependent tests (`tests/test_qdrant.py`) |

Note: `test_chroma.py` currently lacks its own `SKIP_CHROMA_TESTS` guard — the coarse
`SKIP_INTEGRATION_TESTS` var is the safe bypass until W9 from the workplan is resolved.

Test files:
- `tests/test_chroma.py` — ChromaDB adapter integration tests
- `tests/test_qdrant.py` — Qdrant adapter integration tests (has `SKIP_QDRANT_TESTS` guard)
- `tests/conftest.py` — shared fixtures

---

## Development

```bash
uv run ruff check .
uv run mypy src/
uv run pytest
```

---

## References

- [Collection registry](../README.md) — canonical collection names and module ownership
- [workplan §P22](../../../docs/test-upgrade-workplan.md) — embedding.py test coverage task
- [workplan §W9](../../../docs/test-upgrade-workplan.md) — SKIP_CHROMA_TESTS guard gap
