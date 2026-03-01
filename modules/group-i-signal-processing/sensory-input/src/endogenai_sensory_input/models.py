"""
Data models for the Sensory / Input Layer.

All models mirror the constraints defined in shared/types/signal.schema.json.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Modality(StrEnum):
    """Primary sensory or data modality of a signal."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    SENSOR = "sensor"
    API_EVENT = "api-event"
    INTERNAL = "internal"
    CONTROL = "control"


class SignalSource(BaseModel):
    """Originating module reference, matching signal.schema.json#/properties/source."""

    module_id: str = Field(alias="moduleId")
    layer: str
    instance_id: str | None = Field(default=None, alias="instanceId")

    model_config = {"populate_by_name": True}


class TraceContext(BaseModel):
    """W3C Trace Context, matching signal.schema.json#/properties/traceContext."""

    traceparent: str
    tracestate: str | None = None


class Signal(BaseModel):
    """
    Canonical signal envelope.

    Conforms to shared/types/signal.schema.json.  Every signal created by the
    Sensory / Input Layer must validate against this model before being
    forwarded upstream.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    modality: Modality
    source: SignalSource
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    ingested_at: datetime | None = Field(
        default_factory=lambda: datetime.now(tz=UTC), alias="ingestedAt"
    )
    payload: Any
    encoding: str | None = None
    trace_context: TraceContext | None = Field(default=None, alias="traceContext")
    session_id: str | None = Field(default=None, alias="sessionId")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    parent_signal_id: str | None = Field(default=None, alias="parentSignalId")
    priority: int = Field(default=5, ge=0, le=10)
    ttl: int | None = Field(default=None, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class RawInput(BaseModel):
    """
    Raw input accepted by the SignalIngestor before normalisation.

    Callers provide the raw payload and modality; the ingestor adds all
    envelope fields (id, timestamp, source, etc.).
    """

    modality: Modality
    payload: Any
    encoding: str | None = None
    session_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=0, le=10)
