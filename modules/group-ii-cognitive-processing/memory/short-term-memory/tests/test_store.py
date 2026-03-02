"""Unit tests for ShortTermMemoryStore."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import UpsertResponse

from short_term_memory.models import ConsolidationReport
from short_term_memory.store import ShortTermMemoryStore

from .conftest import make_item


@pytest.mark.asyncio
async def test_write_novel_item_calls_adapter(store: ShortTermMemoryStore) -> None:
    """Novel item should be written to both ChromaDB and Redis."""
    item = make_item()
    item_id = await store.write(item)
    assert item_id == "test-item-1"


@pytest.mark.asyncio
async def test_write_novel_item_calls_redis_rpush(
    store: ShortTermMemoryStore,
    mock_redis: MagicMock,
) -> None:
    """Novel item should be appended to the Redis session list."""
    item = make_item(session_id="session-xyz")
    await store.write(item)
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_session_empty(store: ShortTermMemoryStore) -> None:
    """Empty Redis list returns empty list."""
    items = await store.get_by_session("unknown-session")
    assert items == []


@pytest.mark.asyncio
async def test_expire_session_deletes_redis_key(
    store: ShortTermMemoryStore,
    mock_redis: MagicMock,
) -> None:
    """expire_session should delete the Redis key."""
    report: ConsolidationReport = await store.expire_session("session-abc")
    mock_redis.delete.assert_called_once_with("session:session-abc")
    assert report.session_id == "session-abc"


@pytest.mark.asyncio
async def test_write_duplicate_boosts_importance(
    mock_redis: MagicMock,
    mock_adapter: MagicMock,
) -> None:
    """Duplicate item should boost the importanceScore of the existing item."""
    from endogenai_vector_store.models import QueryResponse, QueryResult

    from short_term_memory.novelty import NoveltyChecker

    existing_item = make_item(item_id="existing-1", importance_score=0.5)
    mock_adapter.query = AsyncMock(
        return_value=QueryResponse(
            results=[QueryResult(item=existing_item, score=0.95)]
        )
    )
    mock_adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=["existing-1"]))

    checker = NoveltyChecker(adapter=mock_adapter, threshold=0.9)
    store = ShortTermMemoryStore(
        redis_client=mock_redis,
        adapter=mock_adapter,
        novelty_checker=checker,
    )

    new_item = make_item(item_id="new-1", content="very similar content")
    returned_id = await store.write(new_item)

    assert returned_id == "existing-1"
    # importanceScore should have been boosted
    upsert_call_args = mock_adapter.upsert.call_args
    upserted_items = upsert_call_args[0][0].items
    assert upserted_items[0].importance_score == pytest.approx(0.55, abs=1e-6)
