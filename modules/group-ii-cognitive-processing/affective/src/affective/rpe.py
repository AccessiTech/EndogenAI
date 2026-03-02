"""Reward Prediction Error (RPE) computation.

Implements the dopaminergic VTA phasic burst model:
  - RPE > 0: unexpected reward (positive prediction error)
  - RPE < 0: unexpected penalty (negative prediction error)
  - RPE == 0: outcome matched expectation exactly

The magnitude of RPE encodes the degree of surprise, which modulates the
strength of learning updates and memory encoding (BLA → hippocampus pathway).
"""

from __future__ import annotations

from affective.models import RPEResult


def compute_rpe(signal_value: float, expected_value: float) -> RPEResult:
    """Compute the Reward Prediction Error between an observed value and its expectation.

    Args:
        signal_value: Observed reward/penalty value in [-1, 1].
        expected_value: Prior expected value in [-1, 1].

    Returns:
        RPEResult with rpe, magnitude, and valence fields populated.

    Examples:
        >>> result = compute_rpe(0.8, 0.3)
        >>> result.rpe
        0.5
        >>> result.valence
        'positive'
    """
    rpe = signal_value - expected_value
    magnitude = abs(rpe)

    if rpe > 1e-9:
        valence = "positive"
    elif rpe < -1e-9:
        valence = "negative"
    else:
        valence = "neutral"

    return RPEResult(
        signal_value=signal_value,
        expected_value=expected_value,
        rpe=rpe,
        magnitude=magnitude,
        valence=valence,
    )
