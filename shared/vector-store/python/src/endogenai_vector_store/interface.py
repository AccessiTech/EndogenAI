"""Abstract base class — VectorStoreAdapter.

All backend implementations (Chroma, Qdrant, pgvector) MUST subclass this
and implement every abstract method.  The method signatures exactly mirror
the JSON interface contract in shared/vector-store/adapter.interface.json.

Usage::

    class MyAdapter(VectorStoreAdapter):
        async def upsert(self, request: UpsertRequest) -> UpsertResponse: ...
        ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from endogenai_vector_store.models import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteRequest,
    DeleteResponse,
    DropCollectionRequest,
    DropCollectionResponse,
    ListCollectionsResponse,
    QueryRequest,
    QueryResponse,
    UpsertRequest,
    UpsertResponse,
)


class VectorStoreAdapter(ABC):
    """Abstract interface for EndogenAI vector store adapters.

    Implementations must be async-native. All methods are coroutines.
    Adapters own the embedding step — callers never supply raw vectors.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Optional: establish a connection / warm up the client.

        Called once at startup. Default is a no-op; override if your backend
        needs an explicit connection step (e.g. connection pool warm-up).
        """

    async def close(self) -> None:
        """Optional: release resources held by this adapter.

        Called at shutdown. Default is a no-op; override if your backend
        holds persistent connections (e.g. gRPC channels).
        """

    # ------------------------------------------------------------------
    # Core operations (must implement)
    # ------------------------------------------------------------------

    @abstractmethod
    async def upsert(self, request: UpsertRequest) -> UpsertResponse:
        """Insert or update MemoryItems. Generates embeddings internally.

        Items with existing IDs are overwritten. The returned `upserted_ids`
        list length MAY be smaller than the input if partial failures occur —
        implementations should raise AdapterError for total failures.
        """

    @abstractmethod
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Semantic similarity search. Embeds ``query_text`` internally."""

    @abstractmethod
    async def delete(self, request: DeleteRequest) -> DeleteResponse:
        """Delete MemoryItems by ID. Missing IDs are silently ignored."""

    @abstractmethod
    async def create_collection(
        self, request: CreateCollectionRequest
    ) -> CreateCollectionResponse:
        """Create a collection. Idempotent — no error if already exists."""

    @abstractmethod
    async def drop_collection(self, request: DropCollectionRequest) -> DropCollectionResponse:
        """Permanently delete a collection and all its records."""

    @abstractmethod
    async def list_collections(self) -> ListCollectionsResponse:
        """Return all collections present in the backend."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def ensure_collection(self, collection_name: str) -> bool:
        """Create the collection if it does not exist.

        Returns True if created, False if it already existed.
        Convenience wrapper over create_collection.
        """
        resp = await self.create_collection(
            CreateCollectionRequest(collection_name=collection_name)
        )
        return resp.created

    async def __aenter__(self) -> "VectorStoreAdapter":
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()


class AdapterError(Exception):
    """Raised by adapter implementations for unrecoverable backend errors."""

    def __init__(self, message: str, *, backend: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.backend = backend
        self.retryable = retryable
