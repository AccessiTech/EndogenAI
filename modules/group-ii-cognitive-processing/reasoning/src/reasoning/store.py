"""Vector store adapter for the brain.reasoning collection.

Wraps the endogenai_vector_store ChromaAdapter to persist:
  - InferenceTrace records (serialised as MemoryItem content)
  - CausalPlan summaries

Uses the shared adapter exclusively — never imports chromadb or qdrant_client directly.
"""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig
from endogenai_vector_store.models import (
    MemoryItem,
    MemoryType,
    QueryRequest,
    QueryResponse,
    UpsertRequest,
)

from reasoning.models import CausalPlan, InferenceTrace

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION_NAME = "brain.reasoning"


def _build_default_adapter() -> ChromaAdapter:
    """Construct a ChromaAdapter for the brain.reasoning collection."""
    chroma_config = ChromaConfig(host="localhost", port=8000, collection_name=COLLECTION_NAME)
    embedding_config = EmbeddingConfig(
        model="nomic-embed-text",
        backend="ollama",
        base_url="http://localhost:11434",
    )
    return ChromaAdapter(config=chroma_config, embedding_config=embedding_config)


class ReasoningStore:
    """Persists inference traces and causal plans to brain.reasoning.

    All vector store access routes through ChromaAdapter — never touches
    chromadb or qdrant_client directly.
    """

    def __init__(self, adapter: ChromaAdapter | None = None) -> None:
        self._adapter = adapter or _build_default_adapter()

    async def store_trace(self, trace: InferenceTrace) -> str:
        """Embed and upsert an InferenceTrace into brain.reasoning.

        The trace is serialised to a human-readable content string so that
        it can be semantically queried for relevant prior reasoning.

        Returns:
            The trace UUID.
        """
        content = (
            f"InferenceTrace strategy={trace.strategy} confidence={trace.confidence:.3f} "
            f"query={trace.query[:100]} conclusion={trace.conclusion[:200]}"
        )
        metadata: dict[str, str] = {
            "strategy": str(trace.strategy),
            "model_used": trace.model_used,
            "confidence": str(trace.confidence),
            "source_module": trace.source_module,
            "created_at": trace.created_at,
            **trace.metadata,
        }
        item = MemoryItem(
            id=trace.id,
            collection_name=COLLECTION_NAME,
            content=content,
            type=MemoryType.WORKING,
            source_module=trace.source_module,
            importance_score=trace.confidence,
            created_at=trace.created_at,
            metadata=metadata,
        )
        request = UpsertRequest(collection_name=COLLECTION_NAME, items=[item])
        await self._adapter.upsert(request)
        logger.info("reasoning_store.trace_stored", trace_id=trace.id, strategy=trace.strategy)
        return trace.id

    async def store_plan(self, plan: CausalPlan) -> str:
        """Embed and upsert a CausalPlan into brain.reasoning.

        Returns:
            The plan UUID.
        """
        steps_summary = " -> ".join(plan.steps[:5]) if plan.steps else "(empty plan)"
        content = (
            f"CausalPlan goal={plan.goal[:100]} "
            f"steps={len(plan.steps)} uncertainty={plan.uncertainty:.3f} "
            f"summary={steps_summary}"
        )
        metadata: dict[str, str] = {
            "goal": plan.goal[:256],
            "step_count": str(len(plan.steps)),
            "uncertainty": str(plan.uncertainty),
            "horizon": str(plan.horizon),
            "created_at": plan.created_at,
        }
        item = MemoryItem(
            id=plan.id,
            collection_name=COLLECTION_NAME,
            content=content,
            type=MemoryType.WORKING,
            source_module="reasoning",
            importance_score=max(0.0, 1.0 - plan.uncertainty),
            created_at=plan.created_at,
            metadata=metadata,
        )
        request = UpsertRequest(collection_name=COLLECTION_NAME, items=[item])
        await self._adapter.upsert(request)
        logger.info("reasoning_store.plan_stored", plan_id=plan.id, steps=len(plan.steps))
        return plan.id

    async def query_traces(self, query: str, n_results: int = 5) -> list[MemoryItem]:
        """Semantic search over stored inference traces.

        Args:
            query: The semantic query string.
            n_results: Maximum number of results to return.

        Returns:
            A list of MemoryItems matching the query.
        """
        request = QueryRequest(
            collection_name=COLLECTION_NAME,
            query_text=query,
            n_results=n_results,
        )
        response: QueryResponse = await self._adapter.query(request)
        logger.info(
            "reasoning_store.query",
            query=query[:80],
            results=len(response.results),
        )
        return [r.item for r in response.results]
