"""Pydantic models for the EndogenAI vector store adapter.

All models are derived from the JSON schemas in shared/vector-store/*.schema.json
and shared/types/memory-item.schema.json.

Key design decisions:
- `collection_name` fields enforce ^brain\\.[a-z][a-z0-9-]*$ pattern (mirrors memory-item.schema.json).
- `MemoryItem.embedding` is populated by the adapter — callers must NOT set it.
- All models are frozen dataclasses under the hood (model_config = ConfigDict(frozen=True))
  except where mutability is needed (e.g. UpsertRequest.items for batch encoding).
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLLECTION_NAME_RE = re.compile(r"^brain\.[a-z][a-z0-9-]*$")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EmbeddingProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class ChromaMode(str, Enum):
    HTTP = "http"
    EMBEDDED = "embedded"


class MemoryType(str, Enum):
    WORKING = "working"
    SHORT_TERM = "short-term"
    LONG_TERM = "long-term"
    EPISODIC = "episodic"


class Layer(str, Enum):
    SENSORY = "sensory"
    SUBCORTICAL = "subcortical"
    LIMBIC = "limbic"
    MEMORY = "memory"
    PREFRONTAL = "prefrontal"
    MOTOR = "motor"
    CEREBELLUM = "cerebellum"


# ---------------------------------------------------------------------------
# Embedding config
# ---------------------------------------------------------------------------


class EmbeddingFallback(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProvider
    model: str
    base_url: str | None = None


class EmbeddingConfig(BaseModel):
    """Configuration for the embedding provider used by vector store adapters."""

    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProvider = EmbeddingProvider.OLLAMA
    model: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"
    dimensions: int | None = None
    batch_size: int = Field(default=32, ge=1, le=512)
    timeout_ms: int = Field(default=30_000, ge=1_000)
    fallback: EmbeddingFallback | None = None


# ---------------------------------------------------------------------------
# Backend configs
# ---------------------------------------------------------------------------


class ChromaConfig(BaseModel):
    """Configuration for the ChromaDB adapter."""

    model_config = ConfigDict(frozen=True)

    mode: ChromaMode = ChromaMode.HTTP
    host: str = "localhost"
    port: int = Field(default=8000, ge=1, le=65535)
    ssl: bool = False
    headers: dict[str, str] = Field(default_factory=dict)
    persist_directory: str | None = None
    tenant: str = "default_tenant"
    database: str = "default_database"


class QdrantConfig(BaseModel):
    """Configuration for the Qdrant adapter."""

    model_config = ConfigDict(frozen=True)

    host: str = "localhost"
    port: int = Field(default=6333, ge=1, le=65535)
    grpc_port: int = Field(default=6334, ge=1, le=65535)
    use_grpc: bool = True
    https: bool = False
    api_key: str | None = None
    timeout: int = Field(default=10_000, ge=1_000)


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


class MemoryItem(BaseModel):
    """EndogenAI memory record stored in a vector collection.

    The ``embedding`` field is populated by the adapter after calling the
    embedding provider.  Callers should leave it as ``None``.
    """

    model_config = ConfigDict(frozen=False)  # mutable so adapter can attach embedding

    id: str = Field(..., description="UUID v7 string identifying this record.")
    collection_name: str = Field(..., description="Target collection (brain.<module-name>).")
    content: str = Field(..., description="Plain-text content to embed.")
    type: MemoryType
    source_module: str = Field(..., description="moduleId of the writing module.")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: str = Field(..., description="ISO-8601 UTC timestamp.")
    updated_at: str | None = None
    expires_at: str | None = None
    access_count: int = Field(default=0, ge=0)
    last_accessed_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    embedding: list[float] | None = Field(
        default=None,
        description="Set by adapter after embedding. Do not set manually.",
    )
    embedding_model: str | None = None
    parent_id: str | None = None
    related_ids: list[str] = Field(default_factory=list)

    @field_validator("collection_name")
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        if not COLLECTION_NAME_RE.match(v):
            raise ValueError(
                f"collection_name must match ^brain\\.[a-z][a-z0-9-]*$, got: {v!r}"
            )
        return v


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


class UpsertRequest(BaseModel):
    model_config = ConfigDict(frozen=False)

    collection_name: str = Field(..., pattern=r"^brain\.[a-z][a-z0-9-]*$")
    items: list[MemoryItem] = Field(..., min_length=1)


class UpsertResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    upserted_ids: list[str]


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    collection_name: str = Field(..., pattern=r"^brain\.[a-z][a-z0-9-]*$")
    query_text: str = Field(..., min_length=1)
    n_results: int = Field(default=10, ge=1, le=100)
    where: dict[str, Any] | None = None
    """Optional metadata equality filter applied before vector search."""
    where_document: str | None = None
    """Optional full-text filter applied to content before vector search."""


class QueryResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    item: MemoryItem
    score: float = Field(..., description="Cosine similarity in [0, 1]. Higher = more similar.")


class QueryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    results: list[QueryResult]


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class DeleteRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    collection_name: str = Field(..., pattern=r"^brain\.[a-z][a-z0-9-]*$")
    ids: list[str] = Field(..., min_length=1)


class DeleteResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    deleted_ids: list[str]


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------


class CreateCollectionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    collection_name: str = Field(..., pattern=r"^brain\.[a-z][a-z0-9-]*$")
    metadata: dict[str, str] = Field(default_factory=dict)


class CreateCollectionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    collection_name: str
    created: bool
    """True if newly created; False if it already existed (idempotent)."""


class DropCollectionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    collection_name: str = Field(..., pattern=r"^brain\.[a-z][a-z0-9-]*$")


class DropCollectionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    collection_name: str
    dropped: bool


class CollectionInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    count: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ListCollectionsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    collections: list[CollectionInfo]
