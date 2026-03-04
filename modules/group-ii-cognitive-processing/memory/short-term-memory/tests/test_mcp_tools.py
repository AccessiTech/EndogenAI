"""test_mcp_tools.py — Unit tests for short-term memory MCP tool handler.

Tests all tool names dispatched via MCPTools.handle():
  - stm.write: stores item, returns item_id
  - stm.search: delegates to search, returns items
  - stm.expire_session: runs consolidation pipeline, returns report
  - stm.get_by_session: returns all items for a session
  - unknown tool name raises ValueError
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType

from short_term_memory.mcp_tools import MCPTools
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
def mcp_tools() -> MCPTools:
    store = MagicMock()
    store.write = AsyncMock(return_value="item-001")
    store.get_by_session = AsyncMock(return_value=[_make_memory_item("item-005")])

    search = MagicMock()
    search.search = AsyncMock(return_value=[_make_memory_item("item-002")])

    pipeline = MagicMock()
    pipeline.run = AsyncMock(
        return_value=ConsolidationReport(
            session_id="sess-1",
            promoted_episodic=1,
            promoted_ltm=0,
            deleted=0,
            total_processed=1,
        )
    )

    return MCPTools(store=store, search=search, pipeline=pipeline)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_stm_write_returns_item_id(mcp_tools: MCPTools) -> None:
    item = _make_memory_item()
    result = await mcp_tools.handle("stm.write", {"item": item.model_dump()})
    assert result["item_id"] == "item-001"
    mcp_tools._store.write.assert_awaited_once()


async def test_stm_search_returns_items(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "stm.search",
        {"session_id": "sess-1", "query": "test", "top_k": 3},
    )
    assert "items" in result
    assert len(result["items"]) == 1
    call_kwargs = mcp_tools._search.search.call_args.kwargs
    assert call_kwargs["top_k"] == 3


async def test_stm_search_default_top_k(mcp_tools: MCPTools) -> None:
    await mcp_tools.handle("stm.search", {"session_id": "s", "query": "q"})
    call_kwargs = mcp_tools._search.search.call_args.kwargs
    assert call_kwargs["top_k"] == 10


async def test_stm_expire_session_returns_report(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("stm.expire_session", {"session_id": "sess-1"})
    assert result["session_id"] == "sess-1"
    assert result["promoted_episodic"] == 1
    mcp_tools._pipeline.run.assert_awaited_once_with("sess-1")


async def test_stm_get_by_session_returns_items(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("stm.get_by_session", {"session_id": "sess-1"})
    assert "items" in result
    assert len(result["items"]) == 1
    mcp_tools._store.get_by_session.assert_awaited_once_with("sess-1")


async def test_unknown_tool_raises(mcp_tools: MCPTools) -> None:
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await mcp_tools.handle("stm.nonexistent", {})


async def test_mcp_tools_stores_dependencies() -> None:
    store = MagicMock()
    search = MagicMock()
    pipeline = MagicMock()

    tools = MCPTools(store=store, search=search, pipeline=pipeline)

    assert tools._store is store
    assert tools._search is search
    assert tools._pipeline is pipeline
