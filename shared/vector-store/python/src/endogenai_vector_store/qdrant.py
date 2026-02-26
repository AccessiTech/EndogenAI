"""Qdrant vector store adapter — production backend.

The Qdrant adapter targets Qdrant ≥ 1.9 and uses the qdrant-client Python SDK.
It is an optional dependency — install with ``pip install endogenai-vector-store[qdrant]``.

Qdrant is recommended for production deployments where you need:
- Payload-indexed filtering (fast WHERE clauses on metadata fields)
- On-disk vector storage for large collections
- gRPC throughput at scale

Add Qdrant to your docker-compose.yml to test locally:

    qdrant:
      image: qdrant/qdrant:latest
      ports:
        - "6333:6333"
        - "6334:6334"
      volumes:
        - qdrant_data:/qdrant/storage

Usage::

    from endogenai_vector_store.qdrant import QdrantAdapter
    from endogenai_vector_store.models import QdrantConfig, EmbeddingConfig

    async with QdrantAdapter(
        config=QdrantConfig(host="localhost", port=6333),
        embedding_config=EmbeddingConfig(),
    ) as adapter:
        await adapter.create_collection(CreateCollectionRequest(collection_name="brain.knowledge"))
"""

from __future__ import annotations

from typing import Any

import structlog

from endogenai_vector_store.embedding import EmbeddingClient
from endogenai_vector_store.interface import AdapterError, VectorStoreAdapter
from endogenai_vector_store.models import (
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
    MemoryType,
    QueryRequest,
    QueryResponse,
    QueryResult,
    QdrantConfig,
    UpsertRequest,
    UpsertResponse,
)

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_VECTOR_NAME = "content"  # Named vector key used in Qdrant collections


def _item_to_payload(item: MemoryItem) -> dict[str, Any]:
    """Serialise a MemoryItem to a Qdrant payload dict (str/int/float/bool/list/dict allowed)."""
    payload = item.model_dump(exclude={"embedding", "id"})
    # Remove None values to keep payloads lean
    return {k: v for k, v in payload.items() if v is not None}


def _payload_to_item(point_id: str, payload: dict[str, Any], vector: list[float]) -> MemoryItem:
    """Reconstruct a MemoryItem from a Qdrant point payload."""
    return MemoryItem(
        id=point_id,
        collection_name=payload.get("collection_name", "brain.unknown"),
        content=payload.get("content", ""),
        type=MemoryType(payload.get("type", "working")),
        source_module=payload.get("source_module", ""),
        importance_score=float(payload.get("importance_score", 0.5)),
        created_at=payload.get("created_at", ""),
        updated_at=payload.get("updated_at"),
        expires_at=payload.get("expires_at"),
        access_count=int(payload.get("access_count", 0)),
        last_accessed_at=payload.get("last_accessed_at"),
        metadata=payload.get("metadata", {}),
        tags=payload.get("tags", []),
        embedding=vector,
        embedding_model=payload.get("embedding_model"),
        parent_id=payload.get("parent_id"),
        related_ids=payload.get("related_ids", []),
    )


class QdrantAdapter(VectorStoreAdapter):
    """Qdrant implementation of VectorStoreAdapter.

    Requires ``qdrant-client`` — install with ``pip install endogenai-vector-store[qdrant]``.
    """

    def __init__(
        self,
        config: QdrantConfig | None = None,
        embedding_config: EmbeddingConfig | None = None,
    ) -> None:
        try:
            import qdrant_client  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required for QdrantAdapter. "
                "Install with: pip install endogenai-vector-store[qdrant]"
            ) from exc

        self._config = config or QdrantConfig(host="localhost")
        self._embedding_config = embedding_config or EmbeddingConfig()
        self._client: Any = None  # qdrant_client.AsyncQdrantClient
        self._embedder = EmbeddingClient(self._embedding_config)
        self._vector_size: int | None = self._embedding_config.dimensions

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        from qdrant_client import AsyncQdrantClient

        await self._embedder.connect()
        cfg = self._config

        self._client = AsyncQdrantClient(
            host=cfg.host,
            port=cfg.port,
            grpc_port=cfg.grpc_port,
            prefer_grpc=cfg.use_grpc,
            https=cfg.https,
            api_key=cfg.api_key,
            timeout=cfg.timeout / 1000,
        )

        logger.info(
            "qdrant.connected",
            host=cfg.host,
            port=cfg.port,
            use_grpc=cfg.use_grpc,
        )

    async def close(self) -> None:
        await self._embedder.close()
        if self._client is not None:
            await self._client.close()
        logger.info("qdrant.closed")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_connected(self) -> Any:
        if self._client is None:
            raise AdapterError(
                "QdrantAdapter is not connected — call connect() or use as async context manager.",
                backend="qdrant",
                retryable=False,
            )
        return self._client

    async def _get_vector_size(self) -> int:
        """Determine embedding dimensionality via a probe embed if not configured."""
        if self._vector_size is None:
            probe = await self._embedder.embed_one("probe")
            self._vector_size = len(probe)
        return self._vector_size

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    async def upsert(self, request: UpsertRequest) -> UpsertResponse:
        from qdrant_client.models import PointStruct

        client = self._assert_connected()
        texts = [item.content for item in request.items]
        vectors = await self._embedder.embed(texts)
        model_name = self._embedding_config.model

        points: list[PointStruct] = []
        for item, vector in zip(request.items, vectors, strict=True):
            item.embedding = vector
            item.embedding_model = model_name
            points.append(
                PointStruct(
                    id=item.id,
                    vector={_VECTOR_NAME: vector},
                    payload=_item_to_payload(item),
                )
            )

        try:
            await client.upsert(
                collection_name=request.collection_name,
                points=points,
                wait=True,
            )
        except Exception as exc:
            raise AdapterError(
                f"Qdrant upsert failed: {exc}", backend="qdrant", retryable=True
            ) from exc

        ids = [item.id for item in request.items]
        logger.info("qdrant.upsert", collection=request.collection_name, count=len(ids))
        return UpsertResponse(upserted_ids=ids)

    async def query(self, request: QueryRequest) -> QueryResponse:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = self._assert_connected()
        query_vector = await self._embedder.embed_one(request.query_text)

        qdrant_filter = None
        if request.where:
            must_conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in request.where.items()
            ]
            qdrant_filter = Filter(must=must_conditions)

        try:
            hits = await client.search(
                collection_name=request.collection_name,
                query_vector=(_VECTOR_NAME, query_vector),
                limit=request.n_results,
                query_filter=qdrant_filter,
                with_payload=True,
                with_vectors=True,
            )
        except Exception as exc:
            raise AdapterError(
                f"Qdrant search failed: {exc}", backend="qdrant", retryable=True
            ) from exc

        results = [
            QueryResult(
                item=_payload_to_item(
                    str(hit.id),
                    hit.payload or {},
                    hit.vector.get(_VECTOR_NAME, []) if isinstance(hit.vector, dict) else [],  # type: ignore[union-attr]
                ),
                score=hit.score,
            )
            for hit in hits
        ]

        logger.debug(
            "qdrant.query",
            collection=request.collection_name,
            query=request.query_text[:80],
            n_results=len(results),
        )
        return QueryResponse(results=results)

    async def delete(self, request: DeleteRequest) -> DeleteResponse:
        from qdrant_client.models import PointIdsList

        client = self._assert_connected()
        try:
            await client.delete(
                collection_name=request.collection_name,
                points_selector=PointIdsList(points=request.ids),
                wait=True,
            )
        except Exception as exc:
            raise AdapterError(
                f"Qdrant delete failed: {exc}", backend="qdrant", retryable=True
            ) from exc

        logger.info(
            "qdrant.delete", collection=request.collection_name, count=len(request.ids)
        )
        return DeleteResponse(deleted_ids=request.ids)

    async def create_collection(
        self, request: CreateCollectionRequest
    ) -> CreateCollectionResponse:
        from qdrant_client.models import Distance, VectorParams

        client = self._assert_connected()

        try:
            existing = await client.get_collections()
            existing_names = {c.name for c in existing.collections}
        except Exception as exc:
            raise AdapterError(
                f"Qdrant get_collections failed: {exc}", backend="qdrant", retryable=True
            ) from exc

        if request.collection_name in existing_names:
            return CreateCollectionResponse(
                collection_name=request.collection_name, created=False
            )

        vector_size = await self._get_vector_size()
        try:
            await client.create_collection(
                collection_name=request.collection_name,
                vectors_config={
                    _VECTOR_NAME: VectorParams(size=vector_size, distance=Distance.COSINE)
                },
            )
        except Exception as exc:
            raise AdapterError(
                f"Qdrant create_collection failed: {exc}", backend="qdrant", retryable=False
            ) from exc

        logger.info("qdrant.create_collection", collection=request.collection_name)
        return CreateCollectionResponse(collection_name=request.collection_name, created=True)

    async def drop_collection(self, request: DropCollectionRequest) -> DropCollectionResponse:
        client = self._assert_connected()

        try:
            existing = await client.get_collections()
            existing_names = {c.name for c in existing.collections}
        except Exception as exc:
            raise AdapterError(
                f"Qdrant get_collections failed: {exc}", backend="qdrant", retryable=True
            ) from exc

        if request.collection_name not in existing_names:
            return DropCollectionResponse(collection_name=request.collection_name, dropped=False)

        try:
            await client.delete_collection(request.collection_name)
        except Exception as exc:
            raise AdapterError(
                f"Qdrant delete_collection failed: {exc}", backend="qdrant", retryable=False
            ) from exc

        logger.info("qdrant.drop_collection", collection=request.collection_name)
        return DropCollectionResponse(collection_name=request.collection_name, dropped=True)

    async def list_collections(self) -> ListCollectionsResponse:
        client = self._assert_connected()

        try:
            raw = await client.get_collections()
        except Exception as exc:
            raise AdapterError(
                f"Qdrant get_collections failed: {exc}", backend="qdrant", retryable=True
            ) from exc

        collections = [CollectionInfo(name=c.name) for c in raw.collections]
        return ListCollectionsResponse(collections=collections)
