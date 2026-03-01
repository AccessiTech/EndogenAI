"""Configuration for the sensory-input module."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Payload guard
# ---------------------------------------------------------------------------

MAX_PAYLOAD_BYTES: int = int(os.environ.get("ENDOGEN_MAX_PAYLOAD_BYTES", "1048576"))

# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------

MODULE_ID: str = os.environ.get("ENDOGEN_MODULE_ID", "sensory-input")
SERVICE_NAME: str = "sensory-input"
SERVICE_VERSION: str = "0.1.0"

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

PORT: int = int(os.environ.get("SENSORY_INPUT_PORT", "8100"))
HOST: str = os.environ.get("SENSORY_INPUT_HOST", "0.0.0.0")  # noqa: S104
