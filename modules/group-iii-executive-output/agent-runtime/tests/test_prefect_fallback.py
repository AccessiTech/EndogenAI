"""Tests for prefect_fallback — sequential execution fallback."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from agent_runtime.models import ChannelType, PipelineStatus, SkillStep
from agent_runtime.prefect_fallback import _dispatch_step, _run_sequential, run_intention_flow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pipeline(steps: list[SkillStep]) -> MagicMock:
    pipeline = MagicMock()
    pipeline.steps = steps
    return pipeline


def _make_step(
    step_id: str = "step-01",
    tool_id: str = "skill.test",
    channel: str = "a2a",
    params: dict[str, Any] | None = None,
) -> SkillStep:
    return SkillStep(
        step_id=step_id,
        tool_id=tool_id,
        channel=ChannelType(channel),
        params=params or {},
        depends_on=[],
    )


# ---------------------------------------------------------------------------
# run_intention_flow (entry point)
# ---------------------------------------------------------------------------


async def test_run_intention_flow_uses_prefect_when_available() -> None:
    """run_intention_flow calls _run_with_prefect when Prefect is installed."""
    with patch(
        "agent_runtime.prefect_fallback._run_with_prefect",
        new=AsyncMock(return_value={"status": "completed", "goal_id": "g-1", "results": []}),
    ) as mock_pfct:
        result = await run_intention_flow("g-1", {})
    mock_pfct.assert_awaited_once()
    assert result["status"] == "completed"


async def test_run_intention_flow_falls_back_on_prefect_error() -> None:
    """run_intention_flow falls to _run_sequential when _run_with_prefect raises."""
    with (
        patch(
            "agent_runtime.prefect_fallback._run_with_prefect",
            new=AsyncMock(side_effect=RuntimeError("prefect error")),
        ),
        patch(
            "agent_runtime.prefect_fallback._run_sequential",
            new=AsyncMock(return_value={"status": "completed", "goal_id": "g-2", "results": []}),
        ) as mock_seq,
    ):
        result = await run_intention_flow("g-2", {})
    mock_seq.assert_awaited_once()
    assert result["goal_id"] == "g-2"


# ---------------------------------------------------------------------------
# _run_sequential
# ---------------------------------------------------------------------------


async def test_run_sequential_dispatches_each_step() -> None:
    """_run_sequential calls _dispatch_step for every step in the pipeline."""
    step = _make_step()
    pipeline = _make_pipeline([step])

    with (
        patch("agent_runtime.decomposer.PipelineDecomposer") as MockDec,
        patch(
            "agent_runtime.prefect_fallback._dispatch_step",
            new=AsyncMock(return_value={"success": True}),
        ) as mock_dispatch,
    ):
        MockDec.return_value.decompose = AsyncMock(return_value=pipeline)
        result = await _run_sequential(
            "goal-1",
            {"description": "run this"},
            "http://localhost:8163",
            "http://localhost:8161",
        )

    assert result["status"] == "completed"
    assert result["goal_id"] == "goal-1"
    assert len(result["results"]) == 1
    mock_dispatch.assert_awaited_once()


async def test_run_sequential_empty_pipeline() -> None:
    """_run_sequential returns completed with empty results for zero-step plan."""
    pipeline = _make_pipeline([])

    with patch("agent_runtime.decomposer.PipelineDecomposer") as MockDec:
        MockDec.return_value.decompose = AsyncMock(return_value=pipeline)
        result = await _run_sequential("goal-empty", {}, "http://localhost:8163", "http://localhost:8161")

    assert result["results"] == []
    assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# _dispatch_step
# ---------------------------------------------------------------------------


async def test_dispatch_step_returns_result_on_success() -> None:
    """_dispatch_step POSTs to motor-output and returns the result payload."""
    with respx.mock:
        respx.post("http://localhost:8163/tasks").mock(
            return_value=httpx.Response(200, json={"result": {"dispatched": True}})
        )
        step: dict[str, Any] = {
            "step_id": "step-01",
            "tool_id": "skill.test",
            "channel": "a2a",
            "params": {"key": "val"},
        }
        result = await _dispatch_step(step, "goal-1", "http://localhost:8163")

    assert result.get("dispatched") is True


async def test_dispatch_step_returns_empty_on_null_result() -> None:
    """_dispatch_step returns empty dict when response has no 'result' key."""
    with respx.mock:
        respx.post("http://localhost:8163/tasks").mock(
            return_value=httpx.Response(200, json={})
        )
        step: dict[str, Any] = {"step_id": "s", "tool_id": "t", "channel": "a2a", "params": {}}
        result = await _dispatch_step(step, "goal-x", "http://localhost:8163")

    assert isinstance(result, dict)


async def test_dispatch_step_returns_error_on_network_failure() -> None:
    """_dispatch_step returns error dict (no raise) on network failure."""
    with respx.mock:
        respx.post("http://localhost:8163/tasks").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        step: dict[str, Any] = {"step_id": "s", "tool_id": "t", "channel": "a2a", "params": {}}
        result = await _dispatch_step(step, "goal-err", "http://localhost:8163")

    assert result.get("success") is False
    assert "connection refused" in result.get("error", "")


async def test_dispatch_step_returns_error_on_http_error() -> None:
    """_dispatch_step returns error dict on 4xx/5xx response."""
    with respx.mock:
        respx.post("http://localhost:8163/tasks").mock(
            return_value=httpx.Response(500, json={"error": "internal"})
        )
        step: dict[str, Any] = {"step_id": "s", "tool_id": "t", "channel": "a2a", "params": {}}
        result = await _dispatch_step(step, "goal-500", "http://localhost:8163")

    assert result.get("success") is False
