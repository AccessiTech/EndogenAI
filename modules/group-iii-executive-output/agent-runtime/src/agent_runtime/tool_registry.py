"""tool_registry.py — Dynamic tool/skill discovery and registration.

Discovers tools by fetching /.well-known/agent-card.json from configured endpoints.
Maintains health status; filters unavailable tools before decomposition.

Neuroanatomical analogue:
  - Superior parietal cortex: maps available effectors (registered tools)
    to capabilities; routes motor commands to them.
  - Cerebellar cortico-nuclear loop: validates that decomposed pipeline steps
    can actually be executed (no unavailable tools).
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path  # noqa: TC003 — used at runtime for Path(persistence_path)
from typing import Any

import httpx
import structlog

from agent_runtime.models import SkillEntry

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class ToolRegistry:
    """Dynamic tool/skill registry with A2A agent-card discovery.

    On startup: probes each configured endpoint for /.well-known/agent-card.json.
    Periodic health checks: marks unavailable tools to prevent dead dispatch.
    """

    def __init__(
        self,
        discovery_targets: list[str] | None = None,
        health_check_interval_seconds: float = 30.0,
        persistence_path: Path | None = None,
    ) -> None:
        self._targets = discovery_targets or []
        self._health_interval = health_check_interval_seconds
        self._persistence_path = persistence_path
        self._skills: dict[str, SkillEntry] = {}
        self._health_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Discover tools from all configured endpoints and start health checks."""
        await self._discover_all()
        if self._persistence_path and self._persistence_path.exists():
            await self._load_persisted()
        self._health_task = asyncio.create_task(self._health_loop())
        logger.info("tool_registry.started", num_skills=len(self._skills))

    async def stop(self) -> None:
        """Stop the health check background task."""
        if self._health_task:
            self._health_task.cancel()

    def register(self, entry: SkillEntry) -> None:
        """Manually register a skill."""
        self._skills[entry.skill_id] = entry
        logger.info("tool_registry.registered", skill_id=entry.skill_id)

    def get_healthy_skills(self) -> list[SkillEntry]:
        """Return list of currently healthy registered skills."""
        return [s for s in self._skills.values() if s.healthy]

    def get_all_skills(self) -> list[SkillEntry]:
        """Return all registered skills regardless of health."""
        return list(self._skills.values())

    def get_skill(self, skill_id: str) -> SkillEntry | None:
        """Look up a skill by ID."""
        return self._skills.get(skill_id)

    async def _discover_all(self) -> None:
        """Fetch agent-card.json from all discovery targets."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            tasks = [self._probe_endpoint(client, url) for url in self._targets]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _probe_endpoint(
        self, client: httpx.AsyncClient, base_url: str
    ) -> None:
        """Fetch /.well-known/agent-card.json from a single endpoint."""
        try:
            resp = await client.get(f"{base_url}/.well-known/agent-card.json")
            resp.raise_for_status()
            card: dict[str, Any] = resp.json()
            for skill_data in card.get("skills", []):
                entry = SkillEntry(
                    skill_id=skill_data.get("id", f"unknown-{base_url}"),
                    name=skill_data.get("name", ""),
                    description=skill_data.get("description", ""),
                    agent_url=card.get("endpoints", {}).get("a2a", base_url),
                    capabilities=card.get("capabilities", []),
                    healthy=True,
                )
                self._skills[entry.skill_id] = entry
            logger.info(
                "tool_registry.discovered",
                url=base_url,
                skills_found=len(card.get("skills", [])),
            )
        except Exception as exc:
            logger.debug("tool_registry.probe_failed", url=base_url, error=str(exc))

    async def _health_loop(self) -> None:
        """Periodic health check loop."""
        while True:
            await asyncio.sleep(self._health_interval)
            await self._run_health_checks()

    async def _run_health_checks(self) -> None:
        """Ping each registered skill's agent URL."""
        async with httpx.AsyncClient(timeout=3.0) as client:
            for skill in self._skills.values():
                try:
                    resp = await client.get(f"{skill.agent_url}/health")
                    skill.healthy = resp.status_code < 500
                except Exception:
                    skill.healthy = False
                    logger.debug("tool_registry.unhealthy", skill_id=skill.skill_id)

    async def _load_persisted(self) -> None:
        """Load persisted tool registry from disk (JSON)."""
        if self._persistence_path and self._persistence_path.exists():
            try:
                data = json.loads(self._persistence_path.read_text())
                for entry_data in data.get("skills", []):
                    entry = SkillEntry.model_validate(entry_data)
                    if entry.skill_id not in self._skills:
                        self._skills[entry.skill_id] = entry
                logger.info("tool_registry.loaded_from_disk")
            except Exception as exc:
                logger.warning("tool_registry.load_error", error=str(exc))
