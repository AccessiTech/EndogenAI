"""Unit tests for SQLFactStore."""

from __future__ import annotations

import pytest

from long_term_memory.models import SemanticFact
from long_term_memory.sql_store import SQLFactStore


def make_fact(
    entity_id: str = "entity-1",
    predicate: str = "is_a",
    object_value: str = "concept",
    importance: float = 0.7,
) -> SemanticFact:
    return SemanticFact(
        entity_id=entity_id,
        predicate=predicate,
        object_value=object_value,
        importance=importance,
        created_at="2026-03-01T12:00:00+00:00",
    )


@pytest.mark.asyncio
async def test_write_and_query_fact(sql_store: SQLFactStore) -> None:
    """Write a fact and retrieve it by entity_id."""
    fact = make_fact()
    fact_id = await sql_store.write_fact(fact)
    assert fact_id != ""

    facts = await sql_store.query_facts("entity-1")
    assert len(facts) == 1
    assert facts[0].predicate == "is_a"


@pytest.mark.asyncio
async def test_upsert_keeps_higher_importance(sql_store: SQLFactStore) -> None:
    """Duplicate fact should update importance to the higher value."""
    fact_low = make_fact(importance=0.4)
    await sql_store.write_fact(fact_low)

    fact_high = make_fact(importance=0.9)
    await sql_store.write_fact(fact_high)

    facts = await sql_store.query_facts("entity-1")
    assert len(facts) == 1
    assert facts[0].importance == pytest.approx(0.9, abs=1e-6)


@pytest.mark.asyncio
async def test_query_empty_entity(sql_store: SQLFactStore) -> None:
    """Query for unknown entity returns empty list."""
    facts = await sql_store.query_facts("nonexistent-entity")
    assert facts == []
