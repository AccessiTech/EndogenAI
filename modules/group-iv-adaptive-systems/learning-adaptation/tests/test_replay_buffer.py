"""tests/test_replay_buffer.py — Unit tests for ReplayBuffer.

Uses a mock ChromaAdapter — no live ChromaDB required.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from endogenai_vector_store.models import MemoryItem, MemoryType, QueryResult

from learning_adaptation.models import LearningAdaptationEpisode
from learning_adaptation.replay.buffer import (
    COLLECTION_NAME,
    ReplayBuffer,
    _episode_to_memory_item,
)


def make_episode(
    task_type: str = "default",
    reward: float = 1.0,
    done: bool = False,
) -> LearningAdaptationEpisode:
    return LearningAdaptationEpisode(
        episode_id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        episode_boundary="bdi_cycle",
        observation={
            "success_rate": 0.8,
            "mean_deviation": 0.1,
            "escalation_rate": 0.0,
            "task_type_onehot": [1.0, 0.0, 0.0, 0.0],
            "channel_success_rate": [0.9, 0.8, 0.7, 0.6, 0.5],
        },
        action={"goal_priority_deltas": [0.05, -0.05, 0.0, 0.1]},
        reward=reward,
        next_observation={
            "success_rate": 0.9,
            "mean_deviation": 0.05,
            "escalation_rate": 0.0,
        },
        done=done,
        task_type=task_type,
        priority=abs(reward),
    )


def make_memory_item(
    importance_score: float = 0.5,
    task_type: str = "default",
    reward: float = 0.5,
) -> MemoryItem:
    """Create a MemoryItem with episodic metadata for testing."""
    return MemoryItem(
        id=str(uuid.uuid4()),
        collection_name=COLLECTION_NAME,
        content=f"ep task={task_type}",
        type=MemoryType.EPISODIC,
        source_module="learning-adaptation",
        importance_score=importance_score,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        metadata={
            "task_type": task_type,
            "reward": reward,
            "priority": importance_score,
            "done": False,
            "episode_boundary": "bdi_cycle",
            "observation": "{}",
            "action": "{}",
            "next_observation": "{}",
        },
    )


def make_mock_adapter(stored_items: list[MemoryItem] | None = None) -> Any:
    """Create a mock ChromaAdapter returning QueryResult-wrapped items."""
    adapter = MagicMock()
    query_results = [QueryResult(item=item, score=0.9) for item in (stored_items or [])]

    async def mock_upsert(req: Any) -> Any:
        result = MagicMock()
        result.ids = [item.id for item in req.items]
        return result

    async def mock_query(req: Any) -> Any:
        result = MagicMock()
        limit = getattr(req, "n_results", len(query_results))
        result.results = query_results[:limit]
        return result

    async def mock_delete(req: Any) -> Any:
        result = MagicMock()
        return result

    adapter.upsert = mock_upsert
    adapter.query = mock_query
    adapter.delete = mock_delete
    return adapter


class TestReplayBufferAdd:
    @pytest.mark.asyncio
    async def test_add_calls_upsert_with_correct_collection(self) -> None:
        """add() should call upsert with collection_name=brain.learning-adaptation."""
        upsert_calls: list[Any] = []

        adapter = MagicMock()

        async def capture_upsert(req: Any) -> Any:
            upsert_calls.append(req)
            result = MagicMock()
            result.ids = [item.id for item in req.items]
            return result

        async def empty_query(req: Any) -> Any:
            result = MagicMock()
            result.results = []
            return result

        adapter.upsert = capture_upsert
        adapter.query = empty_query

        buf = ReplayBuffer(adapter=adapter, max_size=100)
        ep = make_episode()
        await buf.add(ep)

        assert len(upsert_calls) == 1
        req = upsert_calls[0]
        assert req.collection_name == COLLECTION_NAME
        assert len(req.items) == 1
        assert req.items[0].id == ep.episode_id

    @pytest.mark.asyncio
    async def test_add_stores_task_type_in_metadata(self) -> None:
        """add() should include task_type in the item metadata."""
        upsert_calls: list[Any] = []

        adapter = MagicMock()

        async def capture_upsert(req: Any) -> Any:
            upsert_calls.append(req)
            result = MagicMock()
            result.ids = ["test-id"]
            return result

        async def empty_query(req: Any) -> Any:
            result = MagicMock()
            result.results = []
            return result

        adapter.upsert = capture_upsert
        adapter.query = empty_query

        buf = ReplayBuffer(adapter=adapter, max_size=100)
        ep = make_episode(task_type="planning")
        await buf.add(ep)

        item = upsert_calls[0].items[0]
        assert item.metadata["task_type"] == "planning"

    @pytest.mark.asyncio
    async def test_add_triggers_eviction_when_over_max_size(self) -> None:
        """add() should call delete when size exceeds max_size."""
        # Simulate 5 existing items wrapped in QueryResult
        existing_items = [make_memory_item(importance_score=0.1) for _ in range(5)]
        existing_qr = [QueryResult(item=item, score=0.9) for item in existing_items]
        delete_calls: list[Any] = []

        adapter = MagicMock()

        async def mock_upsert(req: Any) -> Any:
            result = MagicMock()
            result.ids = [item.id for item in req.items]
            return result

        async def mock_query(req: Any) -> Any:
            result = MagicMock()
            result.results = existing_qr
            return result

        async def capture_delete(req: Any) -> Any:
            delete_calls.append(req)
            result = MagicMock()
            return result

        adapter.upsert = mock_upsert
        adapter.query = mock_query
        adapter.delete = capture_delete

        buf = ReplayBuffer(adapter=adapter, max_size=3)  # max 3, 5 exist → evict 2
        ep = make_episode()
        await buf.add(ep)

        assert len(delete_calls) >= 1  # eviction triggered


class TestReplayBufferSample:
    @pytest.mark.asyncio
    async def test_sample_returns_at_most_n_records(self) -> None:
        """sample(n) should return at most n records."""

        episodes = [make_episode(reward=float(i)) for i in range(10)]
        items = [_episode_to_memory_item(ep) for ep in episodes]

        adapter = make_mock_adapter(stored_items=items)
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        results = await buf.sample(5)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_sample_returns_empty_list_on_error(self) -> None:
        """sample() should return [] if adapter raises."""
        adapter = MagicMock()

        async def failing_query(req: Any) -> Any:
            raise RuntimeError("ChromaDB down")

        adapter.query = failing_query
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        results = await buf.sample(5)
        assert results == []

    @pytest.mark.asyncio
    async def test_sample_sorted_by_priority_descending(self) -> None:
        """sample() results should be sorted by priority descending."""

        low = make_episode(task_type="default", reward=0.1)
        low.priority = 0.1
        high = make_episode(task_type="query", reward=0.9)
        high.priority = 0.9
        mid = make_episode(task_type="action", reward=0.5)
        mid.priority = 0.5

        items = [
            _episode_to_memory_item(low),
            _episode_to_memory_item(high),
            _episode_to_memory_item(mid),
        ]
        adapter = make_mock_adapter(stored_items=items)
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        results = await buf.sample(3)
        if len(results) > 1:
            priorities = [r.priority for r in results]
            assert priorities == sorted(priorities, reverse=True)


class TestReplayBufferEvict:
    @pytest.mark.asyncio
    async def test_evict_lowest_calls_delete(self) -> None:
        """evict_lowest(n) should call adapter.delete with n IDs."""
        items = [
            make_memory_item(importance_score=float(i) / 10)
            for i in range(5)
        ]
        query_results = [QueryResult(item=item, score=0.9) for item in items]
        delete_calls: list[Any] = []

        adapter = MagicMock()

        async def mock_query(req: Any) -> Any:
            result = MagicMock()
            result.results = query_results
            return result

        async def capture_delete(req: Any) -> Any:
            delete_calls.append(req)
            result = MagicMock()
            return result

        adapter.query = mock_query
        adapter.delete = capture_delete

        buf = ReplayBuffer(adapter=adapter, max_size=100)
        await buf.evict_lowest(2)

        assert len(delete_calls) == 1
        assert len(delete_calls[0].ids) == 2


class TestReplayBufferStats:
    @pytest.mark.asyncio
    async def test_stats_returns_correct_counts(self) -> None:
        """stats() should return accurate total_episodes count."""

        episodes = [make_episode(task_type="default", reward=float(i) * 0.1) for i in range(3)]
        items = [_episode_to_memory_item(ep) for ep in episodes]
        adapter = make_mock_adapter(stored_items=items)
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        stats = await buf.stats()
        assert stats.total_episodes == 3
        assert isinstance(stats.mean_reward, float)

    @pytest.mark.asyncio
    async def test_stats_returns_zero_when_empty(self) -> None:
        """stats() on empty buffer returns zeroed stats."""
        adapter = make_mock_adapter(stored_items=[])
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        stats = await buf.stats()
        assert stats.total_episodes == 0
        assert stats.mean_reward == 0.0
        assert stats.top_task_type is None


class TestReplayBufferSize:
    @pytest.mark.asyncio
    async def test_size_returns_count(self) -> None:
        items = [make_memory_item() for _ in range(7)]
        adapter = make_mock_adapter(stored_items=items)
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        count = await buf.size()
        assert count == 7

    @pytest.mark.asyncio
    async def test_size_returns_zero_on_error(self) -> None:
        adapter = MagicMock()

        async def failing_query(req: Any) -> Any:
            raise RuntimeError("error")

        adapter.query = failing_query
        buf = ReplayBuffer(adapter=adapter, max_size=100)
        assert await buf.size() == 0
