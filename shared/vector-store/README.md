---
id: shared-vector-store
version: 0.1.0
status: draft
last-reviewed: "2025-07-14"
---

# Shared Vector Store Adapter

Unified vector store abstraction for all EndogenAI modules. Provides a common interface to ChromaDB (default), Qdrant
(production), and pgvector — with Ollama-powered embeddings by default.

## Directory layout

```
shared/vector-store/
├── adapter.interface.json          # Language-agnostic interface contract
├── collection-registry.json        # All 15 brain.* collections
├── embedding.config.schema.json    # Embedding provider config schema
├── chroma.config.schema.json       # ChromaDB backend config schema
├── qdrant.config.schema.json       # Qdrant backend config schema
├── pgvector.config.schema.json     # pgvector backend config schema
├── python/                         # Python adapter (uv package)
│   ├── pyproject.toml
│   ├── src/endogenai_vector_store/
│   │   ├── __init__.py
│   │   ├── interface.py            # VectorStoreAdapter ABC
│   │   ├── models.py               # Pydantic models
│   │   ├── embedding.py            # EmbeddingClient (Ollama / OpenAI-compat)
│   │   ├── chroma.py               # ChromaDB adapter
│   │   └── qdrant.py               # Qdrant adapter
│   └── tests/
│       ├── conftest.py             # Testcontainers fixtures + MockEmbeddingClient
│       ├── test_chroma.py          # ChromaDB integration tests
│       └── test_qdrant.py          # Qdrant integration tests
└── typescript/                     # TypeScript adapter (npm package)
    ├── package.json
    ├── tsconfig.json
    ├── src/
    │   ├── index.ts                # Barrel export
    │   ├── interface.ts            # VectorStoreAdapter interface + AdapterError
    │   ├── models.ts               # TypeScript types / interfaces
    │   └── adapters/
    │       └── chroma.ts           # ChromaDB adapter
    └── tests/
        └── chroma.test.ts          # Vitest + Testcontainers integration tests
```

## Interface contract

All adapters expose exactly six operations defined in `adapter.interface.json`:

| Operation           | Description                                                  |
| ------------------- | ------------------------------------------------------------ |
| `upsert`            | Insert or update `MemoryItem` records (generates embeddings) |
| `query`             | Semantic similarity search by natural-language text          |
| `delete`            | Delete records by ID                                         |
| `create-collection` | Create a collection (idempotent)                             |
| `drop-collection`   | Permanently delete a collection                              |
| `list-collections`  | List all collections in the backend                          |

Adapters own the embedding step. Callers **never** supply raw vectors — pass plain text in `MemoryItem.content` and
`QueryRequest.queryText`. The adapter calls the configured embedding provider and populates `MemoryItem.embedding` after
upsert.

## Collection naming

All collections must match `^brain\.[a-z][a-z0-9-]*$`. The authoritative list of 15 collections is in
`collection-registry.json`:

| Collection                  | Layer       | Memory type |
| --------------------------- | ----------- | ----------- |
| `brain.sensory-input`       | sensory     | working     |
| `brain.attention-filtering` | subcortical | working     |
| `brain.perception`          | sensory     | short-term  |
| `brain.working-memory`      | prefrontal  | working     |
| `brain.short-term-memory`   | memory      | short-term  |
| `brain.long-term-memory`    | memory      | long-term   |
| `brain.episodic-memory`     | memory      | episodic    |
| `brain.affective`           | limbic      | short-term  |
| `brain.reasoning`           | prefrontal  | working     |
| `brain.executive-agent`     | prefrontal  | working     |
| `brain.agent-runtime`       | motor       | short-term  |
| `brain.motor-output`        | motor       | episodic    |
| `brain.learning-adaptation` | subcortical | long-term   |
| `brain.metacognition`       | prefrontal  | long-term   |
| `brain.knowledge`           | memory      | long-term   |

## Backend selection

| Backend  | When to use                              | docker-compose | Status      |
| -------- | ---------------------------------------- | -------------- | ----------- |
| ChromaDB | Local dev, all modules (default)         | ✅ port 8000   | Implemented |
| Qdrant   | Production, large collections, filtering | Add manually   | Implemented |
| pgvector | Postgres-native deployments              | Add manually   | Schema only |

ChromaDB is pre-configured in `docker-compose.yml` with `IS_PERSISTENT=TRUE` on port 8000.

## Embedding model

The default embedding model is **`nomic-embed-text`** served by Ollama (port 11434, also in `docker-compose.yml`).
Change the model via `EmbeddingConfig` or the `ENDOGEN_EMBEDDING_MODEL` env var.

Recommended models:

| Model                    | Provider | Dimensions | Notes                                     |
| ------------------------ | -------- | ---------- | ----------------------------------------- |
| `nomic-embed-text`       | Ollama   | 768        | Default. Fast, good quality, local.       |
| `mxbai-embed-large`      | Ollama   | 1024       | Higher quality, slower.                   |
| `text-embedding-3-small` | OpenAI   | 1536       | Cloud. Needs `ENDOGEN_EMBEDDING_API_KEY`. |

## Python usage

```bash
cd shared/vector-store/python
uv sync
```

```python
from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig
from endogenai_vector_store.models import MemoryItem, MemoryType, UpsertRequest, QueryRequest
import datetime, uuid

async def main():
    async with ChromaAdapter(
        config=ChromaConfig(mode="http", host="localhost", port=8000),
        embedding_config=EmbeddingConfig(provider="ollama", model="nomic-embed-text"),
    ) as adapter:
        await adapter.ensure_collection("brain.knowledge")

        item = MemoryItem(
            id=str(uuid.uuid4()),
            collection_name="brain.knowledge",
            content="The prefrontal cortex governs executive function.",
            type=MemoryType.LONG_TERM,
            source_module="knowledge",
            importance_score=0.9,
            created_at=datetime.datetime.utcnow().isoformat(),
        )
        await adapter.upsert(UpsertRequest(collection_name="brain.knowledge", items=[item]))

        results = await adapter.query(QueryRequest(
            collection_name="brain.knowledge",
            query_text="executive function brain region",
            n_results=5,
        ))
        for r in results.results:
            print(r.score, r.item.content)
```

### Running Python tests

```bash
cd shared/vector-store/python
uv sync
uv run pytest tests/ -v
# Skip Qdrant tests (no Docker Qdrant):
SKIP_QDRANT_TESTS=1 uv run pytest tests/test_chroma.py -v
```

## TypeScript usage

```bash
cd shared/vector-store/typescript
pnpm install
pnpm build
```

```ts
import { ChromaAdapter, ensureCollection } from "@accessitech/vector-store";

const adapter = new ChromaAdapter({ host: "localhost", port: 8000 });
await adapter.connect();
await ensureCollection(adapter, "brain.knowledge");

const { upsertedIds } = await adapter.upsert({
  collectionName: "brain.knowledge",
  items: [
    {
      id: crypto.randomUUID(),
      collectionName: "brain.knowledge",
      content: "The hippocampus consolidates short-term to long-term memory.",
      type: "long-term",
      sourceModule: "knowledge",
      importanceScore: 0.9,
      createdAt: new Date().toISOString(),
      accessCount: 0,
      metadata: {},
      tags: [],
      relatedIds: [],
    },
  ],
});

const { results } = await adapter.query({
  collectionName: "brain.knowledge",
  queryText: "memory consolidation",
  nResults: 5,
});
results.forEach((r) => console.log(r.score, r.item.content));
```

### Running TypeScript tests

```bash
cd shared/vector-store/typescript
pnpm install
pnpm test
```

## Environment variables

| Variable                     | Default                  | Description                          |
| ---------------------------- | ------------------------ | ------------------------------------ |
| `OLLAMA_HOST`                | `http://localhost:11434` | Overrides `EmbeddingConfig.baseUrl`  |
| `ENDOGEN_EMBEDDING_MODEL`    | `nomic-embed-text`       | Overrides `EmbeddingConfig.model`    |
| `ENDOGEN_EMBEDDING_API_KEY`  | —                        | API key for non-Ollama providers     |
| `CHROMA_HOST`                | `localhost`              | Overrides `ChromaConfig.host`        |
| `CHROMA_PORT`                | `8000`                   | Overrides `ChromaConfig.port`        |
| `CHROMA_AUTH_TOKEN`          | —                        | Bearer token for ChromaDB Cloud      |
| `QDRANT_HOST`                | `localhost`              | Overrides `QdrantConfig.host`        |
| `QDRANT_PORT`                | `6333`                   | Overrides `QdrantConfig.port`        |
| `QDRANT_API_KEY`             | —                        | API key for Qdrant Cloud             |
| `PGVECTOR_CONNECTION_STRING` | —                        | PostgreSQL connection string         |
| `SKIP_QDRANT_TESTS`          | —                        | Set to skip Qdrant integration tests |
