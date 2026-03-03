"""test_channel_selector.py — Unit tests for channel selection logic."""
from __future__ import annotations

from motor_output.channel_selector import select_channel
from motor_output.models import ActionSpec, ChannelType


def _spec(type_: str, params: dict | None = None, channel: ChannelType | None = None) -> ActionSpec:
    return ActionSpec(type=type_, channel=channel, params=params or {})


def test_explicit_channel_respected() -> None:
    spec = ActionSpec(
        type="anything",
        channel=ChannelType.FILE,
        params={"channel": "file"},
    )
    assert select_channel(spec) == ChannelType.FILE


def test_param_a2a_url_selects_a2a() -> None:
    spec = _spec("task", params={"a2a_url": "http://service/tasks"})
    assert select_channel(spec) == ChannelType.A2A


def test_param_path_selects_file() -> None:
    spec = _spec("store", params={"path": "/tmp/out.txt"})
    assert select_channel(spec) == ChannelType.FILE


def test_type_hint_render() -> None:
    spec = _spec("render_summary")
    assert select_channel(spec) == ChannelType.RENDER


def test_type_hint_write_file() -> None:
    spec = _spec("write_file")
    assert select_channel(spec) == ChannelType.FILE


def test_type_hint_delegate() -> None:
    spec = _spec("delegate_to_agent")
    assert select_channel(spec) == ChannelType.A2A


def test_default_http() -> None:
    spec = _spec("unknown_action")
    assert select_channel(spec) == ChannelType.HTTP


def test_url_param_selects_http() -> None:
    spec = _spec("call", params={"url": "https://api.example.com"})
    assert select_channel(spec) == ChannelType.HTTP
