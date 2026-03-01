"""Unit and integration tests for the attention-filtering module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

from attention_filtering import config
from attention_filtering.models import Signal, SignalSource
from attention_filtering.processor import AttentionFilter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signal(
    *,
    modality: str = "text",
    sig_type: str = "text.input",
    priority: int = 5,
    payload: object = "hello",
) -> Signal:
    return Signal(
        id="aaaaaaaa-0000-0000-0000-000000000001",
        type=sig_type,
        modality=modality,  # type: ignore[arg-type]
        source=SignalSource(moduleId="sensory-input", layer="sensory-input"),
        timestamp="2024-01-01T00:00:00Z",
        payload=payload,
        priority=priority,
    )


# ---------------------------------------------------------------------------
# Unit tests — salience scoring
# ---------------------------------------------------------------------------


class TestSalienceScoring:
    def test_high_priority_gets_high_score(self) -> None:
        af = AttentionFilter()
        signal = _make_signal(priority=10, modality="text", sig_type="text.input")
        score = af.score(signal)
        assert score >= 0.7  # priority 10 → 0.4*1.0 + 0.3*0.8 + 0.3*0.7 = 0.85

    def test_low_priority_gets_low_score(self) -> None:
        af = AttentionFilter()
        signal = _make_signal(priority=0, modality="internal", sig_type="internal.tick")
        score = af.score(signal)
        assert score <= 0.5

    def test_control_modality_boosts_score(self) -> None:
        af = AttentionFilter()
        ctrl = _make_signal(priority=5, modality="control", sig_type="attention.directive")
        text = _make_signal(priority=5, modality="text", sig_type="text.input")
        assert af.score(ctrl) > af.score(text)

    def test_score_within_bounds(self) -> None:
        af = AttentionFilter()
        for priority in [0, 5, 10]:
            for modality in ["text", "image", "audio", "sensor", "internal", "control"]:
                signal = _make_signal(priority=priority, modality=modality)
                score = af.score(signal)
                assert 0.0 <= score <= 1.0, f"Score {score} out of bounds"


# ---------------------------------------------------------------------------
# Unit tests — filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    def test_above_threshold_passes(self) -> None:
        af = AttentionFilter(threshold=0.3)
        signal = _make_signal(priority=8, modality="text")
        result = af.filter(signal)
        assert result.scored.passed is True
        assert result.dropped is False

    def test_below_threshold_dropped(self) -> None:
        af = AttentionFilter(threshold=0.99)  # very high threshold
        signal = _make_signal(priority=0, modality="internal", sig_type="internal.tick")
        result = af.filter(signal)
        assert result.scored.passed is False
        assert result.dropped is True

    def test_passed_signal_has_route(self) -> None:
        af = AttentionFilter(threshold=0.1)
        signal = _make_signal(priority=5, modality="text")
        result = af.filter(signal)
        assert result.scored.routed_to is not None
        assert "8102" in result.scored.routed_to  # default → perception

    def test_dropped_signal_has_no_route(self) -> None:
        af = AttentionFilter(threshold=0.99)
        signal = _make_signal(priority=0, modality="internal", sig_type="internal.tick")
        result = af.filter(signal)
        assert result.scored.routed_to is None


# ---------------------------------------------------------------------------
# Unit tests — attention directives
# ---------------------------------------------------------------------------


class TestAttentionDirectives:
    def test_directive_updates_threshold(self) -> None:
        af = AttentionFilter(threshold=0.3)
        directive = _make_signal(
            modality="control",
            sig_type="attention.directive",
            priority=10,
            payload={"threshold": 0.8},
        )
        af.filter(directive)
        assert af.threshold == 0.8

    def test_directive_updates_modality_weight(self) -> None:
        af = AttentionFilter()
        original_weight = af.modality_weights["text"]
        directive = _make_signal(
            modality="control",
            sig_type="attention.directive",
            priority=10,
            payload={"modality_weights": {"text": 0.99}},
        )
        af.filter(directive)
        assert af.modality_weights["text"] == 0.99
        assert af.modality_weights["text"] != original_weight

    def test_directive_updates_routing(self) -> None:
        af = AttentionFilter()
        directive = _make_signal(
            modality="control",
            sig_type="attention.directive",
            priority=10,
            payload={"routing": {"text": "http://custom-host:9999/ingest"}},
        )
        af.filter(directive)
        assert af.routing["text"] == "http://custom-host:9999/ingest"

    def test_invalid_directive_payload_is_ignored(self) -> None:
        af = AttentionFilter(threshold=0.3)
        directive = _make_signal(
            modality="control",
            sig_type="attention.directive",
            priority=10,
            payload="not-a-dict",
        )
        af.filter(directive)
        assert af.threshold == 0.3  # unchanged


# ---------------------------------------------------------------------------
# Unit tests — payload size guard
# ---------------------------------------------------------------------------


class TestPayloadSizeGuard:
    def test_oversized_raises(self) -> None:
        from attention_filtering.processor import check_payload_size
        with pytest.raises(ValueError, match="exceeds limit"):
            check_payload_size(b"x" * (config.MAX_PAYLOAD_BYTES + 1))

    def test_within_limit_passes(self) -> None:
        from attention_filtering.processor import check_payload_size
        check_payload_size(b"x" * 100)


# ---------------------------------------------------------------------------
# Integration tests — HTTP server
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    async def test_health_ok(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestStateEndpoint:
    async def test_state_returns_threshold(self, client: AsyncClient) -> None:
        resp = await client.get("/state")
        assert resp.status_code == 200
        body = resp.json()
        assert "threshold" in body
        assert "routing" in body


class TestFilterEndpoint:
    async def test_valid_signal_filtered(
        self, client: AsyncClient, text_signal_dict: dict[str, object]
    ) -> None:
        payload = {"signal": text_signal_dict}
        resp = await client.post("/filter", content=json.dumps(payload))
        assert resp.status_code == 200
        body = resp.json()
        assert "scored" in body
        assert "dropped" in body
        assert 0.0 <= body["scored"]["score"] <= 1.0

    async def test_missing_signal_field_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/filter", content=json.dumps({}))
        assert resp.status_code == 422

    async def test_oversized_payload_returns_413(self, client: AsyncClient) -> None:
        big = "x" * (config.MAX_PAYLOAD_BYTES + 1)
        resp = await client.post("/filter", content=big.encode())
        assert resp.status_code == 413

    async def test_attention_directive_updates_state(
        self,
        client: AsyncClient,
        control_signal_dict: dict[str, object],
    ) -> None:
        payload = {"signal": control_signal_dict}
        resp = await client.post("/filter", content=json.dumps(payload))
        assert resp.status_code == 200
        # After directive with threshold=0.5, /state should reflect it
        state_resp = await client.get("/state")
        assert state_resp.json()["threshold"] == 0.5


class TestMcpEndpoint:
    async def test_valid_mcp_filtered(self, client: AsyncClient) -> None:
        mcp = {
            "id": "00000000-0000-0000-0000-000000000001",
            "version": "0.1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "source": {"moduleId": "sensory-input", "layer": "sensory-input"},
            "contentType": "signal/text.input",
            "payload": "Hello",
        }
        resp = await client.post("/mcp", content=json.dumps(mcp))
        assert resp.status_code == 200

    async def test_invalid_mcp_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/mcp", content=json.dumps({"bad": "data"}))
        assert resp.status_code == 422


class TestA2aEndpoint:
    async def test_valid_a2a_filtered(self, client: AsyncClient) -> None:
        a2a = {
            "id": "00000000-0000-0000-0000-000000000002",
            "role": "user",
            "timestamp": "2024-01-01T00:00:00Z",
            "parts": [{"type": "text", "text": "hi"}],
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
        assert resp.json()["name"] == "attention-filtering"
