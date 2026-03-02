"""Novelty detection for short-term memory — Dentate Gyrus pattern separation analogue.

Before every write, queries brain.short-term-memory for near-duplicates.
If cosine similarity of the top-1 result exceeds NOVELTY_THRESHOLD (default 0.9),
the new item is considered a duplicate and the existing item's importanceScore
is incremented instead of creating a new record.
"""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, QueryRequest

logger: structlog.BoundLogger = structlog.get_logger(__name__)

NOVELTY_THRESHOLD = 0.9
COLLECTION = "brain.short-term-memory"


class NoveltyChecker:
    """Checks whether a new MemoryItem is novel or a near-duplicate of an existing one.

    Queries brain.short-term-memory for the nearest neighbour of the candidate
    content.  If cosine similarity > threshold, returns the existing item;
    otherwise returns None (the candidate is novel and should be written fresh).
    """

    def __init__(
        self,
        adapter: ChromaAdapter,
        threshold: float = NOVELTY_THRESHOLD,
    ) -> None:
        self._adapter = adapter
        self._threshold = threshold

    async def find_duplicate(
        self,
        candidate: MemoryItem,
        session_id: str,
    ) -> MemoryItem | None:
        """Return the existing duplicate item if found, else None.

        Args:
            candidate: The new MemoryItem about to be written.
            session_id: Restrict the duplicate search to this session.

        Returns:
            The nearest-neighbour MemoryItem if similarity > threshold, else None.
        """
        request = QueryRequest(
            collection_name=COLLECTION,
            query_text=candidate.content,
            n_results=1,
            where={"session_id": session_id},
        )
        response = await self._adapter.query(request)
        if not response.results:
            return None

        top = response.results[0]
        if top.score >= self._threshold:
            logger.debug(
                "novelty_duplicate_found",
                existing_id=top.item.id,
                similarity=top.score,
                threshold=self._threshold,
            )
            return top.item

        return None
