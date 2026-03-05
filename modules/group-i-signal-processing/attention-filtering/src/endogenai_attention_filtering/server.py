"""FastAPI server for the attention-filtering module.

Exposes:
  POST /tasks                          JSON-RPC 2.0 A2A task endpoint
  GET  /.well-known/agent-card.json    Module agent card
  GET  /health                         Health probe

Environment variables:
  PORT   Server port (default: 8102)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"

app = FastAPI(title="attention-filtering", version="0.1.0")


@app.get("/.well-known/agent-card.json", response_class=JSONResponse)
async def agent_card() -> JSONResponse:
    """Return the module agent card."""
    card = json.loads(_AGENT_CARD_PATH.read_text())
    return JSONResponse(content=card)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tasks")
async def tasks(request: dict) -> dict:  # type: ignore[type-arg]
    """Stub A2A JSON-RPC 2.0 endpoint."""
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"status": "pending"}}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8102"))
    uvicorn.run("endogenai_attention_filtering.server:app", host="0.0.0.0", port=port, reload=False)
