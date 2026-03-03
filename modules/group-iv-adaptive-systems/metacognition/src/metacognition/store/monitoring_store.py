"""monitoring_store.py — ChromaDB-backed append-only store for MetacognitiveEvaluation events.

Uses ``endogenai_vector_store.ChromaAdapter`` — never imports chromadb directly.
Collection: ``brain.metacognition``

Usage::

    store = MonitoringStore(chromadb_url="http://localhost:8000")
    await store.initialise()
    await store.append(evaluation)
    results = await store.query_recent("default", n=10)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig
from endogenai_vector_store.models import (
    CreateCollectionRequest,
    MemoryItem,
    MemoryType,
    QueryRequest,
    UpsertRequest,
)

if TYPE_CHECKING:
    from metacognition.evaluation.evaluator import MetacognitiveEvaluation

logger = logging.getLogger(__name__)

_COLLECTION = "brain.metacognition"
_SOURCE_MODULE = "metacognition"


class MonitoringStore:
    """Append-only ChromaDB store for metacognitive evaluation events.

    Embeds each ``MetacognitiveEvaluation`` as a text string so that trend
    queries ("has confidence for goal_class X been declining?") are supported
    via semantic similarity search.
    """

    def __init__(
        self,
        chromadb_url: str = "http://localhost:8000",
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        host, _, port_str = chromadb_url.replace("http://", "").partition(":")
        port = int(port_str) if port_str else 8000
        self._adapter = ChromaAdapter(
            config=ChromaConfig(mode="http", host=host, port=port),
            embedding_config=EmbeddingConfig(provider="ollama", model=embedding_model),
        )

    async def initialise(self) -> None:
        """Ensure the ``brain.metacognition`` collection exists."""
        try:
            await self._adapter.create_collection(
                CreateCollectionRequest(collection_name=_COLLECTION)
            )
            logger.info("Collection ensured: %s", _COLLECTION)
        except Exception as exc:  # noqa: BLE001
            # Collection likely already exists — log and continue
            logger.debug("create_collection skipped: %s", exc)

    @staticmethod
    def _to_content(evaluation: MetacognitiveEvaluation) -> str:
        """Serialise evaluation to plain-text content for embedding."""
        return (
            f"task_type={evaluation.task_type} "
            f"task_confidence={evaluation.task_confidence:.4f} "
            f"deviation_zscore={evaluation.deviation_zscore:.4f} "
            f"error_detected={evaluation.error_detected} "
            f"success_rate={evaluation.success_rate:.4f} "
            f"reward_delta={evaluation.reward_delta:.4f} "
            f"timestamp={evaluation.timestamp}"
        )

    async def append(self, evaluation: MetacognitiveEvaluation) -> None:
        """Persist a MetacognitiveEvaluation to the vector store.

        Args:
            evaluation: Evaluation event to store.
        """
        content = self._to_content(evaluation)
        metadata: dict[str, object] = {
            "task_type": evaluation.task_type,
            "task_confidence": evaluation.task_confidence,
            "deviation_zscore": evaluation.deviation_zscore,
            "error_detected": evaluation.error_detected,
            "correction_triggered": evaluation.correction_triggered,
            "timestamp": evaluation.timestamp,
            "session_id": evaluation.session_id or "",
        }

        item = MemoryItem(
            id=evaluation.evaluation_id,
            collection_name=_COLLECTION,
            content=content,
            type=MemoryType.LONG_TERM,
            source_module=_SOURCE_MODULE,
            # low confidence → high importance for monitoring
            importance_score=round(1.0 - evaluation.task_confidence, 4),
            created_at=evaluation.timestamp,
            metadata=metadata,
        )

        await self._adapter.upsert(
            UpsertRequest(collection_name=_COLLECTION, items=[item])
        )
        logger.debug("Appended evaluation %s to %s", evaluation.evaluation_id, _COLLECTION)

    async def query_recent(self, task_type: str, n: int = 10) -> list[dict[str, object]]:
        """Return up to ``n`` recent evaluations for a given task_type.

        Uses semantic similarity ordered by score (highest first).

        Args:
            task_type: The task_type filter string.
            n: Maximum number of results to return.

        Returns:
            List of dicts with ``id``, ``content``, ``metadata``, and ``score``.
        """
        query_text = f"task_type={task_type} confidence evaluation"
        response = await self._adapter.query(
            QueryRequest(
                collection_name=_COLLECTION,
                query_text=query_text,
                n_results=n,
                where={"task_type": task_type} if task_type else None,
            )
        )
        results: list[dict[str, object]] = []
        if response and response.results:
            for result in response.results:
                entry: dict[str, object] = {
                    "id": result.item.id,
                    "content": result.item.content,
                    "metadata": result.item.metadata,
                    "score": result.score,
                }
                results.append(entry)
        return results
