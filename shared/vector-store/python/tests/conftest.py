"""Pytest fixtures for EndogenAI vector store adapter integration tests.

Requires:
    docker (local daemon or testcontainers-cloud)
    pip install endogenai-vector-store[qdrant]  (for Qdrant fixtures)

Environment variables:
    OLLAMA_HOST         — Override Ollama base URL (default: http://localhost:11434)
    SKIP_QDRANT_TESTS   — Set to any non-empty value to skip Qdrant tests when
                         no Qdrant container is available.

Testcontainers strategy:
    - ChromaDB: chromadb/chroma image on a random port (fastest boot).
    - Qdrant:   qdrant/qdrant image on random ports 6333 + 6334.
    - Ollama:   NOT containerised. Tests request embeddings from Ollama running
                on the host (avoids pulling the large Ollama model inside CI).
                If Ollama is unavailable the embedding step falls back to a
                deterministic mock via the ``mock_embedder`` fixture.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from endogenai_vector_store.models import (
    ChromaConfig,
    ChromaMode,
    EmbeddingConfig,
    EmbeddingProvider,
    MemoryItem,
    MemoryType,
    QdrantConfig,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_item(
    *,
    collection_name: str,
    content: str = "The quick brown fox jumps over the lazy dog.",
    memory_type: MemoryType = MemoryType.WORKING,
    source_module: str = "test",
    importance: float = 0.7,
) -> MemoryItem:
    """Factory for MemoryItem test fixtures."""
    import datetime

    return MemoryItem(
        id=str(uuid.uuid4()),
        collection_name=collection_name,
        content=content,
        type=memory_type,
        source_module=source_module,
        importance_score=importance,
        created_at=datetime.datetime.utcnow().isoformat(),
    )


# ---------------------------------------------------------------------------
# Mock embedding client (no Ollama required)
# ---------------------------------------------------------------------------


class MockEmbeddingClient:
    """Deterministic embedding client for unit tests.

    Returns a normalised hash-based vector so we can validate round-trips
    without running Ollama.  Dimensionality defaults to 16.
    """

    DIMENSIONS = 16

    def __init__(self, dimensions: int = DIMENSIONS) -> None:
        self.dimensions = dimensions
        self.call_count = 0

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [self._hash_embed(t) for t in texts]

    async def embed_one(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]

    def _hash_embed(self, text: str) -> list[float]:
        import hashlib
        import math

        digest = hashlib.sha256(text.encode()).digest()
        floats = []
        for i in range(self.dimensions):
            byte = digest[i % len(digest)]
            floats.append(math.sin(float(byte + i)))
        # L2-normalise
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]


# ---------------------------------------------------------------------------
# ChromaDB container fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def chroma_container() -> Generator[tuple[str, int], None, None]:
    """Start a ChromaDB Testcontainer and yield (host, port)."""
    from testcontainers.chromadb import ChromaDbContainer  # type: ignore[import-untyped]

    with ChromaDbContainer("chromadb/chroma:latest") as container:
        host = container.get_container_host_ip()
        port = int(container.get_exposed_port(8000))
        yield host, port


@pytest.fixture(scope="session")
def chroma_config(chroma_container: tuple[str, int]) -> ChromaConfig:
    host, port = chroma_container
    return ChromaConfig(mode=ChromaMode.HTTP, host=host, port=port)


@pytest_asyncio.fixture
async def chroma_adapter(
    chroma_config: ChromaConfig,
) -> AsyncGenerator:
    """A connected ChromaAdapter backed by mock embeddings (no Ollama needed)."""
    from endogenai_vector_store.chroma import ChromaAdapter

    adapter = ChromaAdapter(
        config=chroma_config,
        embedding_config=EmbeddingConfig(
            provider=EmbeddingProvider.OLLAMA,
            model="mock",
            dimensions=MockEmbeddingClient.DIMENSIONS,
        ),
    )
    # Replace real embedder with mock
    adapter._embedder = MockEmbeddingClient()  # type: ignore[assignment]
    adapter._vector_size = MockEmbeddingClient.DIMENSIONS  # type: ignore[attr-defined]  # not on ChromaAdapter but harmless
    await adapter.connect()
    yield adapter
    await adapter.close()


# ---------------------------------------------------------------------------
# Qdrant container fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qdrant_container() -> Generator[tuple[str, int, int], None, None]:
    """Start a Qdrant Testcontainer and yield (host, http_port, grpc_port)."""
    if os.environ.get("SKIP_QDRANT_TESTS"):
        pytest.skip("SKIP_QDRANT_TESTS is set")

    try:
        from testcontainers.core.container import DockerContainer  # type: ignore[import-untyped]
    except ImportError:
        pytest.skip("testcontainers not available")

    with DockerContainer("qdrant/qdrant:latest").with_exposed_ports(6333, 6334) as container:
        host = container.get_container_host_ip()
        http_port = int(container.get_exposed_port(6333))
        grpc_port = int(container.get_exposed_port(6334))
        yield host, http_port, grpc_port


@pytest.fixture(scope="session")
def qdrant_config(qdrant_container: tuple[str, int, int]) -> QdrantConfig:
    host, http_port, grpc_port = qdrant_container
    return QdrantConfig(
        host=host,
        port=http_port,
        grpc_port=grpc_port,
        use_grpc=False,  # HTTP in tests to avoid gRPC TLS complexity
    )


@pytest_asyncio.fixture
async def qdrant_adapter(
    qdrant_config: QdrantConfig,
) -> AsyncGenerator:
    """A connected QdrantAdapter backed by mock embeddings."""
    try:
        from endogenai_vector_store.qdrant import QdrantAdapter
    except ImportError:
        pytest.skip("qdrant-client not installed")

    adapter = QdrantAdapter(
        config=qdrant_config,
        embedding_config=EmbeddingConfig(
            provider=EmbeddingProvider.OLLAMA,
            model="mock",
            dimensions=MockEmbeddingClient.DIMENSIONS,
        ),
    )
    adapter._embedder = MockEmbeddingClient()  # type: ignore[assignment]
    adapter._vector_size = MockEmbeddingClient.DIMENSIONS
    await adapter.connect()
    yield adapter
    await adapter.close()


# ---------------------------------------------------------------------------
# Shared helpers exported for test modules
# ---------------------------------------------------------------------------

pytest.helpers = pytest.helpers if hasattr(pytest, "helpers") else type("helpers", (), {})()  # type: ignore[attr-defined]

# Re-export factory so tests can import from conftest
make_item = _make_item
