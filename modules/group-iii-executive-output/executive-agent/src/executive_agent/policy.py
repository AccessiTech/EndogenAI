"""policy.py — OPA HTTP client for executive-agent policy evaluation.

Calls the standalone OPA REST API at localhost:8181 (Option B — standalone HTTP).
All policy decisions route through this module — OPA is never embedded as a library.

Neuroanatomical analogue:
  - ACC (BA 24/32): conflict detection; policy violations set triggers deliberation escalation
  - vmPFC (BA 10–12): fast heuristic pre-filter before full OPA evaluation

OPA packages used:
  - endogenai.identity  (policies/identity.rego)
  - endogenai.goals     (policies/goals.rego)
  - endogenai.actions   (policies/actions.rego)
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from executive_agent.models import PolicyDecision

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_OPA_BASE_URL = "http://localhost:8181"
_DECISION_CACHE_SIZE = 100


class PolicyEngine:
    """Wrapper around the OPA REST API (/v1/data/{package}/{rule}).

    Provides:
      - evaluate_policy(): POST to OPA, return PolicyDecision
      - load_bundle(): PUT bundle tar.gz to OPA for hot-reload
      - health_check(): GET /health; raises RuntimeError if unreachable
    """

    def __init__(self, base_url: str = _OPA_BASE_URL, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)
        # LRU cache: OrderedDict with a fixed capacity; oldest entries are evicted first.
        self._cache: OrderedDict[str, PolicyDecision] = OrderedDict()

    async def evaluate_policy(
        self,
        package: str,
        rule: str,
        input_data: dict[str, Any],
    ) -> PolicyDecision:
        """Evaluate a policy rule and return a PolicyDecision.

        Caches allow=True decisions for identical inputs within this session.
        Eviction policy: LRU, maximum ``_DECISION_CACHE_SIZE`` entries.
        Cache key = SHA-256(package + rule + canonical JSON of input_data).
        """
        cache_key = _hash_input(package, rule, input_data)

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            self._cache.move_to_end(cache_key)  # keep LRU order fresh
            logger.debug("policy.cache_hit", package=package, rule=rule)
            return cached.model_copy(update={"cached": True})

        url = f"/v1/data/{package.replace('.', '/')}/{rule}"
        body = {"input": input_data}

        try:
            response = await self._client.post(url, json=body)
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as exc:
            logger.error("policy.opa_http_error", url=url, error=str(exc))
            # Fail-closed: OPA unavailability blocks goal execution.
            # allow=False ensures no action proceeds without an explicit permit.
            return PolicyDecision(
                allow=False,
                violations=[f"OPA communication error: {exc}"],
                explanation="OPA server unreachable or returned an error.",
                package=package,
                rule=rule,
                evaluated_at=datetime.now(UTC),
            )

        raw_result = result.get("result", False)

        # OPA returns the rule value directly; for violations[] it's a list
        if rule == "allow":
            allow = bool(raw_result)
            violations: list[str] = []
        elif rule == "violations":
            violations = list(raw_result) if isinstance(raw_result, list) else []
            allow = len(violations) == 0
        else:
            # Generic boolean rule
            allow = bool(raw_result)
            violations = []

        decision = PolicyDecision(
            allow=allow,
            violations=violations,
            package=package,
            rule=rule,
            evaluated_at=datetime.now(UTC),
            cached=False,
            input_hash=cache_key,
        )

        # Cache positive decisions only (deny = do not cache, may change).
        # LRU eviction: if at capacity, drop the least-recently-used entry first.
        if allow:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
            else:
                if len(self._cache) >= _DECISION_CACHE_SIZE:
                    self._cache.popitem(last=False)  # evict oldest
                self._cache[cache_key] = decision

        logger.info(
            "policy.evaluated",
            package=package,
            rule=rule,
            allow=allow,
            violation_count=len(violations),
        )
        return decision

    async def load_policy(self, policy_path: str, policy_id: str = "endogenai") -> None:
        """Upload a single Rego source file to OPA via PUT /v1/policies/{id}.

        OPA's /v1/policies/{id} endpoint expects raw Rego source as text/plain.
        For multi-policy bundles served at startup, configure the OPA "--bundle"
        flag in docker-compose.yml instead of calling this method.

        Args:
            policy_path: Path to a .rego source file on the local filesystem.
            policy_id:   OPA policy identifier (default ``"endogenai"``).
        """
        with open(policy_path) as fh:
            rego_source = fh.read()
        response = await self._client.put(
            f"/v1/policies/{policy_id}",
            content=rego_source.encode(),
            headers={"Content-Type": "text/plain"},
        )
        response.raise_for_status()
        logger.info("policy.policy_loaded", policy_path=policy_path, policy_id=policy_id)

    async def load_bundle(self, bundle_path: str) -> None:  # pragma: no cover
        """Deprecated: use load_policy() for single Rego files or configure OPA
        with --bundle /policies at startup for directory bundles.

        This method is retained for backwards compatibility but is a no-op;
        calling it logs a deprecation warning.
        """
        logger.warning(
            "policy.load_bundle_deprecated",
            bundle_path=bundle_path,
            suggestion="Use load_policy() for a single .rego file, or configure "
                       "OPA --bundle /policies in docker-compose.yml.",
        )

    async def health_check(self) -> bool:
        """GET /health — raises RuntimeError if OPA is unreachable."""
        try:
            response = await self._client.get("/health")
            response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OPA health check failed: {exc}") from exc

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> PolicyEngine:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    def clear_cache(self) -> None:
        """Clear the in-process decision cache (e.g. after bundle hot-reload)."""
        self._cache.clear()


def _hash_input(package: str, rule: str, input_data: dict[str, Any]) -> str:
    """Produce a deterministic SHA-256 key for the policy cache."""
    canonical = json.dumps({"package": package, "rule": rule, "input": input_data}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
