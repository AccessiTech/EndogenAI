"""a2a_handler.py — A2A JSON-RPC 2.0 task routing for metacognition module.

Inbound tasks:
  evaluate_output   Receives Phase 6 feedback; runs evaluator; persists to store.

Outbound tasks (dispatched by evaluator when correction needed):
  request_correction  → executive-agent A2A endpoint.

Usage::

    result = await handle_task(task_type, payload, evaluator, store)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from metacognition.evaluation.evaluator import EvaluateOutputPayload, MetacognitionEvaluator

if TYPE_CHECKING:
    from metacognition.store.monitoring_store import MonitoringStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def handle_task(
    task_type: str,
    payload: dict[str, Any],
    evaluator: MetacognitionEvaluator,
    store: MonitoringStore,
) -> dict[str, Any]:
    """Dispatch an inbound A2A task to the appropriate handler.

    Args:
        task_type: JSON-RPC method name (e.g. ``"evaluate_output"``).
        payload: Decoded JSON-RPC params dict.
        evaluator: Module-global MetacognitionEvaluator instance.
        store: Module-global MonitoringStore instance.

    Returns:
        Result dict to include in the JSON-RPC response.

    Raises:
        ValueError: If ``task_type`` is unknown.
    """
    if task_type == "evaluate_output":
        return await _handle_evaluate_output(payload, evaluator, store)

    raise ValueError(f"Unknown task_type: {task_type!r}")


async def _handle_evaluate_output(
    payload: dict[str, Any],
    evaluator: MetacognitionEvaluator,
    store: MonitoringStore,
) -> dict[str, Any]:
    """Handle the ``evaluate_output`` inbound task.

    Validates the payload, runs the evaluator, persists the evaluation to
    the ChromaDB store, and returns the evaluation as a dict.
    """
    try:
        ep = EvaluateOutputPayload.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("evaluate_output payload validation failed", error=str(exc))
        raise ValueError(f"Invalid evaluate_output payload: {exc}") from exc

    evaluation = await evaluator.evaluate(ep)

    # Best-effort store append — don't fail the A2A call on store errors
    try:
        await store.append(evaluation)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist evaluation to store", error=str(exc))

    return evaluation.model_dump()
