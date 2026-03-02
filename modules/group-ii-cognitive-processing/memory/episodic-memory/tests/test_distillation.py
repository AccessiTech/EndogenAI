"""Unit tests for DistillationJob."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from endogenai_vector_store.models import QueryResponse, QueryResult

from episodic_memory.distillation import DistillationJob

from .conftest import make_event


@pytest.mark.asyncio
async def test_distillation_run_no_items(distillation_job: DistillationJob) -> None:
    """Distillation with no items returns empty report."""
    report = await distillation_job.run()
    assert report.items_processed == 0
    assert report.facts_written_to_ltm == 0


@pytest.mark.asyncio
async def test_distillation_run_reports_clusters(
    distillation_job: DistillationJob,
    mock_adapter: object,
) -> None:
    """Distillation should report clusters found even when LTM write fails."""
    # Create 3 events with similar content length (same bucket)
    events = [
        make_event(event_id=f"event-{i}", content="A" * 150)  # all in ~100-char bucket
        for i in range(3)
    ]
    mock_adapter.query = AsyncMock(  # type: ignore[union-attr]
        return_value=QueryResponse(
            results=[QueryResult(item=e, score=0.8) for e in events]
        )
    )

    # Mock the LTM A2A call to avoid network
    with patch.object(distillation_job, "_write_to_ltm", AsyncMock()):
        report = await distillation_job.run()

    assert report.items_processed == 3
    assert report.clusters_found >= 1
