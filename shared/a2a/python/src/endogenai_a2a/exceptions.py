"""A2A exception hierarchy."""

from __future__ import annotations


class A2AError(Exception):
    """Base class for all A2A client errors."""


class A2AProtocolError(A2AError):
    """Raised when the server returns an invalid or unexpected JSON-RPC response."""


class A2ATaskNotFound(A2AError):
    """Raised when tasks/get returns a null or missing result for the requested task ID."""
