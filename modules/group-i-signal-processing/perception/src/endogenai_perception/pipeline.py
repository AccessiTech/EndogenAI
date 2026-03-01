"""
Perception pipeline for the brAIn Perception Layer.

PerceptionPipeline orchestrates:
  1. Feature extraction from filtered signals (entities, intent, summary)
  2. Language understanding via LiteLLM (text modality)
  3. Multimodal fusion (scene parsing for image/audio)
  4. Embedding of perceptual representations into brain.perception

Analogous to the association cortices: this is where raw signals become
structured semantic representations.

Usage
-----
>>> from endogenai_vector_store import ChromaAdapter, ChromaConfig, EmbeddingConfig
>>> adapter = ChromaAdapter(
...     config=ChromaConfig(mode="http", host="localhost", port=8000),
...     embedding_config=EmbeddingConfig(provider="ollama", model="nomic-embed-text"),
... )
>>> pipeline = PerceptionPipeline(vector_store=adapter)
>>> result = await pipeline.process(filtered_signal)
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import litellm
import structlog
from endogenai_vector_store import VectorStoreAdapter
from endogenai_vector_store.models import MemoryItem, MemoryType, UpsertRequest

from endogenai_perception.imports import Signal
from endogenai_perception.models import PerceptionResult, PerceptualFeatures

log = structlog.get_logger(__name__)

_COLLECTION = "brain.perception"

_FEATURE_EXTRACTION_PROMPT = """\
You are a perceptual feature extractor.  Given the signal below, extract:
- entities: list of named entities, objects, or key concepts (max 10)
- intent: one of question|command|observation|statement|unknown
- summary: one sentence summarising the signal content
- language: BCP-47 language tag (e.g. en, fr) — text only, else null

Respond ONLY with a JSON object with keys: entities, intent, summary, language.

Signal modality: {modality}
Signal content: {content}
"""


class PerceptionPipeline:
    """
    Signal perception pipeline.

    Parameters
    ----------
    vector_store:
        Initialised VectorStoreAdapter instance (ChromaAdapter or QdrantAdapter).
        Must have the brain.perception collection available.
    llm_model:
        LiteLLM model string for language understanding inference
        (default: ``"ollama/llama3.2"``).
    embed_model:
        LiteLLM model string for embedding (default: ``"ollama/nomic-embed-text"``).
    module_id:
        Canonical module id for logging.
    """

    def __init__(
        self,
        vector_store: VectorStoreAdapter,
        llm_model: str = "ollama/llama3.2",
        embed_model: str = "ollama/nomic-embed-text",
        module_id: str = "perception",
    ) -> None:
        self._vs = vector_store
        self._llm_model = llm_model
        self._embed_model = embed_model
        self._module_id = module_id
        self._logger = log.bind(module_id=module_id)

    async def process(self, signal: Signal) -> PerceptionResult:
        """
        Process a single signal through the full perception pipeline.

        Steps
        -----
        1. Extract perceptual features via LiteLLM (text) or heuristics (other).
        2. Build the embedding text from extracted features.
        3. Upsert the feature record into brain.perception.
        4. Return a PerceptionResult.

        Parameters
        ----------
        signal:
            The filtered signal to perceive (from the Attention & Filtering Layer).

        Returns
        -------
        PerceptionResult
            Extracted features and the vector store embedding id.
        """
        self._logger.info("perception_processing", signal_id=signal.id)

        features = await self._extract_features(signal)
        embedding_text = self._build_embedding_text(features)
        features.raw_embedding_text = embedding_text

        embedding_id = await self._embed_and_store(signal, features, embedding_text)

        self._logger.info(
            "perception_complete",
            signal_id=signal.id,
            embedding_id=embedding_id,
        )

        return PerceptionResult(
            signal_id=signal.id,
            features=features,
            embedding_id=embedding_id,
            embedding_model=self._embed_model,
        )

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    async def _extract_features(self, signal: Signal) -> PerceptualFeatures:
        """Extract perceptual features appropriate to the signal modality."""
        if signal.modality.value == "text":
            return await self._extract_text_features(signal)
        if signal.modality.value in ("image", "audio"):
            return self._extract_media_features(signal)
        return self._extract_structured_features(signal)

    async def _extract_text_features(self, signal: Signal) -> PerceptualFeatures:
        """Use LiteLLM to extract semantic features from a text signal."""
        content = str(signal.payload) if signal.payload is not None else ""

        prompt = _FEATURE_EXTRACTION_PROMPT.format(
            modality=signal.modality.value,
            content=content[:2000],  # guard against huge payloads
        )

        try:
            response = await litellm.acompletion(
                model=self._llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=256,
            )
            raw_json = response.choices[0].message.content or "{}"
            parsed: dict[str, Any] = json.loads(raw_json)
        except Exception as exc:  # noqa: BLE001
            self._logger.warning(
                "llm_extraction_failed", signal_id=signal.id, error=str(exc)
            )
            parsed = {}

        return PerceptualFeatures(
            signal_id=signal.id,
            modality=signal.modality.value,
            entities=parsed.get("entities") or [],
            intent=parsed.get("intent"),
            summary=parsed.get("summary"),
            language=parsed.get("language"),
        )

    def _extract_media_features(self, signal: Signal) -> PerceptualFeatures:
        """Heuristic feature extraction for image/audio signals."""
        return PerceptualFeatures(
            signal_id=signal.id,
            modality=signal.modality.value,
            scene={"raw": True, "encoding": signal.encoding or "unknown"},
            summary=f"Raw {signal.modality.value} signal received at {signal.timestamp}",
        )

    def _extract_structured_features(self, signal: Signal) -> PerceptualFeatures:
        """Heuristic feature extraction for structured/sensor/event signals."""
        payload_keys: list[str] = []
        if isinstance(signal.payload, dict):
            payload_keys = list(signal.payload.keys())

        return PerceptualFeatures(
            signal_id=signal.id,
            modality=signal.modality.value,
            entities=payload_keys,
            intent="observation",
            summary=f"{signal.type} signal with {len(payload_keys)} fields",
        )

    # ------------------------------------------------------------------
    # Embedding and storage
    # ------------------------------------------------------------------

    @staticmethod
    def _build_embedding_text(features: PerceptualFeatures) -> str:
        """Build a text string to embed from extracted features."""
        parts: list[str] = []
        if features.summary:
            parts.append(features.summary)
        if features.entities:
            parts.append("Entities: " + ", ".join(features.entities))
        if features.intent:
            parts.append(f"Intent: {features.intent}")
        return " | ".join(parts) if parts else f"signal:{features.signal_id}"

    async def _embed_and_store(
        self,
        signal: Signal,
        features: PerceptualFeatures,
        embedding_text: str,
    ) -> str:
        """Embed the feature text and upsert into brain.perception."""
        from datetime import UTC, datetime

        embedding_id = str(uuid.uuid4())

        item = MemoryItem(
            id=embedding_id,
            collection_name=_COLLECTION,
            content=embedding_text,
            type=MemoryType.SHORT_TERM,
            source_module=self._module_id,
            created_at=datetime.now(tz=UTC).isoformat(),
            metadata={
                "signal_id": signal.id,
                "modality": features.modality,
                "intent": features.intent or "",
                "language": features.language or "",
                "session_id": signal.session_id or "",
                "signal_type": signal.type,
            },
            importance_score=signal.priority / 10.0,
        )

        await self._vs.upsert(UpsertRequest(collection_name=_COLLECTION, items=[item]))
        return embedding_id
