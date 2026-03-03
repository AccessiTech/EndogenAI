"""prefect_fallback.py — Prefect-based fallback orchestrator for agent-runtime.

Invoked by orchestrator.py when Temporal is unavailable (circuit-breaker).
Mirrors the IntentionWorkflow logic without Temporal's durability guarantees.

Neuroanatomical analogue:
  - Secondary motor cortex fallback: simplified motor programme executed
    when the primary cerebellar pathway (Temporal) is disrupted.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def run_intention_flow(
    goal_id: str,
    context_payload: dict[str, Any],
    motor_output_url: str = "http://localhost:8163",
    executive_agent_url: str = "http://localhost:8161",
) -> dict[str, Any]:
    """Prefect fallback: execute a committed intention without Temporal.

    Pipeline decomposition and step dispatch are executed sequentially.
    Partial feedback is emitted on high-deviation steps (best-effort).

    Note: This function does NOT use Prefect's @flow decorator when Prefect
    is not installed. It degrades gracefully to sequential execution.
    """
    try:
        # Attempt to use Prefect if available
        import prefect  # noqa: F401 — optional dependency check

        return await _run_with_prefect(
            goal_id, context_payload, motor_output_url, executive_agent_url
        )
    except ImportError:
        logger.warning("prefect_fallback.prefect_not_installed", goal_id=goal_id)
    except Exception as exc:
        logger.warning("prefect_fallback.prefect_error", goal_id=goal_id, error=str(exc))

    # Final fallback: sequential execution without any orchestration framework
    return await _run_sequential(
        goal_id, context_payload, motor_output_url, executive_agent_url
    )


async def _run_with_prefect(
    goal_id: str,
    context_payload: dict[str, Any],
    motor_output_url: str,
    executive_agent_url: str,
) -> dict[str, Any]:
    """Prefect flow execution (requires prefect>=3.0)."""
    from prefect import flow, task

    @task(retries=3, retry_delay_seconds=10, name="execute-skill-step")
    async def execute_step(step: dict[str, Any], gid: str) -> dict[str, Any]:
        return await _dispatch_step(step, gid, motor_output_url)

    @task(name="decompose-goal")
    async def decompose(gid: str, payload: dict[str, Any]) -> dict[str, Any]:
        from agent_runtime.decomposer import PipelineDecomposer

        dec = PipelineDecomposer()
        pipeline = await dec.decompose(
            goal_id=gid,
            description=payload.get("description", f"Goal {gid}"),
            context_payload=payload,
        )
        result: dict[str, Any] = pipeline.model_dump(mode="json")
        return result

    @flow(name="intention-workflow")
    async def intention_flow_inner(
        gid: str, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        pipeline = await decompose(gid, ctx)
        results: list[dict[str, Any]] = []
        for step in pipeline.get("steps", []):
            result: dict[str, Any] = await execute_step(step, gid)
            results.append(result)
        return {"status": "completed", "goal_id": gid, "results": results}

    result: dict[str, Any] = await intention_flow_inner(goal_id, context_payload)
    return result


async def _run_sequential(
    goal_id: str,
    context_payload: dict[str, Any],
    motor_output_url: str,
    executive_agent_url: str,
) -> dict[str, Any]:
    """Plain sequential fallback — no orchestration framework."""
    from agent_runtime.decomposer import PipelineDecomposer

    dec = PipelineDecomposer()
    pipeline = await dec.decompose(
        goal_id=goal_id,
        description=context_payload.get("description", f"Goal {goal_id}"),
        context_payload=context_payload,
    )

    results: list[dict[str, Any]] = []
    for step in pipeline.steps:
        step_dict = step.model_dump(mode="json")
        result = await _dispatch_step(step_dict, goal_id, motor_output_url)
        results.append(result)

    logger.info("prefect_fallback.sequential_completed", goal_id=goal_id)
    return {"status": "completed", "goal_id": goal_id, "results": results}


async def _dispatch_step(
    step: dict[str, Any], goal_id: str, motor_output_url: str
) -> dict[str, Any]:
    """Dispatch a single step to motor-output."""
    from uuid import uuid4

    from agent_runtime.models import ActionSpec, ChannelType

    action_spec = ActionSpec(
        type=step.get("tool_id", "unknown"),
        channel=ChannelType(step.get("channel", "a2a")),
        params=step.get("params", {}),
        goal_id=goal_id,
        step_id=step.get("step_id"),
    )
    payload = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "id": str(uuid4()),
        "params": {
            "task_type": "dispatch_action",
            "payload": action_spec.model_dump(mode="json"),
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{motor_output_url}/tasks", json=payload)
            resp.raise_for_status()
            body: dict[str, Any] = resp.json()
            result: dict[str, Any] = body.get("result") or {}
            return result
        except Exception as exc:
            logger.error("prefect_fallback.step_error", step=step, error=str(exc))
            return {"success": False, "error": str(exc), "goal_id": goal_id}
