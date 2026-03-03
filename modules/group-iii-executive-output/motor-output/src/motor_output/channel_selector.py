"""channel_selector.py — PMd-analogue channel selection pre-action signal.

Supplementary Motor Area (SMA/pre-SMA) analogue: context-dependent selection
of the motor channel (effector pathway) before the primary M1 dispatch.

The selector inspects ActionSpec params and type to determine the best channel,
matching the SMA's role in selecting between competing movement programmes based
on internal context (not sensory trigger).
"""
from __future__ import annotations

import structlog

from motor_output.models import ActionSpec, ChannelType

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Route hints: if these param keys are present, prefer the indicated channel
_PARAM_HINTS: list[tuple[str, ChannelType]] = [
    ("path", ChannelType.FILE),
    ("file_path", ChannelType.FILE),
    ("output_path", ChannelType.FILE),
    ("a2a_url", ChannelType.A2A),
    ("task_type", ChannelType.A2A),
    ("url", ChannelType.HTTP),
    ("endpoint", ChannelType.HTTP),
]

# Route hints based on action type prefixes
_TYPE_HINTS: list[tuple[str, ChannelType]] = [
    ("render", ChannelType.RENDER),
    ("generate", ChannelType.RENDER),
    ("synthesise", ChannelType.RENDER),
    ("synthesize", ChannelType.RENDER),
    ("write_file", ChannelType.FILE),
    ("save_file", ChannelType.FILE),
    ("delegate", ChannelType.A2A),
    ("send_task", ChannelType.A2A),
    ("http_", ChannelType.HTTP),
    ("post_", ChannelType.HTTP),
    ("get_", ChannelType.HTTP),
]


def select_channel(action_spec: ActionSpec) -> ChannelType:
    """Determine the dispatch channel for an ActionSpec.

    Priority:
      1. Explicit channel field on ActionSpec (trust the orchestrator)
      2. Param-based hints (file path → FILE, a2a_url → A2A, url → HTTP)
      3. Type-based hints (render/* → RENDER, write_file → FILE, etc.)
      4. Default: HTTP
    """
    # 1. Explicit channel already set — honour it
    if action_spec.channel is not None:
        logger.debug(
            "channel_selector.explicit",
            channel=action_spec.channel,
            action_id=action_spec.action_id,
        )
        return action_spec.channel

    params_lower = {k.lower(): v for k, v in action_spec.params.items()}
    action_type = action_spec.type.lower()

    # 2. Param-based hints
    for hint_key, channel in _PARAM_HINTS:
        if hint_key in params_lower:
            logger.debug(
                "channel_selector.param_hint",
                hint=hint_key,
                channel=channel,
                action_id=action_spec.action_id,
            )
            return channel

    # 3. Type-based hints
    for type_prefix, channel in _TYPE_HINTS:
        if action_type.startswith(type_prefix) or action_type == type_prefix.rstrip("_"):
            logger.debug(
                "channel_selector.type_hint",
                prefix=type_prefix,
                channel=channel,
                action_id=action_spec.action_id,
            )
            return channel

    # 4. Default
    logger.debug(
        "channel_selector.default",
        action_type=action_spec.type,
        channel=ChannelType.HTTP,
        action_id=action_spec.action_id,
    )
    return ChannelType.HTTP
