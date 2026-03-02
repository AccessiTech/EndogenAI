"""FastAPI server for the affective / motivational layer module.

Exposes three interfaces:
  POST /tasks                        JSON-RPC 2.0 → A2AHandler.handle()
  GET  /.well-known/agent-card.json  Serve module agent card
  GET  /sse                          MCP Server-Sent Events (FastMCP)

Environment variables:
  CHROMADB_URL      ChromaDB base URL (default: http://localhost:8000)
  WM_A2A_URL        Working-memory A2A endpoint (default: http://localhost:8201)
  A2A_PORT          A2A server port (default: 8205)
  MCP_PORT          MCP SSE port (default: 8305)
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from affective.a2a_handler import A2AHandler
from affective.drive import DriveStateMachine
from affective.mcp_tools import MCPTools
from affective.store import AffectiveStore
from affective.weighting import WeightingDispatcher

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"

_handler: A2AHandler | None = None
_mcp_tools: MCPTools | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise module components on startup; clean up on shutdown."""
    global _handler, _mcp_tools

    wm_url = os.getenv("WM_A2A_URL", "http://localhost:8201")

    store = AffectiveStore()
    drive_machine = DriveStateMachine()
    dispatcher = WeightingDispatcher(a2a_url=wm_url)

    _handler = A2AHandler(store=store, drive_machine=drive_machine, dispatcher=dispatcher)
    _mcp_tools = MCPTools(store=store, drive_machine=drive_machine, dispatcher=dispatcher)

    logger.info("affective.server.startup", wm_url=wm_url)
    yield
    logger.info("affective.server.shutdown")


app = FastAPI(title="affective", version="0.1.0", lifespan=lifespan)


@app.post("/tasks")
async def dispatch_task(request: Request) -> JSONResponse:
    """JSON-RPC 2.0 dispatcher for incoming A2A task delegations."""
    body: dict[str, Any] = await request.json()
    rpc_id: str = body.get("id", str(uuid.uuid4()))

    if "method" in body and body.get("method") == "tasks/send":
        params: dict[str, Any] = body.get("params", {})
        task_type: str = params.pop("task_type", "")
        payload = params
    else:
        task_type = body.pop("type", body.pop("task_type", ""))
        payload = body

    if _handler is None:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": "unavailable", "message": "Handler not initialised"}},
            status_code=503,
        )

    try:
        result = await _handler.handle(task_type, payload)
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
    except ValueError as exc:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": "invalid-input", "message": str(exc)}},
            status_code=400,
        )
    except Exception as exc:
        logger.exception("affective.server.task_error", task_type=task_type)
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": "internal-error", "message": str(exc)}},
            status_code=500,
        )


@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    """Serve the module agent card from the filesystem."""
    try:
        card = json.loads(_AGENT_CARD_PATH.read_text())
        return JSONResponse(card)
    except FileNotFoundError:
        return JSONResponse({"error": "agent-card.json not found"}, status_code=404)


@app.get("/sse")
async def sse_health() -> JSONResponse:
    """MCP SSE endpoint placeholder."""
    return JSONResponse({"status": "ok", "module": "affective", "protocol": "mcp-sse"})


@app.get("/health")
async def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok", "module": "affective"})


def main() -> None:
    """Entry point for the ``serve`` script."""
    port = int(os.getenv("A2A_PORT", "8205"))
    uvicorn.run("affective.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
