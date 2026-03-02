"""Unit tests for LTMVectorStore."""

from __future__ import annotations

import pytest

from long_term_memory.vector_store import LTMVectorStore

from .conftest import make_ltm_item


@pytest.mark.asyncio
async def test_write_accepted_above_threshold(vector_store: LTMVectorStore) -> None:
    """Item with importanceScore >= 0.5 should be written."""
    item = make_ltm_item(importance_score=0.6)
    item_id = await vector_store.write(item)
    assert item_id == "ltm-item-1"


@pytest.mark.asyncio
async def test_write_rejected_below_threshold(vector_store: LTMVectorStore) -> None:
    """Item with importanceScore < 0.5 should raise ValueError."""
    item = make_ltm_item(importance_score=0.3)
    with pytest.raises(ValueError, match="importanceScore"):
        await vector_store.write(item)


@pytest.mark.asyncio
async def test_write_accepted_at_threshold(vector_store: LTMVectorStore) -> None:
    """Item with importanceScore == 0.5 should be accepted."""
    item = make_ltm_item(importance_score=0.5)
    item_id = await vector_store.write(item)
    assert item_id == "ltm-item-1"


@pytest.mark.asyncio
async def test_query_returns_empty_list(vector_store: LTMVectorStore) -> None:
    """Query with no results returns empty list."""
    results = await vector_store.query("test query")
    assert results == []


@pytest.mark.asyncio
async def test_delete_skips_empty_list(vector_store: LTMVectorStore) -> None:
    """delete() with empty list should not call the adapter."""
    await vector_store.delete([])
    # Should not raise or call adapter.delete
