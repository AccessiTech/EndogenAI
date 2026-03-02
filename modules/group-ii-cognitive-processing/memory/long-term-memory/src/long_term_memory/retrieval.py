"""Hybrid retrieval with re-ranking for long-term memory.

Combines semantic vector search with optional exact-match SQL lookup,
then re-ranks results by importanceScore.
"""

from __future__ import annotations

import structlog
from endogenai_vector_store.models import MemoryItem

from long_term_memory.models import SemanticFact
from long_term_memory.sql_store import SQLFactStore
from long_term_memory.vector_store import LTMVectorStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class HybridRetrieval:
    """Performs semantic + optional structured retrieval with re-ranking."""

    def __init__(
        self,
        vector_store: LTMVectorStore,
        sql_store: SQLFactStore,
    ) -> None:
        self._vector_store = vector_store
        self._sql_store = sql_store

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        filters: dict[str, object] | None = None,
    ) -> list[MemoryItem]:
        """Semantic search with importance-based re-ranking.

        Args:
            query_text: Natural-language query.
            top_k: Maximum results to return.
            filters: Optional metadata equality filters.

        Returns:
            List of MemoryItem, sorted by importanceScore descending.
        """
        items = await self._vector_store.query(
            query_text=query_text,
            top_k=top_k * 2,  # over-fetch for re-ranking
            where=filters,
        )
        # Re-rank by importanceScore (descending)
        items.sort(key=lambda it: it.importance_score, reverse=True)
        result = items[:top_k]
        logger.debug(
            "ltm_hybrid_retrieval",
            query=query_text[:60],
            fetched=len(items),
            returned=len(result),
        )
        return result

    async def query_facts(self, entity_id: str) -> list[SemanticFact]:
        """Exact-match structured lookup for a single entity."""
        return await self._sql_store.query_facts(entity_id)
