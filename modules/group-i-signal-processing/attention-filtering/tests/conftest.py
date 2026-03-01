"""Shared fixtures for attention-filtering tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from attention_filtering.server import app


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[misc]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac  # type: ignore[misc]


@pytest.fixture()
def text_signal_dict() -> dict[str, object]:
    return {
        "id": "11111111-0000-0000-0000-000000000001",
        "type": "text.input",
        "modality": "text",
        "source": {"moduleId": "sensory-input", "layer": "sensory-input"},
        "timestamp": "2024-01-01T00:00:00Z",
        "payload": "Hello world",
        "priority": 7,
    }


@pytest.fixture()
def control_signal_dict() -> dict[str, object]:
    return {
        "id": "11111111-0000-0000-0000-000000000002",
        "type": "attention.directive",
        "modality": "control",
        "source": {"moduleId": "executive", "layer": "executive"},
        "timestamp": "2024-01-01T00:00:00Z",
        "payload": {"threshold": 0.5},
        "priority": 10,
    }
