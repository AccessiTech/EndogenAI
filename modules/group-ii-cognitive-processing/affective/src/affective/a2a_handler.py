"""A2A task handler for the Affective / Motivational Layer.

Handles incoming A2A task delegations:
- emit_reward_signal: generate and store a reward signal
- get_drive_state: return current drive variable snapshot
- update_drive: increment/decrement a drive variable
- dispatch_boost: send importance boost to working memory
- compute_rpe: compute RPE between observed and expected values
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from affective.drive import DriveStateMachine
from affective.models import DriveType, RewardSignal, SignalType, TriggerType
from affective.rpe import compute_rpe
from affective.store import AffectiveStore
from affective.weighting import WeightingDispatcher

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AHandler:
    """Handles incoming A2A task delegations for affective processing."""

    def __init__(
        self,
        store: AffectiveStore,
        drive_machine: DriveStateMachine,
        dispatcher: WeightingDispatcher,
    ) -> None:
        self._store = store
        self._drive = drive_machine
        self._dispatcher = dispatcher

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an A2A task by type."""
        match task_type:
            case "emit_reward_signal":
                return await self._emit_reward_signal(payload)

            case "get_drive_state":
                return self._drive.state.model_dump()

            case "update_drive":
                updated = self._drive.update(
                    drive_type=DriveType(payload["drive_type"]),
                    delta=float(payload["delta"]),
                )
                return updated.model_dump()

            case "dispatch_boost":
                signal = RewardSignal.model_validate(payload["signal"])
                result = await self._dispatcher.dispatch_boost(signal)
                return result

            case "compute_rpe":
                rpe_result = compute_rpe(
                    signal_value=float(payload["signal_value"]),
                    expected_value=float(payload["expected_value"]),
                )
                return rpe_result.model_dump()

            case _:
                raise ValueError(f"Unknown A2A task type: {task_type!r}")

    async def _emit_reward_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        signal = RewardSignal(
            id=payload.get("id", str(uuid.uuid4())),
            timestamp=payload.get("timestamp", datetime.now(UTC).isoformat()),
            sourceModule=payload.get("source_module", "affective"),
            targetModule=payload.get("target_module"),
            value=float(payload["value"]),
            type=SignalType(payload["type"]),
            trigger=TriggerType(payload["trigger"]) if payload.get("trigger") else None,
            associatedMemoryItemId=payload.get("associated_memory_item_id"),
            associatedSignalId=payload.get("associated_signal_id"),
            associatedTaskId=payload.get("associated_task_id"),
            sessionId=payload.get("session_id"),
            metadata={k: str(v) for k, v in payload.get("metadata", {}).items()},
        )
        stored_id = await self._store.store_reward_signal(signal)
        boost_result = await self._dispatcher.dispatch_boost(signal)
        return {
            "signal_id": stored_id,
            "type": str(signal.type),
            "value": signal.value,
            "boost": boost_result,
        }
