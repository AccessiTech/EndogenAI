"""tests/conftest.py — Shared fixtures for learning-adaptation tests."""

from __future__ import annotations

import pytest

from learning_adaptation.env.brain_env import BrainEnv
from learning_adaptation.models import LearningConfig

GOAL_CLASSES = ["default", "query", "action", "planning"]


@pytest.fixture
def config() -> LearningConfig:
    return LearningConfig(
        goal_classes=GOAL_CLASSES,
        observation_window_size=10,
        total_timesteps_per_run=64,
        shadow_promotion_eval_episodes=2,
        shadow_promotion_threshold=0.0,  # easy to meet in tests
        habit_threshold_episode_count=5,
        habit_threshold_success_rate=1.0,
    )


@pytest.fixture
def env(config: LearningConfig) -> BrainEnv:
    return BrainEnv(
        goal_classes=config.goal_classes,
        observation_window=config.observation_window_size,
    )
