#!/usr/bin/env python3
"""Validate YAML frontmatter in knowledge resource documents.

Required fields: id, version, status, maps-to-modules
"""

import re
import sys
from pathlib import Path
from typing import Any, cast

import yaml

REQUIRED_FIELDS = ["id", "version", "status", "maps-to-modules"]
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def extract_frontmatter(path: Path) -> dict[str, Any] | None:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter must be a YAML mapping, got {type(data).__name__}")
    return cast(dict[str, Any], data)


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        fm = extract_frontmatter(path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if fm is None:
        errors.append(f"{path}: missing YAML frontmatter block")
        return errors
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"{path}: missing required frontmatter field '{field}'")
    return errors


def main() -> int:
    resources_dir = Path(__file__).parent.parent / "resources"
    md_files = [p for p in resources_dir.rglob("*.md") if p.name.lower() != "readme.md"]
    if not md_files:
        print("No markdown files found in resources/")
        return 0

    all_errors: list[str] = []
    for path in sorted(md_files):
        all_errors.extend(validate_file(path))

    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        return 1

    print(f"Frontmatter valid: {len(md_files)} file(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
