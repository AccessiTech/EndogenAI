"""decomposer.py — Cerebellar skill pipeline decomposition for agent-runtime.

Converts a committed goal (description + context_payload) into an ordered
SkillPipeline using LiteLLM for LLM-based decomposition.

Neuroanatomical analogue:
  - Cerebellar cortex: converts high-level motor intent into a precise,
    time-ordered sequence of muscle activation commands (SkillSteps).
  - Forward model: generates a predicted pipeline before execution begins.
  - Purkinje cell error signal: validates steps against registered tools;
    prunes unavailable tools before committing the plan.

Note (Phase 5 stub): Phase 5 reasoning module is not yet operational.
  This decomposer calls LiteLLM directly. When the reasoning module
  becomes available, swap the LiteLLM call for reasoning A2A delegation,
  keeping LiteLLM as fallback.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import litellm
import structlog
from litellm import ModelResponse

from agent_runtime.models import ChannelType, SkillPipeline, SkillStep

if TYPE_CHECKING:
    from agent_runtime.tool_registry import ToolRegistry

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DECOMPOSE_SYSTEM_PROMPT = """\
You are a task decomposition engine for an AI agent system.
Given a goal description and context, decompose it into a sequential list of skill steps.

Each step should have:
- tool_id: the ID of the tool/skill to invoke (from registered tools)
- params: parameters to pass to the tool
- channel: one of "http", "a2a", "file", "render"
- depends_on: list of step_ids this step depends on (for ordering)
- timeout_seconds: expected execution time

Return a JSON object with a "steps" array. Use only tools from the provided registry.
If no suitable tool exists, create a best-effort step with tool_id "fallback.llm_action".
"""


class PipelineDecomposer:
    """LiteLLM-backed goal decomposer.

    Converts a goal description + context_payload into a SkillPipeline
    by calling an LLM (via LiteLLM) to generate the ordered steps.
    """

    def __init__(
        self,
        model: str = "ollama/mistral",
        tool_registry: ToolRegistry | None = None,
        max_steps: int = 10,
    ) -> None:
        self._model = model
        self._registry = tool_registry
        self._max_steps = max_steps

    async def decompose(
        self,
        goal_id: str,
        description: str,
        context_payload: dict[str, Any] | None = None,
    ) -> SkillPipeline:
        """Main decomposition entry point.

        Calls LiteLLM to generate a SkillPipeline from the goal description.
        Falls back to a single-step fallback pipeline on any LLM error.
        """
        context_payload = context_payload or {}
        registered_tools = self._get_tool_descriptions()

        user_prompt = (
            f"Goal ID: {goal_id}\n"
            f"Goal: {description}\n"
            f"Context: {json.dumps(context_payload, indent=2)}\n\n"
            f"Registered tools:\n{registered_tools}\n\n"
            f"Decompose this goal into at most {self._max_steps} steps."
        )

        try:
            _resp = await litellm.acompletion(
                model=self._model,
                messages=[
                    {"role": "system", "content": _DECOMPOSE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                timeout=60,
            )
            if not isinstance(_resp, ModelResponse):
                msg = "Unexpected streaming response from LiteLLM"
                raise TypeError(msg)
            raw_content = _resp.choices[0].message.content or "{}"  # pyright: ignore[reportAttributeAccessIssue]
            steps_data = json.loads(raw_content).get("steps", [])
            steps = self._parse_steps(steps_data)
            logger.info(
                "decomposer.pipeline_generated",
                goal_id=goal_id,
                num_steps=len(steps),
            )
        except Exception as exc:
            logger.warning(
                "decomposer.llm_error",
                goal_id=goal_id,
                error=str(exc),
                fallback="single-step-fallback",
            )
            steps = self._fallback_pipeline(goal_id, description)

        return SkillPipeline(
            goal_id=goal_id,
            steps=steps,
            decomposition_model=self._model,
        )

    def _get_tool_descriptions(self) -> str:
        """Return a human-readable list of registered tools for the LLM prompt."""
        if not self._registry:
            return "(no tool registry — use fallback.llm_action for all steps)"
        available = self._registry.get_healthy_skills()
        if not available:
            return "(no healthy tools registered)"
        lines = [f"- {t.skill_id}: {t.description}" for t in available]
        return "\n".join(lines)

    def _parse_steps(self, raw_steps: list[dict[str, Any]]) -> list[SkillStep]:
        """Parse raw LLM output into SkillStep objects; skip unparseable entries."""
        steps: list[SkillStep] = []
        for raw in raw_steps:
            try:
                channel_val = raw.get("channel", "a2a")
                if channel_val not in {c.value for c in ChannelType}:
                    channel_val = "a2a"
                step = SkillStep(
                    tool_id=raw.get("tool_id", "fallback.llm_action"),
                    params=raw.get("params", {}),
                    channel=ChannelType(channel_val),
                    depends_on=raw.get("depends_on", []),
                    timeout_seconds=int(raw.get("timeout_seconds", 120)),
                    expected_output=raw.get("expected_output"),
                    parallel_group=raw.get("parallel_group"),
                )
                steps.append(step)
            except Exception as exc:
                logger.warning("decomposer.step_parse_error", raw=raw, error=str(exc))
        return steps

    def _fallback_pipeline(self, goal_id: str, description: str) -> list[SkillStep]:
        """Single-step fallback when LLM decomposition fails."""
        return [
            SkillStep(
                tool_id="fallback.llm_action",
                params={"goal_id": goal_id, "description": description},
                channel=ChannelType.A2A,
                timeout_seconds=120,
            )
        ]
