"""Embedding client — wraps Ollama (default) and OpenAI-compatible APIs.

Design principles:
- Local-first: default to Ollama on http://localhost:11434.
- Batching: embeds in configurable batch sizes to respect provider rate limits.
- Retry with back-off via tenacity (network transient failures only).
- Zero vendor lock-in: any OpenAI-compatible endpoint works by setting base_url.

Usage::

    client = EmbeddingClient(config=EmbeddingConfig())
    vectors = await client.embed(["hello world", "foo bar"])
"""

from __future__ import annotations

from typing import Any, cast

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from endogenai_vector_store.models import EmbeddingConfig, EmbeddingProvider

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class EmbeddingClient:
    """Async embedding client supporting Ollama and OpenAI-compatible APIs."""

    def __init__(self, config: EmbeddingConfig) -> None:
        self._config = config
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Initialise the underlying HTTP client."""
        headers: dict[str, str] = {}
        if self._config.provider != EmbeddingProvider.OLLAMA:
            import os

            api_key = os.environ.get("ENDOGEN_EMBEDDING_API_KEY", "")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        self._http = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers=headers,
            timeout=self._config.timeout_ms / 1000,
        )
        logger.info(
            "embedding_client.connected",
            provider=self._config.provider,
            model=self._config.model,
            base_url=self._config.base_url,
        )

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> EmbeddingClient:
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a list of texts.

        Handles batching internally. Order is preserved.
        Raises ``EmbeddingError`` on non-retryable failures.
        """
        if not texts:
            return []

        if self._http is None:
            await self.connect()

        batch_size = self._config.batch_size
        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

        results: list[list[float]] = []
        for batch in batches:
            vectors = await self._embed_batch(batch)
            results.extend(vectors)

        return results

    async def embed_one(self, text: str) -> list[float]:
        """Convenience wrapper for a single text."""
        vectors = await self.embed([text])
        return vectors[0]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
        reraise=True,
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        assert self._http is not None  # noqa: S101

        provider = self._config.provider
        model = self._config.model

        if provider == EmbeddingProvider.OLLAMA:
            return await self._embed_ollama(texts, model)
        else:
            # OpenAI-compatible endpoint (OpenAI, Cohere, HuggingFace TEI, etc.)
            return await self._embed_openai_compatible(texts, model)

    async def _embed_ollama(self, texts: list[str], model: str) -> list[list[float]]:
        """Ollama /api/embed endpoint (batch capable since Ollama 0.3)."""
        assert self._http is not None  # noqa: S101

        payload = {"model": model, "input": texts}
        resp = await self._http.post("/api/embed", json=payload)

        if resp.status_code != 200:
            raise EmbeddingError(
                f"Ollama embed failed: HTTP {resp.status_code} — {resp.text[:200]}",
                provider="ollama",
                retryable=resp.status_code >= 500,
            )

        data = resp.json()
        # Ollama ≥ 0.3 returns {"embeddings": [[...], ...]}
        embeddings: list[list[float]] = cast(
            "list[list[float]]", data.get("embeddings") or data.get("embedding") or []
        )
        if not embeddings:
            raise EmbeddingError(
                "Ollama embed returned empty embeddings", provider="ollama", retryable=False
            )

        # Single-text fallback: Ollama may return a flat list for single inputs
        if isinstance(embeddings[0], float):
            embeddings = cast("list[list[float]]", [embeddings])  # noqa: PGH003

        return embeddings

    async def _embed_openai_compatible(
        self, texts: list[str], model: str
    ) -> list[list[float]]:
        """OpenAI /v1/embeddings endpoint (also used by Cohere, HF TEI, etc.)."""
        assert self._http is not None  # noqa: S101

        payload = {"model": model, "input": texts}
        resp = await self._http.post("/v1/embeddings", json=payload)

        if resp.status_code != 200:
            raise EmbeddingError(
                f"Embedding API failed: HTTP {resp.status_code} — {resp.text[:200]}",
                provider=str(self._config.provider),
                retryable=resp.status_code >= 500,
            )

        data = resp.json()
        items: list[dict[str, Any]] = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]


class EmbeddingError(Exception):
    """Raised when the embedding provider returns an error."""

    def __init__(self, message: str, *, provider: str, retryable: bool) -> None:
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable
