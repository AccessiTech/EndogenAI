"""server.py — FastAPI application for motor-output.

Co-hosts:
  - A2A JSON-RPC 2.0 endpoint (POST /tasks)
  - MCP SSE endpoint (GET /sse, POST /mcp/tools/call)
  - Agent-card serving (GET /.well-known/agent-card.json)
  - Health probe (GET /health)

Port controlled via MO_PORT env var (default 8163).
"""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from motor_output.a2a_handler import handle_task
from motor_output.dispatcher import Dispatcher
from motor_output.error_policy import ErrorPolicy
from motor_output.feedback import FeedbackEmitter
from motor_output.mcp_tools import MCPTools
from motor_output.models import ErrorPolicyConfig

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_ROOT = Path(__file__).parent.parent.parent  # module root

_AGENT_CARD_PATH = _ROOT / "agent-card.json"
_ERROR_POLICY_PATH = _ROOT / "error-policy.config.json"
_CHANNELS_CONFIG_PATH = _ROOT / "channels.config.json"

_dispatcher: Dispatcher | None = None
_mcp_tools: MCPTools | None = None


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _dispatcher, _mcp_tools

    executive_agent_url = os.environ.get(
        "EXECUTIVE_AGENT_URL", "http://localhost:8161"
    )

    # Load error policy config
    error_policy_config = ErrorPolicyConfig()
    if _ERROR_POLICY_PATH.exists():
        raw = json.loads(_ERROR_POLICY_PATH.read_text())
        # Top-level keys match error-policy.config.json: retryPolicy / circuitBreaker / escalation
        retry_cfg = raw.get("retryPolicy", {})
        cb_cfg = raw.get("circuitBreaker", {})
        esc_cfg = raw.get("escalation", {})
        error_policy_config = ErrorPolicyConfig.model_validate(
            {
                "maxAttempts": retry_cfg.get("maxAttempts", 3),
                "backoffMultiplier": retry_cfg.get("backoffMultiplier", 2.0),
                "initialDelaySeconds": retry_cfg.get("initialDelaySeconds", 1.0),
                "maxDelaySeconds": retry_cfg.get("maxDelaySeconds", 30.0),
                "circuitBreakerEnabled": cb_cfg.get("enabled", True),
                "failureThreshold": cb_cfg.get("failureThreshold", 5),
                "recoveryTimeSeconds": cb_cfg.get("recoveryTimeSeconds", 60.0),
                "escalateBaseUrl": esc_cfg.get(
                    "executiveAgentUrl", executive_agent_url
                ),
            }
        )

    # Read corollary discharge setting from channels config
    corollary_enabled = True
    if _CHANNELS_CONFIG_PATH.exists():
        ch_cfg = json.loads(_CHANNELS_CONFIG_PATH.read_text())
        corollary_enabled = ch_cfg.get("corollaryDischarge", {}).get("enabled", True)

    feedback_emitter = FeedbackEmitter(executive_agent_url=executive_agent_url)
    error_policy = ErrorPolicy(
        config=error_policy_config,
        executive_agent_url=executive_agent_url,
    )
    _dispatcher = Dispatcher(
        error_policy=error_policy,
        feedback_emitter=feedback_emitter,
        corollary_discharge_enabled=corollary_enabled,
    )
    _mcp_tools = MCPTools(dispatcher=_dispatcher)

    logger.info("motor_output.started", executive_agent_url=executive_agent_url)
    yield
    logger.info("motor_output.stopped")


app = FastAPI(title="motor-output", lifespan=_lifespan)
FastAPIInstrumentor().instrument_app(app)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "module": "motor-output"}


@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    if _AGENT_CARD_PATH.exists():
        return JSONResponse(json.loads(_AGENT_CARD_PATH.read_text()))
    return JSONResponse({"error": "agent-card.json not found"}, status_code=404)


@app.post("/tasks")
async def a2a_tasks(request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    params: dict[str, Any] = body.get("params", {})
    task_type: str = params.pop("task_type", "")
    payload = params  # remaining params IS the flat payload (A2AClient-compatible)
    rpc_id = body.get("id", "")

    if _dispatcher is None:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"message": "Not initialised"}},
            status_code=503,
        )

    result = await handle_task(task_type, payload, _dispatcher)
    return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})


@app.post("/mcp/tools/call")
async def mcp_call(request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    tool_name: str = body.get("name", "")
    arguments: dict[str, Any] = body.get("arguments", {})

    if _mcp_tools is None:
        return JSONResponse({"error": "Not initialised"}, status_code=503)

    result = await _mcp_tools.call_tool(tool_name, arguments)
    return JSONResponse({"content": [{"type": "text", "text": json.dumps(result)}]})


@app.get("/mcp/tools/list")
async def mcp_list_tools() -> JSONResponse:
    if _mcp_tools is None:
        return JSONResponse({"error": "Not initialised"}, status_code=503)
    return JSONResponse({"tools": _mcp_tools.get_tool_definitions()})


@app.get("/sse")
async def sse_endpoint() -> StreamingResponse:
    """Minimal SSE endpoint for MCP transport negotiation."""

    async def _event_stream() -> AsyncGenerator[str, None]:
        tools_json = json.dumps(
            _mcp_tools.get_tool_definitions() if _mcp_tools else []
        )
        yield f"data: {tools_json}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    port = int(os.environ.get("MO_PORT", "8163"))
    uvicorn.run("motor_output.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
