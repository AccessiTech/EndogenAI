"""Tests for working_memory.subscriptions module."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from working_memory.subscriptions import clear, notify_all, subscribe, unsubscribe


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    """Clear the subscriber registry before and after each test."""
    clear()
    yield
    clear()


class TestSubscribe:
    def test_subscribe_and_notify_calls_callback(self) -> None:
        """Registering a callback then calling notify_all triggers it with the URI."""
        cb = Mock()
        subscribe("session-1", cb)
        notify_all("brain://group-ii/working-memory/context/current")
        cb.assert_called_once_with("brain://group-ii/working-memory/context/current")

    def test_multiple_subscribers_all_notified(self) -> None:
        """All registered callbacks are called when notify_all is invoked."""
        cb1, cb2, cb3 = Mock(), Mock(), Mock()
        subscribe("s1", cb1)
        subscribe("s2", cb2)
        subscribe("s3", cb3)
        uri = "brain://group-ii/working-memory/context/current"
        notify_all(uri)
        cb1.assert_called_once_with(uri)
        cb2.assert_called_once_with(uri)
        cb3.assert_called_once_with(uri)

    def test_unsubscribe_prevents_callback(self) -> None:
        """After unsubscribe, the removed callback is NOT called."""
        cb = Mock()
        subscribe("session-x", cb)
        unsubscribe("session-x")
        notify_all("brain://group-ii/working-memory/context/current")
        cb.assert_not_called()

    def test_dead_subscriber_does_not_block_others(self) -> None:
        """If one callback raises, remaining callbacks are still notified."""
        dead = Mock(side_effect=RuntimeError("connection lost"))
        live = Mock()
        subscribe("dead-session", dead)
        subscribe("live-session", live)
        uri = "brain://group-ii/working-memory/context/current"
        # Should not raise even though 'dead' raises
        notify_all(uri)
        live.assert_called_once_with(uri)

    def test_unsubscribe_nonexistent_is_noop(self) -> None:
        """Unsubscribing an unknown session_id is a no-op (does not raise)."""
        unsubscribe("does-not-exist")  # must not raise

    def test_subscribe_replaces_existing_callback(self) -> None:
        """Re-subscribing with the same session_id replaces the previous callback."""
        cb_old = Mock()
        cb_new = Mock()
        subscribe("session-1", cb_old)
        subscribe("session-1", cb_new)
        notify_all("brain://group-ii/working-memory/context/current")
        cb_old.assert_not_called()
        cb_new.assert_called_once()

    def test_notify_with_no_subscribers_is_noop(self) -> None:
        """notify_all with no registered subscribers does not raise."""
        notify_all("brain://group-ii/working-memory/context/current")

    def test_uri_passed_verbatim_to_callback(self) -> None:
        """The exact URI string passed to notify_all is forwarded to the callback."""
        cb = Mock()
        subscribe("session-1", cb)
        custom_uri = "brain://group-ii/working-memory/items/abc-123"
        notify_all(custom_uri)
        cb.assert_called_once_with(custom_uri)
