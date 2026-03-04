"""test_mcp_tools.py — Unit tests for reasoning MCP tool handler.

Covers all tools:
  - reasoning.run_inference (with and without plan)
  - reasoning.create_plan
  - reasoning.query_traces
  - unknown tool raises ValueError
"""

from __future__ import annotations

import pytest

from reasoning.mcp_tools import MCPTools


async def test_run_inference_returns_trace(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.run_inference",
        {"query": "What is the cause?", "context": ["Fact A"]},
    )
    assert "trace" in result
    assert "conclusion" in result["trace"]


async def test_run_inference_default_strategy(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.run_inference",
        {"query": "Test query"},
    )
    assert "trace" in result


async def test_run_inference_with_plan(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.run_inference",
        {"query": "Plan something", "include_plan": True},
    )
    assert "trace" in result
    assert "plan" in result


async def test_run_inference_without_plan(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.run_inference",
        {"query": "No plan needed", "include_plan": False},
    )
    assert result["plan"] is None


async def test_create_plan_returns_plan(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.create_plan",
        {"goal": "Build something useful"},
    )
    assert "goal" in result
    assert "steps" in result


async def test_create_plan_with_context(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.create_plan",
        {"goal": "Achieve X", "context": ["Resource A"]},
    )
    assert isinstance(result["steps"], list)


async def test_query_traces_returns_list(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.query_traces",
        {"query": "past reasoning about X"},
    )
    assert isinstance(result, list)


async def test_query_traces_with_n_results(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "reasoning.query_traces",
        {"query": "test", "n_results": 3},
    )
    assert isinstance(result, list)


async def test_unknown_tool_raises_value_error(mcp_tools: MCPTools) -> None:
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await mcp_tools.handle("reasoning.nonexistent", {})
