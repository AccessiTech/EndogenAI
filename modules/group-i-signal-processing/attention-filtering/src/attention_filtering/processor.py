"""Core processing logic for the attention-filtering module.

Design
------
* Salience score formula::

      score = 0.4 * (priority / 10.0)
            + 0.3 * modality_weight[modality]
            + 0.3 * type_weight[type_prefix]

* Signals scoring below `threshold` are dropped.
* Accepted signals are forwarded to the URL mapped by their modality (or type
  prefix) in the routing table.  Routing is **fire-and-forget** via httpx; the
  HTTP response is not awaited in the hot path — it runs as a background task.
* `attention.directive` signals (type == "attention.directive") update the
  module's internal state: threshold, weights, routing table.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import jsonschema
import structlog

from attention_filtering import config
from attention_filtering.models import (
    AttentionDirective,
    FilterResponse,
    Modality,
    ScoredSignal,
    Signal,
)

log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_SCHEMA_DIR = Path(__file__).parent / "schemas"


# ---------------------------------------------------------------------------
# Schema loading & validation
# ---------------------------------------------------------------------------


def _load_schema(filename: str) -> dict[str, Any]:
    with (_SCHEMA_DIR / filename).open() as fh:
        return cast("dict[str, Any]", json.load(fh))


_SIGNAL_SCHEMA: dict[str, Any] = _load_schema("signal.schema.json")
_MCP_SCHEMA: dict[str, Any] = _load_schema("mcp-context.schema.json")
_A2A_SCHEMA: dict[str, Any] = _load_schema("a2a-message.schema.json")


def check_payload_size(data: bytes) -> None:
    if len(data) > config.MAX_PAYLOAD_BYTES:
        raise ValueError(
            f"Payload {len(data)} bytes exceeds limit {config.MAX_PAYLOAD_BYTES} bytes"
        )


def validate_mcp(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=_MCP_SCHEMA)


def validate_a2a(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=_A2A_SCHEMA)


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

_DEFAULT_MODALITY_WEIGHTS: dict[str, float] = {
    "control": 1.0,
    "text": 0.8,
    "image": 0.7,
    "audio": 0.7,
    "api-event": 0.6,
    "sensor": 0.5,
    "internal": 0.4,
}

_DEFAULT_TYPE_WEIGHTS: dict[str, float] = {
    "attention": 1.0,   # attention.directive
    "reward": 0.9,      # reward.signal
    "decision": 0.85,   # decision.plan
    "motor": 0.8,       # motor.command
    "text": 0.7,        # text.input / text.output
    "image": 0.65,
    "audio": 0.65,
    "memory": 0.6,
    "api": 0.55,
    "sensor": 0.5,
    "internal": 0.4,
}

# Default routing: forward everything to perception on port 8102
_DEFAULT_ROUTING: dict[str, str] = {
    "text": "http://localhost:8102/ingest",
    "image": "http://localhost:8102/ingest",
    "audio": "http://localhost:8102/ingest",
    "sensor": "http://localhost:8102/ingest",
    "api-event": "http://localhost:8102/ingest",
    "internal": "http://localhost:8102/ingest",
}


# ---------------------------------------------------------------------------
# AttentionFilter — stateful processor
# ---------------------------------------------------------------------------


class AttentionFilter:
    """Stateful attention-filtering processor.

    A single instance is held by the FastAPI application lifespan.  Its state
    (threshold, weights, routing table) can be updated at runtime via
    ``attention.directive`` signals.
    """

    def __init__(self, threshold: float | None = None) -> None:
        self.threshold: float = threshold if threshold is not None else config.DEFAULT_THRESHOLD
        self.modality_weights: dict[str, float] = dict(_DEFAULT_MODALITY_WEIGHTS)
        self.type_weights: dict[str, float] = dict(_DEFAULT_TYPE_WEIGHTS)
        self.routing: dict[str, str] = dict(_DEFAULT_ROUTING)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(self, signal: Signal) -> float:
        """Return a salience score in [0.0, 1.0]."""
        priority_score = signal.priority / 10.0
        modality_score = self.modality_weights.get(signal.modality, 0.5)
        type_prefix = signal.type.split(".")[0] if "." in signal.type else signal.type
        type_score = self.type_weights.get(type_prefix, 0.5)
        return round(
            0.4 * priority_score + 0.3 * modality_score + 0.3 * type_score,
            6,
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def route_url(self, signal: Signal) -> str | None:
        """Return the downstream URL for *signal*, or None if not mapped."""
        # First try full modality match, then type prefix
        url = self.routing.get(signal.modality)
        if url is None:
            type_prefix = signal.type.split(".")[0]
            url = self.routing.get(type_prefix)
        return url

    # ------------------------------------------------------------------
    # Filter entry point
    # ------------------------------------------------------------------

    def filter(self, signal: Signal) -> FilterResponse:
        """Score, gate, and route a single signal."""
        # Handle attention directives before scoring
        if signal.type == "attention.directive":
            self._apply_directive(signal)

        score = self.score(signal)
        passed = score >= self.threshold
        routed_to: str | None = None

        if passed:
            routed_to = self.route_url(signal)

        scored = ScoredSignal(signal=signal, score=score, passed=passed, routed_to=routed_to)
        result = FilterResponse(scored=scored, dropped=not passed)

        log.info(
            "signal.filtered",
            signal_id=signal.id,
            modality=signal.modality,
            type=signal.type,
            score=score,
            passed=passed,
            routed_to=routed_to,
        )
        return result

    # ------------------------------------------------------------------
    # Top-down modulation
    # ------------------------------------------------------------------

    def _apply_directive(self, signal: Signal) -> None:
        """Apply an attention.directive signal to update module state."""
        payload = signal.payload
        if not isinstance(payload, dict):
            log.warning("attention.directive payload is not a dict; ignoring", signal_id=signal.id)
            return

        try:
            directive = AttentionDirective.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            log.warning("attention.directive validation failed", error=str(exc))
            return

        if directive.threshold is not None:
            self.threshold = directive.threshold
            log.info("attention.threshold_updated", threshold=self.threshold)

        if directive.modality_weights:
            self.modality_weights.update(directive.modality_weights)
            log.info("attention.modality_weights_updated", weights=directive.modality_weights)

        if directive.type_weights:
            self.type_weights.update(directive.type_weights)
            log.info("attention.type_weights_updated", weights=directive.type_weights)

        if directive.routing:
            self.routing.update(directive.routing)
            log.info("attention.routing_updated", routing=directive.routing)

    # ------------------------------------------------------------------
    # MCP / A2A adapters
    # ------------------------------------------------------------------

    def process_mcp(self, mcp: dict[str, Any]) -> FilterResponse:
        """Extract a Signal from an MCPContext dict and filter it."""
        payload_data = mcp.get("payload")
        if not isinstance(payload_data, dict):
            # Wrap raw payload in a minimal Signal structure
            content_type: str = str(mcp.get("contentType", "signal/text.input"))
            modality_str = content_type.split("/")[0] if "/" in content_type else "text"
            modality_map: dict[str, str] = {
                "signal": "text", "text": "text", "image": "image",
                "audio": "audio", "sensor": "sensor",
            }
            resolved_modality = modality_map.get(modality_str, "text")
            sig_type_raw = content_type.split("/", 1)[1] if "/" in content_type else "text.input"
            source_data = cast("dict[str, Any]", mcp.get("source", {}))
            signal = Signal(
                id=str(mcp.get("id", "unknown")),
                type=sig_type_raw,
                modality=cast("Modality", resolved_modality),
                source={
                    "moduleId": source_data.get("moduleId", "mcp-sender"),
                    "layer": source_data.get("layer", "application"),
                },
                timestamp=str(mcp.get("timestamp", "")),
                payload=mcp.get("payload"),
                priority=int(mcp.get("priority", 5)),
            )
        else:
            signal = Signal.model_validate(payload_data)
        return self.filter(signal)

    def process_a2a(self, msg: dict[str, Any]) -> FilterResponse:
        """Extract a Signal from an A2AMessage dict and filter it."""
        parts: list[dict[str, Any]] = cast("list[dict[str, Any]]", msg.get("parts", []))
        payload: Any = None
        modality: Modality = "text"
        sig_type = "text.input"

        if parts:
            part = parts[0]
            if part.get("type") == "text":
                payload = part.get("text", "")
            elif part.get("type") == "data":
                payload = part.get("data")
                modality = "internal"
                sig_type = "api.event"

        signal = Signal(
            id=str(msg.get("id", "unknown")),
            type=sig_type,
            modality=modality,
            source={
                "moduleId": config.MODULE_ID,
                "layer": "sensory-input",
            },
            timestamp=str(msg.get("timestamp", "")),
            payload=payload,
            priority=5,
        )
        return self.filter(signal)

    # ------------------------------------------------------------------
    # State inspection
    # ------------------------------------------------------------------

    def state(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "modality_weights": self.modality_weights,
            "type_weights": self.type_weights,
            "routing": self.routing,
        }
