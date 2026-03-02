"""Emotional weighting and importanceScore boost dispatch.

Dispatches prioritisation cues to the working-memory module via A2A so that
high-valence affective events boost the importanceScore of co-occurring memory
items in brain.short-term-memory and brain.long-term-memory.

Analogous to the BLA → hippocampus emotional tagging pathway:
  Strong emotional events → stronger encoding (higher importanceScore).
"""

from __future__ import annotations

import structlog
from endogenai_a2a import A2AClient

from affective.models import AffectiveTag, RewardSignal

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_WORKING_MEMORY_A2A_URL = "http://localhost:8201"
_BOOST_TASK_TYPE = "apply_affective_boost"

# Minimum absolute signal value to trigger a boost dispatch
_BOOST_THRESHOLD = 0.1


class WeightingDispatcher:
    """Dispatches importanceScore boost cues to working memory via A2A.

    In production this sends HTTP POST to the working-memory A2A endpoint.
    An ``A2AClient`` is created automatically from ``a2a_url`` when no client is
    injected; pass ``a2a_client`` explicitly in tests to inject a mock and avoid
    network I/O.
    """

    def __init__(
        self,
        a2a_url: str = _WORKING_MEMORY_A2A_URL,
        a2a_client: A2AClient | None = None,
    ) -> None:
        self._a2a_url = a2a_url
        # Always have a real client in production; tests may inject a mock.
        self._a2a_client: A2AClient = (
            a2a_client if a2a_client is not None else A2AClient(url=a2a_url)
        )

    def _compute_importance_boost(self, signal: RewardSignal) -> float:
        """Map reward signal value to an importanceScore delta.

        Positive RPE → boost; negative RPE → decay (but not below 0).
        The boost is clamped so it never exceeds 1.0 when applied.
        """
        return max(-0.5, min(0.5, signal.value))

    def tag_from_signal(self, signal: RewardSignal) -> AffectiveTag | None:
        """Build an AffectiveTag from a RewardSignal, or None if no memory link."""
        if signal.associated_memory_item_id is None:
            return None
        return AffectiveTag(
            memory_item_id=signal.associated_memory_item_id,
            valence=signal.value,
            arousal=abs(signal.value),
            source_signal_id=signal.id,
        )

    async def dispatch_boost(self, signal: RewardSignal) -> dict[str, object]:
        """Send an A2A apply_affective_boost task to working memory.

        Only dispatches if:
        1. signal has an associatedMemoryItemId
        2. abs(signal.value) >= _BOOST_THRESHOLD

        Returns a dict with dispatch status details.
        """
        if signal.associated_memory_item_id is None:
            logger.debug("weighting.skip_no_memory_link", signal_id=signal.id)
            return {"status": "skipped", "reason": "no_memory_link"}

        boost = self._compute_importance_boost(signal)
        if abs(boost) < _BOOST_THRESHOLD:
            logger.debug("weighting.skip_below_threshold", signal_id=signal.id, boost=boost)
            return {"status": "skipped", "reason": "below_threshold"}

        try:
            await self._a2a_client.send_task(
                _BOOST_TASK_TYPE,
                {
                    "item_id": signal.associated_memory_item_id,
                    "reward_value": boost,
                    "signal_id": signal.id,
                },
            )
            logger.info(
                "weighting.boost_dispatched",
                signal_id=signal.id,
                memory_item_id=signal.associated_memory_item_id,
                boost=boost,
            )
            return {"status": "dispatched", "boost": boost}
        except Exception as exc:  # noqa: BLE001
            logger.warning("weighting.dispatch_error", error=str(exc), signal_id=signal.id)
            return {"status": "error", "error": str(exc)}
