"""Integration tests for STM consolidation pipeline.

These tests require running Redis and ChromaDB containers.
They are marked with @pytest.mark.integration and are skipped in CI unless
the ENDOGENAI_INTEGRATION_TESTS environment variable is set.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("ENDOGENAI_INTEGRATION_TESTS"),
    reason="Integration tests require ENDOGENAI_INTEGRATION_TESTS=1 and running services",
)
async def test_integration_placeholder() -> None:
    """Placeholder — implement with testcontainers once services are available."""
    # TODO: spin up Redis + ChromaDB via testcontainers, run consolidation pipeline end-to-end
    assert True
