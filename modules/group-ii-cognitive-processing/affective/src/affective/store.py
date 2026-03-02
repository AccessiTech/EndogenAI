"""Vector store adapter for the brain.affective collection.

Wraps the endogenai_vector_store ChromaAdapter to persist:
  - RewardSignal records (serialised as MemoryItem content)
  - Emotional state snapshots

Uses the shared adapter exclusively — never imports chromadb or qdrant_client directly.
"""

from __future__ import annotations

import structlog
from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig
from endogenai_vector_store.models import MemoryItem, MemoryType, UpsertRequest

from affective.models import RewardSignal

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION_NAME = "brain.affective"


def _build_default_adapter() -> ChromaAdapter:
    """Construct a ChromaAdapter for the brain.affective collection."""
    chroma_config = ChromaConfig(host="localhost", port=8000, collection_name=COLLECTION_NAME)
    embedding_config = EmbeddingConfig(
        model="nomic-embed-text",
        backend="ollama",
        base_url="http://localhost:11434",
    )
    return ChromaAdapter(config=chroma_config, embedding_config=embedding_config)


class AffectiveStore:
    """Persists reward signals and emotional state snapshots to brain.affective.

    All vector store access routes through ChromaAdapter — never touches
    chromadb or qdrant_client directly.
    """

    def __init__(self, adapter: ChromaAdapter | None = None) -> None:
        self._adapter = adapter or _build_default_adapter()

    async def store_reward_signal(self, signal: RewardSignal) -> str:
        """Embed and upsert a RewardSignal into brain.affective.

        The signal is serialised to a human-readable content string so that
        it can be semantically queried alongside emotional state snapshots.

        Returns:
            The signal's UUID (pass-through for caller convenience).
        """
        content = (
            f"RewardSignal type={signal.type} value={signal.value:.3f} "
            f"trigger={signal.trigger} source={signal.source_module}"
        )
        metadata: dict[str, str] = {
            "signal_type": str(signal.type),
            "source_module": signal.source_module,
            "timestamp": signal.timestamp,
            **signal.metadata,
        }
        if signal.associated_memory_item_id:
            metadata["associated_memory_item_id"] = signal.associated_memory_item_id
        if signal.session_id:
            metadata["session_id"] = signal.session_id

        item = MemoryItem(
            id=signal.id,
            collection_name=COLLECTION_NAME,
            content=content,
            type=MemoryType.SHORT_TERM,
            source_module=signal.source_module,
            importance_score=max(0.0, signal.value),
            created_at=signal.timestamp,
            metadata=metadata,
        )
        request = UpsertRequest(collection_name=COLLECTION_NAME, items=[item])
        await self._adapter.upsert(request)
        logger.info("affective_store.signal_stored", signal_id=signal.id, type=signal.type)
        return signal.id

    async def store_emotional_snapshot(
        self,
        snapshot_id: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Embed and upsert an arbitrary emotional state snapshot.

        Args:
            snapshot_id: UUID for the snapshot record.
            content: Human-readable description of the emotional state.
            metadata: Optional string key-value annotations.

        Returns:
            snapshot_id for caller convenience.
        """
        from datetime import UTC, datetime

        item = MemoryItem(
            id=snapshot_id,
            collection_name=COLLECTION_NAME,
            content=content,
            type=MemoryType.SHORT_TERM,
            source_module="affective",
            importance_score=0.5,
            created_at=datetime.now(UTC).isoformat(),
            metadata=metadata or {},
        )
        request = UpsertRequest(collection_name=COLLECTION_NAME, items=[item])
        await self._adapter.upsert(request)
        logger.info("affective_store.snapshot_stored", snapshot_id=snapshot_id)
        return snapshot_id

    @property
    def adapter(self) -> ChromaAdapter:
        """Expose underlying adapter for query operations."""
        return self._adapter
