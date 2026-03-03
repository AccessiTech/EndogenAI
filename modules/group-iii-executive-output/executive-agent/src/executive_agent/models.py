"""models.py — Core Pydantic models for the executive-agent module.

Aligned with:
  - shared/schemas/executive-goal.schema.json
  - shared/schemas/policy-decision.schema.json
  - shared/schemas/motor-feedback.schema.json
  - shared/types/reward-signal.schema.json

Neuroanatomical analogues:
  - GoalItem: DLPFC goal stack unit + OFC priority score
  - SelfModel: Frontal lobe identity / self-referential state
  - PolicyDecision: ACC policy-violation gate
  - BDIPlan: BG direct pathway commitment record
  - MotorFeedback: Spinocerebellar corollary-discharge outcome
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class LifecycleState(StrEnum):
    """BDI goal lifecycle FSM states.

    Transitions:
      PENDING → EVALUATING  (option-generator picks it up)
      EVALUATING → COMMITTED (OPA allow; BDI deliberation selects it)
      EVALUATING → PENDING   (OPA allow; not selected this cycle)
      EVALUATING → FAILED    (OPA deny; unresolvable policy violation)
      COMMITTED → EXECUTING  (pushed to agent-runtime execution queue)
      EXECUTING → COMPLETED  (MotorFeedback: success)
      EXECUTING → FAILED     (MotorFeedback: escalate=true)
      EXECUTING → DEFERRED   (stop signal; BG hyperdirect abort)
      DEFERRED → EVALUATING  (re-queued on next deliberation cycle)
    """

    PENDING = "PENDING"
    EVALUATING = "EVALUATING"
    COMMITTED = "COMMITTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEFERRED = "DEFERRED"


class GoalItem(BaseModel):
    """A goal managed by the BDI deliberation loop.

    DLPFC analogue: active maintenance in working memory, capacity-constrained.
    OFC analogue: priority score derived from value computation.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str = Field(..., min_length=1, max_length=1024)
    priority: float = Field(..., ge=0.0, le=1.0)
    lifecycle_state: LifecycleState = LifecycleState.PENDING
    goal_class: str | None = None
    deadline: datetime | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    workflow_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parent_goal_id: str | None = None
    source_agent: str | None = None
    context_payload: dict[str, Any] = Field(default_factory=dict)


class SelfModel(BaseModel):
    """Agent identity and self-referential state.

    Frontal lobe / vmPFC analogue: coherent self-model maintained over time.
    """

    agent_name: str
    agent_version: str
    core_values: list[str]
    max_active_goals: int
    deliberation_cycle_ms: int
    recent_achievements: list[str] = Field(default_factory=list)
    deltas: list[dict[str, Any]] = Field(default_factory=list)


class PolicyDecision(BaseModel):
    """OPA policy evaluation result.

    ACC analogue: conflict / violation detection gate before commitment.
    """

    allow: bool
    violations: list[str] = Field(default_factory=list)
    explanation: str | None = None
    package: str
    rule: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cached: bool = False
    input_hash: str | None = None


class BDIPlan(BaseModel):
    """Record of a committed BDI intention.

    BG direct pathway analogue: disinhibited commitment to action.
    """

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    goal_id: str
    pipeline_request: dict[str, Any] = Field(default_factory=dict)
    workflow_id: str | None = None
    committed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MotorFeedback(BaseModel):
    """Outcome from motor-output closes the corollary-discharge loop.

    Spinocerebellar analogue: observed outcome vs predicted; computes deviation.
    """

    action_id: str
    goal_id: str
    channel: str
    predicted_outcome: dict[str, Any] | None = None
    actual_outcome: dict[str, Any]
    deviation_score: float = Field(..., ge=0.0, le=1.0)
    success: bool
    escalate: bool
    error: str | None = None
    retry_count: int = 0
    reward_signal: dict[str, Any]
    dispatched_at: datetime
    completed_at: datetime
    latency_ms: int | None = None


class DriveState(BaseModel):
    """Snapshot of drive variables pulled from the affective module."""

    urgency: float = 0.0
    valence: float = 0.0
    arousal: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict)


class IdentityConfig(BaseModel):
    """Loaded from identity.config.json at startup."""

    agent_name: str = Field(alias="agentName")
    agent_version: str = Field(alias="agentVersion")
    core_values: list[str] = Field(alias="coreValues")
    max_active_goals: int = Field(alias="maxActiveGoals")
    deliberation_cycle_ms: int = Field(alias="deliberationCycleMs")
    goal_capacity_enforcement: bool = Field(alias="goalCapacityEnforcement")
    identity_collection_name: str = Field(alias="identityCollectionName")
    working_memory_module: str = Field(alias="workingMemoryModule")
    affective_module: str = Field(alias="affectiveModule")
    agent_runtime_module: str = Field(alias="agentRuntimeModule")

    model_config = {"populate_by_name": True}
