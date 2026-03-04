"""test_a2a_handler.py — Unit tests for reasoning A2A task handler.

Covers all task types:
  - run_inference
  - create_plan
  - query_traces
  - run_full_reasoning (include_plan=False and True)
  - unknown task type raises ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from reasoning.a2a_handler import A2AHandler
from reasoning.models import InferenceTrace, ReasoningStrategy
from tests.conftest import make_inference_trace


async def test_run_inference_calls_pipeline(a2a_handler: A2AHandler, mock_pipeline: MagicMock) -> None:
    result = await a2a_handler.handle(
        "run_inference",
        {"query": "Why does X happen?", "context": ["Context A"]},
    )
    assert "query" in result
    assert "conclusion" in result
    mock_pipeline.run_inference.assert_awaited_once()


async def test_run_inference_default_strategy(a2a_handler: A2AHandler) -> None:
    result = await a2a_handler.handle(
        "run_inference",
        {"query": "Test"},
    )
    assert result["strategy"] == ReasoningStrategy.DEDUCTIVE


async def test_create_plan_calls_planner(a2a_handler: A2AHandler, mock_planner: MagicMock) -> None:
    result = await a2a_handler.handle(
        "create_plan",
        {"goal": "Achieve objective Y", "context": ["step 1"]},
    )
    assert "goal" in result
    assert "steps" in result
    mock_planner.create_plan.assert_awaited_once()


async def test_create_plan_stores_result(a2a_handler: A2AHandler) -> None:
    result = await a2a_handler.handle(
        "create_plan",
        {"goal": "Do something"},
    )
    assert isinstance(result["steps"], list)


async def test_query_traces_returns_items(a2a_handler: A2AHandler) -> None:
    result = await a2a_handler.handle(
        "query_traces",
        {"query": "search for reasoning", "n_results": 3},
    )
    assert "items" in result
    assert isinstance(result["items"], list)


async def test_query_traces_default_n_results(a2a_handler: A2AHandler) -> None:
    result = await a2a_handler.handle(
        "query_traces",
        {"query": "test"},
    )
    assert "items" in result


async def test_run_full_reasoning_no_plan(a2a_handler: A2AHandler) -> None:
    result = await a2a_handler.handle(
        "run_full_reasoning",
        {"query": "What is the best path?", "include_plan": False},
    )
    assert "trace" in result
    assert result["plan"] is None


async def test_run_full_reasoning_with_plan(
    a2a_handler: A2AHandler, mock_planner: MagicMock
) -> None:
    result = await a2a_handler.handle(
        "run_full_reasoning",
        {"query": "How to solve Z?", "include_plan": True},
    )
    assert "trace" in result
    assert result["plan"] is not None
    mock_planner.create_plan.assert_awaited_once()


async def test_unknown_task_raises_value_error(a2a_handler: A2AHandler) -> None:
    with pytest.raises(ValueError, match="Unknown A2A task type"):
        await a2a_handler.handle("nonexistent_task", {})


async def test_handler_stores_dependencies() -> None:
    store = MagicMock()
    pipeline = MagicMock()
    planner = MagicMock()
    h = A2AHandler(store=store, pipeline=pipeline, planner=planner)
    assert h._store is store
    assert h._pipeline is pipeline
    assert h._planner is planner
