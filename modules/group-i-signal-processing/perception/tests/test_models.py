"""Tests for perception data models and pipeline static helpers."""

from __future__ import annotations

from endogenai_perception.models import PerceptionResult, PerceptualFeatures
from endogenai_perception.pipeline import PerceptionPipeline


class TestPerceptualFeatures:
    def test_required_fields(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.signal_id == "s1"
        assert f.modality == "text"

    def test_entities_defaults_empty(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.entities == []

    def test_intent_defaults_none(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.intent is None

    def test_summary_defaults_none(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.summary is None

    def test_language_defaults_none(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.language is None

    def test_scene_defaults_empty_dict(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="image")
        assert f.scene == {}

    def test_raw_embedding_text_defaults_none(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.raw_embedding_text is None

    def test_metadata_defaults_empty_dict(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        assert f.metadata == {}

    def test_entities_populated(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text", entities=["cat", "dog"])
        assert f.entities == ["cat", "dog"]

    def test_scene_populated(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="image", scene={"objects": ["car"]})
        assert f.scene == {"objects": ["car"]}

    def test_all_fields_set(self) -> None:
        f = PerceptualFeatures(
            signal_id="s1",
            modality="text",
            entities=["entity1"],
            intent="question",
            summary="A question about something.",
            language="en",
            raw_embedding_text="A question about something. | Entities: entity1 | Intent: question",
            metadata={"source": "user"},
        )
        assert f.intent == "question"
        assert f.language == "en"
        assert f.summary is not None
        assert f.raw_embedding_text is not None


class TestPerceptionResult:
    def test_signal_id_stored(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        r = PerceptionResult(signal_id="s1", features=f)
        assert r.signal_id == "s1"

    def test_features_stored(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text", intent="observation")
        r = PerceptionResult(signal_id="s1", features=f)
        assert r.features.intent == "observation"

    def test_embedding_id_defaults_none(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        r = PerceptionResult(signal_id="s1", features=f)
        assert r.embedding_id is None

    def test_embedding_model_defaults_none(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        r = PerceptionResult(signal_id="s1", features=f)
        assert r.embedding_model is None

    def test_embedding_id_set(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        r = PerceptionResult(signal_id="s1", features=f, embedding_id="emb-abc")
        assert r.embedding_id == "emb-abc"

    def test_embedding_model_set(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text")
        r = PerceptionResult(
            signal_id="s1",
            features=f,
            embedding_id="emb-1",
            embedding_model="ollama/nomic-embed-text",
        )
        assert r.embedding_model == "ollama/nomic-embed-text"


class TestBuildEmbeddingText:
    """Tests for PerceptionPipeline._build_embedding_text (static helper)."""

    def test_summary_only(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text", summary="Quick fox.")
        result = PerceptionPipeline._build_embedding_text(f)
        assert result == "Quick fox."

    def test_summary_and_entities(self) -> None:
        f = PerceptualFeatures(
            signal_id="s1", modality="text", summary="Quick fox.", entities=["fox"]
        )
        result = PerceptionPipeline._build_embedding_text(f)
        assert "Quick fox." in result
        assert "Entities: fox" in result
        assert " | " in result

    def test_all_fields_joined(self) -> None:
        f = PerceptualFeatures(
            signal_id="s1",
            modality="text",
            summary="A question.",
            entities=["entity1", "entity2"],
            intent="question",
        )
        result = PerceptionPipeline._build_embedding_text(f)
        assert "A question." in result
        assert "Entities: entity1, entity2" in result
        assert "Intent: question" in result

    def test_intent_only(self) -> None:
        f = PerceptualFeatures(signal_id="s1", modality="text", intent="command")
        result = PerceptionPipeline._build_embedding_text(f)
        assert "Intent: command" in result

    def test_empty_features_falls_back_to_signal_id(self) -> None:
        f = PerceptualFeatures(signal_id="sig-xyz", modality="sensor")
        result = PerceptionPipeline._build_embedding_text(f)
        assert result == "signal:sig-xyz"

    def test_entities_joined_with_comma(self) -> None:
        f = PerceptualFeatures(
            signal_id="s1", modality="text", entities=["alpha", "beta", "gamma"]
        )
        result = PerceptionPipeline._build_embedding_text(f)
        assert "alpha, beta, gamma" in result
