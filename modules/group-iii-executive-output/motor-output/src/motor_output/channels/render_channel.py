"""render_channel.py — Structured output / render channel.

LiteLLM-backed text generation: converts ActionSpec params into a
structured response via the configured language model.

Cerebellar vermis analogue: fine motor coordination — generating precise,
structured output from high-level directives.
"""
from __future__ import annotations

from typing import Any

import litellm
import structlog
from litellm import ModelResponse

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DEFAULT_MODEL = "ollama/mistral"
_DEFAULT_MAX_TOKENS = 2048
_DEFAULT_TEMPERATURE = 0.3


class RenderChannel:
    """Generates structured text output via LiteLLM."""

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def dispatch(
        self,
        params: dict[str, Any],
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        """Generate text output using LiteLLM.

        Expected params keys:
          - prompt (required): the generation prompt or instruction
          - system_prompt (optional): system context for the model
          - format (optional): "text" | "json" (default: "text")
          - model (optional): override the default model
          - max_tokens (optional): override default max_tokens
        """
        prompt: str = params.get("prompt", "")
        if not prompt:
            raise ValueError("RenderChannel.dispatch requires params['prompt']")
        system_prompt: str = params.get(
            "system_prompt",
            "You are a helpful AI assistant that follows instructions precisely.",
        )
        output_format: str = params.get("format", "text")
        model: str = params.get("model", self._model)
        max_tokens: int = int(params.get("max_tokens", self._max_tokens))

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        extra_kwargs: dict[str, Any] = {}
        if output_format == "json":
            extra_kwargs["response_format"] = {"type": "json_object"}

        logger.debug("render_channel.generate", model=model, format=output_format)

        _resp = await litellm.acompletion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=self._temperature,
            timeout=float(timeout_seconds),
            **extra_kwargs,
        )
        if not isinstance(_resp, ModelResponse):
            msg = "Unexpected streaming response from LiteLLM"
            raise TypeError(msg)

        content: str = _resp.choices[0].message.content or ""  # pyright: ignore[reportAttributeAccessIssue]
        logger.info("render_channel.generated", model=model, tokens=len(content.split()))

        return {
            "success": True,
            "content": content,
            "model": model,
            "format": output_format,
        }
