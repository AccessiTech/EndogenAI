#!/usr/bin/env python3
"""Scan the EndogenAI workspace for modules and packages missing required documentation.

Required documentation per target:
  - Every directory under modules/<group>/ must have a README.md.
  - Every directory under infrastructure/ must have a README.md.
  - Every directory under shared/ (excluding .venv, __pycache__ etc.) must have a README.md.
  - README.md files must contain the required section headings (H2 ##) listed in docs/AGENTS.md.

Usage:
  uv run python scripts/docs/scan_missing_docs.py [--dry-run]

Options:
  --dry-run  Report gaps without exiting non-zero (CI preview mode).

Exit codes:
  0  No gaps found (or --dry-run mode).
  1  One or more required documentation items are missing.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODULES_DIR = REPO_ROOT / "modules"
INFRA_DIR = REPO_ROOT / "infrastructure"
SHARED_DIR = REPO_ROOT / "shared"

# Skip these directories during scans
SKIP_DIRS = {".venv", "node_modules", "dist", "__pycache__", ".git", "tests", "src"}

# Required H2 sections per target type
MODULE_REQUIRED_SECTIONS = {"## Purpose", "## Interface", "## Configuration", "## Deployment"}
INFRA_REQUIRED_SECTIONS = {"## Purpose", "## Architecture", "## API", "## Running locally"}
SHARED_REQUIRED_SECTIONS = {"## Purpose"}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class Gap:
    """A single documentation gap found during a workspace scan."""

    path: str
    item: str
    severity: str  # HIGH | WARN | INFO


@dataclass
class ScanResult:
    """Accumulates Gap instances from a workspace scan."""

    gaps: list[Gap] = field(default_factory=list)

    def add(self, path: str, item: str, severity: str = "HIGH") -> None:
        """Append a new gap with the given path, description, and severity."""
        self.gaps.append(Gap(path=path, item=item, severity=severity))

    @property
    def high(self) -> int:
        return sum(1 for g in self.gaps if g.severity == "HIGH")

    @property
    def warn(self) -> int:
        return sum(1 for g in self.gaps if g.severity == "WARN")

    @property
    def info(self) -> int:
        return sum(1 for g in self.gaps if g.severity == "INFO")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rel(path: Path) -> str:
    """Return path relative to repo root, or the full path if outside the repo."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _has_section(readme: Path, section: str) -> bool:
    """Return True if the README contains the given H2 heading."""
    content = readme.read_text(encoding="utf-8")
    return any(line.strip() == section for line in content.splitlines())


def _check_readme_sections(
    readme: Path,
    required: set[str],
    result: ScanResult,
    rel: str,
) -> None:
    """Record WARN gaps for each required H2 heading absent from *readme*."""
    for section in sorted(required):
        if not _has_section(readme, section):
            result.add(rel, f"README.md missing section `{section}`", "WARN")


def _scan_dir(
    base: Path,
    required_sections: set[str],
    result: ScanResult,
    depth: int = 1,
) -> None:
    """Check immediate subdirectories of base for README.md presence and sections."""
    if not base.exists():
        return
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS or child.name.startswith("."):
            continue
        if depth > 1:
            # Recurse one more level (e.g. modules/<group>/<module>)
            _scan_dir(child, required_sections, result, depth - 1)
            continue
        rel = _rel(child)
        readme = child / "README.md"
        if not readme.exists():
            result.add(rel, "README.md missing", "HIGH")
        else:
            _check_readme_sections(readme, required_sections, result, rel)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_scan() -> ScanResult:
    """Run a full workspace scan and return a ScanResult with all detected gaps.

    Checks modules/, infrastructure/, and shared/ for missing README.md files
    and missing required H2 section headings.
    """
    result = ScanResult()

    # modules/<group>/<module>/ — two levels deep
    _scan_dir(MODULES_DIR, MODULE_REQUIRED_SECTIONS, result, depth=2)

    # infrastructure/<package>/
    _scan_dir(INFRA_DIR, INFRA_REQUIRED_SECTIONS, result, depth=1)

    # shared/ (top-level subdirs only, excluding vector-store sub-packages)
    _scan_dir(SHARED_DIR, SHARED_REQUIRED_SECTIONS, result, depth=1)

    return result


def main(argv: list[str] | None = None) -> int:
    """Entry point for the scan_missing_docs CLI.

    Runs a full workspace scan and prints a gap report.  Exits 1 when gaps are
    found (unless --dry-run is set), exits 0 when the workspace is complete.
    """
    parser = argparse.ArgumentParser(
        description="Report EndogenAI workspace gaps in required documentation."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print gap report without exiting non-zero.",
    )
    args = parser.parse_args(argv)

    result = run_scan()

    if result.gaps:
        print("Documentation gaps found:")
        print()
        print(f"{'Path':<45} {'Missing item':<55} Severity")
        print("-" * 110)
        for gap in result.gaps:
            print(f"{gap.path:<45} {gap.item:<55} {gap.severity}")
        print()
        print(
            f"Completeness result: {len(result.gaps)} gaps found "
            f"({result.high} HIGH, {result.warn} WARN, {result.info} INFO)"
        )
        if args.dry_run:
            print("[dry-run] Exiting 0 despite gaps.")
            return 0
        return 1

    print("Completeness result: PASS — all required documentation present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
