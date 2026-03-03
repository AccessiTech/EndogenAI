"""store.py — Vector store adapter for executive-agent (brain.executive-agent collection).

All reads and writes go through the shared endogenai_vector_store adapter.
Collection: brain.executive-agent (prefrontal layer, long-term memory type).

Never import chromadb or qdrant_client directly — always use this module.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_COLLECTION = "brain.executive-agent"


class ExecutiveStore:
    """Thin wrapper around VectorStoreAdapter for the executive-agent collection.

    Usage:
        store = ExecutiveStore(adapter)
        await store.upsert_goal(goal)
        results = await store.search("achieve the task")
    """

    def __init__(self, adapter: Any) -> None:  # VectorStoreAdapter typed as Any to avoid import
        self._adapter = adapter

    async def upsert_goal(self, goal: Any) -> None:
        """Embed and upsert a GoalItem into brain.executive-agent."""
        text = f"Goal [{goal.lifecycle_state}]: {goal.description}"
        metadata: dict[str, Any] = {
            "type": "goal",
            "goal_id": goal.id,
            "priority": goal.priority,
            "lifecycle_state": goal.lifecycle_state,
            "goal_class": goal.goal_class or "",
            "created_at": goal.created_at.isoformat(),
        }
        try:
            await self._adapter.upsert(
                collection_name=_COLLECTION,
                texts=[text],
                metadatas=[metadata],
                ids=[goal.id],
            )
            logger.debug("store.goal_upserted", goal_id=goal.id)
        except Exception as exc:
            logger.warning("store.upsert_error", goal_id=goal.id, error=str(exc))

    async def upsert_identity_delta(self, delta: dict[str, Any]) -> None:
        """Append an identity delta record to brain.executive-agent."""
        text = f"Identity delta: {json.dumps(delta)}"
        metadata: dict[str, Any] = {
            "type": "identity_delta",
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        try:
            await self._adapter.upsert(
                collection_name=_COLLECTION,
                texts=[text],
                metadatas=[metadata],
            )
            logger.debug("store.identity_delta_stored")
        except Exception as exc:
            logger.warning("store.identity_delta_error", error=str(exc))

    async def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Semantic search over brain.executive-agent."""
        try:
            results: list[dict[str, Any]] = await self._adapter.query(
                collection_name=_COLLECTION,
                query_texts=[query],
                n_results=n_results,
            )
            return results
        except Exception as exc:
            logger.warning("store.search_error", query=query[:50], error=str(exc))
            return []
