"""Retrieval-augmented context assembler for working memory.

Queries three sources:
  1. brain.short-term-memory — Redis/ChromaDB session-scoped items
  2. brain.long-term-memory  — persistent semantic facts
  3. brain.episodic-memory   — ordered event log

Results are merged (deduplicated by content hash), sorted by importanceScore,
then trimmed to maxItems and tokenBudget before returning a ContextPayload.
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, QueryRequest

from working_memory.models import ContextPayload

logger: structlog.BoundLogger = structlog.get_logger(__name__)

STM_COLLECTION = "brain.short-term-memory"
LTM_COLLECTION = "brain.long-term-memory"
EPISODIC_COLLECTION = "brain.episodic-memory"
ESTIMATED_TOKENS_PER_CHAR = 0.25


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _estimate_tokens(content: str) -> int:
    return max(1, int(len(content) * ESTIMATED_TOKENS_PER_CHAR))


class LoaderConfig(NamedTuple):
    """Snapshot of retrieval configuration for a single load call."""

    top_k_per_source: int = 10
    max_items: int = 20
    token_budget: int = 8000
    min_importance_score: float = 0.1


class ContextLoader:
    """Assembles a ContextPayload by querying all three memory stores.

    Uses a single ChromaAdapter instance that can query multiple collections.
    """

    def __init__(
        self,
        adapter: ChromaAdapter,
        config: LoaderConfig | None = None,
    ) -> None:
        self._adapter = adapter
        self._config = config or LoaderConfig()

    async def load(
        self,
        session_id: str,
        query: str,
        capacity_override: int | None = None,
    ) -> ContextPayload:
        """Assemble a context payload from all three memory sources.

        Args:
            session_id: Current session identifier.
            query: Natural-language query driving context retrieval.
            capacity_override: If provided, overrides ``max_items`` from config.

        Returns:
            A ContextPayload with deduplicated, ranked MemoryItems.
        """
        max_items = capacity_override or self._config.max_items
        top_k = self._config.top_k_per_source

        # Query all three sources concurrently (sequential for simplicity; can use asyncio.gather)
        stm_items = await self._query_collection(
            STM_COLLECTION, query, top_k, {"session_id": session_id}
        )
        ltm_items = await self._query_collection(LTM_COLLECTION, query, top_k)
        episodic_items = await self._query_collection(
            EPISODIC_COLLECTION, query, top_k, {"session_id": session_id}
        )

        all_items = stm_items + ltm_items + episodic_items

        # Deduplicate by content hash
        seen: set[str] = set()
        unique: list[MemoryItem] = []
        for item in all_items:
            h = _content_hash(item.content)
            if h not in seen:
                seen.add(h)
                unique.append(item)

        # Filter by minimum importance
        filtered = [
            it for it in unique if it.importance_score >= self._config.min_importance_score
        ]

        # Sort by importanceScore descending
        filtered.sort(key=lambda it: it.importance_score, reverse=True)

        # Trim to max_items and token_budget
        selected: list[MemoryItem] = []
        total_tokens = 0
        for item in filtered:
            if len(selected) >= max_items:
                break
            item_tokens = _estimate_tokens(item.content)
            if total_tokens + item_tokens > self._config.token_budget:
                continue
            selected.append(item)
            total_tokens += item_tokens

        logger.debug(
            "wm_context_assembled",
            session_id=session_id,
            total_candidates=len(all_items),
            selected=len(selected),
            total_tokens=total_tokens,
        )
        return ContextPayload(
            session_id=session_id,
            query=query,
            items=selected,
            total_tokens=total_tokens,
            capacity_used=len(selected),
            capacity_limit=max_items,
        )

    async def _query_collection(
        self,
        collection: str,
        query: str,
        top_k: int,
        where: dict[str, object] | None = None,
    ) -> list[MemoryItem]:
        """Query a single collection; return empty list on error."""
        try:
            request = QueryRequest(
                collection_name=collection,
                query_text=query,
                n_results=top_k,
                where=where,
            )
            response = await self._adapter.query(request)
            return [r.item for r in response.results]
        except Exception:
            logger.exception("wm_loader_query_failed", collection=collection)
            return []
