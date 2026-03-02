"""Unit tests for HybridRetrieval."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store.models import QueryResponse, QueryResult

from long_term_memory.retrieval import HybridRetrieval

from .conftest import make_ltm_item


@pytest.mark.asyncio
async def test_query_returns_re_ranked_items(
    retrieval: HybridRetrieval,
    mock_adapter: MagicMock,
) -> None:
    """Items should be returned sorted by importanceScore descending."""
    item_low = make_ltm_item(item_id="low", importance_score=0.5)
    item_high = make_ltm_item(item_id="high", importance_score=0.9)

    mock_adapter.query = AsyncMock(
        return_value=QueryResponse(
            results=[
                QueryResult(item=item_low, score=0.8),
                QueryResult(item=item_high, score=0.7),
            ]
        )
    )
    results = await retrieval.query("test query", top_k=5)
    assert results[0].id == "high"
    assert results[1].id == "low"


@pytest.mark.asyncio
async def test_query_empty_result(retrieval: HybridRetrieval) -> None:
    """Empty vector search returns empty list."""
    results = await retrieval.query("something obscure", top_k=5)
    assert results == []
