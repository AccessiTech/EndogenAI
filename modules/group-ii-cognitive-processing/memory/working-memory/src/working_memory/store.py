"""In-process KV store for working memory with compound-priority eviction.

Compound eviction priority formula:
    eviction_priority =
        (1 - importanceScore) * importanceScoreWeight
      + time_decay(last_accessed_at, now, half_life=decayHalfLifeSeconds)
      + (1 - cosine_similarity(item.embedding, query_embedding)) * contextualRelevanceWeight

Both ``maxItems`` and ``tokenBudget`` constraints are enforced on every write.
On capacity breach, the item with the HIGHEST eviction_priority is dropped.
On tie (same priority), the item with the OLDEST ``created_at`` is evicted.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import structlog
from endogenai_vector_store.models import MemoryItem

from working_memory.models import ActiveItem

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Default capacity config (overridden via capacity.config.json at runtime)
DEFAULT_MAX_ITEMS = 20
DEFAULT_TOKEN_BUDGET = 8000
DEFAULT_DECAY_HALF_LIFE = 300.0
DEFAULT_IMPORTANCE_WEIGHT = 0.6
DEFAULT_RELEVANCE_WEIGHT = 0.4
ESTIMATED_TOKENS_PER_CHAR = 0.25  # rough estimate for token counting fallback


def _compute_time_decay(last_accessed_at: str | None, half_life_seconds: float) -> float:
    """Exponential decay: ``1 - exp(-Δt / half_life)``.

    Returns a value in [0, 1] — 0 for just-accessed, approaching 1 for stale items.
    """
    if not last_accessed_at:
        return 1.0
    try:
        last = datetime.fromisoformat(last_accessed_at)
        now = datetime.now(UTC)
        delta_seconds = max((now - last).total_seconds(), 0.0)
        return 1.0 - math.exp(-delta_seconds / max(half_life_seconds, 1.0))
    except (ValueError, TypeError):
        return 1.0


def _cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    """Cosine similarity between two float vectors, or 0.5 if unavailable."""
    if not a or not b or len(a) != len(b):
        return 0.5
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _estimate_token_count(content: str) -> int:
    """Rough token estimate: 0.25 × character count."""
    return max(1, int(len(content) * ESTIMATED_TOKENS_PER_CHAR))


class WorkingMemoryStore:
    """In-process KV store for working memory items.

    Uses a dict keyed by item_id → ActiveItem.
    Eviction fires when maxItems or tokenBudget is breached.
    Evicted items are dispatched to ConsolidationDispatcher (called externally).
    """

    def __init__(
        self,
        max_items: int = DEFAULT_MAX_ITEMS,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        decay_half_life_seconds: float = DEFAULT_DECAY_HALF_LIFE,
        importance_score_weight: float = DEFAULT_IMPORTANCE_WEIGHT,
        contextual_relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT,
    ) -> None:
        self._max_items = max_items
        self._token_budget = token_budget
        self._decay_half_life = decay_half_life_seconds
        self._importance_weight = importance_score_weight
        self._relevance_weight = contextual_relevance_weight
        self._store: dict[str, ActiveItem] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(
        self,
        item: MemoryItem,
        query_embedding: list[float] | None = None,
    ) -> MemoryItem | None:
        """Add an item to working memory; evict if capacity is exceeded.

        Enforces both ``maxItems`` and ``tokenBudget`` constraints.

        Args:
            item: The MemoryItem to store.
            query_embedding: Current query embedding for contextual relevance scoring.

        Returns:
            The evicted MemoryItem if one was dropped, else None.
        """
        token_count = _estimate_token_count(item.content)
        active = ActiveItem(item=item, token_count=token_count)
        self._store[item.id] = active

        evicted: MemoryItem | None = None

        # Enforce both capacity constraints
        while self._is_over_capacity():
            evicted = self._evict_one(query_embedding)
            if evicted is None:
                break

        return evicted

    def read(self, item_id: str) -> MemoryItem | None:
        """Return item and apply reconsolidation side-effects (accessCount, lastAccessedAt)."""
        active = self._store.get(item_id)
        if active is None:
            return None
        active.item.access_count += 1
        active.item.last_accessed_at = datetime.now(UTC).isoformat()
        active.item.importance_score = min(active.item.importance_score + 0.01, 1.0)
        return active.item

    def evict(self, item_id: str) -> MemoryItem | None:
        """Explicitly evict an item by ID.

        Returns:
            The evicted MemoryItem, or None if not found.
        """
        active = self._store.pop(item_id, None)
        if active is None:
            return None
        logger.info("wm_explicit_eviction", item_id=item_id)
        return active.item

    def list_active(self) -> list[MemoryItem]:
        """Return all active items sorted by importanceScore descending."""
        items = sorted(
            (a.item for a in self._store.values()),
            key=lambda it: it.importance_score,
            reverse=True,
        )
        return list(items)

    def compute_eviction_priority(
        self,
        item: MemoryItem,
        query_embedding: list[float] | None = None,
    ) -> float:
        """Compute compound eviction priority for an item.

        Higher value = more likely to be evicted.
        """
        decay = _compute_time_decay(item.last_accessed_at, self._decay_half_life)
        cosine = _cosine_similarity(item.embedding, query_embedding)
        priority = (
            (1.0 - item.importance_score) * self._importance_weight
            + decay
            + (1.0 - cosine) * self._relevance_weight
        )
        return priority

    def update(self, item_id: str, delta: dict[str, object]) -> MemoryItem | None:
        """Patch metadata fields on an active item; returns updated item or None if missing."""
        active = self._store.get(item_id)
        if active is None:
            return None
        item = active.item
        for key, value in delta.items():
            if hasattr(item, key):
                setattr(item, key, value)
        return item

    # ------------------------------------------------------------------
    # Capacity helpers
    # ------------------------------------------------------------------

    def _total_tokens(self) -> int:
        return sum(a.token_count for a in self._store.values())

    def _is_over_capacity(self) -> bool:
        return len(self._store) > self._max_items or self._total_tokens() > self._token_budget

    def _evict_one(self, query_embedding: list[float] | None) -> MemoryItem | None:
        """Find and remove the item with the highest eviction_priority."""
        if not self._store:
            return None
        worst_id = max(
            self._store,
            key=lambda iid: (
                self.compute_eviction_priority(self._store[iid].item, query_embedding),
                self._store[iid].item.created_at,
            ),
        )
        evicted_active = self._store.pop(worst_id)
        logger.info(
            "wm_auto_eviction",
            item_id=worst_id,
            importance=evicted_active.item.importance_score,
        )
        return evicted_active.item
