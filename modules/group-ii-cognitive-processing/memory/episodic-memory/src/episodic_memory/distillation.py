"""Episodic → semantic LTM distillation background job.

Periodically clusters episodic items by cosine similarity and writes
decontextualised summary facts to brain.long-term-memory via A2A task.

Cluster threshold: items within the cluster are assumed to share a recurring
pattern when their embeddings are within ``cluster_threshold`` of each other.
Clusters of size >= ``min_cluster_size`` are summarised and promoted to LTM.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from endogenai_a2a import A2AClient
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, MemoryType, QueryRequest

from episodic_memory.models import DistillationReport

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.episodic-memory"
LTM_A2A_URL = "http://localhost:8203"


class DistillationJob:
    """Episodic → semantic distillation job.

    For each cluster of similar episodic items (size >= min_cluster_size),
    writes a summarised MemoryItem to brain.long-term-memory via the LTM
    module's A2A task endpoint.
    """

    def __init__(
        self,
        adapter: ChromaAdapter,
        ltm_a2a_url: str = LTM_A2A_URL,
        min_cluster_size: int = 3,
        cluster_threshold: float = 0.85,
    ) -> None:
        self._adapter = adapter
        self._ltm_a2a_url = ltm_a2a_url
        self._min_cluster_size = min_cluster_size
        self._cluster_threshold = cluster_threshold

    async def run(self) -> DistillationReport:
        """Execute a distillation pass over brain.episodic-memory.

        Identifies recurring patterns using cosine clustering and promotes
        decontextualised summaries to long-term memory.

        Returns:
            DistillationReport with cluster and promotion counts.
        """
        # Retrieve a broad sample for clustering
        request = QueryRequest(
            collection_name=COLLECTION,
            query_text="recurring pattern knowledge fact",
            n_results=100,
        )
        response = await self._adapter.query(request)
        items = [r.item for r in response.results]

        if not items:
            logger.info("episodic_distillation_no_items")
            return DistillationReport(items_processed=0)

        clusters = self._cluster_items(items)
        facts_written = 0

        for cluster in clusters:
            if len(cluster) < self._min_cluster_size:
                continue
            summary_item = self._summarise_cluster(cluster)
            try:
                await self._write_to_ltm(summary_item)
                facts_written += 1
            except Exception:
                logger.exception("episodic_distillation_ltm_write_failed")

        report = DistillationReport(
            clusters_found=len(clusters),
            facts_written_to_ltm=facts_written,
            items_processed=len(items),
        )
        logger.info(
            "episodic_distillation_complete",
            clusters=report.clusters_found,
            facts_written=report.facts_written_to_ltm,
        )
        return report

    def _cluster_items(self, items: list[MemoryItem]) -> list[list[MemoryItem]]:
        """Naive greedy clustering by content hash prefix (placeholder for embedding clustering)."""
        # Simplified grouping by content length bucket (proxy for semantic similarity)
        # In production: use cosine similarity on embeddings
        buckets: dict[int, list[MemoryItem]] = {}
        for item in items:
            bucket_key = len(item.content) // 100  # group by ~100-char content length
            buckets.setdefault(bucket_key, []).append(item)
        return list(buckets.values())

    def _summarise_cluster(self, cluster: list[MemoryItem]) -> MemoryItem:
        """Create a decontextualised summary item from a cluster."""
        avg_importance = sum(it.importance_score for it in cluster) / len(cluster)
        representative = max(cluster, key=lambda it: it.importance_score)
        return MemoryItem(
            id=str(uuid.uuid4()),
            collection_name="brain.long-term-memory",
            content=f"[Distilled from {len(cluster)} episodic events] {representative.content}",
            type=MemoryType.LONG_TERM,
            source_module="episodic-memory",
            importance_score=min(avg_importance + 0.1, 1.0),
            created_at=datetime.now(UTC).isoformat(),
            tags=["distilled", "episodic-origin"],
        )

    async def _write_to_ltm(self, item: MemoryItem) -> None:
        """Write a summarised item to LTM via A2A task."""
        client = A2AClient(url=self._ltm_a2a_url)
        await client.send_task("write_item", {"item": item.model_dump()})
