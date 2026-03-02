"""Integration tests for end-to-end signal flow through the affective module.

These tests are marked @pytest.mark.integration and are excluded from the default
CI run. They require ChromaDB and Ollama to be running locally.
Run explicitly with: uv run pytest tests/ -m integration
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from endogenai_vector_store import ChromaAdapter
from endogenai_vector_store.models import UpsertResponse

from affective.a2a_handler import A2AHandler
from affective.drive import DriveStateMachine
from affective.mcp_tools import MCPTools
from affective.models import RewardSignal, SignalType, TriggerType
from affective.store import AffectiveStore
from affective.weighting import WeightingDispatcher

# Path to the canonical JSON Schema for reward signals
# Traversal: tests/ → affective/ → group-ii-cognitive-processing/ → modules/ → EndogenAI/
_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "shared"
    / "types"
    / "reward-signal.schema.json"
)


@pytest.mark.integration
class TestSignalSchemaConformance:
    """Validate emitted RewardSignal objects against reward-signal.schema.json."""

    def test_schema_file_exists(self) -> None:
        assert _SCHEMA_PATH.exists(), f"Schema not found at {_SCHEMA_PATH}"

    def test_reward_signal_conforms_to_schema(self) -> None:
        """Validate that a RewardSignal serialises to a schema-conformant dict."""
        try:
            import jsonschema  # noqa: PLC0415
        except ImportError:
            pytest.skip("jsonschema not installed — skipping schema validation test")

        schema = json.loads(_SCHEMA_PATH.read_text())
        signal = RewardSignal(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            sourceModule="affective",
            value=0.75,
            type=SignalType.REWARD,
            trigger=TriggerType.TASK_SUCCESS,
            associatedMemoryItemId=str(uuid.uuid4()),
        )
        # Serialise using camelCase aliases to match schema
        data = signal.model_dump(by_alias=True, exclude_none=True)
        jsonschema.validate(instance=data, schema=schema)  # raises if invalid


@pytest.mark.integration
class TestEndToEndSignalFlow:
    """End-to-end signal flow: emit → store → boost dispatch."""

    @pytest.fixture
    def mock_adapter(self) -> MagicMock:
        adapter = MagicMock(spec=ChromaAdapter)
        adapter.upsert = AsyncMock(return_value=UpsertResponse(upserted_ids=[]))
        return adapter

    @pytest.fixture
    def affective_store(self, mock_adapter: MagicMock) -> AffectiveStore:
        return AffectiveStore(adapter=mock_adapter)

    @pytest.fixture
    def drive_machine(self) -> DriveStateMachine:
        return DriveStateMachine()

    @pytest.fixture
    def dispatcher(self) -> WeightingDispatcher:
        return WeightingDispatcher()

    @pytest.fixture
    def a2a(
        self,
        affective_store: AffectiveStore,
        drive_machine: DriveStateMachine,
        dispatcher: WeightingDispatcher,
    ) -> A2AHandler:
        return A2AHandler(
            store=affective_store,
            drive_machine=drive_machine,
            dispatcher=dispatcher,
        )

    @pytest.fixture
    def mcp(
        self,
        affective_store: AffectiveStore,
        drive_machine: DriveStateMachine,
        dispatcher: WeightingDispatcher,
    ) -> MCPTools:
        return MCPTools(
            store=affective_store,
            drive_machine=drive_machine,
            dispatcher=dispatcher,
        )

    async def test_a2a_emit_reward_signal_stores_and_returns_id(
        self, a2a: A2AHandler, mock_adapter: MagicMock
    ) -> None:
        memory_id = str(uuid.uuid4())
        result = await a2a.handle(
            "emit_reward_signal",
            {
                "value": 0.8,
                "type": "reward",
                "trigger": "task-success",
                "associated_memory_item_id": memory_id,
                "session_id": "session-int-001",
            },
        )
        assert "signal_id" in result
        assert result["value"] == pytest.approx(0.8)
        mock_adapter.upsert.assert_awaited_once()

    async def test_mcp_emit_reward_signal_end_to_end(
        self, mcp: MCPTools, mock_adapter: MagicMock
    ) -> None:
        memory_id = str(uuid.uuid4())
        result = await mcp.handle(
            "affective.emit_reward_signal",
            {
                "value": 0.5,
                "type": "urgency",
                "trigger": "prediction-error",
                "associated_memory_item_id": memory_id,
            },
        )
        assert result["stored"] is True
        assert "signal_id" in result

    async def test_compute_rpe_via_a2a(self, a2a: A2AHandler) -> None:
        result = await a2a.handle(
            "compute_rpe",
            {"signal_value": 0.9, "expected_value": 0.4},
        )
        assert result["rpe"] == pytest.approx(0.5)
        assert result["valence"] == "positive"

    async def test_drive_state_round_trip_via_a2a(self, a2a: A2AHandler) -> None:
        await a2a.handle("update_drive", {"drive_type": "urgency", "delta": 0.6})
        state = await a2a.handle("get_drive_state", {})
        assert state["urgency"] == pytest.approx(0.6)

    async def test_mcp_combine_signals(self, mcp: MCPTools) -> None:
        result = await mcp.handle(
            "affective.combine_signals",
            {"signals": [0.3, 0.7], "weights": [1.0, 1.0]},
        )
        assert result["combined_score"] == pytest.approx(0.5)
