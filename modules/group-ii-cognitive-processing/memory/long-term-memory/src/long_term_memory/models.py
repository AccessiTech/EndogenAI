"""Pydantic models for the long-term memory module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticFact(BaseModel):
    """A decontextualised fact stored in the SQL structured store."""

    entity_id: str = Field(..., description="Subject entity identifier.")
    predicate: str = Field(..., description="Relationship or property name.")
    object_value: str = Field(..., description="Object or property value.")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    source_item_id: str | None = Field(
        default=None, description="MemoryItem ID that generated this fact."
    )
    created_at: str = Field(..., description="ISO-8601 UTC timestamp.")


class GraphEdge(BaseModel):
    """A directed edge in the knowledge graph."""

    source_entity_id: str
    predicate: str
    target_entity_id: str
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    source_item_id: str | None = None


class LTMItem(BaseModel):
    """Wrapper combining a MemoryItem ID with LTM-specific metadata."""

    item_id: str
    entity_id: str | None = None
    graph_edges: list[GraphEdge] = Field(default_factory=list)
    facts: list[SemanticFact] = Field(default_factory=list)


class SeedReport(BaseModel):
    """Result of the boot-time seed pipeline."""

    chunks_written: int = Field(default=0, ge=0)
    already_seeded: bool = Field(default=False)
    source_path: str = ""
