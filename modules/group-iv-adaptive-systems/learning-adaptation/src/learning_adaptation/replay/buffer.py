"""buffer.py — ChromaDB-backed episodic replay buffer with priority sampling.

Priority = |reward|. Rolling eviction when size > max_size.
Uses endogenai_vector_store.ChromaAdapter — never imports chromadb directly.

Neuroanatomical analogue: hippocampal episodic memory replay driving
basal ganglia dopamine-modulated policy updates.
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import TYPE_CHECKING, Any

import structlog
from endogenai_vector_store.models import (
    DeleteRequest,
    MemoryItem,
    MemoryType,
    QueryRequest,
    UpsertRequest,
)

if TYPE_CHECKING:
    from endogenai_vector_store import ChromaAdapter

from learning_adaptation.models import LearningAdaptationEpisode, ReplayBufferStats

COLLECTION_NAME = "brain.learning-adaptation"

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def _episode_to_memory_item(episode: LearningAdaptationEpisode) -> MemoryItem:
    """Convert a LearningAdaptationEpisode to a MemoryItem for ChromaDB storage."""
    now = datetime.datetime.now(datetime.UTC).isoformat()
    content = (
        f"task_type={episode.task_type} reward={episode.reward:.4f} "
        f"done={episode.done} boundary={episode.episode_boundary}"
    )
    priority = episode.priority if episode.priority else abs(episode.reward)
    return MemoryItem(
        id=episode.episode_id,
        collection_name=COLLECTION_NAME,
        content=content,
        type=MemoryType.EPISODIC,
        source_module="learning-adaptation",
        importance_score=min(1.0, priority),
        created_at=episode.timestamp or now,
        metadata={
            "episode_id": episode.episode_id,
            "task_type": episode.task_type,
            "reward": episode.reward,
            "priority": priority,
            "done": episode.done,
            "episode_boundary": episode.episode_boundary,
            "observation": json.dumps(episode.observation),
            "action": json.dumps(episode.action),
            "next_observation": json.dumps(episode.next_observation),
            "goal_id": episode.goal_id or "",
            "session_id": episode.session_id or "",
        },
        tags=["episode", episode.task_type],
    )


def _memory_item_to_episode(item: MemoryItem) -> LearningAdaptationEpisode:
    """Reconstruct a LearningAdaptationEpisode from a MemoryItem."""
    meta = item.metadata
    priority = float(meta.get("priority", abs(float(meta.get("reward", 0.0)))))
    observation: dict[str, Any] = {}
    action: dict[str, Any] = {}
    next_observation: dict[str, Any] = {}
    try:
        obs_raw = meta.get("observation", "{}")
        observation = json.loads(obs_raw) if isinstance(obs_raw, str) else obs_raw
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        act_raw = meta.get("action", "{}")
        action = json.loads(act_raw) if isinstance(act_raw, str) else act_raw
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        nobs_raw = meta.get("next_observation", "{}")
        next_observation = json.loads(nobs_raw) if isinstance(nobs_raw, str) else nobs_raw
    except (json.JSONDecodeError, TypeError):
        pass
    return LearningAdaptationEpisode(
        episode_id=str(meta.get("episode_id", item.id)),
        timestamp=item.created_at,
        episode_boundary=str(meta.get("episode_boundary", "bdi_cycle")),
        observation=observation,
        action=action,
        reward=float(meta.get("reward", 0.0)),
        next_observation=next_observation,
        done=bool(meta.get("done", False)),
        task_type=str(meta.get("task_type", "default")),
        priority=priority,
        goal_id=str(meta.get("goal_id", "")) or None,
        session_id=str(meta.get("session_id", "")) or None,
    )


class ReplayBuffer:
    """ChromaDB-backed episodic replay buffer with priority sampling.

    Priority = |reward|. Rolling eviction when size > max_size.
    Uses endogenai_vector_store.ChromaAdapter — never imports chromadb directly.
    """

    def __init__(self, adapter: ChromaAdapter, max_size: int = 1000) -> None:
        self._adapter = adapter
        self._max_size = max_size

    async def add(self, episode: LearningAdaptationEpisode) -> None:
        """Persist an episode to the ChromaDB replay buffer.

        Automatically evicts lowest-priority records when over max_size.
        """
        item = _episode_to_memory_item(episode)
        req = UpsertRequest(
            collection_name=COLLECTION_NAME,
            items=[item],
        )
        await self._adapter.upsert(req)
        logger.debug(
            "replay_buffer.add",
            episode_id=episode.episode_id,
            task_type=episode.task_type,
        )

        current_size = await self.size()
        if current_size > self._max_size:
            evict_count = current_size - self._max_size
            await self.evict_lowest(evict_count)

    async def sample(self, n: int) -> list[LearningAdaptationEpisode]:
        """Return up to n episodes sorted by |priority| descending.

        Oversamples (up to 100 candidates) so that the final top-N sort by
        priority reflects true high-importance episodes rather than being
        limited to whatever the semantic similarity query returns.
        """
        oversample = max(100, n * 10)
        req = QueryRequest(
            collection_name=COLLECTION_NAME,
            query_text="episode reward task_type",
            n_results=oversample,
        )
        try:
            resp = await self._adapter.query(req)
            episodes = [_memory_item_to_episode(r.item) for r in resp.results]
            episodes.sort(key=lambda e: e.priority, reverse=True)
            return episodes[:n]
        except Exception:
            logger.exception("replay_buffer.sample.error")
            return []

    async def evict_lowest(self, n: int) -> None:
        """Remove the n lowest-priority episodes from the buffer."""
        if n <= 0:
            return
        req = QueryRequest(
            collection_name=COLLECTION_NAME,
            query_text="episode",
            n_results=min(self._max_size + n, 100),
        )
        try:
            resp = await self._adapter.query(req)
            items_sorted = sorted(resp.results, key=lambda r: r.item.importance_score)
            to_evict = items_sorted[:n]
            if to_evict:
                ids_to_delete = [r.item.id for r in to_evict]
                del_req = DeleteRequest(
                    collection_name=COLLECTION_NAME,
                    ids=ids_to_delete,
                )
                await self._adapter.delete(del_req)
                logger.debug("replay_buffer.evict", count=len(ids_to_delete))
        except Exception:
            logger.exception("replay_buffer.evict.error")

    async def stats(self) -> ReplayBufferStats:
        """Return summary statistics about the replay buffer."""
        try:
            req = QueryRequest(
                collection_name=COLLECTION_NAME,
                query_text="episode",
                n_results=100,
            )
            resp = await self._adapter.query(req)
            total = len(resp.results)
            if total == 0:
                return ReplayBufferStats(total_episodes=0, mean_reward=0.0, top_task_type=None)

            rewards = [float(r.item.metadata.get("reward", 0.0)) for r in resp.results]
            mean_reward = sum(rewards) / total

            task_counts: dict[str, int] = {}
            for r in resp.results:
                tt = str(r.item.metadata.get("task_type", "default"))
                task_counts[tt] = task_counts.get(tt, 0) + 1
            top_task_type = max(task_counts, key=lambda k: task_counts[k]) if task_counts else None

            return ReplayBufferStats(
                total_episodes=total,
                mean_reward=mean_reward,
                top_task_type=top_task_type,
            )
        except Exception:
            logger.exception("replay_buffer.stats.error")
            return ReplayBufferStats(total_episodes=0, mean_reward=0.0, top_task_type=None)

    async def size(self) -> int:
        """Return the current number of episodes in the buffer."""
        try:
            req = QueryRequest(
                collection_name=COLLECTION_NAME,
                query_text="episode",
                n_results=100,
            )
            resp = await self._adapter.query(req)
            return len(resp.results)
        except Exception:
            return 0

    @staticmethod
    def new_episode_id() -> str:
        """Generate a new UUID v4 episode ID."""
        return str(uuid.uuid4())
