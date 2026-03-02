"""Decision-Making & Reasoning Layer.

Prefrontal cortex analogue — logical inference, causal planning,
conflict resolution, and structured generation via LiteLLM.
"""

from __future__ import annotations

from reasoning.a2a_handler import A2AHandler
from reasoning.inference import InferencePipeline, run_inference
from reasoning.mcp_tools import MCPTools
from reasoning.models import (
    CausalPlan,
    ConflictResolutionPolicy,
    InferenceTrace,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStrategy,
)
from reasoning.planner import CausalPlanner, create_plan
from reasoning.store import ReasoningStore

__all__ = [
    "A2AHandler",
    "CausalPlan",
    "CausalPlanner",
    "ConflictResolutionPolicy",
    "InferencePipeline",
    "InferenceTrace",
    "MCPTools",
    "ReasoningRequest",
    "ReasoningResult",
    "ReasoningStore",
    "ReasoningStrategy",
    "create_plan",
    "run_inference",
]
