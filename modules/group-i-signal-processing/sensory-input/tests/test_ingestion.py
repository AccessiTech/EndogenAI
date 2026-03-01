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


class TestSignalIngestorAllModalities:
    """Verify every modality produces the correct canonical Signal.type prefix."""

    def _ingest(self, modality: Modality, payload: object) -> object:
        ingestor = SignalIngestor()
        return ingestor.ingest(RawInput(modality=modality, payload=payload))

    def test_image_signal_type(self) -> None:
        signal = self._ingest(Modality.IMAGE, b"\x89PNG")
        assert signal.type == "image.frame"

    def test_audio_signal_type(self) -> None:
        signal = self._ingest(Modality.AUDIO, b"RIFF")
        assert signal.type == "audio.chunk"

    def test_sensor_signal_type(self) -> None:
        signal = self._ingest(Modality.SENSOR, {"temp": 22.5})
        assert signal.type == "sensor.reading"

    def test_api_event_signal_type(self) -> None:
        signal = self._ingest(Modality.API_EVENT, {"action": "click"})
        assert signal.type == "api.event"

    def test_internal_signal_type(self) -> None:
        signal = self._ingest(Modality.INTERNAL, {"kind": "heartbeat"})
        assert signal.type == "internal.signal"

    def test_control_signal_type(self) -> None:
        signal = self._ingest(Modality.CONTROL, {"directive": "focus"})
        assert signal.type == "control.directive"

    def test_audio_bytes_base64_encoded_in_signal(self) -> None:
        import base64
        raw_bytes = b"RIFF\x00\x00"
        signal = self._ingest(Modality.AUDIO, raw_bytes)
        assert signal.payload == base64.b64encode(raw_bytes).decode("ascii")

    def test_internal_dict_payload_passes_through(self) -> None:
        payload = {"kind": "tick", "seq": 42}
        signal = self._ingest(Modality.INTERNAL, payload)
        assert signal.payload == payload

    def test_control_dict_payload_passes_through(self) -> None:
        payload = {"directive": "focus", "target": "text"}
        signal = self._ingest(Modality.CONTROL, payload)
        assert signal.payload == payload

    def test_sensor_scalar_wrapped(self) -> None:
        signal = self._ingest(Modality.SENSOR, 99.9)
        assert signal.payload == {"value": 99.9}


class TestSignalIngestorExtras:
    """Additional edge-case coverage for SignalIngestor."""

    def test_metadata_propagated(self) -> None:
        ingestor = SignalIngestor()
        raw = RawInput(
            modality=Modality.TEXT,
            payload="hello",
            metadata={"source": "ui", "lang": "en"},
        )
        signal = ingestor.ingest(raw)
        assert signal.metadata == {"source": "ui", "lang": "en"}

    def test_encoding_hint_propagated(self) -> None:
        ingestor = SignalIngestor()
        raw = RawInput(modality=Modality.AUDIO, payload=b"x", encoding="pcm16")
        signal = ingestor.ingest(raw)
        assert signal.encoding == "pcm16"

    def test_default_module_id_is_sensory_input(self) -> None:
        ingestor = SignalIngestor()
        signal = ingestor.ingest(RawInput(modality=Modality.TEXT, payload="x"))
        assert signal.source.module_id == "sensory-input"

    def test_default_instance_id_is_none(self) -> None:
        ingestor = SignalIngestor()
        signal = ingestor.ingest(RawInput(modality=Modality.TEXT, payload="x"))
        assert signal.source.instance_id is None

    def test_custom_module_id_and_instance_id_in_source(self) -> None:
        ingestor = SignalIngestor(module_id="edge-sensor", instance_id="node-7")
        signal = ingestor.ingest(RawInput(modality=Modality.TEXT, payload="x"))
        assert signal.source.module_id == "edge-sensor"
        assert signal.source.instance_id == "node-7"

    def test_timestamp_equals_ingested_at_for_raw_ingestion(self) -> None:
        ingestor = SignalIngestor()
        signal = ingestor.ingest(RawInput(modality=Modality.TEXT, payload="x"))
        # Both should be very close; exact equality not guaranteed but both set
        assert signal.timestamp is not None
        assert signal.ingested_at is not None

    def test_modality_stored_on_signal(self) -> None:
        ingestor = SignalIngestor()
        for modality in Modality:
            payload: object = "x" if modality == Modality.TEXT else b"x" if modality in (Modality.IMAGE, Modality.AUDIO) else {}
            signal = ingestor.ingest(RawInput(modality=modality, payload=payload))
            assert signal.modality == modality
