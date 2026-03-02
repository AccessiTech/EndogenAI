"""Episodic event validator — enforces the Tulving triple and affective valence requirement.

Every incoming MemoryItem of type ``episodic`` must carry:
  - ``metadata['session_id']``  (where)
  - ``metadata['source_task_id']`` (what)
  - ``created_at`` ISO-8601 (when)
  - ``metadata['affective_valence']`` float -1.0 to 1.0

Raises ``ValueError`` if any required field is missing or malformed.
"""

from __future__ import annotations

import re

import structlog
from endogenai_vector_store.models import MemoryItem

from episodic_memory.models import EpisodeEvent

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class EpisodicIndexer:
    """Validates and indexes incoming episodic MemoryItems.

    Enforces the Tulving triple requirement and returns a structured EpisodeEvent
    on successful validation.
    """

    @staticmethod
    def validate(item: MemoryItem) -> EpisodeEvent:
        """Validate an episodic MemoryItem and extract its EpisodeEvent.

        Args:
            item: A MemoryItem with ``type == "episodic"``.

        Returns:
            An EpisodeEvent built from the validated item.

        Raises:
            ValueError: If any required field is absent or malformed.
        """
        meta = item.metadata

        session_id = meta.get("session_id")
        if not session_id:
            raise ValueError(
                f"Episodic item {item.id!r} missing required metadata field: 'session_id'"
            )

        source_task_id = meta.get("source_task_id")
        if not source_task_id:
            raise ValueError(
                f"Episodic item {item.id!r} missing required metadata field: 'source_task_id'"
            )

        if not item.created_at or not _ISO8601_RE.match(item.created_at):
            raise ValueError(
                f"Episodic item {item.id!r} has invalid or missing 'created_at': {item.created_at!r}"
            )

        # affective_valence is optional with default 0.0; validate range if present
        affective_valence: float = 0.0
        if "affective_valence" in meta:
            v = float(meta["affective_valence"])
            if not (-1.0 <= v <= 1.0):
                raise ValueError(
                    f"Episodic item {item.id!r} affective_valence {v} out of range [-1.0, 1.0]"
                )
            affective_valence = v

        logger.debug(
            "episodic_item_validated",
            event_id=item.id,
            session_id=session_id,
            source_task_id=source_task_id,
        )
        return EpisodeEvent(
            event_id=item.id,
            session_id=str(session_id),
            source_task_id=str(source_task_id),
            created_at=item.created_at,
            affective_valence=affective_valence,
        )
