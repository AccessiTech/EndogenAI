"""manager.py — HabitManager for stable policy promotion.

Promotes stable policies to habit checkpoints when success_rate >= threshold
over habit_threshold_episode_count consecutive episodes for a specific task_type.

Neuroanatomical analogue: dorsolateral striatum — consolidates well-practised
action sequences into habitual, automatic motor programs.
"""

from __future__ import annotations

import datetime
import os
import tempfile
from collections import defaultdict
from typing import TYPE_CHECKING

import structlog

from learning_adaptation.models import HabitRecord, LearningConfig

if TYPE_CHECKING:
    from learning_adaptation.training.trainer import PolicyTrainer

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class _TaskWindow:
    """Rolling window of episode outcomes for a single task_type."""

    def __init__(self, required_count: int, threshold: float) -> None:
        self.required_count = required_count
        self.threshold = threshold
        self._successes: list[bool] = []
        self._rewards: list[float] = []

    def record(self, success: bool, reward: float) -> None:
        self._successes.append(success)
        self._rewards.append(reward)

    def should_promote(self) -> bool:
        """Return True when the last N episodes meet the criteria."""
        if len(self._successes) < self.required_count:
            return False
        window = self._successes[-self.required_count:]
        return all(window) and (sum(window) / self.required_count) >= self.threshold

    def reset(self) -> None:
        self._successes.clear()
        self._rewards.clear()


class HabitManager:
    """Dorsolateral striatum analogue: promotes stable policies to habit checkpoints.

    Promotion criteria:
      - success_rate >= habit_threshold_success_rate (default 0.95)
      - over habit_threshold_episode_count (default 20) consecutive episodes
      - for the specific task_type

    Once promoted, the policy is saved to disk and a HabitRecord is stored.
    """

    def __init__(self, config: LearningConfig) -> None:
        self._config = config
        self._windows: dict[str, _TaskWindow] = defaultdict(
            lambda: _TaskWindow(
                required_count=config.habit_threshold_episode_count,
                threshold=config.habit_threshold_success_rate,
            )
        )
        self._habits: dict[str, HabitRecord] = {}
        self._habit_dir = os.path.join(tempfile.gettempdir(), "endogenai-habits")
        os.makedirs(self._habit_dir, exist_ok=True)

    def record_episode(self, task_type: str, success: bool, reward: float) -> bool:
        """Record an episode outcome for the given task_type.

        Returns True if this episode triggered habit promotion.
        """
        window = self._windows[task_type]
        if not success:
            # Reset consecutive window on failure
            window.reset()
            return False
        window.record(success, reward)
        return window.should_promote()

    def should_promote(self, task_type: str) -> bool:
        """Return True if the task_type window has met promotion criteria."""
        if task_type not in self._windows:
            return False
        return self._windows[task_type].should_promote()

    async def promote(self, task_type: str, trainer: PolicyTrainer) -> HabitRecord:
        """Save the active policy as a habit checkpoint for the given task_type.

        Returns the HabitRecord for the promoted habit.
        """
        policy_path = os.path.join(self._habit_dir, f"habit_{task_type}.zip")
        trainer.save_active(policy_path)

        eval_score = 0.0
        window = self._windows.get(task_type)
        if window and window._rewards:
            tail = window._rewards[-self._config.habit_threshold_episode_count:]
            eval_score = sum(tail) / len(tail)

        record = HabitRecord(
            task_type=task_type,
            policy_path=policy_path,
            eval_score=eval_score,
            promoted_at=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        self._habits[task_type] = record
        # Reset the window after promotion
        self._windows[task_type].reset()
        logger.info(
            "habit_manager.promoted",
            task_type=task_type,
            policy_path=policy_path,
            eval_score=eval_score,
        )
        return record

    def list_habits(self) -> list[HabitRecord]:
        """Return all promoted habit records."""
        return list(self._habits.values())
