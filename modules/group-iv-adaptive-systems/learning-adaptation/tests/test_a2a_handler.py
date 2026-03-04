"""Tests for learning-adaptation A2A task handler."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from learning_adaptation.interfaces.a2a_handler import (
    _feedback_to_episode,
    _handle_adapt_policy,
    _handle_replay_episode,
    _notify_adaptation_failed,
    _notify_habit_promoted,
    handle_task,
)
from learning_adaptation.models import (
    ActionPrediction,
    HabitRecord,
    LearningAdaptationEpisode,
    MotorFeedback,
    TrainingResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_feedback(**kwargs: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "action_id": "act-001",
        "goal_id": "goal-001",
        "channel": "a2a",
        "success": True,
        "escalate": False,
        "deviation_score": 0.1,
        "reward_signal": {"value": 0.5},
        "task_type": "default",
    }
    defaults.update(kwargs)
    return defaults


@pytest.fixture
def mock_replay_buffer() -> AsyncMock:
    buf = AsyncMock()
    buf.add = AsyncMock()
    buf.sample = AsyncMock(return_value=[])
    return buf


@pytest.fixture
def mock_trainer() -> MagicMock:
    trainer = MagicMock()
    trainer._env = MagicMock()
    trainer._env.push_feedback = MagicMock()
    trainer.train_step = AsyncMock(
        return_value=TrainingResult(
            total_timesteps=64,
            mean_reward=0.5,
            episodes=1,
            policy_updated=True,
        )
    )
    return trainer


@pytest.fixture
def mock_habit_manager() -> MagicMock:
    hm = MagicMock()
    hm.record_episode = MagicMock(return_value=False)
    hm.should_promote = MagicMock(return_value=False)
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
# _feedback_to_episode
# ---------------------------------------------------------------------------


def test_feedback_to_episode_basic() -> None:
    fb = MotorFeedback(**_make_feedback())
    episode = _feedback_to_episode(fb)
    assert isinstance(episode, LearningAdaptationEpisode)
    assert episode.reward == 0.5
    assert episode.done is True  # success=True


def test_feedback_to_episode_failed() -> None:
    fb = MotorFeedback(**_make_feedback(success=False, escalate=False, reward_signal={"reward": 0.0}))
    episode = _feedback_to_episode(fb)
    assert episode.done is False
    assert episode.reward == 0.0


def test_feedback_to_episode_with_next_obs() -> None:
    fb = MotorFeedback(**_make_feedback())
    next_obs = {"success_rate": 1.0, "mean_deviation": 0.0, "escalation_rate": 0.0, "channel_success_rate": [1.0] * 5}
    episode = _feedback_to_episode(fb, next_obs=next_obs)
    assert episode.next_observation == next_obs


# ---------------------------------------------------------------------------
# handle_task
# ---------------------------------------------------------------------------


async def test_handle_task_adapt_policy(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    result = await handle_task(
        task_name="adapt_policy",
        params={"motor_feedback": [_make_feedback()]},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
    )
    assert result["status"] == "ok"
    assert result["episodes_added"] == 1


async def test_handle_task_replay_episode(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    result = await handle_task(
        task_name="replay_episode",
        params={"motor_feedback": [_make_feedback()]},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
    )
    assert result["status"] == "ok"
    assert result["episodes_added"] == 1


async def test_handle_task_unknown(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    result = await handle_task(
        task_name="nonexistent",
        params={},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
    )
    assert "error" in result
    assert "unknown task" in result["error"]


# ---------------------------------------------------------------------------
# _handle_adapt_policy
# ---------------------------------------------------------------------------


async def test_adapt_policy_single_feedback(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    """adapt_policy with single dict (not list) should still work."""
    result = await _handle_adapt_policy(
        params={"motor_feedback": _make_feedback()},  # single dict
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
        executive_agent_url="",
        metacognition_url="",
    )
    assert result["episodes_added"] == 1


async def test_adapt_policy_with_training_result(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    """adapt_policy returns training result when episodes are available."""
    mock_replay_buffer.sample = AsyncMock(return_value=["ep1"])
    result = await _handle_adapt_policy(
        params={"motor_feedback": [_make_feedback()]},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
        executive_agent_url="",
        metacognition_url="",
    )
    assert result["training"] is not None
    assert result["training"]["total_timesteps"] == 64


async def test_adapt_policy_habit_promotion(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    """adapt_policy promotes habit when conditions are met."""
    mock_habit_manager.record_episode = MagicMock(return_value=True)
    mock_habit_manager.should_promote = MagicMock(return_value=True)
    result = await _handle_adapt_policy(
        params={"motor_feedback": [_make_feedback()]},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
        executive_agent_url="",
        metacognition_url="",
    )
    assert result["episodes_added"] == 1
    mock_habit_manager.promote.assert_awaited_once()


async def test_adapt_policy_training_error_notifies(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    """adapt_policy sends adaptation_failed notification when train_step raises."""
    mock_replay_buffer.sample = AsyncMock(return_value=["ep1"])
    mock_trainer.train_step = AsyncMock(side_effect=RuntimeError("train failed"))
    with patch(
        "learning_adaptation.interfaces.a2a_handler._notify_adaptation_failed",
        new=AsyncMock(),
    ) as mock_notify:
        result = await _handle_adapt_policy(
            params={"motor_feedback": [_make_feedback()]},
            replay_buffer=mock_replay_buffer,
            trainer=mock_trainer,
            habit_manager=mock_habit_manager,
            executive_agent_url="",
            metacognition_url="http://meta",
        )
    mock_notify.assert_awaited_once()
    assert result["training"] is None


async def test_adapt_policy_bad_item_continues(
    mock_replay_buffer: AsyncMock, mock_trainer: MagicMock, mock_habit_manager: MagicMock
) -> None:
    """adapt_policy skips invalid items and continues processing."""
    result = await _handle_adapt_policy(
        params={"motor_feedback": [{"invalid": "data"}, _make_feedback()]},
        replay_buffer=mock_replay_buffer,
        trainer=mock_trainer,
        habit_manager=mock_habit_manager,
        executive_agent_url="",
        metacognition_url="",
    )
    # Only valid items are counted
    assert result["episodes_added"] == 1


# ---------------------------------------------------------------------------
# _handle_replay_episode
# ---------------------------------------------------------------------------


async def test_handle_replay_episode_list(mock_replay_buffer: AsyncMock) -> None:
    result = await _handle_replay_episode(
        params={"motor_feedback": [_make_feedback(), _make_feedback()]},
        replay_buffer=mock_replay_buffer,
    )
    assert result["episodes_added"] == 2


async def test_handle_replay_episode_dict(mock_replay_buffer: AsyncMock) -> None:
    """Accepts single dict (not wrapped in list)."""
    result = await _handle_replay_episode(
        params={"motor_feedback": _make_feedback()},
        replay_buffer=mock_replay_buffer,
    )
    assert result["episodes_added"] == 1


# ---------------------------------------------------------------------------
# _notify_* (best-effort outbound calls)
# ---------------------------------------------------------------------------


async def test_notify_habit_promoted_no_url() -> None:
    """Empty URL silently skips notification."""
    await _notify_habit_promoted({"task_type": "default"}, "")  # should not raise


async def test_notify_adaptation_failed_no_url() -> None:
    """Empty URL silently skips notification."""
    await _notify_adaptation_failed({"reason": "test"}, "")  # should not raise


async def test_notify_habit_promoted_exception_swallowed() -> None:
    """Exception during notification is swallowed (best-effort)."""
    with patch("endogenai_a2a.A2AClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.send_task = AsyncMock(side_effect=RuntimeError("net error"))
        mock_cls.return_value = mock_instance
        await _notify_habit_promoted({"task_type": "x"}, "http://exec-agent")
    # Should not raise
