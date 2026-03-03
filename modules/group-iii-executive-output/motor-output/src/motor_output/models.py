"""models.py — Shared data models for motor-output.

ActionSpec and MotorFeedback mirror the shared schemas:
  - shared/schemas/action-spec.schema.json
  - shared/schemas/motor-feedback.schema.json

These types are intentionally re-declared here (not imported from executive-agent
or agent-runtime) to keep each module independently deployable.
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ChannelType(StrEnum):
    """Available output channels. M1 analogue: population-coded effector selection."""

    HTTP = "http"
    A2A = "a2a"
    FILE = "file"
    RENDER = "render"


class DispatchStatus(StrEnum):
    PENDING = "PENDING"
    IN_FLIGHT = "IN_FLIGHT"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    ESCALATED = "ESCALATED"


class ActionSpec(BaseModel):
    """Parameterised action ready for dispatch.

    Maps to shared/schemas/action-spec.schema.json.
    PMd analogue: channel selection + parameter staging before M1 dispatch.
    """

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    channel: ChannelType | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    predicted_outcome: dict[str, Any] | None = None
    goal_id: str | None = None
    step_id: str | None = None
    pipeline_id: str | None = None
    timeout_seconds: int = 120
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MotorFeedback(BaseModel):
    """Outcome report after action dispatch.

    Maps to shared/schemas/motor-feedback.schema.json.
    Spinocerebellar analogue: proprioceptive signal comparing predicted vs. actual.
    """

    action_id: str
    goal_id: str
    channel: ChannelType
    actual_outcome: dict[str, Any]
    deviation_score: float = 0.0
    success: bool
    escalate: bool = False
    reward_signal: dict[str, Any] = Field(
        default_factory=lambda: {"value": 0.5, "source": "motor_output"}
    )
    dispatched_at: datetime
    completed_at: datetime
    predicted_outcome: dict[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0
    latency_ms: float | None = None


class DispatchRecord(BaseModel):
    """In-memory record of a dispatched action (circuit-breaker state)."""

    action_id: str
    goal_id: str | None = None
    channel: ChannelType
    status: DispatchStatus = DispatchStatus.PENDING
    attempt: int = 0
    error: str | None = None
    feedback: MotorFeedback | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class ErrorPolicyConfig(BaseModel):
    """Loaded from error-policy.config.json."""

    max_attempts: int = Field(alias="maxAttempts", default=3)
    backoff_multiplier: float = Field(alias="backoffMultiplier", default=2.0)
    initial_delay_seconds: float = Field(alias="initialDelaySeconds", default=1.0)
    max_delay_seconds: float = Field(alias="maxDelaySeconds", default=30.0)
    circuit_breaker_enabled: bool = Field(alias="circuitBreakerEnabled", default=True)
    failure_threshold: int = Field(alias="failureThreshold", default=5)
    recovery_time_seconds: float = Field(alias="recoveryTimeSeconds", default=60.0)
    escalate_base_url: str = Field(
        alias="escalateBaseUrl", default="http://localhost:8161"
    )

    model_config = {"populate_by_name": True}
