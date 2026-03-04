"""test_a2a_handler.py — Unit tests for agent-runtime A2A task handler.

Covers all 4 task types:
  - execute_intention
  - abort_execution
  - revise_plan
  - get_status
  - unknown task type raises ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_runtime.a2a_handler import handle_task
from agent_runtime.models import ExecutionStatus, PipelineStatus


def _make_orchestrator() -> MagicMock:
    orch = MagicMock()
    orch.execute_intention = AsyncMock(
        return_value={"workflow_id": "wf-001", "orchestrator": "temporal", "status": "running"}
    )
    orch.abort_execution = AsyncMock(
        return_value={"goal_id": "goal-1", "status": "aborted"}
    )
    orch.get_execution_status = AsyncMock(
        return_value=ExecutionStatus(
            goal_id="goal-1",
            workflow_id="wf-001",
            status=PipelineStatus.RUNNING,
        )
    )
    orch._temporal_client = None
    orch._build_workflow_id = MagicMock(return_value="wf-001")
    return orch


def _make_tool_registry() -> MagicMock:
    reg = MagicMock()
    reg.get_healthy_skills = MagicMock(return_value=[])
    return reg


# ---------------------------------------------------------------------------
# execute_intention
# ---------------------------------------------------------------------------


async def test_execute_intention_success() -> None:
    orch = _make_orchestrator()
    result = await handle_task(
        "execute_intention",
        {"goal_id": "goal-1", "context_payload": {"description": "Do something"}},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    assert result["workflow_id"] == "wf-001"
    orch.execute_intention.assert_awaited_once_with(
        "goal-1", {"description": "Do something"}
    )


async def test_execute_intention_default_context() -> None:
    orch = _make_orchestrator()
    await handle_task(
        "execute_intention",
        {"goal_id": "goal-2"},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    orch.execute_intention.assert_awaited_once_with("goal-2", {})


# ---------------------------------------------------------------------------
# abort_execution
# ---------------------------------------------------------------------------


async def test_abort_execution_success() -> None:
    orch = _make_orchestrator()
    result = await handle_task(
        "abort_execution",
        {"goal_id": "goal-1"},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    assert result["status"] == "aborted"
    orch.abort_execution.assert_awaited_once_with("goal-1")


# ---------------------------------------------------------------------------
# revise_plan (temporal unavailable path)
# ---------------------------------------------------------------------------


async def test_revise_plan_temporal_unavailable() -> None:
    orch = _make_orchestrator()
    orch._temporal_client = None

    result = await handle_task(
        "revise_plan",
        {"goal_id": "goal-1", "revised_pipeline": {"steps": []}},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    assert result["status"] == "temporal_unavailable"
    assert result["goal_id"] == "goal-1"


async def test_revise_plan_temporal_error() -> None:
    """Temporal handle update error is caught and returned gracefully."""
    temporal_client = MagicMock()
    handle = MagicMock()
    handle.execute_update = AsyncMock(side_effect=RuntimeError("connection timeout"))
    temporal_client.get_workflow_handle = MagicMock(return_value=handle)

    orch = _make_orchestrator()
    orch._temporal_client = temporal_client

    result = await handle_task(
        "revise_plan",
        {"goal_id": "goal-1", "revised_pipeline": {}},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    assert result["status"] == "revision_failed"


async def test_revise_plan_temporal_success() -> None:
    temporal_client = MagicMock()
    handle = MagicMock()
    handle.execute_update = AsyncMock(return_value="ack-123")
    temporal_client.get_workflow_handle = MagicMock(return_value=handle)

    orch = _make_orchestrator()
    orch._temporal_client = temporal_client

    result = await handle_task(
        "revise_plan",
        {"goal_id": "goal-1", "revised_pipeline": {"steps": ["step_a"]}},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    assert result["status"] == "revision_accepted"
    assert result["ack"] == "ack-123"


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


async def test_get_status_success() -> None:
    orch = _make_orchestrator()
    result = await handle_task(
        "get_status",
        {"goal_id": "goal-1"},
        orchestrator=orch,
        tool_registry=_make_tool_registry(),
    )
    assert result["goal_id"] == "goal-1"
    assert result["workflow_id"] == "wf-001"
    orch.get_execution_status.assert_awaited_once_with("goal-1")


# ---------------------------------------------------------------------------
# unknown task
# ---------------------------------------------------------------------------


async def test_unknown_task_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown task_type"):
        await handle_task(
            "nonexistent_task",
            {},
            orchestrator=_make_orchestrator(),
            tool_registry=_make_tool_registry(),
        )
