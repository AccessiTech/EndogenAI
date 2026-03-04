"""test_mcp_tools.py — Unit tests for executive-agent MCP tool handler.

Covers all 6 tools:
  - executive_agent.push_goal
  - executive_agent.get_goal_stack
  - executive_agent.evaluate_policy
  - executive_agent.update_identity
  - executive_agent.abort_goal
  - executive_agent.get_drive_state (with and without affective client)
  - unknown tool raises ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from executive_agent.goal_stack import GoalStack
from executive_agent.identity import IdentityManager
from executive_agent.mcp_tools import MCPTools
from executive_agent.models import GoalItem, LifecycleState, PolicyDecision, SelfModel


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_goal(priority: float = 0.7) -> GoalItem:
    return GoalItem(description="Test goal", priority=priority)


def _make_self_model() -> SelfModel:
    return SelfModel(
        agent_name="exec",
        agent_version="0.1.0",
        core_values=["accuracy"],
        max_active_goals=5,
        deliberation_cycle_ms=500,
    )


@pytest.fixture
def mcp_tools() -> MCPTools:
    goal = _make_goal()
    self_model = _make_self_model()

    goal_stack = MagicMock(spec=GoalStack)
    goal_stack.push = AsyncMock(return_value=goal)
    goal_stack.get_all = AsyncMock(return_value=[goal])
    goal_stack.abort = AsyncMock(return_value=goal)

    policy = MagicMock()
    policy.evaluate_policy = AsyncMock(
        return_value=PolicyDecision(allow=True, violations=[], package="endogenai.actions", rule="allow")
    )

    identity = MagicMock(spec=IdentityManager)
    identity.update_self_model = AsyncMock(return_value=self_model)

    return MCPTools(goal_stack=goal_stack, policy=policy, identity=identity)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_push_goal(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "executive_agent.push_goal",
        {"description": "Do something important", "priority": 0.9},
    )
    assert "id" in result
    mcp_tools._goal_stack.push.assert_awaited_once()


async def test_push_goal_with_deadline(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "executive_agent.push_goal",
        {
            "description": "Deadline task",
            "priority": 0.6,
            "deadline": "2030-01-01T00:00:00+00:00",
        },
    )
    assert "id" in result


async def test_get_goal_stack(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("executive_agent.get_goal_stack", {})
    assert "goals" in result
    assert len(result["goals"]) == 1


async def test_get_goal_stack_with_filter(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "executive_agent.get_goal_stack",
        {"filter_states": ["PENDING"]},
    )
    assert "goals" in result
    mcp_tools._goal_stack.get_all.assert_awaited_once_with(
        filter_states=[LifecycleState.PENDING]
    )


async def test_evaluate_policy_allow(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "executive_agent.evaluate_policy",
        {"action": "push_goal", "context": {"priority": 0.8}},
    )
    assert result["allow"] is True
    assert "violations" in result


async def test_evaluate_policy_default_package(mcp_tools: MCPTools) -> None:
    await mcp_tools.handle(
        "executive_agent.evaluate_policy",
        {"action": "do_something"},
    )
    mcp_tools._policy.evaluate_policy.assert_awaited_once_with(
        package="endogenai.actions",
        rule="allow",
        input_data={"action": "do_something", "context": {}},
    )


async def test_update_identity(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "executive_agent.update_identity",
        {"delta": {"agent_name": "exec-v2"}},
    )
    assert result["agent_name"] == "exec"
    mcp_tools._identity.update_self_model.assert_awaited_once()


async def test_abort_goal(mcp_tools: MCPTools) -> None:
    goal = _make_goal()
    result = await mcp_tools.handle(
        "executive_agent.abort_goal",
        {"goal_id": goal.id, "reason": "user cancel"},
    )
    assert "id" in result
    mcp_tools._goal_stack.abort.assert_awaited_once_with(goal.id, "user cancel")


async def test_abort_goal_default_reason(mcp_tools: MCPTools) -> None:
    goal = _make_goal()
    await mcp_tools.handle(
        "executive_agent.abort_goal",
        {"goal_id": goal.id},
    )
    mcp_tools._goal_stack.abort.assert_awaited_once_with(
        goal.id, "abort requested via MCP"
    )


async def test_get_drive_state_no_affective(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("executive_agent.get_drive_state", {})
    assert "urgency" in result
    assert "valence" in result


async def test_get_drive_state_with_affective() -> None:
    goal = _make_goal()
    goal_stack = MagicMock()
    goal_stack.push = AsyncMock(return_value=goal)
    goal_stack.get_all = AsyncMock(return_value=[])
    goal_stack.abort = AsyncMock(return_value=goal)

    policy = MagicMock()
    policy.evaluate_policy = AsyncMock(return_value=PolicyDecision(allow=True, package="endogenai.actions", rule="allow"))

    identity = MagicMock()
    identity.update_self_model = AsyncMock(return_value=_make_self_model())

    affective_client = MagicMock()
    affective_client.send_task = AsyncMock(return_value={"urgency": 0.9, "valence": 0.5, "arousal": 0.7})

    tools = MCPTools(
        goal_stack=goal_stack,
        policy=policy,
        identity=identity,
        affective_client=affective_client,
    )
    result = await tools.handle("executive_agent.get_drive_state", {})
    assert result["urgency"] == 0.9


async def test_get_drive_state_affective_error() -> None:
    """Affective client error is swallowed; returns default DriveState."""
    goal_stack = MagicMock()
    policy = MagicMock()
    identity = MagicMock()
    affective_client = MagicMock()
    affective_client.send_task = AsyncMock(side_effect=RuntimeError("timeout"))

    tools = MCPTools(
        goal_stack=goal_stack,
        policy=policy,
        identity=identity,
        affective_client=affective_client,
    )
    result = await tools.handle("executive_agent.get_drive_state", {})
    assert "urgency" in result


async def test_unknown_tool_raises_value_error(mcp_tools: MCPTools) -> None:
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await mcp_tools.handle("executive_agent.nonexistent", {})
