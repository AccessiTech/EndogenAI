"""Unit tests for ConsolidationDispatcher."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_a2a import A2AClient

from working_memory.consolidation import ConsolidationDispatcher, _has_tulving_triple

from .conftest import make_wm_item


def test_has_tulving_triple_full() -> None:
    """Item with all three triple fields returns True."""
    item = make_wm_item()
    item.metadata["source_task_id"] = "task-1"
    assert _has_tulving_triple(item) is True


def test_has_tulving_triple_missing_source_task() -> None:
    """Item missing source_task_id returns False."""
    item = make_wm_item()
    assert _has_tulving_triple(item) is False


def _mock_a2a_client() -> A2AClient:
    """Build a MagicMock A2AClient with send_task stubbed."""
    mock = MagicMock(spec=A2AClient)
    mock.send_task = AsyncMock(return_value={"status": "ok"})
    return mock  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_dispatch_routes_to_stm_without_triple() -> None:
    """Item without Tulving triple should be routed to STM via A2AClient."""
    item = make_wm_item()
    mock_client = _mock_a2a_client()

    dispatcher = ConsolidationDispatcher(a2a_client=mock_client)
    target = await dispatcher.dispatch(item)

    assert target == "brain.short-term-memory"
    mock_client.send_task.assert_awaited_once_with(
        "consolidate_item", {"item": item.model_dump()}
    )


@pytest.mark.asyncio
async def test_dispatch_routes_to_episodic_with_triple() -> None:
    """Item with Tulving triple should be routed to episodic memory via A2AClient."""
    item = make_wm_item()
    item.metadata["source_task_id"] = "task-xyz"
    mock_client = _mock_a2a_client()

    dispatcher = ConsolidationDispatcher(a2a_client=mock_client)
    target = await dispatcher.dispatch(item)

    assert target == "brain.episodic-memory"
    mock_client.send_task.assert_awaited_once_with(
        "write_event", {"item": item.model_dump()}
    )


@pytest.mark.asyncio
async def test_dispatch_handles_a2a_error_gracefully() -> None:
    """Dispatch should swallow exceptions and still return the target collection."""
    item = make_wm_item()
    mock_client = MagicMock(spec=A2AClient)
    mock_client.send_task = AsyncMock(side_effect=Exception("network error"))

    dispatcher = ConsolidationDispatcher(a2a_client=mock_client)
    # Should NOT raise — exceptions are caught to avoid blocking eviction
    target = await dispatcher.dispatch(item)
    assert target == "brain.short-term-memory"
