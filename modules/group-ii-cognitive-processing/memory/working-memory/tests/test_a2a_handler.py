"""Unit tests for A2AHandler — covering apply_affective_boost delta semantics.

Ensures that reward_value is applied as a delta to the existing importance_score
and the result is clamped to [0.0, 1.0], not overwritten directly.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import QueryResponse

from tests.conftest import make_wm_item
from working_memory.a2a_handler import A2AHandler
from working_memory.consolidation import ConsolidationDispatcher
from working_memory.loader import ContextLoader
from working_memory.store import WorkingMemoryStore


def _make_handler(store: WorkingMemoryStore) -> A2AHandler:
    mock_adapter = MagicMock(spec=ChromaAdapter)
    mock_adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    loader = ContextLoader(adapter=mock_adapter)
    dispatcher = ConsolidationDispatcher()
    return A2AHandler(store=store, loader=loader, dispatcher=dispatcher)


@pytest.mark.asyncio
async def test_apply_affective_boost_adds_delta() -> None:
    """Positive reward_value should increase importance_score by the delta amount."""
    store = WorkingMemoryStore()
    item = make_wm_item("item-1", importance_score=0.5)
    store.write(item)

    handler = _make_handler(store)
    result = await handler.handle(
        "apply_affective_boost",
        {"item_id": "item-1", "reward_value": 0.3},
    )

    assert result["importance_score"] == pytest.approx(0.8, abs=1e-9)


@pytest.mark.asyncio
async def test_apply_affective_boost_negative_delta_decays() -> None:
    """Negative reward_value should decrease importance_score without going below 0."""
    store = WorkingMemoryStore()
    item = make_wm_item("item-2", importance_score=0.2)
    store.write(item)

    handler = _make_handler(store)
    result = await handler.handle(
        "apply_affective_boost",
        {"item_id": "item-2", "reward_value": -0.5},
    )

    assert result["importance_score"] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.asyncio
async def test_apply_affective_boost_clamps_at_one() -> None:
    """Result must not exceed 1.0 even with a large positive boost."""
    store = WorkingMemoryStore()
    item = make_wm_item("item-3", importance_score=0.9)
    store.write(item)

    handler = _make_handler(store)
    result = await handler.handle(
        "apply_affective_boost",
        {"item_id": "item-3", "reward_value": 0.5},
    )

    assert result["importance_score"] == pytest.approx(1.0, abs=1e-9)


@pytest.mark.asyncio
async def test_apply_affective_boost_missing_item_raises() -> None:
    """A ValueError should be raised when item_id does not exist in the store."""
    store = WorkingMemoryStore()
    handler = _make_handler(store)

    with pytest.raises(ValueError, match="Item not found"):
        await handler.handle(
            "apply_affective_boost",
            {"item_id": "nonexistent", "reward_value": 0.2},
        )
