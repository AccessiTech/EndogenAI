"""FastAPI server for the long-term memory module.

Exposes three interfaces:
  POST /tasks                        JSON-RPC 2.0 → A2AHandler.handle()
  GET  /.well-known/agent-card.json  Serve module agent card
  GET  /sse                          MCP Server-Sent Events (FastMCP)

Environment variables:
  CHROMADB_URL          ChromaDB base URL (default: http://localhost:8000)
  CHROMADB_HOST         ChromaDB host (overrides CHROMADB_URL host extraction)
  SEED_DOCUMENTS_PATH   Path to seed documents (default: resources/static/knowledge/)
  A2A_PORT              A2A server port (default: 8203)
  MCP_PORT              MCP SSE port (default: 8303)
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

from long_term_memory.a2a_handler import A2AHandler
from long_term_memory.graph_store import KuzuGraphStore
from long_term_memory.mcp_tools import MCPTools
from long_term_memory.retrieval import HybridRetrieval
from long_term_memory.seed_pipeline import SeedPipeline
from long_term_memory.sql_store import SQLFactStore
from long_term_memory.vector_store import LTMVectorStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"

_handler: A2AHandler | None = None
_mcp_tools: MCPTools | None = None


def _build_adapter() -> Any:
    """Build a ChromaAdapter from environment configuration."""
    from endogenai_vector_store import ChromaAdapter
    from endogenai_vector_store.models import ChromaConfig, ChromaMode

    chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
    host = os.getenv("CHROMADB_HOST") or chromadb_url.split("://")[-1].split(":")[0]
    config = ChromaConfig(mode=ChromaMode.HTTP, host=host)
    return ChromaAdapter(config=config)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise module components on startup; clean up on shutdown."""
    global _handler, _mcp_tools

    seed_path = os.getenv("SEED_DOCUMENTS_PATH", "resources/static/knowledge/")
    kuzu_db_path = os.getenv("KUZU_DB_PATH", "/tmp/endogenai_ltm.kuzu")

    adapter = _build_adapter()

    vector_store = LTMVectorStore(adapter=adapter)
    sql_store = SQLFactStore()
    graph_store = KuzuGraphStore(db_path=kuzu_db_path)
    seed_pipeline = SeedPipeline(adapter=adapter, seed_documents_path=seed_path)
    retrieval = HybridRetrieval(vector_store=vector_store, sql_store=sql_store)

    _handler = A2AHandler(
        vector_store=vector_store,
        retrieval=retrieval,
        sql_store=sql_store,
        seed_pipeline=seed_pipeline,
    )
    _mcp_tools = MCPTools(
        vector_store=vector_store,
        retrieval=retrieval,
        sql_store=sql_store,
        graph_store=graph_store,
        seed_pipeline=seed_pipeline,
    )

    logger.info("long_term_memory.server.startup", seed_path=seed_path)
    yield
    logger.info("long_term_memory.server.shutdown")


app = FastAPI(title="long-term-memory", version="0.1.0", lifespan=lifespan)


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
        logger.exception("long_term_memory.server.task_error", task_type=task_type)
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
    return JSONResponse({"status": "ok", "module": "long-term-memory", "protocol": "mcp-sse"})


@app.get("/health")
async def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok", "module": "long-term-memory"})


def main() -> None:
    """Entry point for the ``serve`` script."""
    port = int(os.getenv("A2A_PORT", "8203"))
    uvicorn.run("long_term_memory.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
