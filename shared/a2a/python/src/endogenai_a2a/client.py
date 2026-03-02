"""A2A async HTTP client — JSON-RPC 2.0 task delegation.

Provides a thin, typed wrapper around httpx for agent-to-agent communication.
All Group II Python modules use this instead of raw httpx calls, ensuring
consistent JSON-RPC 2.0 framing, error handling, and logging.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import structlog

from endogenai_a2a.exceptions import A2AError, A2AProtocolError, A2ATaskNotFound
from endogenai_a2a.models import A2ARequest, A2AResponse

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AClient:
    """Async JSON-RPC 2.0 client for inter-module A2A communication.

    Usage::

        client = A2AClient(url="http://localhost:8202", timeout=10.0)
        result = await client.send_task("consolidate_item", {"item": item.model_dump()})

    The client sends all requests to ``{url}/tasks`` using JSON-RPC 2.0 envelopes.
    Each ``send_task`` call maps to the ``tasks/send`` JSON-RPC method.
    Each ``get_task`` call maps to the ``tasks/get`` JSON-RPC method.

    Args:
        url: Base URL of the target A2A module (e.g. ``http://localhost:8202``).
            Must not include a trailing path — ``/tasks`` is appended automatically.
        timeout: HTTP timeout in seconds. Default: 10.0.
        http_client: Optional pre-configured ``httpx.AsyncClient`` for testing.
    """

    def __init__(
        self,
        url: str,
        timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = url.rstrip("/")
        self._timeout = timeout
        self._client = http_client

    async def send_task(
        self,
        task_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a JSON-RPC 2.0 ``tasks/send`` request to the target module.

        The ``payload`` dict is merged into the JSON-RPC ``params`` alongside
        ``task_type`` so the receiving handler can dispatch correctly.

        Args:
            task_type: The A2A task type string (e.g. ``"consolidate_item"``).
            payload: Arbitrary dict of task parameters.

        Returns:
            The ``result`` dict from the JSON-RPC response.

        Raises:
            A2AProtocolError: If the server returns an invalid or error JSON-RPC response.
            A2AError: For any other transport-layer failure.
        """
        request = A2ARequest(
            method="tasks/send",
            params={"task_type": task_type, **payload},
            id=str(uuid.uuid4()),
        )
        log = logger.bind(task_type=task_type, target_url=self._base_url)
        log.debug("a2a.send_task.start")

        try:
            response_data = await self._post(request)
        except A2AError:
            raise
        except Exception as exc:
            log.warning("a2a.send_task.transport_error", error=str(exc))
            raise A2AError(f"A2A transport error calling {self._base_url}: {exc}") from exc

        if response_data.error is not None:
            log.warning("a2a.send_task.rpc_error", error=response_data.error)
            raise A2AProtocolError(
                f"tasks/send returned error: {response_data.error}"
            )

        result: dict[str, Any] = response_data.result or {}
        log.debug("a2a.send_task.ok", result_keys=list(result.keys()))
        return result

    async def get_task(self, task_id: str) -> dict[str, Any]:
        """Fetch a previously submitted task by its ID via ``tasks/get``.

        Args:
            task_id: The UUID of the task to retrieve.

        Returns:
            The ``result`` dict from the JSON-RPC response.

        Raises:
            A2ATaskNotFound: If the server returns a null result.
            A2AProtocolError: If the server returns an error response.
            A2AError: For transport failures.
        """
        request = A2ARequest(
            method="tasks/get",
            params={"id": task_id},
            id=str(uuid.uuid4()),
        )
        try:
            response_data = await self._post(request)
        except A2AError:
            raise
        except Exception as exc:
            raise A2AError(f"A2A transport error calling {self._base_url}: {exc}") from exc

        if response_data.error is not None:
            raise A2AProtocolError(f"tasks/get returned error: {response_data.error}")

        if response_data.result is None:
            raise A2ATaskNotFound(f"Task {task_id!r} not found at {self._base_url}")

        return response_data.result

    async def _post(self, request: A2ARequest) -> A2AResponse:
        """Send the JSON-RPC envelope to ``{base_url}/tasks`` and parse the response.

        If a pre-configured client was injected (e.g. in tests), it is used directly.
        Otherwise a fresh ``httpx.AsyncClient`` is created per call.
        """
        endpoint = f"{self._base_url}/tasks"
        body = request.model_dump(mode="json", by_alias=True)

        if self._client is not None:
            http_response = await self._client.post(
                endpoint, json=body, timeout=self._timeout
            )
            http_response.raise_for_status()
            return A2AResponse.model_validate(http_response.json())

        async with httpx.AsyncClient() as client:
            http_response = await client.post(
                endpoint, json=body, timeout=self._timeout
            )
            http_response.raise_for_status()

        try:
            return A2AResponse.model_validate(http_response.json())
        except Exception as exc:
            raise A2AProtocolError(
                f"Invalid JSON-RPC response from {endpoint}: {exc}"
            ) from exc
