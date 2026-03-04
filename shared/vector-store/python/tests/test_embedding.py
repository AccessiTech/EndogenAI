"""test_embedding.py — Unit tests for EmbeddingClient.

Tests cover:
  - Connect / close lifecycle
  - embed([]) returns empty list without HTTP call
  - embed_one() convenience wrapper
  - _embed_ollama() success path (batch and single-text fallback)
  - _embed_ollama() error path (HTTP 4xx non-retryable, HTTP 5xx retryable)
  - _embed_openai_compatible() success path
  - _embed_openai_compatible() error path
  - Automatic connect() on first embed() call
  - Batch splitting respects batch_size
  - EmbeddingError attributes
  - ENDOGEN_EMBEDDING_API_KEY injected as Authorization header for non-Ollama

All tests mock httpx.AsyncClient — no live Ollama or OpenAI endpoint required.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from endogenai_vector_store.embedding import EmbeddingClient, EmbeddingError
from endogenai_vector_store.models import EmbeddingConfig, EmbeddingProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ollama_response(vectors: list[list[float]]) -> MagicMock:
    """Return a mock httpx.Response for an Ollama /api/embed success."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"embeddings": vectors}
    return resp


def _make_openai_response(vectors: list[list[float]]) -> MagicMock:
    """Return a mock httpx.Response for an OpenAI /v1/embeddings success."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": [{"index": i, "embedding": v} for i, v in enumerate(vectors)]
    }
    return resp


def _make_error_response(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = f"error {status_code}"
    return resp


def _ollama_config(batch_size: int = 10) -> EmbeddingConfig:
    return EmbeddingConfig(
        provider=EmbeddingProvider.OLLAMA,
        model="nomic-embed-text",
        base_url="http://localhost:11434",
        batch_size=batch_size,
    )


def _openai_config() -> EmbeddingConfig:
    return EmbeddingConfig(
        provider=EmbeddingProvider.OPENAI,
        model="text-embedding-3-small",
        base_url="http://localhost:8080",
    )


# ---------------------------------------------------------------------------
# EmbeddingError
# ---------------------------------------------------------------------------


def test_embedding_error_attributes() -> None:
    err = EmbeddingError("bad request", provider="ollama", retryable=False)
    assert err.provider == "ollama"
    assert err.retryable is False
    assert "bad request" in str(err)


def test_embedding_error_retryable() -> None:
    err = EmbeddingError("server error", provider="openai", retryable=True)
    assert err.retryable is True
    assert err.provider == "openai"


# ---------------------------------------------------------------------------
# Lifecycle — connect / close
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_creates_http_client() -> None:
    client = EmbeddingClient(_ollama_config())
    assert client._http is None
    await client.connect()
    assert client._http is not None
    await client.close()


@pytest.mark.asyncio
async def test_close_nulls_http_client() -> None:
    client = EmbeddingClient(_ollama_config())
    await client.connect()
    await client.close()
    assert client._http is None


@pytest.mark.asyncio
async def test_close_when_already_closed_is_noop() -> None:
    client = EmbeddingClient(_ollama_config())
    # Should not raise
    await client.close()
    assert client._http is None


@pytest.mark.asyncio
async def test_context_manager() -> None:
    config = _ollama_config()
    async with EmbeddingClient(config) as client:
        assert client._http is not None
    assert client._http is None


# ---------------------------------------------------------------------------
# embed([]) edge case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_empty_list_returns_empty() -> None:
    client = EmbeddingClient(_ollama_config())
    result = await client.embed([])
    assert result == []
    # HTTP client must NOT have been initialised for an empty call
    assert client._http is None


# ---------------------------------------------------------------------------
# Ollama embed path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_ollama_success() -> None:
    config = _ollama_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(
        return_value=_make_ollama_response([[0.1, 0.2], [0.3, 0.4]])
    )
    client._http = mock_http

    result = await client.embed(["hello", "world"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    mock_http.post.assert_called_once()
    call_kwargs = mock_http.post.call_args
    assert call_kwargs[0][0] == "/api/embed"


@pytest.mark.asyncio
async def test_embed_one_returns_single_vector() -> None:
    config = _ollama_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_make_ollama_response([[0.5, 0.6, 0.7]]))
    client._http = mock_http

    result = await client.embed_one("single text")
    assert result == [0.5, 0.6, 0.7]


@pytest.mark.asyncio
async def test_embed_ollama_single_text_flat_list_fallback() -> None:
    """Ollama may return a flat float list for a single input — must be wrapped."""
    config = _ollama_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    flat_resp = MagicMock()
    flat_resp.status_code = 200
    # Flat list (not nested) — the old Ollama behaviour
    flat_resp.json.return_value = {"embeddings": [0.1, 0.2, 0.3]}
    mock_http.post = AsyncMock(return_value=flat_resp)
    client._http = mock_http

    result = await client.embed(["single"])
    assert result == [[0.1, 0.2, 0.3]]


@pytest.mark.asyncio
async def test_embed_ollama_http4xx_raises_non_retryable() -> None:
    config = _ollama_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_make_error_response(400))
    client._http = mock_http

    with pytest.raises(EmbeddingError) as exc_info:
        await client._embed_batch(["text"])

    assert exc_info.value.provider == "ollama"
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_embed_ollama_http5xx_raises_retryable() -> None:
    config = _ollama_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_make_error_response(503))
    client._http = mock_http

    with pytest.raises(EmbeddingError) as exc_info:
        # tenacity will retry up to 3× before re-raising
        await client._embed_batch(["text"])

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_embed_ollama_empty_embeddings_raise() -> None:
    config = _ollama_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    empty_resp = MagicMock()
    empty_resp.status_code = 200
    empty_resp.json.return_value = {"embeddings": []}
    mock_http.post = AsyncMock(return_value=empty_resp)
    client._http = mock_http

    with pytest.raises(EmbeddingError, match="empty embeddings"):
        await client._embed_batch(["text"])


# ---------------------------------------------------------------------------
# OpenAI-compatible embed path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_openai_success() -> None:
    config = _openai_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(
        return_value=_make_openai_response([[0.9, 0.8], [0.7, 0.6]])
    )
    client._http = mock_http

    result = await client.embed(["a", "b"])
    assert result == [[0.9, 0.8], [0.7, 0.6]]
    call_args = mock_http.post.call_args
    assert call_args[0][0] == "/v1/embeddings"


@pytest.mark.asyncio
async def test_embed_openai_http_error_raises() -> None:
    config = _openai_config()
    client = EmbeddingClient(config)
    await client.connect()

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_make_error_response(401))
    client._http = mock_http

    with pytest.raises(EmbeddingError) as exc_info:
        await client._embed_batch(["text"])

    assert exc_info.value.retryable is False


# ---------------------------------------------------------------------------
# Batching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batching_splits_calls() -> None:
    """batch_size=2 with 5 texts should dispatch 3 HTTP calls."""
    config = _ollama_config(batch_size=2)
    client = EmbeddingClient(config)
    await client.connect()

    call_count = 0

    async def _mock_post(path: str, **kwargs: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        batch = kwargs.get("json", {}).get("input", [])
        return _make_ollama_response([[float(i)] for i in range(len(batch))])

    mock_http = AsyncMock()
    mock_http.post = _mock_post
    client._http = mock_http

    texts = ["a", "b", "c", "d", "e"]
    result = await client.embed(texts)

    assert call_count == 3  # ceil(5/2) = 3
    assert len(result) == 5


# ---------------------------------------------------------------------------
# Auto-connect on first embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_auto_connects() -> None:
    """embed() should implicitly call connect() if _http is None."""
    config = _ollama_config()
    client = EmbeddingClient(config)
    assert client._http is None

    with patch.object(
        client,
        "_embed_batch",
        new_callable=AsyncMock,
        return_value=[[0.0, 1.0]],
    ) as mock_batch:
        result = await client.embed(["hi"])

    assert result == [[0.0, 1.0]]
    # connect() was called since _http was None → now set
    assert client._http is not None
    await client.close()


# ---------------------------------------------------------------------------
# API key header injected for non-Ollama providers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_api_key_header_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENDOGEN_EMBEDDING_API_KEY", "secret-key")
    config = _openai_config()
    client = EmbeddingClient(config)

    mock_http_instance = AsyncMock(spec=httpx.AsyncClient)
    mock_http_class = MagicMock(return_value=mock_http_instance)

    with patch("endogenai_vector_store.embedding.httpx.AsyncClient", mock_http_class):
        await client.connect()

    init_kwargs = mock_http_class.call_args.kwargs
    headers = init_kwargs.get("headers", {})
    assert headers.get("Authorization") == "Bearer secret-key"
