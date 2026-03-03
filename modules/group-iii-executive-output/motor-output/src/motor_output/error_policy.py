"""error_policy.py — Three-tier error policy for motor-output dispatch.

Tier 1: Retry with exponential backoff (transient errors, e.g. 429, 503)
Tier 2: Circuit-breaker (fail fast when a channel is persistently unhealthy)
Tier 3: Escalate to executive-agent A2A (unrecoverable errors)

Neuroanatomical analogues:
  - Tier 1 (retry): stretch reflex arc — local error correction at spinal level
  - Tier 2 (circuit-breaker): descending inhibition — cortical suppression
    of futile motor commands
  - Tier 3 (escalate): cortico-thalamo-cortical loop — escalation to higher
    executive centres when motor programme fails
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Callable  # noqa: TC003
from typing import Any

import structlog

from motor_output.models import ChannelType, ErrorPolicyConfig  # noqa: TC001

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class CircuitBreaker:
    """Per-channel circuit breaker.

    States: CLOSED (normal) → OPEN (fail-fast) → HALF_OPEN (probe)
    """

    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 60.0) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_seconds = recovery_seconds
        self._failures: deque[float] = deque(maxlen=failure_threshold)
        self._opened_at: float = 0.0
        self._state: str = "CLOSED"

    def record_failure(self) -> None:
        self._failures.append(time.monotonic())
        if len(self._failures) >= self._failure_threshold:
            self._state = "OPEN"
            self._opened_at = time.monotonic()
            logger.warning("circuit_breaker.opened")

    def record_success(self) -> None:
        self._failures.clear()
        self._state = "CLOSED"

    def is_open(self) -> bool:
        if self._state == "OPEN":
            if time.monotonic() - self._opened_at > self._recovery_seconds:
                self._state = "HALF_OPEN"
                return False
            return True
        return False


class ErrorPolicy:
    """Applies the three-tier error policy to channel dispatch calls."""

    def __init__(
        self,
        config: ErrorPolicyConfig,
        executive_agent_url: str = "http://localhost:8161",
    ) -> None:
        self._config = config
        self._executive_url = executive_agent_url
        self._breakers: dict[ChannelType, CircuitBreaker] = {}

    def _get_breaker(self, channel: ChannelType) -> CircuitBreaker:
        if channel not in self._breakers:
            self._breakers[channel] = CircuitBreaker(
                failure_threshold=self._config.failure_threshold,
                recovery_seconds=self._config.recovery_time_seconds,
            )
        return self._breakers[channel]

    async def execute(
        self,
        channel: ChannelType,
        dispatch_fn: Callable[[], Any],
        action_id: str,
        goal_id: str | None = None,
    ) -> dict[str, Any]:
        """Run dispatch_fn through the three-tier error policy.

        Returns: dispatch result dict with retry_count added.
        """
        breaker = self._get_breaker(channel)

        # Tier 2: circuit-breaker check before even trying
        if breaker.is_open():
            logger.warning(
                "error_policy.circuit_open", channel=channel, action_id=action_id
            )
            if self._config.escalate_base_url:
                await self._escalate(
                    action_id=action_id,
                    goal_id=goal_id,
                    reason="circuit_breaker_open",
                    channel=channel,
                )
            return {
                "success": False,
                "error": f"circuit breaker open for channel {channel}",
                "escalated": True,
                "retry_count": 0,
            }

        # Tier 1: retry with exponential backoff
        delay = self._config.initial_delay_seconds
        last_exc: Exception | None = None

        for attempt in range(self._config.max_attempts):
            try:
                result: dict[str, Any] = await dispatch_fn()
                breaker.record_success()
                result_with_retries: dict[str, Any] = {**result, "retry_count": attempt}
                return result_with_retries
            except Exception as exc:
                last_exc = exc
                breaker.record_failure()
                logger.warning(
                    "error_policy.retry",
                    attempt=attempt + 1,
                    max_attempts=self._config.max_attempts,
                    error=str(exc),
                    channel=channel,
                )
                if attempt < self._config.max_attempts - 1:
                    await asyncio.sleep(min(delay, self._config.max_delay_seconds))
                    delay = min(delay * self._config.backoff_multiplier, self._config.max_delay_seconds)

        # Tier 3: all retries exhausted — escalate
        logger.error(
            "error_policy.max_retries_exceeded",
            action_id=action_id,
            channel=channel,
            error=str(last_exc),
        )
        await self._escalate(
            action_id=action_id,
            goal_id=goal_id,
            reason="max_retries_exceeded",
            channel=channel,
            error=str(last_exc),
        )
        return {
            "success": False,
            "error": str(last_exc),
            "escalated": True,
            "retry_count": self._config.max_attempts,
        }

    async def _escalate(
        self,
        action_id: str,
        goal_id: str | None,
        reason: str,
        channel: ChannelType,
        error: str = "",
    ) -> None:
        """Notify executive-agent of an unrecoverable dispatch failure."""
        try:
            import httpx as _httpx

            payload = {
                "jsonrpc": "2.0",
                "method": "dispatch_failure",
                "id": action_id,
                "params": {
                    "task_type": "dispatch_failure",
                    "payload": {
                        "action_id": action_id,
                        "goal_id": goal_id,
                        "channel": channel,
                        "reason": reason,
                        "error": error,
                    },
                },
            }
            async with _httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{self._executive_url}/tasks", json=payload)
            logger.info("error_policy.escalated", action_id=action_id, reason=reason)
        except Exception as exc:
            logger.warning("error_policy.escalation_failed", error=str(exc))
