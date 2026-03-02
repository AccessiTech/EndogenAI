"""Consolidation dispatcher — routes evicted working memory items downstream.

On eviction:
- If item has sessionId + sourceTaskId + createdAt → route to episodic-memory.
- Otherwise → route to short-term-memory (for consolidation into LTM later).

Routing is done via A2A task calls to the respective module endpoints.
"""

from __future__ import annotations

import structlog
from endogenai_a2a import A2AClient
from endogenai_vector_store.models import MemoryItem

logger: structlog.BoundLogger = structlog.get_logger(__name__)

STM_A2A_URL = "http://localhost:8202"
EPISODIC_A2A_URL = "http://localhost:8204"


def _has_tulving_triple(item: MemoryItem) -> bool:
    meta = item.metadata
    return bool(meta.get("session_id") and meta.get("source_task_id") and item.created_at)


class ConsolidationDispatcher:
    """Routes evicted working memory items to STM or episodic memory via A2A."""

    def __init__(
        self,
        stm_a2a_url: str = STM_A2A_URL,
        episodic_a2a_url: str = EPISODIC_A2A_URL,
        a2a_client: A2AClient | None = None,
    ) -> None:
        self._stm_url = stm_a2a_url
        self._episodic_url = episodic_a2a_url
        self._a2a_client = a2a_client

    def _get_client(self, url: str) -> A2AClient:
        """Return the injected client (for testing) or create one for the given URL."""
        if self._a2a_client is not None:
            return self._a2a_client
        return A2AClient(url=url)

    async def dispatch(self, item: MemoryItem) -> str:
        """Dispatch an evicted item to the appropriate downstream module.

        Args:
            item: The evicted MemoryItem to dispatch.

        Returns:
            The target collection name where the item was routed.
        """
        if _has_tulving_triple(item):
            target_url = self._episodic_url
            task_type = "write_event"
            target = "brain.episodic-memory"
        else:
            target_url = self._stm_url
            task_type = "consolidate_item"
            target = "brain.short-term-memory"

        try:
            client = self._get_client(target_url)
            # episodic write_event expects key "event"; STM consolidate_item expects "item"
            task_payload = (
                {"event": item.model_dump()}
                if task_type == "write_event"
                else {"item": item.model_dump()}
            )
            await client.send_task(task_type, task_payload)
            logger.info("wm_eviction_dispatched", item_id=item.id, target=target)
        except Exception:
            logger.exception("wm_eviction_dispatch_failed", item_id=item.id)

        return target
