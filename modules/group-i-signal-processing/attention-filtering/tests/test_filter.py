"""Tests for AttentionFilter."""

from __future__ import annotations

import pytest

from endogenai_attention_filtering.filter import AttentionFilter
from endogenai_attention_filtering.imports import Modality, Signal, SignalSource
from endogenai_attention_filtering.models import AttentionDirective, FilteredSignal


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


class TestAttentionFilterRouting:
    """Verify every modality is routed to the expected downstream module."""

    def _eval(self, modality: Modality, priority: int = 7) -> FilteredSignal | None:
        af = AttentionFilter(threshold=0.0)  # pass everything
        signal = _make_signal(modality=modality, priority=priority)
        return af.evaluate(signal)

    def test_text_routes_to_perception(self) -> None:
        result = self._eval(Modality.TEXT)
        assert result is not None
        assert result.routed_to == "perception"

    def test_image_routes_to_perception(self) -> None:
        result = self._eval(Modality.IMAGE)
        assert result is not None
        assert result.routed_to == "perception"

    def test_audio_routes_to_perception(self) -> None:
        result = self._eval(Modality.AUDIO)
        assert result is not None
        assert result.routed_to == "perception"

    def test_sensor_routes_to_perception(self) -> None:
        result = self._eval(Modality.SENSOR)
        assert result is not None
        assert result.routed_to == "perception"

    def test_api_event_routes_to_perception(self) -> None:
        result = self._eval(Modality.API_EVENT)
        assert result is not None
        assert result.routed_to == "perception"

    def test_internal_routes_to_perception(self) -> None:
        result = self._eval(Modality.INTERNAL)
        assert result is not None
        assert result.routed_to == "perception"

    def test_control_routes_to_executive(self) -> None:
        result = self._eval(Modality.CONTROL)
        assert result is not None
        assert result.routed_to == "executive"


class TestAttentionFilterTypeBoost:
    """Verify type_boost on directives biases salience by signal type prefix."""

    def test_type_boost_raises_salience_for_matching_prefix(self) -> None:
        af_plain = AttentionFilter(threshold=0.0)
        af_boosted = AttentionFilter(threshold=0.0)
        signal = _make_signal(modality=Modality.TEXT, priority=3, signal_type="text.input")

        result_plain = af_plain.evaluate(signal)
        assert result_plain is not None
        plain_score = result_plain.salience.score

        directive = AttentionDirective(directive_id="boost-text-input", type_boost={"text.input": 3.0})
        af_boosted.apply_directive(directive)
        result_boosted = af_boosted.evaluate(signal)
        assert result_boosted is not None
        assert result_boosted.salience.score > plain_score

    def test_type_boost_prefix_match_is_startswith(self) -> None:
        """A boost for 'text' should match 'text.input' since code uses startswith."""
        af = AttentionFilter(threshold=0.9)
        signal = _make_signal(modality=Modality.TEXT, priority=3, signal_type="text.input")
        # Without boost this should be below 0.9
        assert af.evaluate(signal) is None

        directive = AttentionDirective(directive_id="boost", type_boost={"text": 4.0})
        af.apply_directive(directive)
        # After boost should pass
        assert af.evaluate(signal) is not None

    def test_type_boost_does_not_affect_non_matching_type(self) -> None:
        af = AttentionFilter(threshold=0.9)
        signal = _make_signal(modality=Modality.TEXT, priority=3, signal_type="text.input")
        # Boost for audio.chunk should not help text.input
        directive = AttentionDirective(directive_id="boost-audio", type_boost={"audio.chunk": 5.0})
        af.apply_directive(directive)
        assert af.evaluate(signal) is None


class TestAttentionFilterMultipleDirectives:
    """Verify behaviour when multiple directives are active simultaneously."""

    def test_multiple_directives_stack_multiplicatively(self) -> None:
        af = AttentionFilter(threshold=0.0)
        signal = _make_signal(modality=Modality.TEXT, priority=3)

        result_plain = af.evaluate(signal)
        assert result_plain is not None
        base_score = result_plain.salience.score

        # Apply two boosts in sequence
        af.apply_directive(AttentionDirective(directive_id="d1", modality_boost={"text": 2.0}))
        af.apply_directive(AttentionDirective(directive_id="d2", modality_boost={"text": 1.5}))
        result_boosted = af.evaluate(signal)
        assert result_boosted is not None
        # Score should be boosted beyond base by both multipliers
        assert result_boosted.salience.score > base_score

    def test_latest_threshold_override_wins(self) -> None:
        af = AttentionFilter(threshold=0.5)
        signal = _make_signal(modality=Modality.TEXT, priority=3)

        # First directive raises threshold to 0.9 (would gate signal out)
        af.apply_directive(AttentionDirective(directive_id="d-raise", threshold_override=0.9))
        assert af.evaluate(signal) is None

        # Second directive lowers threshold to 0.1 (should let signal through)
        af.apply_directive(AttentionDirective(directive_id="d-lower", threshold_override=0.1))
        assert af.evaluate(signal) is not None


class TestAttentionFilterSignalTTL:
    """Verify signal TTL handling in evaluate()."""

    def test_signal_within_ttl_passes(self) -> None:
        af = AttentionFilter(threshold=0.0)
        signal = _make_signal(modality=Modality.TEXT, priority=5)
        # High TTL — signal should not be expired
        signal.ttl = 999999
        result = af.evaluate(signal)
        assert result is not None

    def test_salience_rationale_contains_modality_and_priority(self) -> None:
        af = AttentionFilter(threshold=0.0)
        signal = _make_signal(modality=Modality.TEXT, priority=7)
        result = af.evaluate(signal)
        assert result is not None
        assert "text" in result.salience.rationale
        assert "7" in result.salience.rationale
