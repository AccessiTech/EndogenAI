"""Unit tests for WorkingMemoryStore."""

from __future__ import annotations

import pytest

from working_memory.store import WorkingMemoryStore, _compute_time_decay, _cosine_similarity

from .conftest import make_wm_item


def test_write_single_item(wm_store: WorkingMemoryStore) -> None:
    """Writing a single item should store it without eviction."""
    item = make_wm_item()
    evicted = wm_store.write(item)
    assert evicted is None
    assert len(wm_store.list_active()) == 1


def test_write_evicts_when_over_max_items() -> None:
    """Writing beyond maxItems should evict the lowest-priority item."""
    store = WorkingMemoryStore(max_items=2)
    for i in range(3):
        store.write(make_wm_item(item_id=f"item-{i}", importance_score=0.5))
    assert len(store.list_active()) <= 2


def test_read_increments_access_count(wm_store: WorkingMemoryStore) -> None:
    """read() should increment accessCount."""
    item = make_wm_item()
    wm_store.write(item)
    read_item = wm_store.read("wm-item-1")
    assert read_item is not None
    assert read_item.access_count == 1


def test_read_missing_returns_none(wm_store: WorkingMemoryStore) -> None:
    """read() for non-existent item returns None."""
    result = wm_store.read("does-not-exist")
    assert result is None


def test_evict_removes_item(wm_store: WorkingMemoryStore) -> None:
    """Explicit evict removes the item and returns it."""
    item = make_wm_item()
    wm_store.write(item)
    evicted = wm_store.evict("wm-item-1")
    assert evicted is not None
    assert evicted.id == "wm-item-1"
    assert len(wm_store.list_active()) == 0


def test_list_active_sorted_by_importance(wm_store: WorkingMemoryStore) -> None:
    """list_active() should return items sorted by importanceScore descending."""
    wm_store.write(make_wm_item("item-low", importance_score=0.3))
    wm_store.write(make_wm_item("item-high", importance_score=0.9))
    items = wm_store.list_active()
    assert items[0].importance_score >= items[1].importance_score


def test_compute_time_decay_returns_one_for_none() -> None:
    """time_decay returns 1.0 when no last_accessed_at is set."""
    decay = _compute_time_decay(None, half_life_seconds=300.0)
    assert decay == 1.0


def test_cosine_similarity_identical_vectors() -> None:
    """Cosine similarity of identical non-zero vectors is 1.0."""
    vec = [1.0, 2.0, 3.0]
    sim = _cosine_similarity(vec, vec)
    assert sim == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_none_returns_half() -> None:
    """Cosine similarity returns 0.5 when embeddings are unavailable."""
    sim = _cosine_similarity(None, None)
    assert sim == 0.5


def test_update_item(wm_store: WorkingMemoryStore) -> None:
    """update() patches the specified field."""
    item = make_wm_item()
    wm_store.write(item)
    updated = wm_store.update("wm-item-1", {"importance_score": 0.99})
    assert updated is not None
    assert updated.importance_score == pytest.approx(0.99)


def test_compound_priority_higher_for_low_importance(wm_store: WorkingMemoryStore) -> None:
    """High importance item should have lower eviction priority."""
    item_high = make_wm_item("high-1", importance_score=0.9)
    item_low = make_wm_item("low-1", importance_score=0.1)
    p_high = wm_store.compute_eviction_priority(item_high)
    p_low = wm_store.compute_eviction_priority(item_low)
    assert p_low > p_high
