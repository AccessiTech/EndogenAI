"""DSPy-style inference pipeline for the reasoning module.

All LLM calls route exclusively through LiteLLM (litellm.acompletion).
Never imports openai, anthropic, or ollama SDKs directly.
"""

from __future__ import annotations

from typing import Any

import litellm
import structlog

from reasoning.models import InferenceTrace, ReasoningStrategy

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Default configuration (overridden by InferencePipeline constructor)
# ---------------------------------------------------------------------------
_DEFAULT_MODEL = "ollama/mistral"
_DEFAULT_MAX_TOKENS = 1024
_DEFAULT_TEMPERATURE = 0.2


def _build_system_prompt(strategy: ReasoningStrategy) -> str:
    """Return a system prompt tailored to the requested reasoning strategy."""
    base = (
        "You are a precise reasoning engine. "
        "Think step by step and produce a structured chain of thought. "
        "Conclude with a clear, concise answer."
    )
    strategy_hints = {
        ReasoningStrategy.DEDUCTIVE: "Apply deductive logic: derive conclusions necessarily from premises.",
        ReasoningStrategy.INDUCTIVE: "Apply inductive reasoning: generalise from specific evidence.",
        ReasoningStrategy.ABDUCTIVE: "Apply abductive reasoning: infer the most likely explanation.",
        ReasoningStrategy.CAUSAL: "Apply causal reasoning: identify cause-and-effect relationships.",
        ReasoningStrategy.PLANNING: "Apply planning reasoning: produce an ordered sequence of steps to reach the goal.",
    }
    return f"{base} {strategy_hints.get(strategy, '')}"


def _build_user_prompt(query: str, context: list[str]) -> str:
    """Combine the query and retrieved context into a user prompt."""
    if context:
        context_block = "\n".join(f"- {c}" for c in context)
        return (
            f"Context:\n{context_block}\n\n"
            f"Question / Task:\n{query}\n\n"
            "Provide your chain of thought followed by your conclusion."
        )
    return (
        f"Question / Task:\n{query}\n\n"
        "Provide your chain of thought followed by your conclusion."
    )


def _parse_response(raw: str) -> tuple[list[str], str]:
    """Parse raw LLM text into (chain_of_thought, conclusion).

    Looks for an explicit 'Conclusion:' marker; falls back to treating
    the last paragraph as the conclusion.
    """
    import re

    # Try to find an explicit conclusion marker
    match = re.search(r"(?i)conclusion[:\s]+(.+?)$", raw, re.DOTALL)
    if match:
        conclusion = match.group(1).strip()
        preceding = raw[: match.start()].strip()
        chain = [line.strip() for line in preceding.splitlines() if line.strip()]
        return chain, conclusion

    # Fallback: last non-empty paragraph is the conclusion
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        conclusion = paragraphs[-1]
        chain = [s.strip() for p in paragraphs[:-1] for s in p.splitlines() if s.strip()]
        return chain, conclusion

    # Final fallback: no structure detected
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if lines:
        return lines[:-1], lines[-1]
    return [], raw.strip()


class InferencePipeline:
    """Executes reasoning queries through LiteLLM.

    All LLM calls are routed through ``litellm.acompletion``:
    no openai, anthropic, or ollama SDK imports here.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
        api_base: str | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._api_base = api_base

    async def run_inference(
        self,
        query: str,
        context: list[str],
        strategy: ReasoningStrategy = ReasoningStrategy.DEDUCTIVE,
        model_override: str | None = None,
    ) -> InferenceTrace:
        """Run a single inference step and return an InferenceTrace.

        Args:
            query: The question or problem statement.
            context: Retrieved evidence snippets to include in the prompt.
            strategy: Reasoning strategy to instruct the LLM.
            model_override: Optional LiteLLM model string override.

        Returns:
            A populated InferenceTrace with chain-of-thought and conclusion.
        """
        model = model_override or self._model
        messages: list[dict[str, str]] = [
            {"role": "system", "content": _build_system_prompt(strategy)},
            {"role": "user", "content": _build_user_prompt(query, context)},
        ]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
        }
        if self._api_base:
            kwargs["api_base"] = self._api_base

        logger.info("reasoning.inference.start", model=model, strategy=strategy, query=query[:80])

        response: litellm.ModelResponse = await litellm.acompletion(**kwargs)

        raw_text: str = ""
        choices = getattr(response, "choices", None)
        if choices:
            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            if message:
                raw_text = str(getattr(message, "content", "") or "")

        chain_of_thought, conclusion = _parse_response(raw_text)

        # Derive a simple confidence heuristic from chain length
        confidence = min(1.0, max(0.1, len(chain_of_thought) / 10.0))

        trace = InferenceTrace(
            query=query,
            context=context,
            chain_of_thought=chain_of_thought,
            conclusion=conclusion,
            confidence=confidence,
            strategy=strategy,
            model_used=model,
        )

        logger.info(
            "reasoning.inference.complete",
            trace_id=trace.id,
            confidence=trace.confidence,
            chain_steps=len(chain_of_thought),
        )
        return trace


# ---------------------------------------------------------------------------
# Module-level convenience wrapper
# ---------------------------------------------------------------------------

_default_pipeline: InferencePipeline | None = None


def get_default_pipeline() -> InferencePipeline:
    """Return a lazily-initialised default InferencePipeline."""
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = InferencePipeline()
    return _default_pipeline


async def run_inference(
    query: str,
    context: list[str],
    strategy: ReasoningStrategy = ReasoningStrategy.DEDUCTIVE,
) -> InferenceTrace:
    """Convenience function: run inference using the default pipeline."""
    return await get_default_pipeline().run_inference(query=query, context=context, strategy=strategy)
