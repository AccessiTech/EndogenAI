"""mcp_tools.py — MCP tool registrations for motor-output.

Exposes four tools that agent-runtime and executive-agent can call via the
Model Context Protocol SSE transport.
"""
from __future__ import annotations

from typing import Any

import structlog

from motor_output.dispatcher import Dispatcher  # noqa: TC001
from motor_output.models import ActionSpec

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """Registers and handles MCP tool calls for motor-output."""

    def __init__(self, dispatcher: Dispatcher) -> None:
        self._dispatcher = dispatcher

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return JSON-serialisable MCP tool descriptors."""
        return [
            {
                "name": "motor_output.dispatch_action",
                "description": "Dispatch an action to the appropriate output channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "string"},
                        "goal_id": {"type": "string"},
                        "type": {"type": "string"},
                        "channel": {"type": "string", "nullable": True},
                        "params": {"type": "object"},
                    },
                    "required": ["action_id", "type"],
                },
            },
            {
                "name": "motor_output.get_dispatch_status",
                "description": "Retrieve the status and feedback for a dispatched action.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "string"},
                    },
                    "required": ["action_id"],
                },
            },
            {
                "name": "motor_output.list_channels",
                "description": "List available output channels and their handler classes.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "motor_output.abort_dispatch",
                "description": "Attempt to abort a pending or retrying dispatch.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "string"},
                    },
                    "required": ["action_id"],
                },
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch an MCP tool call and return a JSON-serialisable result."""
        handlers: dict[str, Any] = {
            "motor_output.dispatch_action": self._dispatch_action,
            "motor_output.get_dispatch_status": self._get_dispatch_status,
            "motor_output.list_channels": self._list_channels,
            "motor_output.abort_dispatch": self._abort_dispatch,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        return await handler(arguments)  # type: ignore[no-any-return]

    # ── Handlers ──────────────────────────────────────────────────────────────

    async def _dispatch_action(self, args: dict[str, Any]) -> dict[str, Any]:
        try:
            spec = ActionSpec.model_validate(args)
            feedback = await self._dispatcher.dispatch(spec)
            return feedback.model_dump(mode="json")
        except Exception as exc:
            logger.error("mcp.dispatch_action.failed", error=str(exc))
            return {"error": str(exc)}

    async def _get_dispatch_status(self, args: dict[str, Any]) -> dict[str, Any]:
        action_id: str = args.get("action_id", "")
        record = self._dispatcher.get_record(action_id)
        if record is None:
            return {"error": f"No record for action_id={action_id}"}
        return record.model_dump(mode="json")

    async def _list_channels(self, _args: dict[str, Any]) -> dict[str, Any]:
        return {"channels": self._dispatcher.list_channels()}

    async def _abort_dispatch(self, args: dict[str, Any]) -> dict[str, Any]:
        action_id: str = args.get("action_id", "")
        success = self._dispatcher.abort_dispatch(action_id)
        return {"aborted": success, "action_id": action_id}
