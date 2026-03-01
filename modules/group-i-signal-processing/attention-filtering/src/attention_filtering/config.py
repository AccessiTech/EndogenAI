"""Configuration for the attention-filtering module."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Payload guard
# ---------------------------------------------------------------------------

MAX_PAYLOAD_BYTES: int = int(os.environ.get("ENDOGEN_MAX_PAYLOAD_BYTES", "1048576"))

# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------

MODULE_ID: str = os.environ.get("ENDOGEN_MODULE_ID", "attention-filtering")
SERVICE_NAME: str = "attention-filtering"
SERVICE_VERSION: str = "0.1.0"

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

PORT: int = int(os.environ.get("ATTENTION_FILTERING_PORT", "8101"))
HOST: str = os.environ.get("ATTENTION_FILTERING_HOST", "0.0.0.0")  # noqa: S104

# ---------------------------------------------------------------------------
# Attention defaults
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD: float = float(os.environ.get("ATTENTION_THRESHOLD", "0.3"))
