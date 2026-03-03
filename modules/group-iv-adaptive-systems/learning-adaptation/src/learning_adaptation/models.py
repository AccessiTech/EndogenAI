"""models.py — Shared Pydantic models for the Learning & Adaptation module.

These models are used across env, replay, training, habits, and interfaces.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LearningConfig(BaseModel):
    """Runtime configuration loaded from learning.config.json."""

    algorithm: str = "PPO"
    total_timesteps_per_run: int = 10000
    replay_buffer_size: int = 1000
    habit_threshold_success_rate: float = 0.95
    habit_threshold_episode_count: int = 20
    shadow_policy_enabled: bool = True
    shadow_promotion_eval_episodes: int = 5
    shadow_promotion_threshold: float = 0.8
    async_replay_interval_seconds: int = 30
    goal_classes: list[str] = Field(
        default_factory=lambda: ["default", "query", "action", "planning"]
    )
    observation_window_size: int = 20
    chromadb_url: str = "http://localhost:8000"
    metacognition_url: str = "http://localhost:8171"
    executive_agent_url: str = "http://localhost:8161"


class MotorFeedback(BaseModel):
    """Subset of motor-feedback.schema.json used for RL training."""

    action_id: str
    goal_id: str
    channel: str
    success: bool
    escalate: bool
    deviation_score: float
    reward_signal: dict[str, Any]  # full RewardSignal dict
    retry_count: int = 0
    error: str | None = None
    task_type: str = "default"  # injected by the A2A handler


class TrainingResult(BaseModel):
    """Result returned from a PPO training step."""

    total_timesteps: int
    mean_reward: float
    episodes: int
    policy_updated: bool
    shadow_promoted: bool = False


class ActionPrediction(BaseModel):
    """Predicted goal-priority deltas from the active policy."""

    goal_priority_deltas: list[float]
    task_type: str


class HabitRecord(BaseModel):
    """A promoted habit checkpoint for a specific task_type."""

    task_type: str
    policy_path: str
    eval_score: float
    promoted_at: str  # ISO 8601


class PolicySummary(BaseModel):
    """Summary of the active policy state."""

    algorithm: str
    total_timesteps: int
    last_updated: str | None


class ReplayBufferStats(BaseModel):
    """Statistics about the ChromaDB replay buffer."""

    total_episodes: int
    mean_reward: float
    top_task_type: str | None


class ObservationVector(BaseModel):
    """BrainEnv observation components stored in a LearningAdaptationEpisode."""

    success_rate: float
    mean_deviation: float
    escalation_rate: float
    task_type_onehot: list[float] = Field(default_factory=list)
    channel_success_rate: list[float] = Field(default_factory=lambda: [0.5] * 5)


class LearningAdaptationEpisode(BaseModel):
    """Episode record stored in the ChromaDB replay buffer.

    Follows shared/schemas/learning-adaptation-episode.schema.json.
    """

    episode_id: str
    timestamp: str
    episode_boundary: str = "bdi_cycle"
    observation: dict[str, Any]
    action: dict[str, Any]  # {"goal_priority_deltas": list[float]}
    reward: float
    next_observation: dict[str, Any]
    done: bool
    task_type: str
    priority: float = 0.0
    goal_id: str | None = None
    session_id: str | None = None


class PolicyPromotion(BaseModel):
    """Result of promoting a shadow policy to active."""

    promoted: bool
    eval_score: float
    total_timesteps: int
    promoted_at: str
