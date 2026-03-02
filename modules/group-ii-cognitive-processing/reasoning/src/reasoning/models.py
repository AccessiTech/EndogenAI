"""Pydantic models for the Decision-Making & Reasoning Layer.

Defines the core data structures for inference traces, causal plans,
reasoning results, and incoming requests. All models are Pydantic v2.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ReasoningStrategy(StrEnum):
    """High-level reasoning strategy applied to a query."""

    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    CAUSAL = "causal"
    PLANNING = "planning"


class ConflictResolutionPolicy(StrEnum):
    """Policy for resolving conflicting hypotheses or plans."""

    HIGHEST_CONFIDENCE = "highest-confidence"
    MOST_RECENT = "most-recent"
    WEIGHTED_AVERAGE = "weighted-average"
    MAJORITY_VOTE = "majority-vote"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class InferenceTrace(BaseModel):
    """A single reasoning trace produced by the inference pipeline.

    Mirrors the inference step structure from the prefrontal cortex analogy:
    each trace records the query, retrieved context, chain-of-thought, and
    the final conclusion with a confidence score.
    """

    id: Annotated[str, Field(description="Unique trace identifier (UUID).")] = Field(
        default_factory=lambda: __import__("uuid").uuid4().__str__()
    )
    query: str = Field(description="Original reasoning query or problem statement.")
    context: list[str] = Field(
        default_factory=list,
        description="Retrieved evidence snippets used as reasoning context.",
    )
    chain_of_thought: list[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning chain produced by the inference pipeline.",
    )
    conclusion: str = Field(description="Final conclusion or answer derived from the chain.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the conclusion (0.0–1.0).",
    )
    strategy: ReasoningStrategy = Field(
        default=ReasoningStrategy.DEDUCTIVE,
        description="Reasoning strategy applied.",
    )
    model_used: str = Field(
        default="ollama/mistral",
        description="LiteLLM model string used for inference.",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO-8601 timestamp for creation.",
    )
    source_module: str = Field(
        default="reasoning",
        description="Module that produced this trace.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional key-value metadata.",
    )


class CausalPlan(BaseModel):
    """A causal plan produced by the planner for a stated goal.

    Analogous to the DLPFC forward simulation: a sequence of steps that
    causally leads from current state to the goal, with uncertainty scores.
    """

    id: Annotated[str, Field(description="Unique plan identifier (UUID).")] = Field(
        default_factory=lambda: __import__("uuid").uuid4().__str__()
    )
    goal: str = Field(description="The goal to be achieved.")
    steps: list[str] = Field(
        default_factory=list,
        description="Ordered causal steps from current state to goal.",
    )
    uncertainty: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated uncertainty of the plan (0.0 = certain, 1.0 = highly uncertain).",
    )
    horizon: int = Field(
        default=5,
        description="Planning horizon — maximum number of steps considered.",
    )
    trace_ids: list[str] = Field(
        default_factory=list,
        description="InferenceTrace IDs used to build this plan.",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO-8601 timestamp for creation.",
    )


class ReasoningResult(BaseModel):
    """Aggregated result returned to callers of the reasoning module.

    Bundles the primary inference trace with any causal plan and metadata
    about conflict resolution applied.
    """

    trace: InferenceTrace = Field(description="Primary inference trace.")
    plan: CausalPlan | None = Field(
        default=None,
        description="Causal plan produced alongside the trace, if applicable.",
    )
    conflicts_resolved: int = Field(
        default=0,
        description="Number of conflicting hypotheses resolved during processing.",
    )
    resolution_policy: ConflictResolutionPolicy = Field(
        default=ConflictResolutionPolicy.HIGHEST_CONFIDENCE,
        description="Policy applied to resolve conflicts.",
    )


class ReasoningRequest(BaseModel):
    """Incoming request to the reasoning module.

    Carries the query, optional pre-fetched context, and configuration
    overrides for this invocation.
    """

    query: str = Field(description="The reasoning query or problem statement.")
    context: list[str] = Field(
        default_factory=list,
        description="Optional pre-fetched context snippets (e.g. from long-term memory).",
    )
    strategy: ReasoningStrategy = Field(
        default=ReasoningStrategy.DEDUCTIVE,
        description="Reasoning strategy to apply.",
    )
    include_plan: bool = Field(
        default=False,
        description="Whether to generate a causal plan alongside the inference trace.",
    )
    model: str | None = Field(
        default=None,
        description="LiteLLM model string override (uses strategy.config.json default if None).",
    )
