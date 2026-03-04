"""test_server.py — Unit tests for agent-runtime FastAPI server routes.

Tests all HTTP endpoints without spawning the full lifespan:
  GET  /health
  GET  /.well-known/agent-card.json
  POST /tasks
  POST /mcp/tools/call
  GET  /sse
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

import agent_runtime.server as _srv
from agent_runtime.models import ExecutionStatus, PipelineStatus
from agent_runtime.server import agent_card, health, mcp_call, tasks


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    orch = MagicMock()
    orch.execute_intention = AsyncMock(
        return_value={"workflow_id": "wf-1", "orchestrator": "temporal"}
    )
    orch.abort_execution = AsyncMock(return_value={"goal_id": "g-1", "status": "aborted"})
    orch.get_execution_status = AsyncMock(
        return_value=ExecutionStatus(
            goal_id="g-1", workflow_id="wf-1", status=PipelineStatus.RUNNING
        )
    )
    orch._temporal_client = None
    orch._build_workflow_id = MagicMock(return_value="wf-1")
    return orch


@pytest.fixture
def mock_mcp_tools() -> MagicMock:
    tools = MagicMock()
    tools.handle = AsyncMock(return_value={"result": "ok"})
    return tools


@pytest.fixture
def test_app(mock_orchestrator: MagicMock, mock_mcp_tools: MagicMock) -> FastAPI:
    app = FastAPI()
    app.get("/health")(health)
    app.get("/.well-known/agent-card.json")(agent_card)
    app.post("/tasks")(tasks)
    app.post("/mcp/tools/call")(mcp_call)

    _srv._orchestrator = mock_orchestrator
    _srv._tool_registry = MagicMock()
    _srv._mcp_tools = mock_mcp_tools
    yield app

    _srv._orchestrator = None
    _srv._tool_registry = None
    _srv._mcp_tools = None


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
    data = resp.json()
    assert data["status"] == "ok"
    assert data["orchestrator"] is True


async def test_health_orchestrator_none() -> None:
    app = FastAPI()
    app.get("/health")(health)
    orig = _srv._orchestrator
    _srv._orchestrator = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/health")
    _srv._orchestrator = orig
    assert resp.json()["orchestrator"] is False


# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------


async def test_agent_card_found(client: httpx.AsyncClient, tmp_path: Path) -> None:
    card = {"name": "agent-runtime", "skills": []}
    card_file = tmp_path / "agent-card.json"
    card_file.write_text(json.dumps(card))
    with patch.object(_srv, "_AGENT_CARD_PATH", card_file):
        resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "agent-runtime"


# ---------------------------------------------------------------------------
# A2A tasks
# ---------------------------------------------------------------------------


async def test_tasks_execute_intention(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "execute_intention",
            "params": {"goal_id": "g-1"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    assert data["result"]["workflow_id"] == "wf-1"


async def test_tasks_unknown_method(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": "2",
            "method": "unknown_task",
            "params": {},
        },
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


async def test_tasks_get_status(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": "3",
            "method": "get_status",
            "params": {"goal_id": "g-1"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["goal_id"] == "g-1"


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


async def test_mcp_call_success(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "agent_runtime.execute", "parameters": {"goal_id": "g-1"}},
    )
    assert resp.status_code == 200
    assert "result" in resp.json()


async def test_mcp_call_unknown_tool(
    client: httpx.AsyncClient, mock_mcp_tools: MagicMock
) -> None:
    mock_mcp_tools.handle = AsyncMock(side_effect=ValueError("Unknown MCP tool"))
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "unknown_tool", "parameters": {}},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


async def test_mcp_call_none_tools() -> None:
    """When _mcp_tools is None, call raises and returns 500."""
    app = FastAPI()
    app.post("/mcp/tools/call")(mcp_call)
    orig = _srv._mcp_tools
    _srv._mcp_tools = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/mcp/tools/call",
            json={"name": "some_tool", "parameters": {}},
        )
    _srv._mcp_tools = orig
    assert resp.status_code == 500


async def test_tasks_internal_error(
    client: httpx.AsyncClient, mock_orchestrator: MagicMock
) -> None:
    """When handle_task raises non-ValueError, returns 500."""
    mock_orchestrator.execute_intention = AsyncMock(side_effect=RuntimeError("unexpected"))
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": "4",
            "method": "execute_intention",
            "params": {"goal_id": "g-1"},
        },
    )
    assert resp.status_code == 500
    data = resp.json()
    assert "error" in data


# ---------------------------------------------------------------------------
# SSE — test the generator directly to avoid infinite-loop hang
# ---------------------------------------------------------------------------


async def test_sse_no_agent_card(test_app: FastAPI) -> None:
    """SSE sends an empty tools_available event when no agent card exists."""
    from agent_runtime.server import sse

    with patch.object(_srv, "_AGENT_CARD_PATH", Path("/nonexistent/agent-card.json")):
        response = await sse()

    # Consume only the first chunk from the generator
    gen = response.body_iterator
    first_chunk = await gen.__anext__()
    assert "tools_available" in first_chunk
    assert '"tools": []' in first_chunk or '"tools":[]' in first_chunk
    # Cleanly close the generator to avoid ResourceWarning
    await gen.aclose()


async def test_sse_with_agent_card(tmp_path: Path) -> None:
    """SSE streams skills from agent card when it exists."""
    from agent_runtime.server import sse

    card = {"name": "agent-runtime", "skills": [{"id": "skill-1", "name": "test"}]}
    card_file = tmp_path / "agent-card.json"
    card_file.write_text(json.dumps(card))
    with patch.object(_srv, "_AGENT_CARD_PATH", card_file):
        response = await sse()

    gen = response.body_iterator
    first_chunk = await gen.__anext__()
    data_line = first_chunk.split("data: ", 1)[1].split("\n")[0]
    payload = json.loads(data_line)
    assert len(payload["tools"]) == 1
    assert payload["tools"][0]["id"] == "skill-1"
    await gen.aclose()
