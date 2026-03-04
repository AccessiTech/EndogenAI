"""test_store.py — Unit tests for ExecutiveStore adapter.

Covers:
  - upsert_goal: successful upsert and error handling
  - upsert_identity_delta: successful upsert and error handling
  - search: successful query and error handling
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from executive_agent.models import GoalItem, LifecycleState
from executive_agent.store import ExecutiveStore


def _make_store() -> tuple[ExecutiveStore, MagicMock]:
    adapter = MagicMock()
    adapter.upsert = AsyncMock(return_value=None)
    adapter.query = AsyncMock(return_value=[{"id": "goal-1", "score": 0.9}])
    store = ExecutiveStore(adapter=adapter)
    return store, adapter


def _make_goal() -> GoalItem:
    return GoalItem(
        description="Achieve a useful outcome",
        priority=0.75,
        lifecycle_state=LifecycleState.EXECUTING,
    )


# ---------------------------------------------------------------------------
# upsert_goal
# ---------------------------------------------------------------------------


async def test_upsert_goal_calls_adapter() -> None:
    store, adapter = _make_store()
    goal = _make_goal()
    await store.upsert_goal(goal)
    adapter.upsert.assert_awaited_once()
    call_kwargs = adapter.upsert.await_args.kwargs
    assert call_kwargs["collection_name"] == "brain.executive-agent"
    assert goal.id in call_kwargs["ids"]


async def test_upsert_goal_metadata_contains_lifecycle_state() -> None:
    store, adapter = _make_store()
    goal = _make_goal()
    await store.upsert_goal(goal)
    meta = adapter.upsert.await_args.kwargs["metadatas"][0]
    assert meta["lifecycle_state"] == LifecycleState.EXECUTING


async def test_upsert_goal_adapter_error_is_swallowed() -> None:
    store, adapter = _make_store()
    adapter.upsert = AsyncMock(side_effect=RuntimeError("DB error"))
    goal = _make_goal()
    # Should not raise
    await store.upsert_goal(goal)


# ---------------------------------------------------------------------------
# upsert_identity_delta
# ---------------------------------------------------------------------------


async def test_upsert_identity_delta_calls_adapter() -> None:
    store, adapter = _make_store()
    await store.upsert_identity_delta({"agent_name": "exec-v2"})
    adapter.upsert.assert_awaited_once()
    call_kwargs = adapter.upsert.await_args.kwargs
    assert call_kwargs["collection_name"] == "brain.executive-agent"
    assert "identity_delta" in call_kwargs["metadatas"][0]["type"]


async def test_upsert_identity_delta_error_swallowed() -> None:
    store, adapter = _make_store()
    adapter.upsert = AsyncMock(side_effect=RuntimeError("timeout"))
    # Should not raise
    await store.upsert_identity_delta({"key": "value"})


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


async def test_search_returns_results() -> None:
    store, adapter = _make_store()
    results = await store.search("find relevant goals", n_results=3)
    assert isinstance(results, list)
    adapter.query.assert_awaited_once()


async def test_search_error_returns_empty_list() -> None:
    store, adapter = _make_store()
    adapter.query = AsyncMock(side_effect=RuntimeError("ChromaDB unreachable"))
    results = await store.search("test query")
    assert results == []


async def test_store_initialises_with_adapter() -> None:
    adapter = MagicMock()
    store = ExecutiveStore(adapter=adapter)
    assert store._adapter is adapter
