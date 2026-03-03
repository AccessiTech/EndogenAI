"""test_error_policy.py -- Unit tests for retry/circuit-breaker/escalation logic."""
from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from motor_output.error_policy import CircuitBreaker, ErrorPolicy
from motor_output.models import ChannelType, ErrorPolicyConfig


def _easy_config(**overrides: object) -> ErrorPolicyConfig:
    defaults: dict[str, object] = {
        "maxAttempts": 3,
        "backoffMultiplier": 1.0,
        "initialDelaySeconds": 0.0,
        "maxDelaySeconds": 1.0,
        "circuitBreakerEnabled": False,
        "failureThreshold": 3,
        "recoveryTimeSeconds": 1.0,
        "escalateBaseUrl": "http://localhost:8161",
    }
    defaults.update(overrides)
    return ErrorPolicyConfig.model_validate(defaults)


def test_circuit_breaker_starts_closed() -> None:
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=60.0)
    assert cb._state == "CLOSED"
    assert cb.is_open() is False


def test_circuit_breaker_opens_after_threshold() -> None:
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=60.0)
    cb.record_failure()
    cb.record_failure()
    assert cb._state == "CLOSED"
    cb.record_failure()
    assert cb._state == "OPEN"
    assert cb.is_open() is True


def test_circuit_breaker_half_open_after_recovery() -> None:
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=0.01)
    cb.record_failure()
    assert cb._state == "OPEN"
    time.sleep(0.05)
    assert cb.is_open() is False
    assert cb._state == "HALF_OPEN"


def test_circuit_breaker_closes_on_success() -> None:
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=0.01)
    cb.record_failure()
    time.sleep(0.05)
    cb.is_open()
    cb.record_success()
    assert cb._state == "CLOSED"


@pytest.mark.asyncio
async def test_error_policy_success_first_try() -> None:
    policy = ErrorPolicy(config=_easy_config(), executive_agent_url="http://localhost:8161")
    dispatch_fn = AsyncMock(return_value={"success": True, "http_status": 200})
    result = await policy.execute(
        channel=ChannelType.HTTP,
        dispatch_fn=dispatch_fn,
        action_id="a1",
        goal_id="g1",
    )
    assert result["success"] is True
    assert dispatch_fn.call_count == 1


@pytest.mark.asyncio
async def test_error_policy_retries_on_exception() -> None:
    policy = ErrorPolicy(config=_easy_config(maxAttempts=3), executive_agent_url="http://localhost:8161")
    call_results: list[object] = [Exception("timeout"), Exception("timeout"), {"success": True}]
    call_idx = 0

    async def _fn() -> object:
        nonlocal call_idx
        r = call_results[call_idx]
        call_idx += 1
        if isinstance(r, Exception):
            raise r
        return r

    result = await policy.execute(
        channel=ChannelType.HTTP,
        dispatch_fn=_fn,
        action_id="a1",
        goal_id="g1",
    )
    assert result["success"] is True
    assert call_idx == 3


@pytest.mark.asyncio
async def test_error_policy_escalates_after_all_retries_fail() -> None:
    policy = ErrorPolicy(
        config=_easy_config(maxAttempts=2),
        executive_agent_url="http://localhost:8161",
    )
    dispatch_fn = AsyncMock(side_effect=Exception("permanent failure"))

    with patch.object(policy, "_escalate", new=AsyncMock()) as mock_escalate:
        result = await policy.execute(
            channel=ChannelType.HTTP,
            dispatch_fn=dispatch_fn,
            action_id="a1",
            goal_id="g1",
        )
    assert result["escalated"] is True
    mock_escalate.assert_awaited_once()


@pytest.mark.asyncio
async def test_error_policy_circuit_open_skips_dispatch() -> None:
    policy = ErrorPolicy(
        config=_easy_config(circuitBreakerEnabled=True, failureThreshold=1),
        executive_agent_url="http://localhost:8161",
    )
    cb = policy._get_breaker(ChannelType.HTTP)
    cb.record_failure()
    assert cb.is_open()

    dispatch_fn = AsyncMock(return_value={"success": True})
    with patch.object(policy, "_escalate", new=AsyncMock()):
        result = await policy.execute(
            channel=ChannelType.HTTP,
            dispatch_fn=dispatch_fn,
            action_id="a1",
            goal_id="g1",
        )
    assert result.get("escalated") is True
    dispatch_fn.assert_not_awaited()
