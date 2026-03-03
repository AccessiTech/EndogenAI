"""server.py — FastAPI server for the learning-adaptation module (port 8170).

Interfaces:
  POST /tasks                       JSON-RPC 2.0 → A2A task dispatcher
  GET  /.well-known/agent-card.json Module agent card
  GET  /health                      Liveness probe
  GET  /mcp/resources/list          MCP resource listing
  GET  /mcp/resources/read          MCP resource reader
  GET  /mcp/tools/list              MCP tool listing
  POST /mcp/tools/call              MCP tool call dispatcher

Environment variables:
  LEARNING_ADAPTATION_PORT   Server port (default: 8170)
  CHROMADB_URL               ChromaDB URL (default: http://localhost:8000)
  EXECUTIVE_AGENT_URL        executive-agent A2A URL (default: http://localhost:8161)
  METACOGNITION_URL          metacognition A2A URL (default: http://localhost:8171)
"""

from __future__ import annotations

import asyncio
import contextlib
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
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from learning_adaptation.env.brain_env import BrainEnv
from learning_adaptation.habits.manager import HabitManager
from learning_adaptation.interfaces.a2a_handler import handle_task
from learning_adaptation.interfaces.mcp_server import (
    MCP_RESOURCES,
    MCP_TOOLS,
    call_predict,
    call_promote_habit,
    call_train,
    get_habits_catalog,
    get_policy_current,
    get_replay_buffer_stats,
)
from learning_adaptation.models import LearningConfig
from learning_adaptation.replay.buffer import COLLECTION_NAME, ReplayBuffer
from learning_adaptation.training.trainer import PolicyTrainer

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_AGENT_CARD_PATH = Path(__file__).resolve().parent.parent.parent / "agent-card.json"
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "learning.config.json"

_env: BrainEnv | None = None
_replay_buffer: ReplayBuffer | None = None
_trainer: PolicyTrainer | None = None
_habit_manager: HabitManager | None = None
_config: LearningConfig | None = None
_replay_loop_task: asyncio.Task[None] | None = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_config() -> LearningConfig:
    if _CONFIG_PATH.exists():
        data = json.loads(_CONFIG_PATH.read_text())
        return LearningConfig(**data)
    return LearningConfig()


async def _async_replay_loop(
    replay_buffer: ReplayBuffer,
    trainer: PolicyTrainer,
    interval_seconds: int,
) -> None:
    """Background loop: sample from replay buffer and train periodically."""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            episodes = await replay_buffer.sample(64)
            if episodes:
                result = await trainer.train_step(episodes)
                logger.info(
                    "replay_loop.train",
                    episodes=result.episodes,
                    mean_reward=result.mean_reward,
                    shadow_promoted=result.shadow_promoted,
                )
        except Exception:
            logger.exception("replay_loop.error")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _env, _replay_buffer, _trainer, _habit_manager, _config, _replay_loop_task

    _config = _load_config()

    # Init BrainEnv
    _env = BrainEnv(
        goal_classes=_config.goal_classes,
        observation_window=_config.observation_window_size,
    )

    # Init ChromaDB adapter
    from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig

    chroma_url = os.environ.get("CHROMADB_URL", _config.chromadb_url)
    host, _, raw_port = chroma_url.replace("http://", "").replace("https://", "").partition(":")
    port = int(raw_port) if raw_port else 8000

    chroma_config = ChromaConfig(mode="http", host=host, port=port)
    embedding_config = EmbeddingConfig()
    adapter = ChromaAdapter(config=chroma_config, embedding_config=embedding_config)
    await adapter.connect()

    # Ensure collection exists
    from endogenai_vector_store.models import CreateCollectionRequest

    with contextlib.suppress(Exception):
        await adapter.create_collection(
            CreateCollectionRequest(collection_name=COLLECTION_NAME)
        )

    _replay_buffer = ReplayBuffer(adapter=adapter, max_size=_config.replay_buffer_size)
    _trainer = PolicyTrainer(env=_env, config=_config, replay_buffer=_replay_buffer)
    _habit_manager = HabitManager(config=_config)

    # Start async replay loop
    _replay_loop_task = asyncio.create_task(
        _async_replay_loop(
            replay_buffer=_replay_buffer,
            trainer=_trainer,
            interval_seconds=_config.async_replay_interval_seconds,
        )
    )

    logger.info(
        "learning_adaptation.started",
        port=os.environ.get("LEARNING_ADAPTATION_PORT", 8170),
    )
    FastAPIInstrumentor().instrument_app(app)
    yield

    # Shutdown
    if _replay_loop_task:
        _replay_loop_task.cancel()
    with contextlib.suppress(Exception):
        await adapter.close()
    logger.info("learning_adaptation.stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="learning-adaptation", version="0.1.0", lifespan=lifespan)


@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    if _AGENT_CARD_PATH.exists():
        return JSONResponse(json.loads(_AGENT_CARD_PATH.read_text()))
    return JSONResponse({"error": "agent-card.json not found"}, status_code=404)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "module": "learning-adaptation"}


@app.post("/tasks")
async def tasks(request: Request) -> JSONResponse:
    body = await request.json()
    req_id = body.get("id", 1)
    method = body.get("method", "")
    params = body.get("params", {})
    task_name = params.get("task_type", method)

    if _replay_buffer is None or _trainer is None or _habit_manager is None:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": "not initialised"},
            },
            status_code=503,
        )

    cfg = _config or LearningConfig()
    try:
        result = await handle_task(
            task_name=task_name,
            params=params,
            replay_buffer=_replay_buffer,
            trainer=_trainer,
            habit_manager=_habit_manager,
            executive_agent_url=os.environ.get("EXECUTIVE_AGENT_URL", cfg.executive_agent_url),
            metacognition_url=os.environ.get("METACOGNITION_URL", cfg.metacognition_url),
        )
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})
    except Exception as exc:
        logger.exception("tasks.error", method=method)
        return JSONResponse(
            {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}},
            status_code=500,
        )


# ---------------------------------------------------------------------------
# MCP endpoints
# ---------------------------------------------------------------------------


@app.get("/mcp/resources/list")
async def mcp_resources_list() -> dict[str, Any]:
    return {"resources": MCP_RESOURCES}


@app.get("/mcp/resources/read")
async def mcp_resources_read(uri: str) -> JSONResponse:
    if _trainer is None or _replay_buffer is None or _habit_manager is None:
        return JSONResponse({"error": "not initialised"}, status_code=503)

    resource_data: Any
    if "policy/current" in uri:
        resource_data = await get_policy_current(_trainer)
    elif "replay-buffer/stats" in uri:
        resource_data = await get_replay_buffer_stats(_replay_buffer)
    elif "habits/catalog" in uri:
        resource_data = await get_habits_catalog(_habit_manager)
    else:
        return JSONResponse({"error": f"unknown resource: {uri}"}, status_code=404)

    return JSONResponse({"uri": uri, "contents": [{"text": json.dumps(resource_data)}]})


@app.get("/mcp/tools/list")
async def mcp_tools_list() -> dict[str, Any]:
    return {"tools": MCP_TOOLS}


@app.post("/mcp/tools/call")
async def mcp_tools_call(request: Request) -> JSONResponse:
    body = await request.json()
    tool_name = body.get("name", "")
    arguments: dict[str, Any] = body.get("arguments", {})

    if _trainer is None or _replay_buffer is None or _habit_manager is None:
        return JSONResponse({"error": "not initialised"}, status_code=503)

    try:
        if tool_name == "train":
            result = await call_train(arguments, _replay_buffer, _trainer, _habit_manager)
        elif tool_name == "predict":
            result = await call_predict(arguments, _trainer)
        elif tool_name == "promote-habit":
            result = await call_promote_habit(arguments, _habit_manager, _trainer)
        else:
            return JSONResponse({"error": f"unknown tool: {tool_name}"}, status_code=404)

        return JSONResponse({"content": [{"type": "text", "text": json.dumps(result)}]})
    except Exception as exc:
        logger.exception("mcp_tools.error", tool=tool_name)
        return JSONResponse({"error": str(exc)}, status_code=500)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    port = int(os.environ.get("LEARNING_ADAPTATION_PORT", 8170))
    uvicorn.run(app, host="0.0.0.0", port=port)  # noqa: S104


if __name__ == "__main__":
    main()
