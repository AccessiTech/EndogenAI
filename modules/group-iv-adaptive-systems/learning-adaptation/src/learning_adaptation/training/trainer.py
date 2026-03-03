"""trainer.py — SB3 PPO training loop with shadow policy.

Maintains:
  - active_policy: PPO model (serves live predictions)
  - shadow_policy: PPO model (trained offline, promoted after N consecutive evals)

Both policies use BrainEnv. Shadow policy is promoted to active after
shadow_promotion_eval_episodes consecutive evaluations above threshold.

Neuroanatomical analogue:
  - Basal ganglia actor-critic (dopamine-gated direct/indirect pathway balance)
  - Cerebellar supervised correction via SkillFeedbackCallback
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import numpy as np
import structlog

from learning_adaptation.models import (
    ActionPrediction,
    LearningAdaptationEpisode,
    LearningConfig,
    PolicyPromotion,
    PolicySummary,
    TrainingResult,
)

if TYPE_CHECKING:
    from learning_adaptation.env.brain_env import BrainEnv
    from learning_adaptation.replay.buffer import ReplayBuffer

try:
    from stable_baselines3 import PPO
except ImportError as exc:
    raise ImportError(  # noqa: B904
        "stable-baselines3 is required: pip install stable-baselines3>=2.3.0"
    ) from exc

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class PolicyTrainer:
    """SB3 PPO training loop with shadow policy.

    Shadow policy is trained offline from replay buffer episodes.
    Promoted to active after shadow_promotion_eval_episodes consecutive
    evaluations above shadow_promotion_threshold.
    """

    def __init__(
        self,
        env: BrainEnv,
        config: LearningConfig,
        replay_buffer: ReplayBuffer,
    ) -> None:
        self._env = env
        self._config = config
        self._replay_buffer = replay_buffer

        self._active_policy: PPO = self._make_policy(env)
        self._shadow_policy: PPO | None = (
            self._make_policy(env) if config.shadow_policy_enabled else None
        )

        self._total_timesteps_active: int = 0
        self._total_timesteps_shadow: int = 0
        self._last_updated: str | None = None

        # Shadow promotion tracking
        self._shadow_eval_above_threshold: int = 0
        self._shadow_eval_scores: list[float] = []

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    async def train_step(
        self, episodes: list[LearningAdaptationEpisode]
    ) -> TrainingResult:
        """Train the shadow policy on the given episodes.

        Injects episodes into BrainEnv, trains for total_timesteps_per_run
        timesteps, then evaluates the shadow for possible promotion.
        """
        if not episodes:
            return TrainingResult(
                total_timesteps=0,
                mean_reward=0.0,
                episodes=0,
                policy_updated=False,
            )

        # Pre-load feedback into the env so training has signal
        for ep in episodes:
            # Simulate feedback injection from episode data

            synth_feedback = _episode_to_motor_feedback(ep)
            self._env.push_feedback(synth_feedback)

        timesteps = min(self._config.total_timesteps_per_run, len(episodes) * 10)

        shadow_promoted = False
        policy_updated = False
        mean_reward = 0.0
        timesteps_executed = 0

        try:
            # Build callback
            from learning_adaptation.training.skill_feedback_callback import SkillFeedbackCallback

            callback = SkillFeedbackCallback(replay_buffer=self._replay_buffer)

            policy_to_train = (
                self._shadow_policy if self._shadow_policy is not None
                else self._active_policy
            )
            policy_to_train.learn(
                total_timesteps=timesteps,
                callback=callback,
                reset_num_timesteps=False,
            )

            # Only account for timesteps once training succeeds
            timesteps_executed = timesteps
            if self._shadow_policy is not None:
                self._total_timesteps_shadow += timesteps
            else:
                self._total_timesteps_active += timesteps

            self._last_updated = datetime.datetime.now(datetime.UTC).isoformat()
            policy_updated = True

            # Compute mean reward from episodes
            if episodes:
                mean_reward = sum(ep.reward for ep in episodes) / len(episodes)

            # Evaluate shadow for promotion
            if self._shadow_policy is not None and self._config.shadow_policy_enabled:
                eval_score = await self.evaluate_shadow()
                if eval_score >= self._config.shadow_promotion_threshold:
                    self._shadow_eval_above_threshold += 1
                else:
                    self._shadow_eval_above_threshold = 0

                if self._shadow_eval_above_threshold >= self._config.shadow_promotion_eval_episodes:
                    await self.promote_shadow_to_active()
                    shadow_promoted = True
                    self._shadow_eval_above_threshold = 0

        except Exception:
            logger.exception("trainer.train_step.error")

        return TrainingResult(
            total_timesteps=timesteps_executed,
            mean_reward=mean_reward,
            episodes=len(episodes),
            policy_updated=policy_updated,
            shadow_promoted=shadow_promoted,
        )

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    async def predict(self, observation: list[float]) -> ActionPrediction:
        """Return goal-priority deltas from the active policy."""
        obs_array = np.array(observation, dtype=np.float32).reshape(1, -1)
        action, _ = self._active_policy.predict(obs_array, deterministic=True)
        deltas = action.flatten().tolist()
        # Determine task type from observation onehot (indices 3..3+K)
        K = len(self._config.goal_classes)
        onehot = observation[3: 3 + K] if len(observation) >= 3 + K else [0.0] * K
        task_type = "default"
        if onehot:
            max_idx = int(np.argmax(onehot))
            if max_idx < len(self._config.goal_classes):
                task_type = self._config.goal_classes[max_idx]
        return ActionPrediction(goal_priority_deltas=deltas, task_type=task_type)

    # ------------------------------------------------------------------
    # Shadow evaluation and promotion
    # ------------------------------------------------------------------

    async def evaluate_shadow(self) -> float:
        """Evaluate the shadow policy; returns mean reward over eval episodes."""
        if self._shadow_policy is None:
            return 0.0
        try:
            obs, _ = self._env.reset()
            total_reward = 0.0
            n_eps = self._config.shadow_promotion_eval_episodes
            for _ in range(n_eps):
                action, _ = self._shadow_policy.predict(
                    obs.reshape(1, -1), deterministic=True
                )
                obs, reward, terminated, truncated, _ = self._env.step(action.flatten())
                total_reward += float(reward)
                if terminated or truncated:
                    obs, _ = self._env.reset()
            mean_score = total_reward / max(n_eps, 1)
            self._shadow_eval_scores.append(mean_score)
            return mean_score
        except Exception:
            logger.exception("trainer.evaluate_shadow.error")
            return 0.0

    async def promote_shadow_to_active(self) -> PolicyPromotion:
        """Promote the shadow policy to active, creating a new shadow."""
        if self._shadow_policy is None:
            return PolicyPromotion(
                promoted=False,
                eval_score=0.0,
                total_timesteps=self._total_timesteps_active,
                promoted_at=datetime.datetime.now(datetime.UTC).isoformat(),
            )
        eval_score = self._shadow_eval_scores[-1] if self._shadow_eval_scores else 0.0
        now = datetime.datetime.now(datetime.UTC).isoformat()
        # Swap shadow → active
        self._active_policy = self._shadow_policy
        self._total_timesteps_active = self._total_timesteps_shadow
        # Create fresh shadow
        self._shadow_policy = self._make_policy(self._env)
        self._total_timesteps_shadow = 0
        self._last_updated = now
        logger.info("trainer.shadow_promoted", eval_score=eval_score)
        return PolicyPromotion(
            promoted=True,
            eval_score=eval_score,
            total_timesteps=self._total_timesteps_active,
            promoted_at=now,
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_policy_summary(self) -> PolicySummary:
        """Return summary of the active policy."""
        return PolicySummary(
            algorithm=self._config.algorithm,
            total_timesteps=self._total_timesteps_active,
            last_updated=self._last_updated,
        )

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def save_active(self, path: str) -> None:
        """Save the active policy to disk."""
        self._active_policy.save(path)
        logger.info("trainer.active_saved", path=path)

    def load_active(self, path: str) -> None:
        """Load a saved policy as the active policy."""
        self._active_policy = PPO.load(path, env=self._env)
        logger.info("trainer.active_loaded", path=path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _make_policy(env: BrainEnv) -> PPO:
        """Create a fresh PPO policy for the given environment."""
        return PPO(
            "MlpPolicy",
            env,
            verbose=0,
            device="cpu",
            n_steps=64,
            batch_size=32,
            n_epochs=4,
        )


def _episode_to_motor_feedback(ep: LearningAdaptationEpisode) -> Any:
    """Create a lightweight MotorFeedback-like object from an episode record."""
    from learning_adaptation.models import MotorFeedback

    obs = ep.observation
    reward_value = ep.reward
    channel_rates = obs.get("channel_success_rate", [0.5] * 5)
    channels = ["http", "a2a", "file", "render", "control-signal"]
    # Pick channel with highest success rate
    if channel_rates and len(channel_rates) >= 1:
        best_idx = int(np.argmax(channel_rates))
        channel = channels[best_idx] if best_idx < len(channels) else "http"
    else:
        channel = "http"

    return MotorFeedback(
        action_id=ep.episode_id,
        goal_id=ep.goal_id or ep.episode_id,
        channel=channel,
        success=reward_value > 0.0,
        escalate=ep.done and reward_value < 0.0,
        deviation_score=float(obs.get("mean_deviation", 0.0)),
        reward_signal={"value": reward_value},
        task_type=ep.task_type,
    )
