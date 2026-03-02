"""Drive State Machine — hypothalamic drive variable computation.

Implements three configurable drive variables (urgency, novelty, threat) and
a weighted combination function that produces a single drive activation score.
Analogous to hypothalamic homeostatic and motivational state regulation.

Drive variables are bounded to [0, 1] and optionally decay between sessions
according to the noveltyDecayRate in drive.config.json.
"""

from __future__ import annotations

import math

import structlog

from affective.models import DriveState, DriveType

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DEFAULT_DECAY_RATE = 0.1
_DEFAULT_URGENCY_THRESHOLD = 0.7
_DEFAULT_CURIOSITY_BOOST = 1.5


class DriveStateMachine:
    """Maintains and updates the three hypothalamic drive variables.

    Drive variables:
    - urgency: time-pressure or task-criticality signal
    - novelty: degree of environmental/input novelty (decays over time)
    - threat: detected aversive/constraint-violation signal

    All values are clamped to [0, 1] at every update.
    """

    def __init__(
        self,
        urgency_threshold: float = _DEFAULT_URGENCY_THRESHOLD,
        novelty_decay_rate: float = _DEFAULT_DECAY_RATE,
        curiosity_boost_factor: float = _DEFAULT_CURIOSITY_BOOST,
    ) -> None:
        self._state = DriveState()
        self._urgency_threshold = urgency_threshold
        self._novelty_decay_rate = novelty_decay_rate
        self._curiosity_boost_factor = curiosity_boost_factor

    @property
    def state(self) -> DriveState:
        """Current drive state snapshot."""
        return self._state.model_copy()

    def update(self, drive_type: DriveType, delta: float) -> DriveState:
        """Increment or decrement a drive variable by delta.

        Args:
            drive_type: Which drive variable to update.
            delta: Signed change to apply. Clamped to keep result in [0, 1].

        Returns:
            Updated DriveState snapshot.
        """
        current = self._state.model_dump()
        current[drive_type.value] = max(0.0, min(1.0, current[drive_type.value] + delta))
        self._state = DriveState(**current)
        logger.debug("drive.updated", drive=drive_type.value, new_value=current[drive_type.value])
        return self.state

    def decay_novelty(self) -> DriveState:
        """Apply exponential decay to novelty drive.

        Models the diminishing salience of a novel stimulus over time.
        novelty_new = novelty * exp(-novelty_decay_rate)
        """
        decayed = self._state.novelty * math.exp(-self._novelty_decay_rate)
        self._state = DriveState(
            urgency=self._state.urgency,
            novelty=decayed,
            threat=self._state.threat,
        )
        return self.state

    def is_urgency_triggered(self) -> bool:
        """Return True when urgency exceeds the configured threshold."""
        return self._state.urgency >= self._urgency_threshold

    def reset(self) -> None:
        """Reset all drives to zero (end-of-session flush when not persisted)."""
        self._state = DriveState()

    def curiosity_adjusted_novelty(self) -> float:
        """Return novelty boosted by the curiosity factor.

        Analogous to nucleus accumbens incentive salience amplification.
        """
        return min(1.0, self._state.novelty * self._curiosity_boost_factor)


def combine_signals(signals: list[float], weights: list[float]) -> float:
    """Compute a weighted combination of drive signals, normalised to [0, 1].

    Args:
        signals: List of drive signal values (each in [0, 1]).
        weights: List of non-negative weights, same length as signals.

    Returns:
        Weighted average in [0, 1]. Returns 0.0 for empty inputs.

    Raises:
        ValueError: If lengths of signals and weights differ, or any weight < 0.
    """
    if not signals:
        return 0.0
    if len(signals) != len(weights):
        raise ValueError(
            f"signals length ({len(signals)}) must equal weights length ({len(weights)})"
        )
    if any(w < 0 for w in weights):
        raise ValueError("All weights must be non-negative.")

    total_weight = sum(weights)
    if total_weight == 0.0:
        return 0.0

    weighted_sum = sum(s * w for s, w in zip(signals, weights, strict=True))
    return max(0.0, min(1.0, weighted_sum / total_weight))
