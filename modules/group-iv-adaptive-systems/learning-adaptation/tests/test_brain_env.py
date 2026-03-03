"""tests/test_brain_env.py — Unit tests for BrainEnv."""

from __future__ import annotations

import numpy as np
import pytest

from learning_adaptation.env.brain_env import BrainEnv
from learning_adaptation.models import MotorFeedback

GOAL_CLASSES = ["default", "query", "action", "planning"]
K = len(GOAL_CLASSES)
EXPECTED_OBS_DIM = 3 + K + 5  # = 12


@pytest.fixture
def env() -> BrainEnv:
    return BrainEnv(goal_classes=GOAL_CLASSES, observation_window=20)


def make_feedback(
    success: bool = True,
    escalate: bool = False,
    deviation: float = 0.1,
    channel: str = "http",
    task_type: str = "default",
    reward: float = 1.0,
) -> MotorFeedback:
    return MotorFeedback(
        action_id="a1",
        goal_id="g1",
        channel=channel,
        success=success,
        escalate=escalate,
        deviation_score=deviation,
        reward_signal={"value": reward},
        task_type=task_type,
    )


class TestBrainEnvReset:
    def test_reset_returns_correct_obs_shape(self, env: BrainEnv) -> None:
        obs, info = env.reset()
        assert obs.shape == (EXPECTED_OBS_DIM,), (
            f"Expected shape ({EXPECTED_OBS_DIM},), got {obs.shape}"
        )
        assert isinstance(info, dict)

    def test_reset_obs_dtype_float32(self, env: BrainEnv) -> None:
        obs, _ = env.reset()
        assert obs.dtype == np.float32

    def test_reset_obs_values_in_range(self, env: BrainEnv) -> None:
        obs, _ = env.reset()
        assert np.all(obs >= 0.0), "Obs values below 0"
        assert np.all(obs <= 1.0), "Obs values above 1"


class TestBrainEnvStep:
    def test_step_returns_correct_tuple_shape(self, env: BrainEnv) -> None:
        env.reset()
        action = np.zeros(K, dtype=np.float32)
        result = env.step(action)
        assert len(result) == 5, "Expected (obs, reward, terminated, truncated, info)"
        obs, reward, terminated, truncated, info = result
        assert obs.shape == (EXPECTED_OBS_DIM,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_step_obs_clipped_to_unit_interval(self, env: BrainEnv) -> None:
        env.reset()
        action = np.zeros(K, dtype=np.float32)
        obs, _, _, _, _ = env.step(action)
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0)

    def test_step_action_clipped(self, env: BrainEnv) -> None:
        """Actions outside [-0.2, 0.2] must be clipped silently."""
        env.reset()
        extreme_action = np.array([10.0, -10.0, 5.0, -5.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(extreme_action)
        assert obs.shape == (EXPECTED_OBS_DIM,)
        # The info dict should contain the action taken (clipped)
        if "action" in info:
            for a in info["action"]:
                assert a <= 0.20001 and a >= -0.20001, f"action {a} not clipped"

    def test_step_accumulates_reward_from_feedback(self, env: BrainEnv) -> None:
        env.reset()
        fb = make_feedback(reward=0.75)
        env.push_feedback(fb)
        _, reward, _, _, _ = env.step(np.zeros(K, dtype=np.float32))
        assert reward == pytest.approx(0.75)


class TestBrainEnvPushFeedback:
    def test_push_feedback_updates_success_rate(self, env: BrainEnv) -> None:
        env.reset()
        for _ in range(5):
            env.push_feedback(make_feedback(success=True))
        obs, _ = env.reset()
        # After reset the state is cleared, so check before reset
        env2 = BrainEnv(goal_classes=GOAL_CLASSES, observation_window=5)
        env2.reset()
        for _ in range(5):
            env2.push_feedback(make_feedback(success=True))
        obs2 = env2._build_obs()
        assert obs2[0] == pytest.approx(1.0), "success_rate should be 1.0 after all successes"

    def test_push_feedback_sets_goal_lifecycle_complete_on_success(self, env: BrainEnv) -> None:
        env.reset()
        assert not env._episode_boundary_reached()
        env.push_feedback(make_feedback(success=True))
        assert env._episode_boundary_reached()

    def test_push_feedback_sets_goal_lifecycle_complete_on_escalate(self, env: BrainEnv) -> None:
        env.reset()
        env.push_feedback(make_feedback(success=False, escalate=True))
        assert env._episode_boundary_reached()


class TestBrainEnvEpisodeBoundary:
    def test_episode_boundary_triggers_terminated(self, env: BrainEnv) -> None:
        env.reset()
        env.push_feedback(make_feedback(success=True))
        _, _, terminated, _, _ = env.step(np.zeros(K, dtype=np.float32))
        assert terminated is True

    def test_episode_boundary_resets_after_step(self, env: BrainEnv) -> None:
        env.reset()
        env.push_feedback(make_feedback(success=True))
        env.step(np.zeros(K, dtype=np.float32))
        # After triggered, should be cleared
        assert not env._episode_boundary_reached()

    def test_no_boundary_without_feedback(self, env: BrainEnv) -> None:
        env.reset()
        _, _, terminated, _, _ = env.step(np.zeros(K, dtype=np.float32))
        assert terminated is False


class TestBrainEnvObsValues:
    def test_obs_clipped_to_zero_one(self, env: BrainEnv) -> None:
        env.reset()
        obs = env._build_obs()
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0)

    def test_task_type_onehot_correct_index(self, env: BrainEnv) -> None:
        env.reset()
        env._current_task_type = "query"
        obs = env._build_obs()
        # onehot starts at index 3, "query" is index 1
        assert obs[3 + 1] == pytest.approx(1.0)
        assert obs[3 + 0] == pytest.approx(0.0)
        assert obs[3 + 2] == pytest.approx(0.0)
        assert obs[3 + 3] == pytest.approx(0.0)

    def test_unknown_channel_ignored(self, env: BrainEnv) -> None:
        env.reset()
        # Should not raise
        env.push_feedback(make_feedback(channel="unknown-channel"))
        obs = env._build_obs()
        assert obs.shape == (EXPECTED_OBS_DIM,)
