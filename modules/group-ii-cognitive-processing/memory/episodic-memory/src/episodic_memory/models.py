"""Pydantic models for the episodic memory module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EpisodeEvent(BaseModel):
    """A single discrete event in the episodic log.

    The Tulving triple — sessionId (where), sourceTaskId (what), createdAt (when) —
    is mandatory on every event. Validation is enforced by EpisodicIndexer.
    """

    event_id: str = Field(..., description="UUID of the event MemoryItem.")
    session_id: str = Field(..., description="Where: session context identifier.")
    source_task_id: str = Field(..., description="What: originating task identifier.")
    created_at: str = Field(..., description="When: ISO-8601 UTC timestamp.")
    affective_valence: float = Field(
        default=0.0, ge=-1.0, le=1.0, description="Emotional valence (-1 to 1)."
    )


class Episode(BaseModel):
    """An ordered sequence of events constituting a coherent episode."""

    session_id: str
    events: list[EpisodeEvent] = Field(default_factory=list)
    start_time: str = ""
    end_time: str = ""


class TimelineQuery(BaseModel):
    """Parameters for a temporal or composite search query."""

    session_id: str | None = None
    query_text: str | None = None
    time_window_start: str | None = None
    time_window_end: str | None = None
    top_k: int = Field(default=10, ge=1, le=100)


class DistillationReport(BaseModel):
    """Result of an episodic → semantic distillation run."""

    clusters_found: int = Field(default=0, ge=0)
    facts_written_to_ltm: int = Field(default=0, ge=0)
    items_processed: int = Field(default=0, ge=0)
