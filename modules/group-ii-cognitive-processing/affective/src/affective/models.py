"""Pydantic models for the Affective / Motivational Layer.

Local definitions that mirror shared/types/reward-signal.schema.json.
All generated RewardSignal instances must conform to that schema.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SignalType(StrEnum):
    """Semantic category of a reward signal (mirrors schema enum)."""

    REWARD = "reward"
    PENALTY = "penalty"
    NEUTRAL = "neutral"
    NOVELTY = "novelty"
    URGENCY = "urgency"
    CURIOSITY = "curiosity"
    SATISFACTION = "satisfaction"
    FRUSTRATION = "frustration"
    CONFIDENCE_BOOST = "confidence-boost"
    CONFIDENCE_DROP = "confidence-drop"


class TriggerType(StrEnum):
    """What caused a reward signal to be generated (mirrors schema enum)."""

    USER_EXPLICIT = "user-explicit"
    USER_IMPLICIT = "user-implicit"
    TASK_SUCCESS = "task-success"
    TASK_FAILURE = "task-failure"
    GOAL_ACHIEVED = "goal-achieved"
    GOAL_ABANDONED = "goal-abandoned"
    PREDICTION_ERROR = "prediction-error"
    NOVELTY_DETECTION = "novelty-detection"
    CONSTRAINT_VIOLATION = "constraint-violation"
    IDLE_TIMEOUT = "idle-timeout"
    SELF_EVALUATION = "self-evaluation"


class DriveType(StrEnum):
    """Hypothalamic drive variable types."""

    URGENCY = "urgency"
    NOVELTY = "novelty"
    THREAT = "threat"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class RPEResult(BaseModel):
    """Reward Prediction Error computation result.

    Analogous to dopaminergic VTA phasic burst signalling:
    - rpe > 0: unexpected reward (positive prediction error)
    - rpe < 0: unexpected penalty (negative prediction error)
    - rpe == 0: outcome matched expectation exactly
    """

    signal_value: float = Field(description="Observed signal/outcome value.")
    expected_value: float = Field(description="Prior expected value.")
    rpe: float = Field(description="Reward prediction error: signal_value - expected_value.")
    magnitude: float = Field(description="Absolute magnitude of the RPE; encodes surprise level.")
    valence: str = Field(description="'positive', 'negative', or 'neutral'.")


class DriveState(BaseModel):
    """Current state of the three hypothalamic drive variables."""

    urgency: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    novelty: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    threat: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0

    @field_validator("urgency", "novelty", "threat", mode="before")
    @classmethod
    def clamp(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


class AffectiveTag(BaseModel):
    """Affective valence tag attached to a memory item or reasoning step.

    Analogous to BLA emotional tagging that amplifies hippocampal encoding strength.
    """

    memory_item_id: str = Field(description="UUID of the tagged MemoryItem.")
    valence: Annotated[float, Field(ge=-1.0, le=1.0)] = Field(
        description="Affective valence score in [-1, 1]. Positive = approach; negative = avoidance."
    )
    arousal: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.0, description="Arousal intensity [0, 1]."
    )
    source_signal_id: str | None = Field(
        default=None, description="UUID of the RewardSignal that generated this tag."
    )
    tagged_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp.",
    )


class DecayParams(BaseModel):
    """Temporal decay parameters for a reward signal."""

    half_life_ms: int = Field(ge=1, description="Half-life in milliseconds.")
    model: str = Field(default="exponential", description="Decay model: exponential, linear, step.")


class RewardSignal(BaseModel):
    """Local Pydantic representation of a reward signal.

    Mirrors shared/types/reward-signal.schema.json exactly.
    All emitted instances must pass JSON Schema validation against that file.
    """

    id: str = Field(description="UUID v4 identifier.")
    timestamp: str = Field(description="ISO 8601 UTC timestamp.")
    source_module: str = Field(
        alias="sourceModule",
        description="Module that generated this signal.",
        default="affective",
    )
    target_module: str | None = Field(
        alias="targetModule",
        default=None,
        description="Target module (None = broadcast).",
    )
    value: Annotated[float, Field(ge=-1.0, le=1.0)] = Field(
        description="Scalar reward value in [-1, 1]."
    )
    type: SignalType = Field(description="Semantic category of the reward signal.")
    trigger: TriggerType | None = Field(default=None, description="What caused this signal.")
    associated_signal_id: str | None = Field(
        alias="associatedSignalId", default=None, description="UUID of triggering Signal."
    )
    associated_task_id: str | None = Field(
        alias="associatedTaskId", default=None, description="A2A task ID."
    )
    associated_memory_item_id: str | None = Field(
        alias="associatedMemoryItemId",
        default=None,
        description="Memory item whose importance should be updated.",
    )
    session_id: str | None = Field(alias="sessionId", default=None)
    decay: DecayParams | None = Field(default=None, description="Temporal decay parameters.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Arbitrary string annotations."
    )

    model_config = {"populate_by_name": True}
