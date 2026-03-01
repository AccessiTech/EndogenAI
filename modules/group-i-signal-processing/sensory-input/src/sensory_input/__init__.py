"""sensory-input — EndogenAI signal ingestion module."""

from sensory_input.models import (
    IngestRequest,
    IngestResponse,
    Layer,
    Modality,
    Signal,
    SignalSource,
)
from sensory_input.processor import (
    a2a_to_signal,
    check_payload_size,
    ingest_request_to_signal,
    mcp_to_signal,
    validate_a2a,
    validate_mcp,
)

__all__ = [
    "Signal",
    "SignalSource",
    "Layer",
    "Modality",
    "IngestRequest",
    "IngestResponse",
    "check_payload_size",
    "validate_mcp",
    "validate_a2a",
    "ingest_request_to_signal",
    "mcp_to_signal",
    "a2a_to_signal",
]

__version__ = "0.1.0"
