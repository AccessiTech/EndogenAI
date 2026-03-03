"""a2a_handler.py — A2A inbound task handlers for executive-agent.

Handles JSON-RPC 2.0 tasks received at POST /tasks from other modules.

Task types:
  commit_intention  — Push goal → COMMITTED; get workflow_id from agent-runtime
  receive_feedback  — Process MotorFeedback; close actor-critic loop
  abort_goal        — Transition goal to DEFERRED (BG hyperdirect analogue)
  get_identity      — Return current SelfModel

All outbound A2A calls use the shared endogenai_a2a A2AClient (JSON-RPC 2.0).
"""
from __future__ import annotations

from typing import Any

import structlog

from executive_agent.models import LifecycleState, MotorFeedback

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def handle_task(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch an inbound A2A task to the appropriate handler.

    Returns:
        JSON-serialisable result dict.

    Raises:
        ValueError: if task_type is unknown.
    """
    handlers = {
        "commit_intention": _handle_commit_intention,
        "receive_feedback": _handle_receive_feedback,
        "abort_goal": _handle_abort_goal,
        "get_identity": _handle_get_identity,
    }
    handler = handlers.get(task_type)
    if handler is None:
        raise ValueError(f"Unknown A2A task type: {task_type!r}")

    logger.info("a2a.task_received", task_type=task_type)
    return await handler(payload)


async def _handle_commit_intention(payload: dict[str, Any]) -> dict[str, Any]:
    """Commit a goal intention and delegate execution to agent-runtime.

    Input:  {goal_id, context_payload}
    Output: GoalItem with workflow_id
    """
    from executive_agent.server import get_goal_stack, get_runtime_client

    goal_id: str = payload["goal_id"]
    context_payload: dict[str, Any] = payload.get("context_payload", {})

    goal_stack = get_goal_stack()

    # Transition to COMMITTED
    await goal_stack.transition(goal_id, LifecycleState.COMMITTED)

    # Delegate to agent-runtime via A2A
    runtime = get_runtime_client()
    if runtime is not None:
        try:
            result = await runtime.send_task(
                "execute_intention",
                {"goal_id": goal_id, "context_payload": context_payload},
            )
            workflow_id = result.get("workflow_id") if isinstance(result, dict) else None
            if workflow_id:
                await goal_stack.transition(
                    goal_id, LifecycleState.EXECUTING, workflow_id=workflow_id
                )
            logger.info("a2a.intention_delegated", goal_id=goal_id, workflow_id=workflow_id)
        except Exception as exc:
            logger.error("a2a.runtime_delegation_error", goal_id=goal_id, error=str(exc))

    goal = await goal_stack.get(goal_id)
    return goal.model_dump(mode="json")


async def _handle_receive_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    """Receive MotorFeedback and update goal state + priority.

    Input:  {motor_feedback: MotorFeedback}
    Output: {goal_id, new_state, reward_signal}
    """
    from executive_agent.server import get_feedback_handler

    raw_feedback = payload.get("motor_feedback", payload)
    feedback = MotorFeedback.model_validate(raw_feedback)
    handler = get_feedback_handler()
    return await handler.receive_feedback(feedback)


async def _handle_abort_goal(payload: dict[str, Any]) -> dict[str, Any]:
    """BG hyperdirect pathway: abort a goal immediately.

    Input:  {goal_id, reason}
    Output: GoalItem with state=DEFERRED
    """
    from executive_agent.server import get_goal_stack

    goal_id: str = payload["goal_id"]
    reason: str = payload.get("reason", "abort requested via A2A")

    stack = get_goal_stack()
    goal = await stack.abort(goal_id, reason)
    logger.warning("a2a.goal_aborted", goal_id=goal_id, reason=reason)
    return goal.model_dump(mode="json")


async def _handle_get_identity(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the current SelfModel.

    Input:  {} (empty)
    Output: SelfModel dict
    """
    from executive_agent.server import get_identity_manager

    manager = get_identity_manager()
    return manager.get_self_model().model_dump(mode="json")
