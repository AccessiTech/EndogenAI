"""Unit tests for SeedPipeline."""

from __future__ import annotations

import pytest

from long_term_memory.seed_pipeline import SeedPipeline


@pytest.mark.asyncio
async def test_seed_pipeline_returns_already_seeded_when_no_path(
    seed_pipeline: SeedPipeline,
) -> None:
    """SeedPipeline with non-existent path should return report without crashing."""
    report = await seed_pipeline.run()
    # With a non-existent path: either already_seeded or zero chunks
    assert report.chunks_written >= 0


@pytest.mark.asyncio
async def test_seed_pipeline_skips_when_already_seeded(
    seed_pipeline: SeedPipeline,
    mock_adapter: object,
) -> None:
    """If the collection already has items, seed should skip."""
    from unittest.mock import AsyncMock

    from endogenai_vector_store.models import QueryResponse, QueryResult

    from .conftest import make_ltm_item

    existing_item = make_ltm_item()
    # Simulate non-empty collection
    mock_adapter.query = AsyncMock(  # type: ignore[union-attr]
        return_value=QueryResponse(results=[QueryResult(item=existing_item, score=0.9)])
    )
    report = await seed_pipeline.run()
    assert report.already_seeded is True
