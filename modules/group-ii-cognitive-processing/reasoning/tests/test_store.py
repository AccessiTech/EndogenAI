"""Unit tests for ReasoningStore.

ChromaAdapter is mocked — no live ChromaDB calls are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, MemoryType, QueryResponse, QueryResult

from reasoning.models import CausalPlan, InferenceTrace, ReasoningStrategy
from reasoning.store import COLLECTION_NAME, ReasoningStore


def _make_memory_item(item_id: str = "test-id", content: str = "sample content") -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name=COLLECTION_NAME,
        content=content,
        type=MemoryType.WORKING,
        source_module="reasoning",
        importance_score=0.7,
        created_at="2026-01-01T00:00:00+00:00",
        metadata={},
    )


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=None)
    adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    return adapter


@pytest.fixture
def store(mock_adapter: MagicMock) -> ReasoningStore:
    return ReasoningStore(adapter=mock_adapter)


@pytest.fixture
def sample_trace() -> InferenceTrace:
    return InferenceTrace(
        query="What causes climate change?",
        context=["CO2 emissions data"],
        chain_of_thought=["Step 1: greenhouse gases trap heat."],
        conclusion="Greenhouse gas emissions are the primary driver.",
        confidence=0.85,
        strategy=ReasoningStrategy.CAUSAL,
    )


@pytest.fixture
def sample_plan() -> CausalPlan:
    return CausalPlan(
        goal="Reduce carbon emissions by 50%",
        steps=["Increase renewables", "Reduce coal usage", "Carbon capture"],
        uncertainty=0.4,
        horizon=5,
    )


class TestReasoningStoreTrace:
    """Tests for storing and querying InferenceTrace objects."""

    @pytest.mark.asyncio
    async def test_store_trace_calls_upsert(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_trace: InferenceTrace
    ) -> None:
        returned_id = await store.store_trace(sample_trace)
        assert returned_id == sample_trace.id
        mock_adapter.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_trace_upsert_contains_trace_id(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_trace: InferenceTrace
    ) -> None:
        await store.store_trace(sample_trace)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        assert upsert_request.items[0].id == sample_trace.id

    @pytest.mark.asyncio
    async def test_store_trace_collection_name_is_correct(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_trace: InferenceTrace
    ) -> None:
        await store.store_trace(sample_trace)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        assert upsert_request.collection_name == COLLECTION_NAME
        assert upsert_request.items[0].collection_name == COLLECTION_NAME

    @pytest.mark.asyncio
    async def test_store_trace_importance_score_reflects_confidence(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_trace: InferenceTrace
    ) -> None:
        await store.store_trace(sample_trace)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        assert upsert_request.items[0].importance_score == pytest.approx(sample_trace.confidence)

    @pytest.mark.asyncio
    async def test_store_trace_metadata_includes_strategy(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_trace: InferenceTrace
    ) -> None:
        await store.store_trace(sample_trace)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        metadata = upsert_request.items[0].metadata
        assert metadata["strategy"] == str(sample_trace.strategy)


class TestReasoningStorePlan:
    """Tests for storing CausalPlan objects."""

    @pytest.mark.asyncio
    async def test_store_plan_calls_upsert(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_plan: CausalPlan
    ) -> None:
        returned_id = await store.store_plan(sample_plan)
        assert returned_id == sample_plan.id
        mock_adapter.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_plan_collection_name(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_plan: CausalPlan
    ) -> None:
        await store.store_plan(sample_plan)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        assert upsert_request.collection_name == COLLECTION_NAME

    @pytest.mark.asyncio
    async def test_store_plan_uncertainty_in_metadata(
        self, store: ReasoningStore, mock_adapter: MagicMock, sample_plan: CausalPlan
    ) -> None:
        await store.store_plan(sample_plan)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        metadata = upsert_request.items[0].metadata
        assert float(metadata["uncertainty"]) == pytest.approx(sample_plan.uncertainty)

    @pytest.mark.asyncio
    async def test_store_plan_importance_inversely_proportional_to_uncertainty(
        self, store: ReasoningStore, mock_adapter: MagicMock
    ) -> None:
        plan = CausalPlan(goal="G.", steps=[], uncertainty=0.2)
        await store.store_plan(plan)
        upsert_request = mock_adapter.upsert.call_args[0][0]
        assert upsert_request.items[0].importance_score == pytest.approx(0.8)


class TestReasoningStoreQuery:
    """Tests for querying inference traces."""

    @pytest.mark.asyncio
    async def test_query_traces_returns_items(
        self, store: ReasoningStore, mock_adapter: MagicMock
    ) -> None:
        item = _make_memory_item("trace-1", "InferenceTrace query=test conclusion=answer")
        mock_adapter.query = AsyncMock(
            return_value=QueryResponse(results=[QueryResult(item=item, score=0.9)])
        )
        results = await store.query_traces("test query")
        assert len(results) == 1
        assert results[0].id == "trace-1"

    @pytest.mark.asyncio
    async def test_query_traces_empty_result(
        self, store: ReasoningStore, mock_adapter: MagicMock
    ) -> None:
        mock_adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
        results = await store.query_traces("no match query")
        assert results == []

    @pytest.mark.asyncio
    async def test_query_traces_passes_n_results(
        self, store: ReasoningStore, mock_adapter: MagicMock
    ) -> None:
        mock_adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
        await store.query_traces("query", n_results=3)
        query_request = mock_adapter.query.call_args[0][0]
        assert query_request.n_results == 3
