"""Shared pytest fixtures for episodic memory tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import (
    DeleteResponse,
    MemoryItem,
    MemoryType,
    QueryResponse,
    UpsertResponse,
)

from episodic_memory.distillation import DistillationJob
from episodic_memory.retrieval import EpisodicRetrieval
from episodic_memory.store import EpisodicStore
from episodic_memory.timeline import Timeline


def make_event(
    event_id: str = "event-1",
    content: str = "The agent completed task X successfully.",
    session_id: str = "session-abc",
    source_task_id: str = "task-xyz",
    importance_score: float = 0.7,
    affective_valence: float = 0.5,
) -> MemoryItem:
    return MemoryItem(
        id=event_id,
        collection_name="brain.episodic-memory",
        content=content,
        type=MemoryType.EPISODIC,
        source_module="episodic-memory",
        importance_score=importance_score,
        created_at="2026-03-01T12:00:00+00:00",
        metadata={
            "session_id": session_id,
            "source_task_id": source_task_id,
            "affective_valence": affective_valence,
        },
    )


@pytest.fixture
def mock_adapter() -> MagicMock:
    adapter = MagicMock(spec=ChromaAdapter)
    adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=["event-1"]))
    adapter.query = AsyncMock(return_value=QueryResponse(results=[]))
    adapter.delete = AsyncMock(return_value=DeleteResponse(deleted_ids=[]))
    return adapter


@pytest.fixture
def episodic_store(mock_adapter: MagicMock) -> EpisodicStore:
    return EpisodicStore(adapter=mock_adapter)


@pytest.fixture
def episodic_retrieval(mock_adapter: MagicMock) -> EpisodicRetrieval:
    return EpisodicRetrieval(adapter=mock_adapter)


@pytest.fixture
def timeline(mock_adapter: MagicMock) -> Timeline:
    return Timeline(adapter=mock_adapter)


@pytest.fixture
def distillation_job(mock_adapter: MagicMock) -> DistillationJob:
    return DistillationJob(
        adapter=mock_adapter,
        ltm_a2a_url="http://localhost:8053",
        min_cluster_size=2,
    )
