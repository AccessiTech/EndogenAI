"""test_a2a_handler.py — Unit tests for short-term memory A2A task handler.

Tests all task types dispatched via A2AHandler.handle():
  - write_record: stores an item, returns item_id
  - search_session: delegates to search, returns items
  - consolidate_session: runs pipeline, returns report
  - consolidate_item: writes item, returns promoted_to
  - unknown task type raises ValueError
"""

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType

from short_term_memory.a2a_handler import A2AHandler
from short_term_memory.models import ConsolidationReport


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_memory_item(item_id: str = "item-001") -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name="brain.short-term-memory",
        content="Test working memory content.",
        type=MemoryType.WORKING,
        source_module="test",
        importance_score=0.6,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )


@pytest.fixture
def handler() -> A2AHandler:
    store = MagicMock()
    store.write = AsyncMock(return_value="item-001")

    search = MagicMock()
    search.search = AsyncMock(return_value=[_make_memory_item("item-002")])

    pipeline = MagicMock()
    pipeline.run = AsyncMock(
        return_value=ConsolidationReport(
            session_id="sess-1",
            promoted_episodic=2,
            promoted_ltm=1,
            deleted=0,
            total_processed=3,
        )
    )

    return A2AHandler(store=store, search=search, pipeline=pipeline)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_write_record_returns_item_id(handler: A2AHandler) -> None:
    item = _make_memory_item()
    result = await handler.handle("write_record", {"item": item.model_dump()})
    assert result["item_id"] == "item-001"
    handler._store.write.assert_awaited_once()


async def test_search_session_returns_items(handler: A2AHandler) -> None:
    result = await handler.handle(
        "search_session",
        {"session_id": "sess-1", "query": "test", "top_k": 5},
    )
    assert "items" in result
    assert len(result["items"]) == 1
    call_kwargs = handler._search.search.call_args.kwargs
    assert call_kwargs["session_id"] == "sess-1"
    assert call_kwargs["top_k"] == 5


async def test_search_session_default_top_k(handler: A2AHandler) -> None:
    await handler.handle("search_session", {"session_id": "sess-2", "query": "x"})
    call_kwargs = handler._search.search.call_args.kwargs
    assert call_kwargs["top_k"] == 10


async def test_consolidate_session_returns_report(handler: A2AHandler) -> None:
    result = await handler.handle("consolidate_session", {"session_id": "sess-1"})
    assert result["session_id"] == "sess-1"
    assert result["promoted_episodic"] == 2
    handler._pipeline.run.assert_awaited_once_with("sess-1")


async def test_consolidate_item_returns_promoted_to(handler: A2AHandler) -> None:
    item = _make_memory_item()
    result = await handler.handle("consolidate_item", {"item": item.model_dump()})
    assert result["promoted_to"] == "brain.short-term-memory"
    handler._store.write.assert_awaited_once()


async def test_unknown_task_raises(handler: A2AHandler) -> None:
    with pytest.raises(ValueError, match="Unknown A2A task type"):
        await handler.handle("invalid_type", {})


async def test_handler_stores_dependencies() -> None:
    store = MagicMock()
    search = MagicMock()
    pipeline = MagicMock()

    h = A2AHandler(store=store, search=search, pipeline=pipeline)

    assert h._store is store
    assert h._search is search
    assert h._pipeline is pipeline
