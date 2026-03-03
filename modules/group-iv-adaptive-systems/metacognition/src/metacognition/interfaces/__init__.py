"""interfaces — A2A handler and MCP server for metacognition module."""

from metacognition.interfaces.a2a_handler import handle_task
from metacognition.interfaces.mcp_server import (
    MCP_RESOURCES,
    MCP_TOOLS,
    get_anomalies_recent,
    get_confidence_current,
    get_session_report,
)

__all__ = [
    "handle_task",
    "MCP_RESOURCES",
    "MCP_TOOLS",
    "get_anomalies_recent",
    "get_confidence_current",
    "get_session_report",
]
