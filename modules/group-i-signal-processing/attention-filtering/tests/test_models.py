"""Tests for attention-filtering data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from endogenai_attention_filtering.imports import Modality, Signal, SignalSource
from endogenai_attention_filtering.models import (
    AttentionDirective,
    FilteredSignal,
    SalienceScore,
)


def _make_signal(modality: Modality = Modality.TEXT, priority: int = 5) -> Signal:
    return Signal(
        type=f"{modality.value}.input",
        modality=modality,
        source=SignalSource(moduleId="sensory-input", layer="sensory-input"),
        payload="test",
        priority=priority,
    )


class TestSalienceScore:
    def test_score_stored(self) -> None:
        s = SalienceScore(signal_id="abc", score=0.75)
        assert s.score == 0.75

    def test_signal_id_stored(self) -> None:
        s = SalienceScore(signal_id="abc", score=0.5)
        assert s.signal_id == "abc"

    def test_rationale_defaults_empty_string(self) -> None:
        s = SalienceScore(signal_id="abc", score=0.5)
        assert s.rationale == ""

    def test_rationale_stored(self) -> None:
        s = SalienceScore(signal_id="abc", score=0.5, rationale="modality=text")
        assert s.rationale == "modality=text"

    def test_score_at_zero_boundary(self) -> None:
        s = SalienceScore(signal_id="abc", score=0.0)
        assert s.score == 0.0

    def test_score_at_one_boundary(self) -> None:
        s = SalienceScore(signal_id="abc", score=1.0)
        assert s.score == 1.0

    def test_score_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            SalienceScore(signal_id="abc", score=1.01)

    def test_score_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            SalienceScore(signal_id="abc", score=-0.01)


class TestFilteredSignal:
    def test_signal_and_salience_stored(self) -> None:
        signal = _make_signal()
        salience = SalienceScore(signal_id=signal.id, score=0.7)
        fs = FilteredSignal(signal=signal, salience=salience, routed_to="perception")
        assert fs.signal.id == signal.id
        assert fs.salience.score == 0.7

    def test_routed_to_stored(self) -> None:
        signal = _make_signal()
        salience = SalienceScore(signal_id=signal.id, score=0.6)
        fs = FilteredSignal(signal=signal, salience=salience, routed_to="executive")
        assert fs.routed_to == "executive"

    def test_routed_to_defaults_to_none(self) -> None:
        signal = _make_signal()
        salience = SalienceScore(signal_id=signal.id, score=0.5)
        fs = FilteredSignal(signal=signal, salience=salience)
        assert fs.routed_to is None

    def test_original_signal_payload_preserved(self) -> None:
        signal = _make_signal()
        signal_id = signal.id
        salience = SalienceScore(signal_id=signal_id, score=0.8)
        fs = FilteredSignal(signal=signal, salience=salience, routed_to="perception")
        assert fs.signal.payload == "test"

    def test_salience_signal_id_matches_signal(self) -> None:
        signal = _make_signal()
        salience = SalienceScore(signal_id=signal.id, score=0.85)
        fs = FilteredSignal(signal=signal, salience=salience, routed_to="perception")
        assert fs.salience.signal_id == fs.signal.id


class TestAttentionDirective:
    def test_directive_id_stored(self) -> None:
        d = AttentionDirective(directive_id="focus-text")
        assert d.directive_id == "focus-text"

    def test_modality_boost_defaults_empty(self) -> None:
        d = AttentionDirective(directive_id="d-1")
        assert d.modality_boost == {}

    def test_type_boost_defaults_empty(self) -> None:
        d = AttentionDirective(directive_id="d-1")
        assert d.type_boost == {}

    def test_ttl_ms_defaults_to_none(self) -> None:
        d = AttentionDirective(directive_id="d-1")
        assert d.ttl_ms is None

    def test_threshold_override_defaults_to_none(self) -> None:
        d = AttentionDirective(directive_id="d-1")
        assert d.threshold_override is None

    def test_session_id_defaults_to_none(self) -> None:
        d = AttentionDirective(directive_id="d-1")
        assert d.session_id is None

    def test_modality_boost_stored(self) -> None:
        d = AttentionDirective(directive_id="d-1", modality_boost={"text": 1.5, "audio": 0.8})
        assert d.modality_boost == {"text": 1.5, "audio": 0.8}

    def test_type_boost_stored(self) -> None:
        d = AttentionDirective(directive_id="d-1", type_boost={"text.input": 2.0})
        assert d.type_boost == {"text.input": 2.0}

    def test_threshold_override_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            AttentionDirective(directive_id="d-1", threshold_override=1.5)

    def test_threshold_override_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            AttentionDirective(directive_id="d-1", threshold_override=-0.1)

    def test_threshold_override_at_boundaries(self) -> None:
        d_low = AttentionDirective(directive_id="d-low", threshold_override=0.0)
        d_high = AttentionDirective(directive_id="d-high", threshold_override=1.0)
        assert d_low.threshold_override == 0.0
        assert d_high.threshold_override == 1.0
