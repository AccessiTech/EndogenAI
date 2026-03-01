"""Tests for the sensory-input data models."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from endogenai_sensory_input.models import (
    Modality,
    RawInput,
    Signal,
    SignalSource,
    TraceContext,
)


class TestModality:
    def test_all_seven_modality_values(self) -> None:
        expected = {"text", "image", "audio", "sensor", "api-event", "internal", "control"}
        assert {m.value for m in Modality} == expected

    def test_modality_is_str_comparable(self) -> None:
        assert Modality.TEXT == "text"
        assert Modality.API_EVENT == "api-event"
        assert Modality.CONTROL == "control"

    def test_modality_from_string(self) -> None:
        assert Modality("text") is Modality.TEXT
        assert Modality("api-event") is Modality.API_EVENT

    def test_invalid_modality_raises(self) -> None:
        with pytest.raises(ValueError):
            Modality("unknown")


class TestSignalSource:
    def test_module_id_populated_via_alias(self) -> None:
        src = SignalSource(moduleId="sensory-input", layer="sensory-input")
        assert src.module_id == "sensory-input"

    def test_module_id_populated_by_name(self) -> None:
        src = SignalSource.model_validate({"module_id": "sensory-input", "layer": "sensory-input"})
        assert src.module_id == "sensory-input"

    def test_instance_id_defaults_to_none(self) -> None:
        src = SignalSource(moduleId="m", layer="l")
        assert src.instance_id is None

    def test_instance_id_set_via_alias(self) -> None:
        src = SignalSource(moduleId="m", layer="l", instanceId="node-0")
        assert src.instance_id == "node-0"

    def test_layer_stored(self) -> None:
        src = SignalSource(moduleId="m", layer="sensory-input")
        assert src.layer == "sensory-input"


class TestRawInput:
    def test_default_priority_is_5(self) -> None:
        raw = RawInput(modality=Modality.TEXT, payload="hello")
        assert raw.priority == 5

    def test_priority_minimum_0(self) -> None:
        raw = RawInput(modality=Modality.TEXT, payload="x", priority=0)
        assert raw.priority == 0

    def test_priority_maximum_10(self) -> None:
        raw = RawInput(modality=Modality.TEXT, payload="x", priority=10)
        assert raw.priority == 10

    def test_priority_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            RawInput(modality=Modality.TEXT, payload="x", priority=-1)

    def test_priority_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            RawInput(modality=Modality.TEXT, payload="x", priority=11)

    def test_default_metadata_is_empty_dict(self) -> None:
        raw = RawInput(modality=Modality.TEXT, payload="x")
        assert raw.metadata == {}

    def test_metadata_stored(self) -> None:
        raw = RawInput(modality=Modality.TEXT, payload="x", metadata={"key": "val"})
        assert raw.metadata == {"key": "val"}

    def test_encoding_defaults_to_none(self) -> None:
        raw = RawInput(modality=Modality.AUDIO, payload=b"x")
        assert raw.encoding is None

    def test_session_id_defaults_to_none(self) -> None:
        raw = RawInput(modality=Modality.TEXT, payload="x")
        assert raw.session_id is None

    def test_payload_can_be_any_type(self) -> None:
        assert RawInput(modality=Modality.TEXT, payload="str").payload == "str"
        assert RawInput(modality=Modality.SENSOR, payload=3.14).payload == 3.14
        assert RawInput(modality=Modality.IMAGE, payload=b"\x00").payload == b"\x00"


class TestSignal:
    def _make(self, **kwargs: object) -> Signal:
        return Signal(
            type="text.input",
            modality=Modality.TEXT,
            source=SignalSource(moduleId="sensory-input", layer="sensory-input"),
            payload="hello",
            **kwargs,  # type: ignore[arg-type]
        )

    def test_auto_id_is_valid_uuid(self) -> None:
        signal = self._make()
        uuid.UUID(signal.id)  # raises ValueError if invalid

    def test_two_signals_have_different_ids(self) -> None:
        assert self._make().id != self._make().id

    def test_auto_timestamp_is_set(self) -> None:
        assert self._make().timestamp is not None

    def test_auto_ingested_at_is_set(self) -> None:
        assert self._make().ingested_at is not None

    def test_default_priority_is_5(self) -> None:
        assert self._make().priority == 5

    def test_ttl_defaults_to_none(self) -> None:
        assert self._make().ttl is None

    def test_trace_context_defaults_to_none(self) -> None:
        assert self._make().trace_context is None

    def test_trace_context_set(self) -> None:
        signal = self._make(
            trace_context=TraceContext(traceparent="00-abc-0000-01"),
        )
        assert signal.trace_context is not None
        assert signal.trace_context.traceparent == "00-abc-0000-01"

    def test_correlation_id_defaults_to_none(self) -> None:
        assert self._make().correlation_id is None

    def test_parent_signal_id_defaults_to_none(self) -> None:
        assert self._make().parent_signal_id is None

    def test_metadata_defaults_empty(self) -> None:
        assert self._make().metadata == {}


class TestTraceContext:
    def test_traceparent_stored(self) -> None:
        tc = TraceContext(traceparent="00-trace-span-01")
        assert tc.traceparent == "00-trace-span-01"

    def test_tracestate_defaults_to_none(self) -> None:
        tc = TraceContext(traceparent="00-trace-span-01")
        assert tc.tracestate is None

    def test_tracestate_set(self) -> None:
        tc = TraceContext(traceparent="00-trace-span-01", tracestate="vendor=value")
        assert tc.tracestate == "vendor=value"
