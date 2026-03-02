"""A2A task handler for the episodic memory module."""

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


class A2AHandler:
    """Handles incoming A2A task delegations for episodic memory."""

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

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an A2A task by type."""
        match task_type:
            case "write_event":
                item = MemoryItem.model_validate(payload["event"])
                event_id = await self._store.append(item)
                return {"event_id": event_id}

            case "search_episodes":
                items = await self._retrieval.semantic_search(
                    query=payload["query"],
                    top_k=int(payload.get("top_k", 10)),
                    session_id=payload.get("session_id"),
                    time_window_start=payload.get("time_window_start"),
                    time_window_end=payload.get("time_window_end"),
                )
                return {"items": [it.model_dump() for it in items]}

            case "get_timeline":
                events = await self._timeline.get_session_timeline(payload["session_id"])
                return {"events": [it.model_dump() for it in events]}

            case "run_distillation":
                report: DistillationReport = await self._distillation.run()
                return report.model_dump()

            case _:
                raise ValueError(f"Unknown A2A task type: {task_type!r}")
