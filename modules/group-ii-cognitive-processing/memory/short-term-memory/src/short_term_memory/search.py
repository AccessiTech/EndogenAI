"""Semantic search over the current session in brain.short-term-memory."""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, QueryRequest

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.short-term-memory"
DEFAULT_TOP_K = 10


class SemanticSearch:
    """Semantic search scoped to a single session in brain.short-term-memory."""

    def __init__(self, adapter: ChromaAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        session_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[MemoryItem]:
        """Return the top-k most semantically similar items for a session.

        Args:
            session_id: Restrict results to this session.
            query: Natural-language query string.
            top_k: Maximum number of results to return.

        Returns:
            List of MemoryItem sorted by cosine similarity (highest first).
        """
        request = QueryRequest(
            collection_name=COLLECTION,
            query_text=query,
            n_results=top_k,
            where={"session_id": session_id},
        )
        response = await self._adapter.query(request)
        items = [result.item for result in response.results]
        logger.debug(
            "stm_semantic_search",
            session_id=session_id,
            query=query[:60],
            returned=len(items),
        )
        return items
