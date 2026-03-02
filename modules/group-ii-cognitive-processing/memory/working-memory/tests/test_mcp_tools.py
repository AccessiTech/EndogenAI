"""Unit tests for MCPTools in working memory."""

from __future__ import annotations

import pytest

from working_memory.mcp_tools import MCPTools
from working_memory.store import WorkingMemoryStore

from .conftest import make_wm_item


@pytest.fixture
def mcp_tools(
    wm_store: WorkingMemoryStore,
    loader: object,
    dispatcher: object,
) -> MCPTools:
    return MCPTools(store=wm_store, loader=loader, dispatcher=dispatcher)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_write_item_tool(mcp_tools: MCPTools) -> None:
    """working_memory.write_item should store item and return item_id."""
    item = make_wm_item()
    result = await mcp_tools.handle("working_memory.write_item", {"item": item.model_dump()})
    assert result["item_id"] == "wm-item-1"


@pytest.mark.asyncio
async def test_list_active_tool(mcp_tools: MCPTools) -> None:
    """working_memory.list_active should return all active items as dicts."""
    item = make_wm_item()
    await mcp_tools.handle("working_memory.write_item", {"item": item.model_dump()})
    result = await mcp_tools.handle("working_memory.list_active", {"session_id": "session-abc"})
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_unknown_tool_raises(mcp_tools: MCPTools) -> None:
    """Unknown tool name should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await mcp_tools.handle("nonexistent.tool", {})
