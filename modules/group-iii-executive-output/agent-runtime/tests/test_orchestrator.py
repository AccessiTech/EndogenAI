"""Tests for Orchestrator — circuit-breaker, workflow ID strategy, abort."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

if TYPE_CHECKING:
    from agent_runtime.models import OrchestratorConfig

from agent_runtime.orchestrator import OrchestrationError, Orchestrator


@pytest.fixture
def orchestrator(sample_orch_config: OrchestratorConfig) -> Orchestrator:
    orch = Orchestrator(
        config=sample_orch_config,
        motor_output_url="http://localhost:8163",
        executive_agent_url="http://localhost:8161",
    )
    return orch


class TestWorkflowIdStrategy:
    def test_goal_id_with_attempt_default(self, orchestrator: Orchestrator) -> None:
        wf_id = orchestrator._build_workflow_id("goal-abc")
        assert wf_id.startswith("goal-abc-")

    def test_workflow_id_is_deterministic(self, orchestrator: Orchestrator) -> None:
        id1 = orchestrator._build_workflow_id("goal-xyz")
        id2 = orchestrator._build_workflow_id("goal-xyz")
        assert id1 == id2


class TestFallbackPeriod:
    def test_not_in_fallback_period_initially(self, orchestrator: Orchestrator) -> None:
        assert not orchestrator._in_fallback_period()

    def test_in_fallback_period_after_switch(self, orchestrator: Orchestrator) -> None:
        import time

        orchestrator._fallback_until = time.monotonic() + 60.0
        assert orchestrator._in_fallback_period()


class TestExecuteIntentionFallback:
    async def test_routes_to_prefect_when_temporal_unavailable(
        self, orchestrator: Orchestrator
    ) -> None:
        """Temporal circuit-breaker triggers → falls back to Prefect."""
        # Pre-saturate failures so one more triggers the circuit-breaker
        orchestrator._connect_failures = 2  # max = 3; next failure opens breaker
        with (
            patch(
                "temporalio.client.Client.connect",
                new=AsyncMock(side_effect=RuntimeError("cannot connect")),
            ),
            patch(
                "agent_runtime.prefect_fallback.run_intention_flow",
                new=AsyncMock(return_value={"status": "completed", "orchestrator": "prefect"}),
            ) as mock_prefect,
        ):
            result = await orchestrator.execute_intention("goal-001", {})

        assert mock_prefect.called or "orchestrator" in result

    async def test_raises_on_max_retries_exceeded(
        self, orchestrator: Orchestrator
    ) -> None:
        """After maxTemporalConnectRetries failures, OrchestrationError is raised."""
        orchestrator._connect_failures = 3  # saturate before call
        with (
            patch(
                "temporalio.client.Client.connect",
                new=AsyncMock(side_effect=RuntimeError("still down")),
            ),
            patch(
                "agent_runtime.prefect_fallback.run_intention_flow",
                new=AsyncMock(side_effect=RuntimeError("prefect also down")),
            ),pytest.raises((OrchestrationError, RuntimeError))
        ):
            await orchestrator.execute_intention("goal-fail", {})


class TestAbortExecution:
    async def test_abort_with_no_temporal_client(
        self, orchestrator: Orchestrator
    ) -> None:
        orchestrator._temporal_client = None
        result = await orchestrator.abort_execution("goal-404")
        assert result["goal_id"] == "goal-404"


class TestFromConfigFile:
    async def test_loads_config_file(
        self, tmp_path: pytest.TempPathFactory, sample_orch_config: OrchestratorConfig
    ) -> None:
        import json

        cfg_path = tmp_path / "orchestrator.config.json"  # type: ignore[operator]
        cfg_path.write_text(  # type: ignore[union-attr]
            json.dumps(
                {
                    "primary": "temporal",
                    "fallback": "prefect",
                    "temporalServerUrl": "localhost:7233",
                    "temporalNamespace": "test",
                    "temporalTaskQueue": "test-queue",
                    "fallbackTrigger": {"maxTemporalConnectRetries": 2},
                    "fallbackCooldownSeconds": 30,
                }
            )
        )

        orch = Orchestrator.from_config_file(
            tmp_path / "orchestrator.config.json",  # type: ignore[operator]
            motor_output_url="http://localhost:8163",
            executive_agent_url="http://localhost:8161",
        )

        assert orch._config.temporal_namespace == "test"
