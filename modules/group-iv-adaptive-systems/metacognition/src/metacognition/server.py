"""server.py — FastAPI server for the metacognition module (port 8171).

Interfaces:
  POST /tasks                       JSON-RPC 2.0 → A2A task dispatcher
  GET  /.well-known/agent-card.json Module agent card
  GET  /health                      Liveness probe
  GET  /mcp/resources/list          MCP resource listing
  GET  /mcp/resources/read          MCP resource reader
  GET  /mcp/tools/list              MCP tool listing
  POST /mcp/tools/call              MCP tool call dispatcher

Environment variables:
  METACOGNITION_PORT     Server port (default: 8171)
  EXECUTIVE_AGENT_URL    executive-agent A2A URL (default: http://localhost:8161)
  CHROMADB_URL           ChromaDB URL (default: http://localhost:8000)
  OTLP_ENDPOINT          OTLP gRPC endpoint (default: http://localhost:4317)
  PROMETHEUS_PORT        Prometheus scrape port (default: 9464)
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

from metacognition.evaluation.evaluator import (
    MetacognitionEvaluator,
    MonitoringConfig,
)
from metacognition.instrumentation.metrics import MetricsBundle, create_metrics
from metacognition.instrumentation.otel_setup import configure_telemetry
from metacognition.interfaces.a2a_handler import handle_task
from metacognition.interfaces.mcp_server import (
    MCP_RESOURCES,
    MCP_TOOLS,
    get_anomalies_recent,
    get_confidence_current,
    get_session_report,
)
from metacognition.store.monitoring_store import MonitoringStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "monitoring.config.json"

_evaluator: MetacognitionEvaluator | None = None
_store: MonitoringStore | None = None
_metrics_bundle: MetricsBundle | None = None


# ---------------------------------------------------------------------------
# Getters
# ---------------------------------------------------------------------------


def get_evaluator() -> MetacognitionEvaluator:
    if _evaluator is None:
        raise RuntimeError("MetacognitionEvaluator not initialised — server not started")
    return _evaluator


def get_store() -> MonitoringStore:
    if _store is None:
        raise RuntimeError("MonitoringStore not initialised — server not started")
    return _store


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise OTel, evaluator, and store on startup."""
    global _evaluator, _store, _metrics_bundle

    # Load config
    config = MonitoringConfig()
    if _CONFIG_PATH.exists():
        with _CONFIG_PATH.open() as fh:
            raw = json.load(fh)
        config = MonitoringConfig.model_validate(raw)

    # Override from env
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", config.otlp_endpoint)
    prometheus_port = int(os.getenv("PROMETHEUS_PORT", str(config.prometheus_port)))
    executive_agent_url = os.getenv("EXECUTIVE_AGENT_URL", config.executive_agent_url)
    chromadb_url = os.getenv("CHROMADB_URL", config.chromadb_url)

    # OTel
    tracer, meter = configure_telemetry(
        otlp_endpoint=otlp_endpoint,
        prometheus_port=prometheus_port,
        service_name=config.service_name,
        service_namespace=config.service_namespace,
    )

    # Metrics
    _metrics_bundle = create_metrics(meter)

    # Evaluator
    _evaluator = MetacognitionEvaluator(config=config, metrics_bundle=_metrics_bundle)

    # A2A client for outbound request_correction
    try:
        from endogenai_a2a import A2AClient

        a2a_client = A2AClient(url=executive_agent_url)
        _evaluator.set_a2a_client(a2a_client)
        logger.info("A2A client configured", executive_agent_url=executive_agent_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("A2A client setup failed — correction dispatch disabled", error=str(exc))

    # Store
    _store = MonitoringStore(chromadb_url=chromadb_url)
    try:
        await _store.initialise()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Store initialisation failed — continuing without persistence",
            error=str(exc),
        )

    FastAPIInstrumentor.instrument_app(app)
    logger.info("Metacognition module started", port=int(os.getenv("METACOGNITION_PORT", "8171")))

    yield

    logger.info("Metacognition module shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="metacognition",
    version="0.1.0",
    description="Metacognition & Monitoring Layer — §7.2",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "module": "metacognition"}


# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------


@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    if _AGENT_CARD_PATH.exists():
        with _AGENT_CARD_PATH.open() as fh:
            card = json.load(fh)
        return JSONResponse(content=card)
    return JSONResponse(content={"error": "agent-card.json not found"}, status_code=404)


# ---------------------------------------------------------------------------
# A2A JSON-RPC 2.0 dispatcher
# ---------------------------------------------------------------------------


@app.post("/tasks")
async def tasks_endpoint(request: Request) -> JSONResponse:
    """Receive and dispatch JSON-RPC 2.0 A2A task requests."""
    evaluator = get_evaluator()
    store = get_store()

    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            },
            status_code=400,
        )

    rpc_id = body.get("id", str(uuid.uuid4()))
    method = body.get("method", "")
    params = body.get("params", {})

    # JSON-RPC 2.0: method is "tasks/send" with task_type in params
    task_type = params.get("task_type", method)

    try:
        result = await handle_task(
            task_type=task_type,
            payload=params,
            evaluator=evaluator,
            store=store,
        )
        return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "result": result})
    except ValueError as exc:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": str(exc)},
            },
            status_code=400,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error in tasks endpoint", error=str(exc))
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32603, "message": f"Internal error: {exc}"},
            },
            status_code=500,
        )


# ---------------------------------------------------------------------------
# MCP endpoints
# ---------------------------------------------------------------------------


@app.get("/mcp/resources/list")
async def mcp_resources_list() -> JSONResponse:
    return JSONResponse(content={"resources": MCP_RESOURCES})


@app.get("/mcp/resources/read")
async def mcp_resources_read(uri: str) -> JSONResponse:
    evaluator = get_evaluator()

    if uri == "resource://brain.metacognition/confidence/current":
        data: Any = await get_confidence_current(evaluator)
    elif uri == "resource://brain.metacognition/anomalies/recent":
        data = await get_anomalies_recent(evaluator)
    elif uri == "resource://brain.metacognition/report/session":
        data = await get_session_report(evaluator)
    else:
        return JSONResponse(content={"error": f"Unknown resource URI: {uri}"}, status_code=404)

    return JSONResponse(
        content={"contents": [{"uri": uri, "mimeType": "application/json", "data": data}]}
    )


@app.get("/mcp/tools/list")
async def mcp_tools_list() -> JSONResponse:
    return JSONResponse(content={"tools": MCP_TOOLS})


@app.post("/mcp/tools/call")
async def mcp_tools_call(request: Request) -> JSONResponse:
    """Dispatch an MCP tool call."""
    evaluator = get_evaluator()
    store = get_store()

    body = await request.json()
    tool_name: str = body.get("name", "")
    tool_input: dict[str, Any] = body.get("arguments", {})

    if tool_name == "evaluate":
        result = await handle_task(
            task_type="evaluate_output",
            payload=tool_input,
            evaluator=evaluator,
            store=store,
        )
    elif tool_name == "configure-threshold":
        default_thresh = evaluator.get_confidence_threshold()
        new_threshold = float(tool_input.get("confidence_threshold", default_thresh))
        evaluator.set_confidence_threshold(new_threshold)
        result = {"confidence_threshold": new_threshold, "status": "updated"}
    elif tool_name == "report":
        result = await get_session_report(evaluator)
    else:
        return JSONResponse(content={"error": f"Unknown tool: {tool_name}"}, status_code=404)

    return JSONResponse(content={"content": [{"type": "text", "text": json.dumps(result)}]})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    port = int(os.getenv("METACOGNITION_PORT", "8171"))
    uvicorn.run("metacognition.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
