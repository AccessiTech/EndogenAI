"""MCP tool definitions for the working memory module."""

from __future__ import annotations

from typing import Any

import structlog
from endogenai_vector_store.models import MemoryItem

from working_memory.consolidation import ConsolidationDispatcher
from working_memory.loader import ContextLoader
from working_memory.models import ContextPayload
from working_memory.store import WorkingMemoryStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for working memory operations."""

    def __init__(
        self,
        store: WorkingMemoryStore,
        loader: ContextLoader,
        dispatcher: ConsolidationDispatcher,
    ) -> None:
        self._store = store
        self._loader = loader
        self._dispatcher = dispatcher

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name."""
        match tool_name:
            case "working_memory.assemble_context":
                payload: ContextPayload = await self._loader.load(
                    session_id=params["session_id"],
                    query=params["query"],
                    capacity_override=params.get("capacity_override"),
                )
                return payload.model_dump()

            case "working_memory.write_item":
                item = MemoryItem.model_validate(params["item"])
                evicted = self._store.write(item)
                if evicted is not None:
                    await self._dispatcher.dispatch(evicted)
                return {"item_id": item.id}

            case "working_memory.update_item":
                updated = self._store.update(params["item_id"], params["delta"])
                if updated is None:
                    raise ValueError(f"Item not found in working memory: {params['item_id']!r}")
                return updated.model_dump()

            case "working_memory.evict_item":
                evicted = self._store.evict(params["item_id"])
                if evicted is not None:
                    await self._dispatcher.dispatch(evicted)
                return {"status": "ok"}

            case "working_memory.list_active":
                items = self._store.list_active()
                return {"items": [it.model_dump() for it in items]}

            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")
