"""
Data models for the Attention & Filtering Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from endogenai_attention_filtering.imports import Signal


class SalienceScore(BaseModel):
    """Computed salience score for a signal."""

    signal_id: str
    score: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class FilteredSignal(BaseModel):
    """A signal that has passed attention gating, augmented with its salience score."""

    signal: Signal
    salience: SalienceScore
    routed_to: str | None = None  # downstream module id


class AttentionDirective(BaseModel):
    """
    Top-down attention directive dispatched from the Executive / Agent Layer.

    Directives can raise or lower the effective salience of specific modalities
    or signal types, implementing goal-directed attentional bias.
    """

    directive_id: str
    modality_boost: dict[str, float] = Field(
        default_factory=dict,
        description="Modality → salience multiplier (e.g. {'text': 1.5}).",
    )
    type_boost: dict[str, float] = Field(
        default_factory=dict,
        description="Signal type prefix → salience multiplier (e.g. {'text.input': 2.0}).",
    )
    threshold_override: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Override the global salience threshold for this directive.",
    )
    session_id: str | None = None
    ttl_ms: int | None = None  # directive expires after this many milliseconds
