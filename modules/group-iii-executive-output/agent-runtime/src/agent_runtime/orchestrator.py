"""orchestrator.py — Runtime-agnostic orchestration facade for agent-runtime.

Routes execution to Temporal (primary) or Prefect (fallback) based on
the OrchestratorConfig circuit-breaker rules.

Neuroanatomical analogue:
  - Corticospinal tract: the primary motor pathway. Temporal = intact tract.
    Prefect fallback = pyramidal system degradation, using extrapyramidal backup.
  - Circuit-breaker = descending inhibition preventing runaway retries.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from agent_runtime.models import ExecutionStatus, OrchestratorConfig, PipelineStatus

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "orchestrator.config.json"


class OrchestrationError(Exception):
    """Raised when both primary and fallback orchestrators fail."""


class Orchestrator:
    """Unified orchestration facade.

    Tries the configured primary orchestrator (Temporal).
    On failure (after maxTemporalConnectRetries), switches to fallback (Prefect).
    Circuit-breaker: after fallback succeeds once, primary retries may resume after
    fallbackCooldownSeconds.
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        motor_output_url: str = "http://localhost:8163",
        executive_agent_url: str = "http://localhost:8161",
    ) -> None:
        self._config = config
        self._motor_url = motor_output_url
        self._executive_url = executive_agent_url
        self._temporal_client: Any = None
        self._connect_failures: int = 0
        self._fallback_until: float = 0.0

    @classmethod
    def from_config_file(
        cls,
        path: Path = _DEFAULT_CONFIG_PATH,
        motor_output_url: str = "http://localhost:8163",
        executive_agent_url: str = "http://localhost:8161",
    ) -> Orchestrator:
        raw = json.loads(path.read_text())
        # Parse nested fallbackTrigger fields
        trigger = raw.pop("fallbackTrigger", {})
        raw["maxTemporalConnectRetries"] = trigger.get("maxTemporalConnectRetries", 3)
        raw["fallbackCooldownSeconds"] = trigger.get("fallbackCooldownSeconds", 60)
        config = OrchestratorConfig.model_validate(raw)
        return cls(
            config=config,
            motor_output_url=motor_output_url,
            executive_agent_url=executive_agent_url,
        )

    async def execute_intention(
        self, goal_id: str, context_payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a committed intention via the configured orchestrator.

        Returns: {"workflow_id": str, "orchestrator": "temporal"|"prefect", "status": str}
        """
        workflow_id = self._build_workflow_id(goal_id)

        # Check if we should skip Temporal (circuit-breaker active)
        if self._in_fallback_period() or self._config.primary == "none":
            return await self._run_fallback(goal_id, context_payload, workflow_id)

        # Try primary (Temporal)
        if self._config.primary == "temporal":
            try:
                result = await self._run_temporal(goal_id, context_payload, workflow_id)
                self._connect_failures = 0  # Reset on success
                return result
            except Exception as exc:
                self._connect_failures += 1
                logger.warning(
                    "orchestrator.temporal_failed",
                    goal_id=goal_id,
                    failures=self._connect_failures,
                    error=str(exc),
                )
                if self._connect_failures >= self._config.max_temporal_connect_retries:
                    import time

                    self._fallback_until = time.monotonic() + self._config.fallback_cooldown_seconds
                    logger.warning("orchestrator.circuit_breaker_open", goal_id=goal_id)
                    return await self._run_fallback(goal_id, context_payload, workflow_id)
                raise

        return await self._run_fallback(goal_id, context_payload, workflow_id)

    async def get_execution_status(self, goal_id: str) -> ExecutionStatus:
        """Query execution status for a running or completed workflow."""
        workflow_id = self._build_workflow_id(goal_id)

        if self._temporal_client and self._config.primary == "temporal":
            try:
                handle = self._temporal_client.get_workflow_handle(workflow_id)
                status_data: dict[str, Any] = await handle.query("get_status")
                return ExecutionStatus(
                    goal_id=goal_id,
                    workflow_id=workflow_id,
                    orchestrator="temporal",
                    abort_requested=status_data.get("abort_requested", False),
                    has_pending_revision=status_data.get("has_pending_revision", False),
                    steps_completed=status_data.get("steps_completed", 0),
                )
            except Exception as exc:
                logger.warning(
                    "orchestrator.status_query_failed", goal_id=goal_id, error=str(exc)
                )

        return ExecutionStatus(goal_id=goal_id, status=PipelineStatus.RUNNING)

    async def abort_execution(self, goal_id: str) -> dict[str, Any]:
        """Send abort signal to a running Temporal Workflow."""
        workflow_id = self._build_workflow_id(goal_id)
        if self._temporal_client:
            try:
                handle = self._temporal_client.get_workflow_handle(workflow_id)
                await handle.signal("abort")
                logger.info("orchestrator.aborted", goal_id=goal_id)
                return {"status": "aborted", "workflow_id": workflow_id}
            except Exception as exc:
                logger.warning("orchestrator.abort_failed", goal_id=goal_id, error=str(exc))
        return {"status": "abort_failed", "goal_id": goal_id}

    async def _run_temporal(
        self, goal_id: str, context_payload: dict[str, Any], workflow_id: str
    ) -> dict[str, Any]:
        """Start a Temporal IntentionWorkflow."""
        from temporalio.client import Client

        from agent_runtime.workflow import IntentionWorkflow

        if self._temporal_client is None:
            self._temporal_client = await Client.connect(
                self._config.temporal_server_url,
                namespace=self._config.temporal_namespace,
            )

        await self._temporal_client.start_workflow(
            IntentionWorkflow.run,
            args=[goal_id, context_payload],
            id=workflow_id,
            task_queue=self._config.temporal_task_queue,
        )
        logger.info("orchestrator.temporal_started", goal_id=goal_id, workflow_id=workflow_id)
        return {"workflow_id": workflow_id, "orchestrator": "temporal", "status": "started"}

    async def _run_fallback(
        self, goal_id: str, context_payload: dict[str, Any], workflow_id: str
    ) -> dict[str, Any]:
        """Run via Prefect fallback orchestrator."""
        if self._config.fallback == "none":
            raise OrchestrationError(
                f"Temporal unavailable and fallback disabled for goal {goal_id}"
            )

        from agent_runtime.prefect_fallback import run_intention_flow

        logger.info("orchestrator.using_fallback", goal_id=goal_id)
        result = await run_intention_flow(
            goal_id=goal_id,
            context_payload=context_payload,
            motor_output_url=self._motor_url,
            executive_agent_url=self._executive_url,
        )
        return {
            "workflow_id": workflow_id,
            "orchestrator": "prefect",
            "status": result.get("status", "completed"),
            "results": result.get("results", []),
        }

    def _build_workflow_id(self, goal_id: str) -> str:
        """Build workflow ID per the configured strategy."""
        if self._config.workflow_id_strategy == "goal_id":
            return goal_id
        # goal_id_with_attempt: "{goal_id}-{attempt:03d}"
        attempt = self._connect_failures + 1
        return f"{goal_id}-{attempt:03d}"

    def _in_fallback_period(self) -> bool:
        """True if the circuit-breaker is currently open."""
        if self._fallback_until <= 0:
            return False
        import time

        if time.monotonic() > self._fallback_until:
            self._fallback_until = 0.0
            self._connect_failures = 0
            return False
        return True
