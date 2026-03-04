"""
prune_scratchpad.py — Scratchpad size management for .tmp.md

Purpose:
    Prunes the cross-agent scratchpad (.tmp.md) by compressing completed H2 sections
    into one-line archived summaries, preserving only active/live sections in full.
    Writes an '## Active Context' header at the top summarising what remains live.

    A section is considered "completed" when its heading contains any of the archive
    keywords: Results, Complete, Completed, Summary, Archived, Handoff, Done, Output.
    Sections whose heading contains "Active", "Escalation", "Session" (current), or
    "Plan" are treated as live and left intact.

    The rule of thumb: if .tmp.md exceeds 200 lines, prune before the next delegation.

Inputs:
    .tmp.md at the workspace root (default) or a path passed via --file.

Outputs:
    Rewrites .tmp.md (or prints to stdout in --dry-run mode) with:
    - A leading '## Active Context' block listing all compressed sections
    - Full content of live sections
    - One-line archive stubs replacing completed sections:
        ## <Original Heading> (archived <YYYY-MM-DD> — <first-line-of-content>)

Usage:
    # Dry run — print result, do not write
    python scripts/prune_scratchpad.py --dry-run

    # Prune in place
    python scripts/prune_scratchpad.py

    # Target a different file
    python scripts/prune_scratchpad.py --file path/to/scratchpad.md

    # Force prune regardless of line count
    python scripts/prune_scratchpad.py --force

Exit codes:
    0 — success (pruned or no pruning needed)
    1 — file not found or parse error
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# Headings whose content is NOT archived (kept in full)
LIVE_KEYWORDS = frozenset(["active", "escalation", "plan", "session"])

# Headings whose content IS archived (compressed to one line)
ARCHIVE_KEYWORDS = frozenset(
    ["results", "complete", "completed", "summary", "archived",
     "handoff", "done", "output", "sweep", "gaps"]
)

# If line count is below this threshold, skip pruning unless --force
SIZE_GUARD = 200


def _classify(heading: str) -> str:
    """Return 'live' or 'archive' based on heading text."""
    lower = heading.lower()
    for kw in LIVE_KEYWORDS:
        if kw in lower:
            return "live"
    for kw in ARCHIVE_KEYWORDS:
        if kw in lower:
            return "archive"
    # Default: keep live (unknown sections are preserved)
    return "live"


def _first_content_line(lines: list[str]) -> str:
    """Return the first non-empty, non-heading content line."""
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            # Truncate long lines for the one-liner
            return stripped[:80] + ("…" if len(stripped) > 80 else "")
    return "(no content)"


def parse_sections(text: str) -> list[dict]:
    """
    Split .tmp.md into a list of section dicts:
        { "heading": str, "level": int, "lines": list[str] }

    The leading content before the first H2 is stored as a special
    section with heading="" and level=0.
    """
    sections: list[dict] = []
    current_heading = ""
    current_level = 0
    current_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        h_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if h_match:
            level = len(h_match.group(1))
            heading = h_match.group(2).strip()
            if level == 2:
                # Save previous section
                sections.append({
                    "heading": current_heading,
                    "level": current_level,
                    "lines": current_lines,
                })
                current_heading = heading
                current_level = level
                current_lines = []
                continue
        current_lines.append(line)

    # Save final section
    sections.append({
        "heading": current_heading,
        "level": current_level,
        "lines": current_lines,
    })
    return sections


def prune(text: str, today: str) -> tuple[str, list[str], list[str]]:
    """
    Prune the scratchpad text.

    Returns:
        (pruned_text, archived_headings, kept_headings)
    """
    sections = parse_sections(text)
    archived: list[str] = []
    kept: list[str] = []
    output_parts: list[str] = []

    for section in sections:
        heading = section["heading"]
        lines = section["lines"]

        if not heading:
            # Pre-H2 content — always keep
            output_parts.extend(lines)
            continue

        classification = _classify(heading)

        if classification == "archive":
            summary = _first_content_line(lines)
            stub = f"## {heading} (archived {today} — {summary})\n\n"
            output_parts.append(stub)
            archived.append(heading)
        else:
            output_parts.append(f"## {heading}\n")
            output_parts.extend(lines)
            kept.append(heading)

    # Build Active Context header
    active_header_lines = [
        "## Active Context\n",
        "\n",
        "**Live sections** (full content below):\n",
    ]
    for h in kept:
        active_header_lines.append(f"- {h}\n")
    active_header_lines.append("\n")
    if archived:
        active_header_lines.append("**Archived sections** (one-line stubs inline):\n")
        for h in archived:
            active_header_lines.append(f"- {h}\n")
        active_header_lines.append("\n")
    active_header_lines.append("---\n\n")

    # Inject Active Context after first section (pre-H2 content)
    first_section_lines = sections[0]["lines"] if sections else []
    pre_content = "".join(first_section_lines)

    pruned = pre_content + "".join(active_header_lines) + "".join(
        p for p in output_parts[len(first_section_lines):]
    )
    return pruned, archived, kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1].strip())
    parser.add_argument(
        "--file",
        default=".tmp.md",
        help="Path to the scratchpad file (default: .tmp.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pruned content without writing the file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Prune regardless of line count (bypasses size guard)",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: {path} not found.", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    line_count = text.count("\n")

    if not args.force and line_count < SIZE_GUARD:
        print(
            f"INFO: {path} has {line_count} lines (threshold: {SIZE_GUARD}). "
            "No pruning needed. Use --force to prune anyway."
        )
        return 0

    today = date.today().isoformat()
    pruned, archived, kept = prune(text, today)

    if args.dry_run:
        print(pruned)
        print(
            f"\n--- DRY RUN ---\n"
            f"Would archive {len(archived)} sections, keep {len(kept)} sections live.\n"
            f"Archived: {archived}\n"
            f"Kept live: {kept}"
        )
        return 0

    path.write_text(pruned, encoding="utf-8")
    print(
        f"Pruned {path}:\n"
        f"  Archived {len(archived)} sections: {archived}\n"
        f"  Kept live {len(kept)} sections: {kept}\n"
        f"  New line count: {pruned.count(chr(10))}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
