"""Shared pytest fixtures for the reasoning module tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter

from reasoning.a2a_handler import A2AHandler
from reasoning.inference import InferencePipeline
from reasoning.mcp_tools import MCPTools
from reasoning.models import InferenceTrace, ReasoningStrategy
from reasoning.planner import CausalPlanner
from reasoning.store import ReasoningStore


def make_inference_trace(
    query: str = "What causes X?",
    conclusion: str = "X is caused by Y.",
    confidence: float = 0.8,
    strategy: ReasoningStrategy = ReasoningStrategy.DEDUCTIVE,
) -> InferenceTrace:
    """Factory helper for InferenceTrace test instances."""
    return InferenceTrace(
        query=query,
        context=["Evidence A", "Evidence B"],
        chain_of_thought=["Step 1: analyse A", "Step 2: cross-reference B"],
        conclusion=conclusion,
        confidence=confidence,
        strategy=strategy,
        model_used="ollama/mistral",
    )


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=None)
    from endogenai_vector_store.models import QueryResponse
    adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    return adapter


@pytest.fixture
def reasoning_store(mock_adapter: MagicMock) -> ReasoningStore:
    return ReasoningStore(adapter=mock_adapter)


@pytest.fixture
def mock_pipeline() -> MagicMock:
    pipeline = MagicMock(spec=InferencePipeline)
    pipeline.run_inference = AsyncMock(return_value=make_inference_trace())
    return pipeline


@pytest.fixture
def mock_planner() -> MagicMock:
    from reasoning.models import CausalPlan
    planner = MagicMock(spec=CausalPlanner)
    planner.create_plan = AsyncMock(
        return_value=CausalPlan(
            goal="Test goal",
            steps=["Step A", "Step B"],
            uncertainty=0.3,
        )
    )
    return planner


@pytest.fixture
def mcp_tools(
    reasoning_store: ReasoningStore,
    mock_pipeline: MagicMock,
    mock_planner: MagicMock,
) -> MCPTools:
    return MCPTools(
        store=reasoning_store,
        pipeline=mock_pipeline,  # type: ignore[arg-type]
        planner=mock_planner,  # type: ignore[arg-type]
    )


@pytest.fixture
def a2a_handler(
    reasoning_store: ReasoningStore,
    mock_pipeline: MagicMock,
    mock_planner: MagicMock,
) -> A2AHandler:
    return A2AHandler(
        store=reasoning_store,
        pipeline=mock_pipeline,  # type: ignore[arg-type]
        planner=mock_planner,  # type: ignore[arg-type]
    )
