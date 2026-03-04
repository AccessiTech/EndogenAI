"""test_mcp_tools.py — Unit tests for episodic memory MCP tool handler.

Tests all tool names dispatched via MCPTools.handle():
  - em.write_event: stores an event, returns event_id
  - em.search: delegates to retrieval, returns items
  - em.get_timeline: delegates to timeline, returns events
  - em.run_distillation: runs distillation, returns report dict
  - unknown tool name raises ValueError
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType

from episodic_memory.mcp_tools import MCPTools
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
def mcp_tools() -> MCPTools:
    store = MagicMock()
    store.append = AsyncMock(return_value="ev-001")

    retrieval = MagicMock()
    retrieval.semantic_search = AsyncMock(return_value=[_make_memory_item("ev-002")])

    timeline = MagicMock()
    timeline.get_session_timeline = AsyncMock(return_value=[_make_memory_item("ev-003")])

    distillation = MagicMock()
    distillation.run = AsyncMock(
        return_value=DistillationReport(
            clusters_found=1,
            facts_written_to_ltm=2,
            items_processed=3,
        )
    )

    return MCPTools(
        store=store,
        retrieval=retrieval,
        timeline=timeline,
        distillation=distillation,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_write_event_returns_event_id(mcp_tools: MCPTools) -> None:
    item = _make_memory_item()
    result = await mcp_tools.handle("em.write_event", {"event": item.model_dump()})
    assert result["event_id"] == "ev-001"
    mcp_tools._store.append.assert_awaited_once()


async def test_search_returns_items(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "em.search",
        {"query": "agent success", "top_k": 5, "session_id": "sess-1"},
    )
    assert "items" in result
    assert len(result["items"]) == 1
    call_kwargs = mcp_tools._retrieval.semantic_search.call_args.kwargs
    assert call_kwargs["query"] == "agent success"
    assert call_kwargs["top_k"] == 5


async def test_search_default_top_k(mcp_tools: MCPTools) -> None:
    await mcp_tools.handle("em.search", {"query": "test"})
    call_kwargs = mcp_tools._retrieval.semantic_search.call_args.kwargs
    assert call_kwargs["top_k"] == 10


async def test_get_timeline_returns_events(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("em.get_timeline", {"session_id": "sess-abc"})
    assert "events" in result
    assert len(result["events"]) == 1


async def test_run_distillation_returns_report(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("em.run_distillation", {})
    assert result["clusters_found"] == 1
    assert result["facts_written_to_ltm"] == 2
    mcp_tools._distillation.run.assert_awaited_once()


async def test_unknown_tool_raises(mcp_tools: MCPTools) -> None:
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await mcp_tools.handle("em.nonexistent", {})


async def test_mcp_tools_stores_dependencies() -> None:
    """Verify MCPTools __init__ stores all dependencies."""
    store = MagicMock()
    retrieval = MagicMock()
    timeline = MagicMock()
    distillation = MagicMock()

    tools = MCPTools(
        store=store,
        retrieval=retrieval,
        timeline=timeline,
        distillation=distillation,
    )

    assert tools._store is store
    assert tools._retrieval is retrieval
    assert tools._timeline is timeline
    assert tools._distillation is distillation
