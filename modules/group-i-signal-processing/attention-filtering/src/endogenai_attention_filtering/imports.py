"""
Lightweight Signal type reference for the Attention & Filtering Layer.

This module re-declares the minimal Signal fields needed by this layer.
Full schema definition lives in shared/types/signal.schema.json.
Cross-module data exchange uses the Signal envelope; source code is NOT
imported from other modules (see modules/AGENTS.md Cross-Group Dependency Rule).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    SENSOR = "sensor"
    API_EVENT = "api-event"
    INTERNAL = "internal"
    CONTROL = "control"


class SignalSource(BaseModel):
    module_id: str = Field(alias="moduleId")
    layer: str
    instance_id: str | None = Field(default=None, alias="instanceId")

    model_config = {"populate_by_name": True}


class TraceContext(BaseModel):
    traceparent: str
    tracestate: str | None = None


class Signal(BaseModel):
    """Signal envelope — conforms to shared/types/signal.schema.json."""

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
    session_id: str | None = Field(default=None, alias="sessionId")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    parent_signal_id: str | None = Field(default=None, alias="parentSignalId")
    priority: int = Field(default=5, ge=0, le=10)
    ttl: int | None = Field(default=None, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
