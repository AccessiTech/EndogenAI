"""Unit tests for Timeline."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from endogenai_vector_store.models import QueryResponse, QueryResult

from episodic_memory.timeline import Timeline

from .conftest import make_event


@pytest.mark.asyncio
async def test_get_session_timeline_ordered(
    timeline: Timeline, mock_adapter: object
) -> None:
    """Timeline should return events sorted by created_at ascending."""
    event_a = make_event(event_id="event-late", content="Later event")
    object.__setattr__(event_a, "created_at", "2026-03-01T15:00:00+00:00")

    event_b = make_event(event_id="event-early", content="Earlier event")
    # Default created_at is 12:00:00

    mock_adapter.query = AsyncMock(  # type: ignore[union-attr]
        return_value=QueryResponse(
            results=[
                QueryResult(item=event_a, score=0.9),
                QueryResult(item=event_b, score=0.8),
            ]
        )
    )

    events = await timeline.get_session_timeline("session-abc")
    assert events[0].id == "event-early"
    assert events[1].id == "event-late"


@pytest.mark.asyncio
async def test_timeline_empty_session(timeline: Timeline) -> None:
    """No events for unknown session returns empty list."""
    events = await timeline.get_session_timeline("ghost-session")
    assert events == []
