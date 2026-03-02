"""FastAPI server for the short-term memory module.

Exposes three interfaces:
  POST /tasks                        JSON-RPC 2.0 → A2AHandler.handle()
  GET  /.well-known/agent-card.json  Serve module agent card
  GET  /sse                          MCP Server-Sent Events (FastMCP)

Environment variables:
  CHROMADB_URL      ChromaDB base URL (default: http://localhost:8000)
  CHROMADB_HOST     ChromaDB host (overrides CHROMADB_URL host extraction)
  REDIS_URL         Redis connection URL (default: redis://localhost:6379)
  LTM_A2A_URL       Long-term memory A2A endpoint (default: http://localhost:8203)
  EPISODIC_A2A_URL  Episodic memory A2A endpoint (default: http://localhost:8204)
  A2A_PORT          A2A server port (default: 8202)
  MCP_PORT          MCP SSE port (default: 8302)
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

import redis.asyncio as aioredis
import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from short_term_memory.a2a_handler import A2AHandler
from short_term_memory.consolidation import ConsolidationPipeline
from short_term_memory.mcp_tools import MCPTools
from short_term_memory.novelty import NoveltyChecker
from short_term_memory.search import SemanticSearch
from short_term_memory.store import ShortTermMemoryStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"

_handler: A2AHandler | None = None
_mcp_tools: MCPTools | None = None
_redis_client: aioredis.Redis | None = None


def _build_adapter(chromadb_url: str) -> Any:
    """Build a ChromaAdapter from environment configuration."""
    from endogenai_vector_store import ChromaAdapter
    from endogenai_vector_store.models import ChromaConfig, ChromaMode

    host = os.getenv("CHROMADB_HOST") or chromadb_url.split("://")[-1].split(":")[0]
    config = ChromaConfig(mode=ChromaMode.HTTP, host=host)
    return ChromaAdapter(config=config)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise module components on startup; clean up on shutdown."""
    global _handler, _mcp_tools, _redis_client

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
    ltm_url = os.getenv("LTM_A2A_URL", "http://localhost:8203")
    episodic_url = os.getenv("EPISODIC_A2A_URL", "http://localhost:8204")

    _redis_client = aioredis.from_url(redis_url, decode_responses=False)
    adapter = _build_adapter(chromadb_url)
    ltm_adapter = _build_adapter(chromadb_url)
    episodic_adapter = _build_adapter(chromadb_url)

    novelty_checker = NoveltyChecker(adapter=adapter)
    store = ShortTermMemoryStore(
        redis_client=_redis_client,
        adapter=adapter,
        novelty_checker=novelty_checker,
    )
    search = SemanticSearch(adapter=adapter)
    pipeline = ConsolidationPipeline(
        store=store,
        ltm_adapter=ltm_adapter,
        episodic_adapter=episodic_adapter,
    )

    _handler = A2AHandler(store=store, search=search, pipeline=pipeline)
    _mcp_tools = MCPTools(store=store, search=search, pipeline=pipeline)

    logger.info(
        "short_term_memory.server.startup",
        redis_url=redis_url,
        ltm_url=ltm_url,
        episodic_url=episodic_url,
    )
    yield

    if _redis_client is not None:
        await _redis_client.aclose()
    logger.info("short_term_memory.server.shutdown")


app = FastAPI(title="short-term-memory", version="0.1.0", lifespan=lifespan)


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
        logger.exception("short_term_memory.server.task_error", task_type=task_type)
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
    return JSONResponse({"status": "ok", "module": "short-term-memory", "protocol": "mcp-sse"})


@app.get("/health")
async def health() -> JSONResponse:
    """Basic health check."""
    return JSONResponse({"status": "ok", "module": "short-term-memory"})


def main() -> None:
    """Entry point for the ``serve`` script."""
    port = int(os.getenv("A2A_PORT", "8202"))
    uvicorn.run("short_term_memory.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
