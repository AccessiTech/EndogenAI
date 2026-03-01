"""perception — EndogenAI feature extraction and perceptual representation module."""

from perception.models import (
    PerceptionRequest,
    PerceptionResult,
    Signal,
)
from perception.processor import PerceptionPipeline

__all__ = [
    "PerceptionPipeline",
    "PerceptionRequest",
    "PerceptionResult",
    "Signal",
]

__version__ = "0.1.0"
