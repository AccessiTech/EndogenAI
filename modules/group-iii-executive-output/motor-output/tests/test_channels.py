"""test_channels.py — Unit tests for individual channel handlers."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import Response
from litellm import ModelResponse

from motor_output.channels.a2a_channel import A2AChannel
from motor_output.channels.file_channel import FileChannel
from motor_output.channels.http_channel import HTTPChannel
from motor_output.channels.render_channel import RenderChannel


def _make_llm_response(content: str) -> ModelResponse:
    """Minimal non-streaming ModelResponse for test mocks."""
    return ModelResponse(
        choices=[
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    )

# ── HTTP Channel ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_http_channel_get_success() -> None:
    respx.get("http://example.com/resource").mock(
        return_value=Response(200, json={"ok": True})
    )
    chan = HTTPChannel()
    result = await chan.dispatch({"url": "http://example.com/resource", "method": "GET"})
    assert result["success"] is True
    assert result["http_status"] == 200


@pytest.mark.asyncio
@respx.mock
async def test_http_channel_missing_url_raises() -> None:
    chan = HTTPChannel()
    with pytest.raises(ValueError, match="url"):
        await chan.dispatch({})


@pytest.mark.asyncio
@respx.mock
async def test_http_channel_server_error() -> None:
    respx.post("http://example.com/api").mock(return_value=Response(500))
    chan = HTTPChannel()
    result = await chan.dispatch({"url": "http://example.com/api", "method": "POST"})
    assert result["success"] is False
    assert result["http_status"] == 500


# ── A2A Channel ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_a2a_channel_success() -> None:
    respx.post("http://service/tasks").mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "id": "x", "result": {"ok": True}})
    )
    chan = A2AChannel()
    result = await chan.dispatch({
        "a2a_url": "http://service/tasks",
        "task_type": "ping",
        "payload": {},
    })
    assert result["success"] is True


@pytest.mark.asyncio
@respx.mock
async def test_a2a_channel_missing_url_raises() -> None:
    chan = A2AChannel()
    with pytest.raises(ValueError, match="a2a_url"):
        await chan.dispatch({})


@pytest.mark.asyncio
@respx.mock
async def test_a2a_channel_rpc_error() -> None:
    respx.post("http://service/tasks").mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "id": "x", "error": {"message": "bad"}})
    )
    chan = A2AChannel()
    result = await chan.dispatch({
        "a2a_url": "http://service/tasks",
        "task_type": "fail",
        "payload": {},
    })
    assert result["success"] is False


# ── File Channel ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_file_channel_write_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chan = FileChannel(allowed_base_paths=[tmp])
        out_path = str(Path(tmp) / "output.txt")
        result = await chan.dispatch({"path": out_path, "content": "hello world"})
        assert result["success"] is True
        assert Path(out_path).read_text() == "hello world"


@pytest.mark.asyncio
async def test_file_channel_disallowed_path_raises() -> None:
    chan = FileChannel(allowed_base_paths=["/tmp/allowed"])
    with pytest.raises(PermissionError, match="allowed base path"):
        await chan.dispatch({"path": "/etc/passwd", "content": "hack"})


@pytest.mark.asyncio
async def test_file_channel_missing_path_raises() -> None:
    chan = FileChannel(allowed_base_paths=["/tmp"])
    with pytest.raises(ValueError, match="path"):
        await chan.dispatch({})


# ── Render Channel ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_render_channel_success() -> None:
    mock_response = _make_llm_response("Here is the rendered output.")

    with patch("motor_output.channels.render_channel.litellm") as mock_litellm:
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        chan = RenderChannel()
        result = await chan.dispatch({"prompt": "Summarise this", "format": "text"})
        assert result["success"] is True
        assert "Here is the rendered output." in result["content"]


@pytest.mark.asyncio
async def test_render_channel_missing_prompt_raises() -> None:
    chan = RenderChannel()
    with pytest.raises(ValueError, match="prompt"):
        await chan.dispatch({})
