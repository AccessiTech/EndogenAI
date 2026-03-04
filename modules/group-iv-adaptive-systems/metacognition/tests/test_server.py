"""test_server.py — Unit tests for metacognition FastAPI server routes.

Tests all HTTP endpoints without spawning the full lifespan:
  GET  /health
  GET  /.well-known/agent-card.json
  POST /tasks
  GET  /mcp/resources/list
  GET  /mcp/resources/read
  GET  /mcp/tools/list
  POST /mcp/tools/call
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse

import metacognition.server as _srv
from metacognition.evaluation.evaluator import MetacognitionEvaluator, MonitoringConfig
from metacognition.instrumentation.metrics import MetricsBundle
from metacognition.server import (
    agent_card,
    health,
    mcp_resources_list,
    mcp_resources_read,
    mcp_tools_call,
    mcp_tools_list,
    tasks_endpoint,
)
from metacognition.store.monitoring_store import MonitoringStore


# ---------------------------------------------------------------------------
# Test app fixture
# ---------------------------------------------------------------------------


def _make_metrics_bundle() -> MetricsBundle:
    gauge = MagicMock()
    counter = MagicMock()
    histogram = MagicMock()
    return MetricsBundle(
        task_confidence=gauge,
        deviation_score=gauge,
        reward_delta=histogram,
        task_success_rate=gauge,
        escalation_total=counter,
        retry_count=histogram,
        policy_denial_rate=gauge,
        deviation_zscore=gauge,
    )


@pytest.fixture
def evaluator() -> MetacognitionEvaluator:
    return MetacognitionEvaluator(
        config=MonitoringConfig(), metrics_bundle=_make_metrics_bundle()
    )


@pytest.fixture
def test_app(evaluator: MetacognitionEvaluator) -> FastAPI:
    app = FastAPI()
    app.get("/health")(health)
    app.get("/.well-known/agent-card.json")(agent_card)
    app.post("/tasks")(tasks_endpoint)
    app.get("/mcp/resources/list")(mcp_resources_list)
    app.get("/mcp/resources/read")(mcp_resources_read)
    app.get("/mcp/tools/list")(mcp_tools_list)
    app.post("/mcp/tools/call")(mcp_tools_call)

    store = MagicMock(spec=MonitoringStore)
    store.append = AsyncMock()

    _srv._evaluator = evaluator
    _srv._store = store
    yield app
    _srv._evaluator = None
    _srv._store = None


@pytest.fixture
async def client(test_app: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "module": "metacognition"}


# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------


async def test_agent_card_not_found(client: httpx.AsyncClient) -> None:
    with patch.object(_srv, "_AGENT_CARD_PATH", Path("/nonexistent/agent-card.json")):
        resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 404


async def test_agent_card_found(client: httpx.AsyncClient, tmp_path: Path) -> None:
    card = {"name": "metacognition"}
    card_file = tmp_path / "agent-card.json"
    card_file.write_text(json.dumps(card))
    with patch.object(_srv, "_AGENT_CARD_PATH", card_file):
        resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "metacognition"


# ---------------------------------------------------------------------------
# A2A tasks
# ---------------------------------------------------------------------------


async def test_tasks_evaluate_output(client: httpx.AsyncClient) -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "task_type": "evaluate_output",
            "goal_id": "g-1",
            "action_id": "a-1",
            "success": True,
            "escalate": False,
            "deviation_score": 0.1,
            "reward_value": 0.8,
        },
    }
    resp = await client.post("/tasks", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data


async def test_tasks_unknown_method(client: httpx.AsyncClient) -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "unknown_method",
        "params": {},
    }
    resp = await client.post("/tasks", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data


async def test_tasks_not_initialised() -> None:
    """When evaluator is None, get_evaluator() raises RuntimeError."""
    orig_evaluator = _srv._evaluator
    _srv._evaluator = None
    try:
        with pytest.raises(RuntimeError, match="not initialised"):
            _srv.get_evaluator()
    finally:
        _srv._evaluator = orig_evaluator


# ---------------------------------------------------------------------------
# MCP resources
# ---------------------------------------------------------------------------


async def test_mcp_resources_list(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/resources/list")
    assert resp.status_code == 200
    assert "resources" in resp.json()


async def test_mcp_resources_read_confidence(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/mcp/resources/read",
        params={"uri": "resource://brain.metacognition/confidence/current"},
    )
    assert resp.status_code == 200
    assert "contents" in resp.json()


async def test_mcp_resources_read_anomalies(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/mcp/resources/read",
        params={"uri": "resource://brain.metacognition/anomalies/recent"},
    )
    assert resp.status_code == 200


async def test_mcp_resources_read_report(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/mcp/resources/read",
        params={"uri": "resource://brain.metacognition/report/session"},
    )
    assert resp.status_code == 200


async def test_mcp_resources_read_unknown_uri(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/mcp/resources/read",
        params={"uri": "resource://unknown"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


async def test_mcp_tools_list(client: httpx.AsyncClient) -> None:
    resp = await client.get("/mcp/tools/list")
    assert resp.status_code == 200
    assert "tools" in resp.json()


async def test_mcp_tools_call_evaluate(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={
            "name": "evaluate",
            "arguments": {
                "goal_id": "g-1",
                "action_id": "a-1",
                "success": True,
                "escalate": False,
                "deviation_score": 0.1,
                "reward_value": 0.8,
            },
        },
    )
    assert resp.status_code == 200
    assert "content" in resp.json()


async def test_mcp_tools_call_configure_threshold(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "configure-threshold", "arguments": {"confidence_threshold": 0.6}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data


async def test_mcp_tools_call_report(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "report", "arguments": {}},
    )
    assert resp.status_code == 200


async def test_mcp_tools_call_unknown_tool(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "nonexistent", "arguments": {}},
    )
    assert resp.status_code == 404
