"""Unit tests for EpisodicIndexer."""

from __future__ import annotations

import pytest

from episodic_memory.indexer import EpisodicIndexer

from .conftest import make_event


def test_validate_valid_event() -> None:
    """Valid event returns an EpisodeEvent."""
    event = make_event()
    episode_event = EpisodicIndexer.validate(event)
    assert episode_event.event_id == "event-1"
    assert episode_event.session_id == "session-abc"
    assert episode_event.source_task_id == "task-xyz"
    assert episode_event.affective_valence == 0.5


def test_validate_missing_session_id_raises() -> None:
    """Missing session_id should raise ValueError."""
    event = make_event()
    event.metadata.pop("session_id")
    with pytest.raises(ValueError, match="session_id"):
        EpisodicIndexer.validate(event)


def test_validate_missing_source_task_id_raises() -> None:
    """Missing source_task_id should raise ValueError."""
    event = make_event()
    event.metadata.pop("source_task_id")
    with pytest.raises(ValueError, match="source_task_id"):
        EpisodicIndexer.validate(event)


def test_validate_invalid_affective_valence_raises() -> None:
    """Affective valence out of range should raise ValueError."""
    event = make_event()
    event.metadata["affective_valence"] = 2.0
    with pytest.raises(ValueError, match="affective_valence"):
        EpisodicIndexer.validate(event)


def test_validate_zero_affective_valence_ok() -> None:
    """Affective valence of 0.0 is acceptable."""
    event = make_event(affective_valence=0.0)
    episode_event = EpisodicIndexer.validate(event)
    assert episode_event.affective_valence == 0.0
