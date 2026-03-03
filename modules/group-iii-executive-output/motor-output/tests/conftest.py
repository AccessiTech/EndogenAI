"""conftest.py — Shared fixtures for motor-output tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from motor_output.dispatcher import Dispatcher
from motor_output.error_policy import ErrorPolicy
from motor_output.feedback import FeedbackEmitter
from motor_output.models import ActionSpec, ChannelType, ErrorPolicyConfig


@pytest.fixture
def sample_action_spec() -> ActionSpec:
    return ActionSpec(
        action_id="test-action-001",
        type="test.http_call",
        channel=ChannelType.HTTP,
        params={"url": "http://example.com/api", "method": "GET"},
        goal_id="goal-001",
        predicted_outcome={"status_code": 200, "success": True},
    )


@pytest.fixture
def sample_a2a_spec() -> ActionSpec:
    return ActionSpec(
        action_id="test-action-a2a",
        type="test.delegate",
        channel=ChannelType.A2A,
        params={"a2a_url": "http://localhost:8162/tasks", "task_type": "ping", "payload": {}},
        goal_id="goal-002",
    )


@pytest.fixture
def mock_error_policy() -> ErrorPolicy:
    config = ErrorPolicyConfig.model_validate(
        {
            "maxAttempts": 2,
            "backoffMultiplier": 1.0,
            "initialDelaySeconds": 0.0,
            "maxDelaySeconds": 1.0,
            "circuitBreakerEnabled": False,
            "failureThreshold": 5,
            "recoveryTimeSeconds": 60.0,
            "escalateBaseUrl": "http://localhost:8161",
        }
    )
    return ErrorPolicy(config=config, executive_agent_url="http://localhost:8161")


@pytest.fixture
def mock_feedback_emitter() -> FeedbackEmitter:
    emitter = MagicMock(spec=FeedbackEmitter)
    emitter.emit = AsyncMock(return_value=None)
    emitter.emit_preaction_signal = AsyncMock(return_value=None)
    emitter.build_feedback = FeedbackEmitter("http://localhost:8161").build_feedback
    return emitter


@pytest.fixture
def dispatcher(
    mock_error_policy: ErrorPolicy,
    mock_feedback_emitter: FeedbackEmitter,
) -> Dispatcher:
    return Dispatcher(
        error_policy=mock_error_policy,
        feedback_emitter=mock_feedback_emitter,
        corollary_discharge_enabled=False,
    )
