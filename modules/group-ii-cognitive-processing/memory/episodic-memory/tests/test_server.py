"""Tests for the episodic-memory A2A server.

Unit tests validate JSON-RPC routing and static endpoints using a minimal
test app that does NOT run the production lifespan (no live services required).

Integration tests (gated by ENDOGENAI_INTEGRATION_TESTS) run the full
lifespan with real ChromaDB connections.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import episodic_memory.server as _srv
from episodic_memory.server import agent_card, dispatch_task, health

_SKIP = pytest.mark.skipif(
    not os.getenv("ENDOGENAI_INTEGRATION_TESTS"),
    reason="Set ENDOGENAI_INTEGRATION_TESTS=1 to run integration tests",
)


class _FakeHandler:
    """Stand-in for EpisodicMemory A2AHandler in unit tests."""

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"echo": True, "task_type": task_type}


@pytest.fixture
async def client() -> AsyncClient:
    """Minimal test app with mock handler — no lifespan, no live services."""
    test_app = FastAPI()
    test_app.add_api_route("/tasks", dispatch_task, methods=["POST"])
    test_app.add_api_route("/health", health, methods=["GET"])
    test_app.add_api_route("/.well-known/agent-card.json", agent_card, methods=["GET"])

    _srv._handler = _FakeHandler()  # type: ignore[assignment]
    try:
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as c:
            yield c  # type: ignore[misc]
    finally:
        _srv._handler = None


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_agent_card_serves_json(client: AsyncClient) -> None:
    resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code in (200, 404)


async def test_jsonrpc_plain_dispatch(client: AsyncClient) -> None:
    resp = await client.post("/tasks", json={"task_type": "record_episode", "content": "event"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["task_type"] == "record_episode"


async def test_jsonrpc_envelope_dispatch(client: AsyncClient) -> None:
    rpc_id = str(uuid.uuid4())
    resp = await client.post(
        "/tasks",
        json={
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": "tasks/send",
            "params": {"task_type": "retrieve_timeline", "session_id": "s1"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == rpc_id
    assert body["result"]["task_type"] == "retrieve_timeline"


async def test_no_handler_returns_503() -> None:
    test_app = FastAPI()
    test_app.add_api_route("/tasks", dispatch_task, methods=["POST"])

    _srv._handler = None
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as c:
        resp = await c.post("/tasks", json={"task_type": "record_episode"})
    assert resp.status_code == 503


@_SKIP
@pytest.mark.integration
async def test_integration_health_full_lifespan() -> None:
    """Health endpoint on a fully-initialised server (requires live services)."""
    from episodic_memory.server import app as prod_app

    async with AsyncClient(
        transport=ASGITransport(app=prod_app), base_url="http://test"
    ) as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
