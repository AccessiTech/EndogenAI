"""MCP tool definitions for the short-term memory module.

Tools exposed:
  stm.write            — Write session record; novelty check applied.
  stm.search           — Semantic search over current session.
  stm.expire_session   — End session; run consolidation pipeline.
  stm.get_by_session   — Return all items for a session (ordered).
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


class MCPTools:
    """MCP tool handler for short-term memory operations."""

    def __init__(
        self,
        store: ShortTermMemoryStore,
        search: SemanticSearch,
        pipeline: ConsolidationPipeline,
    ) -> None:
        self._store = store
        self._search = search
        self._pipeline = pipeline

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name.

        Args:
            tool_name: The MCP tool identifier (e.g. ``stm.write``).
            params: Tool parameters as a JSON-deserialisable dict.

        Returns:
            Tool-specific response value.

        Raises:
            ValueError: If the tool_name is not recognised.
        """
        match tool_name:
            case "stm.write":
                item = MemoryItem.model_validate(params["item"])
                item_id = await self._store.write(item)
                return {"item_id": item_id}

            case "stm.search":
                items = await self._search.search(
                    session_id=params["session_id"],
                    query=params["query"],
                    top_k=int(params.get("top_k", 10)),
                )
                return {"items": [it.model_dump() for it in items]}

            case "stm.expire_session":
                report: ConsolidationReport = await self._pipeline.run(params["session_id"])
                return report.model_dump()

            case "stm.get_by_session":
                items = await self._store.get_by_session(params["session_id"])
                return {"items": [it.model_dump() for it in items]}

            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")
