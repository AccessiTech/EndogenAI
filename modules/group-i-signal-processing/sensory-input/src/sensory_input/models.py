"""Pydantic models for the sensory-input module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
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
# Signal sub-models
# ---------------------------------------------------------------------------


class SignalSource(BaseModel):
    """Originating module reference."""

    moduleId: str
    layer: Layer
    instanceId: str | None = None


class TraceContext(BaseModel):
    """W3C Trace Context."""

    traceparent: str
    tracestate: str | None = None


# ---------------------------------------------------------------------------
# Signal envelope
# ---------------------------------------------------------------------------


class Signal(BaseModel):
    """Canonical signal envelope (conforms to signal.schema.json)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    modality: Modality
    source: SignalSource
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
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
# Ingest request / response
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    """Payload for the POST /ingest endpoint."""

    modality: Modality
    type: str
    payload: Any = None
    source_module_id: str = "external"
    encoding: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    priority: int = Field(default=5, ge=0, le=10)
    metadata: dict[str, str] | None = None
    trace_context: TraceContext | None = None


class IngestResponse(BaseModel):
    """Response from POST /ingest."""

    signal: Signal
    accepted: bool = True


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str
    detail: str | None = None
