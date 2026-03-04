"""FastAPI server for the working memory module.

Exposes three interfaces:
  POST /tasks                     JSON-RPC 2.0 → A2AHandler.handle()
  GET  /.well-known/agent-card.json   Serve module agent card
  GET  /sse                       MCP Server-Sent Events (FastMCP)

Environment variables:
  CHROMADB_URL     ChromaDB base URL (default: http://localhost:8000)
  A2A_PORT         A2A server port (default: 8201)
  MCP_PORT         MCP SSE port (default: 8301)
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

from working_memory.a2a_handler import A2AHandler
from working_memory.consolidation import ConsolidationDispatcher
from working_memory.loader import ContextLoader
from working_memory.mcp_tools import MCPTools
from working_memory.store import WorkingMemoryStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Path to agent-card.json at module root (2 levels up from src/working_memory/)
_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"

# Global handler — initialised during lifespan startup
_handler: A2AHandler | None = None
_mcp_tools: MCPTools | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise module components on startup; clean up on shutdown."""
    global _handler, _mcp_tools

    chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")

    from endogenai_vector_store import ChromaAdapter
    from endogenai_vector_store.models import ChromaConfig, ChromaMode

    config = ChromaConfig(mode=ChromaMode.HTTP, host=chromadb_url.split("://")[-1].split(":")[0])
    adapter = ChromaAdapter(config=config)

    store = WorkingMemoryStore()
    loader = ContextLoader(adapter=adapter)
    dispatcher = ConsolidationDispatcher()
    _handler = A2AHandler(store=store, loader=loader, dispatcher=dispatcher)
    _mcp_tools = MCPTools(store=store, loader=loader, dispatcher=dispatcher)

    # Configure OTel tracing + structlog trace_id injection (§8.4)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    from working_memory.instrumentation.otel_setup import configure_telemetry  # noqa: PLC0415
    configure_telemetry(otlp_endpoint=otlp_endpoint)

    logger.info("working_memory.server.startup", chromadb_url=chromadb_url)
    yield
    logger.info("working_memory.server.shutdown")


app = FastAPI(title="working-memory", version="0.1.0", lifespan=lifespan)


@app.post("/tasks")
async def dispatch_task(request: Request) -> JSONResponse:
    """JSON-RPC 2.0 dispatcher for incoming A2A task delegations."""
    body: dict[str, Any] = await request.json()
    rpc_id: str = body.get("id", str(uuid.uuid4()))

    # Support both JSON-RPC 2.0 envelope (params.task_type) and legacy plain dict
    if "method" in body and body.get("method") == "tasks/send":
        params: dict[str, Any] = body.get("params", {})
        task_type: str = params.pop("task_type", "")
        payload = params
    else:
        # Legacy fallback: {"type": task_type, ...}
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
        logger.exception("working_memory.server.task_error", task_type=task_type)
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
    """MCP SSE endpoint placeholder — returns tool listing."""
    if _mcp_tools is None:
        return JSONResponse({"error": "MCP tools not ready"}, status_code=503)
    return JSONResponse({"status": "ok", "module": "working-memory", "protocol": "mcp-sse"})


@app.get("/health")
async def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok", "module": "working-memory"})


def main() -> None:
    """Entry point for the ``serve`` script."""
    port = int(os.getenv("A2A_PORT", "8201"))
    uvicorn.run("working_memory.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
