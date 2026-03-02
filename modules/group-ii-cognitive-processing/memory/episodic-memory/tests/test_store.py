"""Unit tests for EpisodicStore."""

from __future__ import annotations

import pytest

from episodic_memory.store import EpisodicStore

from .conftest import make_event


@pytest.mark.asyncio
async def test_append_valid_event(episodic_store: EpisodicStore) -> None:
    """Valid episodic event with Tulving triple should be written."""
    event = make_event()
    event_id = await episodic_store.append(event)
    assert event_id == "event-1"


@pytest.mark.asyncio
async def test_append_missing_session_id_raises(episodic_store: EpisodicStore) -> None:
    """Event without session_id should raise ValueError."""
    event = make_event()
    event.metadata.pop("session_id")
    with pytest.raises(ValueError, match="session_id"):
        await episodic_store.append(event)


@pytest.mark.asyncio
async def test_append_missing_source_task_id_raises(episodic_store: EpisodicStore) -> None:
    """Event without source_task_id should raise ValueError."""
    event = make_event()
    event.metadata.pop("source_task_id")
    with pytest.raises(ValueError, match="source_task_id"):
        await episodic_store.append(event)


@pytest.mark.asyncio
async def test_append_missing_created_at_raises(episodic_store: EpisodicStore) -> None:
    """Event without created_at should raise ValueError."""
    event = make_event()
    object.__setattr__(event, "created_at", "")
    with pytest.raises(ValueError):
        await episodic_store.append(event)
