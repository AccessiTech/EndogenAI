"""mcp_tools.py — MCP tool registrations for executive-agent.

Exposes BDI loop operations as MCP tools via the handle(tool_name, params)
dispatcher pattern (consistent with all Phase 5 modules).

Tools:
  executive_agent.push_goal         — Add a goal to the stack
  executive_agent.get_goal_stack    — Return ranked active goals
  executive_agent.evaluate_policy   — Run OPA evaluation
  executive_agent.update_identity   — Append identity delta
  executive_agent.abort_goal        — Transition goal to DEFERRED/FAILED
  executive_agent.get_drive_state   — Return affective drive variables
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

from executive_agent.models import DriveState, GoalItem, LifecycleState

if TYPE_CHECKING:
    from executive_agent.goal_stack import GoalStack
    from executive_agent.identity import IdentityManager
    from executive_agent.policy import PolicyEngine

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for executive-agent operations."""

    def __init__(
        self,
        goal_stack: GoalStack,
        policy: PolicyEngine,
        identity: IdentityManager,
        affective_client: Any | None = None,
    ) -> None:
        self._goal_stack = goal_stack
        self._policy = policy
        self._identity = identity
        self._affective = affective_client
        self._drive_state: DriveState = DriveState()

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name."""
        match tool_name:
            case "executive_agent.push_goal":
                return await self._push_goal(params)
            case "executive_agent.get_goal_stack":
                return await self._get_goal_stack(params)
            case "executive_agent.evaluate_policy":
                return await self._evaluate_policy(params)
            case "executive_agent.update_identity":
                return await self._update_identity(params)
            case "executive_agent.abort_goal":
                return await self._abort_goal(params)
            case "executive_agent.get_drive_state":
                return await self._get_drive_state(params)
            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")

    async def _push_goal(self, params: dict[str, Any]) -> dict[str, Any]:
        deadline = params.get("deadline")
        goal = GoalItem(
            description=params["description"],
            priority=float(params["priority"]),
            deadline=datetime.fromisoformat(deadline) if deadline else None,
            constraints=params.get("constraints", {}),
            goal_class=params.get("goal_class"),
            context_payload=params.get("context_payload", {}),
        )
        result = await self._goal_stack.push(goal)
        return result.model_dump(mode="json")

    async def _get_goal_stack(self, params: dict[str, Any]) -> dict[str, Any]:
        raw_states = params.get("filter_states")
        states = [LifecycleState(s) for s in raw_states] if raw_states else None
        goals = await self._goal_stack.get_all(filter_states=states)
        return {"goals": [g.model_dump(mode="json") for g in goals]}

    async def _evaluate_policy(self, params: dict[str, Any]) -> dict[str, Any]:
        package = params.get("package", "endogenai.actions")
        decision = await self._policy.evaluate_policy(
            package=package,
            rule="allow",
            input_data={
                "action": params["action"],
                "context": params.get("context", {}),
            },
        )
        return decision.model_dump(mode="json")

    async def _update_identity(self, params: dict[str, Any]) -> dict[str, Any]:
        delta: dict[str, Any] = params.get("delta", params)
        self_model = await self._identity.update_self_model(delta)
        return self_model.model_dump(mode="json")

    async def _abort_goal(self, params: dict[str, Any]) -> dict[str, Any]:
        goal_id: str = params["goal_id"]
        reason: str = params.get("reason", "abort requested via MCP")
        goal = await self._goal_stack.abort(goal_id, reason)
        return goal.model_dump(mode="json")

    async def _get_drive_state(self, params: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG002
        if self._affective is not None:
            try:
                result = await self._affective.send_task("get_drive_state", {})
                if isinstance(result, dict):
                    self._drive_state = DriveState(**result)
            except Exception as exc:
                logger.warning("mcp.drive_state_fetch_error", error=str(exc))
        return self._drive_state.model_dump(mode="json")
