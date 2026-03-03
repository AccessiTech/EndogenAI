"""server.py — FastAPI server for the executive-agent module.

Exposes three interfaces:
  POST /tasks                          JSON-RPC 2.0 → A2A task dispatcher
  GET  /.well-known/agent-card.json    Module agent card
  GET  /sse                            MCP SSE (tools listing)
  GET  /health                         Health check

Environment variables:
  CHROMADB_URL           ChromaDB base URL (default: http://localhost:8000)
  OPA_URL                OPA REST API base URL (default: http://localhost:8181)
  AGENT_RUNTIME_A2A_URL  agent-runtime A2A URL (default: http://localhost:8162)
  AFFECTIVE_A2A_URL      affective module A2A URL (default: http://localhost:8205)
  WORKING_MEMORY_A2A_URL working-memory A2A URL (default: http://localhost:8201)
  A2A_PORT               A2A server port (default: 8161)
  MCP_PORT               MCP SSE port (default: 8261)
  METACOGNITION_URL      metacognition A2A URL (default: None — disabled)
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
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from executive_agent.a2a_handler import handle_task
from executive_agent.deliberation import DeliberationLoop
from executive_agent.feedback import FeedbackHandler
from executive_agent.goal_stack import GoalStack
from executive_agent.identity import IdentityManager, load_identity_config
from executive_agent.mcp_tools import MCPTools
from executive_agent.policy import PolicyEngine
from executive_agent.store import ExecutiveStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"
_IDENTITY_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "identity.config.json"

# ---------------------------------------------------------------------------
# Module-global singletons — initialised during lifespan startup
# ---------------------------------------------------------------------------
_goal_stack: GoalStack | None = None
_policy: PolicyEngine | None = None
_identity: IdentityManager | None = None
_feedback_handler: FeedbackHandler | None = None
_deliberation: DeliberationLoop | None = None
_mcp_tools: MCPTools | None = None
_runtime_client: Any | None = None  # A2AClient to agent-runtime


# ---------------------------------------------------------------------------
# Getter functions used by mcp_tools.py and a2a_handler.py
# ---------------------------------------------------------------------------

def get_goal_stack() -> GoalStack:
    if _goal_stack is None:
        raise RuntimeError("GoalStack not initialised — server not started")
    return _goal_stack


def get_policy_engine() -> PolicyEngine:
    if _policy is None:
        raise RuntimeError("PolicyEngine not initialised — server not started")
    return _policy


def get_identity_manager() -> IdentityManager:
    if _identity is None:
        raise RuntimeError("IdentityManager not initialised — server not started")
    return _identity


def get_feedback_handler() -> FeedbackHandler:
    if _feedback_handler is None:
        raise RuntimeError("FeedbackHandler not initialised — server not started")
    return _feedback_handler


def get_runtime_client() -> Any | None:
    return _runtime_client


async def get_drive_state() -> Any:
    from executive_agent.models import DriveState

    if _runtime_client is None:
        return DriveState()
    from executive_agent.server import _mcp_tools as mtools  # noqa: PLC0415

    if mtools is None:
        return DriveState()
    result = await mtools.handle("executive_agent.get_drive_state", {})
    from executive_agent.models import DriveState as DS

    return DS(**result)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _goal_stack, _policy, _identity, _feedback_handler
    global _deliberation, _mcp_tools, _runtime_client

    chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
    opa_url = os.getenv("OPA_URL", "http://localhost:8181")
    runtime_url = os.getenv("AGENT_RUNTIME_A2A_URL", "http://localhost:8162")
    affective_url = os.getenv("AFFECTIVE_A2A_URL", "http://localhost:8205")
    metacognition_url = os.getenv("METACOGNITION_URL", None)

    # ---- Vector store adapter ----
    from endogenai_vector_store import ChromaAdapter
    from endogenai_vector_store.models import ChromaConfig, ChromaMode

    chroma_host = chromadb_url.replace("http://", "").replace("https://", "").split(":")[0]
    chroma_config = ChromaConfig(mode=ChromaMode.HTTP, host=chroma_host)
    chroma_adapter = ChromaAdapter(config=chroma_config)
    store = ExecutiveStore(adapter=chroma_adapter)

    # ---- A2A clients ----
    from endogenai_a2a import A2AClient

    _runtime_client = A2AClient(url=runtime_url)
    affective_client = A2AClient(url=affective_url)

    # ---- Core components ----
    identity_config = load_identity_config(_IDENTITY_CONFIG_PATH)
    _identity = IdentityManager(config=identity_config, store=store)
    _goal_stack = GoalStack(max_active_goals=identity_config.max_active_goals)
    _policy = PolicyEngine(base_url=opa_url)
    metacognition_client = None
    if metacognition_url:
        metacognition_client = A2AClient(url=metacognition_url)

    _feedback_handler = FeedbackHandler(
        goal_stack=_goal_stack,
        affective_client=affective_client,
        metacognition_client=metacognition_client,
    )

    # ---- MCP tools ----
    _mcp_tools = MCPTools(
        goal_stack=_goal_stack,
        policy=_policy,
        identity=_identity,
        affective_client=affective_client,
    )

    # ---- Deliberation loop ----
    _deliberation = DeliberationLoop(
        goal_stack=_goal_stack,
        policy=_policy,
        cycle_ms=identity_config.deliberation_cycle_ms,
    )
    await _deliberation.start()

    logger.info(
        "executive_agent.server.startup",
        opa_url=opa_url,
        chromadb_url=chromadb_url,
        runtime_url=runtime_url,
    )
    FastAPIInstrumentor().instrument_app(app)
    yield

    # Shutdown
    if _deliberation:
        await _deliberation.stop()
    if _policy:
        await _policy.aclose()
    logger.info("executive_agent.server.shutdown")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(title="executive-agent", version="0.1.0", lifespan=lifespan)


@app.post("/tasks")
async def dispatch_task(request: Request) -> JSONResponse:
    """JSON-RPC 2.0 dispatcher for inbound A2A task delegations."""
    body: dict[str, Any] = await request.json()
    rpc_id: str = body.get("id", str(uuid.uuid4()))

    if "method" in body and body.get("method") == "tasks/send":
        params: dict[str, Any] = body.get("params", {})
        task_type: str = params.pop("task_type", "")
        payload = params
    else:
        task_type = body.pop("type", body.pop("task_type", ""))
        payload = body

    try:
        result = await handle_task(task_type, payload)
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
    except ValueError as exc:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": "invalid-input",
                                                          "message": str(exc)}},
            status_code=400,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("executive_agent.server.task_error", task_type=task_type)
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": "internal-error", "message": str(exc)},
            },
            status_code=500,
        )


@app.post("/mcp/tools/call")
async def call_mcp_tool(request: Request) -> JSONResponse:
    """MCP tool invocation endpoint."""
    if _mcp_tools is None:
        return JSONResponse({"error": "MCP tools not initialised"}, status_code=503)
    body: dict[str, Any] = await request.json()
    tool_name: str = body.get("name", "")
    params: dict[str, Any] = body.get("params", body.get("arguments", {}))
    try:
        result = await _mcp_tools.handle(tool_name, params)
        return JSONResponse({"result": result})
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:  # noqa: BLE001
        logger.exception("executive_agent.mcp_tool_error", tool_name=tool_name)
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    """Serve the module agent card."""
    try:
        card = json.loads(_AGENT_CARD_PATH.read_text())
        return JSONResponse(card)
    except FileNotFoundError:
        return JSONResponse({"error": "agent-card.json not found"}, status_code=404)


@app.get("/sse")
async def sse_health() -> JSONResponse:
    """MCP SSE endpoint placeholder."""
    if _mcp_tools is None:
        return JSONResponse({"error": "MCP tools not ready"}, status_code=503)
    return JSONResponse(
        {
            "status": "ok",
            "module": "executive-agent",
            "protocol": "mcp-sse",
            "tools": [
                "executive_agent.push_goal",
                "executive_agent.get_goal_stack",
                "executive_agent.evaluate_policy",
                "executive_agent.update_identity",
                "executive_agent.abort_goal",
                "executive_agent.get_drive_state",
            ],
        }
    )


@app.get("/health")
async def health() -> JSONResponse:
    """Basic health check."""
    opa_ok = False
    if _policy:
        try:
            opa_ok = await _policy.health_check()
        except RuntimeError:
            opa_ok = False
    return JSONResponse(
        {
            "status": "ok",
            "module": "executive-agent",
            "deliberation_running": _deliberation is not None and _deliberation._running,
            "opa_healthy": opa_ok,
        }
    )


def main() -> None:
    """Entry point for the ``serve`` script."""
    port = int(os.getenv("A2A_PORT", "8161"))
    uvicorn.run("executive_agent.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
