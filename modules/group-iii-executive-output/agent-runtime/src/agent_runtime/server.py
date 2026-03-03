"""server.py — FastAPI application entry-point for agent-runtime.

Co-hosts:
  - A2A JSON-RPC 2.0 endpoint  (POST /tasks)
  - MCP tools endpoint          (POST /mcp/tools/call)
  - MCP SSE stream              (GET  /sse)
  - Agent card                  (GET  /.well-known/agent-card.json)
  - Health probe                (GET  /health)

Two background tasks are managed via the FastAPI lifespan:
  - Temporal Worker (primary orchestration)
  - Tool Registry health-check loop
"""
from __future__ import annotations

import asyncio
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

from agent_runtime.a2a_handler import handle_task
from agent_runtime.decomposer import PipelineDecomposer
from agent_runtime.mcp_tools import MCPTools
from agent_runtime.models import OrchestratorConfig
from agent_runtime.orchestrator import Orchestrator
from agent_runtime.tool_registry import ToolRegistry
from agent_runtime.worker import run_worker

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ── Environment ──────────────────────────────────────────────────────────────
_PORT = int(os.getenv("AR_PORT", "8162"))
_MOTOR_OUTPUT_URL = os.getenv("MOTOR_OUTPUT_URL", "http://localhost:8163")
_EXECUTIVE_AGENT_URL = os.getenv("EXECUTIVE_AGENT_URL", "http://localhost:8161")
_CONFIG_PATH = Path(
    os.getenv(
        "ORCHESTRATOR_CONFIG",
        str(Path(__file__).parent.parent.parent / "orchestrator.config.json"),
    )
)
_REGISTRY_CONFIG_PATH = Path(
    os.getenv(
        "TOOL_REGISTRY_CONFIG",
        str(Path(__file__).parent.parent.parent / "tool-registry.config.json"),
    )
)
_AGENT_CARD_PATH = Path(__file__).parent.parent.parent / "agent-card.json"

# ── Singletons (populated during lifespan) ───────────────────────────────────
_orchestrator: Orchestrator | None = None
_tool_registry: ToolRegistry | None = None
_decomposer: PipelineDecomposer | None = None
_mcp_tools: MCPTools | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _orchestrator, _tool_registry, _decomposer, _mcp_tools

    # ── Tool Registry ─────────────────────────────────────────────────────
    registry_config: dict[str, Any] = {}
    if _REGISTRY_CONFIG_PATH.exists():
        registry_config = json.loads(_REGISTRY_CONFIG_PATH.read_text())

    targets: list[int] = registry_config.get("discoveryTargets", [8161, 8163])
    discovery_targets = [f"http://localhost:{p}" for p in targets]
    persistence_path = registry_config.get("registryPersistencePath", ".tool-registry.json")
    health_interval: int = registry_config.get("healthCheckIntervalSeconds", 30)

    _tool_registry = ToolRegistry(
        discovery_targets=discovery_targets,
        health_check_interval_seconds=health_interval,
        persistence_path=persistence_path,
    )
    await _tool_registry.start()

    # ── Orchestrator ──────────────────────────────────────────────────────
    if _CONFIG_PATH.exists():
        _orchestrator = Orchestrator.from_config_file(
            _CONFIG_PATH,
            motor_output_url=_MOTOR_OUTPUT_URL,
            executive_agent_url=_EXECUTIVE_AGENT_URL,
        )
    else:
        cfg = OrchestratorConfig(
            primary="temporal",
            fallback="prefect",
            temporalServerUrl="localhost:7233",
            temporalNamespace="endogenai",
            temporalTaskQueue="brain-runtime",
            maxTemporalConnectRetries=3,
            fallbackCooldownSeconds=60,
        )
        _orchestrator = Orchestrator(
            config=cfg,
            motor_output_url=_MOTOR_OUTPUT_URL,
            executive_agent_url=_EXECUTIVE_AGENT_URL,
        )

    # ── Decomposer ────────────────────────────────────────────────────────
    _decomposer = PipelineDecomposer(tool_registry=_tool_registry)

    # ── MCP Tools ─────────────────────────────────────────────────────────
    _mcp_tools = MCPTools(orchestrator=_orchestrator, tool_registry=_tool_registry)

    # ── Temporal Worker (background) ──────────────────────────────────────
    temporal_url = _orchestrator._config.temporal_server_url
    namespace = _orchestrator._config.temporal_namespace
    task_queue = _orchestrator._config.temporal_task_queue
    worker_task = asyncio.create_task(
        run_worker(
            temporal_url=temporal_url,
            namespace=namespace,
            task_queue=task_queue,
            motor_output_url=_MOTOR_OUTPUT_URL,
            executive_agent_url=_EXECUTIVE_AGENT_URL,
        )
    )

    logger.info("agent_runtime.startup", port=_PORT)
    try:
        yield
    finally:
        worker_task.cancel()
        if _tool_registry is not None:
            await _tool_registry.stop()
        logger.info("agent_runtime.shutdown")


app = FastAPI(title="EndogenAI Agent Runtime", lifespan=lifespan)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    data = json.loads(_AGENT_CARD_PATH.read_text())
    return JSONResponse(data)


@app.get("/health")
async def health() -> JSONResponse:
    orchestrator_ok = _orchestrator is not None
    return JSONResponse({"status": "ok", "orchestrator": orchestrator_ok})


@app.post("/tasks")
async def tasks(request: Request) -> JSONResponse:
    """A2A JSON-RPC 2.0 task endpoint."""
    body = await request.json()
    task_type: str = body.get("method", "")
    payload: dict[str, Any] = body.get("params", {})
    rpc_id = body.get("id", 1)

    try:
        result = await handle_task(
            task_type=task_type,
            payload=payload,
            orchestrator=_orchestrator,  # type: ignore[arg-type]
            tool_registry=_tool_registry,  # type: ignore[arg-type]
        )
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
    except ValueError as exc:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": str(exc)}},
            status_code=400,
        )
    except Exception as exc:
        logger.exception("tasks.error", error=str(exc))
        return JSONResponse(
            {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32603, "message": str(exc)}},
            status_code=500,
        )


@app.post("/mcp/tools/call")
async def mcp_call(request: Request) -> JSONResponse:
    """MCP tool call endpoint."""
    body = await request.json()
    tool_name: str = body.get("name", "")
    params: dict[str, Any] = body.get("parameters", {})

    try:
        result = await _mcp_tools.handle(tool_name, params)  # type: ignore[union-attr]
        return JSONResponse({"result": result})
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        logger.exception("mcp_call.error", tool=tool_name, error=str(exc))
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/sse")
async def sse() -> StreamingResponse:
    """MCP Server-Sent Events stream (tool schema advertisement)."""
    if _AGENT_CARD_PATH.exists():
        card = json.loads(_AGENT_CARD_PATH.read_text())
        skills = card.get("skills", [])
    else:
        skills = []

    async def event_stream() -> AsyncGenerator[str, None]:
        import json as _json

        payload = _json.dumps({"event": "tools_available", "tools": skills})
        yield f"data: {payload}\n\n"
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield "data: {\"event\":\"ping\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def main() -> None:
    uvicorn.run("agent_runtime.server:app", host="0.0.0.0", port=_PORT, reload=False)


if __name__ == "__main__":
    main()
