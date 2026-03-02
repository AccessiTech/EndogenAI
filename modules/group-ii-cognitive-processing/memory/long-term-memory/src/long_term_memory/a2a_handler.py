"""A2A task handler for the long-term memory module."""

from __future__ import annotations

from typing import Any

import structlog
from endogenai_vector_store.models import MemoryItem

from long_term_memory.models import SeedReport, SemanticFact
from long_term_memory.retrieval import HybridRetrieval
from long_term_memory.seed_pipeline import SeedPipeline
from long_term_memory.sql_store import SQLFactStore
from long_term_memory.vector_store import LTMVectorStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AHandler:
    """Handles incoming A2A task delegations for long-term memory."""

    def __init__(
        self,
        vector_store: LTMVectorStore,
        retrieval: HybridRetrieval,
        sql_store: SQLFactStore,
        seed_pipeline: SeedPipeline,
    ) -> None:
        self._vector_store = vector_store
        self._retrieval = retrieval
        self._sql_store = sql_store
        self._seed_pipeline = seed_pipeline

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an A2A task by type."""
        match task_type:
            case "write_item":
                item = MemoryItem.model_validate(payload["item"])
                item_id = await self._vector_store.write(item)
                return {"item_id": item_id}

            case "query":
                items = await self._retrieval.query(
                    query_text=payload["query"],
                    top_k=int(payload.get("top_k", 10)),
                    filters=payload.get("filters"),
                )
                return {"items": [it.model_dump() for it in items]}

            case "write_fact":
                fact = SemanticFact.model_validate(payload["fact"])
                fact_id = await self._sql_store.write_fact(fact)
                return {"fact_id": fact_id}

            case "seed":
                report: SeedReport = await self._seed_pipeline.run()
                return report.model_dump()

            case _:
                raise ValueError(f"Unknown A2A task type: {task_type!r}")
