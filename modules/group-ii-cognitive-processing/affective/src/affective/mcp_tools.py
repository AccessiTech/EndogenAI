"""MCP tool definitions for the Affective / Motivational Layer.

Exposes reward signal generation, drive state queries, urgency scoring,
and emotional weighting operations as MCP-compatible tool handlers.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from affective.drive import DriveStateMachine, combine_signals
from affective.models import DriveType, RewardSignal, SignalType, TriggerType
from affective.rpe import compute_rpe
from affective.store import AffectiveStore
from affective.weighting import WeightingDispatcher

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for affective / motivational layer operations."""

    def __init__(
        self,
        store: AffectiveStore,
        drive_machine: DriveStateMachine,
        dispatcher: WeightingDispatcher,
    ) -> None:
        self._store = store
        self._drive = drive_machine
        self._dispatcher = dispatcher

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name.

        Supported tools:
        - affective.emit_reward_signal
        - affective.compute_rpe
        - affective.get_drive_state
        - affective.update_drive
        - affective.combine_signals
        """
        match tool_name:
            case "affective.emit_reward_signal":
                return await self._emit_reward_signal(params)

            case "affective.compute_rpe":
                result = compute_rpe(
                    signal_value=float(params["signal_value"]),
                    expected_value=float(params["expected_value"]),
                )
                return result.model_dump()

            case "affective.get_drive_state":
                return self._drive.state.model_dump()

            case "affective.update_drive":
                updated = self._drive.update(
                    drive_type=DriveType(params["drive_type"]),
                    delta=float(params["delta"]),
                )
                return updated.model_dump()

            case "affective.combine_signals":
                score = combine_signals(
                    signals=[float(s) for s in params["signals"]],
                    weights=[float(w) for w in params["weights"]],
                )
                return {"combined_score": score}

            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")

    async def _emit_reward_signal(self, params: dict[str, Any]) -> dict[str, Any]:
        signal = RewardSignal(
            id=params.get("id", str(uuid.uuid4())),
            timestamp=params.get("timestamp", datetime.now(UTC).isoformat()),
            sourceModule=params.get("source_module", "affective"),
            targetModule=params.get("target_module"),
            value=float(params["value"]),
            type=SignalType(params["type"]),
            trigger=TriggerType(params["trigger"]) if params.get("trigger") else None,
            associatedMemoryItemId=params.get("associated_memory_item_id"),
            associatedSignalId=params.get("associated_signal_id"),
            associatedTaskId=params.get("associated_task_id"),
            sessionId=params.get("session_id"),
            metadata={k: str(v) for k, v in params.get("metadata", {}).items()},
        )
        await self._store.store_reward_signal(signal)
        boost_result = await self._dispatcher.dispatch_boost(signal)
        return {
            "signal_id": signal.id,
            "stored": True,
            "boost": boost_result,
        }
