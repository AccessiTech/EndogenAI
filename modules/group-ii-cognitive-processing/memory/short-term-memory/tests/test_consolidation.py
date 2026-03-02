"""Unit tests for ConsolidationPipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from short_term_memory.consolidation import ConsolidationPipeline, _compute_final_score

from .conftest import make_item


def test_compute_final_score_basic() -> None:
    """finalScore = importanceScore + accessCount*0.1 + affectiveValence*0.2."""
    item = make_item(importance_score=0.5)
    item.access_count = 2
    item.metadata["affective_valence"] = 0.5
    score = _compute_final_score(item)
    assert score == pytest.approx(0.5 + 0.2 + 0.1, abs=1e-6)


def test_compute_final_score_capped_at_one() -> None:
    """finalScore is capped at 1.0 regardless of component values."""
    item = make_item(importance_score=1.0)
    item.access_count = 10
    item.metadata["affective_valence"] = 1.0
    score = _compute_final_score(item)
    assert score == 1.0


@pytest.mark.asyncio
async def test_run_promotes_high_score_item_to_ltm(
    pipeline: ConsolidationPipeline,
    mock_redis: MagicMock,
    mock_ltm_adapter: MagicMock,
) -> None:
    """Items with finalScore >= 0.5 (no Tulving triple) should go to LTM."""
    item = make_item(importance_score=0.7, session_id="session-1")
    item_json = item.model_dump_json()
    mock_redis.lrange = AsyncMock(return_value=[item_json])

    report = await pipeline.run("session-1")
    assert report.promoted_ltm == 1
    assert report.promoted_episodic == 0
    mock_ltm_adapter.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_run_promotes_tulving_item_to_episodic(
    pipeline: ConsolidationPipeline,
    mock_redis: MagicMock,
    mock_episodic_adapter: MagicMock,
) -> None:
    """Items with Tulving triple and finalScore >= 0.5 should go to episodic."""
    item = make_item(importance_score=0.8, session_id="session-2")
    item.metadata["source_task_id"] = "task-xyz"
    item_json = item.model_dump_json()
    mock_redis.lrange = AsyncMock(return_value=[item_json])

    report = await pipeline.run("session-2")
    assert report.promoted_episodic == 1
    assert report.promoted_ltm == 0
    mock_episodic_adapter.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_run_deletes_low_score_item(
    pipeline: ConsolidationPipeline,
    mock_redis: MagicMock,
) -> None:
    """Items with finalScore < 0.5 should be counted as deleted."""
    item = make_item(importance_score=0.1, session_id="session-3")
    item_json = item.model_dump_json()
    mock_redis.lrange = AsyncMock(return_value=[item_json])

    report = await pipeline.run("session-3")
    assert report.deleted == 1
    assert report.promoted_ltm == 0
    assert report.promoted_episodic == 0
