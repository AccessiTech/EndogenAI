"""test_mcp_tools.py — Unit tests for MCPTools."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from motor_output.mcp_tools import MCPTools
from motor_output.models import (
    ChannelType,
    DispatchRecord,
    DispatchStatus,
    MotorFeedback,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _sample_feedback(action_id: str = "act-001") -> MotorFeedback:
    return MotorFeedback(
        action_id=action_id,
        goal_id="goal-001",
        channel=ChannelType.HTTP,
        actual_outcome={"success": True},
        success=True,
        dispatched_at=_now(),
        completed_at=_now(),
    )


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    d = MagicMock()
    d.dispatch = AsyncMock(return_value=_sample_feedback())
    d.get_record = MagicMock(return_value=None)
    d.abort_dispatch = MagicMock(return_value=True)
    d.list_channels = MagicMock(return_value=[{"channel": "http", "handler": "HTTPChannel"}])
    return d


@pytest.fixture
def mcp(mock_dispatcher: MagicMock) -> MCPTools:
    return MCPTools(dispatcher=mock_dispatcher)


def test_get_tool_definitions_returns_four(mcp: MCPTools) -> None:
    tools = mcp.get_tool_definitions()
    assert len(tools) == 4
    names = {t["name"] for t in tools}
    assert "motor_output.dispatch_action" in names
    assert "motor_output.list_channels" in names


@pytest.mark.asyncio
async def test_dispatch_action_tool(mcp: MCPTools) -> None:
    result = await mcp.call_tool(
        "motor_output.dispatch_action",
        {"action_id": "act-001", "type": "test.call", "channel": "http", "params": {}},
    )
    assert result["action_id"] == "act-001"
    assert result["success"] is True


@pytest.mark.asyncio
async def test_list_channels_tool(mcp: MCPTools) -> None:
    result = await mcp.call_tool("motor_output.list_channels", {})
    assert "channels" in result
    assert result["channels"][0]["channel"] == "http"


@pytest.mark.asyncio
async def test_abort_dispatch_tool(mcp: MCPTools) -> None:
    result = await mcp.call_tool("motor_output.abort_dispatch", {"action_id": "act-001"})
    assert result["aborted"] is True
    assert result["action_id"] == "act-001"


@pytest.mark.asyncio
async def test_get_dispatch_status_not_found(mcp: MCPTools) -> None:
    result = await mcp.call_tool("motor_output.get_dispatch_status", {"action_id": "missing"})
    assert "error" in result


@pytest.mark.asyncio
async def test_get_dispatch_status_found(mcp: MCPTools, mock_dispatcher: MagicMock) -> None:
    mock_dispatcher.get_record.return_value = DispatchRecord(
        action_id="act-999",
        channel=ChannelType.HTTP,
        status=DispatchStatus.SUCCESS,
    )
    result = await mcp.call_tool("motor_output.get_dispatch_status", {"action_id": "act-999"})
    assert result["action_id"] == "act-999"
    assert result["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_unknown_tool_returns_error(mcp: MCPTools) -> None:
    result = await mcp.call_tool("motor_output.unknown", {})
    assert "error" in result
