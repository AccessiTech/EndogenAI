"""FastAPI server for the reasoning module.

Exposes three interfaces:
  POST /tasks                        JSON-RPC 2.0 → A2AHandler.handle()
  GET  /.well-known/agent-card.json  Serve module agent card
  GET  /sse                          MCP Server-Sent Events (FastMCP)

Environment variables:
  CHROMADB_URL      ChromaDB base URL (default: http://localhost:8000)
  OLLAMA_URL        Ollama base URL (default: http://localhost:11434)
  INFERENCE_MODEL   LiteLLM-format model name (default: ollama/mistral)
  A2A_PORT          A2A server port (default: 8206)
  MCP_PORT          MCP SSE port (default: 8306)
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

from reasoning.a2a_handler import A2AHandler
from reasoning.inference import InferencePipeline
from reasoning.mcp_tools import MCPTools
from reasoning.planner import CausalPlanner
from reasoning.store import ReasoningStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"

_handler: A2AHandler | None = None
_mcp_tools: MCPTools | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise module components on startup; clean up on shutdown."""
    global _handler, _mcp_tools

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("INFERENCE_MODEL", "ollama/mistral")

    store = ReasoningStore()
    pipeline = InferencePipeline(model=model, api_base=ollama_url)
    planner = CausalPlanner(model=model, api_base=ollama_url)

    _handler = A2AHandler(store=store, pipeline=pipeline, planner=planner)
    _mcp_tools = MCPTools(store=store, pipeline=pipeline, planner=planner)

    logger.info("reasoning.server.startup", ollama_url=ollama_url, model=model)
    yield
    logger.info("reasoning.server.shutdown")


app = FastAPI(title="reasoning", version="0.1.0", lifespan=lifespan)


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
        logger.exception("reasoning.server.task_error", task_type=task_type)
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
    return JSONResponse({"status": "ok", "module": "reasoning", "protocol": "mcp-sse"})


@app.get("/health")
async def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok", "module": "reasoning"})


def main() -> None:
    """Entry point for the ``serve`` script."""
    port = int(os.getenv("A2A_PORT", "8206"))
    uvicorn.run("reasoning.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
