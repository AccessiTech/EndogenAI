#!/usr/bin/env python3
"""
Fix tool IDs in .agent.md files: strip namespace prefixes.

The canonical VS Code Copilot tool IDs use bare names (no slash-prefixed namespace).
This script renames all prefixed IDs to their canonical bare form.

Usage:
    uv run python scripts/fix_agent_tools.py [--dry-run]

Sources:
    https://code.visualstudio.com/docs/copilot/customization/custom-agents
"""

import argparse
import pathlib
import re
import sys

TOOL_MAP = {
    "search/codebase":             "codebase",
    "edit/editFiles":              "editFiles",
    "execute/runInTerminal":       "runInTerminal",
    "execute/runTests":            "runTests",
    "execute/getTerminalOutput":   "getTerminalOutput",
    "read/problems":               "problems",
    "read/terminalLastCommand":    "terminalLastCommand",
    "search/usages":               "usages",
    "web/fetch":                   "fetch",
}

# Also fix inline #tool: references in body text
INLINE_MAP = {f"#tool:{old}": f"#tool:{new}" for old, new in TOOL_MAP.items()}


def fix_content(text: str) -> tuple[str, list[str]]:
    changes = []
    for old, new in {**TOOL_MAP, **INLINE_MAP}.items():
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            changes.append(f"  {old} -> {new}  ({count}x)")
    return text, changes


def main():
    parser = argparse.ArgumentParser(description="Fix agent tool IDs")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    agents_dir = pathlib.Path(__file__).parent.parent / ".github" / "agents"
    files = sorted(agents_dir.glob("*.agent.md"))
    if not files:
        print(f"No .agent.md files found in {agents_dir}", file=sys.stderr)
        sys.exit(1)

    total_files = 0
    for f in files:
        original = f.read_text(encoding="utf-8")
        fixed, changes = fix_content(original)
        if changes:
            total_files += 1
            print(f"{'[DRY-RUN] ' if args.dry_run else ''}Updated: {f.name}")
            for c in changes:
                print(c)
            if not args.dry_run:
                f.write_text(fixed, encoding="utf-8")

    if total_files == 0:
        print("Nothing to change — all tool IDs are already canonical.")
    else:
        action = "Would update" if args.dry_run else "Updated"
        print(f"\n{action} {total_files} file(s).")


if __name__ == "__main__":
    main()
