"""Boot-time seed pipeline for long-term memory using LlamaIndex.

Called once at module startup if ``brain.long-term-memory`` is empty.
Loads documents from ``resources/static/knowledge/``, splits them into
frontmatter-aware chunks, embeds via Ollama nomic-embed-text, and writes
to ``brain.long-term-memory`` via the endogenai_vector_store adapter.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import structlog
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import MemoryItem, MemoryType, UpsertRequest

from long_term_memory.models import SeedReport

logger: structlog.BoundLogger = structlog.get_logger(__name__)

COLLECTION = "brain.long-term-memory"
SOURCE_MODULE = "long-term-memory"


class SeedPipeline:
    """Idempotent boot-time seed pipeline.

    Uses LlamaIndex SimpleDirectoryReader + SentenceSplitter to load and
    chunk markdown documents from the knowledge base, then writes them
    into brain.long-term-memory via the shared adapter.
    """

    def __init__(
        self,
        adapter: ChromaAdapter,
        seed_documents_path: str = "resources/static/knowledge/",
        max_chunk_tokens: int = 512,
        chunk_overlap_tokens: int = 50,
    ) -> None:
        self._adapter = adapter
        self._seed_path = Path(seed_documents_path)
        self._max_chunk_tokens = max_chunk_tokens
        self._chunk_overlap_tokens = chunk_overlap_tokens

    async def is_seeded(self) -> bool:
        """Return True if brain.long-term-memory already contains items."""
        from endogenai_vector_store.models import QueryRequest

        request = QueryRequest(
            collection_name=COLLECTION,
            query_text="knowledge",
            n_results=1,
        )
        resp = await self._adapter.query(request)
        return bool(resp.results)

    async def run(self) -> SeedReport:
        """Execute the seed pipeline (idempotent).

        Returns:
            SeedReport with the number of chunks written or already_seeded flag.
        """
        if await self.is_seeded():
            logger.info("ltm_seed_already_seeded")
            return SeedReport(already_seeded=True, source_path=str(self._seed_path))

        if not self._seed_path.exists():
            logger.warning("ltm_seed_path_missing", path=str(self._seed_path))
            return SeedReport(source_path=str(self._seed_path))

        try:
            from llama_index.core import SimpleDirectoryReader
            from llama_index.core.node_parser import (
                SentenceSplitter,
            )
        except ImportError:
            logger.error("llama_index_not_installed")
            return SeedReport(source_path=str(self._seed_path))

        reader = SimpleDirectoryReader(
            input_dir=str(self._seed_path),
            recursive=True,
        )
        documents = reader.load_data()

        splitter = SentenceSplitter(
            chunk_size=self._max_chunk_tokens,
            chunk_overlap=self._chunk_overlap_tokens,
        )
        nodes = splitter.get_nodes_from_documents(documents)

        items: list[MemoryItem] = []
        now = datetime.now(UTC).isoformat()

        for node in nodes:
            node_text: str = node.get_content()
            if not node_text.strip():
                continue
            metadata: dict[str, object] = {}
            if hasattr(node, "metadata") and isinstance(node.metadata, dict):
                metadata = {str(k): str(v) for k, v in node.metadata.items()}
            item = MemoryItem(
                id=str(uuid.uuid4()),
                collection_name=COLLECTION,
                content=node_text,
                type=MemoryType.LONG_TERM,
                source_module=SOURCE_MODULE,
                importance_score=0.6,
                created_at=now,
                metadata=metadata,
                tags=["seed", "knowledge"],
            )
            items.append(item)

        if items:
            # Batch upsert in chunks of 50
            batch_size = 50
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                await self._adapter.upsert(UpsertRequest(collection_name=COLLECTION, items=batch))

        logger.info("ltm_seed_complete", chunks_written=len(items))
        return SeedReport(
            chunks_written=len(items),
            already_seeded=False,
            source_path=str(self._seed_path),
        )
