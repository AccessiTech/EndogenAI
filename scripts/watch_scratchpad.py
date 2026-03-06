"""
watch_scratchpad.py — Auto-annotate scratchpad session files on change.

Purpose:
    Watches the .tmp/ directory for changes to *.md session files and immediately
    runs `prune_scratchpad.py --annotate` on the changed file. This keeps every H2
    heading annotated with its current line range [Lstart–Lend] at all times,
    enabling agents to reference sections by precise line numbers rather than by
    vague heading names.

    _index.md and any heading-starting-with-underscore files are excluded.

    A cooldown window (COOLDOWN_SECONDS) prevents the annotator's own file write
    from re-triggering an annotation loop. The cooldown timer is recorded AFTER
    the subprocess completes so the window covers the period of the annotator's
    own write (see _handle() in ScratchpadHandler).

    ## Architecture — three layers

    1. watchdog (Python library) — low-level OS filesystem event detection.
       Tells this script "a .tmp/*.md file changed." Provides Observer +
       FileSystemEventHandler; has no built-in debounce or cooldown.
    2. watch_scratchpad.py (this script) — built on top of watchdog. Defines
       WHAT to do on change (run prune_scratchpad.py --annotate) and implements
       the cooldown timer manually (watchdog has no built-in debounce).
    3. VS Code tasks.json "runOn: folderOpen" — tells VS Code to LAUNCH this
       script automatically on workspace open. This is the VS Code task runner;
       it is independent of watchdog. Removing runOn makes the task manual-only.
       The auto-start is intentional — see .vscode/tasks.json detail field.

Usage:
    uv run python scripts/watch_scratchpad.py
    uv run python scripts/watch_scratchpad.py --tmp-dir .tmp

    Start this as a background VS Code task at the beginning of each session
    (see .vscode/tasks.json task "Watch Scratchpad"). Stop with Ctrl-C.

Requirements:
    watchdog >= 4.0 — listed in root pyproject.toml [dependency-groups] dev-tools.
    Install with: uv sync  (all groups installed by default)
    Or explicitly: uv sync --group dev-tools

Exit codes:
    0 — clean exit (Ctrl-C or observer stopped)
    1 — watchdog not installed
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print(
        "ERROR: watchdog is not installed.\n"
        "Install it with: uv sync  (or: uv add --group dev watchdog)",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COOLDOWN_SECONDS = 2.0
"""Seconds to ignore further events on a file after we write to it ourselves."""

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
ANNOTATE_SCRIPT = SCRIPT_DIR / "prune_scratchpad.py"


# ---------------------------------------------------------------------------
# Event handler
# ---------------------------------------------------------------------------


class ScratchpadHandler(FileSystemEventHandler):
    """Watchdog event handler that runs the annotator on session file changes."""

    def __init__(self) -> None:
        super().__init__()
        self._recently_written: dict[str, float] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Cooldown helpers
    # ------------------------------------------------------------------

    def _cooldown_ok(self, path: str) -> bool:
        """Return True if enough time has passed since we last wrote to this path."""
        with self._lock:
            last = self._recently_written.get(path, 0.0)
            return (time.monotonic() - last) > COOLDOWN_SECONDS

    def _record(self, path: str) -> None:
        """Record that we are about to write to this path."""
        with self._lock:
            self._recently_written[path] = time.monotonic()

    # ------------------------------------------------------------------
    # Core handler
    # ------------------------------------------------------------------

    def _handle(self, src_path: str) -> None:
        p = Path(src_path)

        # Only process Markdown session files
        if p.suffix != ".md":
            return
        # Skip index files and hidden files
        if p.name.startswith("_") or p.name.startswith("."):
            return
        # Skip if the file has vanished
        if not p.exists():
            return
        # Suppress re-triggers from our own writes
        if not self._cooldown_ok(src_path):
            return

        try:
            rel = p.relative_to(REPO_ROOT)
        except ValueError:
            rel = p

        print(f"[watch_scratchpad] Changed: {rel} — annotating…", flush=True)

        result = subprocess.run(
            [sys.executable, str(ANNOTATE_SCRIPT), "--annotate", "--file", src_path],
            capture_output=True,
            text=True,
        )

        # Record cooldown AFTER subprocess completes so the timer covers the
        # period when the annotator's own file write could re-trigger the watcher.
        self._record(src_path)

        if result.returncode != 0:
            print(
                f"[watch_scratchpad] ERROR annotating {rel}:\n{result.stderr.strip()}",
                file=sys.stderr,
                flush=True,
            )
        else:
            msg = result.stdout.strip()
            if msg:
                print(f"[watch_scratchpad] {msg}", flush=True)

    # ------------------------------------------------------------------
    # Watchdog callbacks
    # ------------------------------------------------------------------

    def on_modified(self, event) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._handle(event.src_path)

    def on_created(self, event) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._handle(event.src_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watch .tmp/ and auto-annotate scratchpad session files on change."
    )
    parser.add_argument(
        "--tmp-dir",
        default=str(REPO_ROOT / ".tmp"),
        help="Directory to watch (default: .tmp/ at repo root)",
    )
    args = parser.parse_args()

    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    handler = ScratchpadHandler()
    observer = Observer()
    observer.schedule(handler, str(tmp_dir), recursive=True)
    observer.start()

    print(f"[watch_scratchpad] Watching {tmp_dir}/ (Ctrl-C to stop)", flush=True)

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
