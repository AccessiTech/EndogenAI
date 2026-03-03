"""mcp_tools.py — MCP tool registrations for agent-runtime.

Exposes runtime operations as MCP tools via the handle(tool_name, params)
dispatcher pattern (consistent with all Phase 5/6 modules).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from agent_runtime.orchestrator import Orchestrator
    from agent_runtime.tool_registry import ToolRegistry

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for agent-runtime operations."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        tool_registry: ToolRegistry,
    ) -> None:
        self._orchestrator = orchestrator
        self._registry = tool_registry
        self._dispatch: dict[str, Any] = {
            "agent_runtime.decompose": self._decompose,
            "agent_runtime.execute_intention": self._execute_intention,
            "agent_runtime.get_execution_status": self._get_execution_status,
            "agent_runtime.abort_execution": self._abort_execution,
            "agent_runtime.list_tools": self._list_tools,
            "agent_runtime.register_tool": self._register_tool,
        }

    async def handle(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Dispatch to the named tool handler."""
        handler = self._dispatch.get(tool_name)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        result: dict[str, Any] = await handler(params)
        return result

    async def _decompose(self, params: dict[str, Any]) -> dict[str, Any]:
        """Decompose a goal into a SkillPipeline without executing."""
        from agent_runtime.decomposer import PipelineDecomposer

        goal_id = params["goal_id"]
        context_payload = params.get("context_payload", {})
        dec = PipelineDecomposer(tool_registry=self._registry)
        pipeline = await dec.decompose(
            goal_id=goal_id,
            description=context_payload.get("description", f"Goal {goal_id}"),
            context_payload=context_payload,
        )
        result: dict[str, Any] = pipeline.model_dump(mode="json")
        return result

    async def _execute_intention(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a committed intention via the orchestrator."""
        goal_id = params["goal_id"]
        context_payload = params.get("context_payload", {})
        result = await self._orchestrator.execute_intention(goal_id, context_payload)
        return result

    async def _get_execution_status(self, params: dict[str, Any]) -> dict[str, Any]:
        """Query execution status for a goal."""
        goal_id = params["goal_id"]
        status = await self._orchestrator.get_execution_status(goal_id)
        data: dict[str, Any] = status.model_dump(mode="json")
        return data

    async def _abort_execution(self, params: dict[str, Any]) -> dict[str, Any]:
        """Send abort signal to a running workflow."""
        goal_id = params["goal_id"]
        result = await self._orchestrator.abort_execution(goal_id)
        return result

    async def _list_tools(self, params: dict[str, Any]) -> dict[str, Any]:
        """Return registered skills, optionally filtered by capability."""
        capability_filter = params.get("capability_filter")
        skills = self._registry.get_all_skills()
        if capability_filter:
            skills = [s for s in skills if capability_filter in s.capabilities]
        return {
            "skills": [s.model_dump(mode="json") for s in skills],
            "total": len(skills),
        }

    async def _register_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        """Manually register a tool/skill."""
        from agent_runtime.models import SkillEntry

        entry = SkillEntry.model_validate(params)
        self._registry.register(entry)
        data: dict[str, Any] = entry.model_dump(mode="json")
        return data
