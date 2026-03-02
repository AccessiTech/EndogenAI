"""A2A task handler for the working memory module."""

from __future__ import annotations

from typing import Any

import structlog

from working_memory.consolidation import ConsolidationDispatcher
from working_memory.loader import ContextLoader
from working_memory.models import ConsolidationReport, ContextPayload
from working_memory.store import WorkingMemoryStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AHandler:
    """Handles incoming A2A task delegations for working memory."""

    def __init__(
        self,
        store: WorkingMemoryStore,
        loader: ContextLoader,
        dispatcher: ConsolidationDispatcher,
    ) -> None:
        self._store = store
        self._loader = loader
        self._dispatcher = dispatcher

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an A2A task by type."""
        match task_type:
            case "assemble_context":
                context: ContextPayload = await self._loader.load(
                    session_id=payload["session_id"],
                    query=payload["query"],
                )
                return context.model_dump()

            case "consolidate_session":
                # Flush all items for the specified session
                items = [
                    active
                    for active in self._store.list_active()
                    if active.metadata.get("session_id") == payload.get("session_id")
                ]
                for item in items:
                    evicted = self._store.evict(item.id)
                    if evicted is not None:
                        await self._dispatcher.dispatch(evicted)
                return ConsolidationReport(
                    session_id=payload.get("session_id", ""),
                    items_flushed=len(items),
                ).model_dump()

            case "apply_affective_boost":
                updated = self._store.update(
                    payload["item_id"],
                    {"importance_score": min(float(payload.get("reward_value", 0.1)), 1.0)},
                )
                if updated is None:
                    raise ValueError(f"Item not found: {payload['item_id']!r}")
                return updated.model_dump()

            case _:
                raise ValueError(f"Unknown A2A task type: {task_type!r}")
