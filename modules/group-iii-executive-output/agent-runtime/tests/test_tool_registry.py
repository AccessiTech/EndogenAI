"""Tests for ToolRegistry — agent-card discovery, health checks, registration."""
from __future__ import annotations

import json
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



class TestStartStopAndHealthCheck:
    async def test_stop_cancels_health_task(self, registry: ToolRegistry, sample_skill_entry: "SkillEntry") -> None:
        """stop() cancels the running health task."""
        registry.register(sample_skill_entry)
        import asyncio

        async def _fake_loop() -> None:
            try:
                await asyncio.sleep(9999)
            except asyncio.CancelledError:
                raise

        registry._health_task = asyncio.create_task(_fake_loop())
        await asyncio.sleep(0)  # let the task actually start waiting
        await registry.stop()
        # Give the event loop a turn to process the CancelledError
        try:
            await asyncio.wait_for(asyncio.shield(registry._health_task), timeout=1.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        assert registry._health_task.done()

    async def test_stop_when_no_task(self, registry: ToolRegistry) -> None:
        """stop() is safe when no health task is running."""
        await registry.stop()  # should not raise


class TestRunHealthChecks:
    async def test_health_check_marks_healthy(self, registry: ToolRegistry, sample_skill_entry: "SkillEntry") -> None:
        registry.register(sample_skill_entry)
        with respx.mock:
            respx.get("http://localhost:9999/health").mock(
                return_value=httpx.Response(200)
            )
            await registry._run_health_checks()
        skill = registry.get_skill("skill.test")
        assert skill is not None
        assert skill.healthy is True

    async def test_health_check_marks_unhealthy_on_error(self, registry: ToolRegistry, sample_skill_entry: "SkillEntry") -> None:
        registry.register(sample_skill_entry)
        with respx.mock:
            respx.get("http://localhost:9999/health").mock(
                side_effect=httpx.ConnectError("refused")
            )
            await registry._run_health_checks()
        skill = registry.get_skill("skill.test")
        assert skill is not None
        assert skill.healthy is False


class TestLoadPersisted:
    async def test_load_persisted_adds_skills(self, tmp_path: Path) -> None:
        from agent_runtime.models import SkillEntry
        skill = SkillEntry(
            skill_id="skill.persisted",
            name="Persisted Skill",
            description="From disk",
            agent_url="http://localhost:8161",
            capabilities=["test"],
            healthy=True,
        )
        persistence_path = tmp_path / "registry.json"
        persistence_path.write_text(json.dumps({"skills": [skill.model_dump(mode="json")]}))
        registry = ToolRegistry(
            persistence_path=persistence_path,
            health_check_interval_seconds=999,
        )
        await registry._load_persisted()
        assert registry.get_skill("skill.persisted") is not None

    async def test_load_persisted_skips_duplicates(self, tmp_path: Path) -> None:
        from agent_runtime.models import SkillEntry
        skill = SkillEntry(
            skill_id="skill.existing",
            name="Existing Skill",
            description="Already in registry",
            agent_url="http://localhost:8161",
            capabilities=[],
            healthy=True,
        )
        persistence_path = tmp_path / "registry.json"
        persistence_path.write_text(json.dumps({"skills": [skill.model_dump(mode="json")]}))
        registry = ToolRegistry(persistence_path=persistence_path)
        registry.register(skill)
        await registry._load_persisted()
        # Should still only have one entry
        skills = [s for s in registry.get_all_skills() if s.skill_id == "skill.existing"]
        assert len(skills) == 1

    async def test_load_persisted_handles_corrupt_json(self, tmp_path: Path) -> None:
        persistence_path = tmp_path / "registry.json"
        persistence_path.write_text("not valid json")
        registry = ToolRegistry(persistence_path=persistence_path)
        await registry._load_persisted()  # should not raise
