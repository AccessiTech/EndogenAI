"""test_a2a_handler.py — Unit tests for episodic memory A2A task handler.

Tests all task types dispatched via A2AHandler.handle():
  - write_event: stores an event, returns event_id
  - search_episodes: delegates to retrieval, returns items list
  - get_timeline: delegates to timeline, returns events
  - run_distillation: runs distillation, returns report
  - unknown task type raises ValueError
"""

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType

from episodic_memory.a2a_handler import A2AHandler
from episodic_memory.models import DistillationReport


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_memory_item(event_id: str = "ev-001") -> MemoryItem:
    return MemoryItem(
        id=event_id,
        collection_name="brain.episodic-memory",
        content="The agent succeeded.",
        type=MemoryType.EPISODIC,
        source_module="test",
        importance_score=0.8,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )


@pytest.fixture
def handler() -> A2AHandler:
    store = MagicMock()
    store.append = AsyncMock(return_value="ev-001")

    retrieval = MagicMock()
    retrieval.semantic_search = AsyncMock(return_value=[_make_memory_item("ev-002")])

    timeline = MagicMock()
    timeline.get_session_timeline = AsyncMock(return_value=[_make_memory_item("ev-003")])

    distillation = MagicMock()
    distillation.run = AsyncMock(
        return_value=DistillationReport(
            clusters_found=2,
            facts_written_to_ltm=3,
            items_processed=5,
        )
    )

    return A2AHandler(
        store=store,
        retrieval=retrieval,
        timeline=timeline,
        distillation=distillation,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_write_event_returns_event_id(handler: A2AHandler) -> None:
    item = _make_memory_item()
    payload = {"event": item.model_dump()}
    result = await handler.handle("write_event", payload)
    assert result["event_id"] == "ev-001"
    handler._store.append.assert_awaited_once()


async def test_search_episodes_returns_items(handler: A2AHandler) -> None:
    payload = {"query": "agent success", "top_k": 5, "session_id": "sess-1"}
    result = await handler.handle("search_episodes", payload)
    assert "items" in result
    assert len(result["items"]) == 1
    handler._retrieval.semantic_search.assert_awaited_once_with(
        query="agent success",
        top_k=5,
        session_id="sess-1",
        time_window_start=None,
        time_window_end=None,
    )


async def test_search_episodes_default_top_k(handler: A2AHandler) -> None:
    payload = {"query": "test"}
    result = await handler.handle("search_episodes", payload)
    call_kwargs = handler._retrieval.semantic_search.call_args.kwargs
    assert call_kwargs["top_k"] == 10  # default


async def test_get_timeline_returns_events(handler: A2AHandler) -> None:
    payload = {"session_id": "sess-abc"}
    result = await handler.handle("get_timeline", payload)
    assert "events" in result
    assert len(result["events"]) == 1
    handler._timeline.get_session_timeline.assert_awaited_once_with("sess-abc")


async def test_run_distillation_returns_report(handler: A2AHandler) -> None:
    result = await handler.handle("run_distillation", {})
    assert result["clusters_found"] == 2
    assert result["facts_written_to_ltm"] == 3
    handler._distillation.run.assert_awaited_once()


async def test_unknown_task_type_raises(handler: A2AHandler) -> None:
    with pytest.raises(ValueError, match="Unknown A2A task type"):
        await handler.handle("nonexistent", {})


async def test_handler_stores_dependencies() -> None:
    """Verify __init__ stores all dependencies as expected."""
    store = MagicMock()
    retrieval = MagicMock()
    timeline = MagicMock()
    distillation = MagicMock()

    h = A2AHandler(
        store=store,
        retrieval=retrieval,
        timeline=timeline,
        distillation=distillation,
    )

    assert h._store is store
    assert h._retrieval is retrieval
    assert h._timeline is timeline
    assert h._distillation is distillation
