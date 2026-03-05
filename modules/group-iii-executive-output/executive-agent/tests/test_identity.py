"""tests/test_identity.py — Unit tests for IdentityManager.

Tests identity configuration loading, self-model composition,
and the append-only update_self_model rule.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from executive_agent.identity import IdentityManager, load_identity_config
from executive_agent.models import IdentityConfig

if TYPE_CHECKING:
    from pathlib import Path


def _make_store() -> MagicMock:
    store = MagicMock()
    store.upsert = AsyncMock()
    return store


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "identity.config.json"
    p.write_text(json.dumps(data))
    return p


SAMPLE_CONFIG = {
    "agentName": "frankenbrAIn",
    "agentVersion": "0.1.0",
    "coreValues": ["honesty", "helpfulness"],
    "deliberationCycleMs": 1000,
    "maxActiveGoals": 5,
    "goalCapacityEnforcement": True,
    "identityCollectionName": "brain.executive-agent",
    "workingMemoryModule": "http://localhost:8141",
    "affectiveModule": "http://localhost:8151",
    "agentRuntimeModule": "http://localhost:8162",
}


class TestLoadIdentityConfig:
    def test_loads_valid_config(self, tmp_path: Path) -> None:
        cfg_path = _write_config(tmp_path, SAMPLE_CONFIG)
        cfg = load_identity_config(cfg_path)
        assert cfg.agent_name == "frankenbrAIn"
        assert "honesty" in cfg.core_values

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_identity_config(tmp_path / "missing.json")

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        import json

        p = tmp_path / "bad.json"
        p.write_text("{broken")
        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_identity_config(p)


class TestIdentityManager:
    def _make_manager(self) -> IdentityManager:
        cfg = IdentityConfig.model_validate(SAMPLE_CONFIG)
        store = _make_store()
        return IdentityManager(config=cfg, store=store)

    def test_get_self_model_returns_core_values(self) -> None:
        mgr = self._make_manager()
        model = mgr.get_self_model()
        assert "honesty" in model.core_values
        assert model.agent_name == "frankenbrAIn"

    async def test_update_self_model_is_append_only(self) -> None:
        mgr = self._make_manager()
        delta = {"capability": "advanced-reasoning", "source": "task-reflection"}
        model = await mgr.update_self_model(delta)
        # delta should appear in model.deltas (append-only)
        assert any("capability" in str(d) for d in model.deltas)
        assert len(model.deltas) == 1

    async def test_update_self_model_persists_to_store(self) -> None:
        mgr = self._make_manager()
        await mgr.update_self_model({"capability": "test"})
        mgr._store.upsert.assert_called_once()

    def test_record_achievement_stores_in_ring_buffer(self) -> None:
        mgr = self._make_manager()
        for i in range(3):
            mgr.record_achievement(f"achievement-{i}")
        # Only most recent achievements are shown (10 in recent_achievements)
        model = mgr.get_self_model()
        assert len(model.recent_achievements) == 3

    def test_ring_buffer_caps_at_fifty(self) -> None:
        mgr = self._make_manager()
        for i in range(60):
            mgr.record_achievement(f"achievement-{i}")
        assert len(mgr._recent_achievements) == 50

