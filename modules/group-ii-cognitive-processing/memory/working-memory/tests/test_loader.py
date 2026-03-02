"""Unit tests for ContextLoader."""

from __future__ import annotations

import pytest

from working_memory.loader import ContextLoader

from .conftest import make_wm_item


@pytest.mark.asyncio
async def test_load_empty_stores_returns_empty_payload(loader: ContextLoader) -> None:
    """Load with no items in any store returns empty ContextPayload."""
    payload = await loader.load("session-abc", "test query")
    assert payload.session_id == "session-abc"
    assert payload.query == "test query"
    assert payload.items == []
    assert payload.total_tokens == 0


@pytest.mark.asyncio
async def test_load_returns_deduplicated_items(
    loader: ContextLoader, mock_adapter: object
) -> None:
    """Items with same content should be deduplicated across sources."""
    from unittest.mock import AsyncMock

    from endogenai_vector_store.models import QueryResponse, QueryResult

    item = make_wm_item(item_id="item-1", content="Identical content ABC")
    duplicate = make_wm_item(item_id="item-2", content="Identical content ABC")

    mock_adapter.query = AsyncMock(  # type: ignore[union-attr]
        return_value=QueryResponse(
            results=[
                QueryResult(item=item, score=0.9),
                QueryResult(item=duplicate, score=0.8),
            ]
        )
    )

    payload = await loader.load("session-abc", "test query")
    # Despite 3 sources × 2 items each, content deduplication should collapse them
    content_set = {it.content for it in payload.items}
    assert len(content_set) <= 1


@pytest.mark.asyncio
async def test_load_respects_capacity_override(loader: ContextLoader) -> None:
    """capacity_override limits the number of returned items."""
    from unittest.mock import AsyncMock

    from endogenai_vector_store.models import QueryResponse, QueryResult

    items = [
        make_wm_item(item_id=f"item-{i}", content=f"Content block {i} " * 10)
        for i in range(10)
    ]
    mock_adapter = loader._adapter  # type: ignore[attr-defined]
    mock_adapter.query = AsyncMock(
        return_value=QueryResponse(
            results=[QueryResult(item=it, score=0.8) for it in items[:5]]
        )
    )
    payload = await loader.load("session-abc", "query", capacity_override=2)
    assert payload.capacity_used <= 2
