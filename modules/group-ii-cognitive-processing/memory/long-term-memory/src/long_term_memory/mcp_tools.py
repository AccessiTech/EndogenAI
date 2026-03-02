"""MCP tool definitions for the long-term memory module."""

from __future__ import annotations

from typing import Any

import structlog
from endogenai_vector_store.models import MemoryItem

from long_term_memory.graph_store import KuzuGraphStore
from long_term_memory.models import SeedReport, SemanticFact
from long_term_memory.retrieval import HybridRetrieval
from long_term_memory.seed_pipeline import SeedPipeline
from long_term_memory.sql_store import SQLFactStore
from long_term_memory.vector_store import LTMVectorStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for long-term memory operations."""

    def __init__(
        self,
        vector_store: LTMVectorStore,
        retrieval: HybridRetrieval,
        sql_store: SQLFactStore,
        graph_store: KuzuGraphStore,
        seed_pipeline: SeedPipeline,
    ) -> None:
        self._vector_store = vector_store
        self._retrieval = retrieval
        self._sql_store = sql_store
        self._graph_store = graph_store
        self._seed_pipeline = seed_pipeline

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name."""
        match tool_name:
            case "ltm.write":
                item = MemoryItem.model_validate(params["item"])
                item_id = await self._vector_store.write(item)
                return {"item_id": item_id}

            case "ltm.query":
                items = await self._retrieval.query(
                    query_text=params["query"],
                    top_k=int(params.get("top_k", 10)),
                    filters=params.get("filters"),
                )
                return {"items": [it.model_dump() for it in items]}

            case "ltm.write_fact":
                fact = SemanticFact.model_validate(params["fact"])
                fact_id = await self._sql_store.write_fact(fact)
                return {"fact_id": fact_id}

            case "ltm.query_facts":
                facts = await self._sql_store.query_facts(params["entity_id"])
                return {"facts": [f.model_dump() for f in facts]}

            case "ltm.write_edge":
                self._graph_store.write_edge(
                    src=params["src"],
                    predicate=params["predicate"],
                    dst=params["dst"],
                    strength=float(params.get("strength", 1.0)),
                )
                return {"status": "ok"}

            case "ltm.query_graph":
                edges = self._graph_store.query_neighbours(
                    entity_id=params["entity_id"],
                    depth=int(params.get("depth", 1)),
                )
                return {"edges": [e.model_dump() for e in edges]}

            case "ltm.run_seed_pipeline":
                report: SeedReport = await self._seed_pipeline.run()
                return report.model_dump()

            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")
