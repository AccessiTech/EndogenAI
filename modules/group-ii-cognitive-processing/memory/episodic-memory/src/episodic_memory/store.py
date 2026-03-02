"""Append-only episodic event store backed by brain.episodic-memory ChromaDB collection.

Events are NEVER updated after initial write (immutable log).
On reconsolidation (retrieval), only ``accessCount`` and ``importanceScore``
metadata fields are updated — content is preserved.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, UpsertRequest, UpsertResponse

from episodic_memory.indexer import EpisodicIndexer

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.episodic-memory"


class EpisodicStore:
    """Append-only store for episodic events in brain.episodic-memory.

    Validates each item via EpisodicIndexer before writing.
    """

    def __init__(self, adapter: ChromaAdapter) -> None:
        self._adapter = adapter
        self._indexer = EpisodicIndexer()

    async def append(self, item: MemoryItem) -> str:
        """Validate and append an episodic event.

        Args:
            item: A MemoryItem with required Tulving triple in metadata.

        Returns:
            The event_id of the written item.

        Raises:
            ValueError: If the Tulving triple validation fails.
        """
        # Validate — raises ValueError if invalid
        EpisodicIndexer.validate(item)

        upsert_req = UpsertRequest(collection_name=COLLECTION, items=[item])
        resp: UpsertResponse = await self._adapter.upsert(upsert_req)
        event_id = resp.upserted_ids[0]
        logger.info("episodic_event_appended", event_id=event_id)
        return event_id

    async def on_retrieval(self, item: MemoryItem) -> None:
        """Apply reconsolidation side-effects: increment accessCount + boost importanceScore.

        Content is NEVER modified on reconsolidation.
        """
        item.access_count += 1
        item.last_accessed_at = datetime.now(UTC).isoformat()
        item.importance_score = min(item.importance_score + 0.01, 1.0)
        upsert_req = UpsertRequest(collection_name=COLLECTION, items=[item])
        await self._adapter.upsert(upsert_req)
        logger.debug("episodic_reconsolidation", event_id=item.id)
