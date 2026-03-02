"""A2A task handler for the short-term memory module.

Supported task types:
  write_record       — Write a MemoryItem to the session store.
  search_session     — Semantic search over a session.
  consolidate_item   — Consolidate a single item into LTM or episodic.
  consolidate_session — Run the full consolidation pipeline for a session.
"""

from __future__ import annotations

from typing import Any

import structlog
from endogenai_vector_store.models import MemoryItem

from short_term_memory.consolidation import ConsolidationPipeline
from short_term_memory.models import ConsolidationReport
from short_term_memory.search import SemanticSearch
from short_term_memory.store import ShortTermMemoryStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AHandler:
    """Handles incoming A2A task delegations for short-term memory."""

    def __init__(
        self,
        store: ShortTermMemoryStore,
        search: SemanticSearch,
        pipeline: ConsolidationPipeline,
    ) -> None:
        self._store = store
        self._search = search
        self._pipeline = pipeline

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an A2A task by type.

        Args:
            task_type: The A2A task type string.
            payload: Task input payload.

        Returns:
            Task output payload as a dict.

        Raises:
            ValueError: If the task_type is not recognised.
        """
        match task_type:
            case "write_record":
                item = MemoryItem.model_validate(payload["item"])
                item_id = await self._store.write(item)
                return {"item_id": item_id}

            case "search_session":
                items = await self._search.search(
                    session_id=payload["session_id"],
                    query=payload["query"],
                    top_k=int(payload.get("top_k", 10)),
                )
                return {"items": [it.model_dump() for it in items]}

            case "consolidate_session":
                report: ConsolidationReport = await self._pipeline.run(
                    payload["session_id"]
                )
                return report.model_dump()

            case "consolidate_item":
                # Single-item consolidation: write the item directly to the appropriate store.
                item = MemoryItem.model_validate(payload["item"])
                await self._store.write(item)
                return {"promoted_to": "brain.short-term-memory"}

            case _:
                raise ValueError(f"Unknown A2A task type: {task_type!r}")
