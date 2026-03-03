"""mcp_server.py — MCP resources and tools for the metacognition module.

Exposes three resources:
  confidence/current    → dict[task_type, float]
  anomalies/recent      → list[MetacognitiveEvaluation]
  report/session        → MetacognitiveSessionReport

All resources are served as JSON over the FastAPI ``/mcp/resources/read``
endpoint. Tools are listed at ``/mcp/tools/list`` and called at
``/mcp/tools/call``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel

if TYPE_CHECKING:
    from metacognition.evaluation.evaluator import MetacognitionEvaluator

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Session report model
# ---------------------------------------------------------------------------


class MetacognitiveSessionReport(BaseModel):
    """Aggregate session-level metacognitive report."""

    generated_at: str = ""
    total_evaluations: int = 0
    mean_task_confidence: float = 0.0
    error_detection_count: int = 0
    correction_trigger_count: int = 0
    task_type_summary: dict[str, float] = {}

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        if not data.get("generated_at"):
            data["generated_at"] = datetime.now(UTC).isoformat()
        super().__init__(**data)


# ---------------------------------------------------------------------------
# Resource handlers
# ---------------------------------------------------------------------------


async def get_confidence_current(evaluator: MetacognitionEvaluator) -> dict[str, float]:
    """Return current task_confidence per task_type.

    MCP resource: ``resource://brain.metacognition/confidence/current``
    """
    return evaluator.get_current_confidence()


async def get_anomalies_recent(
    evaluator: MetacognitionEvaluator, n: int = 10
) -> list[dict[str, Any]]:
    """Return up to n most recent anomalous evaluations.

    MCP resource: ``resource://brain.metacognition/anomalies/recent``
    """
    anomalies = evaluator.get_recent_anomalies(n)
    return [a.model_dump() for a in anomalies]


async def get_session_report(evaluator: MetacognitionEvaluator) -> dict[str, Any]:
    """Build and return a session-level metacognitive report.

    MCP resource: ``resource://brain.metacognition/report/session``
    """
    confidence = evaluator.get_current_confidence()
    recent = evaluator.get_all_recent()

    total = len(recent)
    error_count = sum(1 for e in recent if e.error_detected)
    correction_count = sum(1 for e in recent if e.correction_triggered)
    mean_conf = sum(confidence.values()) / len(confidence) if confidence else 0.0

    report = MetacognitiveSessionReport(
        total_evaluations=total,
        mean_task_confidence=round(mean_conf, 4),
        error_detection_count=error_count,
        correction_trigger_count=correction_count,
        task_type_summary={k: round(v, 4) for k, v in confidence.items()},
    )
    return report.model_dump()


# ---------------------------------------------------------------------------
# MCP tool + resource registry
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "evaluate",
        "description": "Trigger an evaluate_output A2A task from MCP context.",
        "inputSchema": {
            "type": "object",
            "required": [
                "goal_id", "action_id", "success",
                "escalate", "deviation_score", "reward_value",
            ],
            "properties": {
                "goal_id": {"type": "string"},
                "action_id": {"type": "string"},
                "success": {"type": "boolean"},
                "escalate": {"type": "boolean"},
                "deviation_score": {"type": "number"},
                "reward_value": {"type": "number"},
                "task_type": {"type": "string", "default": "default"},
            },
        },
    },
    {
        "name": "configure-threshold",
        "description": "Update confidence_threshold at runtime.",
        "inputSchema": {
            "type": "object",
            "required": ["confidence_threshold"],
            "properties": {
                "confidence_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0}
            },
        },
    },
    {
        "name": "report",
        "description": "Return the current session-level metacognitive report.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

MCP_RESOURCES = [
    {
        "uri": "resource://brain.metacognition/confidence/current",
        "name": "confidence/current",
        "description": "Current task_confidence per task_type (dict).",
        "mimeType": "application/json",
    },
    {
        "uri": "resource://brain.metacognition/anomalies/recent",
        "name": "anomalies/recent",
        "description": "Most recent anomalous evaluation events (error_detected=True).",
        "mimeType": "application/json",
    },
    {
        "uri": "resource://brain.metacognition/report/session",
        "name": "report/session",
        "description": "Session-level aggregate metacognitive report.",
        "mimeType": "application/json",
    },
]
