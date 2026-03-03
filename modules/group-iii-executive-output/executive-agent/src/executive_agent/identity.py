"""identity.py — Agent self-model management for executive-agent.

Loads identity.config.json at startup. Provides get_self_model() and
append-only update_self_model() writes to the brain.executive-agent vector store.

Neuroanatomical analogue:
  - vmPFC / mPFC (BA 10–12): self-referential processing, maintaining a coherent
    model of the self over time (reconsolidation analogue: always append, never overwrite).
  - Frontal lobe identity: core values, agent name, recent achievements.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from executive_agent.models import IdentityConfig, SelfModel

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "identity.config.json"


class IdentityManager:
    """Manages the agent's self-model.

    - Loads IdentityConfig from identity.config.json on construction.
    - Stores identity deltas in brain.executive-agent collection (append-only).
    - Returns SelfModel composed from config + recent vector store items.
    """

    def __init__(
        self,
        config: IdentityConfig,
        store: Any,  # VectorStoreAdapter — typed as Any to avoid circular import
    ) -> None:
        self._config = config
        self._store = store
        self._recent_achievements: list[str] = []
        self._deltas: list[dict[str, Any]] = []
        logger.info("identity.loaded", agent_name=config.agent_name)

    @classmethod
    def from_config_file(
        cls,
        store: Any,
        config_path: Path = _CONFIG_PATH,
    ) -> IdentityManager:
        """Load IdentityConfig from file and return an IdentityManager."""
        with open(config_path) as fh:
            raw = json.load(fh)
        config = IdentityConfig.model_validate(raw)
        return cls(config=config, store=store)

    def get_self_model(self) -> SelfModel:
        """Return the current SelfModel.

        Composed from:
          1. Static identity config (agent_name, core_values, etc.)
          2. In-memory deltas accumulated since startup
          3. Recent achievements (populated from MotorFeedback events)
        """
        return SelfModel(
            agent_name=self._config.agent_name,
            agent_version=self._config.agent_version,
            core_values=self._config.core_values,
            max_active_goals=self._config.max_active_goals,
            deliberation_cycle_ms=self._config.deliberation_cycle_ms,
            recent_achievements=list(self._recent_achievements[-10:]),
            deltas=list(self._deltas[-20:]),
        )

    async def update_self_model(self, delta: dict[str, Any]) -> SelfModel:
        """Append an identity delta to the self-model (reconsolidation analogue).

        Never overwrites existing identity state — always appends to history.
        Writes a new item to brain.executive-agent via the vector store adapter.
        """
        delta["_updated_at"] = datetime.now(UTC).isoformat()
        self._deltas.append(delta)

        # Write to vector store (append-only)
        text_repr = f"Identity delta: {json.dumps(delta)}"
        try:
            await self._store.upsert(
                collection_name=self._config.identity_collection_name,
                texts=[text_repr],
                metadatas=[{"type": "identity_delta", "agent": self._config.agent_name}],
            )
            logger.info("identity.delta_stored", delta_keys=list(delta.keys()))
        except Exception as exc:
            logger.warning("identity.store_error", error=str(exc))

        return self.get_self_model()

    def record_achievement(self, description: str) -> None:
        """Record a recent goal-completion achievement in the in-memory ring buffer."""
        self._recent_achievements.append(description)
        if len(self._recent_achievements) > 50:
            self._recent_achievements.pop(0)

    @property
    def config(self) -> IdentityConfig:
        return self._config


def load_identity_config(config_path: Path = _CONFIG_PATH) -> IdentityConfig:
    """Load IdentityConfig from a JSON file. Raises FileNotFoundError or ValidationError."""
    if not config_path.exists():
        raise FileNotFoundError(f"identity.config.json not found at {config_path}")
    with open(config_path) as fh:
        raw = json.load(fh)
    return IdentityConfig.model_validate(raw)
