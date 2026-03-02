"""Shared pytest fixtures for short-term memory tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import (
    DeleteResponse,
    MemoryItem,
    MemoryType,
    QueryResponse,
    UpsertResponse,
)

from short_term_memory.consolidation import ConsolidationPipeline
from short_term_memory.novelty import NoveltyChecker
from short_term_memory.search import SemanticSearch
from short_term_memory.store import ShortTermMemoryStore


def make_item(
    item_id: str = "test-item-1",
    content: str = "test content",
    session_id: str = "session-abc",
    importance_score: float = 0.7,
) -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name="brain.short-term-memory",
        content=content,
        type=MemoryType.SHORT_TERM,
        source_module="short-term-memory",
        importance_score=importance_score,
        created_at="2026-03-01T12:00:00+00:00",
        metadata={"session_id": session_id},
    )


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=["test-item-1"]))
    adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    adapter.delete = AsyncMock(return_value=DeleteResponse(deleted_ids=[]))
    return adapter


@pytest.fixture
def mock_ltm_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=["ltm-item-1"]))
    return adapter


@pytest.fixture
def mock_episodic_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=["episodic-item-1"]))
    return adapter


@pytest.fixture
def mock_redis() -> MagicMock:
    redis = MagicMock()
    redis.rpush = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.lrange = AsyncMock(return_value=[])
    redis.delete = AsyncMock(return_value=1)
    return redis


@pytest.fixture
def novelty_checker(mock_adapter: MagicMock) -> NoveltyChecker:
    return NoveltyChecker(adapter=mock_adapter)


@pytest.fixture
def store(
    mock_redis: MagicMock,
    mock_adapter: MagicMock,
    novelty_checker: NoveltyChecker,
) -> ShortTermMemoryStore:
    return ShortTermMemoryStore(
        redis_client=mock_redis,
        adapter=mock_adapter,
        novelty_checker=novelty_checker,
    )


@pytest.fixture
def pipeline(
    store: ShortTermMemoryStore,
    mock_ltm_adapter: MagicMock,
    mock_episodic_adapter: MagicMock,
) -> ConsolidationPipeline:
    return ConsolidationPipeline(
        store=store,
        ltm_adapter=mock_ltm_adapter,
        episodic_adapter=mock_episodic_adapter,
    )


@pytest.fixture
def search(mock_adapter: MagicMock) -> SemanticSearch:
    return SemanticSearch(adapter=mock_adapter)
