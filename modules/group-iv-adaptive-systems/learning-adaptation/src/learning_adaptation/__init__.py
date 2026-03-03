"""learning_adaptation — Learning & Adaptation Layer (§7.1).

Basal ganglia (PPO actor-critic) + Cerebellum (supervised correction) +
Hippocampus (ChromaDB episodic replay) for the EndogenAI adaptive-systems group.

Port: 8170
"""

from learning_adaptation.models import (
    ActionPrediction,
    HabitRecord,
    LearningAdaptationEpisode,
    LearningConfig,
    MotorFeedback,
    PolicyPromotion,
    PolicySummary,
    ReplayBufferStats,
    TrainingResult,
)

__all__ = [
    "LearningConfig",
    "MotorFeedback",
    "LearningAdaptationEpisode",
    "TrainingResult",
    "ActionPrediction",
    "HabitRecord",
    "PolicySummary",
    "ReplayBufferStats",
    "PolicyPromotion",
]

__version__ = "0.1.0"
