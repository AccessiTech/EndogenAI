"""Tests for SignalIngestor."""

from __future__ import annotations

from endogenai_sensory_input.ingestion import SignalIngestor
from endogenai_sensory_input.models import Modality, RawInput


def make_ingestor() -> SignalIngestor:
    return SignalIngestor(module_id="sensory-input", instance_id="test")


class TestSignalIngestor:
    """Unit tests for SignalIngestor.ingest()."""

    def test_text_signal_has_correct_type(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="Hello world")
        signal = ingestor.ingest(raw)
        assert signal.type == "text.input"

    def test_text_payload_is_normalised(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="  hello  ")
        signal = ingestor.ingest(raw)
        assert signal.payload == "hello"

    def test_image_bytes_are_base64_encoded(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.IMAGE, payload=b"\x89PNG")
        signal = ingestor.ingest(raw)
        assert isinstance(signal.payload, str)

    def test_api_event_dict_payload_preserved(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.API_EVENT, payload={"event": "click"})
        signal = ingestor.ingest(raw)
        assert signal.payload == {"event": "click"}

    def test_sensor_scalar_wrapped_in_dict(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.SENSOR, payload=42.5)
        signal = ingestor.ingest(raw)
        assert signal.payload == {"value": 42.5}

    def test_signal_has_uuid_id(self) -> None:
        import uuid

        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="test")
        signal = ingestor.ingest(raw)
        uuid.UUID(signal.id)  # raises ValueError if not valid UUID

    def test_signal_source_fields(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="test")
        signal = ingestor.ingest(raw)
        assert signal.source.module_id == "sensory-input"
        assert signal.source.layer == "sensory-input"
        assert signal.source.instance_id == "test"

    def test_timestamp_and_ingested_at_set(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="test")
        signal = ingestor.ingest(raw)
        assert signal.timestamp is not None
        assert signal.ingested_at is not None

    def test_priority_propagated(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="urgent", priority=9)
        signal = ingestor.ingest(raw)
        assert signal.priority == 9

    def test_session_id_propagated(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="x", session_id="sess-123")
        signal = ingestor.ingest(raw)
        assert signal.session_id == "sess-123"

    def test_multiple_ingestions_produce_unique_ids(self) -> None:
        ingestor = make_ingestor()
        raw = RawInput(modality=Modality.TEXT, payload="same")
        ids = {ingestor.ingest(raw).id for _ in range(10)}
        assert len(ids) == 10
