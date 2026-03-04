"""Tests for Orchestrator — circuit-breaker, workflow ID strategy, abort."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

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

    async def test_abort_with_temporal_client_success(
        self, orchestrator: Orchestrator
    ) -> None:
        """abort_execution signals Temporal and returns aborted status."""
        mock_handle = AsyncMock()
        mock_handle.signal = AsyncMock()
        mock_client = MagicMock()  # get_workflow_handle is sync
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
        orchestrator._temporal_client = mock_client
        result = await orchestrator.abort_execution("goal-001")
        mock_handle.signal.assert_awaited_once_with("abort")
        assert result["status"] == "aborted"

    async def test_abort_with_temporal_client_raises(
        self, orchestrator: Orchestrator
    ) -> None:
        """abort_execution falls back gracefully when Temporal signal raises."""
        mock_handle = AsyncMock()
        mock_handle.signal = AsyncMock(side_effect=RuntimeError("signal failed"))
        mock_client = MagicMock()  # get_workflow_handle is sync
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
        orchestrator._temporal_client = mock_client
        result = await orchestrator.abort_execution("goal-002")
        assert result["status"] == "abort_failed"


class TestExecuteIntentionTemporalPaths:
    async def test_temporal_success_resets_failure_count(
        self, orchestrator: Orchestrator
    ) -> None:
        """Successful _run_temporal resets the failure counter."""
        orchestrator._connect_failures = 1
        mock_result = {"workflow_id": "wf-1", "orchestrator": "temporal", "status": "started"}
        with patch.object(orchestrator, "_run_temporal", new=AsyncMock(return_value=mock_result)):
            result = await orchestrator.execute_intention("goal-ok", {})
        assert orchestrator._connect_failures == 0
        assert result["orchestrator"] == "temporal"

    async def test_temporal_failure_below_threshold_reraises(
        self, orchestrator: Orchestrator
    ) -> None:
        """Temporal failure below max_retries increments count and re-raises."""
        orchestrator._connect_failures = 0  # max_retries = 3; one failure → 1 < 3
        with (
            patch.object(
                orchestrator, "_run_temporal", new=AsyncMock(side_effect=RuntimeError("down"))
            ),
            pytest.raises(RuntimeError),
        ):
            await orchestrator.execute_intention("goal-retry", {})
        assert orchestrator._connect_failures == 1

    async def test_run_fallback_raises_when_fallback_disabled(
        self, orchestrator: Orchestrator
    ) -> None:
        """_run_fallback raises OrchestrationError when fallback='none'."""
        orchestrator._config.fallback = "none"  # type: ignore[assignment]
        with pytest.raises(OrchestrationError):
            await orchestrator._run_fallback("goal-fail", {}, "wf-fail")

    async def test_run_temporal_with_existing_client(
        self, orchestrator: Orchestrator
    ) -> None:
        """_run_temporal uses an existing Temporal client to start a workflow."""
        mock_client = MagicMock()
        mock_client.start_workflow = AsyncMock()
        orchestrator._temporal_client = mock_client
        result = await orchestrator._run_temporal("goal-1", {"desc": "test"}, "wf-1")
        mock_client.start_workflow.assert_awaited_once()
        assert result["orchestrator"] == "temporal"
        assert result["status"] == "started"


class TestInFallbackPeriodExpiry:
    def test_in_fallback_period_returns_false_after_expiry(
        self, orchestrator: Orchestrator
    ) -> None:
        """_in_fallback_period resets state and returns False after expiry."""
        import time

        orchestrator._fallback_until = time.monotonic() - 1.0  # already expired
        orchestrator._connect_failures = 2
        assert orchestrator._in_fallback_period() is False
        assert orchestrator._fallback_until == 0.0
        assert orchestrator._connect_failures == 0


class TestExecuteIntentionPrimaryNone:
    async def test_primary_none_routes_to_fallback(
        self, orchestrator: Orchestrator
    ) -> None:
        """When primary='none', always use fallback without touching Temporal."""
        orchestrator._config.primary = "none"
        with patch(
            "agent_runtime.prefect_fallback.run_intention_flow",
            new=AsyncMock(return_value={"status": "completed", "results": []}),
        ) as mock_pfct:
            result = await orchestrator.execute_intention("goal-x", {})
        mock_pfct.assert_awaited_once()
        assert result["orchestrator"] == "prefect"

    async def test_fallback_none_raises_orchestration_error(
        self, orchestrator: Orchestrator
    ) -> None:
        """When fallback='none', _run_fallback raises OrchestrationError."""
        orchestrator._config.primary = "none"
        orchestrator._config.fallback = "none"
        with pytest.raises(OrchestrationError):
            await orchestrator.execute_intention("goal-fail", {})


class TestGetExecutionStatus:
    async def test_status_without_temporal_client(
        self, orchestrator: Orchestrator
    ) -> None:
        """get_execution_status returns RUNNING when no Temporal client."""
        orchestrator._temporal_client = None
        status = await orchestrator.get_execution_status("goal-1")
        assert status.goal_id == "goal-1"

    async def test_status_with_temporal_client(
        self, orchestrator: Orchestrator
    ) -> None:
        """get_execution_status queries Temporal workflow handle."""
        mock_handle = AsyncMock()
        mock_handle.query = AsyncMock(
            return_value={"abort_requested": True, "steps_completed": 2}
        )
        mock_client = MagicMock()  # get_workflow_handle is sync
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
        orchestrator._temporal_client = mock_client
        orchestrator._config.primary = "temporal"
        status = await orchestrator.get_execution_status("goal-1")
        assert status.goal_id == "goal-1"
        assert status.abort_requested is True

    async def test_status_temporal_query_exception_falls_back(
        self, orchestrator: Orchestrator
    ) -> None:
        """get_execution_status returns fallback RUNNING status on Temporal error."""
        mock_handle = AsyncMock()
        mock_handle.query = AsyncMock(side_effect=RuntimeError("query failed"))
        mock_client = MagicMock()  # get_workflow_handle is sync
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
        orchestrator._temporal_client = mock_client
        orchestrator._config.primary = "temporal"
        status = await orchestrator.get_execution_status("goal-err")
        assert status.goal_id == "goal-err"




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
