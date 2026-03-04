"""Tests for learning-adaptation MCP server interface."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from learning_adaptation.interfaces.mcp_server import (
    call_predict,
    call_promote_habit,
    call_train,
    get_habits_catalog,
    get_policy_current,
    get_replay_buffer_stats,
)
from learning_adaptation.models import (
    ActionPrediction,
    HabitRecord,
    PolicySummary,
    ReplayBufferStats,
    TrainingResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_trainer() -> MagicMock:
    trainer = MagicMock()
    trainer.get_policy_summary = MagicMock(
        return_value=PolicySummary(
            algorithm="PPO",
            total_timesteps=1000,
            last_updated="2026-01-01T00:00:00Z",
        )
    )
    trainer.predict = AsyncMock(
        return_value=ActionPrediction(
            goal_priority_deltas=[0.1, 0.2, 0.3, 0.4],
            task_type="default",
        )
    )
    trainer.train_step = AsyncMock(
        return_value=TrainingResult(
            total_timesteps=64,
            mean_reward=0.5,
            episodes=1,
            policy_updated=True,
        )
    )
    trainer._env = MagicMock()
    trainer._env.push_feedback = MagicMock()
    return trainer


@pytest.fixture
def mock_replay_buffer() -> AsyncMock:
    buf = AsyncMock()
    buf.add = AsyncMock()
    buf.sample = AsyncMock(return_value=[])
    buf.stats = AsyncMock(
        return_value=ReplayBufferStats(
            total_episodes=42,
            mean_reward=0.6,
            top_task_type="default",
        )
    )
    return buf


@pytest.fixture
def mock_habit_manager() -> MagicMock:
    hm = MagicMock()
    hm.record_episode = MagicMock(return_value=False)
    hm.should_promote = MagicMock(return_value=False)
    hm.list_habits = MagicMock(
        return_value=[
            HabitRecord(
                task_type="default",
                policy_path="/tmp/habit.pt",
                eval_score=0.9,
                promoted_at="2026-01-01T00:00:00Z",
            )
        ]
    )
    hm.promote = AsyncMock(
        return_value=HabitRecord(
            task_type="default",
            policy_path="/tmp/habit.pt",
            eval_score=0.9,
            promoted_at="2026-01-01T00:00:00Z",
        )
    )
    return hm


# ---------------------------------------------------------------------------
# Resource reads
# ---------------------------------------------------------------------------


async def test_get_policy_current(mock_trainer: MagicMock) -> None:
    result = await get_policy_current(mock_trainer)
    assert result["algorithm"] == "PPO"
    assert result["total_timesteps"] == 1000


async def test_get_replay_buffer_stats(mock_replay_buffer: AsyncMock) -> None:
    result = await get_replay_buffer_stats(mock_replay_buffer)
    assert result["total_episodes"] == 42
    assert result["top_task_type"] == "default"


async def test_get_habits_catalog(mock_habit_manager: MagicMock) -> None:
    result = await get_habits_catalog(mock_habit_manager)
    assert len(result) == 1
    assert result[0]["task_type"] == "default"


# ---------------------------------------------------------------------------
# Tool calls
# ---------------------------------------------------------------------------


async def test_call_train(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    feedback: dict[str, Any] = {
        "action_id": "act-001",
        "goal_id": "goal-001",
        "channel": "a2a",
        "success": True,
        "escalate": False,
        "deviation_score": 0.1,
        "reward_signal": {"value": 0.5},
    }
    result = await call_train(
        arguments={"motor_feedback": [feedback]},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
    )
    assert result["status"] == "ok"
    assert result["episodes_added"] == 1


async def test_call_predict(mock_trainer: MagicMock) -> None:
    result = await call_predict(
        arguments={"observation": [0.0] * 12},
        trainer=mock_trainer,
    )
    assert "goal_priority_deltas" in result
    assert len(result["goal_priority_deltas"]) == 4


async def test_call_promote_habit(mock_habit_manager: MagicMock, mock_trainer: MagicMock) -> None:
    result = await call_promote_habit(
        arguments={"task_type": "default"},
        habit_manager=mock_habit_manager,
        trainer=mock_trainer,
    )
    assert result["task_type"] == "default"
    assert "policy_path" in result
