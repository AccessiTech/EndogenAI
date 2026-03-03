"""Tests for MCPTools dispatcher."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

from agent_runtime.mcp_tools import MCPTools


@pytest.fixture
def mcp(mock_orchestrator: MagicMock, mock_tool_registry: MagicMock) -> MCPTools:
    return MCPTools(orchestrator=mock_orchestrator, tool_registry=mock_tool_registry)


class TestMCPToolsDispatch:
    async def test_unknown_tool_raises(self, mcp: MCPTools) -> None:
        with pytest.raises(ValueError, match="Unknown tool"):
            await mcp.handle("agent_runtime.nonexistent", {})

    async def test_execute_intention(self, mcp: MCPTools) -> None:
        result = await mcp.handle(
            "agent_runtime.execute_intention",
            {"goal_id": "goal-001", "context_payload": {}},
        )
        assert result["workflow_id"] == "goal-001-001"
        assert result["orchestrator"] == "temporal"

    async def test_get_execution_status(self, mcp: MCPTools) -> None:
        result = await mcp.handle(
            "agent_runtime.get_execution_status",
            {"goal_id": "goal-001"},
        )
        assert result["goal_id"] == "goal-001"
        assert "status" in result

    async def test_abort_execution(self, mcp: MCPTools) -> None:
        result = await mcp.handle(
            "agent_runtime.abort_execution",
            {"goal_id": "goal-001"},
        )
        assert result["status"] == "aborted"

    async def test_list_tools_no_filter(self, mcp: MCPTools) -> None:
        result = await mcp.handle("agent_runtime.list_tools", {})
        assert result["total"] == 1
        assert result["skills"][0]["skill_id"] == "skill.test"

    async def test_list_tools_with_matching_filter(self, mcp: MCPTools) -> None:
        result = await mcp.handle(
            "agent_runtime.list_tools",
            {"capability_filter": "test"},
        )
        assert result["total"] == 1

    async def test_list_tools_with_non_matching_filter(self, mcp: MCPTools) -> None:
        result = await mcp.handle(
            "agent_runtime.list_tools",
            {"capability_filter": "nonexistent_capability"},
        )
        assert result["total"] == 0

    async def test_register_tool(self, mcp: MCPTools) -> None:
        params = {
            "skill_id": "skill.new",
            "name": "New Skill",
            "description": "Newly registered",
            "agent_url": "http://localhost:9100",
            "capabilities": ["new"],
            "healthy": True,
        }
        result = await mcp.handle("agent_runtime.register_tool", params)
        assert result["skill_id"] == "skill.new"
        mcp._registry.register.assert_called_once()
