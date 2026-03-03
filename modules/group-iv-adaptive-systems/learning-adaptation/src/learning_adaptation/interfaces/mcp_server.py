"""mcp_server.py — MCP resources and tools for learning-adaptation.

MCP Resources (read-only snapshots):
  resource://brain.learning-adaptation/policy/current         → PolicySummary
  resource://brain.learning-adaptation/replay-buffer/stats    → ReplayBufferStats
  resource://brain.learning-adaptation/habits/catalog         → list[HabitRecord]

MCP Tools (write/trigger actions):
  train    → {motor_feedback: list}  → TrainingResult
  predict  → {observation: list[float]} → ActionPrediction
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from learning_adaptation.habits.manager import HabitManager
    from learning_adaptation.replay.buffer import ReplayBuffer
    from learning_adaptation.training.trainer import PolicyTrainer

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Resource definitions
# ---------------------------------------------------------------------------

MCP_RESOURCES = [
    {
        "uri": "resource://brain.learning-adaptation/policy/current",
        "name": "policy/current",
        "description": "Summary of the currently active PPO policy.",
        "mimeType": "application/json",
    },
    {
        "uri": "resource://brain.learning-adaptation/replay-buffer/stats",
        "name": "replay-buffer/stats",
        "description": "Statistics about the ChromaDB episodic replay buffer.",
        "mimeType": "application/json",
    },
    {
        "uri": "resource://brain.learning-adaptation/habits/catalog",
        "name": "habits/catalog",
        "description": "Catalog of all promoted habit checkpoints.",
        "mimeType": "application/json",
    },
]

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "train",
        "description": "Train the PPO policy on provided MotorFeedback episodes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "motor_feedback": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of MotorFeedback dicts to train on.",
                }
            },
            "required": ["motor_feedback"],
        },
    },
    {
        "name": "predict",
        "description": "Get goal-priority delta prediction from the active policy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "observation": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Observation vector (12 floats).",
                }
            },
            "required": ["observation"],
        },
    },
    {
        "name": "promote-habit",
        "description": "Manually promote the active policy as a habit for a task_type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {"type": "string"},
            },
            "required": ["task_type"],
        },
    },
]


# ---------------------------------------------------------------------------
# Resource read functions
# ---------------------------------------------------------------------------


async def get_policy_current(trainer: PolicyTrainer) -> dict[str, Any]:
    """Return the active policy summary."""
    summary = trainer.get_policy_summary()
    return summary.model_dump()


async def get_replay_buffer_stats(replay_buffer: ReplayBuffer) -> dict[str, Any]:
    """Return replay buffer statistics."""
    stats = await replay_buffer.stats()
    return stats.model_dump()


async def get_habits_catalog(habit_manager: HabitManager) -> list[dict[str, Any]]:
    """Return the habit catalog."""
    return [h.model_dump() for h in habit_manager.list_habits()]


# ---------------------------------------------------------------------------
# Tool call functions
# ---------------------------------------------------------------------------


async def call_train(
    arguments: dict[str, Any],
    replay_buffer: ReplayBuffer,
    trainer: PolicyTrainer,
    habit_manager: HabitManager,
) -> dict[str, Any]:
    """Handle the 'train' MCP tool call."""
    from learning_adaptation.interfaces.a2a_handler import _handle_adapt_policy

    result = await _handle_adapt_policy(
        params={"motor_feedback": arguments.get("motor_feedback", [])},
        replay_buffer=replay_buffer,
        trainer=trainer,
        habit_manager=habit_manager,
        executive_agent_url="",
        metacognition_url="",
    )
    return result


async def call_predict(
    arguments: dict[str, Any],
    trainer: PolicyTrainer,
) -> dict[str, Any]:
    """Handle the 'predict' MCP tool call."""
    observation = arguments.get("observation", [])
    prediction = await trainer.predict(observation)
    return prediction.model_dump()


async def call_promote_habit(
    arguments: dict[str, Any],
    habit_manager: HabitManager,
    trainer: PolicyTrainer,
) -> dict[str, Any]:
    """Handle the 'promote-habit' MCP tool call."""
    task_type = arguments.get("task_type", "default")
    record = await habit_manager.promote(task_type, trainer)
    return record.model_dump()
