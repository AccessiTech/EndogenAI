"""Unit tests for SemanticSearch."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import QueryResponse, QueryResult

from short_term_memory.search import SemanticSearch

from .conftest import make_item


@pytest.mark.asyncio
async def test_search_returns_items(mock_adapter: MagicMock) -> None:
    """search() should return items from QueryResponse."""
    item = make_item()
    mock_adapter.query = AsyncMock(
        return_value=QueryResponse(results=[QueryResult(item=item, score=0.85)])
    )
    search = SemanticSearch(adapter=mock_adapter)
    results = await search.search("session-abc", "test query")
    assert len(results) == 1
    assert results[0].id == "test-item-1"


@pytest.mark.asyncio
async def test_search_passes_session_filter(mock_adapter: MagicMock) -> None:
    """search() should pass session_id as a where filter."""
    mock_adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    search = SemanticSearch(adapter=mock_adapter)
    await search.search("my-session", "query", top_k=5)

    call_args = mock_adapter.query.call_args[0][0]
    assert call_args.where == {"session_id": "my-session"}
    assert call_args.n_results == 5


@pytest.mark.asyncio
async def test_search_empty_result(mock_adapter: MagicMock) -> None:
    """search() should return empty list when no results found."""
    mock_adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    search = SemanticSearch(adapter=mock_adapter)
    results = await search.search("session-empty", "anything")
    assert results == []
