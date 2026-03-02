"""ChromaDB/Qdrant vector store for long-term memory via endogenai_vector_store adapter.

Enforces importanceScore >= 0.5 gate before any write.
"""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import (
    DeleteRequest,
    MemoryItem,
    QueryRequest,
    UpsertRequest,
    UpsertResponse,
)

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.long-term-memory"
IMPORTANCE_GATE = 0.5


class LTMVectorStore:
    """Vector store adapter for brain.long-term-memory.

    Wraps ChromaAdapter to enforce the importance gate (>= 0.5) on all writes
    and to provide LTM-specific query helpers.
    """

    def __init__(self, adapter: ChromaAdapter) -> None:
        self._adapter = adapter

    async def write(self, item: MemoryItem) -> str:
        """Write a MemoryItem to brain.long-term-memory.

        Raises:
            ValueError: If importanceScore < 0.5.

        Returns:
            The upserted item_id.
        """
        if item.importance_score < IMPORTANCE_GATE:
            raise ValueError(
                f"LTM write rejected: importanceScore {item.importance_score:.3f} < {IMPORTANCE_GATE}"
            )
        upsert_req = UpsertRequest(collection_name=COLLECTION, items=[item])
        resp: UpsertResponse = await self._adapter.upsert(upsert_req)
        logger.info("ltm_item_written", item_id=resp.upserted_ids[0])
        return resp.upserted_ids[0]

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        where: dict[str, object] | None = None,
    ) -> list[MemoryItem]:
        """Semantic search over brain.long-term-memory.

        Args:
            query_text: Natural-language query.
            top_k: Maximum number of results.
            where: Optional metadata filter dict.

        Returns:
            List of MemoryItem sorted by cosine similarity (highest first).
        """
        request = QueryRequest(
            collection_name=COLLECTION,
            query_text=query_text,
            n_results=top_k,
            where=where,
        )
        response = await self._adapter.query(request)
        return [result.item for result in response.results]

    async def update(self, item: MemoryItem) -> str:
        """Update an existing item (reconsolidation — metadata + optional re-embed).

        Args:
            item: The updated MemoryItem. If content has changed, the adapter
                  will re-embed it on next query.

        Returns:
            The item_id.
        """
        upsert_req = UpsertRequest(collection_name=COLLECTION, items=[item])
        resp = await self._adapter.upsert(upsert_req)
        return resp.upserted_ids[0]

    async def delete(self, item_ids: list[str]) -> None:
        """Delete items by ID from brain.long-term-memory."""
        if not item_ids:
            return
        delete_req = DeleteRequest(collection_name=COLLECTION, ids=item_ids)
        await self._adapter.delete(delete_req)
