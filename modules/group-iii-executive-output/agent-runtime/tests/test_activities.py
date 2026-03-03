"""Tests for RuntimeActivities — decompose_goal, dispatch_to_motor_output."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from endogenai_a2a import A2AError

from agent_runtime.activities import RuntimeActivities
from agent_runtime.models import ChannelType, PipelineStatus, SkillPipeline, SkillStep


@pytest.fixture
def mock_decomposer() -> MagicMock:
    dec = MagicMock()
    dec.decompose = AsyncMock(
        return_value=SkillPipeline(
            id="pipe-001",
            goal_id="goal-001",
            steps=[
                SkillStep(
                    step_id="s1",
                    tool_id="skill.test",
                    channel=ChannelType.HTTP,
                    params={"url": "http://localhost:9999/act"},
                    depends_on=[],
                )
            ],
            status=PipelineStatus.PENDING,
        )
    )
    return dec


@pytest.fixture
def activities(mock_decomposer: MagicMock) -> RuntimeActivities:
    return RuntimeActivities(
        motor_output_url="http://localhost:8163",
        executive_agent_url="http://localhost:8161",
        decomposer=mock_decomposer,
    )


class TestDecomposeGoalActivity:
    async def test_decompose_goal_returns_pipeline(
        self, activities: RuntimeActivities
    ) -> None:
        result = await activities.decompose_goal(
            goal_id="goal-001",
            context_payload={"description": "test goal"},
        )
        assert result["goal_id"] == "goal-001"
        assert "steps" in result
        assert len(result["steps"]) == 1

    async def test_decompose_goal_passes_context(
        self, activities: RuntimeActivities, mock_decomposer: MagicMock
    ) -> None:
        ctx = {"description": "specific task", "priority": "high"}
        await activities.decompose_goal("goal-ctx", ctx)
        mock_decomposer.decompose.assert_called_once_with(
            goal_id="goal-ctx",
            description="specific task",
            context_payload=ctx,
        )


class TestDispatchToMotorOutput:
    async def test_dispatch_success(self, activities: RuntimeActivities) -> None:
        response_data = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "action_id": "act-001",
                "status": "dispatched",
                "success": True,
            },
        }
        step = {
            "step_id": "s1",
            "tool_id": "skill.test",
            "channel": "http",
            "params": {"url": "http://localhost:9999/act"},
            "depends_on": [],
        }
        with respx.mock:
            respx.post("http://localhost:8163/tasks").mock(
                return_value=httpx.Response(200, json=response_data)
            )
            result = await activities.dispatch_to_motor_output(
                step=step,
                goal_id="goal-001",
            )

        assert result["success"] is True

    async def test_dispatch_propagates_error(
        self, activities: RuntimeActivities
    ) -> None:
        step = {
            "step_id": "s1",
            "tool_id": "skill.test",
            "channel": "http",
            "params": {},
            "depends_on": [],
        }
        with respx.mock:
            respx.post("http://localhost:8163/tasks").mock(
                side_effect=httpx.ConnectError("refused")
            )
            with pytest.raises(A2AError):
                await activities.dispatch_to_motor_output(
                    step=step,
                    goal_id="goal-001",
                )


class TestEmitPartialFeedback:
    async def test_emit_partial_feedback_success(
        self, activities: RuntimeActivities
    ) -> None:
        response_data = {"jsonrpc": "2.0", "id": "1", "result": {"status": "received"}}
        result_dict = {
            "action_id": "act-001",
            "channel": "http",
            "actual_outcome": {"http_status": 200},
            "deviation_score": 0.1,
            "success": True,
        }
        with respx.mock:
            respx.post("http://localhost:8161/tasks").mock(
                return_value=httpx.Response(200, json=response_data)
            )
            await activities.emit_partial_feedback(
                goal_id="goal-001",
                result=result_dict,
            )
        # No exception = success

    async def test_emit_partial_feedback_tolerates_failure(
        self, activities: RuntimeActivities
    ) -> None:
        """Partial feedback failures must not abort the workflow step."""
        result_dict = {
            "action_id": "act-001",
            "deviation_score": 0.9,
            "success": False,
        }
        with respx.mock:
            respx.post("http://localhost:8161/tasks").mock(
                side_effect=httpx.ConnectError("agent down")
            )
            # Should not raise
            await activities.emit_partial_feedback(
                goal_id="goal-001",
                result=result_dict,
            )

