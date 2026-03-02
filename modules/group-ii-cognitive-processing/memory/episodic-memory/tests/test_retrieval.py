"""Unit tests for EpisodicRetrieval."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from endogenai_vector_store.models import QueryResponse, QueryResult

from episodic_memory.retrieval import EpisodicRetrieval

from .conftest import make_event


@pytest.mark.asyncio
async def test_semantic_search_returns_items(
    episodic_retrieval: EpisodicRetrieval,
    mock_adapter: object,
) -> None:
    """search() should return items from QueryResponse."""
    event = make_event()
    mock_adapter.query = AsyncMock(  # type: ignore[union-attr]
        return_value=QueryResponse(results=[QueryResult(item=event, score=0.8)])
    )
    results = await episodic_retrieval.semantic_search("task completion")
    assert len(results) == 1
    assert results[0].id == "event-1"


@pytest.mark.asyncio
async def test_time_window_filter_excludes_out_of_range(
    episodic_retrieval: EpisodicRetrieval,
    mock_adapter: object,
) -> None:
    """Items outside the time window should be filtered out."""
    event = make_event()
    mock_adapter.query = AsyncMock(  # type: ignore[union-attr]
        return_value=QueryResponse(results=[QueryResult(item=event, score=0.8)])
    )
    results = await episodic_retrieval.semantic_search(
        "query",
        time_window_start="2027-01-01T00:00:00",  # item is 2026, so excluded
        time_window_end="2027-12-31T23:59:59",
    )
    assert results == []


@pytest.mark.asyncio
async def test_empty_search_result(episodic_retrieval: EpisodicRetrieval) -> None:
    """Empty result returns empty list."""
    results = await episodic_retrieval.semantic_search("unknown")
    assert results == []
