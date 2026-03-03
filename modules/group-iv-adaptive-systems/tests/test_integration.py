"""test_integration.py — Phase 7 §7.3 end-to-end integration tests.

Test 1 — Escalation loop:
  MotorFeedback (escalate=True) → FeedbackHandler → metacognition.send_task("evaluate_output")
  MetacognitionEvaluator.evaluate() → escalation_total counter incremented, error_detected=True

Test 2 — Adaptation loop:
  MotorFeedback batch → handle_task("adapt_policy") → replay buffer upsert called
  trainer.train_step(episodes) → TrainingResult with total_timesteps > 0

Both tests are fully self-contained — no live Docker services required.
All external calls are mocked at the Python unit level.
"""

from __future__ import annotations

import datetime
import sys
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# sys.path: bring sibling src directories onto the Python path.
# The integration package cannot enumerate all transitive editable dependencies
# reliably across all uv sync variants, so we inject paths explicitly.
# ---------------------------------------------------------------------------
_GROUP_IV = Path(__file__).parent.parent
_GROUP_III = _GROUP_IV.parent / "group-iii-executive-output"

sys.path.insert(0, str(_GROUP_IV / "metacognition" / "src"))
sys.path.insert(0, str(_GROUP_IV / "learning-adaptation" / "src"))
sys.path.insert(0, str(_GROUP_III / "executive-agent" / "src"))

# ---------------------------------------------------------------------------
# Imports — after sys.path manipulation
# ---------------------------------------------------------------------------
from metacognition.evaluation.evaluator import (  # noqa: E402
    EvaluateOutputPayload,
    MetacognitionEvaluator,
    MonitoringConfig,
)

from learning_adaptation.env.brain_env import BrainEnv  # noqa: E402
from learning_adaptation.habits.manager import HabitManager  # noqa: E402
from learning_adaptation.interfaces.a2a_handler import handle_task  # noqa: E402
from learning_adaptation.models import (  # noqa: E402
    LearningAdaptationEpisode,
    LearningConfig,
    TrainingResult,
)
from learning_adaptation.replay.buffer import ReplayBuffer  # noqa: E402

from executive_agent.feedback import FeedbackHandler  # noqa: E402
from executive_agent.models import MotorFeedback as ExecutiveMotorFeedback  # noqa: E402

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------
GOAL_CLASSES = ["default", "query", "action", "planning"]
_K = len(GOAL_CLASSES)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_metrics_bundle() -> Any:
    """Return a mock MetricsBundle where all OTel instruments are MagicMocks."""
    bundle = MagicMock()
    bundle.task_confidence = MagicMock()
    bundle.deviation_score = MagicMock()
    bundle.reward_delta = MagicMock()
    bundle.task_success_rate = MagicMock()
    bundle.escalation_total = MagicMock()
    bundle.retry_count = MagicMock()
    bundle.policy_denial_rate = MagicMock()
    bundle.deviation_zscore = MagicMock()
    return bundle


def make_mock_ppo() -> Any:
    """Return a mock SB3 PPO that does nothing on learn() and returns zeros on predict()."""
    import numpy as np

    ppo = MagicMock()
    ppo.learn = MagicMock(return_value=ppo)
    ppo.predict = MagicMock(
        return_value=(  #
            np.zeros((1, _K), dtype=np.float32),
            None,
        )
    )
    ppo.save = MagicMock()
    return ppo


def make_mock_chroma_adapter() -> tuple[Any, list[Any]]:
    """Return (mock_adapter, upsert_calls) where upsert_calls accumulates all upsert requests."""
    upsert_calls: list[Any] = []
    adapter = MagicMock()

    async def capture_upsert(req: Any) -> Any:
        upsert_calls.append(req)
        result = MagicMock()
        result.ids = [item.id for item in req.items]
        return result

    async def empty_query(req: Any) -> Any:
        result = MagicMock()
        result.results = []
        return result

    async def noop_delete(req: Any) -> Any:
        return MagicMock()

    adapter.upsert = capture_upsert
    adapter.query = empty_query
    adapter.delete = noop_delete
    return adapter, upsert_calls


def make_learning_episode(reward: float = 1.0, task_type: str = "default") -> LearningAdaptationEpisode:
    """Build a minimal LearningAdaptationEpisode for trainer.train_step() tests."""
    return LearningAdaptationEpisode(
        episode_id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        episode_boundary="bdi_cycle",
        observation={
            "success_rate": 0.8,
            "mean_deviation": 0.1,
            "escalation_rate": 0.0,
            "task_type_onehot": [1.0, 0.0, 0.0, 0.0],
            "channel_success_rate": [0.9, 0.8, 0.7, 0.6, 0.5],
        },
        action={"goal_priority_deltas": [0.0, 0.0, 0.0, 0.0]},
        reward=reward,
        next_observation={
            "success_rate": 0.9,
            "mean_deviation": 0.05,
            "escalation_rate": 0.0,
        },
        done=True,
        task_type=task_type,
        priority=abs(reward),
    )


def make_motor_feedback_dict(
    *,
    success: bool = True,
    escalate: bool = False,
    deviation_score: float = 0.2,
    reward_value: float = 1.0,
    task_type: str = "default",
) -> dict[str, Any]:
    """Build a dict matching learning_adaptation.models.MotorFeedback for A2A handler input."""
    return {
        "action_id": str(uuid.uuid4()),
        "goal_id": str(uuid.uuid4()),
        "channel": "default",
        "success": success,
        "escalate": escalate,
        "deviation_score": deviation_score,
        "reward_signal": {"value": reward_value},
        "retry_count": 0,
        "task_type": task_type,
    }


# ---------------------------------------------------------------------------
# Test 1 — Escalation loop
# ---------------------------------------------------------------------------


async def test_escalation_triggers_evaluate_and_correction() -> None:
    """
    §7.3 Test 1 — Escalation loop (Phase 6 → metacognition → executive-agent):

    1. Build a mock MotorFeedback (escalate=True, success=False, deviation_score=0.9)
       routed through FeedbackHandler (executive-agent side).
    2. Assert that metacognition A2A client receives a ``send_task("evaluate_output", ...)`` call.
    3. Directly invoke MetacognitionEvaluator.evaluate() to exercise the metric recording path.
    4. Assert ``escalation_total`` counter was incremented (escalate=True in payload).
    5. Assert ``error_detected=True`` (deviation z-score exceeds threshold after initial push).
    """
    # --- Mock dependencies for FeedbackHandler ---
    mock_goal_stack = MagicMock()
    mock_goal_stack.transition = AsyncMock()
    mock_goal_stack.update_score = AsyncMock()

    mock_metacognition_client = MagicMock()
    mock_metacognition_client.send_task = AsyncMock()

    # --- Build executive_agent MotorFeedback (closed corollary-discharge payload) ---
    now = datetime.datetime.now(datetime.UTC)
    feedback = ExecutiveMotorFeedback(
        action_id="action-escalation-test-001",
        goal_id="goal-escalation-test-001",
        channel="default",
        actual_outcome={"status": "failed", "reason": "simulated motor error"},
        predicted_outcome={"status": "success"},
        deviation_score=0.9,
        success=False,
        escalate=True,
        error="simulated motor error",
        reward_signal={"value": -0.8},
        dispatched_at=now,
        completed_at=now,
        retry_count=1,
    )

    # --- Wire and invoke FeedbackHandler ---
    handler = FeedbackHandler(
        goal_stack=mock_goal_stack,
        metacognition_client=mock_metacognition_client,
    )
    result = await handler.receive_feedback(feedback)

    # GoalStack transition was called for the goal
    mock_goal_stack.transition.assert_awaited_once()

    # Metacognition A2A client received evaluate_output task
    mock_metacognition_client.send_task.assert_awaited_once()
    task_name = mock_metacognition_client.send_task.call_args[0][0]
    assert task_name == "evaluate_output", (
        f"Expected send_task('evaluate_output', ...) but got send_task({task_name!r}, ...)"
    )

    # Payload contains the expected fields (flat — no task_result wrapper)
    task_payload = mock_metacognition_client.send_task.call_args[0][1]
    assert task_payload.get("goal_id") == "goal-escalation-test-001"
    assert task_payload.get("escalate") is True

    # --- Exercise MetacognitionEvaluator directly ---
    metrics = make_metrics_bundle()
    config = MonitoringConfig(
        # Keep thresholds low so a single high-deviation hit triggers error_detected
        deviation_error_threshold=0.5,
        confidence_threshold=0.7,
        escalation_enabled=False,  # do not attempt outbound A2A calls in tests
        rolling_window_size=20,
    )
    evaluator = MetacognitionEvaluator(config=config, metrics_bundle=metrics)

    payload = EvaluateOutputPayload(
        goal_id="goal-escalation-test-001",
        action_id="action-escalation-test-001",
        success=False,
        escalate=True,
        deviation_score=0.9,
        reward_value=-0.8,
        task_type="default",
    )
    evaluation = await evaluator.evaluate(payload)

    # escalate=True → escalation_total counter must be incremented
    metrics.escalation_total.add.assert_called_once_with(1, {"task_type": "default"})

    # With only one observation, z-score = (0.9 - 0.9) / 1.0 = 0.0 (empty window std = 1.0)
    # On first call the window has exactly this one point; check deviation_score > threshold:
    # deviation_zscore = (0.9 - 0.9) / 1.0 = 0.0, but config.deviation_error_threshold = 0.5
    # First call: z-score = 0 since there's only one point (mu==current, sigma=1.0)
    # We verify the structural output is correct regardless of single-call z-score
    assert evaluation.task_type == "default"
    assert evaluation.deviation_score == pytest.approx(0.9)  # rolling mean of [0.9]
    assert isinstance(evaluation.error_detected, bool)

    # Second evaluation: add another high-deviation event → z-score will now exceed threshold
    payload2 = EvaluateOutputPayload(
        goal_id="goal-escalation-test-002",
        action_id="action-escalation-test-002",
        success=False,
        escalate=True,
        deviation_score=0.95,
        reward_value=-0.9,
        task_type="default",
    )
    # Prime the window with several high-deviation entries so z-score fires
    for _ in range(5):
        await evaluator.evaluate(
            EvaluateOutputPayload(
                goal_id="g",
                action_id="a",
                success=False,
                escalate=False,
                deviation_score=0.1,
                reward_value=0.1,
                task_type="default",
            )
        )
    # Now inject an anomalous spike
    spike_payload = EvaluateOutputPayload(
        goal_id="goal-spike",
        action_id="action-spike",
        success=False,
        escalate=True,
        deviation_score=0.95,
        reward_value=-0.9,
        task_type="default",
    )
    spike_eval = await evaluator.evaluate(spike_payload)
    # After priming with low-deviation and then a high spike, error_detected should be True
    assert spike_eval.error_detected is True, (
        f"Expected error_detected=True on spike but got deviation_zscore={spike_eval.deviation_zscore:.3f}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Adaptation loop
# ---------------------------------------------------------------------------


async def test_adapt_policy_populates_replay_buffer() -> None:
    """
    §7.3 Test 2 — Adaptation loop (motor-output → learning-adaptation → replay buffer):

    1. Build 5 mock MotorFeedback payloads (success and failure mix).
    2. Call handle_task("adapt_policy", ...) with the batch.
    3. Assert ChromaDB adapter upsert was called (episodes stored in brain.learning-adaptation).
    4. Call trainer.train_step() with mock episodes.
    5. Assert TrainingResult.total_timesteps > 0.
    """
    # --- Mock ChromaDB adapter ---
    adapter, upsert_calls = make_mock_chroma_adapter()

    # --- Config ---
    config = LearningConfig(
        goal_classes=GOAL_CLASSES,
        total_timesteps_per_run=64,
        shadow_policy_enabled=False,       # simplify — no shadow promotion in integration test
        habit_threshold_episode_count=100,  # never promote habits during test
        habit_threshold_success_rate=1.0,
        observation_window_size=10,
    )

    # --- BrainEnv (real) ---
    env = BrainEnv(
        goal_classes=config.goal_classes,
        observation_window=config.observation_window_size,
    )

    # --- ReplayBuffer backed by mock adapter ---
    replay_buf = ReplayBuffer(adapter=adapter, max_size=100)

    # --- HabitManager ---
    habit_manager = HabitManager(config=config)

    # --- PolicyTrainer with patched PPO ---
    mock_ppo = make_mock_ppo()
    with patch("learning_adaptation.training.trainer.PPO", return_value=mock_ppo):
        from learning_adaptation.training.trainer import PolicyTrainer  # noqa: PLC0415

        trainer = PolicyTrainer(env=env, config=config, replay_buffer=replay_buf)
        # Ensure the already-created active policy is our mock
        trainer._active_policy = mock_ppo  # type: ignore[assignment]

    # --- Build 5 mixed MotorFeedback payloads ---
    motor_feedback_batch = [
        make_motor_feedback_dict(success=True,  deviation_score=0.1, reward_value=1.0),
        make_motor_feedback_dict(success=False, escalate=True, deviation_score=0.8, reward_value=-0.6),
        make_motor_feedback_dict(success=True,  deviation_score=0.2, reward_value=0.9),
        make_motor_feedback_dict(success=False, deviation_score=0.6, reward_value=-0.4),
        make_motor_feedback_dict(success=True,  deviation_score=0.15, reward_value=0.85),
    ]

    # --- Invoke A2A adapt_policy handler ---
    response = await handle_task(
        task_name="adapt_policy",
        params={"motor_feedback": motor_feedback_batch},
        replay_buffer=replay_buf,
        trainer=trainer,
        habit_manager=habit_manager,
        executive_agent_url="",   # empty → notification skipped (best-effort)
        metacognition_url="",
    )

    # Handler returned ok status
    assert response["status"] == "ok", f"Unexpected response: {response}"

    # Episodes were added (upsert was called at least 5 times — one per feedback item)
    assert response["episodes_added"] == 5, (
        f"Expected 5 episodes_added but got {response['episodes_added']}"
    )
    assert len(upsert_calls) >= 5, (
        f"Expected upsert to be called ≥5 times but was called {len(upsert_calls)} times"
    )

    # Each upsert stored an item in the correct collection
    for call_req in upsert_calls:
        from learning_adaptation.replay.buffer import COLLECTION_NAME  # noqa: PLC0415

        assert call_req.collection_name == COLLECTION_NAME, (
            f"Wrong collection: {call_req.collection_name!r}"
        )

    # --- Directly call train_step with 5 mock episodes ---
    mock_episodes = [make_learning_episode(reward=0.5 * i - 1.0) for i in range(5)]
    train_result = await trainer.train_step(mock_episodes)

    # TrainingResult must report executed timesteps
    assert isinstance(train_result, TrainingResult)
    assert train_result.total_timesteps > 0, (
        f"Expected total_timesteps > 0 but got {train_result.total_timesteps}"
    )
    assert train_result.episodes == 5, (
        f"Expected episodes=5 but got {train_result.episodes}"
    )
    assert train_result.policy_updated is True, "policy_updated should be True after training"
