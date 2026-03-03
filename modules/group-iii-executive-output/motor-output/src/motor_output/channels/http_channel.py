"""http_channel.py — Outbound HTTP action channel.

M1 corticospinal tract analogue: direct pathway to the peripheral effector
(external HTTP service). Supports GET, POST, PUT, PATCH, DELETE.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class HTTPChannel:
    """Dispatches ActionSpec params to an external HTTP endpoint."""

    async def dispatch(
        self,
        params: dict[str, Any],
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """Send an HTTP request and return the normalised response.

        Expected params keys:
          - url (required): target endpoint
          - method (optional, default POST): HTTP verb
          - body / json / data: request body
          - headers (optional): extra request headers
        """
        url: str = params.get("url", "")
        if not url:
            raise ValueError("HTTPChannel.dispatch requires params['url']")
        method: str = params.get("method", "POST").upper()
        headers: dict[str, str] = params.get("headers", {})
        body: dict[str, Any] | None = params.get("json") or params.get("body")
        data: str | None = params.get("data")

        logger.debug("http_channel.dispatch", url=url, method=method)
        started_at = datetime.now(UTC)

        async with httpx.AsyncClient(timeout=float(timeout_seconds)) as client:
            resp = await client.request(
                method=method,
                url=url,
                json=body,
                content=data,
                headers=headers,
            )

        latency_ms = (datetime.now(UTC) - started_at).total_seconds() * 1000
        logger.info(
            "http_channel.response",
            url=url,
            status=resp.status_code,
            latency_ms=round(latency_ms),
        )

        try:
            response_body: dict[str, Any] = resp.json()
        except Exception:
            response_body = {"raw": resp.text}

        return {
            "http_status": resp.status_code,
            "success": resp.is_success,
            "body": response_body,
            "latency_ms": latency_ms,
        }
