"""tests/test_policy.py — Unit tests for PolicyEngine (OPA HTTP client).

Uses pytest-mock to mock the httpx.AsyncClient so no live OPA server is needed.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from executive_agent.policy import PolicyEngine, _hash_input


class TestPolicyEngineEvaluate:
    async def test_allow_true_on_opa_allow_response(self) -> None:
        engine = PolicyEngine()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"result": True}

        with patch.object(engine._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            decision = await engine.evaluate_policy(
                package="endogenai.goals",
                rule="allow",
                input_data={"candidate": {"id": "abc", "goal_class": "planning"}},
            )

        assert decision.allow is True
        assert decision.violations == []
        assert decision.package == "endogenai.goals"

    async def test_allow_false_on_opa_deny_response(self) -> None:
        engine = PolicyEngine()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"result": False}

        with patch.object(engine._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            decision = await engine.evaluate_policy(
                package="endogenai.goals",
                rule="allow",
                input_data={"candidate": {}},
            )

        assert decision.allow is False

    async def test_violations_rule_parsed_correctly(self) -> None:
        engine = PolicyEngine()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"result": ["Goal class 'planning' already executing"]}

        with patch.object(engine._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            decision = await engine.evaluate_policy(
                package="endogenai.goals",
                rule="violations",
                input_data={},
            )

        assert decision.allow is False
        assert len(decision.violations) == 1

    async def test_opa_unavailable_returns_deny(self) -> None:
        import httpx

        engine = PolicyEngine()

        with patch.object(
            engine._client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            decision = await engine.evaluate_policy(
                package="endogenai.goals",
                rule="allow",
                input_data={},
            )

        assert decision.allow is False
        assert any("OPA" in v for v in decision.violations)

    async def test_cache_hit_returns_cached_decision(self) -> None:
        engine = PolicyEngine()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"result": True}

        input_data: dict[str, Any] = {"candidate": {"id": "same"}}

        with patch.object(engine._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            # First call — populates cache
            await engine.evaluate_policy("endogenai.goals", "allow", input_data)
            # Second call — should hit cache
            d2 = await engine.evaluate_policy("endogenai.goals", "allow", input_data)

        assert mock_post.call_count == 1  # Only one HTTP call
        assert d2.cached is True
        assert d2.cached is True

    async def test_clear_cache_works(self) -> None:
        engine = PolicyEngine()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"result": True}

        input_data: dict[str, Any] = {"x": 1}

        with patch.object(engine._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            await engine.evaluate_policy("pkg", "allow", input_data)
            assert len(engine._cache) == 1
            engine.clear_cache()
            assert len(engine._cache) == 0


class TestHashInput:
    def test_same_inputs_produce_same_hash(self) -> None:
        h1 = _hash_input("pkg", "rule", {"a": 1, "b": 2})
        h2 = _hash_input("pkg", "rule", {"b": 2, "a": 1})
        assert h1 == h2

    def test_different_inputs_produce_different_hashes(self) -> None:
        h1 = _hash_input("pkg", "rule", {"a": 1})
        h2 = _hash_input("pkg", "rule", {"a": 2})
        assert h1 != h2
