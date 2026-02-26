"""ChromaDB adapter integration tests.

These tests spin up a real ChromaDB container via Testcontainers and exercise
every operation in the VectorStoreAdapter interface contract.

Run::

    cd shared/vector-store/python
    uv run pytest tests/test_chroma.py -v

Requirements:
    docker daemon running locally (or TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE set)
    uv sync (installs testcontainers[chromadb] in dev dependencies)

No Ollama instance is needed — a deterministic MockEmbeddingClient is used.
"""

from __future__ import annotations

import uuid

import pytest

from endogenai_vector_store.interface import AdapterError
from endogenai_vector_store.models import (
    CreateCollectionRequest,
    DeleteRequest,
    DropCollectionRequest,
    MemoryType,
    QueryRequest,
    UpsertRequest,
)
from tests.conftest import make_item

# ---------------------------------------------------------------------------
# Collection lifecycle
# ---------------------------------------------------------------------------

TEST_COLLECTION = "brain.working-memory"
ALT_COLLECTION = "brain.episodic-memory"


@pytest.mark.asyncio
async def test_create_collection(chroma_adapter):
    resp = await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    assert resp.collection_name == TEST_COLLECTION
    # First call → fresh collection
    assert resp.created is True


@pytest.mark.asyncio
async def test_create_collection_idempotent(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    resp = await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    # Second call → already exists
    assert resp.created is False


@pytest.mark.asyncio
async def test_list_collections_includes_created(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    resp = await chroma_adapter.list_collections()
    names = [c.name for c in resp.collections]
    assert TEST_COLLECTION in names


@pytest.mark.asyncio
async def test_drop_collection(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=ALT_COLLECTION)
    )
    resp = await chroma_adapter.drop_collection(
        DropCollectionRequest(collection_name=ALT_COLLECTION)
    )
    assert resp.dropped is True
    assert resp.collection_name == ALT_COLLECTION

    # Verify it's gone
    list_resp = await chroma_adapter.list_collections()
    names = [c.name for c in list_resp.collections]
    assert ALT_COLLECTION not in names


@pytest.mark.asyncio
async def test_drop_collection_nonexistent(chroma_adapter):
    resp = await chroma_adapter.drop_collection(
        DropCollectionRequest(collection_name="brain.long-term-memory")
    )
    # Should return dropped=False, not raise
    assert resp.dropped is False


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_single_item(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    item = make_item(collection_name=TEST_COLLECTION, content="Hello EndogenAI")
    resp = await chroma_adapter.upsert(UpsertRequest(collection_name=TEST_COLLECTION, items=[item]))
    assert item.id in resp.upserted_ids
    # Adapter should have populated embedding on the item
    assert item.embedding is not None
    assert len(item.embedding) > 0


@pytest.mark.asyncio
async def test_upsert_multiple_items(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(collection_name=TEST_COLLECTION, content=f"Item number {i}")
        for i in range(5)
    ]
    resp = await chroma_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=items)
    )
    assert len(resp.upserted_ids) == 5
    assert set(resp.upserted_ids) == {item.id for item in items}


@pytest.mark.asyncio
async def test_upsert_overwrites_existing(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    item = make_item(collection_name=TEST_COLLECTION, content="Original content")
    await chroma_adapter.upsert(UpsertRequest(collection_name=TEST_COLLECTION, items=[item]))

    # Same ID, different content → should overwrite
    import datetime

    updated = item.model_copy(
        update={"content": "Updated content", "updated_at": datetime.datetime.utcnow().isoformat()}
    )
    resp = await chroma_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=[updated])
    )
    assert item.id in resp.upserted_ids


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_returns_results(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(
            collection_name=TEST_COLLECTION,
            content=text,
        )
        for text in [
            "the cat sat on the mat",
            "a dog ran through the park",
            "neural networks learn representations",
            "vector databases enable semantic search",
        ]
    ]
    await chroma_adapter.upsert(UpsertRequest(collection_name=TEST_COLLECTION, items=items))

    resp = await chroma_adapter.query(
        QueryRequest(
            collection_name=TEST_COLLECTION,
            query_text="machine learning embeddings",
            n_results=2,
        )
    )
    assert len(resp.results) == 2
    for result in resp.results:
        assert 0.0 <= result.score <= 1.0
        assert result.item.content != ""


@pytest.mark.asyncio
async def test_query_respects_n_results(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(collection_name=TEST_COLLECTION, content=f"Document {i}")
        for i in range(10)
    ]
    await chroma_adapter.upsert(UpsertRequest(collection_name=TEST_COLLECTION, items=items))

    resp = await chroma_adapter.query(
        QueryRequest(collection_name=TEST_COLLECTION, query_text="document", n_results=3)
    )
    assert len(resp.results) <= 3


@pytest.mark.asyncio
async def test_query_results_ordered_by_score(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(collection_name=TEST_COLLECTION, content=f"Fact about cats {i}")
        for i in range(5)
    ]
    await chroma_adapter.upsert(UpsertRequest(collection_name=TEST_COLLECTION, items=items))

    resp = await chroma_adapter.query(
        QueryRequest(collection_name=TEST_COLLECTION, query_text="cat facts", n_results=5)
    )
    scores = [r.score for r in resp.results]
    assert scores == sorted(scores, reverse=True), "Results should be ordered highest score first"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_items(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    item = make_item(collection_name=TEST_COLLECTION, content="To be deleted")
    await chroma_adapter.upsert(UpsertRequest(collection_name=TEST_COLLECTION, items=[item]))

    del_resp = await chroma_adapter.delete(
        DeleteRequest(collection_name=TEST_COLLECTION, ids=[item.id])
    )
    assert item.id in del_resp.deleted_ids

    # After deletion, querying should not return the deleted item
    query_resp = await chroma_adapter.query(
        QueryRequest(
            collection_name=TEST_COLLECTION, query_text="to be deleted", n_results=10
        )
    )
    returned_ids = [r.item.id for r in query_resp.results]
    assert item.id not in returned_ids


@pytest.mark.asyncio
async def test_delete_nonexistent_id_is_silent(chroma_adapter):
    await chroma_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    fake_id = str(uuid.uuid4())
    # Should not raise
    resp = await chroma_adapter.delete(
        DeleteRequest(collection_name=TEST_COLLECTION, ids=[fake_id])
    )
    assert fake_id in resp.deleted_ids  # ChromaDB silently accepts missing IDs


# ---------------------------------------------------------------------------
# ensure_collection helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_collection_creates_if_missing(chroma_adapter):
    name = "brain.short-term-memory"
    # Drop if exists from previous test runs
    await chroma_adapter.drop_collection(DropCollectionRequest(collection_name=name))

    created = await chroma_adapter.ensure_collection(name)
    assert created is True

    # Second call → already exists
    created = await chroma_adapter.ensure_collection(name)
    assert created is False


# ---------------------------------------------------------------------------
# Context manager protocol
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_adapter_as_context_manager(chroma_config):
    from endogenai_vector_store.chroma import ChromaAdapter
    from endogenai_vector_store.models import EmbeddingConfig, EmbeddingProvider
    from tests.conftest import MockEmbeddingClient

    async with ChromaAdapter(
        config=chroma_config,
        embedding_config=EmbeddingConfig(
            provider=EmbeddingProvider.OLLAMA, model="mock", dimensions=16
        ),
    ) as adapter:
        adapter._embedder = MockEmbeddingClient()  # type: ignore[assignment]
        resp = await adapter.list_collections()
    # After __aexit__ the adapter should be closeable without error
    assert isinstance(resp.collections, list)
