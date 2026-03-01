"""Pydantic models for the attention-filtering module."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared type aliases (mirror signal schema)
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
# Signal (inbound) — mirrors signal.schema.json
# ---------------------------------------------------------------------------


class SignalSource(BaseModel):
    moduleId: str
    layer: Layer
    instanceId: str | None = None


class TraceContext(BaseModel):
    traceparent: str
    tracestate: str | None = None


class Signal(BaseModel):
    """Inbound Signal envelope from sensory-input."""

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
# Filtering results
# ---------------------------------------------------------------------------


class ScoredSignal(BaseModel):
    """Signal annotated with a salience score."""

    signal: Signal
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    routed_to: str | None = None


class FilterRequest(BaseModel):
    """Request payload for POST /filter."""

    signal: Signal


class FilterResponse(BaseModel):
    """Response from POST /filter."""

    scored: ScoredSignal
    dropped: bool


# ---------------------------------------------------------------------------
# Attention directive
# ---------------------------------------------------------------------------


class AttentionDirective(BaseModel):
    """Top-down modulation payload — updates threshold and routing at runtime."""

    threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    modality_weights: dict[str, float] | None = None
    type_weights: dict[str, float] | None = None
    routing: dict[str, str] | None = None


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class RouteEntry(BaseModel):
    """Routing table entry: maps a key to a downstream URL."""

    key: str
    url: str
