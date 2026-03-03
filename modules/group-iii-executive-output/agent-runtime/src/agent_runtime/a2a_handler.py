"""a2a_handler.py — A2A inbound task handler for agent-runtime.

Handles JSON-RPC 2.0 task requests from executive-agent and other modules.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from agent_runtime.orchestrator import Orchestrator
    from agent_runtime.tool_registry import ToolRegistry

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def handle_task(
    task_type: str,
    payload: dict[str, Any],
    orchestrator: Orchestrator,
    tool_registry: ToolRegistry,
) -> dict[str, Any]:
    """Route inbound A2A task to the appropriate handler."""
    handlers = {
        "execute_intention": _handle_execute_intention,
        "abort_execution": _handle_abort_execution,
        "revise_plan": _handle_revise_plan,
        "get_status": _handle_get_status,
    }
    handler = handlers.get(task_type)
    if handler is None:
        raise ValueError(f"Unknown task_type: {task_type!r}")
    return await handler(payload, orchestrator, tool_registry)


async def _handle_execute_intention(
    payload: dict[str, Any],
    orchestrator: Orchestrator,
    tool_registry: ToolRegistry,
) -> dict[str, Any]:
    """Start Temporal Workflow (or Prefect fallback) for a committed intention."""
    goal_id = payload["goal_id"]
    context_payload = payload.get("context_payload", {})
    result = await orchestrator.execute_intention(goal_id, context_payload)
    logger.info("a2a.execute_intention", goal_id=goal_id, orchestrator=result.get("orchestrator"))
    return result


async def _handle_abort_execution(
    payload: dict[str, Any],
    orchestrator: Orchestrator,
    tool_registry: ToolRegistry,
) -> dict[str, Any]:
    """Send abort signal to a running workflow."""
    goal_id = payload["goal_id"]
    result = await orchestrator.abort_execution(goal_id)
    logger.info("a2a.abort_execution", goal_id=goal_id)
    return result


async def _handle_revise_plan(
    payload: dict[str, Any],
    orchestrator: Orchestrator,
    tool_registry: ToolRegistry,
) -> dict[str, Any]:
    """Send a plan revision Update to a running Temporal Workflow."""
    goal_id = payload["goal_id"]
    revised_pipeline = payload.get("revised_pipeline", {})
    workflow_id = orchestrator._build_workflow_id(goal_id)

    if orchestrator._temporal_client:
        try:
            handle = orchestrator._temporal_client.get_workflow_handle(workflow_id)
            ack: str = await handle.execute_update("revise_plan", args=[revised_pipeline])
            logger.info("a2a.revise_plan", goal_id=goal_id, ack=ack)
            return {"status": "revision_accepted", "ack": ack}
        except Exception as exc:
            logger.warning("a2a.revise_plan_failed", goal_id=goal_id, error=str(exc))
            return {"status": "revision_failed", "error": str(exc)}

    return {"status": "temporal_unavailable", "goal_id": goal_id}


async def _handle_get_status(
    payload: dict[str, Any],
    orchestrator: Orchestrator,
    tool_registry: ToolRegistry,
) -> dict[str, Any]:
    """Query execution status for a goal."""
    goal_id = payload["goal_id"]
    status = await orchestrator.get_execution_status(goal_id)
    result: dict[str, Any] = status.model_dump(mode="json")
    return result
