"""Reconsolidation engine for long-term memory.

On every retrieval:
  1. Increment accessCount on the retrieved item.
  2. Re-evaluate importanceScore based on access frequency.
  3. Re-embed the item if its content has changed (labile window analogue).

This mirrors the biological reconsolidation process: retrieved memories
are briefly labile and can be updated before being re-stabilised.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from endogenai_vector_store.models import MemoryItem

from long_term_memory.vector_store import LTMVectorStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

ACCESS_IMPORTANCE_BOOST_PER_HIT = 0.02
MAX_IMPORTANCE = 1.0


class ReconsolidationEngine:
    """Applies reconsolidation side-effects to retrieved LTM items."""

    def __init__(self, vector_store: LTMVectorStore) -> None:
        self._vector_store = vector_store

    async def on_retrieval(
        self,
        item: MemoryItem,
        new_content: str | None = None,
    ) -> MemoryItem:
        """Apply reconsolidation to a retrieved item.

        Increments accessCount, recalculates importanceScore, and re-embeds
        if `new_content` differs from the existing content.

        Args:
            item: The MemoryItem as returned from the vector store.
            new_content: If provided and different from item.content, triggers re-embedding.

        Returns:
            The updated MemoryItem after persistence.
        """
        item.access_count += 1
        item.last_accessed_at = datetime.now(UTC).isoformat()
        item.importance_score = min(
            item.importance_score + ACCESS_IMPORTANCE_BOOST_PER_HIT,
            MAX_IMPORTANCE,
        )
        if new_content is not None and new_content != item.content:
            item.content = new_content
            item.updated_at = datetime.now(UTC).isoformat()
            logger.info("ltm_reconsolidation_reembed", item_id=item.id)

        await self._vector_store.update(item)
        logger.debug(
            "ltm_reconsolidation_done",
            item_id=item.id,
            access_count=item.access_count,
            importance_score=item.importance_score,
        )
        return item
