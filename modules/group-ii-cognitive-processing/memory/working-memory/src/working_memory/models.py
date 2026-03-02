"""Pydantic models for the working memory module."""

from __future__ import annotations

from enum import StrEnum

from endogenai_vector_store.models import MemoryItem
from pydantic import BaseModel, Field


class EvictionPolicy(StrEnum):
    """Eviction policy variants for working memory."""

    COMPOUND_PRIORITY = "compound-priority"
    FIFO = "fifo"
    LRU = "lru"


class ActiveItem(BaseModel):
    """A MemoryItem held in the working memory KV store with eviction metadata."""

    item: MemoryItem
    eviction_priority: float = Field(
        default=0.0,
        description="Computed compound eviction priority — higher means more likely to be evicted.",
    )
    token_count: int = Field(
        default=0, ge=0, description="Estimated token count for budget enforcement."
    )


class ContextPayload(BaseModel):
    """The assembled context window returned to the reasoning module."""

    session_id: str
    query: str
    items: list[MemoryItem] = Field(default_factory=list)
    total_tokens: int = Field(default=0, ge=0)
    capacity_used: int = Field(default=0, ge=0)
    capacity_limit: int = Field(default=20, ge=1)


class ConsolidationReport(BaseModel):
    """Summary of a working memory session consolidation flush."""

    session_id: str
    items_flushed: int = Field(default=0, ge=0)
