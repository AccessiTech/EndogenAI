"""Tests for payload normalisation."""

from __future__ import annotations

import base64

from endogenai_sensory_input.models import Modality
from endogenai_sensory_input.normalize import normalize_payload


class TestNormalizePayload:
    def test_text_stripped(self) -> None:
        assert normalize_payload(Modality.TEXT, "  hi  ", None) == "hi"

    def test_text_coerced_from_int(self) -> None:
        assert normalize_payload(Modality.TEXT, 42, None) == "42"

    def test_image_bytes_base64(self) -> None:
        raw = b"\x00\x01\x02"
        result = normalize_payload(Modality.IMAGE, raw, None)
        assert result == base64.b64encode(raw).decode("ascii")

    def test_image_str_passthrough(self) -> None:
        assert normalize_payload(Modality.IMAGE, "data:image/png;base64,abc", None) == "data:image/png;base64,abc"

    def test_audio_bytes_base64(self) -> None:
        raw = b"RIFF"
        result = normalize_payload(Modality.AUDIO, raw, None)
        assert result == base64.b64encode(raw).decode("ascii")

    def test_sensor_dict_passthrough(self) -> None:
        d = {"temp": 23.5}
        assert normalize_payload(Modality.SENSOR, d, None) == d

    def test_sensor_scalar_wrapped(self) -> None:
        assert normalize_payload(Modality.SENSOR, 99, None) == {"value": 99}

    def test_api_event_dict_passthrough(self) -> None:
        d = {"event": "submit"}
        assert normalize_payload(Modality.API_EVENT, d, None) == d

    def test_api_event_scalar_wrapped(self) -> None:
        assert normalize_payload(Modality.API_EVENT, "click", None) == {"value": "click"}

    def test_internal_passthrough(self) -> None:
        obj = {"kind": "heartbeat"}
        assert normalize_payload(Modality.INTERNAL, obj, None) is obj

    def test_control_passthrough(self) -> None:
        obj = {"directive": "focus"}
        assert normalize_payload(Modality.CONTROL, obj, None) is obj
