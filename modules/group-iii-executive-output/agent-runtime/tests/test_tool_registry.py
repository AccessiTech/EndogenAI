"""Tests for ToolRegistry — agent-card discovery, health checks, registration."""
from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
import respx

if TYPE_CHECKING:
    from agent_runtime.models import SkillEntry

from agent_runtime.tool_registry import ToolRegistry


@pytest.fixture
def registry(tmp_path: pytest.TempPathFactory) -> ToolRegistry:
    return ToolRegistry(
        discovery_targets=["http://localhost:8161"],
        health_check_interval_seconds=999,
        persistence_path=str(tmp_path / "registry.json"),  # type: ignore[operator]
    )


class TestManualRegistration:
    def test_register_and_retrieve(
        self, registry: ToolRegistry, sample_skill_entry: SkillEntry
    ) -> None:
        registry.register(sample_skill_entry)
        skills = registry.get_all_skills()
        assert any(s.skill_id == "skill.test" for s in skills)

    def test_no_duplicate_registration(
        self, registry: ToolRegistry, sample_skill_entry: SkillEntry
    ) -> None:
        registry.register(sample_skill_entry)
        registry.register(sample_skill_entry)
        skills = [s for s in registry.get_all_skills() if s.skill_id == "skill.test"]
        assert len(skills) == 1


class TestAgentCardProbe:
    async def test_probe_agent_card(self, registry: ToolRegistry) -> None:
        card = {
            "name": "test-agent",
            "skills": [
                {
                    "id": "skill.discovered",
                    "name": "Discovered Skill",
                    "description": "Found via probe",
                    "capabilities": ["test"],
                }
            ],
            "endpoints": {
                "a2a": "http://localhost:8161",
                "mcp": "http://localhost:8261",
            },
        }
        with respx.mock:
            respx.get("http://localhost:8161/.well-known/agent-card.json").mock(
                return_value=httpx.Response(200, json=card)
            )
            async with httpx.AsyncClient() as client:
                await registry._probe_endpoint(client, "http://localhost:8161")

        assert any(s.skill_id == "skill.discovered" for s in registry.get_all_skills())

    async def test_probe_skips_on_404(self, registry: ToolRegistry) -> None:
        with respx.mock:
            respx.get("http://localhost:8161/.well-known/agent-card.json").mock(
                return_value=httpx.Response(404)
            )
            async with httpx.AsyncClient() as client:
                await registry._probe_endpoint(client, "http://localhost:8161")

        # No skills registered on 404
        assert registry.get_all_skills() == []

    async def test_probe_skips_on_connection_error(
        self, registry: ToolRegistry
    ) -> None:
        with respx.mock:
            respx.get("http://localhost:8161/.well-known/agent-card.json").mock(
                side_effect=httpx.ConnectError("refused")
            )
            async with httpx.AsyncClient() as client:
                await registry._probe_endpoint(client, "http://localhost:8161")

        assert registry.get_all_skills() == []


class TestGetSkill:
    def test_get_existing_skill(
        self, registry: ToolRegistry, sample_skill_entry: SkillEntry
    ) -> None:
        registry.register(sample_skill_entry)
        found = registry.get_skill("skill.test")
        assert found is not None
        assert found.name == "Test Skill"

    def test_get_missing_skill_returns_none(self, registry: ToolRegistry) -> None:
        result = registry.get_skill("skill.does.not.exist")
        assert result is None
