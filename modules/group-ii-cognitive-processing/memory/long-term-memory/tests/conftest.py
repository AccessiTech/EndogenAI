"""Shared pytest fixtures for long-term memory tests."""

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

from long_term_memory.graph_store import KuzuGraphStore
from long_term_memory.retrieval import HybridRetrieval
from long_term_memory.seed_pipeline import SeedPipeline
from long_term_memory.sql_store import SQLFactStore
from long_term_memory.vector_store import LTMVectorStore


def make_ltm_item(
    item_id: str = "ltm-item-1",
    content: str = "A persistent semantic fact about the world.",
    importance_score: float = 0.75,
) -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name="brain.long-term-memory",
        content=content,
        type=MemoryType.LONG_TERM,
        source_module="long-term-memory",
        importance_score=importance_score,
        created_at="2026-03-01T12:00:00+00:00",
    )


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=["ltm-item-1"]))
    adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    adapter.delete = AsyncMock(return_value=DeleteResponse(deleted_ids=[]))
    return adapter


@pytest.fixture
def vector_store(mock_adapter: MagicMock) -> LTMVectorStore:
    return LTMVectorStore(adapter=mock_adapter)


@pytest.fixture
def sql_store(tmp_path: object) -> SQLFactStore:
    import tempfile

    db_path = tempfile.mktemp(suffix=".db")
    return SQLFactStore(db_path=db_path)


@pytest.fixture
def graph_store(tmp_path: object) -> KuzuGraphStore:
    import tempfile

    db_path = tempfile.mktemp(suffix=".kuzu")
    return KuzuGraphStore(db_path=db_path)


@pytest.fixture
def retrieval(vector_store: LTMVectorStore, sql_store: SQLFactStore) -> HybridRetrieval:
    return HybridRetrieval(vector_store=vector_store, sql_store=sql_store)


@pytest.fixture
def seed_pipeline(mock_adapter: MagicMock) -> SeedPipeline:
    return SeedPipeline(adapter=mock_adapter, seed_documents_path="/tmp/nonexistent_seed_docs/")
