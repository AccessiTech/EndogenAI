"""Pydantic models for the perception module."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared type aliases
# ---------------------------------------------------------------------------

Modality = Literal["text", "image", "audio", "sensor", "api-event", "internal", "control"]

Layer = Literal[
    "sensory-input",
    "attention-filtering",
    "perception",
    "memory",
    "affective",
    "decision-making",
    "executive",
    "agent-execution",
    "motor-output",
    "learning-adaptation",
    "metacognition",
    "application",
    "infrastructure",
]


# ---------------------------------------------------------------------------
# Signal (inbound)
# ---------------------------------------------------------------------------


class SignalSource(BaseModel):
    moduleId: str
    layer: Layer
    instanceId: str | None = None


class TraceContext(BaseModel):
    traceparent: str
    tracestate: str | None = None


class Signal(BaseModel):
    """Inbound Signal envelope from attention-filtering / sensory-input."""

    id: str
    type: str
    modality: Modality
    source: SignalSource
    timestamp: str
    ingestedAt: str | None = None
    payload: Any = None
    encoding: str | None = None
    traceContext: TraceContext | None = None
    sessionId: str | None = None
    correlationId: str | None = None
    parentSignalId: str | None = None
    priority: int = Field(default=5, ge=0, le=10)
    ttl: int | None = None
    metadata: dict[str, str] | None = None


# ---------------------------------------------------------------------------
# Perception result
# ---------------------------------------------------------------------------


class TextFeatures(BaseModel):
    """Features extracted from a text signal."""

    entities: list[str] = Field(default_factory=list)
    intent: str | None = None
    key_phrases: list[str] = Field(default_factory=list)


class PerceptionResult(BaseModel):
    """Unified perceptual representation produced by the pipeline."""

    signal_id: str
    modality: Modality
    pattern: str | None = None
    text_features: TextFeatures | None = None
    passthrough_metadata: dict[str, Any] | None = None
    fused: bool = False
    embedding_id: str | None = None
    timestamp: str


# ---------------------------------------------------------------------------
# Request / response
# ---------------------------------------------------------------------------


class PerceptionRequest(BaseModel):
    """Payload for POST /perceive."""

    signal: Signal


class PerceptionResponse(BaseModel):
    """Response from POST /perceive."""

    result: PerceptionResult
    processed: bool = True


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
