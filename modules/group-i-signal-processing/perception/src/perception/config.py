"""Configuration for the perception module."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Payload guard
# ---------------------------------------------------------------------------

MAX_PAYLOAD_BYTES: int = int(os.environ.get("ENDOGEN_MAX_PAYLOAD_BYTES", "1048576"))

# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------

MODULE_ID: str = os.environ.get("ENDOGEN_MODULE_ID", "perception")
SERVICE_NAME: str = "perception"
SERVICE_VERSION: str = "0.1.0"

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

PORT: int = int(os.environ.get("PERCEPTION_PORT", "8102"))
HOST: str = os.environ.get("PERCEPTION_HOST", "0.0.0.0")  # noqa: S104

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

LLM_MODEL: str = os.environ.get("PERCEPTION_LLM_MODEL", "ollama/llama3.2")

# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------

ENABLE_EMBEDDING: bool = os.environ.get("PERCEPTION_ENABLE_EMBEDDING", "false").lower() == "true"
CHROMA_HOST: str = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT: int = int(os.environ.get("CHROMA_PORT", "8000"))
OLLAMA_ENDPOINT: str = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
PERCEPTION_COLLECTION: str = "brain.perception"
