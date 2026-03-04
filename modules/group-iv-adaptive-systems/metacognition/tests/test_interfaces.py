"""test_interfaces.py — Unit tests for metacognition interfaces module.

Covers:
  - interfaces/__init__.py (import coverage)
  - interfaces/a2a_handler.handle_task — evaluate_output, invalid payload, unknown task
  - interfaces/mcp_server — get_confidence_current, get_anomalies_recent, get_session_report
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the interfaces package itself for __init__ coverage
import metacognition.interfaces as ifaces
from metacognition.evaluation.evaluator import (
    EvaluateOutputPayload,
    MetacognitionEvaluator,
    MetacognitiveEvaluation,
    MonitoringConfig,
)
from metacognition.instrumentation.metrics import MetricsBundle
from metacognition.interfaces.a2a_handler import handle_task
from metacognition.interfaces.mcp_server import (
    get_anomalies_recent,
    get_confidence_current,
    get_session_report,
)
from metacognition.store.monitoring_store import MonitoringStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_metrics_bundle() -> MetricsBundle:
    """Return a MetricsBundle with all fields mocked."""
    gauge = MagicMock()
    counter = MagicMock()
    histogram = MagicMock()
    return MetricsBundle(
        task_confidence=gauge,
        deviation_score=gauge,
        reward_delta=histogram,
        task_success_rate=gauge,
        escalation_total=counter,
        retry_count=histogram,
        policy_denial_rate=gauge,
        deviation_zscore=gauge,
    )


def _make_evaluator() -> MetacognitionEvaluator:
    return MetacognitionEvaluator(
        config=MonitoringConfig(), metrics_bundle=_make_metrics_bundle()
    )


def _make_eval_payload(**kwargs) -> dict:
    base = {
        "goal_id": "g-1",
        "action_id": "a-1",
        "success": True,
        "escalate": False,
        "deviation_score": 0.1,
        "reward_value": 0.8,
        "task_type": "default",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# __init__ imports
# ---------------------------------------------------------------------------


def test_interfaces_init_exports() -> None:
    assert callable(ifaces.handle_task)
    assert isinstance(ifaces.MCP_TOOLS, list)
    assert isinstance(ifaces.MCP_RESOURCES, list)
    assert callable(ifaces.get_confidence_current)
    assert callable(ifaces.get_anomalies_recent)
    assert callable(ifaces.get_session_report)


# ---------------------------------------------------------------------------
# a2a_handler tests
# ---------------------------------------------------------------------------


async def test_evaluate_output_success() -> None:
    evaluator = _make_evaluator()
    store = MagicMock()
    store.append = AsyncMock(return_value=None)

    result = await handle_task(
        "evaluate_output",
        _make_eval_payload(),
        evaluator=evaluator,
        store=store,
    )
    assert "evaluation_id" in result
    assert "task_confidence" in result
    store.append.assert_awaited_once()


async def test_evaluate_output_store_error_does_not_fail() -> None:
    """Store error during evaluate_output is swallowed gracefully."""
    evaluator = _make_evaluator()
    store = MagicMock()
    store.append = AsyncMock(side_effect=RuntimeError("DB down"))

    result = await handle_task(
        "evaluate_output",
        _make_eval_payload(),
        evaluator=evaluator,
        store=store,
    )
    assert "evaluation_id" in result


async def test_evaluate_output_invalid_payload_raises() -> None:
    evaluator = _make_evaluator()
    store = MagicMock()

    with pytest.raises(ValueError, match="Invalid evaluate_output payload"):
        await handle_task(
            "evaluate_output",
            {"invalid": "data"},
            evaluator=evaluator,
            store=store,
        )


async def test_unknown_task_raises() -> None:
    evaluator = _make_evaluator()
    store = MagicMock()

    with pytest.raises(ValueError, match="Unknown task_type"):
        await handle_task("unknown_task", {}, evaluator=evaluator, store=store)


# ---------------------------------------------------------------------------
# mcp_server tests
# ---------------------------------------------------------------------------


async def test_get_confidence_current_returns_dict() -> None:
    evaluator = _make_evaluator()
    result = await get_confidence_current(evaluator)
    assert isinstance(result, dict)


async def test_get_anomalies_recent_returns_list() -> None:
    evaluator = _make_evaluator()
    result = await get_anomalies_recent(evaluator, n=5)
    assert isinstance(result, list)


async def test_get_session_report_returns_report() -> None:
    evaluator = _make_evaluator()
    result = await get_session_report(evaluator)
    assert "total_evaluations" in result
    assert "mean_task_confidence" in result


async def test_get_session_report_with_data() -> None:
    """Report reflects actual evaluation data."""
    evaluator = _make_evaluator()
    store = MagicMock()
    store.append = AsyncMock()
    await handle_task(
        "evaluate_output",
        _make_eval_payload(task_type="my_task"),
        evaluator=evaluator,
        store=store,
    )
    report = await get_session_report(evaluator)
    assert report["total_evaluations"] >= 1
