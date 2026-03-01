"""Core processing pipeline for the perception module.

Pipeline stages
---------------
1. Feature extraction
   - Text   : LiteLLM NLP (entities, intent, key phrases)
   - Image  : pass-through with metadata
   - Audio  : pass-through with metadata
2. Pattern recognition  — classifies the signal into a semantic pattern.
3. Multimodal fusion    — merges concurrent signals (stub; single-signal merge).
4. Embedding            — upserts extracted representation into ``brain.perception``
                          via ``endogenai_vector_store.ChromaAdapter`` (opt-in via
                          ``PERCEPTION_ENABLE_EMBEDDING=true``).

Notes
-----
* LiteLLM is used for ALL inference — never call Ollama/OpenAI SDKs directly.
* ChromaDB is accessed exclusively through ``endogenai_vector_store.ChromaAdapter``.
* Embedding is disabled by default so unit tests require no external services.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import jsonschema
import structlog

from perception import config
from perception.models import (
    Modality,
    PerceptionResult,
    Signal,
    TextFeatures,
)

log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_SCHEMA_DIR = Path(__file__).parent / "schemas"


# ---------------------------------------------------------------------------
# Schema loading & validation
# ---------------------------------------------------------------------------


def _load_schema(filename: str) -> dict[str, Any]:
    with (_SCHEMA_DIR / filename).open() as fh:
        return cast("dict[str, Any]", json.load(fh))


_SIGNAL_SCHEMA: dict[str, Any] = _load_schema("signal.schema.json")
_MCP_SCHEMA: dict[str, Any] = _load_schema("mcp-context.schema.json")
_A2A_SCHEMA: dict[str, Any] = _load_schema("a2a-message.schema.json")


def check_payload_size(data: bytes) -> None:
    if len(data) > config.MAX_PAYLOAD_BYTES:
        raise ValueError(
            f"Payload {len(data)} bytes exceeds limit {config.MAX_PAYLOAD_BYTES} bytes"
        )


def validate_mcp(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=_MCP_SCHEMA)


def validate_a2a(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=_A2A_SCHEMA)


# ---------------------------------------------------------------------------
# Pattern recognition — simple rule-based classifier
# ---------------------------------------------------------------------------

_QUESTION_WORDS = {"what", "who", "where", "when", "why", "how", "is", "are", "can", "does"}
_COMMAND_WORDS = {"please", "do", "run", "start", "stop", "create", "delete", "update", "get"}
_GREETING_WORDS = {"hello", "hi", "hey", "greetings", "good morning", "good afternoon"}
_ERROR_WORDS = {"error", "exception", "fail", "failure", "crash", "bug", "issue", "problem"}


def _classify_pattern(signal: Signal) -> str:
    """Rule-based pattern classifier (text modality only; others return 'data')."""
    if signal.modality != "text":
        return "data"
    payload = signal.payload
    if not isinstance(payload, str):
        return "data"
    lower = payload.lower().strip()
    if any(lower.startswith(w) for w in _QUESTION_WORDS) or lower.endswith("?"):
        return "question"
    if any(w in lower for w in _ERROR_WORDS):
        return "error"
    if any(lower.startswith(w) for w in _GREETING_WORDS):
        return "greeting"
    if any(lower.startswith(w) for w in _COMMAND_WORDS):
        return "command"
    return "statement"


# ---------------------------------------------------------------------------
# LiteLLM feature extraction
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = (
    "Extract features from the following text and return a JSON object with exactly these keys:\n"
    '- "entities": array of named entity strings\n'
    '- "intent": single string describing the primary intent\n'
    '- "key_phrases": array of up to 5 key phrase strings\n'
    "Return only the JSON object, no markdown, no extra text."
)


async def _extract_text_features_llm(text: str) -> TextFeatures:
    """Call LiteLLM to extract entities, intent, and key phrases from *text*."""
    import litellm  # noqa: PLC0415

    try:
        response = await litellm.acompletion(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": _EXTRACTION_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            max_tokens=512,
        )
        raw: str = response.choices[0].message.content or "{}"
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        features_data = json.loads(raw)
        return TextFeatures(
            entities=features_data.get("entities", []),
            intent=features_data.get("intent"),
            key_phrases=features_data.get("key_phrases", []),
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("llm.extraction_failed", error=str(exc))
        return TextFeatures()


def _extract_passthrough_metadata(signal: Signal) -> dict[str, Any]:
    """Return metadata envelope for non-text modalities."""
    return {
        "modality": signal.modality,
        "type": signal.type,
        "source_module": signal.source.moduleId,
        "encoding": signal.encoding,
        "signal_id": signal.id,
    }


# ---------------------------------------------------------------------------
# PerceptionPipeline
# ---------------------------------------------------------------------------


class PerceptionPipeline:
    """Stateless perception pipeline.

    Instantiated once per process.  The ChromaAdapter (if enabled) is
    connected lazily on first use.
    """

    def __init__(self) -> None:
        self._chroma: Any | None = None  # endogenai_vector_store.ChromaAdapter

    async def _get_chroma(self) -> Any | None:
        """Return a connected ChromaAdapter, or None if embedding is disabled."""
        if not config.ENABLE_EMBEDDING:
            return None
        if self._chroma is not None:
            return self._chroma

        from endogenai_vector_store import (  # noqa: PLC0415
            ChromaAdapter,
            ChromaConfig,
            CreateCollectionRequest,
            EmbeddingConfig,
        )

        chroma = ChromaAdapter(
            config=ChromaConfig(mode="http", host=config.CHROMA_HOST, port=config.CHROMA_PORT),
            embedding_config=EmbeddingConfig(
                provider="ollama",
                model="nomic-embed-text",
                base_url=config.OLLAMA_ENDPOINT,
            ),
        )
        await chroma.connect()
        await chroma.create_collection(
            CreateCollectionRequest(collection_name=config.PERCEPTION_COLLECTION)
        )
        self._chroma = chroma
        return self._chroma

    async def _embed(self, signal: Signal, result: PerceptionResult) -> str | None:
        """Upsert the perception result into the brain.perception collection."""
        chroma = await self._get_chroma()
        if chroma is None:
            return None

        from endogenai_vector_store import MemoryItem, UpsertRequest  # noqa: PLC0415

        item_id = str(uuid.uuid4())
        content = json.dumps(result.model_dump(exclude={"embedding_id"}))
        meta: dict[str, str] = {
            "signal_id": signal.id,
            "modality": signal.modality,
            "pattern": result.pattern or "",
        }
        item = MemoryItem(
            id=item_id,
            collection_name=config.PERCEPTION_COLLECTION,
            content=content,
            type="working",
            source_module=config.MODULE_ID,
            importance_score=0.8,
            created_at=result.timestamp,
            metadata=meta,
        )
        await chroma.upsert(UpsertRequest(collection_name=config.PERCEPTION_COLLECTION, items=[item]))
        log.info("perception.embedded", item_id=item_id, collection=config.PERCEPTION_COLLECTION)
        return item_id

    async def process(self, signal: Signal) -> PerceptionResult:
        """Run the full perception pipeline on a single signal."""
        now = datetime.now(UTC).isoformat()

        # Stage 1: Feature extraction
        text_features: TextFeatures | None = None
        passthrough: dict[str, Any] | None = None

        if signal.modality == "text" and isinstance(signal.payload, str):
            text_features = await _extract_text_features_llm(signal.payload)
        else:
            passthrough = _extract_passthrough_metadata(signal)

        # Stage 2: Pattern recognition
        pattern = _classify_pattern(signal)

        # Stage 3: Build result (fusion is single-signal merge; multi-signal fusion is a stub)
        result = PerceptionResult(
            signal_id=signal.id,
            modality=signal.modality,
            pattern=pattern,
            text_features=text_features,
            passthrough_metadata=passthrough,
            fused=False,
            embedding_id=None,
            timestamp=now,
        )

        # Stage 4: Embed (optional)
        embedding_id = await self._embed(signal, result)
        result.embedding_id = embedding_id

        log.info(
            "perception.processed",
            signal_id=signal.id,
            modality=signal.modality,
            pattern=pattern,
            embedded=embedding_id is not None,
        )
        return result

    async def close(self) -> None:
        if self._chroma is not None:
            await self._chroma.close()

    # ------------------------------------------------------------------
    # MCP / A2A adapters
    # ------------------------------------------------------------------

    async def process_mcp(self, mcp: dict[str, Any]) -> PerceptionResult:
        """Extract a Signal from an MCPContext and process it."""
        payload_data = mcp.get("payload")
        if isinstance(payload_data, dict) and "id" in payload_data and "modality" in payload_data:
            signal = Signal.model_validate(payload_data)
        else:
            content_type: str = str(mcp.get("contentType", "signal/text.input"))
            modality_map: dict[str, str] = {
                "signal": "text", "text": "text", "image": "image",
                "audio": "audio", "sensor": "sensor", "api-event": "api-event",
            }
            modality_str = content_type.split("/")[0] if "/" in content_type else "text"
            resolved_modality = modality_map.get(modality_str, "text")
            source_data = cast("dict[str, Any]", mcp.get("source", {}))
            signal = Signal(
                id=str(mcp.get("id", uuid.uuid4())),
                type=content_type.split("/", 1)[1] if "/" in content_type else "text.input",
                modality=cast("Modality", resolved_modality),
                source={
                    "moduleId": source_data.get("moduleId", "mcp-sender"),
                    "layer": source_data.get("layer", "application"),
                },
                timestamp=str(mcp.get("timestamp", datetime.now(UTC).isoformat())),
                payload=mcp.get("payload"),
                priority=int(mcp.get("priority", 5)),
            )
        return await self.process(signal)

    async def process_a2a(self, msg: dict[str, Any]) -> PerceptionResult:
        """Extract a Signal from an A2AMessage and process it."""
        parts: list[dict[str, Any]] = cast("list[dict[str, Any]]", msg.get("parts", []))
        payload: Any = None
        modality: Modality = "text"
        sig_type = "text.input"

        if parts:
            part = parts[0]
            if part.get("type") == "text":
                payload = part.get("text", "")
            elif part.get("type") == "data":
                payload = part.get("data")
                modality = "internal"
                sig_type = "api.event"

        signal = Signal(
            id=str(msg.get("id", uuid.uuid4())),
            type=sig_type,
            modality=modality,
            source={
                "moduleId": config.MODULE_ID,
                "layer": "perception",
            },
            timestamp=str(msg.get("timestamp", datetime.now(UTC).isoformat())),
            payload=payload,
            priority=5,
        )
        return await self.process(signal)
