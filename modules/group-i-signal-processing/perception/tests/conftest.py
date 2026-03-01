"""Shared fixtures for perception tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from perception.server import app


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[misc]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac  # type: ignore[misc]


@pytest.fixture()
def mock_litellm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock litellm.acompletion to return a canned NLP response."""
    import litellm  # noqa: PLC0415

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        '{"entities": ["EndogenAI"], "intent": "greet", "key_phrases": ["Hello"]}'
    )

    async_mock = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(litellm, "acompletion", async_mock)


@pytest.fixture()
def text_signal_dict() -> dict[str, object]:
    return {
        "id": "22222222-0000-0000-0000-000000000001",
        "type": "text.input",
        "modality": "text",
        "source": {"moduleId": "attention-filtering", "layer": "attention-filtering"},
        "timestamp": "2024-01-01T00:00:00Z",
        "payload": "Hello, EndogenAI!",
        "priority": 7,
    }


@pytest.fixture()
def image_signal_dict() -> dict[str, object]:
    return {
        "id": "22222222-0000-0000-0000-000000000002",
        "type": "image.frame",
        "modality": "image",
        "source": {"moduleId": "attention-filtering", "layer": "attention-filtering"},
        "timestamp": "2024-01-01T00:00:00Z",
        "payload": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI6QAAAABJRU5ErkJggg==",
        "encoding": "base64",
        "priority": 5,
    }
