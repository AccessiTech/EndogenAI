"""FastAPI HTTP server for the sensory-input module.

Endpoints
---------
POST /ingest          — direct signal ingestion
POST /mcp             — receive MCPContext, emit Signal
POST /a2a             — receive A2AMessage, emit Signal
GET  /health          — liveness probe
GET  /.well-known/agent-card.json  — agent capability card
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

import jsonschema
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from sensory_input import config, processor
from sensory_input.models import IngestRequest, IngestResponse

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)

log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------

_AGENT_CARD_PATH = Path(__file__).parent.parent.parent.parent / "agent-card.json"


def _load_agent_card() -> dict[str, Any]:
    if _AGENT_CARD_PATH.exists():
        with _AGENT_CARD_PATH.open() as fh:
            return cast("dict[str, Any]", json.load(fh))
    return {
        "name": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION,
        "capabilities": ["mcp-context", "a2a-task"],
        "endpoints": {
            "a2a": f"http://localhost:{config.PORT}",
            "mcp": f"http://localhost:{config.PORT}",
        },
    }


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.SERVICE_VERSION,
    description="Signal ingestion, normalisation, and dispatch.",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _read_body_checked(request: Request) -> bytes:
    """Read the raw request body and enforce the payload size limit."""
    body = await request.body()
    try:
        processor.check_payload_size(body)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return body


def _parse_json(body: bytes) -> dict[str, Any]:
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Expected a JSON object at the top level")
    return cast("dict[str, Any]", data)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.SERVICE_VERSION}


@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    return JSONResponse(content=_load_agent_card())


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: Request) -> IngestResponse:
    """Direct signal ingestion endpoint."""
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        ingest_req = IngestRequest.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    signal = processor.ingest_request_to_signal(ingest_req)
    log.info(
        "ingest.accepted",
        service=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        signal_id=signal.id,
        modality=signal.modality,
    )
    return IngestResponse(signal=signal)


@app.post("/mcp")
async def receive_mcp(request: Request) -> JSONResponse:
    """Receive an MCPContext, validate it, and emit a Signal."""
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        processor.validate_mcp(data)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    signal = processor.mcp_to_signal(data)
    log.info(
        "mcp.accepted",
        service=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        signal_id=signal.id,
    )
    return JSONResponse(content=signal.model_dump())


@app.post("/a2a")
async def receive_a2a(request: Request) -> JSONResponse:
    """Receive an A2AMessage, validate it, and emit a Signal."""
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        processor.validate_a2a(data)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    signal = processor.a2a_to_signal(data)
    log.info(
        "a2a.accepted",
        service=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        signal_id=signal.id,
    )
    return JSONResponse(content=signal.model_dump())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "sensory_input.server:app",
        host=config.HOST,
        port=config.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
