"""test_mcp_tools.py — Unit tests for long-term memory MCP tool handler.

Covers all tools:
  - ltm.write
  - ltm.query
  - ltm.write_fact
  - ltm.query_facts
  - ltm.write_edge
  - ltm.query_graph
  - ltm.run_seed_pipeline
  - unknown tool raises ValueError
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType

from long_term_memory.mcp_tools import MCPTools
from long_term_memory.models import GraphEdge, SemanticFact, SeedReport


def _make_item(item_id: str = "ltm-001") -> MemoryItem:
    return MemoryItem(
        id=item_id,
        collection_name="brain.long-term-memory",
        content="A fact.",
        type=MemoryType.LONG_TERM,
        source_module="test",
        importance_score=0.7,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )


def _make_fact() -> SemanticFact:
    return SemanticFact(
        entity_id="entity-1",
        predicate="is_a",
        object_value="concept",
        importance=0.6,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )


def _make_edge() -> GraphEdge:
    return GraphEdge(
        source_entity_id="entity-1",
        predicate="relates_to",
        target_entity_id="entity-2",
        strength=0.8,
    )


@pytest.fixture
def mcp_tools() -> MCPTools:
    vector_store = MagicMock()
    vector_store.write = AsyncMock(return_value="ltm-001")

    retrieval = MagicMock()
    retrieval.query = AsyncMock(return_value=[_make_item()])

    sql_store = MagicMock()
    sql_store.write_fact = AsyncMock(return_value="fact-001")
    sql_store.query_facts = AsyncMock(return_value=[_make_fact()])

    graph_store = MagicMock()
    graph_store.write_edge = MagicMock()
    graph_store.query_neighbours = MagicMock(return_value=[_make_edge()])

    seed_pipeline = MagicMock()
    seed_pipeline.run = AsyncMock(
        return_value=SeedReport(chunks_written=3, already_seeded=False, source_path="/tmp")
    )

    return MCPTools(
        vector_store=vector_store,
        retrieval=retrieval,
        sql_store=sql_store,
        graph_store=graph_store,
        seed_pipeline=seed_pipeline,
    )


async def test_ltm_write_returns_item_id(mcp_tools: MCPTools) -> None:
    item = _make_item()
    result = await mcp_tools.handle("ltm.write", {"item": item.model_dump()})
    assert result["item_id"] == "ltm-001"


async def test_ltm_query_returns_items(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("ltm.query", {"query": "what is X"})
    assert "items" in result
    assert len(result["items"]) == 1


async def test_ltm_query_with_top_k(mcp_tools: MCPTools) -> None:
    await mcp_tools.handle("ltm.query", {"query": "X", "top_k": 3})
    mcp_tools._retrieval.query.assert_awaited_once_with(
        query_text="X",
        top_k=3,
        filters=None,
    )


async def test_ltm_write_fact_returns_fact_id(mcp_tools: MCPTools) -> None:
    fact = _make_fact()
    result = await mcp_tools.handle("ltm.write_fact", {"fact": fact.model_dump()})
    assert result["fact_id"] == "fact-001"


async def test_ltm_query_facts_returns_facts(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("ltm.query_facts", {"entity_id": "entity-1"})
    assert "facts" in result
    assert len(result["facts"]) == 1


async def test_ltm_write_edge_returns_ok(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "ltm.write_edge",
        {"src": "entity-1", "predicate": "relates_to", "dst": "entity-2"},
    )
    assert result["status"] == "ok"
    mcp_tools._graph_store.write_edge.assert_called_once_with(
        src="entity-1",
        predicate="relates_to",
        dst="entity-2",
        strength=1.0,
    )


async def test_ltm_write_edge_custom_strength(mcp_tools: MCPTools) -> None:
    await mcp_tools.handle(
        "ltm.write_edge",
        {"src": "A", "predicate": "rel", "dst": "B", "strength": 0.5},
    )
    mcp_tools._graph_store.write_edge.assert_called_once_with(
        src="A", predicate="rel", dst="B", strength=0.5
    )


async def test_ltm_query_graph_returns_edges(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle(
        "ltm.query_graph",
        {"entity_id": "entity-1", "depth": 2},
    )
    assert "edges" in result
    assert len(result["edges"]) == 1


async def test_ltm_run_seed_pipeline_returns_report(mcp_tools: MCPTools) -> None:
    result = await mcp_tools.handle("ltm.run_seed_pipeline", {})
    assert result["chunks_written"] == 3
    mcp_tools._seed_pipeline.run.assert_awaited_once()


async def test_unknown_tool_raises_value_error(mcp_tools: MCPTools) -> None:
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await mcp_tools.handle("ltm.nonexistent", {})
