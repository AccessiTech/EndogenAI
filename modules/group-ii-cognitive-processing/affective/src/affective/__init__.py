"""Affective / Motivational Layer package.

Maps to the Limbic System — generates reward signals, computes emotional weighting,
and emits drive-based urgency scores that modulate memory consolidation and decision-making.
"""

from affective.a2a_handler import A2AHandler
from affective.drive import DriveStateMachine
from affective.mcp_tools import MCPTools
from affective.models import AffectiveTag, DriveState, RewardSignal, RPEResult
from affective.rpe import compute_rpe
from affective.store import AffectiveStore
from affective.weighting import WeightingDispatcher

__all__ = [
    "A2AHandler",
    "AffectiveStore",
    "AffectiveTag",
    "DriveState",
    "DriveStateMachine",
    "MCPTools",
    "RPEResult",
    "RewardSignal",
    "WeightingDispatcher",
    "compute_rpe",
]
