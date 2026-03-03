"""a2a_handler.py — A2A inbound task handling for motor-output.

Receives JSON-RPC 2.0 task objects from agent-runtime or executive-agent,
routes to the Dispatcher, and returns A2A-compliant response payloads.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from motor_output.dispatcher import Dispatcher

from motor_output.models import ActionSpec

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def handle_task(
    task_type: str,
    payload: dict[str, Any],
    dispatcher: Dispatcher,
) -> dict[str, Any]:
    """Route an inbound A2A task to the appropriate handler.

    Returns a JSON-serialisable dict suitable for a JSON-RPC 2.0 result field.
    """
    handlers: dict[str, Any] = {
        "dispatch_action": _dispatch_action,
        "get_status": _get_status,
        "abort_dispatch": _abort_dispatch,
        "dispatch_batch": _dispatch_batch,
    }
    handler = handlers.get(task_type)
    if handler is None:
        logger.warning("a2a.unknown_task_type", task_type=task_type)
        return {"error": f"Unknown task_type: {task_type}"}

    try:
        return await handler(payload, dispatcher)  # type: ignore[no-any-return]
    except Exception as exc:
        logger.error("a2a.handler_error", task_type=task_type, error=str(exc))
        return {"error": str(exc)}


# ── Handler functions ──────────────────────────────────────────────────────────

async def _dispatch_action(
    payload: dict[str, Any], dispatcher: Dispatcher
) -> dict[str, Any]:
    spec = ActionSpec.model_validate(payload)
    feedback = await dispatcher.dispatch(spec)
    return feedback.model_dump(mode="json")


async def _get_status(
    payload: dict[str, Any], dispatcher: Dispatcher
) -> dict[str, Any]:
    action_id: str = payload.get("action_id", "")
    record = dispatcher.get_record(action_id)
    if record is None:
        return {"error": f"No record for action_id={action_id}"}
    return record.model_dump(mode="json")


async def _abort_dispatch(
    payload: dict[str, Any], dispatcher: Dispatcher
) -> dict[str, Any]:
    action_id: str = payload.get("action_id", "")
    success = dispatcher.abort_dispatch(action_id)
    return {"aborted": success, "action_id": action_id}


async def _dispatch_batch(
    payload: dict[str, Any], dispatcher: Dispatcher
) -> dict[str, Any]:
    raw_specs: list[dict[str, Any]] = payload.get("action_specs", [])
    specs = [ActionSpec.model_validate(s) for s in raw_specs]
    feedbacks = await dispatcher.dispatch_batch(specs)
    return {"results": [f.model_dump(mode="json") for f in feedbacks]}
