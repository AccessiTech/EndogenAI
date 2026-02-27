#!/usr/bin/env python3
"""validate_all_schemas.py — Validate all JSON Schema files in shared/.

Checks every .schema.json file in shared/schemas/, shared/types/, and
shared/vector-store/ for the four required top-level keys:
  $schema, $id, title, type

Usage:
  uv run python scripts/schema/validate_all_schemas.py          # exits 1 on violations
  uv run python scripts/schema/validate_all_schemas.py --dry-run # always exits 0
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SCAN_DIRS = [
    REPO_ROOT / "shared" / "schemas",
    REPO_ROOT / "shared" / "types",
    REPO_ROOT / "shared" / "vector-store",
]

REQUIRED_KEYS = ["$schema", "$id", "title", "type"]

@dataclass
class SchemaViolation:
    path: Path
    missing_keys: list[str]

    def __str__(self) -> str:
        rel = self.path.relative_to(REPO_ROOT)
        return f"  FAIL  {rel}\n        missing keys: {self.missing_keys}"


@dataclass
class ValidationResult:
    violations: list[SchemaViolation] = field(default_factory=list)
    checked: list[Path] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


def _find_schema_files(scan_dirs: list[Path]) -> list[Path]:
    """Walk scan_dirs and return all .schema.json files (non-recursive into proto/)."""
    found: list[Path] = []
    for base in scan_dirs:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.schema.json")):
            # Skip files inside proto/ subdirectories
            if "proto" in path.parts:
                continue
            found.append(path)
    return found


def _validate_file(schema_path: Path) -> SchemaViolation | None:
    """Return a SchemaViolation if any required key is absent, else None."""
    try:
        data = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return SchemaViolation(path=schema_path, missing_keys=[f"(invalid JSON: {exc})" ])
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        return SchemaViolation(path=schema_path, missing_keys=missing)
    return None

def validate(scan_dirs: list[Path] | None = None) -> ValidationResult:
    """Run validation across all registered scan directories."""
    dirs = scan_dirs if scan_dirs is not None else SCAN_DIRS
    result = ValidationResult()
    for schema_path in _find_schema_files(dirs):
        result.checked.append(schema_path)
        violation = _validate_file(schema_path)
        if violation:
            result.violations.append(violation)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate all JSON Schema files in shared/."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be validated and exit 0 regardless of violations.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate()

    print(f"Checked {len(result.checked)} schema file(s).")

    if args.dry_run:
        for path in result.checked:
            rel = path.relative_to(REPO_ROOT)
            print(f"  OK (dry-run)  {rel}")
        if result.violations:
            print(f"\nWould have reported {len(result.violations)} violation(s):")
            for v in result.violations:
                print(str(v))
        print("\n--dry-run: exiting 0.")
        return 0

    if result.passed:
        for path in result.checked:
            rel = path.relative_to(REPO_ROOT)
            print(f"  PASS  {rel}")
        print("\nAll schemas valid.")
        return 0

    for path in result.checked:
        rel = path.relative_to(REPO_ROOT)
        violation = next((v for v in result.violations if v.path == path), None)
        tag = "FAIL" if violation else "PASS"
        print(f"  {tag}  {rel}")
        if violation:
            print(f"        missing keys: {violation.missing_keys}")

    print(f"\nValidation failed: {len(result.violations)} violation(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
