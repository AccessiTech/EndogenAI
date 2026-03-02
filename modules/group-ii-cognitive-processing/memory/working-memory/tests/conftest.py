"""Shared pytest fixtures for working memory tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import (
    MemoryItem,
    MemoryType,
    QueryResponse,
)

from working_memory.consolidation import ConsolidationDispatcher
from working_memory.loader import ContextLoader
from working_memory.store import WorkingMemoryStore


def make_wm_item(
    item_id: str = "wm-item-1",
    content: str = "An important context item for the active reasoning task.",
    session_id: str = "session-abc",
    importance_score: float = 0.8,
) -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name="brain.working-memory",
        content=content,
        type=MemoryType.WORKING,
        source_module="working-memory",
        importance_score=importance_score,
        created_at="2026-03-01T12:00:00+00:00",
        metadata={"session_id": session_id},
    )


@pytest.fixture
def wm_store() -> WorkingMemoryStore:
    return WorkingMemoryStore(max_items=5, token_budget=1000)


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    return adapter


@pytest.fixture
def loader(mock_adapter: MagicMock) -> ContextLoader:
    return ContextLoader(adapter=mock_adapter)


@pytest.fixture
def dispatcher() -> ConsolidationDispatcher:
    return ConsolidationDispatcher()
