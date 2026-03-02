"""Unit tests for NoveltyChecker."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import QueryResponse, QueryResult

from short_term_memory.novelty import NoveltyChecker

from .conftest import make_item


@pytest.mark.asyncio
async def test_novel_item_returns_none(mock_adapter: MagicMock) -> None:
    """Item with no similar neighbours returns None."""
    checker = NoveltyChecker(adapter=mock_adapter, threshold=0.9)
    item = make_item()
    result = await checker.find_duplicate(item, "session-abc")
    assert result is None


@pytest.mark.asyncio
async def test_duplicate_returned_when_above_threshold(mock_adapter: MagicMock) -> None:
    """Item above threshold should be returned as duplicate."""
    existing = make_item(item_id="existing-1")
    mock_adapter.query = AsyncMock(
        return_value=QueryResponse(results=[QueryResult(item=existing, score=0.95)])
    )
    checker = NoveltyChecker(adapter=mock_adapter, threshold=0.9)
    item = make_item()
    result = await checker.find_duplicate(item, "session-abc")
    assert result is not None
    assert result.id == "existing-1"


@pytest.mark.asyncio
async def test_similar_but_below_threshold_returns_none(mock_adapter: MagicMock) -> None:
    """Item with similarity below threshold is treated as novel."""
    existing = make_item(item_id="existing-2")
    mock_adapter.query = AsyncMock(
        return_value=QueryResponse(results=[QueryResult(item=existing, score=0.7)])
    )
    checker = NoveltyChecker(adapter=mock_adapter, threshold=0.9)
    item = make_item()
    result = await checker.find_duplicate(item, "session-abc")
    assert result is None
