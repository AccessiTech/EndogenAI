"""MCP tool definitions for the episodic memory module."""

from __future__ import annotations

from typing import Any

import structlog
from endogenai_vector_store.models import MemoryItem

from episodic_memory.distillation import DistillationJob
from episodic_memory.models import DistillationReport
from episodic_memory.retrieval import EpisodicRetrieval
from episodic_memory.store import EpisodicStore
from episodic_memory.timeline import Timeline

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for episodic memory operations."""

    def __init__(
        self,
        store: EpisodicStore,
        retrieval: EpisodicRetrieval,
        timeline: Timeline,
        distillation: DistillationJob,
    ) -> None:
        self._store = store
        self._retrieval = retrieval
        self._timeline = timeline
        self._distillation = distillation

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name."""
        match tool_name:
            case "em.write_event":
                item = MemoryItem.model_validate(params["event"])
                event_id = await self._store.append(item)
                return {"event_id": event_id}

            case "em.search":
                items = await self._retrieval.semantic_search(
                    query=params["query"],
                    top_k=int(params.get("top_k", 10)),
                    session_id=params.get("session_id"),
                    time_window_start=params.get("time_window_start"),
                    time_window_end=params.get("time_window_end"),
                )
                return {"items": [it.model_dump() for it in items]}

            case "em.get_timeline":
                events = await self._timeline.get_session_timeline(params["session_id"])
                return {"events": [it.model_dump() for it in events]}

            case "em.run_distillation":
                report: DistillationReport = await self._distillation.run()
                return report.model_dump()

            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")
