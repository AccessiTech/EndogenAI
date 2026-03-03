"""dispatcher.py — Motor-cortex-modelled action dispatch router.

Primary Somatosensory/Motor Cortex analogue: receives ActionSpec from executive
or agent-runtime, selects the appropriate channel, applies error policy, emits
corollary discharge feedback, and returns MotorFeedback.

Supports single-action dispatch and batch dispatch (asyncio.gather).
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog

from motor_output.channel_selector import select_channel
from motor_output.channels import A2AChannel, FileChannel, HTTPChannel, RenderChannel
from motor_output.error_policy import ErrorPolicy  # noqa: TC001
from motor_output.feedback import FeedbackEmitter  # noqa: TC001
from motor_output.models import (
    ActionSpec,
    ChannelType,
    DispatchRecord,
    DispatchStatus,
    MotorFeedback,
)

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class Dispatcher:
    """Routes ActionSpec to the correct channel with error policy and feedback."""

    def __init__(
        self,
        error_policy: ErrorPolicy,
        feedback_emitter: FeedbackEmitter,
        *,
        allowed_file_paths: list[str] | None = None,
        render_model: str = "ollama/llama3",
        corollary_discharge_enabled: bool = True,
    ) -> None:
        self._error_policy = error_policy
        self._feedback = feedback_emitter
        self._corollary_discharge_enabled = corollary_discharge_enabled
        self._records: dict[str, DispatchRecord] = {}

        # Initialise channel handlers
        self._channels: dict[ChannelType, Any] = {
            ChannelType.HTTP: HTTPChannel(),
            ChannelType.A2A: A2AChannel(),
            ChannelType.FILE: FileChannel(allowed_base_paths=allowed_file_paths or []),
            ChannelType.RENDER: RenderChannel(model=render_model),
        }

    # ── Public API ────────────────────────────────────────────────────────────

    async def dispatch(self, action_spec: ActionSpec) -> MotorFeedback:
        """Dispatch a single ActionSpec and return MotorFeedback."""
        dispatched_at = datetime.now(UTC)

        logger.info(
            "dispatch.begin",
            action_id=action_spec.action_id,
            goal_id=action_spec.goal_id,
            type=action_spec.type,
        )

        # 1. SMA pre-action corollary discharge signal
        if self._corollary_discharge_enabled:
            await self._feedback.emit_preaction_signal(action_spec)

        # 2. Select channel
        channel_type = select_channel(action_spec)
        channel_handler = self._channels[channel_type]

        # 3. Build dispatch function for error policy
        action_spec_with_channel = action_spec.model_copy(
            update={"channel": channel_type}
        )

        async def _dispatch_fn() -> dict[str, Any]:
            return await channel_handler.dispatch(action_spec_with_channel.params)  # type: ignore[no-any-return]

        # 4. Execute via error policy (handles retries, circuit breaking, escalation)
        dispatch_result = await self._error_policy.execute(
            channel=channel_type,
            dispatch_fn=_dispatch_fn,
            action_id=action_spec.action_id,
            goal_id=action_spec.goal_id or "",
        )

        # 5. Build MotorFeedback
        feedback_obj = self._feedback.build_feedback(
            action_spec=action_spec_with_channel,
            dispatch_result=dispatch_result,
            dispatched_at=dispatched_at,
        )

        # 6. Record dispatch
        status = (
            DispatchStatus.SUCCESS
            if dispatch_result.get("success")
            else DispatchStatus.FAILED
        )
        if dispatch_result.get("escalated"):
            status = DispatchStatus.ESCALATED

        record = DispatchRecord(
            action_id=action_spec.action_id,
            goal_id=action_spec.goal_id or "",
            channel=channel_type,
            status=status,
            feedback=feedback_obj,
        )
        self._records[action_spec.action_id] = record

        # 7. Emit post-dispatch feedback to executive-agent (non-fatal)
        await self._feedback.emit(feedback_obj)

        logger.info(
            "dispatch.complete",
            action_id=action_spec.action_id,
            channel=channel_type.value,
            success=feedback_obj.success,
            deviation_score=feedback_obj.deviation_score,
        )
        return feedback_obj

    async def dispatch_batch(
        self, action_specs: list[ActionSpec]
    ) -> list[MotorFeedback]:
        """Dispatch multiple ActionSpecs concurrently."""
        logger.info("dispatch_batch.begin", count=len(action_specs))
        results = await asyncio.gather(
            *[self.dispatch(spec) for spec in action_specs],
            return_exceptions=True,
        )
        feedbacks: list[MotorFeedback] = []
        for spec, result in zip(action_specs, results, strict=True):
            if isinstance(result, BaseException):
                logger.error(
                    "dispatch_batch.item_failed",
                    action_id=spec.action_id,
                    error=str(result),
                )
                # Return a failed MotorFeedback for this item
                feedbacks.append(
                    MotorFeedback(
                        action_id=spec.action_id,
                        goal_id=spec.goal_id or "",
                        channel=spec.channel or ChannelType.HTTP,
                        actual_outcome={},
                        deviation_score=1.0,
                        success=False,
                        escalate=True,
                        reward_signal={"value": 0.0, "source": "motor_output"},
                        dispatched_at=datetime.now(UTC),
                        completed_at=datetime.now(UTC),
                        error=str(result),
                    )
                )
            else:
                feedbacks.append(result)
        return feedbacks

    def get_record(self, action_id: str) -> DispatchRecord | None:
        """Retrieve a DispatchRecord by action_id."""
        return self._records.get(action_id)

    def abort_dispatch(self, action_id: str) -> bool:
        """Mark a pending dispatch as ABORTED.

        Returns True if the record existed and was updated, False otherwise.
        For in-flight dispatches the abort is best-effort.
        """
        record = self._records.get(action_id)
        if record is None:
            return False
        if record.status in {DispatchStatus.PENDING, DispatchStatus.RETRYING}:
            record.status = DispatchStatus.ABORTED
            return True
        return False

    def list_channels(self) -> list[dict[str, str]]:
        """List available dispatch channels."""
        return [
            {"channel": ct.value, "handler": type(self._channels[ct]).__name__}
            for ct in ChannelType
        ]
