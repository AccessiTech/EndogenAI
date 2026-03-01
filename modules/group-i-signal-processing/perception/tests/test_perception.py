"""Unit and integration tests for the perception module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

from perception import config
from perception.models import Signal, SignalSource
from perception.processor import PerceptionPipeline, _classify_pattern

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signal(
    *,
    modality: str = "text",
    sig_type: str = "text.input",
    payload: object = "Hello, EndogenAI!",
    priority: int = 5,
) -> Signal:
    return Signal(
        id="aaaaaaaa-0000-0000-0000-000000000001",
        type=sig_type,
        modality=modality,  # type: ignore[arg-type]
        source=SignalSource(moduleId="attention-filtering", layer="attention-filtering"),
        timestamp="2024-01-01T00:00:00Z",
        payload=payload,
        priority=priority,
    )


# ---------------------------------------------------------------------------
# Unit tests — pattern classification
# ---------------------------------------------------------------------------


class TestPatternClassification:
    def test_question_detected(self) -> None:
        signal = _make_signal(payload="What is EndogenAI?")
        assert _classify_pattern(signal) == "question"

    def test_greeting_detected(self) -> None:
        signal = _make_signal(payload="Hello there!")
        assert _classify_pattern(signal) == "greeting"

    def test_error_detected(self) -> None:
        signal = _make_signal(payload="There was an error in the pipeline")
        assert _classify_pattern(signal) == "error"

    def test_command_detected(self) -> None:
        signal = _make_signal(payload="Please start the process")
        assert _classify_pattern(signal) == "command"

    def test_statement_default(self) -> None:
        signal = _make_signal(payload="The weather is nice today")
        assert _classify_pattern(signal) == "statement"

    def test_non_text_returns_data(self) -> None:
        signal = _make_signal(modality="image", sig_type="image.frame", payload="base64data")
        assert _classify_pattern(signal) == "data"

    def test_non_string_payload_returns_data(self) -> None:
        signal = _make_signal(modality="text", payload={"key": "value"})
        assert _classify_pattern(signal) == "data"


# ---------------------------------------------------------------------------
# Unit tests — pipeline (with mocked LiteLLM)
# ---------------------------------------------------------------------------


class TestPerceptionPipeline:
    async def test_text_signal_processed(self, mock_litellm: None) -> None:
        pipeline = PerceptionPipeline()
        signal = _make_signal(payload="Hello, EndogenAI!")
        result = await pipeline.process(signal)

        assert result.signal_id == signal.id
        assert result.modality == "text"
        assert result.pattern is not None
        assert result.text_features is not None
        assert result.timestamp is not None
        # Embedding disabled in tests
        assert result.embedding_id is None

    async def test_text_features_extracted(self, mock_litellm: None) -> None:
        pipeline = PerceptionPipeline()
        signal = _make_signal(payload="Hello, EndogenAI!")
        result = await pipeline.process(signal)

        assert result.text_features is not None
        assert "EndogenAI" in result.text_features.entities
        assert result.text_features.intent == "greet"
        assert "Hello" in result.text_features.key_phrases

    async def test_image_signal_uses_passthrough(self) -> None:
        pipeline = PerceptionPipeline()
        signal = _make_signal(
            modality="image",
            sig_type="image.frame",
            payload="base64data==",
        )
        result = await pipeline.process(signal)

        assert result.modality == "image"
        assert result.text_features is None
        assert result.passthrough_metadata is not None
        assert result.passthrough_metadata["modality"] == "image"

    async def test_audio_signal_uses_passthrough(self) -> None:
        pipeline = PerceptionPipeline()
        signal = _make_signal(
            modality="audio",
            sig_type="audio.chunk",
            payload="pcm-data",
        )
        result = await pipeline.process(signal)

        assert result.modality == "audio"
        assert result.text_features is None

    async def test_output_has_required_fields(self, mock_litellm: None) -> None:
        pipeline = PerceptionPipeline()
        signal = _make_signal()
        result = await pipeline.process(signal)

        assert result.signal_id
        assert result.modality
        assert result.timestamp
        # pattern may be None or a string
        assert result.pattern is None or isinstance(result.pattern, str)

    async def test_llm_failure_returns_empty_features(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If LiteLLM raises an exception, an empty TextFeatures is returned."""
        from unittest.mock import AsyncMock  # noqa: PLC0415

        import litellm  # noqa: PLC0415

        monkeypatch.setattr(litellm, "acompletion", AsyncMock(side_effect=Exception("LLM error")))

        pipeline = PerceptionPipeline()
        signal = _make_signal(payload="test text")
        result = await pipeline.process(signal)

        assert result.text_features is not None
        assert result.text_features.entities == []
        assert result.text_features.intent is None


# ---------------------------------------------------------------------------
# Unit tests — payload size guard
# ---------------------------------------------------------------------------


class TestPayloadSizeGuard:
    def test_oversized_raises(self) -> None:
        from perception.processor import check_payload_size  # noqa: PLC0415

        with pytest.raises(ValueError, match="exceeds limit"):
            check_payload_size(b"x" * (config.MAX_PAYLOAD_BYTES + 1))

    def test_within_limit_passes(self) -> None:
        from perception.processor import check_payload_size  # noqa: PLC0415

        check_payload_size(b"x" * 100)


# ---------------------------------------------------------------------------
# Unit tests — schema validation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_valid_mcp_passes(self) -> None:
        from perception.processor import validate_mcp  # noqa: PLC0415

        mcp = {
            "id": "00000000-0000-0000-0000-000000000001",
            "version": "0.1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "source": {"moduleId": "attention-filtering", "layer": "attention-filtering"},
            "contentType": "signal/text.input",
            "payload": "Hello",
        }
        validate_mcp(mcp)

    def test_invalid_mcp_raises(self) -> None:
        import jsonschema  # noqa: PLC0415

        from perception.processor import validate_mcp  # noqa: PLC0415

        with pytest.raises(jsonschema.ValidationError):
            validate_mcp({"bad": "data"})

    def test_valid_a2a_passes(self) -> None:
        from perception.processor import validate_a2a  # noqa: PLC0415

        a2a = {
            "id": "00000000-0000-0000-0000-000000000002",
            "role": "user",
            "timestamp": "2024-01-01T00:00:00Z",
            "parts": [{"type": "text", "text": "Hi"}],
        }
        validate_a2a(a2a)

    def test_invalid_a2a_raises(self) -> None:
        import jsonschema  # noqa: PLC0415

        from perception.processor import validate_a2a  # noqa: PLC0415

        with pytest.raises(jsonschema.ValidationError):
            validate_a2a({"role": "user"})  # missing required fields


# ---------------------------------------------------------------------------
# Integration tests — HTTP server
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    async def test_health_ok(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "perception"


class TestPerceiveEndpoint:
    async def test_valid_text_signal(
        self,
        client: AsyncClient,
        mock_litellm: None,
        text_signal_dict: dict[str, object],
    ) -> None:
        payload = {"signal": text_signal_dict}
        resp = await client.post("/perceive", content=json.dumps(payload))
        assert resp.status_code == 200
        body = resp.json()
        assert body["processed"] is True
        result = body["result"]
        assert result["modality"] == "text"
        assert result["signal_id"] == "22222222-0000-0000-0000-000000000001"
        assert "text_features" in result

    async def test_valid_image_signal(
        self,
        client: AsyncClient,
        image_signal_dict: dict[str, object],
    ) -> None:
        payload = {"signal": image_signal_dict}
        resp = await client.post("/perceive", content=json.dumps(payload))
        assert resp.status_code == 200
        body = resp.json()
        result = body["result"]
        assert result["modality"] == "image"
        assert result["text_features"] is None
        assert result["passthrough_metadata"] is not None

    async def test_missing_signal_field_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/perceive", content=json.dumps({}))
        assert resp.status_code == 422

    async def test_oversized_payload_returns_413(self, client: AsyncClient) -> None:
        big = "x" * (config.MAX_PAYLOAD_BYTES + 1)
        resp = await client.post("/perceive", content=big.encode())
        assert resp.status_code == 413

    async def test_invalid_json_returns_400(self, client: AsyncClient) -> None:
        resp = await client.post("/perceive", content=b"not-json{{")
        assert resp.status_code == 400

    async def test_ingest_alias_works(
        self,
        client: AsyncClient,
        mock_litellm: None,
        text_signal_dict: dict[str, object],
    ) -> None:
        payload = {"signal": text_signal_dict}
        resp = await client.post("/ingest", content=json.dumps(payload))
        assert resp.status_code == 200


class TestMcpEndpoint:
    async def test_valid_mcp(self, client: AsyncClient, mock_litellm: None) -> None:
        mcp = {
            "id": "00000000-0000-0000-0000-000000000001",
            "version": "0.1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "source": {"moduleId": "attention-filtering", "layer": "attention-filtering"},
            "contentType": "signal/text.input",
            "payload": "Hello world",
        }
        resp = await client.post("/mcp", content=json.dumps(mcp))
        assert resp.status_code == 200

    async def test_invalid_mcp_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/mcp", content=json.dumps({"bad": "data"}))
        assert resp.status_code == 422


class TestA2aEndpoint:
    async def test_valid_a2a(self, client: AsyncClient, mock_litellm: None) -> None:
        a2a = {
            "id": "00000000-0000-0000-0000-000000000002",
            "role": "user",
            "timestamp": "2024-01-01T00:00:00Z",
            "parts": [{"type": "text", "text": "Hello world"}],
        }
        resp = await client.post("/a2a", content=json.dumps(a2a))
        assert resp.status_code == 200

    async def test_invalid_a2a_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/a2a", content=json.dumps({"role": "user"}))
        assert resp.status_code == 422


class TestAgentCard:
    async def test_agent_card_served(self, client: AsyncClient) -> None:
        resp = await client.get("/.well-known/agent-card.json")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "perception"
