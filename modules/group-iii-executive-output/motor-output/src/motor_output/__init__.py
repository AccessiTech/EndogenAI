"""motor_output — Motor / Output / Effector module for EndogenAI.

Motor Cortex analogue: channel-based action dispatch with error policy
and corollary discharge feedback to executive-agent.
"""
from motor_output.dispatcher import Dispatcher
from motor_output.feedback import FeedbackEmitter
from motor_output.models import (
    ActionSpec,
    ChannelType,
    DispatchRecord,
    DispatchStatus,
    ErrorPolicyConfig,
    MotorFeedback,
)

__all__ = [
    "ActionSpec",
    "ChannelType",
    "DispatchRecord",
    "DispatchStatus",
    "Dispatcher",
    "ErrorPolicyConfig",
    "FeedbackEmitter",
    "MotorFeedback",
]
