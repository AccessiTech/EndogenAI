"""EndogenAI vector store adapter package.

Public surface:
    VectorStoreAdapter   — abstract base class (interface contract)
    ChromaAdapter        — ChromaDB implementation (default)
    QdrantAdapter        — Qdrant implementation (production)
    EmbeddingClient      — Ollama / OpenAI embeddings
    models               — Pydantic request/response models

Usage::

    from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig

    adapter = ChromaAdapter(
        config=ChromaConfig(mode="http", host="localhost", port=8000),
        embedding_config=EmbeddingConfig(provider="ollama", model="nomic-embed-text"),
    )
    await adapter.create_collection(CreateCollectionRequest(collection_name="brain.knowledge"))
"""

from endogenai_vector_store.chroma import ChromaAdapter
from endogenai_vector_store.embedding import EmbeddingClient
from endogenai_vector_store.interface import VectorStoreAdapter
from endogenai_vector_store.models import (
    ChromaConfig,
    CollectionInfo,
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteRequest,
    DeleteResponse,
    DropCollectionRequest,
    DropCollectionResponse,
    EmbeddingConfig,
    ListCollectionsResponse,
    MemoryItem,
    QueryRequest,
    QueryResponse,
    QueryResult,
    UpsertRequest,
    UpsertResponse,
)

__all__ = [
    # Adapters
    "VectorStoreAdapter",
    "ChromaAdapter",
    "EmbeddingClient",
    # Config models
    "EmbeddingConfig",
    "ChromaConfig",
    # Request/response models
    "UpsertRequest",
    "UpsertResponse",
    "QueryRequest",
    "QueryResponse",
    "QueryResult",
    "DeleteRequest",
    "DeleteResponse",
    "CreateCollectionRequest",
    "CreateCollectionResponse",
    "DropCollectionRequest",
    "DropCollectionResponse",
    "ListCollectionsResponse",
    "CollectionInfo",
    # Domain types
    "MemoryItem",
]

__version__ = "0.1.0"
