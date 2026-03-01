"""FastAPI HTTP server for the perception module."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import jsonschema
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from perception import config
from perception.models import PerceptionRequest, PerceptionResponse
from perception.processor import PerceptionPipeline, validate_a2a, validate_mcp

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
# Lifespan
# ---------------------------------------------------------------------------

_pipeline: PerceptionPipeline | None = None


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    global _pipeline  # noqa: PLW0603
    _pipeline = PerceptionPipeline()
    log.info("perception.started", embedding_enabled=config.ENABLE_EMBEDDING)
    yield
    if _pipeline is not None:
        await _pipeline.close()
    log.info("perception.stopped")


def _get_pipeline() -> PerceptionPipeline:
    global _pipeline  # noqa: PLW0603
    if _pipeline is None:
        _pipeline = PerceptionPipeline()
    return _pipeline


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.SERVICE_VERSION,
    description="Feature extraction, pattern recognition, and multimodal fusion.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _read_body_checked(request: Request) -> bytes:
    body = await request.body()
    if len(body) > config.MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload exceeds size limit")
    return body


def _parse_json(body: bytes) -> dict[str, Any]:
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Expected a JSON object")
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


@app.post("/perceive", response_model=PerceptionResponse)
async def perceive(request: Request) -> PerceptionResponse:
    """Process a Signal through the full perception pipeline."""
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        perc_req = PerceptionRequest.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = await _get_pipeline().process(perc_req.signal)
    log.info(
        "perceive.processed",
        service=config.SERVICE_NAME,
        signal_id=perc_req.signal.id,
        pattern=result.pattern,
    )
    return PerceptionResponse(result=result)


@app.post("/ingest", response_model=PerceptionResponse)
async def ingest(request: Request) -> PerceptionResponse:
    """Alias for POST /perceive — receives signals from attention-filtering."""
    return await perceive(request)


@app.post("/mcp")
async def receive_mcp(request: Request) -> JSONResponse:
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        validate_mcp(data)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    result = await _get_pipeline().process_mcp(data)
    return JSONResponse(content=result.model_dump())


@app.post("/a2a")
async def receive_a2a(request: Request) -> JSONResponse:
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        validate_a2a(data)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    result = await _get_pipeline().process_a2a(data)
    return JSONResponse(content=result.model_dump())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "perception.server:app",
        host=config.HOST,
        port=config.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
