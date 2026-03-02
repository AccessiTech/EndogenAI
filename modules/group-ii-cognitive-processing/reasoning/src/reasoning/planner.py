"""Causal planner for the reasoning module.

Implements multi-hop / recursive RAG-based causal planning:
each retrieval stage informs the next query, chaining evidence into a
causal reasoning trace (see §2.2 of phase-5-mcp-solutions-and-programmatic-techniques.md).

All LLM calls route exclusively through LiteLLM.
"""

from __future__ import annotations

from typing import Any

import litellm
import structlog

from reasoning.inference import InferencePipeline
from reasoning.models import CausalPlan, InferenceTrace

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DEFAULT_MODEL = "ollama/mistral"
_DEFAULT_MAX_TOKENS = 1024
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_HORIZON = 5


def _build_step_prompt(goal: str, steps_so_far: list[str], context: list[str]) -> str:
    """Build a prompt for the next planning step."""
    context_block = "\n".join(f"- {c}" for c in context) if context else "No additional context."
    steps_block = (
        "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps_so_far))
        if steps_so_far
        else "None yet."
    )
    return (
        f"Goal: {goal}\n\n"
        f"Evidence:\n{context_block}\n\n"
        f"Steps derived so far:\n{steps_block}\n\n"
        "State the single next causal step that moves closest toward the goal. "
        "Respond with one concise sentence. If the goal is already reached, respond with 'DONE'."
    )


def _build_summary_prompt(goal: str, steps: list[str]) -> str:
    steps_block = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    return (
        f"Goal: {goal}\n\n"
        f"Causal steps:\n{steps_block}\n\n"
        "Rate the overall uncertainty of this plan on a scale from 0.0 (certain) "
        "to 1.0 (highly uncertain). Respond with only a floating-point number."
    )


class CausalPlanner:
    """Generates causal plans via multi-hop LLM reasoning through LiteLLM.

    Multi-hop approach: each planning step uses the previously derived steps
    plus retrieved context to condition the next LLM call, building a chain
    of causally-linked actions toward the goal.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
        api_base: str | None = None,
        horizon: int = _DEFAULT_HORIZON,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._api_base = api_base
        self._horizon = horizon
        self._inference_pipeline = InferencePipeline(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            api_base=api_base,
        )

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        """Issue a single LiteLLM completion call and return the text."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
        }
        if self._api_base:
            kwargs["api_base"] = self._api_base

        response: litellm.ModelResponse = await litellm.acompletion(**kwargs)
        choices = getattr(response, "choices", None)
        if choices:
            first = choices[0]
            msg = getattr(first, "message", None)
            if msg:
                return str(getattr(msg, "content", "") or "")
        return ""

    async def create_plan(
        self,
        goal: str,
        context: list[str],
        inference_traces: list[InferenceTrace] | None = None,
    ) -> CausalPlan:
        """Generate a causal plan for the given goal using multi-hop reasoning.

        Each step is derived by conditioning on prior steps + context, creating
        a chain of causally-linked actions. Stops when LLM returns 'DONE' or
        the planning horizon is reached.

        Args:
            goal: The goal to be achieved.
            context: Retrieved evidence snippets (e.g. from brain.long-term-memory).
            inference_traces: Optional prior InferenceTrace objects to inform planning.

        Returns:
            A populated CausalPlan.
        """
        trace_ids = [t.id for t in (inference_traces or [])]

        # Merge prior trace conclusions into context for richer conditioning
        enriched_context = list(context)
        for trace in inference_traces or []:
            if trace.conclusion:
                enriched_context.append(f"[Prior inference] {trace.conclusion}")

        steps: list[str] = []

        logger.info("reasoning.planner.start", goal=goal[:80], horizon=self._horizon)

        for step_idx in range(self._horizon):
            prompt = _build_step_prompt(goal, steps, enriched_context)
            raw = await self._call_llm(
                prompt=prompt,
                system=(
                    "You are a causal planning assistant. "
                    "Produce one concise causal step at a time."
                ),
            )
            step_text = raw.strip().rstrip(".")
            if not step_text or step_text.upper() == "DONE":
                logger.info("reasoning.planner.done", step_idx=step_idx)
                break
            steps.append(step_text)
            # Update context with the newly derived step (multi-hop conditioning)
            enriched_context.append(f"[Step {step_idx + 1}] {step_text}")

        # Estimate uncertainty via a follow-up LLM call
        uncertainty = 0.5
        if steps:
            uncertainty_raw = await self._call_llm(_build_summary_prompt(goal, steps))
            try:
                uncertainty = float(uncertainty_raw.strip().split()[0])
                uncertainty = max(0.0, min(1.0, uncertainty))
            except (ValueError, IndexError):
                uncertainty = 0.5

        plan = CausalPlan(
            goal=goal,
            steps=steps,
            uncertainty=uncertainty,
            horizon=self._horizon,
            trace_ids=trace_ids,
        )

        logger.info(
            "reasoning.planner.complete",
            plan_id=plan.id,
            steps=len(steps),
            uncertainty=uncertainty,
        )
        return plan


# ---------------------------------------------------------------------------
# Module-level convenience wrapper
# ---------------------------------------------------------------------------

_default_planner: CausalPlanner | None = None


def get_default_planner() -> CausalPlanner:
    """Return a lazily-initialised default CausalPlanner."""
    global _default_planner
    if _default_planner is None:
        _default_planner = CausalPlanner()
    return _default_planner


async def create_plan(goal: str, context: list[str]) -> CausalPlan:
    """Convenience function: create a plan using the default planner."""
    return await get_default_planner().create_plan(goal=goal, context=context)
