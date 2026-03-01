"""
EndogenAI Attention & Filtering Layer.

Provides salience scoring, relevance filtering, signal routing, and top-down
attention modulation for the brAIn framework.  Consumes Signal envelopes from
the Sensory / Input Layer and forwards gated signals to the Perception Layer.
"""

from endogenai_attention_filtering.filter import AttentionFilter
from endogenai_attention_filtering.models import (
    AttentionDirective,
    FilteredSignal,
    SalienceScore,
)

__all__ = ["AttentionFilter", "AttentionDirective", "FilteredSignal", "SalienceScore"]
