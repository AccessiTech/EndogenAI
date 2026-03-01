"""
Attention & Filtering logic for the brAIn Attention Layer.

AttentionFilter implements:
  - Salience scoring based on signal priority, modality, and type
  - Configurable salience threshold gating
  - Top-down attention directive injection (executive → sensory modulation)
  - Signal routing to appropriate downstream modules

Analogous to the thalamic relay + reticular nucleus suppression loop.

Usage
-----
>>> af = AttentionFilter(threshold=0.3)
>>> result = af.evaluate(signal)
>>> if result:
...     print(result.salience.score, result.routed_to)
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import structlog

from endogenai_attention_filtering.imports import Signal
from endogenai_attention_filtering.models import (
    AttentionDirective,
    FilteredSignal,
    SalienceScore,
)

log = structlog.get_logger(__name__)

# Base salience weights by modality
_MODALITY_BASE_WEIGHT: dict[str, float] = {
    "text": 0.6,
    "image": 0.5,
    "audio": 0.5,
    "sensor": 0.4,
    "api-event": 0.7,
    "internal": 0.3,
    "control": 0.9,  # top-down control signals always prioritised
}

# Downstream routing table: modality → module id
_DEFAULT_ROUTING: dict[str, str] = {
    "text": "perception",
    "image": "perception",
    "audio": "perception",
    "sensor": "perception",
    "api-event": "perception",
    "internal": "perception",
    "control": "executive",
}


class AttentionFilter:
    """
    Salience-based attention gate and signal router.

    Parameters
    ----------
    threshold:
        Minimum salience score [0, 1] for a signal to pass the gate.
        Signals below this threshold are discarded.
    module_id:
        Canonical module id for logging.
    """

    def __init__(
        self,
        threshold: float = 0.3,
        module_id: str = "attention-filtering",
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")
        self._threshold = threshold
        self._module_id = module_id
        self._active_directives: list[_TimedDirective] = []
        self._logger = log.bind(module_id=module_id)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def apply_directive(self, directive: AttentionDirective) -> None:
        """
        Register a top-down attention directive.

        Directives bias salience scores for specific modalities or signal types
        and remain active until their TTL expires or they are replaced.
        """
        self._active_directives.append(
            _TimedDirective(directive=directive, applied_at=time.monotonic())
        )
        self._logger.info(
            "attention_directive_applied",
            directive_id=directive.directive_id,
            modality_boost=directive.modality_boost,
            type_boost=directive.type_boost,
        )

    def evaluate(self, signal: Signal) -> FilteredSignal | None:
        """
        Evaluate a signal and return a FilteredSignal if it passes gating.

        Parameters
        ----------
        signal:
            The signal to evaluate.

        Returns
        -------
        FilteredSignal | None
            The gated signal with salience score and routing info, or
            ``None`` if the signal is discarded.
        """
        self._expire_directives()
        score = self._compute_salience(signal)
        threshold = self._effective_threshold()

        salience = SalienceScore(
            signal_id=signal.id,
            score=score,
            rationale=f"modality={signal.modality.value} priority={signal.priority}",
        )

        if score < threshold:
            self._logger.debug(
                "signal_gated_out",
                signal_id=signal.id,
                score=score,
                threshold=threshold,
            )
            return None

        # TTL check
        if signal.ttl is not None:
            ingested = signal.ingested_at or datetime.now(tz=UTC)
            age_ms = (datetime.now(tz=UTC) - ingested).total_seconds() * 1000
            if age_ms > signal.ttl:
                self._logger.debug("signal_ttl_expired", signal_id=signal.id)
                return None

        routed_to = _DEFAULT_ROUTING.get(signal.modality.value, "perception")

        self._logger.info(
            "signal_passed_gate",
            signal_id=signal.id,
            score=score,
            routed_to=routed_to,
        )
        return FilteredSignal(signal=signal, salience=salience, routed_to=routed_to)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_salience(self, signal: Signal) -> float:
        """
        Compute a salience score in [0, 1] for the given signal.

        Base score: modality weight × (priority / 10)
        Directive boosts applied multiplicatively.
        """
        base = _MODALITY_BASE_WEIGHT.get(signal.modality.value, 0.5)
        priority_factor = signal.priority / 10.0
        score = base * (0.5 + priority_factor * 0.5)  # blend base + priority

        for td in self._active_directives:
            d = td.directive
            if signal.modality.value in d.modality_boost:
                score *= d.modality_boost[signal.modality.value]
            for type_prefix, mult in d.type_boost.items():
                if signal.type.startswith(type_prefix):
                    score *= mult

        return min(max(score, 0.0), 1.0)

    def _effective_threshold(self) -> float:
        """Return the most recently applied threshold override, or the default."""
        for td in reversed(self._active_directives):
            if td.directive.threshold_override is not None:
                return td.directive.threshold_override
        return self._threshold

    def _expire_directives(self) -> None:
        """Remove expired directives from the active list."""
        now = time.monotonic()
        self._active_directives = [
            td
            for td in self._active_directives
            if td.directive.ttl_ms is None
            or (now - td.applied_at) * 1000 < td.directive.ttl_ms
        ]


class _TimedDirective:
    """Internal wrapper pairing a directive with its application monotonic time."""

    __slots__ = ("directive", "applied_at")

    def __init__(self, directive: AttentionDirective, applied_at: float) -> None:
        self.directive = directive
        self.applied_at = applied_at
