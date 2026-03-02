"""Composite semantic + temporal retrieval for episodic memory."""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, QueryRequest

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.episodic-memory"


class EpisodicRetrieval:
    """Supports semantic and temporal composite queries over brain.episodic-memory."""

    def __init__(self, adapter: ChromaAdapter) -> None:
        self._adapter = adapter

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        session_id: str | None = None,
        time_window_start: str | None = None,
        time_window_end: str | None = None,
    ) -> list[MemoryItem]:
        """Semantic search with optional session and time-window filters.

        Results are re-ranked by ``importance_score × |affective_valence|``.

        Args:
            query: Natural-language query string.
            top_k: Maximum results to return.
            session_id: Restrict search to a specific session.
            time_window_start: ISO-8601 lower bound for ``created_at``.
            time_window_end: ISO-8601 upper bound for ``created_at``.

        Returns:
            List of MemoryItem ordered by composite relevance score.
        """
        where: dict[str, object] | None = None
        if session_id:
            where = {"session_id": session_id}

        request = QueryRequest(
            collection_name=COLLECTION,
            query_text=query,
            n_results=top_k * 2,
            where=where,
        )
        response = await self._adapter.query(request)
        items = [r.item for r in response.results]

        # Apply time-window filter in memory (ChromaDB doesn't support range filters natively)
        if time_window_start or time_window_end:
            items = [
                it
                for it in items
                if self._in_time_window(it.created_at, time_window_start, time_window_end)
            ]

        # Re-rank by importance × |affective_valence|
        items.sort(
            key=lambda it: it.importance_score
            * (abs(float(it.metadata.get("affective_valence", 0.0))) + 0.01),
            reverse=True,
        )
        result = items[:top_k]
        logger.debug(
            "episodic_semantic_search",
            query=query[:60],
            returned=len(result),
        )
        return result

    @staticmethod
    def _in_time_window(
        timestamp: str,
        start: str | None,
        end: str | None,
    ) -> bool:
        """Return True if timestamp falls within [start, end]."""
        if start and timestamp < start:
            return False
        return not (end and timestamp > end)
