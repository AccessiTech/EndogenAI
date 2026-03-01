"""attention-filtering — EndogenAI salience scoring and signal routing."""

from attention_filtering.models import (
    AttentionDirective,
    FilterRequest,
    FilterResponse,
    RouteEntry,
    ScoredSignal,
)
from attention_filtering.processor import AttentionFilter

__all__ = [
    "AttentionFilter",
    "AttentionDirective",
    "FilterRequest",
    "FilterResponse",
    "RouteEntry",
    "ScoredSignal",
]

__version__ = "0.1.0"
