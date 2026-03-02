"""Unit tests for RPE computation in affective.rpe."""

from __future__ import annotations

import pytest

from affective.rpe import compute_rpe


class TestComputeRPE:
    """Unit tests for compute_rpe()."""

    def test_positive_rpe_unexpected_reward(self) -> None:
        result = compute_rpe(signal_value=0.8, expected_value=0.3)
        assert abs(result.rpe - 0.5) < 1e-9
        assert result.magnitude == pytest.approx(0.5)
        assert result.valence == "positive"

    def test_negative_rpe_unexpected_penalty(self) -> None:
        result = compute_rpe(signal_value=-0.4, expected_value=0.1)
        assert result.rpe == pytest.approx(-0.5)
        assert result.magnitude == pytest.approx(0.5)
        assert result.valence == "negative"

    def test_neutral_rpe_exact_match(self) -> None:
        result = compute_rpe(signal_value=0.5, expected_value=0.5)
        assert result.rpe == pytest.approx(0.0, abs=1e-9)
        assert result.magnitude == pytest.approx(0.0, abs=1e-9)
        assert result.valence == "neutral"

    def test_max_positive_rpe(self) -> None:
        result = compute_rpe(signal_value=1.0, expected_value=-1.0)
        assert result.rpe == pytest.approx(2.0)
        assert result.valence == "positive"

    def test_max_negative_rpe(self) -> None:
        result = compute_rpe(signal_value=-1.0, expected_value=1.0)
        assert result.rpe == pytest.approx(-2.0)
        assert result.valence == "negative"

    def test_zero_signal_nonzero_expected(self) -> None:
        result = compute_rpe(signal_value=0.0, expected_value=0.4)
        assert result.rpe == pytest.approx(-0.4)
        assert result.valence == "negative"

    def test_fields_echo_inputs(self) -> None:
        result = compute_rpe(signal_value=0.3, expected_value=0.1)
        assert result.signal_value == pytest.approx(0.3)
        assert result.expected_value == pytest.approx(0.1)

    def test_result_model_dump(self) -> None:
        result = compute_rpe(signal_value=0.6, expected_value=0.2)
        d = result.model_dump()
        assert "rpe" in d
        assert "magnitude" in d
        assert "valence" in d
        assert d["valence"] == "positive"
