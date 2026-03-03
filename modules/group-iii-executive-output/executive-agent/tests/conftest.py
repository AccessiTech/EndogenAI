"""conftest.py — pytest fixtures shared across executive-agent tests."""
from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
