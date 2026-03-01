"""Tests for AttentionFilter."""

from __future__ import annotations

import pytest

from endogenai_attention_filtering.filter import AttentionFilter
from endogenai_attention_filtering.imports import Modality, Signal, SignalSource
from endogenai_attention_filtering.models import AttentionDirective


def _make_signal(
    modality: Modality = Modality.TEXT,
    priority: int = 5,
    signal_type: str = "text.input",
) -> Signal:
    return Signal(
        type=signal_type,
        modality=modality,
        source=SignalSource(moduleId="sensory-input", layer="sensory-input"),
        payload="test payload",
        priority=priority,
    )


class TestAttentionFilter:
    def test_high_priority_text_passes_default_threshold(self) -> None:
        af = AttentionFilter(threshold=0.3)
        signal = _make_signal(priority=8)
        result = af.evaluate(signal)
        assert result is not None
        assert result.signal.id == signal.id

    def test_very_low_priority_gated_out(self) -> None:
        af = AttentionFilter(threshold=0.5)
        signal = _make_signal(priority=0)
        result = af.evaluate(signal)
        assert result is None

    def test_control_signal_always_passes(self) -> None:
        af = AttentionFilter(threshold=0.5)
        signal = _make_signal(modality=Modality.CONTROL, priority=5)
        result = af.evaluate(signal)
        assert result is not None

    def test_routing_text_to_perception(self) -> None:
        af = AttentionFilter()
        signal = _make_signal(modality=Modality.TEXT, priority=7)
        result = af.evaluate(signal)
        assert result is not None
        assert result.routed_to == "perception"

    def test_routing_control_to_executive(self) -> None:
        af = AttentionFilter()
        signal = _make_signal(modality=Modality.CONTROL, priority=5)
        result = af.evaluate(signal)
        assert result is not None
        assert result.routed_to == "executive"

    def test_salience_score_in_range(self) -> None:
        af = AttentionFilter()
        for priority in range(11):
            signal = _make_signal(priority=priority)
            result = af.evaluate(signal)
            if result:
                assert 0.0 <= result.salience.score <= 1.0

    def test_directive_boosts_salience(self) -> None:
        af = AttentionFilter(threshold=0.5)
        # Without directive a low-priority internal signal would be gated out
        signal = _make_signal(modality=Modality.INTERNAL, priority=1)
        assert af.evaluate(signal) is None

        directive = AttentionDirective(
            directive_id="dir-1",
            modality_boost={"internal": 5.0},
        )
        af.apply_directive(directive)
        result = af.evaluate(signal)
        assert result is not None

    def test_directive_threshold_override(self) -> None:
        af = AttentionFilter(threshold=0.8)
        signal = _make_signal(priority=5)
        assert af.evaluate(signal) is None  # below 0.8

        directive = AttentionDirective(
            directive_id="dir-2",
            threshold_override=0.1,
        )
        af.apply_directive(directive)
        assert af.evaluate(signal) is not None

    def test_expired_directive_no_longer_active(self) -> None:
        import time

        af = AttentionFilter(threshold=0.8)
        directive = AttentionDirective(
            directive_id="dir-3",
            threshold_override=0.1,
            ttl_ms=1,  # 1 ms TTL
        )
        af.apply_directive(directive)
        time.sleep(0.01)  # wait 10 ms
        signal = _make_signal(priority=5)
        # Directive expired; default threshold of 0.8 applies
        assert af.evaluate(signal) is None

    def test_invalid_threshold_raises(self) -> None:
        with pytest.raises(ValueError):
            AttentionFilter(threshold=1.5)
