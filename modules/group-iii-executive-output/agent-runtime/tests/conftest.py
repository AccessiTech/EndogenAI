"""Tests for agent-runtime — conftest shared fixtures."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_runtime.models import (
    ActionSpec,
    ChannelType,
    ExecutionStatus,
    OrchestratorConfig,
    PipelineStatus,
    SkillEntry,
    SkillPipeline,
    SkillStep,
)


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_skill_step() -> SkillStep:
    return SkillStep(
        step_id="step-001",
        tool_id="skill.test",
        channel=ChannelType.HTTP,
        params={"url": "http://localhost:9999/action", "method": "POST"},
        depends_on=[],
    )


@pytest.fixture
def sample_pipeline(sample_skill_step: SkillStep) -> SkillPipeline:
    return SkillPipeline(
        id="pipe-001",
        goal_id="goal-001",
        steps=[sample_skill_step],
        status=PipelineStatus.PENDING,
    )


@pytest.fixture
def sample_action_spec(now: datetime) -> ActionSpec:
    return ActionSpec(
        action_id="act-001",
        type="dispatch",
        goal_id="goal-001",
        channel=ChannelType.HTTP,
        params={"url": "http://localhost:9999/action", "method": "POST"},
        timeout_seconds=30,
        predicted_outcome={"http_status": 200},
        created_at=now,
    )


@pytest.fixture
def sample_orch_config() -> OrchestratorConfig:
    return OrchestratorConfig(
        primary="temporal",
        fallback="prefect",
        temporalServerUrl="localhost:7233",
        temporalNamespace="endogenai",
        temporalTaskQueue="brain-runtime",
        maxTemporalConnectRetries=3,
        fallbackCooldownSeconds=60,
    )


@pytest.fixture
def sample_skill_entry() -> SkillEntry:
    return SkillEntry(
        skill_id="skill.test",
        name="Test Skill",
        description="A skill for testing",
        agent_url="http://localhost:9999",
        capabilities=["test", "mock"],
        healthy=True,
    )


@pytest.fixture
def mock_orchestrator(sample_orch_config: OrchestratorConfig) -> MagicMock:
    orch = MagicMock()
    orch.config = sample_orch_config
    orch.execute_intention = AsyncMock(
        return_value={"workflow_id": "goal-001-001", "orchestrator": "temporal"}
    )
    orch.abort_execution = AsyncMock(
        return_value={"status": "aborted", "goal_id": "goal-001"}
    )
    orch.get_execution_status = AsyncMock(
        return_value=ExecutionStatus(
            goal_id="goal-001",
            workflow_id="goal-001-001",
            status=PipelineStatus.RUNNING,
            steps_completed=1,
            steps_total=3,
        )
    )
    orch._build_workflow_id = MagicMock(return_value="goal-001-001")
    orch._temporal_client = None
    return orch


@pytest.fixture
def mock_tool_registry(sample_skill_entry: SkillEntry) -> MagicMock:
    reg = MagicMock()
    reg.get_all_skills = MagicMock(return_value=[sample_skill_entry])
    reg.register = MagicMock()
    reg.get_skill = MagicMock(return_value=sample_skill_entry)
    return reg
