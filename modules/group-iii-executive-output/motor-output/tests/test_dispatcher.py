"""test_dispatcher.py — Unit tests for the Dispatcher."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from motor_output.dispatcher import Dispatcher
from motor_output.error_policy import ErrorPolicy  # noqa: TC001
from motor_output.feedback import FeedbackEmitter  # noqa: TC001
from motor_output.models import ActionSpec, ChannelType, DispatchStatus, MotorFeedback


@pytest.fixture
def dispatcher_with_mocks(
    mock_error_policy: ErrorPolicy,
    mock_feedback_emitter: FeedbackEmitter,
) -> Dispatcher:
    """Dispatcher with mocked error policy and feedback emitter."""
    d = Dispatcher(
        error_policy=mock_error_policy,
        feedback_emitter=mock_feedback_emitter,
        corollary_discharge_enabled=False,
    )
    return d


@pytest.mark.asyncio
async def test_dispatch_http_success(
    dispatcher_with_mocks: Dispatcher, sample_action_spec: ActionSpec
) -> None:
    with patch.object(dispatcher_with_mocks._error_policy, "execute", new=AsyncMock(
        return_value={"success": True, "http_status": 200, "retry_count": 0}
    )):
        fb = await dispatcher_with_mocks.dispatch(sample_action_spec)
    assert isinstance(fb, MotorFeedback)
    assert fb.success is True
    assert fb.action_id == sample_action_spec.action_id


@pytest.mark.asyncio
async def test_dispatch_records_stored(
    dispatcher_with_mocks: Dispatcher, sample_action_spec: ActionSpec
) -> None:
    with patch.object(dispatcher_with_mocks._error_policy, "execute", new=AsyncMock(
        return_value={"success": True, "retry_count": 0}
    )):
        await dispatcher_with_mocks.dispatch(sample_action_spec)
    record = dispatcher_with_mocks.get_record(sample_action_spec.action_id)
    assert record is not None
    assert record.status == DispatchStatus.SUCCESS


@pytest.mark.asyncio
async def test_dispatch_failure_sets_failed_status(
    dispatcher_with_mocks: Dispatcher, sample_action_spec: ActionSpec
) -> None:
    with patch.object(dispatcher_with_mocks._error_policy, "execute", new=AsyncMock(
        return_value={"success": False, "error": "timeout", "retry_count": 3}
    )):
        await dispatcher_with_mocks.dispatch(sample_action_spec)
    record = dispatcher_with_mocks.get_record(sample_action_spec.action_id)
    assert record is not None
    assert record.status == DispatchStatus.FAILED


@pytest.mark.asyncio
async def test_dispatch_batch_returns_all_feedbacks(
    dispatcher_with_mocks: Dispatcher,
    sample_action_spec: ActionSpec,
    sample_a2a_spec: ActionSpec,
) -> None:
    with patch.object(dispatcher_with_mocks._error_policy, "execute", new=AsyncMock(
        return_value={"success": True, "retry_count": 0}
    )):
        results = await dispatcher_with_mocks.dispatch_batch([sample_action_spec, sample_a2a_spec])
    assert len(results) == 2
    assert all(isinstance(r, MotorFeedback) for r in results)


@pytest.mark.asyncio
async def test_dispatch_batch_partial_failure(
    dispatcher_with_mocks: Dispatcher,
    sample_action_spec: ActionSpec,
    sample_a2a_spec: ActionSpec,
) -> None:
    call_count = 0

    async def _side_effect(**kwargs: object) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("channel exploded")
        return {"success": True, "retry_count": 0}

    with patch.object(dispatcher_with_mocks._error_policy, "execute", new=AsyncMock(
        side_effect=_side_effect
    )):
        results = await dispatcher_with_mocks.dispatch_batch([sample_action_spec, sample_a2a_spec])
    assert len(results) == 2
    assert results[0].success is False  # failed item wrapped in error MotorFeedback
    assert results[1].success is True


def test_abort_pending_dispatch(
    dispatcher_with_mocks: Dispatcher, sample_action_spec: ActionSpec
) -> None:
    # Manually create a PENDING record
    from motor_output.models import DispatchRecord
    record = DispatchRecord(
        action_id=sample_action_spec.action_id,
        channel=ChannelType.HTTP,
        status=DispatchStatus.PENDING,
    )
    dispatcher_with_mocks._records[sample_action_spec.action_id] = record
    result = dispatcher_with_mocks.abort_dispatch(sample_action_spec.action_id)
    assert result is True
    assert record.status == DispatchStatus.ABORTED


def test_abort_missing_id_returns_false(dispatcher_with_mocks: Dispatcher) -> None:
    assert dispatcher_with_mocks.abort_dispatch("nonexistent") is False


def test_list_channels_returns_all_types(dispatcher_with_mocks: Dispatcher) -> None:
    channels = dispatcher_with_mocks.list_channels()
    channel_names = {c["channel"] for c in channels}
    assert {"http", "a2a", "file", "render"} == channel_names
