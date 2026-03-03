"""models.py — Core Pydantic models for the agent-runtime module.

Aligned with:
  - shared/schemas/skill-pipeline.schema.json
  - shared/schemas/action-spec.schema.json
  - shared/schemas/motor-feedback.schema.json

Neuroanatomical analogues:
  - SkillPipeline: Cerebellar motor plan — ordered step sequence
  - SkillStep: Individual motor command unit (parallel scheduling via parallel_group)
  - ExecutionStatus: Real-time execution state query (cerebellar forward model)
  - SkillEntry: Tool registry entry — registered effector capability
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class StepStatus(StrEnum):
    """Lifecycle state of an individual SkillStep."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PipelineStatus(StrEnum):
    """Lifecycle state of the full SkillPipeline."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class ChannelType(StrEnum):
    """Action dispatch channel selectors."""

    HTTP = "http"
    A2A = "a2a"
    FILE = "file"
    RENDER = "render"


class SkillStep(BaseModel):
    """Single step in a SkillPipeline.

    Pre-SMA analogue: a pre-configured movement command with expected outcome.
    """

    step_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    expected_output: dict[str, Any] | None = None
    depends_on: list[str] = Field(default_factory=list)
    parallel_group: int | None = None
    channel: ChannelType = ChannelType.A2A
    timeout_seconds: int = 120
    status: StepStatus = StepStatus.PENDING


class SkillPipeline(BaseModel):
    """Ordered sequence of SkillSteps derived from a committed goal.

    Cerebellum analogue: pre-staged motor plan before execution begins.
    Maps to shared/schemas/skill-pipeline.schema.json.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    goal_id: str
    workflow_id: str | None = None
    steps: list[SkillStep] = Field(default_factory=list)
    decomposition_model: str = "litellm-direct"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: PipelineStatus = PipelineStatus.PENDING

    def get_next_pending_steps(self) -> list[SkillStep]:
        """Return steps whose dependencies are all completed."""
        completed_ids = {s.step_id for s in self.steps if s.status == StepStatus.COMPLETED}
        return [
            s
            for s in self.steps
            if s.status == StepStatus.PENDING
            and all(dep in completed_ids for dep in s.depends_on)
        ]


class ActionSpec(BaseModel):
    """Parameterised action ready for motor-output dispatch.

    Maps to shared/schemas/action-spec.schema.json.
    PMd analogue: channel selection + parameter staging before M1 dispatch.
    """

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    channel: ChannelType
    params: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    predicted_outcome: dict[str, Any] | None = None
    goal_id: str | None = None
    step_id: str | None = None
    pipeline_id: str | None = None
    timeout_seconds: int = 120
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SkillEntry(BaseModel):
    """Registered tool/skill in the tool registry.

    Discovered from agent-card.json at /.well-known/agent-card.json endpoints.
    """

    skill_id: str
    name: str
    description: str
    agent_url: str
    channel: ChannelType = ChannelType.A2A
    capabilities: list[str] = Field(default_factory=list)
    healthy: bool = True
    last_health_check: datetime | None = None


class ExecutionStatus(BaseModel):
    """Real-time state of a running or completed workflow."""

    goal_id: str
    workflow_id: str | None = None
    orchestrator: str = "temporal"
    abort_requested: bool = False
    has_pending_revision: bool = False
    status: PipelineStatus = PipelineStatus.PENDING
    steps_total: int = 0
    steps_completed: int = 0
    error: str | None = None


class OrchestratorConfig(BaseModel):
    """Loaded from orchestrator.config.json."""

    primary: str = Field(alias="primary", default="temporal")
    fallback: str = Field(alias="fallback", default="prefect")
    temporal_server_url: str = Field(alias="temporalServerUrl", default="localhost:7233")
    temporal_namespace: str = Field(alias="temporalNamespace", default="endogenai")
    temporal_task_queue: str = Field(alias="temporalTaskQueue", default="brain-runtime")
    prefect_api_url: str = Field(alias="prefectApiUrl", default="http://localhost:4200")
    workflow_id_strategy: str = Field(
        alias="workflowIdStrategy", default="goal_id_with_attempt"
    )
    max_temporal_connect_retries: int = Field(
        alias="maxTemporalConnectRetries", default=3
    )
    fallback_cooldown_seconds: int = Field(alias="fallbackCooldownSeconds", default=60)

    model_config = {"populate_by_name": True}
