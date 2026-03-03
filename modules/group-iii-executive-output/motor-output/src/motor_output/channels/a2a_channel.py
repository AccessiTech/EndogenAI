"""a2a_channel.py — A2A delegation channel.

Corticospinal indirect pathway analogue: task delegation to another agent
via JSON-RPC 2.0 A2A protocol (endogenai-a2a).
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AChannel:
    """Dispatches ActionSpec params as an A2A JSON-RPC 2.0 task."""

    async def dispatch(
        self,
        params: dict[str, Any],
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        """Send an A2A task and return the result.

        Expected params keys:
          - a2a_url (required): target agent A2A endpoint
          - task_type (required): JSON-RPC method name
          - payload (optional): task payload
        """
        a2a_url: str = params.get("a2a_url", "")
        if not a2a_url:
            raise ValueError("A2AChannel.dispatch requires params['a2a_url']")
        task_type: str = params.get("task_type", "execute")
        payload: dict[str, Any] = params.get("payload", {})
        rpc_id = str(uuid4())

        rpc_body = {
            "jsonrpc": "2.0",
            "method": task_type,
            "id": rpc_id,
            "params": payload,
        }

        logger.debug("a2a_channel.dispatch", url=a2a_url, task_type=task_type)

        async with httpx.AsyncClient(timeout=float(timeout_seconds)) as client:
            resp = await client.post(a2a_url, json=rpc_body)
            resp.raise_for_status()
            body: dict[str, Any] = resp.json()

        if "error" in body:
            err = body["error"]
            logger.error("a2a_channel.rpc_error", task_type=task_type, error=err)
            return {
                "success": False,
                "error": str(err.get("message", err)),
                "a2a_url": a2a_url,
            }

        logger.info("a2a_channel.success", url=a2a_url, task_type=task_type)
        result: dict[str, Any] = body.get("result", {})
        return {
            "success": True,
            "result": result,
            "a2a_url": a2a_url,
        }
