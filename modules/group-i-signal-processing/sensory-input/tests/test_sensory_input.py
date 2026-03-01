"""Unit and integration tests for the sensory-input module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

from sensory_input import config
from sensory_input.models import IngestRequest, Signal
from sensory_input.processor import (
    a2a_to_signal,
    check_payload_size,
    ingest_request_to_signal,
    mcp_to_signal,
    validate_a2a,
    validate_mcp,
)

# ---------------------------------------------------------------------------
# Unit tests — processor
# ---------------------------------------------------------------------------


class TestCheckPayloadSize:
    def test_within_limit_passes(self) -> None:
        check_payload_size(b"x" * 100)

    def test_at_limit_passes(self) -> None:
        check_payload_size(b"x" * config.MAX_PAYLOAD_BYTES)

    def test_oversized_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds limit"):
            check_payload_size(b"x" * (config.MAX_PAYLOAD_BYTES + 1))


class TestIngestRequestToSignal:
    def test_valid_text_produces_signal(self) -> None:
        req = IngestRequest(modality="text", type="text.input", payload="hello world")
        signal = ingest_request_to_signal(req)

        assert isinstance(signal, Signal)
        assert signal.modality == "text"
        assert signal.type == "text.input"
        assert signal.payload == "hello world"
        assert signal.source.layer == "sensory-input"
        assert signal.source.moduleId == config.MODULE_ID
        assert signal.ingestedAt is not None
        assert signal.timestamp is not None

    def test_valid_image_produces_signal(self) -> None:
        req = IngestRequest(modality="image", type="image.frame", payload="base64data==")
        signal = ingest_request_to_signal(req)
        assert signal.modality == "image"
        assert signal.type == "image.frame"

    def test_priority_propagated(self) -> None:
        req = IngestRequest(modality="text", type="text.input", payload="hi", priority=9)
        signal = ingest_request_to_signal(req)
        assert signal.priority == 9

    def test_metadata_propagated(self) -> None:
        req = IngestRequest(
            modality="sensor",
            type="sensor.reading",
            payload=42.0,
            metadata={"sensor_id": "temp-01"},
        )
        signal = ingest_request_to_signal(req)
        assert signal.metadata == {"sensor_id": "temp-01"}

    def test_output_has_uuid_id(self) -> None:
        req = IngestRequest(modality="text", type="text.input", payload="x")
        signal = ingest_request_to_signal(req)
        import uuid
        uuid.UUID(signal.id)  # raises if not a valid UUID


class TestMcpToSignal:
    def test_valid_mcp_converts(self, valid_mcp_payload: dict[str, object]) -> None:
        signal = mcp_to_signal(valid_mcp_payload)  # type: ignore[arg-type]
        assert signal.modality == "text"
        assert signal.type == "text.input"
        assert signal.payload == "Hello, EndogenAI!"

    def test_mcp_validation_passes(self, valid_mcp_payload: dict[str, object]) -> None:
        validate_mcp(valid_mcp_payload)  # type: ignore[arg-type]

    def test_mcp_validation_fails_missing_source(self) -> None:
        import jsonschema
        bad = {
            "id": "00000000-0000-0000-0000-000000000001",
            "version": "0.1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "contentType": "signal/text.input",
            "payload": "hi",
            # 'source' is required but missing
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_mcp(bad)


class TestA2aToSignal:
    def test_text_part_converts(self, valid_a2a_payload: dict[str, object]) -> None:
        signal = a2a_to_signal(valid_a2a_payload)  # type: ignore[arg-type]
        assert signal.modality == "text"
        assert signal.type == "text.input"
        assert signal.payload == "Hello, EndogenAI!"

    def test_file_image_part_converts(self) -> None:
        msg = {
            "id": "00000000-0000-0000-0000-000000000003",
            "role": "user",
            "timestamp": "2024-01-01T00:00:00Z",
            "parts": [
                {
                    "type": "file",
                    "file": {
                        "mimeType": "image/png",
                        "bytes": "iVBORw==",
                    },
                }
            ],
        }
        signal = a2a_to_signal(msg)
        assert signal.modality == "image"
        assert signal.type == "image.frame"

    def test_a2a_validation_fails_missing_parts(self) -> None:
        import jsonschema
        bad = {
            "id": "00000000-0000-0000-0000-000000000004",
            "role": "user",
            "timestamp": "2024-01-01T00:00:00Z",
            # 'parts' is required but missing
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_a2a(bad)


# ---------------------------------------------------------------------------
# Integration tests — HTTP server
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    async def test_health_returns_ok(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "sensory-input"


class TestIngestEndpoint:
    async def test_valid_text_ingest(self, client: AsyncClient) -> None:
        payload = {
            "modality": "text",
            "type": "text.input",
            "payload": "Hello, EndogenAI!",
        }
        resp = await client.post("/ingest", content=json.dumps(payload))
        assert resp.status_code == 200
        body = resp.json()
        assert body["accepted"] is True
        signal = body["signal"]
        assert signal["modality"] == "text"
        assert signal["type"] == "text.input"
        assert signal["payload"] == "Hello, EndogenAI!"
        assert signal["source"]["layer"] == "sensory-input"

    async def test_missing_required_field_returns_422(self, client: AsyncClient) -> None:
        # 'type' field is missing
        payload = {"modality": "text", "payload": "hello"}
        resp = await client.post("/ingest", content=json.dumps(payload))
        assert resp.status_code == 422

    async def test_oversized_payload_returns_413(self, client: AsyncClient) -> None:
        oversized = json.dumps(
            {"modality": "text", "type": "text.input", "payload": "x" * (config.MAX_PAYLOAD_BYTES + 1)}
        ).encode()
        resp = await client.post("/ingest", content=oversized)
        assert resp.status_code == 413

    async def test_invalid_json_returns_400(self, client: AsyncClient) -> None:
        resp = await client.post("/ingest", content=b"not-json{{{")
        assert resp.status_code == 400


class TestMcpEndpoint:
    async def test_valid_mcp(
        self, client: AsyncClient, valid_mcp_payload: dict[str, object]
    ) -> None:
        resp = await client.post("/mcp", content=json.dumps(valid_mcp_payload))
        assert resp.status_code == 200
        body = resp.json()
        assert body["modality"] == "text"
        assert body["type"] == "text.input"

    async def test_invalid_mcp_schema_returns_422(self, client: AsyncClient) -> None:
        bad = {"id": "not-a-uuid", "version": "0.1.0"}  # missing required fields
        resp = await client.post("/mcp", content=json.dumps(bad))
        assert resp.status_code == 422


class TestA2aEndpoint:
    async def test_valid_a2a(
        self, client: AsyncClient, valid_a2a_payload: dict[str, object]
    ) -> None:
        resp = await client.post("/a2a", content=json.dumps(valid_a2a_payload))
        assert resp.status_code == 200
        body = resp.json()
        assert body["modality"] == "text"
        assert body["payload"] == "Hello, EndogenAI!"

    async def test_invalid_a2a_returns_422(self, client: AsyncClient) -> None:
        bad = {"id": "00000000-0000-0000-0000-000000000001", "role": "user"}  # missing parts
        resp = await client.post("/a2a", content=json.dumps(bad))
        assert resp.status_code == 422


class TestAgentCard:
    async def test_agent_card_served(self, client: AsyncClient) -> None:
        resp = await client.get("/.well-known/agent-card.json")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "sensory-input"
        assert "endpoints" in body
