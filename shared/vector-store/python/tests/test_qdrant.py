"""Qdrant adapter integration tests.

These tests spin up a real Qdrant container via Testcontainers and exercise
every operation in the VectorStoreAdapter interface contract.

Run::

    cd shared/vector-store/python
    uv run pytest tests/test_qdrant.py -v

Requirements:
    docker daemon running locally
    pip install endogenai-vector-store[qdrant]
    uv sync

Set SKIP_QDRANT_TESTS=1 to skip these tests (e.g. in environments without Docker).

No Ollama instance is needed — a deterministic MockEmbeddingClient is used.
"""

from __future__ import annotations

import os
import uuid

import pytest

from endogenai_vector_store.models import (
    CreateCollectionRequest,
    DeleteRequest,
    DropCollectionRequest,
    QueryRequest,
    UpsertRequest,
)
from tests.conftest import make_item

pytestmark = pytest.mark.skipif(
    bool(os.environ.get("SKIP_QDRANT_TESTS")),
    reason="SKIP_QDRANT_TESTS is set",
)

TEST_COLLECTION = "brain.long-term-memory"
ALT_COLLECTION = "brain.metacognition"


# ---------------------------------------------------------------------------
# Collection lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_collection(qdrant_adapter):
    resp = await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    assert resp.collection_name == TEST_COLLECTION
    assert resp.created is True


@pytest.mark.asyncio
async def test_create_collection_idempotent(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    resp = await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    assert resp.created is False


@pytest.mark.asyncio
async def test_list_collections_includes_created(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    resp = await qdrant_adapter.list_collections()
    names = [c.name for c in resp.collections]
    assert TEST_COLLECTION in names


@pytest.mark.asyncio
async def test_drop_collection(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=ALT_COLLECTION)
    )
    resp = await qdrant_adapter.drop_collection(
        DropCollectionRequest(collection_name=ALT_COLLECTION)
    )
    assert resp.dropped is True

    list_resp = await qdrant_adapter.list_collections()
    names = [c.name for c in list_resp.collections]
    assert ALT_COLLECTION not in names


@pytest.mark.asyncio
async def test_drop_nonexistent_collection(qdrant_adapter):
    resp = await qdrant_adapter.drop_collection(
        DropCollectionRequest(collection_name="brain.reasoning")
    )
    assert resp.dropped is False


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_single_item(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    item = make_item(collection_name=TEST_COLLECTION, content="Qdrant is a vector database")
    resp = await qdrant_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=[item])
    )
    assert item.id in resp.upserted_ids
    assert item.embedding is not None and len(item.embedding) > 0


@pytest.mark.asyncio
async def test_upsert_batch_of_items(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(collection_name=TEST_COLLECTION, content=f"Qdrant batch item {i}")
        for i in range(8)
    ]
    resp = await qdrant_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=items)
    )
    assert len(resp.upserted_ids) == 8


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_returns_results(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(collection_name=TEST_COLLECTION, content=text)
        for text in [
            "Qdrant supports payload filtering",
            "vector similarity search at scale",
            "gRPC improves throughput",
            "cosine distance for embeddings",
        ]
    ]
    await qdrant_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=items)
    )

    resp = await qdrant_adapter.query(
        QueryRequest(
            collection_name=TEST_COLLECTION,
            query_text="fast vector retrieval database",
            n_results=2,
        )
    )
    assert len(resp.results) == 2
    for result in resp.results:
        assert result.score >= 0.0
        assert result.item.content != ""


@pytest.mark.asyncio
async def test_query_respects_n_results(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    items = [
        make_item(collection_name=TEST_COLLECTION, content=f"Qdrant record {i}")
        for i in range(10)
    ]
    await qdrant_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=items)
    )

    resp = await qdrant_adapter.query(
        QueryRequest(collection_name=TEST_COLLECTION, query_text="record", n_results=4)
    )
    assert len(resp.results) <= 4


@pytest.mark.asyncio
async def test_query_with_metadata_filter(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    tag_a = make_item(
        collection_name=TEST_COLLECTION,
        content="Important fact",
        source_module="reasoning",
    )
    tag_b = make_item(
        collection_name=TEST_COLLECTION,
        content="Another fact",
        source_module="perception",
    )
    await qdrant_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=[tag_a, tag_b])
    )

    resp = await qdrant_adapter.query(
        QueryRequest(
            collection_name=TEST_COLLECTION,
            query_text="fact",
            n_results=10,
            where={"source_module": "reasoning"},
        )
    )
    for result in resp.results:
        assert result.item.source_module == "reasoning"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_item(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    item = make_item(collection_name=TEST_COLLECTION, content="To be removed from Qdrant")
    await qdrant_adapter.upsert(
        UpsertRequest(collection_name=TEST_COLLECTION, items=[item])
    )

    del_resp = await qdrant_adapter.delete(
        DeleteRequest(collection_name=TEST_COLLECTION, ids=[item.id])
    )
    assert item.id in del_resp.deleted_ids

    query_resp = await qdrant_adapter.query(
        QueryRequest(
            collection_name=TEST_COLLECTION, query_text="removed from Qdrant", n_results=10
        )
    )
    returned_ids = [r.item.id for r in query_resp.results]
    assert item.id not in returned_ids


@pytest.mark.asyncio
async def test_delete_nonexistent_id_is_silent(qdrant_adapter):
    await qdrant_adapter.create_collection(
        CreateCollectionRequest(collection_name=TEST_COLLECTION)
    )
    fake_id = str(uuid.uuid4())
    resp = await qdrant_adapter.delete(
        DeleteRequest(collection_name=TEST_COLLECTION, ids=[fake_id])
    )
    # Qdrant silently ignores missing IDs
    assert fake_id in resp.deleted_ids


# ---------------------------------------------------------------------------
# ensure_collection helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_collection(qdrant_adapter):
    name = "brain.knowledge"
    # Drop if leftover
    await qdrant_adapter.drop_collection(DropCollectionRequest(collection_name=name))

    created = await qdrant_adapter.ensure_collection(name)
    assert created is True

    created_again = await qdrant_adapter.ensure_collection(name)
    assert created_again is False
