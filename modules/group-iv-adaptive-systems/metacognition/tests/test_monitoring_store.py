"""test_monitoring_store.py — Unit tests for MonitoringStore.

Tests:
  - Mock ChromaAdapter accepts append call
  - append() persists evaluation with correct metadata
  - query_recent() returns list
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metacognition.evaluation.evaluator import MetacognitiveEvaluation
from metacognition.store.monitoring_store import _COLLECTION, MonitoringStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_evaluation(
    task_type: str = "default",
    task_confidence: float = 0.85,
    deviation_zscore: float = 0.3,
    error_detected: bool = False,
) -> MetacognitiveEvaluation:
    return MetacognitiveEvaluation(
        task_type=task_type,
        task_confidence=task_confidence,
        deviation_score=0.2,
        deviation_zscore=deviation_zscore,
        success_rate=0.9,
        reward_delta=0.6,
        error_detected=error_detected,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_initialise_calls_create_collection() -> None:
    """initialise() calls create_collection on the adapter."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        instance = MagicMock()
        instance.create_collection = AsyncMock(return_value=MagicMock())
        MockAdapter.return_value = instance

        store = MonitoringStore(chromadb_url="http://localhost:8000")
        await store.initialise()

        instance.create_collection.assert_called_once()
        call_args = instance.create_collection.call_args[0][0]
        assert call_args.collection_name == _COLLECTION


@pytest.mark.asyncio
async def test_initialise_tolerates_existing_collection() -> None:
    """initialise() does not raise if create_collection raises (collection exists)."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        instance = MagicMock()
        instance.create_collection = AsyncMock(side_effect=Exception("already exists"))
        MockAdapter.return_value = instance

        store = MonitoringStore(chromadb_url="http://localhost:8000")
        # Should not raise
        await store.initialise()


@pytest.mark.asyncio
async def test_append_calls_upsert_with_correct_collection() -> None:
    """append() calls adapter.upsert with the brain.metacognition collection."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        instance = MagicMock()
        instance.upsert = AsyncMock(return_value=MagicMock())
        MockAdapter.return_value = instance

        store = MonitoringStore()
        evaluation = make_evaluation()
        await store.append(evaluation)

        instance.upsert.assert_called_once()
        upsert_req = instance.upsert.call_args[0][0]
        assert upsert_req.collection_name == _COLLECTION


@pytest.mark.asyncio
async def test_append_persists_correct_metadata() -> None:
    """append() passes evaluation fields as metadata to the upsert call."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        instance = MagicMock()
        instance.upsert = AsyncMock(return_value=MagicMock())
        MockAdapter.return_value = instance

        store = MonitoringStore()
        evaluation = make_evaluation(
            task_type="navigation",
            task_confidence=0.72,
            deviation_zscore=1.1,
            error_detected=False,
        )
        await store.append(evaluation)

        upsert_req = instance.upsert.call_args[0][0]
        assert len(upsert_req.items) == 1
        item = upsert_req.items[0]
        assert item.metadata["task_type"] == "navigation"
        assert item.metadata["task_confidence"] == pytest.approx(0.72)
        assert item.metadata["deviation_zscore"] == pytest.approx(1.1)
        assert item.metadata["error_detected"] is False


@pytest.mark.asyncio
async def test_append_uses_evaluation_id_as_document_id() -> None:
    """append() uses the evaluation's evaluation_id as the ChromaDB document id."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        instance = MagicMock()
        instance.upsert = AsyncMock(return_value=MagicMock())
        MockAdapter.return_value = instance

        store = MonitoringStore()
        evaluation = make_evaluation()
        await store.append(evaluation)

        upsert_req = instance.upsert.call_args[0][0]
        assert upsert_req.items[0].id == evaluation.evaluation_id


@pytest.mark.asyncio
async def test_query_recent_returns_list() -> None:
    """query_recent() returns a list (even when empty)."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        # Build mock query response using correct QueryResult/MemoryItem structure
        from endogenai_vector_store.models import MemoryItem, MemoryType

        mock_item = MemoryItem(
            id="test-id",
            collection_name="brain.metacognition",
            content="task_type=default confidence=0.8",
            type=MemoryType.LONG_TERM,
            source_module="metacognition",
            created_at="2026-03-02T00:00:00Z",
            metadata={"task_type": "default", "task_confidence": 0.8},
        )
        mock_result = MagicMock()
        mock_result.item = mock_item
        mock_result.score = 0.95

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        instance = MagicMock()
        instance.query = AsyncMock(return_value=mock_response)
        MockAdapter.return_value = instance

        store = MonitoringStore()
        results = await store.query_recent("default", n=5)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "test-id"


@pytest.mark.asyncio
async def test_query_recent_empty_response_returns_empty_list() -> None:
    """query_recent() returns [] when the adapter returns no results."""
    with patch("metacognition.store.monitoring_store.ChromaAdapter") as MockAdapter:
        mock_response = MagicMock()
        mock_response.results = []

        instance = MagicMock()
        instance.query = AsyncMock(return_value=mock_response)
        MockAdapter.return_value = instance

        store = MonitoringStore()
        results = await store.query_recent("default", n=5)
        assert results == []
