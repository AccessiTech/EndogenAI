"""test_a2a_handler.py — Unit tests for long-term memory A2A task handler.

Covers all task types:
  - write_item
  - query
  - write_fact
  - seed
  - unknown task type raises ValueError
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType

from long_term_memory.a2a_handler import A2AHandler
from long_term_memory.models import SemanticFact, SeedReport


def _make_memory_item(item_id: str = "ltm-001") -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name="brain.long-term-memory",
        content="A semantic fact.",
        type=MemoryType.LONG_TERM,
        source_module="test",
        importance_score=0.7,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )


def _make_fact(entity_id: str = "entity-1") -> SemanticFact:
    return SemanticFact(
        entity_id=entity_id,
        predicate="is_a",
        object_value="concept",
        importance=0.6,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )


@pytest.fixture
def handler() -> A2AHandler:
    vector_store = MagicMock()
    vector_store.write = AsyncMock(return_value="ltm-001")

    retrieval = MagicMock()
    retrieval.query = AsyncMock(return_value=[_make_memory_item()])

    sql_store = MagicMock()
    sql_store.write_fact = AsyncMock(return_value="fact-001")

    seed_pipeline = MagicMock()
    seed_pipeline.run = AsyncMock(
        return_value=SeedReport(chunks_written=5, already_seeded=False, source_path="/tmp/seeds")
    )

    return A2AHandler(
        vector_store=vector_store,
        retrieval=retrieval,
        sql_store=sql_store,
        seed_pipeline=seed_pipeline,
    )


async def test_write_item_returns_item_id(handler: A2AHandler) -> None:
    item = _make_memory_item()
    result = await handler.handle("write_item", {"item": item.model_dump()})
    assert result["item_id"] == "ltm-001"
    handler._vector_store.write.assert_awaited_once()


async def test_query_returns_items(handler: A2AHandler) -> None:
    result = await handler.handle(
        "query",
        {"query": "semantic facts about X", "top_k": 5},
    )
    assert "items" in result
    assert isinstance(result["items"], list)
    assert len(result["items"]) == 1
    handler._retrieval.query.assert_awaited_once_with(
        query_text="semantic facts about X",
        top_k=5,
        filters=None,
    )


async def test_query_default_top_k(handler: A2AHandler) -> None:
    result = await handler.handle("query", {"query": "test"})
    handler._retrieval.query.assert_awaited_once_with(
        query_text="test",
        top_k=10,
        filters=None,
    )


async def test_query_with_filters(handler: A2AHandler) -> None:
    result = await handler.handle(
        "query",
        {"query": "filtered", "filters": {"source_module": "reasoning"}},
    )
    handler._retrieval.query.assert_awaited_once_with(
        query_text="filtered",
        top_k=10,
        filters={"source_module": "reasoning"},
    )


async def test_write_fact_returns_fact_id(handler: A2AHandler) -> None:
    fact = _make_fact()
    result = await handler.handle("write_fact", {"fact": fact.model_dump()})
    assert result["fact_id"] == "fact-001"
    handler._sql_store.write_fact.assert_awaited_once()


async def test_seed_returns_report(handler: A2AHandler) -> None:
    result = await handler.handle("seed", {})
    assert result["chunks_written"] == 5
    assert result["already_seeded"] is False
    handler._seed_pipeline.run.assert_awaited_once()


async def test_unknown_task_raises_value_error(handler: A2AHandler) -> None:
    with pytest.raises(ValueError, match="Unknown A2A task type"):
        await handler.handle("nonexistent", {})


async def test_handler_stores_dependencies() -> None:
    vs = MagicMock()
    ret = MagicMock()
    sql = MagicMock()
    seed = MagicMock()
    h = A2AHandler(vector_store=vs, retrieval=ret, sql_store=sql, seed_pipeline=seed)
    assert h._vector_store is vs
    assert h._retrieval is ret
    assert h._sql_store is sql
    assert h._seed_pipeline is seed
