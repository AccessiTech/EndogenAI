"""Unit tests for DriveStateMachine and combine_signals."""

from __future__ import annotations

import math

import pytest

from affective.drive import DriveStateMachine, combine_signals
from affective.models import DriveType


class TestDriveStateMachine:
    """Unit tests for DriveStateMachine."""

    def test_initial_state_is_zero(self) -> None:
        machine = DriveStateMachine()
        state = machine.state
        assert state.urgency == 0.0
        assert state.novelty == 0.0
        assert state.threat == 0.0

    def test_update_urgency(self) -> None:
        machine = DriveStateMachine()
        state = machine.update(DriveType.URGENCY, 0.5)
        assert state.urgency == pytest.approx(0.5)

    def test_update_clamps_to_1(self) -> None:
        machine = DriveStateMachine()
        state = machine.update(DriveType.NOVELTY, 2.0)
        assert state.novelty == pytest.approx(1.0)

    def test_update_clamps_to_0(self) -> None:
        machine = DriveStateMachine()
        machine.update(DriveType.THREAT, 0.3)
        state = machine.update(DriveType.THREAT, -1.0)
        assert state.threat == pytest.approx(0.0)

    def test_urgency_threshold_not_triggered(self) -> None:
        machine = DriveStateMachine(urgency_threshold=0.7)
        machine.update(DriveType.URGENCY, 0.5)
        assert not machine.is_urgency_triggered()

    def test_urgency_threshold_triggered(self) -> None:
        machine = DriveStateMachine(urgency_threshold=0.7)
        machine.update(DriveType.URGENCY, 0.8)
        assert machine.is_urgency_triggered()

    def test_urgency_threshold_exact(self) -> None:
        machine = DriveStateMachine(urgency_threshold=0.7)
        machine.update(DriveType.URGENCY, 0.7)
        assert machine.is_urgency_triggered()

    def test_decay_novelty(self) -> None:
        machine = DriveStateMachine(novelty_decay_rate=0.1)
        machine.update(DriveType.NOVELTY, 1.0)
        state = machine.decay_novelty()
        expected = 1.0 * math.exp(-0.1)
        assert state.novelty == pytest.approx(expected, rel=1e-6)

    def test_reset_zeros_all_drives(self) -> None:
        machine = DriveStateMachine()
        machine.update(DriveType.URGENCY, 0.9)
        machine.update(DriveType.THREAT, 0.8)
        machine.reset()
        state = machine.state
        assert state.urgency == 0.0
        assert state.threat == 0.0

    def test_curiosity_adjusted_novelty_boost(self) -> None:
        machine = DriveStateMachine(curiosity_boost_factor=1.5)
        machine.update(DriveType.NOVELTY, 0.4)
        adj = machine.curiosity_adjusted_novelty()
        assert adj == pytest.approx(min(1.0, 0.4 * 1.5))

    def test_curiosity_adjusted_clamped_to_1(self) -> None:
        machine = DriveStateMachine(curiosity_boost_factor=2.0)
        machine.update(DriveType.NOVELTY, 1.0)
        adj = machine.curiosity_adjusted_novelty()
        assert adj == pytest.approx(1.0)

    def test_state_is_copy(self) -> None:
        """state property returns a copy; mutating it does not affect the machine."""
        machine = DriveStateMachine()
        machine.update(DriveType.URGENCY, 0.5)
        snap = machine.state
        # Simulate external modification — should not affect internal state
        assert snap.urgency == pytest.approx(0.5)
        machine.update(DriveType.URGENCY, 0.2)
        assert snap.urgency == pytest.approx(0.5)  # unchanged copy
        assert machine.state.urgency == pytest.approx(0.7)


class TestCombineSignals:
    """Unit tests for combine_signals()."""

    def test_equal_weights_average(self) -> None:
        result = combine_signals([0.4, 0.6], [1.0, 1.0])
        assert result == pytest.approx(0.5)

    def test_single_signal(self) -> None:
        result = combine_signals([0.8], [1.0])
        assert result == pytest.approx(0.8)

    def test_empty_signals_returns_zero(self) -> None:
        assert combine_signals([], []) == 0.0

    def test_zero_total_weight_returns_zero(self) -> None:
        assert combine_signals([0.5, 0.5], [0.0, 0.0]) == 0.0

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="must equal weights length"):
            combine_signals([0.5], [1.0, 2.0])

    def test_negative_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            combine_signals([0.5, 0.5], [-1.0, 1.0])

    def test_clamped_to_1(self) -> None:
        result = combine_signals([1.0, 1.0], [1.0, 1.0])
        assert result <= 1.0

    def test_weighted_combination(self) -> None:
        # (0.2 * 3 + 0.8 * 1) / 4 = (0.6 + 0.8) / 4 = 0.35
        result = combine_signals([0.2, 0.8], [3.0, 1.0])
        assert result == pytest.approx(0.35)
