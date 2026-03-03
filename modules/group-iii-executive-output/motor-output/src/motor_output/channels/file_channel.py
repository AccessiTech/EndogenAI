"""file_channel.py — Filesystem write channel.

Descending corticospinal → motor neuron → muscle analogue for persistent
state changes: write structured output to the filesystem.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiofiles
import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_ALLOWED_BASE_PATHS = ["/tmp", "/var/endogenai/outputs"]


class FileChannel:
    """Writes ActionSpec params to the filesystem."""

    def __init__(self, allowed_base_paths: list[str] | None = None) -> None:
        self._allowed_bases = [
            Path(p) for p in (allowed_base_paths or _ALLOWED_BASE_PATHS)
        ]

    def _is_allowed(self, target: Path) -> bool:
        """Return True iff *target* resolves to a path inside an allowed base.

        Uses Path.relative_to() rather than startswith() to prevent prefix-trick
        path-traversal (e.g. /tmp-evil/ passing a /tmp base check).
        """
        resolved = target.resolve()
        for base in self._allowed_bases:
            try:
                resolved.relative_to(base.resolve())
                return True
            except ValueError:
                continue
        return False

    async def dispatch(
        self,
        params: dict[str, Any],
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """Write content to a file path.

        Expected params keys:
          - path (required): target file path (must be under an allowed base)
          - content (required): content to write (string or dict → JSON)
          - mode (optional, default "w"): write mode ("w" or "a")
          - encoding (optional, default "utf-8")
        """
        raw_path: str = params.get("path", "")
        if not raw_path:
            raise ValueError("FileChannel.dispatch requires params['path']")
        file_path = Path(raw_path)
        content = params.get("content", "")
        mode: str = params.get("mode", "w")
        encoding: str = params.get("encoding", "utf-8")

        if not self._is_allowed(file_path):
            raise PermissionError(
                f"Path {file_path} is not under an allowed base path: {self._allowed_bases}"
            )

        text = json.dumps(content, indent=2) if isinstance(content, (dict, list)) else str(content)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, mode=mode, encoding=encoding) as fh:  # type: ignore[call-overload]
            await fh.write(text)

        bytes_written = len(text.encode(encoding))
        logger.info("file_channel.written", path=str(file_path), bytes=bytes_written)

        return {
            "success": True,
            "path": str(file_path),
            "bytes_written": bytes_written,
        }
