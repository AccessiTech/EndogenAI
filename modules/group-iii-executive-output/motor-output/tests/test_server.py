"""test_server.py — Unit tests for motor-output FastAPI server.

Tests the route layer using a minimal FastAPI test app that does NOT run the
production lifespan (no real Dispatcher/FeedbackEmitter/OTel startup).
All external dependencies are mocked via module-level attribute injection.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import motor_output.server as _srv
from motor_output.server import agent_card, a2a_tasks, health, mcp_call, mcp_list_tools, sse_endpoint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeDispatcher:
    """Minimal Dispatcher stand-in that returns a canned result."""

    async def dispatch(self, action_spec: Any) -> Any:
        return MagicMock(action_id="act-001", status="COMPLETED")


class _FakeMCPTools:
    """Minimal MCPTools stand-in."""

    def get_tool_definitions(self) -> list[dict]:
        return [{"name": "dispatch-action", "description": "test tool"}]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        return {"tool": name, "result": "ok"}


@pytest.fixture
async def client() -> AsyncClient:
    """Minimal test app with mocked module-level state."""
    test_app = FastAPI()
    test_app.add_api_route("/health", health, methods=["GET"])
    test_app.add_api_route("/.well-known/agent-card.json", agent_card, methods=["GET"])
    test_app.add_api_route("/tasks", a2a_tasks, methods=["POST"])
    test_app.add_api_route("/mcp/tools/call", mcp_call, methods=["POST"])
    test_app.add_api_route("/mcp/tools/list", mcp_list_tools, methods=["GET"])
    test_app.add_api_route("/sse", sse_endpoint, methods=["GET"])

    _srv._dispatcher = _FakeDispatcher()  # type: ignore[assignment]
    _srv._mcp_tools = _FakeMCPTools()  # type: ignore[assignment]

    try:
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as c:
            yield c  # type: ignore[misc]
    finally:
        _srv._dispatcher = None
        _srv._mcp_tools = None


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["module"] == "motor-output"


# ---------------------------------------------------------------------------
# Agent card
# ---------------------------------------------------------------------------


async def test_agent_card_not_found_returns_404(client: AsyncClient, tmp_path: Any) -> None:
    """When agent-card.json doesn't exist we get 404."""
    nonexistent = tmp_path / "missing-agent-card.json"  # does not exist
    with patch.object(_srv, "_AGENT_CARD_PATH", nonexistent):
        resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 404


async def test_agent_card_found_returns_json(tmp_path: Any, client: AsyncClient) -> None:
    card = {"name": "motor-output", "version": "0.1.0"}
    card_path = tmp_path / "agent-card.json"
    card_path.write_text(json.dumps(card))

    with patch.object(_srv, "_AGENT_CARD_PATH", card_path):
        resp = await client.get("/.well-known/agent-card.json")

    assert resp.status_code == 200
    assert resp.json()["name"] == "motor-output"


# ---------------------------------------------------------------------------
# A2A /tasks endpoint
# ---------------------------------------------------------------------------


async def test_a2a_dispatch_success(client: AsyncClient) -> None:
    """A valid JSON-RPC task envelope is dispatched and returns a result."""
    with patch("motor_output.server.handle_task", new_callable=AsyncMock) as mock_handle:
        mock_handle.return_value = {"dispatched": True}
        resp = await client.post(
            "/tasks",
            json={
                "jsonrpc": "2.0",
                "id": "req-1",
                "method": "tasks/send",
                "params": {"task_type": "dispatch_action", "action": "test"},
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "req-1"
    assert body["result"]["dispatched"] is True


async def test_a2a_no_dispatcher_returns_503() -> None:
    """When _dispatcher is None, /tasks returns 503."""
    test_app = FastAPI()
    test_app.add_api_route("/tasks", a2a_tasks, methods=["POST"])
    _srv._dispatcher = None
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        resp = await c.post(
            "/tasks",
            json={"jsonrpc": "2.0", "id": "req-2", "params": {"task_type": "x"}},
        )
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# MCP tools/list
# ---------------------------------------------------------------------------


async def test_mcp_tools_list(client: AsyncClient) -> None:
    resp = await client.get("/mcp/tools/list")
    assert resp.status_code == 200
    body = resp.json()
    assert "tools" in body
    assert any(t["name"] == "dispatch-action" for t in body["tools"])


async def test_mcp_tools_list_not_initialised() -> None:
    test_app = FastAPI()
    test_app.add_api_route("/mcp/tools/list", mcp_list_tools, methods=["GET"])
    _srv._mcp_tools = None
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        resp = await c.get("/mcp/tools/list")
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# MCP tools/call
# ---------------------------------------------------------------------------


async def test_mcp_call_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/mcp/tools/call",
        json={"name": "dispatch-action", "arguments": {"action": "test"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "content" in body
    content_text = json.loads(body["content"][0]["text"])
    assert content_text["tool"] == "dispatch-action"


async def test_mcp_call_not_initialised() -> None:
    test_app = FastAPI()
    test_app.add_api_route("/mcp/tools/call", mcp_call, methods=["POST"])
    _srv._mcp_tools = None
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        resp = await c.post("/mcp/tools/call", json={"name": "foo", "arguments": {}})
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------


async def test_sse_endpoint_returns_tools_json(client: AsyncClient) -> None:
    resp = await client.get("/sse")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    # Body contains SSE data line with tool definitions as JSON
    assert "dispatch-action" in resp.text


async def test_sse_endpoint_no_mcp_tools() -> None:
    test_app = FastAPI()
    test_app.add_api_route("/sse", sse_endpoint, methods=["GET"])
    _srv._mcp_tools = None
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        resp = await c.get("/sse")
    assert resp.status_code == 200
    assert "[]" in resp.text
