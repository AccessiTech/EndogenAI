"""tests/test_habit_manager.py — Unit tests for HabitManager."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from learning_adaptation.habits.manager import HabitManager
from learning_adaptation.models import LearningConfig

GOAL_CLASSES = ["default", "query", "action", "planning"]


def make_config(episode_count: int = 5, threshold: float = 1.0) -> LearningConfig:
    return LearningConfig(
        goal_classes=GOAL_CLASSES,
        habit_threshold_episode_count=episode_count,
        habit_threshold_success_rate=threshold,
    )


def make_mock_trainer() -> Any:
    trainer = MagicMock()
    trainer.save_active = MagicMock()
    trainer.get_policy_summary = MagicMock()
    return trainer


class TestHabitManagerRecordEpisode:
    def test_record_episode_returns_false_below_threshold(self) -> None:
        """record_episode() returns False when fewer than N consecutive successes."""
        config = make_config(episode_count=5)
        hm = HabitManager(config=config)
        for i in range(4):  # 4 out of 5 required
            result = hm.record_episode("default", success=True, reward=1.0)
            assert result is False, f"Should be False at episode {i + 1}"

    def test_record_episode_returns_true_at_threshold(self) -> None:
        """record_episode() returns True after N consecutive successes."""
        config = make_config(episode_count=5, threshold=1.0)
        hm = HabitManager(config=config)
        for _ in range(4):
            hm.record_episode("default", success=True, reward=1.0)
        result = hm.record_episode("default", success=True, reward=1.0)
        assert result is True

    def test_record_episode_returns_false_on_failure(self) -> None:
        """record_episode() returns False for a failed episode."""
        config = make_config(episode_count=5)
        hm = HabitManager(config=config)
        result = hm.record_episode("default", success=False, reward=-0.5)
        assert result is False

    def test_record_episode_resets_counter_on_failure(self) -> None:
        """record_episode() resets consecutive window on failure."""
        config = make_config(episode_count=3, threshold=1.0)
        hm = HabitManager(config=config)
        # Build up 2 successes
        hm.record_episode("default", success=True, reward=1.0)
        hm.record_episode("default", success=True, reward=1.0)
        # Failure resets
        hm.record_episode("default", success=False, reward=-1.0)
        # Need 3 more now (a fresh window)
        result = hm.record_episode("default", success=True, reward=1.0)
        assert result is False

    def test_record_episode_independent_per_task_type(self) -> None:
        """Windows are independent across task types."""
        config = make_config(episode_count=3, threshold=1.0)
        hm = HabitManager(config=config)
        for _ in range(3):
            hm.record_episode("query", success=True, reward=1.0)
        # query is ready but default is not
        assert hm.should_promote("query") is True
        assert hm.should_promote("default") is False


class TestHabitManagerShouldPromote:
    def test_should_promote_false_initially(self) -> None:
        config = make_config(episode_count=5)
        hm = HabitManager(config=config)
        assert hm.should_promote("default") is False

    def test_should_promote_true_after_consecutive_successes(self) -> None:
        config = make_config(episode_count=3, threshold=1.0)
        hm = HabitManager(config=config)
        for _ in range(3):
            hm.record_episode("planning", success=True, reward=1.0)
        assert hm.should_promote("planning") is True

    def test_should_promote_false_for_unknown_task_type(self) -> None:
        config = make_config()
        hm = HabitManager(config=config)
        assert hm.should_promote("nonexistent") is False


class TestHabitManagerPromote:
    @pytest.mark.asyncio
    async def test_promote_creates_habit_record(self) -> None:
        """promote() should store and return a HabitRecord."""
        config = make_config(episode_count=3, threshold=1.0)
        hm = HabitManager(config=config)
        trainer = make_mock_trainer()

        for _ in range(3):
            hm.record_episode("action", success=True, reward=0.9)

        record = await hm.promote("action", trainer)
        assert record.task_type == "action"
        assert isinstance(record.policy_path, str)
        assert isinstance(record.eval_score, float)
        assert isinstance(record.promoted_at, str)
        trainer.save_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_promote_resets_window(self) -> None:
        """After promotion, the window should be reset."""
        config = make_config(episode_count=3, threshold=1.0)
        hm = HabitManager(config=config)
        trainer = make_mock_trainer()

        for _ in range(3):
            hm.record_episode("action", success=True, reward=1.0)

        await hm.promote("action", trainer)
        # Window reset; should no longer promote
        assert hm.should_promote("action") is False


class TestHabitManagerListHabits:
    @pytest.mark.asyncio
    async def test_list_habits_empty_initially(self) -> None:
        config = make_config()
        hm = HabitManager(config=config)
        assert hm.list_habits() == []

    @pytest.mark.asyncio
    async def test_list_habits_reflects_promoted(self) -> None:
        """list_habits() should include promoted habits."""
        config = make_config(episode_count=2, threshold=1.0)
        hm = HabitManager(config=config)
        trainer = make_mock_trainer()

        for _ in range(2):
            hm.record_episode("query", success=True, reward=1.0)
        await hm.promote("query", trainer)

        habits = hm.list_habits()
        assert len(habits) == 1
        assert habits[0].task_type == "query"

    @pytest.mark.asyncio
    async def test_list_habits_multiple_task_types(self) -> None:
        """list_habits() should list all promoted habit types."""
        config = make_config(episode_count=2, threshold=1.0)
        hm = HabitManager(config=config)
        trainer = make_mock_trainer()

        for task in ["default", "query"]:
            for _ in range(2):
                hm.record_episode(task, success=True, reward=1.0)
            await hm.promote(task, trainer)

        habits = hm.list_habits()
        habit_types = {h.task_type for h in habits}
        assert "default" in habit_types
        assert "query" in habit_types
