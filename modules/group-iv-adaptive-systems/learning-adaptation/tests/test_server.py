"""Tests for learning-adaptation FastAPI server routes."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

import learning_adaptation.server as _srv
from learning_adaptation.models import (
    ActionPrediction,
    HabitRecord,
    PolicySummary,
    ReplayBufferStats,
    TrainingResult,
)
from learning_adaptation.server import agent_card, health, mcp_resources_list, mcp_tools_list


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------


def _make_trainer() -> MagicMock:
    trainer = MagicMock()
    trainer.get_policy_summary = MagicMock(
        return_value=PolicySummary(algorithm="PPO", total_timesteps=100, last_updated=None)
    )
    trainer.predict = AsyncMock(
        return_value=ActionPrediction(goal_priority_deltas=[0.1] * 4, task_type="default")
    )
    trainer.train_step = AsyncMock(
        return_value=TrainingResult(total_timesteps=64, mean_reward=0.5, episodes=1, policy_updated=True)
    )
    trainer._env = MagicMock()
    trainer._env.push_feedback = MagicMock()
    return trainer


def _make_replay_buffer() -> AsyncMock:
    buf = AsyncMock()
    buf.add = AsyncMock()
    buf.sample = AsyncMock(return_value=[])
    buf.stats = AsyncMock(
        return_value=ReplayBufferStats(total_episodes=10, mean_reward=0.4, top_task_type="default")
    )
    return buf


def _make_habit_manager() -> MagicMock:
    hm = MagicMock()
    hm.record_episode = MagicMock(return_value=False)
    hm.should_promote = MagicMock(return_value=False)
    hm.list_habits = MagicMock(return_value=[])
    hm.promote = AsyncMock(
        return_value=HabitRecord(
            task_type="default",
            policy_path="/tmp/h.pt",
            eval_score=0.9,
            promoted_at="2026-01-01T00:00:00Z",
        )
    )
    return hm


@pytest.fixture
def test_app() -> FastAPI:
    from learning_adaptation.server import (
        mcp_resources_read,
        mcp_tools_call,
        tasks,
    )

    app = FastAPI()
    app.get("/health")(health)
    app.get("/.well-known/agent-card.json")(agent_card)
    app.post("/tasks")(tasks)
    app.get("/mcp/resources/list")(mcp_resources_list)
    app.get("/mcp/resources/read")(mcp_resources_read)
    app.get("/mcp/tools/list")(mcp_tools_list)
    app.post("/mcp/tools/call")(mcp_tools_call)

    _srv._replay_buffer = _make_replay_buffer()
    _srv._trainer = _make_trainer()
    _srv._habit_manager = _make_habit_manager()
    _srv._config = None

    yield app

    _srv._replay_buffer = None
    _srv._trainer = None
    _srv._habit_manager = None


@pytest.fixture
async def client(test_app: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def test_health(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------


async def test_agent_card_found(client: httpx.AsyncClient, tmp_path: Path) -> None:
    card = {"name": "learning-adaptation"}
    card_file = tmp_path / "agent-card.json"
    card_file.write_text(json.dumps(card))
    with patch.object(_srv, "_AGENT_CARD_PATH", card_file):
        resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "learning-adaptation"


async def test_agent_card_not_found(client: httpx.AsyncClient) -> None:
    with patch.object(_srv, "_AGENT_CARD_PATH", Path("/nonexistent/agent-card.json")):
        resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tasks (A2A)
# ---------------------------------------------------------------------------


async def test_tasks_not_initialised() -> None:
    app = FastAPI()
    from learning_adaptation.server import tasks

    app.post("/tasks")(tasks)
    _srv._replay_buffer = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/tasks", json={"id": "1", "method": "adapt_policy", "params": {}})
    assert resp.status_code == 503


async def test_tasks_adapt_policy_success(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "adapt_policy",
            "params": {
                "task_type": "adapt_policy",
                "motor_feedback": [
                    {
                        "action_id": "a1",
                        "goal_id": "g1",
                        "channel": "a2a",
                        "success": True,
                        "escalate": False,
                        "deviation_score": 0.1,
                        "reward_signal": {"value": 0.5},
                    }
                ],
            },
        },
    )
    assert resp.status_code == 200
    assert "result" in resp.json()


async def test_tasks_unknown_task(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": "2",
            "method": "unknown_task",
            "params": {"task_type": "unknown_task"},
        },
    )
    assert resp.status_code == 200  # A2A with error in result
    assert "result" in resp.json()
    assert "error" in resp.json()["result"]


# ---------------------------------------------------------------------------
# MCP resources
# ---------------------------------------------------------------------------


async def test_mcp_resources_list(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/resources/list")
    assert resp.status_code == 200
    assert "resources" in resp.json()
    assert len(resp.json()["resources"]) == 3


async def test_mcp_resources_read_policy_current(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/resources/read?uri=resource://brain.learning-adaptation/policy/current")
    assert resp.status_code == 200
    data = resp.json()
    assert "contents" in data


async def test_mcp_resources_read_replay_buffer(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/resources/read?uri=resource://brain.learning-adaptation/replay-buffer/stats")
    assert resp.status_code == 200


async def test_mcp_resources_read_habits(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/resources/read?uri=resource://brain.learning-adaptation/habits/catalog")
    assert resp.status_code == 200


async def test_mcp_resources_read_unknown(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/resources/read?uri=resource://unknown/resource")
    assert resp.status_code == 404


async def test_mcp_resources_read_not_initialised() -> None:
    app = FastAPI()
    from learning_adaptation.server import mcp_resources_read

    app.get("/mcp/resources/read")(mcp_resources_read)
    orig_t = _srv._trainer
    _srv._trainer = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/mcp/resources/read?uri=resource://brain.learning-adaptation/policy/current")
    _srv._trainer = orig_t
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


async def test_mcp_tools_list(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/tools/list")
    assert resp.status_code == 200
    assert "tools" in resp.json()
    assert len(resp.json()["tools"]) == 3


async def test_mcp_tools_call_train(client: httpx.AsyncClient) -> None:
    feedback = {
        "action_id": "a1",
        "goal_id": "g1",
        "channel": "a2a",
        "success": True,
        "escalate": False,
        "deviation_score": 0.1,
        "reward_signal": {"value": 0.5},
    }
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "train", "arguments": {"motor_feedback": [feedback]}},
    )
    assert resp.status_code == 200
    assert "content" in resp.json()


async def test_mcp_tools_call_predict(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "predict", "arguments": {"observation": [0.0] * 12}},
    )
    assert resp.status_code == 200


async def test_mcp_tools_call_promote_habit(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "promote-habit", "arguments": {"task_type": "default"}},
    )
    assert resp.status_code == 200


async def test_mcp_tools_call_unknown(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "unknown-tool", "arguments": {}},
    )
    assert resp.status_code == 404


async def test_mcp_tools_call_not_initialised() -> None:
    app = FastAPI()
    from learning_adaptation.server import mcp_tools_call

    app.post("/mcp/tools/call")(mcp_tools_call)
    orig_t = _srv._trainer
    _srv._trainer = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/mcp/tools/call", json={"name": "train", "arguments": {}})
    _srv._trainer = orig_t
    assert resp.status_code == 503
