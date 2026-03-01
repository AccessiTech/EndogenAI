"""Shared test fixtures for sensory-input tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from sensory_input.server import app


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[misc]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac  # type: ignore[misc]


@pytest.fixture()
def valid_mcp_payload() -> dict[str, object]:
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "version": "0.1.0",
        "timestamp": "2024-01-01T00:00:00Z",
        "source": {"moduleId": "test-sender", "layer": "application"},
        "contentType": "signal/text.input",
        "payload": "Hello, EndogenAI!",
    }


@pytest.fixture()
def valid_a2a_payload() -> dict[str, object]:
    return {
        "id": "00000000-0000-0000-0000-000000000002",
        "role": "user",
        "timestamp": "2024-01-01T00:00:00Z",
        "parts": [{"type": "text", "text": "Hello, EndogenAI!"}],
    }
