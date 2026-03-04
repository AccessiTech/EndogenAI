"""Resource subscription registry for Working Memory.

Maintains a per-session callback registry. On resource write,
all registered callbacks are invoked with the affected URI.

Usage::

    from working_memory.subscriptions import subscribe, unsubscribe, notify_all

    subscribe("session-abc", lambda uri: print(f"updated: {uri}"))
    notify_all("brain://group-ii/working-memory/context/current")
    unsubscribe("session-abc")
"""
from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_subscribers: dict[str, Callable[[str], None]] = {}


def subscribe(session_id: str, callback: Callable[[str], None]) -> None:
    """Register a callback for the given session_id."""
    _subscribers[session_id] = callback


def unsubscribe(session_id: str) -> None:
    """Remove the callback for the given session_id (no-op if not registered)."""
    _subscribers.pop(session_id, None)


def notify_all(uri: str) -> None:
    """Invoke all registered callbacks with the affected uri.

    Dead subscribers (callbacks that raise) are silently skipped so that
    one failing callback cannot block notification of the rest.
    """
    for callback in list(_subscribers.values()):
        with contextlib.suppress(Exception):
            callback(uri)  # dead subscriber — exception silently swallowed


def clear() -> None:
    """Remove all registered subscribers (test helper)."""
    _subscribers.clear()
