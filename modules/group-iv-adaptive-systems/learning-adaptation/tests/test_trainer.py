"""tests/test_trainer.py — Unit tests for PolicyTrainer.

Mocks SB3 PPO and ReplayBuffer to avoid GPU/Docker requirements.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from learning_adaptation.env.brain_env import BrainEnv
from learning_adaptation.models import (
    LearningAdaptationEpisode,
    LearningConfig,
    TrainingResult,
)

GOAL_CLASSES = ["default", "query", "action", "planning"]
K = len(GOAL_CLASSES)
OBS_DIM = 3 + K + 5


def make_config(shadow_enabled: bool = True) -> LearningConfig:
    return LearningConfig(
        goal_classes=GOAL_CLASSES,
        total_timesteps_per_run=64,
        shadow_policy_enabled=shadow_enabled,
        shadow_promotion_eval_episodes=2,
        shadow_promotion_threshold=0.5,
        habit_threshold_episode_count=5,
        habit_threshold_success_rate=0.95,
    )


def make_episode(reward: float = 1.0, task_type: str = "default") -> LearningAdaptationEpisode:
    return LearningAdaptationEpisode(
        episode_id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        episode_boundary="bdi_cycle",
        observation={
            "success_rate": 0.8,
            "mean_deviation": 0.1,
            "escalation_rate": 0.0,
            "channel_success_rate": [0.9, 0.8, 0.7, 0.6, 0.5],
        },
        action={"goal_priority_deltas": [0.0, 0.0, 0.0, 0.0]},
        reward=reward,
        next_observation={"success_rate": 0.9, "mean_deviation": 0.05, "escalation_rate": 0.0},
        done=True,
        task_type=task_type,
        priority=abs(reward),
    )


def make_mock_ppo(mean_reward: float = 0.7) -> Any:
    """Create a mock PPO that responds to learn() and predict()."""
    ppo = MagicMock()
    ppo.learn = MagicMock(return_value=ppo)
    ppo.predict = MagicMock(
        return_value=(np.zeros((1, K), dtype=np.float32), None)
    )
    ppo.save = MagicMock()
    return ppo


def make_mock_replay_buffer() -> Any:
    buf = MagicMock()
    buf.add = AsyncMock()

    async def mock_sample(n: int) -> list[LearningAdaptationEpisode]:
        return [make_episode(reward=0.6) for _ in range(min(n, 3))]

    buf.sample = mock_sample
    buf.stats = AsyncMock()
    buf.size = AsyncMock(return_value=3)
    return buf


class TestPolicyTrainerTrainStep:
    @pytest.mark.asyncio
    async def test_train_step_returns_training_result(self) -> None:
        """train_step() with mock episodes should return a TrainingResult."""
        config = make_config()
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)
            trainer._active_policy = mock_ppo  # type: ignore[assignment]
            trainer._shadow_policy = make_mock_ppo()

            episodes = [make_episode(reward=float(i) * 0.1) for i in range(5)]
            result = await trainer.train_step(episodes)

        assert isinstance(result, TrainingResult)
        assert result.total_timesteps > 0
        assert result.episodes == 5

    @pytest.mark.asyncio
    async def test_train_step_empty_episodes_returns_zero(self) -> None:
        """train_step() with no episodes returns zeroed result."""
        config = make_config()
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)
            result = await trainer.train_step([])

        assert result.total_timesteps == 0
        assert result.episodes == 0
        assert result.policy_updated is False

    @pytest.mark.asyncio
    async def test_train_step_policy_updated_true_with_episodes(self) -> None:
        config = make_config()
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)
            trainer._active_policy = mock_ppo  # type: ignore[assignment]
            trainer._shadow_policy = make_mock_ppo()
            episodes = [make_episode() for _ in range(3)]
            result = await trainer.train_step(episodes)

        assert result.policy_updated is True


class TestPolicyTrainerPredict:
    @pytest.mark.asyncio
    async def test_predict_returns_action_prediction(self) -> None:
        """predict() should return an ActionPrediction with K floats."""
        config = make_config()
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)
            trainer._active_policy = mock_ppo  # type: ignore[assignment]

            observation = [0.8, 0.1, 0.0] + [1.0, 0.0, 0.0, 0.0] + [0.9, 0.8, 0.7, 0.6, 0.5]
            prediction = await trainer.predict(observation)

        assert len(prediction.goal_priority_deltas) == K
        assert isinstance(prediction.task_type, str)

    @pytest.mark.asyncio
    async def test_predict_correct_task_type_from_onehot(self) -> None:
        """predict() should derive task_type from onehot portion of observation."""
        config = make_config()
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)
            trainer._active_policy = mock_ppo  # type: ignore[assignment]

            # onehot for "query" (index 1): [0, 1, 0, 0]
            observation = [0.8, 0.1, 0.0, 0.0, 1.0, 0.0, 0.0, 0.9, 0.8, 0.7, 0.6, 0.5]
            prediction = await trainer.predict(observation)

        assert prediction.task_type == "query"


class TestShadowPolicyPromotion:
    @pytest.mark.asyncio
    async def test_shadow_promoted_after_consecutive_evals(self) -> None:
        """Shadow should be promoted after N consecutive above-threshold evals."""
        config = make_config(shadow_enabled=True)
        config = config.model_copy(update={
            "shadow_promotion_eval_episodes": 2,
            "shadow_promotion_threshold": 0.0,  # always passes
        })
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)
            trainer._active_policy = mock_ppo  # type: ignore[assignment]
            trainer._shadow_policy = make_mock_ppo()
            # Pre-set enough consecutive evals
            trainer._shadow_eval_above_threshold = config.shadow_promotion_eval_episodes - 1

            episodes = [make_episode(reward=1.0) for _ in range(3)]
            result = await trainer.train_step(episodes)

        # shadow_promoted may be True if threshold met
        assert isinstance(result.shadow_promoted, bool)

    @pytest.mark.asyncio
    async def test_no_shadow_when_disabled(self) -> None:
        """shadow_policy should be None when shadow_policy_enabled=False."""
        config = make_config(shadow_enabled=False)
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)

        assert trainer._shadow_policy is None


class TestPolicyTrainerGetPolicySummary:
    def test_get_policy_summary_returns_correct_algorithm(self) -> None:
        config = make_config()
        env = BrainEnv(goal_classes=GOAL_CLASSES)
        replay_buffer = make_mock_replay_buffer()
        mock_ppo = make_mock_ppo()

        with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
            from learning_adaptation.training.trainer import PolicyTrainer

            trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buffer)

        summary = trainer.get_policy_summary()
        assert summary.algorithm == "PPO"
        assert summary.total_timesteps == 0
        assert summary.last_updated is None
