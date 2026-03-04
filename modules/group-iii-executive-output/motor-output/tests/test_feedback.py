"""test_feedback.py — Unit tests for FeedbackEmitter."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
import respx
from httpx import Response

from motor_output.feedback import FeedbackEmitter, _compute_deviation
from motor_output.models import ActionSpec, ChannelType


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def emitter() -> FeedbackEmitter:
    return FeedbackEmitter(executive_agent_url="http://localhost:8161")


# ── Deviation score ────────────────────────────────────────────────────────────

def test_deviation_no_prediction_is_neutral() -> None:
    score = _compute_deviation(None, {"success": True})
    assert score == 0.5


def test_deviation_perfect_match_is_zero() -> None:
    score = _compute_deviation({"success": True}, {"success": True})
    assert score == 0.0


def test_deviation_total_mismatch() -> None:
    score = _compute_deviation({"a": 1}, {"b": 2})
    # 0 intersection, union=2 → key_score=0, similarity=0 → deviation=1.0
    assert score == 1.0


def test_deviation_partial_match() -> None:
    score = _compute_deviation({"a": 1, "b": 2}, {"a": 1, "c": 3})
    assert 0.0 < score < 1.0


# ── FeedbackEmitter.build_feedback ─────────────────────────────────────────────

def test_build_feedback_success(emitter: FeedbackEmitter) -> None:
    spec = ActionSpec(
        action_id="act-001",
        type="test.call",
        channel=ChannelType.HTTP,
        goal_id="goal-001",
        predicted_outcome={"success": True},
    )
    result = {"success": True, "http_status": 200}
    fb = emitter.build_feedback(spec, result, dispatched_at=_now())
    assert fb.action_id == "act-001"
    assert fb.success is True
    assert fb.deviation_score <= 0.5  # close to predicted


def test_build_feedback_failure_sets_escalate(emitter: FeedbackEmitter) -> None:
    spec = ActionSpec(
        action_id="act-002",
        type="test.call",
        channel=ChannelType.HTTP,
        goal_id="goal-002",
        predicted_outcome={"success": True, "http_status": 200},
    )
    result = {"success": False, "error": "conn refused"}
    fb = emitter.build_feedback(spec, result, dispatched_at=_now())
    assert fb.success is False
    assert fb.escalate is True  # deviation > 0.8


# ── FeedbackEmitter.emit ─────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_emit_posts_to_executive(emitter: FeedbackEmitter) -> None:
    respx.post("http://localhost:8161/tasks").mock(return_value=Response(200, json={"jsonrpc": "2.0", "id": "act-003", "result": {}}))
    spec = ActionSpec(
        action_id="act-003",
        type="test.call",
        channel=ChannelType.HTTP,
        goal_id="goal-003",
    )
    fb = emitter.build_feedback(spec, {"success": True}, dispatched_at=_now())
    await emitter.emit(fb)  # should not raise


@pytest.mark.asyncio
async def test_emit_tolerates_failure(emitter: FeedbackEmitter) -> None:
    """emit() must not raise even if executive-agent is unreachable."""
    spec = ActionSpec(
        action_id="act-004",
        type="test.call",
        channel=ChannelType.HTTP,
        goal_id="goal-004",
    )
    fb = emitter.build_feedback(spec, {"success": True}, dispatched_at=_now())
    # No mock — connection will fail, but emit() should log and continue
    await emitter.emit(fb)  # must not raise


@pytest.mark.asyncio
@respx.mock
async def test_preaction_signal_posted(emitter: FeedbackEmitter) -> None:
    respx.post("http://localhost:8161/tasks").mock(return_value=Response(200, json={"jsonrpc": "2.0", "id": "act-005", "result": {}}))
    spec = ActionSpec(
        action_id="act-005",
        type="test.preaction",
        channel=ChannelType.HTTP,
    )
    await emitter.emit_preaction_signal(spec)
