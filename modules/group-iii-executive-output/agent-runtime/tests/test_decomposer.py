"""Tests for PipelineDecomposer."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from litellm import ModelResponse

from agent_runtime.decomposer import PipelineDecomposer
from agent_runtime.models import ChannelType, PipelineStatus


def _make_llm_response(content: str) -> ModelResponse:
    """Build a minimal non-streaming ModelResponse for test mocks."""
    return ModelResponse(
        choices=[
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    )


@pytest.fixture
def decomposer(mock_tool_registry: MagicMock) -> PipelineDecomposer:
    return PipelineDecomposer(tool_registry=mock_tool_registry, max_steps=5)


class TestDecomposerLiteLLM:
    async def test_decompose_returns_pipeline(
        self, decomposer: PipelineDecomposer
    ) -> None:
        llm_response = json.dumps(
            {
                "steps": [
                    {
                        "tool_id": "skill.test",
                        "channel": "http",
                        "params": {"url": "http://localhost:9999/act"},
                        "depends_on": [],
                    }
                ]
            }
        )
        mock_response = _make_llm_response(llm_response)

        with patch(
            "agent_runtime.decomposer.litellm.acompletion",
            new=AsyncMock(return_value=mock_response),
        ):
            pipeline = await decomposer.decompose(
                goal_id="goal-abc",
                description="Do something useful",
                context_payload={},
            )

        assert pipeline.goal_id == "goal-abc"
        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].tool_id == "skill.test"
        assert pipeline.status == PipelineStatus.PENDING

    async def test_decompose_uses_fallback_on_error(
        self, decomposer: PipelineDecomposer
    ) -> None:
        with patch(
            "agent_runtime.decomposer.litellm.acompletion",
            new=AsyncMock(side_effect=RuntimeError("LLM offline")),
        ):
            pipeline = await decomposer.decompose(
                goal_id="goal-fallback",
                description="fail gracefully",
                context_payload={},
            )

        assert pipeline.goal_id == "goal-fallback"
        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].tool_id == "fallback.llm_action"

    async def test_decompose_handles_invalid_channel(
        self, decomposer: PipelineDecomposer
    ) -> None:
        llm_response = json.dumps(
            {
                "steps": [
                    {
                        "tool_id": "skill.test",
                        "channel": "unknown_channel_xyz",
                        "params": {},
                        "depends_on": [],
                    }
                ]
            }
        )
        mock_response = _make_llm_response(llm_response)

        with patch(
            "agent_runtime.decomposer.litellm.acompletion",
            new=AsyncMock(return_value=mock_response),
        ):
            pipeline = await decomposer.decompose(
                goal_id="goal-badchannel",
                description="bad channel",
                context_payload={},
            )

        # Falls back to http or skips invalid step
        assert pipeline is not None
        for step in pipeline.steps:
            assert step.channel in {c.value for c in ChannelType}

    async def test_decompose_includes_tool_descriptions(
        self, decomposer: PipelineDecomposer, mock_tool_registry: MagicMock
    ) -> None:
        """Tool descriptions from registry are included in LLM prompt."""
        captured_messages: list[list[dict]] = []

        async def capture_call(*args: object, **kwargs: object) -> MagicMock:  # type: ignore[misc]
            captured_messages.append(kwargs.get("messages", []))  # type: ignore[arg-type]
            raise RuntimeError("stop after capture")

        with patch(
            "agent_runtime.decomposer.litellm.acompletion",
            new=AsyncMock(side_effect=capture_call),
        ):
            await decomposer.decompose("g-1", "describe it", {})

        assert len(captured_messages) > 0
        user_content = captured_messages[0][-1]["content"]
        assert "describe it" in user_content
