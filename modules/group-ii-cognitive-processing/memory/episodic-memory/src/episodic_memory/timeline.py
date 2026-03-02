"""Session-ordered timeline replay for episodic memory."""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, QueryRequest

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.episodic-memory"
MAX_TIMELINE_ITEMS = 100  # QueryRequest.n_results cap; use pagination for larger sessions


class Timeline:
    """Retrieves all events for a session ordered chronologically."""

    def __init__(self, adapter: ChromaAdapter) -> None:
        self._adapter = adapter

    async def get_session_timeline(self, session_id: str) -> list[MemoryItem]:
        """Return all episodic events for a session in ascending ``created_at`` order.

        Args:
            session_id: The session to retrieve.

        Returns:
            List of MemoryItem ordered by created_at (earliest first).
        """
        request = QueryRequest(
            collection_name=COLLECTION,
            query_text=session_id,  # proxy query to pull session items
            n_results=MAX_TIMELINE_ITEMS,
            where={"session_id": session_id},
        )
        response = await self._adapter.query(request)
        items = [r.item for r in response.results]
        # Sort chronologically
        items.sort(key=lambda it: it.created_at)
        logger.debug(
            "episodic_timeline_retrieved",
            session_id=session_id,
            event_count=len(items),
        )
        return items
