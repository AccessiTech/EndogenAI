"""Integration tests for episodic memory timeline.

Requires running ChromaDB container.
Marked with @pytest.mark.integration — skipped unless ENDOGENAI_INTEGRATION_TESTS=1.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("ENDOGENAI_INTEGRATION_TESTS"),
    reason="Integration tests require ENDOGENAI_INTEGRATION_TESTS=1 and running ChromaDB",
)
async def test_integration_placeholder() -> None:
    """Placeholder — implement with testcontainers once services are available."""
    assert True
