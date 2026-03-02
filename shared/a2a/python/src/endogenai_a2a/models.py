"""Pydantic models for the A2A JSON-RPC 2.0 protocol.

Derived from:
- shared/schemas/a2a-task.schema.json
- shared/schemas/a2a-message.schema.json
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class A2AMessage(BaseModel):
    """A message exchanged as part of an A2A task."""

    model_config = ConfigDict(populate_by_name=True)

    role: str
    parts: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class A2ATaskStatus(BaseModel):
    """Lifecycle state of an A2A task."""

    model_config = ConfigDict(populate_by_name=True)

    state: str
    message: str | None = None
    timestamp: str | None = None


class A2ATask(BaseModel):
    """A discrete unit of work delegated between agents (mirrors a2a-task.schema.json)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    status: A2ATaskStatus
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    session_id: str | None = Field(default=None, alias="sessionId")
    metadata: dict[str, str] = Field(default_factory=dict)
    history: list[A2AMessage] = Field(default_factory=list)


class A2ARequest(BaseModel):
    """JSON-RPC 2.0 request envelope."""

    model_config = ConfigDict(populate_by_name=True)

    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    id: str


class A2AResponse(BaseModel):
    """JSON-RPC 2.0 response envelope."""

    model_config = ConfigDict(populate_by_name=True)

    jsonrpc: str = "2.0"
    id: str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
