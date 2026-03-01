"""FastAPI HTTP server for the attention-filtering module."""

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

from attention_filtering import config
from attention_filtering.models import FilterRequest, FilterResponse
from attention_filtering.processor import AttentionFilter

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
# Application lifespan (holds the stateful filter)
# ---------------------------------------------------------------------------

_filter: AttentionFilter | None = None


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    global _filter  # noqa: PLW0603
    _filter = AttentionFilter()
    log.info("attention_filter.started", threshold=_filter.threshold)
    yield
    log.info("attention_filter.stopped")


def _get_filter() -> AttentionFilter:
    global _filter  # noqa: PLW0603
    if _filter is None:
        _filter = AttentionFilter()
    return _filter


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.SERVICE_VERSION,
    description="Salience scoring, relevance filtering, and signal routing.",
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


@app.get("/state")
async def state() -> JSONResponse:
    return JSONResponse(content=_get_filter().state())


@app.post("/filter", response_model=FilterResponse)
async def filter_signal(request: Request) -> FilterResponse:
    """Score, filter, and route a Signal."""
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        filter_req = FilterRequest.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = _get_filter().filter(filter_req.signal)
    log.info(
        "filter.processed",
        service=config.SERVICE_NAME,
        signal_id=filter_req.signal.id,
        passed=result.scored.passed,
        score=result.scored.score,
    )
    return result


@app.post("/mcp")
async def receive_mcp(request: Request) -> JSONResponse:
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        from attention_filtering.processor import validate_mcp
        validate_mcp(data)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    result = _get_filter().process_mcp(data)
    return JSONResponse(content=result.model_dump())


@app.post("/a2a")
async def receive_a2a(request: Request) -> JSONResponse:
    body = await _read_body_checked(request)
    data = _parse_json(body)

    try:
        from attention_filtering.processor import validate_a2a
        validate_a2a(data)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    result = _get_filter().process_a2a(data)
    return JSONResponse(content=result.model_dump())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "attention_filtering.server:app",
        host=config.HOST,
        port=config.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
