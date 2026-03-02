"""STM consolidation pipeline — SCAN→SCORE→GATE→EMBED→PRUNE.

Stages:
  SCAN:  Retrieve all items for the session from Redis.
  SCORE: finalScore = importanceScore + (accessCount × 0.1) + (affectiveValence × 0.2)
  GATE:  importanceScore ≥ 0.5 → promote to episodic (if Tulving triple present) or LTM.
         Otherwise → delete.
  EMBED: Re-embed promoted items via nomic-embed-text before writing to target collection.
  PRUNE: Delete all processed items from brain.short-term-memory and Redis.
"""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, UpsertRequest

from short_term_memory.models import ConsolidationReport
from short_term_memory.store import ShortTermMemoryStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

GATE_THRESHOLD = 0.5
LTM_COLLECTION = "brain.long-term-memory"
EPISODIC_COLLECTION = "brain.episodic-memory"


def _has_tulving_triple(item: MemoryItem) -> bool:
    """Return True if the item carries sessionId, sourceTaskId, and createdAt."""
    meta = item.metadata
    return bool(
        meta.get("session_id")
        and meta.get("source_task_id")
        and item.created_at
    )


def _compute_final_score(item: MemoryItem) -> float:
    """Compute SCORE stage output.

    finalScore = importanceScore + (accessCount × 0.1) + (affectiveValence × 0.2)
    Capped at 1.0.
    """
    affective_valence: float = float(item.metadata.get("affective_valence", 0.0))
    score = (
        item.importance_score
        + item.access_count * 0.1
        + affective_valence * 0.2
    )
    return min(score, 1.0)


class ConsolidationPipeline:
    """SCAN→SCORE→GATE→EMBED→PRUNE consolidation pipeline for STM sessions."""

    def __init__(
        self,
        store: ShortTermMemoryStore,
        ltm_adapter: ChromaAdapter,
        episodic_adapter: ChromaAdapter,
        gate_threshold: float = GATE_THRESHOLD,
    ) -> None:
        self._store = store
        self._ltm_adapter = ltm_adapter
        self._episodic_adapter = episodic_adapter
        self._threshold = gate_threshold

    async def run(self, session_id: str) -> ConsolidationReport:
        """Execute the full consolidation pipeline for a session.

        Returns:
            ConsolidationReport with counts of promoted/deleted items.
        """
        # SCAN
        items = await self._store.get_by_session(session_id)
        promoted_episodic = 0
        promoted_ltm = 0
        deleted = 0

        episodic_items: list[MemoryItem] = []
        ltm_items: list[MemoryItem] = []

        for item in items:
            final_score = _compute_final_score(item)

            # GATE
            if final_score >= self._threshold:
                if _has_tulving_triple(item):
                    episodic_items.append(item)
                else:
                    ltm_items.append(item)
            else:
                deleted += 1

        # EMBED + write promoted items
        # Note: the ChromaAdapter handles embedding via EmbeddingClient internally.
        if episodic_items:
            upsert = UpsertRequest(
                collection_name=EPISODIC_COLLECTION,
                items=episodic_items,
            )
            await self._episodic_adapter.upsert(upsert)
            promoted_episodic = len(episodic_items)
            logger.info(
                "stm_consolidation_episodic",
                count=promoted_episodic,
                session_id=session_id,
            )

        if ltm_items:
            upsert = UpsertRequest(
                collection_name=LTM_COLLECTION,
                items=ltm_items,
            )
            await self._ltm_adapter.upsert(upsert)
            promoted_ltm = len(ltm_items)
            logger.info(
                "stm_consolidation_ltm",
                count=promoted_ltm,
                session_id=session_id,
            )

        # PRUNE — remove all processed items from STM
        await self._store.expire_session(session_id)

        return ConsolidationReport(
            session_id=session_id,
            promoted_episodic=promoted_episodic,
            promoted_ltm=promoted_ltm,
            deleted=deleted,
            total_processed=len(items),
        )
