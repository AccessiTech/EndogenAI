"""
EndogenAI Perception Layer.

Provides feature extraction, pattern recognition, language understanding, scene
parsing, and multimodal fusion.  Extracted perceptual representations are
embedded into the brain.perception vector collection via the shared
endogenai_vector_store adapter.
"""

from endogenai_perception.models import PerceptionResult, PerceptualFeatures
from endogenai_perception.pipeline import PerceptionPipeline

__all__ = ["PerceptionPipeline", "PerceptualFeatures", "PerceptionResult"]
