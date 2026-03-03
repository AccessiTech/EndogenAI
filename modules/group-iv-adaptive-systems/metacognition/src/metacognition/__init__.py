"""metacognition — Metacognition & Monitoring Layer (§7.2).

ACC-analogue error detection + PFC-BA10 confidence estimation.
Monitors Phase 6 outputs (executive-agent + motor-output).
"""

from metacognition.evaluation.evaluator import EvaluateOutputPayload, MetacognitionEvaluator
from metacognition.store.monitoring_store import MonitoringStore

__all__ = [
    "EvaluateOutputPayload",
    "MetacognitionEvaluator",
    "MonitoringStore",
]
