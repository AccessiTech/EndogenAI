"""Short-term memory package — session-scoped TTL store with consolidation pipeline."""

from short_term_memory.a2a_handler import A2AHandler
from short_term_memory.consolidation import ConsolidationPipeline
from short_term_memory.models import ConsolidationReport, SessionRecord
from short_term_memory.novelty import NoveltyChecker
from short_term_memory.search import SemanticSearch
from short_term_memory.store import ShortTermMemoryStore

__all__ = [
    "ShortTermMemoryStore",
    "NoveltyChecker",
    "ConsolidationPipeline",
    "SemanticSearch",
    "A2AHandler",
    "SessionRecord",
    "ConsolidationReport",
]
