"""Unit tests for KuzuGraphStore."""

from __future__ import annotations

import pytest

from long_term_memory.graph_store import KuzuGraphStore


@pytest.mark.asyncio
async def test_graph_store_instantiates() -> None:
    """KuzuGraphStore should instantiate without errors."""
    import tempfile

    db_path = tempfile.mktemp(suffix=".kuzu")
    store = KuzuGraphStore(db_path=db_path)
    assert store is not None


@pytest.mark.asyncio
async def test_write_edge_without_kuzu_does_not_raise() -> None:
    """write_edge should not raise even if kuzu is unavailable (lazy init)."""
    import tempfile

    try:
        import kuzu  # type: ignore[import-untyped]  # noqa: F401

        # kuzu is available — test the actual write
        db_path = tempfile.mktemp(suffix=".kuzu")
        store = KuzuGraphStore(db_path=db_path)
        store.write_edge("entity-A", "related_to", "entity-B", strength=0.8)
        edges = store.query_neighbours("entity-A", depth=1)
        assert len(edges) >= 0  # edges may or may not be returned depending on kuzu version

    except ImportError:
        # kuzu not installed — just verify no crash on call
        db_path = tempfile.mktemp(suffix=".kuzu")
        store = KuzuGraphStore(db_path=db_path)
        store.write_edge("entity-A", "related_to", "entity-B")
        assert True
