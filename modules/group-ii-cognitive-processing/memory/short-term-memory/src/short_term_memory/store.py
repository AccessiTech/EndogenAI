"""Redis-backed short-term memory store.

Session items are stored in two places:
  1. Redis list ``session:<session_id>`` — ordered list of serialised MemoryItem JSON.
     A TTL is set on the Redis key so it expires automatically.
  2. ChromaDB ``brain.short-term-memory`` collection — for semantic search over the
     current session (novelty checks, semantic retrieval).

All Redis operations use ``redis.asyncio`` (async client).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import redis.asyncio as aioredis
import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import (
    DeleteRequest,
    MemoryItem,
    UpsertRequest,
    UpsertResponse,
)

from short_term_memory.models import ConsolidationReport
from short_term_memory.novelty import NoveltyChecker

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.short-term-memory"


class ShortTermMemoryStore:
    """Session-keyed Redis store with ChromaDB semantic index."""

    def __init__(
        self,
        redis_client: aioredis.Redis,
        adapter: ChromaAdapter,
        novelty_checker: NoveltyChecker,
        ttl_seconds: int = 1800,
        session_key_prefix: str = "session:",
    ) -> None:
        self._redis = redis_client
        self._adapter = adapter
        self._novelty = novelty_checker
        self._ttl = ttl_seconds
        self._prefix = session_key_prefix

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _session_key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    def _now_iso(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def write(self, item: MemoryItem) -> str:
        """Write a MemoryItem to Redis + ChromaDB; novelty check applied.

        If an existing item with similarity > threshold is found, increment its
        importanceScore by 0.05 (capped at 1.0) and return the existing item_id.
        Otherwise write as a new item.

        Returns:
            The item_id that was created or updated.
        """
        session_id: str = item.metadata.get("session_id", "")
        duplicate = await self._novelty.find_duplicate(item, session_id) if session_id else None

        if duplicate is not None:
            # Affective boost: increment importance on the duplicate
            new_score = min(duplicate.importance_score + 0.05, 1.0)
            duplicate.importance_score = new_score
            duplicate.updated_at = self._now_iso()
            upsert_req = UpsertRequest(collection_name=COLLECTION, items=[duplicate])
            await self._adapter.upsert(upsert_req)
            logger.info(
                "stm_duplicate_boosted",
                item_id=duplicate.id,
                new_score=new_score,
            )
            return duplicate.id

        # Novel item — write to both Redis and ChromaDB
        upsert_req = UpsertRequest(collection_name=COLLECTION, items=[item])
        resp: UpsertResponse = await self._adapter.upsert(upsert_req)

        if session_id:
            redis_key = self._session_key(session_id)
            payload = item.model_dump_json()
            await self._redis.rpush(redis_key, payload)  # type: ignore[misc]
            await self._redis.expire(redis_key, self._ttl)

        logger.info("stm_item_written", item_id=resp.upserted_ids[0])
        return resp.upserted_ids[0]

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_session(self, session_id: str) -> list[MemoryItem]:
        """Return all items for a session in insertion order."""
        redis_key = self._session_key(session_id)
        raw_items: list[str] = await self._redis.lrange(redis_key, 0, -1)  # type: ignore[misc]
        items: list[MemoryItem] = []
        for raw in raw_items:
            data = json.loads(raw)
            items.append(MemoryItem.model_validate(data))
        return items

    # ------------------------------------------------------------------
    # Expire / consolidate
    # ------------------------------------------------------------------

    async def expire_session(self, session_id: str) -> ConsolidationReport:
        """End a session: delete from Redis and ChromaDB, return consolidation report stub.

        The full consolidation pipeline is run by ``ConsolidationPipeline.run()``.
        This method handles the PRUNE step only (removing processed items from the store).
        """
        items = await self.get_by_session(session_id)
        item_ids = [it.id for it in items]

        # Remove from Redis
        redis_key = self._session_key(session_id)
        await self._redis.delete(redis_key)

        # Remove from ChromaDB
        if item_ids:
            delete_req = DeleteRequest(collection_name=COLLECTION, ids=item_ids)
            await self._adapter.delete(delete_req)

        logger.info(
            "stm_session_expired",
            session_id=session_id,
            items_removed=len(item_ids),
        )
        return ConsolidationReport(
            session_id=session_id,
            total_processed=len(item_ids),
        )
