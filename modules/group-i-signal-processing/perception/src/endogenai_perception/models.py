"""
Data models for the Perception Layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PerceptualFeatures(BaseModel):
    """
    Structured perceptual features extracted from a signal.

    Carries the semantically meaningful representations produced by the
    Perception Layer before embedding into brain.perception.
    """

    signal_id: str
    modality: str
    entities: list[str] = Field(
        default_factory=list,
        description="Named entities, objects, or concepts detected in the signal.",
    )
    intent: str | None = Field(
        default=None,
        description="Inferred intent or action type (e.g. 'question', 'command', 'observation').",
    )
    summary: str | None = Field(
        default=None,
        description="Short natural-language summary of the signal content.",
    )
    language: str | None = Field(
        default=None,
        description="Detected language (BCP-47 tag, e.g. 'en', 'fr').",
    )
    scene: dict[str, Any] = Field(
        default_factory=dict,
        description="Scene or structure description for image/audio modalities.",
    )
    raw_embedding_text: str | None = Field(
        default=None,
        description="The text string passed to the embedding model for vectorisation.",
    )
    metadata: dict[str, str] = Field(default_factory=dict)


class PerceptionResult(BaseModel):
    """
    Full output of the Perception pipeline for a single signal.

    The features are persisted to brain.perception; the embedding_id references
    the vector store record.
    """

    signal_id: str
    features: PerceptualFeatures
    embedding_id: str | None = Field(
        default=None,
        description="ID of the vector record written to brain.perception.",
    )
    embedding_model: str | None = None
