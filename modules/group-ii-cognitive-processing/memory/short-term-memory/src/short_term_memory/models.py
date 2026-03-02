"""Pydantic models for the short-term memory module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionRecord(BaseModel):
    """Metadata linking a MemoryItem to a Redis session list."""

    session_id: str = Field(..., description="Session identifier.")
    item_id: str = Field(..., description="UUID of the MemoryItem.")
    created_at: str = Field(..., description="ISO-8601 UTC timestamp of record creation.")
    ttl_seconds: int = Field(default=1800, ge=1, description="TTL for the Redis session key.")


class ConsolidationCandidate(BaseModel):
    """Scored item candidate for consolidation promotion."""

    item_id: str
    session_id: str
    final_score: float = Field(..., ge=0.0, description="SCORE stage output.")
    promoted_to: str | None = Field(
        default=None, description="Target collection after promotion."
    )
    deleted: bool = Field(default=False)


class ConsolidationReport(BaseModel):
    """Result summary of a consolidation pipeline run."""

    session_id: str
    promoted_episodic: int = Field(default=0, ge=0)
    promoted_ltm: int = Field(default=0, ge=0)
    deleted: int = Field(default=0, ge=0)
    total_processed: int = Field(default=0, ge=0)
