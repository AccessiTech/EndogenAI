"""a2a_handler.py — A2A JSON-RPC 2.0 task handler for learning-adaptation.

Inbound tasks:
  - adapt_policy  : MotorFeedback (single or batch) → replay + optional train
  - replay_episode: list[MotorFeedback] → adds to replay buffer for later training

Outbound tasks (sent via endogenai-a2a client):
  - habit_promoted   → executive-agent (when a habit is promoted)
  - adaptation_failed → metacognition (when training fails critically)
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

import structlog

from learning_adaptation.models import LearningAdaptationEpisode, MotorFeedback

if TYPE_CHECKING:
    from learning_adaptation.habits.manager import HabitManager
    from learning_adaptation.replay.buffer import ReplayBuffer
    from learning_adaptation.training.trainer import PolicyTrainer

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def _feedback_to_episode(
    feedback: MotorFeedback,
    next_obs: dict[str, Any] | None = None,
) -> LearningAdaptationEpisode:
    """Convert a MotorFeedback record to a LearningAdaptationEpisode."""
    reward_value = 0.0
    rs = feedback.reward_signal
    if isinstance(rs, dict):
        v = rs.get("value", rs.get("reward", 0.0))
        reward_value = float(v) if v is not None else 0.0

    obs: dict[str, Any] = {
        "success_rate": 1.0 if feedback.success else 0.0,
        "mean_deviation": feedback.deviation_score,
        "escalation_rate": 1.0 if feedback.escalate else 0.0,
        "channel_success_rate": [1.0 if feedback.success else 0.0] * 5,
    }
    if next_obs is None:
        next_obs = {**obs}

    priority = abs(reward_value)
    return LearningAdaptationEpisode(
        episode_id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        episode_boundary="bdi_cycle",
        observation=obs,
        action={"goal_priority_deltas": [0.0, 0.0, 0.0, 0.0]},
        reward=reward_value,
        next_observation=next_obs,
        done=feedback.success or feedback.escalate,
        task_type=feedback.task_type,
        priority=priority,
        goal_id=feedback.goal_id,
    )


async def handle_task(
    task_name: str,
    params: dict[str, Any],
    replay_buffer: ReplayBuffer,
    trainer: PolicyTrainer,
    habit_manager: HabitManager,
    executive_agent_url: str = "http://localhost:8161",
    metacognition_url: str = "http://localhost:8171",
) -> dict[str, Any]:
    """Dispatch an inbound A2A task and return the result dict."""
    if task_name == "adapt_policy":
        return await _handle_adapt_policy(
            params, replay_buffer, trainer, habit_manager,
            executive_agent_url, metacognition_url,
        )
    elif task_name == "replay_episode":
        return await _handle_replay_episode(params, replay_buffer)
    else:
        return {"error": f"unknown task: {task_name}"}


async def _handle_adapt_policy(
    params: dict[str, Any],
    replay_buffer: ReplayBuffer,
    trainer: PolicyTrainer,
    habit_manager: HabitManager,
    executive_agent_url: str,
    metacognition_url: str,
) -> dict[str, Any]:
    """Process an adapt_policy task.

    Accepts single MotorFeedback dict or list of MotorFeedback dicts.
    Adds episodes to the replay buffer and optionally triggers a training step.
    """
    feedback_items = params.get("motor_feedback", [])
    if isinstance(feedback_items, dict):
        feedback_items = [feedback_items]

    episodes: list[LearningAdaptationEpisode] = []
    for item in feedback_items:
        try:
            fb = MotorFeedback(**item)
            episode = _feedback_to_episode(fb)
            await replay_buffer.add(episode)
            episodes.append(episode)
            # Update BrainEnv with this feedback
            trainer._env.push_feedback(fb)
            # Record in habit manager
            reward_val = float(item.get("reward_signal", {}).get("value", 0.0))
            promoted = habit_manager.record_episode(fb.task_type, fb.success, reward_val)
            if promoted and habit_manager.should_promote(fb.task_type):
                try:
                    habit_record = await habit_manager.promote(fb.task_type, trainer)
                    logger.info("a2a.habit_promoted", task_type=fb.task_type)
                    # Notify executive-agent (best-effort)
                    await _notify_habit_promoted(habit_record.model_dump(), executive_agent_url)
                except Exception:
                    logger.exception("a2a.habit_promoted.error")
        except Exception:
            logger.exception("a2a.adapt_policy.item.error", item=item)
            continue

    # Trigger training if episodes available
    train_result = None
    if episodes:
        try:
            all_episodes = await replay_buffer.sample(64)
            if all_episodes:
                train_result = await trainer.train_step(all_episodes)
        except Exception:
            logger.exception("a2a.adapt_policy.train.error")
            await _notify_adaptation_failed(
                {"reason": "training error", "episodes": len(episodes)},
                metacognition_url,
            )

    return {
        "status": "ok",
        "episodes_added": len(episodes),
        "training": train_result.model_dump() if train_result else None,
    }


async def _handle_replay_episode(
    params: dict[str, Any],
    replay_buffer: ReplayBuffer,
) -> dict[str, Any]:
    """Process a replay_episode task.

    Accepts a list of MotorFeedback dicts and stores them in the replay buffer.
    """
    feedback_list = params.get("motor_feedback", [])
    if isinstance(feedback_list, dict):
        feedback_list = [feedback_list]

    added = 0
    for item in feedback_list:
        try:
            fb = MotorFeedback(**item)
            episode = _feedback_to_episode(fb)
            await replay_buffer.add(episode)
            added += 1
        except Exception:
            logger.exception("a2a.replay_episode.item.error", item=item)

    return {"status": "ok", "episodes_added": added}


async def _notify_habit_promoted(
    habit_data: dict[str, Any],
    executive_agent_url: str,
) -> None:
    """Best-effort outbound notification to executive-agent."""
    if not executive_agent_url:
        return
    try:
        from endogenai_a2a import A2AClient

        client = A2AClient(url=executive_agent_url)
        await client.send_task(task_type="habit_promoted", payload=habit_data)
    except Exception:
        logger.warning("a2a.notify_habit_promoted.failed", url=executive_agent_url)


async def _notify_adaptation_failed(
    error_data: dict[str, Any],
    metacognition_url: str,
) -> None:
    """Best-effort outbound notification to metacognition."""
    if not metacognition_url:
        return
    try:
        from endogenai_a2a import A2AClient

        client = A2AClient(url=metacognition_url)
        await client.send_task(task_type="adaptation_failed", payload=error_data)
    except Exception:
        logger.warning("a2a.notify_adaptation_failed.failed", url=metacognition_url)
