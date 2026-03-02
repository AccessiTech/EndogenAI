"""Unit tests for A2AClient using httpx.MockTransport.

All tests run without network I/O — the transport is replaced with a mock
that returns pre-configured JSON-RPC 2.0 responses.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock

import httpx
import pytest

from endogenai_a2a.client import A2AClient
from endogenai_a2a.exceptions import A2AError, A2AProtocolError, A2ATaskNotFound


def _make_success_response(request_id: str, result: dict) -> httpx.Response:
    """Build a successful JSON-RPC 2.0 response."""
    body = {"jsonrpc": "2.0", "id": request_id, "result": result}
    return httpx.Response(200, json=body)


def _make_error_response(request_id: str, code: str, message: str) -> httpx.Response:
    """Build an error JSON-RPC 2.0 response."""
    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    return httpx.Response(200, json=body)


class TestA2AClientSendTask:
    """Tests for A2AClient.send_task()."""

    async def test_send_task_returns_result(self) -> None:
        """send_task returns the result dict on success."""
        captured: list[httpx.Request] = []

        def transport_handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            req_body = json.loads(request.content)
            return _make_success_response(req_body["id"], {"status": "ok", "task_id": "t-1"})

        transport = httpx.MockTransport(transport_handler)
        mock_client = httpx.AsyncClient(transport=transport)

        client = A2AClient(url="http://localhost:8202", http_client=mock_client)
        result = await client.send_task("consolidate_item", {"item": {"id": "x"}})

        assert result == {"status": "ok", "task_id": "t-1"}
        assert len(captured) == 1
        req_body = json.loads(captured[0].content)
        assert req_body["method"] == "tasks/send"
        assert req_body["params"]["task_type"] == "consolidate_item"
        assert req_body["params"]["item"] == {"id": "x"}

    async def test_send_task_raises_protocol_error_on_rpc_error(self) -> None:
        """send_task raises A2AProtocolError when the response contains an error."""

        def transport_handler(request: httpx.Request) -> httpx.Response:
            req_body = json.loads(request.content)
            return _make_error_response(req_body["id"], "invalid-input", "bad payload")

        transport = httpx.MockTransport(transport_handler)
        mock_client = httpx.AsyncClient(transport=transport)

        client = A2AClient(url="http://localhost:8202", http_client=mock_client)
        with pytest.raises(A2AProtocolError, match="tasks/send returned error"):
            await client.send_task("consolidate_item", {})

    async def test_send_task_raises_a2a_error_on_http_failure(self) -> None:
        """send_task raises A2AError when the transport raises a network error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = httpx.ConnectError("refused")

        client = A2AClient(url="http://localhost:8202", http_client=mock_client)
        with pytest.raises(A2AError):
            await client.send_task("consolidate_item", {})

    async def test_send_task_url_construction(self) -> None:
        """send_task posts to {base_url}/tasks, stripping trailing slash."""
        captured: list[str] = []

        def transport_handler(request: httpx.Request) -> httpx.Response:
            captured.append(str(request.url))
            req_body = json.loads(request.content)
            return _make_success_response(req_body["id"], {})

        transport = httpx.MockTransport(transport_handler)
        mock_client = httpx.AsyncClient(transport=transport)

        client = A2AClient(url="http://localhost:8202/", http_client=mock_client)
        await client.send_task("noop", {})

        assert captured[0] == "http://localhost:8202/tasks"


class TestA2AClientGetTask:
    """Tests for A2AClient.get_task()."""

    async def test_get_task_returns_result(self) -> None:
        """get_task returns the result dict on success."""
        task_id = str(uuid.uuid4())
        expected = {"id": task_id, "status": {"state": "completed"}}

        def transport_handler(request: httpx.Request) -> httpx.Response:
            req_body = json.loads(request.content)
            assert req_body["method"] == "tasks/get"
            assert req_body["params"]["id"] == task_id
            return _make_success_response(req_body["id"], expected)

        transport = httpx.MockTransport(transport_handler)
        mock_client = httpx.AsyncClient(transport=transport)

        client = A2AClient(url="http://localhost:8202", http_client=mock_client)
        result = await client.get_task(task_id)

        assert result == expected

    async def test_get_task_raises_not_found_on_null_result(self) -> None:
        """get_task raises A2ATaskNotFound when the server returns null result."""

        def transport_handler(request: httpx.Request) -> httpx.Response:
            req_body = json.loads(request.content)
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": req_body["id"], "result": None})

        transport = httpx.MockTransport(transport_handler)
        mock_client = httpx.AsyncClient(transport=transport)

        client = A2AClient(url="http://localhost:8202", http_client=mock_client)
        with pytest.raises(A2ATaskNotFound):
            await client.get_task("does-not-exist")

    async def test_get_task_raises_protocol_error_on_rpc_error(self) -> None:
        """get_task raises A2AProtocolError when the server returns an RPC error."""

        def transport_handler(request: httpx.Request) -> httpx.Response:
            req_body = json.loads(request.content)
            return _make_error_response(req_body["id"], "not-found", "no such task")

        transport = httpx.MockTransport(transport_handler)
        mock_client = httpx.AsyncClient(transport=transport)

        client = A2AClient(url="http://localhost:8202", http_client=mock_client)
        with pytest.raises(A2AProtocolError, match="tasks/get returned error"):
            await client.get_task("some-id")
