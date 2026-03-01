"""
Signal ingestion for the Sensory / Input Layer.

SignalIngestor accepts raw inputs in any supported modality, normalises them,
stamps them with ISO 8601 timestamps, and wraps them in the canonical Signal
envelope (shared/types/signal.schema.json) for dispatch to the Attention &
Filtering Layer.

Usage
-----
>>> ingestor = SignalIngestor(module_id="sensory-input", instance_id="node-0")
>>> signal = ingestor.ingest(RawInput(modality=Modality.TEXT, payload="Hello"))
>>> print(signal.id, signal.timestamp)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog

from endogenai_sensory_input.models import (
    Modality,
    RawInput,
    Signal,
    SignalSource,
)
from endogenai_sensory_input.normalize import normalize_payload

log = structlog.get_logger(__name__)

# Mapping from modality to canonical signal type prefix
_MODALITY_TYPE_PREFIX: dict[Modality, str] = {
    Modality.TEXT: "text.input",
    Modality.IMAGE: "image.frame",
    Modality.AUDIO: "audio.chunk",
    Modality.SENSOR: "sensor.reading",
    Modality.API_EVENT: "api.event",
    Modality.INTERNAL: "internal.signal",
    Modality.CONTROL: "control.directive",
}


class SignalIngestor:
    """
    Multi-modal signal ingestor.

    Accepts raw input from any supported modality and produces a normalised
    Signal envelope ready for downstream processing.

    Parameters
    ----------
    module_id:
        Canonical module identifier (default: ``"sensory-input"``).
    instance_id:
        Optional instance tag for multi-instance deployments.
    """

    def __init__(
        self,
        module_id: str = "sensory-input",
        instance_id: str | None = None,
    ) -> None:
        self._module_id = module_id
        self._instance_id = instance_id
        self._logger = log.bind(module_id=module_id, instance_id=instance_id)

    def ingest(self, raw: RawInput) -> Signal:
        """
        Ingest a raw input and produce a normalised Signal envelope.

        Steps
        -----
        1. Generate a UUID v4 signal identifier.
        2. Record the ingestion timestamp.
        3. Normalise the payload (encoding conversion, type coercion).
        4. Wrap everything into a Signal model.
        5. Log and return.

        Parameters
        ----------
        raw:
            The raw input to ingest.

        Returns
        -------
        Signal
            The normalised signal envelope.
        """
        now = datetime.now(tz=UTC)
        signal_id = str(uuid.uuid4())

        normalised_payload = normalize_payload(raw.modality, raw.payload, raw.encoding)

        signal = Signal(
            id=signal_id,
            type=_MODALITY_TYPE_PREFIX.get(raw.modality, f"{raw.modality.value}.input"),
            modality=raw.modality,
            source=SignalSource(
                module_id=self._module_id,
                layer="sensory-input",
                instance_id=self._instance_id,
            ),
            timestamp=now,
            ingested_at=now,
            payload=normalised_payload,
            encoding=raw.encoding,
            session_id=raw.session_id,
            priority=raw.priority,
            metadata=raw.metadata,
        )

        self._logger.info(
            "signal_ingested",
            signal_id=signal_id,
            modality=raw.modality.value,
            signal_type=signal.type,
        )
        return signal
