"""Core processing logic for the sensory-input module.

Responsibilities
----------------
* Enforce the inbound payload size limit (ENDOGEN_MAX_PAYLOAD_BYTES).
* Validate inbound JSON against the canonical MCP-Context, A2A-Message, and
  Signal JSON Schemas.
* Normalise raw data into a typed :class:`Signal` envelope with a UTC
  timestamp and module-stamped source.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import jsonschema
import structlog

from sensory_input import config
from sensory_input.models import (
    IngestRequest,
    Layer,
    Modality,
    Signal,
    SignalSource,
    TraceContext,
)

log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_SCHEMA_DIR = Path(__file__).parent / "schemas"


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


def _load_schema(filename: str) -> dict[str, Any]:
    with (_SCHEMA_DIR / filename).open() as fh:
        return cast("dict[str, Any]", json.load(fh))


_SIGNAL_SCHEMA: dict[str, Any] = _load_schema("signal.schema.json")
_MCP_SCHEMA: dict[str, Any] = _load_schema("mcp-context.schema.json")
_A2A_SCHEMA: dict[str, Any] = _load_schema("a2a-message.schema.json")


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def check_payload_size(data: bytes) -> None:
    """Raise ValueError when *data* exceeds ENDOGEN_MAX_PAYLOAD_BYTES."""
    if len(data) > config.MAX_PAYLOAD_BYTES:
        raise ValueError(
            f"Payload size {len(data)} bytes exceeds limit {config.MAX_PAYLOAD_BYTES} bytes"
        )


# ---------------------------------------------------------------------------
# Schema validators
# ---------------------------------------------------------------------------


def validate_mcp(data: dict[str, Any]) -> None:
    """Validate *data* against the MCPContext schema. Raises jsonschema.ValidationError."""
    jsonschema.validate(instance=data, schema=_MCP_SCHEMA)


def validate_a2a(data: dict[str, Any]) -> None:
    """Validate *data* against the A2AMessage schema. Raises jsonschema.ValidationError."""
    jsonschema.validate(instance=data, schema=_A2A_SCHEMA)


def validate_signal(data: dict[str, Any]) -> None:
    """Validate *data* against the Signal schema. Raises jsonschema.ValidationError."""
    jsonschema.validate(instance=data, schema=_SIGNAL_SCHEMA)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MODALITY_MAP: dict[str, Modality] = {
    "text": "text",
    "signal": "text",
    "image": "image",
    "audio": "audio",
    "sensor": "sensor",
    "api-event": "api-event",
    "api": "api-event",
    "control": "control",
    "internal": "internal",
}


def _modality_from_content_type(content_type: str) -> Modality:
    prefix = content_type.split("/")[0] if "/" in content_type else content_type
    return _MODALITY_MAP.get(prefix, "text")


def _type_from_content_type(content_type: str) -> str:
    if "/" in content_type:
        modality, sub = content_type.split("/", 1)
        if modality == "signal":
            return sub
        return f"{modality}.{sub}"
    return f"{content_type}.input"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Signal builders
# ---------------------------------------------------------------------------


def ingest_request_to_signal(request: IngestRequest) -> Signal:
    """Convert a direct IngestRequest into a normalised Signal envelope."""
    now = _now_iso()
    signal = Signal(
        id=str(uuid.uuid4()),
        type=request.type,
        modality=request.modality,
        source=SignalSource(moduleId=config.MODULE_ID, layer="sensory-input"),
        timestamp=now,
        ingestedAt=now,
        payload=request.payload,
        encoding=request.encoding,
        traceContext=request.trace_context,
        sessionId=request.session_id,
        correlationId=request.correlation_id,
        priority=request.priority,
        metadata=request.metadata,
    )
    log.info(
        "signal.ingested",
        signal_id=signal.id,
        modality=signal.modality,
        type=signal.type,
        priority=signal.priority,
    )
    return signal


def mcp_to_signal(mcp: dict[str, Any]) -> Signal:
    """Build a Signal from a validated MCPContext dict."""
    now = _now_iso()
    content_type: str = str(mcp.get("contentType", "signal/text.input"))
    modality = _modality_from_content_type(content_type)
    sig_type = _type_from_content_type(content_type)

    source_data: dict[str, Any] = cast("dict[str, Any]", mcp.get("source", {}))
    source_layer_raw: str = str(source_data.get("layer", "application"))
    # Clamp to known layers; fall back to "application" for external senders.
    known_layers: set[str] = {
        "sensory-input", "attention-filtering", "perception", "memory",
        "affective", "decision-making", "executive", "agent-execution",
        "motor-output", "learning-adaptation", "metacognition",
        "application", "infrastructure",
    }
    source_layer: Layer = cast(
        "Layer", source_layer_raw if source_layer_raw in known_layers else "application"
    )

    trace_ctx: TraceContext | None = None
    trace_data = mcp.get("traceContext")
    if trace_data and isinstance(trace_data, dict):
        trace_ctx = TraceContext(
            traceparent=str(trace_data["traceparent"]),
            tracestate=str(trace_data["tracestate"]) if trace_data.get("tracestate") else None,
        )

    signal = Signal(
        id=str(uuid.uuid4()),
        type=sig_type,
        modality=modality,
        source=SignalSource(
            moduleId=str(source_data.get("moduleId", "mcp-sender")),
            layer=source_layer,
        ),
        timestamp=str(mcp.get("timestamp", now)),
        ingestedAt=now,
        payload=mcp.get("payload"),
        traceContext=trace_ctx,
        sessionId=str(mcp["sessionId"]) if mcp.get("sessionId") else None,
        correlationId=str(mcp["correlationId"]) if mcp.get("correlationId") else None,
        priority=int(mcp.get("priority", 5)),
        metadata=cast("dict[str, str] | None", mcp.get("metadata")),
    )
    log.info(
        "mcp.ingested",
        signal_id=signal.id,
        modality=signal.modality,
        type=signal.type,
    )
    return signal


def a2a_to_signal(msg: dict[str, Any]) -> Signal:
    """Build a Signal from a validated A2AMessage dict."""
    now = _now_iso()
    parts: list[dict[str, Any]] = cast("list[dict[str, Any]]", msg.get("parts", []))

    payload: Any = None
    modality: Modality = "text"
    sig_type = "text.input"

    if parts:
        part = parts[0]
        part_type: str = str(part.get("type", "text"))
        if part_type == "text":
            payload = part.get("text", "")
            modality = "text"
            sig_type = "text.input"
        elif part_type == "data":
            payload = part.get("data")
            modality = "internal"
            sig_type = "api.event"
        elif part_type == "file":
            file_info = cast("dict[str, Any]", part.get("file", {}))
            payload = file_info.get("bytes") or file_info.get("uri", "")
            mime: str = str(file_info.get("mimeType", "application/octet-stream"))
            if mime.startswith("image/"):
                modality = "image"
                sig_type = "image.frame"
            elif mime.startswith("audio/"):
                modality = "audio"
                sig_type = "audio.chunk"
            else:
                modality = "internal"
                sig_type = "api.event"

    trace_ctx: TraceContext | None = None
    trace_data = msg.get("traceContext")
    if trace_data and isinstance(trace_data, dict):
        trace_ctx = TraceContext(
            traceparent=str(trace_data["traceparent"]),
            tracestate=str(trace_data["tracestate"]) if trace_data.get("tracestate") else None,
        )

    signal = Signal(
        id=str(uuid.uuid4()),
        type=sig_type,
        modality=modality,
        source=SignalSource(moduleId=config.MODULE_ID, layer="sensory-input"),
        timestamp=str(msg.get("timestamp", now)),
        ingestedAt=now,
        payload=payload,
        traceContext=trace_ctx,
        priority=5,
        metadata=cast("dict[str, str] | None", msg.get("metadata")),
    )
    log.info(
        "a2a.ingested",
        signal_id=signal.id,
        modality=signal.modality,
        type=signal.type,
    )
    return signal
