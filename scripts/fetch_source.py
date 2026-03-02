"""
fetch_source.py — Fetch a URL and save its content to a local file.

Purpose:
    Allows the AI agent (or a human) to fetch a web page and persist it to
    docs/research/sources/ immediately, without holding large page content in
    the AI context window between tool calls.

Usage:
    # Fetch a single URL
    uv run python scripts/fetch_source.py \\
        --url https://en.wikipedia.org/wiki/Motor_cortex \\
        --out docs/research/sources/phase-6/bio-motor-cortex.md

    # Fetch all URLs defined in a manifest JSON file
    uv run python scripts/fetch_source.py \\
        --manifest scripts/fetch_manifests/phase-6.json \\
        --dry-run

Manifest JSON format:
    [
      {
        "url": "https://en.wikipedia.org/wiki/Motor_cortex",
        "out": "docs/research/sources/phase-6/bio-motor-cortex.md",
        "note": "optional human-readable note"
      }
    ]

Output:
    Each saved file begins with a YAML-style metadata header (URL, fetch
    date, HTTP status), followed by the raw text content of the page.

Options:
    --url URL           Single URL to fetch.
    --out PATH          Output file path (relative to repo root or absolute).
    --manifest PATH     JSON manifest file listing multiple URL→out mappings.
    --dry-run           Print what would be fetched/saved without writing files.
    --timeout SECS      Request timeout in seconds (default: 30).
    --user-agent STR    Override User-Agent header.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TIMEOUT = 30
DEFAULT_UA = (
    "Mozilla/5.0 (compatible; EndogenAI-ResearchBot/1.0; "
    "+https://github.com/AccessiTech/EndogenAI)"
)


def fetch_url(url: str, timeout: int, user_agent: str) -> tuple[int, str]:
    """Fetch *url* and return (http_status, body_text)."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status: int = resp.status
            charset = resp.headers.get_content_charset("utf-8")
            body = resp.read().decode(charset, errors="replace")
            return status, body
    except urllib.error.HTTPError as exc:
        return exc.code, f"HTTP error {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return 0, f"URL error: {exc.reason}"


def build_output(url: str, status: int, body: str) -> str:
    """Prepend a metadata header to the fetched body."""
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = textwrap.dedent(f"""\
        <!-- fetch_source.py metadata
        url: {url}
        fetched: {fetched_at}
        http_status: {status}
        -->
        # Fetched source: {url}
        _Fetched: {fetched_at} | HTTP {status}_

        ---

        """)
    return header + body


def save(out_path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] would write {len(content):,} chars → {out_path}")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"  ✓ saved {len(content):,} chars → {out_path}")


def process_one(
    url: str,
    out: str,
    *,
    timeout: int,
    user_agent: str,
    dry_run: bool,
    note: str = "",
) -> bool:
    out_path = Path(out) if Path(out).is_absolute() else REPO_ROOT / out
    label = f"[{note}] " if note else ""
    print(f"→ {label}fetching {url}")
    status, body = fetch_url(url, timeout, user_agent)
    if status == 0 or status >= 400:
        print(f"  ✗ failed (status {status}): {body[:120]}", file=sys.stderr)
        return False
    content = build_output(url, status, body)
    save(out_path, content, dry_run)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a URL and save it to a local file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single URL to fetch.")
    group.add_argument("--manifest", help="JSON manifest file with multiple URL→out entries.")
    parser.add_argument(
        "--out",
        help="Output file path (required with --url).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files.",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout (s).")
    parser.add_argument("--user-agent", default=DEFAULT_UA, help="Override User-Agent header.")

    args = parser.parse_args()

    kwargs = dict(timeout=args.timeout, user_agent=args.user_agent, dry_run=args.dry_run)
    failures = 0

    if args.url:
        if not args.out:
            parser.error("--out is required when using --url")
        ok = process_one(args.url, args.out, **kwargs)
        failures += 0 if ok else 1
    else:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"Manifest not found: {manifest_path}", file=sys.stderr)
            return 1
        entries: list[dict] = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"Manifest: {len(entries)} entries from {manifest_path}")
        for entry in entries:
            ok = process_one(
                entry["url"],
                entry["out"],
                note=entry.get("note", ""),
                **kwargs,
            )
            failures += 0 if ok else 1

    if failures:
        print(f"\n{failures} fetch(es) failed.", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
