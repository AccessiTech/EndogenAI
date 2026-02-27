#!/usr/bin/env python3
"""Scan EndogenAI packages for test coverage gaps.

Runs pytest-cov (Python) and vitest --coverage (TypeScript) for all tracked
packages and reports those below their declared coverage threshold.

In --dry-run mode the coverage commands are printed but not executed, and the
script always exits 0.

Usage:
  uv run python scripts/testing/scan_coverage_gaps.py [--dry-run]

Exit codes:
  0  All packages pass thresholds, or --dry-run mode.
  1  One or more packages below threshold or a blocking configuration gap.

Setup required per package
--------------------------
Python:
  cd <package-dir> && uv add --dev pytest-cov

  pyproject.toml additions:
    [tool.pytest.ini_options]
    addopts = ["--cov=src", "--cov-fail-under=80"]
    [tool.coverage.report]
    fail_under = 80

TypeScript:
  pnpm add -D @vitest/coverage-v8 --filter <pkg-name>

  vitest.config.ts:
    import { defineConfig } from 'vitest/config';
    export default defineConfig({
      test: {
        coverage: {
          provider: 'v8',
          reporter: ['text', 'json', 'json-summary'],
          thresholds: { lines: 80, functions: 80, branches: 80 },
        },
      },
    });
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Package registry
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD = 80  # % lines / functions / branches


@dataclass
class PyPackage:
    """A Python sub-package to scan for coverage."""

    rel_dir: str
    src_subdir: str = "src"
    threshold: int = DEFAULT_THRESHOLD


@dataclass
class TsPackage:
    """A TypeScript package to scan for coverage."""

    rel_dir: str
    filter_name: str  # pnpm --filter value
    threshold: int = DEFAULT_THRESHOLD


# Add entries here as new sub-packages are created.
PYTHON_PACKAGES: list[PyPackage] = [
    PyPackage("shared/vector-store/python", src_subdir="src"),
]

TS_PACKAGES: list[TsPackage] = [
    TsPackage("infrastructure/mcp", filter_name="@accessitech/mcp"),
    TsPackage("infrastructure/a2a", filter_name="@accessitech/a2a"),
    TsPackage("infrastructure/adapters", filter_name="@accessitech/adapters"),
]

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CoverageResult:
    """Coverage outcome for a single package."""

    rel_dir: str
    lang: str  # 'python' | 'typescript'
    passed: bool
    coverage_pct: float | None = None  # None = could not determine
    threshold: int = DEFAULT_THRESHOLD
    error: str | None = None
    config_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Configuration checks
# ---------------------------------------------------------------------------


def _rel(path: Path) -> str:
    """Return repo-relative path string, or str(path) if outside the repo."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _check_python_config(pkg_dir: Path) -> list[str]:
    """Return configuration warnings for a Python sub-package."""
    warnings: list[str] = []
    pyproject = pkg_dir / "pyproject.toml"
    if not pyproject.exists():
        warnings.append(f"{_rel(pkg_dir)}: missing pyproject.toml")
        return warnings
    text = pyproject.read_text(encoding="utf-8")
    if "pytest-cov" not in text:
        warnings.append(
            f"{_rel(pkg_dir)}: pytest-cov not in pyproject.toml — "
            f"run: cd {_rel(pkg_dir)} && uv add --dev pytest-cov"
        )
    return warnings


def _check_ts_config(pkg_dir: Path, filter_name: str) -> list[str]:
    """Return configuration warnings for a TypeScript package."""
    warnings: list[str] = []
    pkg_json_path = pkg_dir / "package.json"
    if not pkg_json_path.exists():
        warnings.append(f"{_rel(pkg_dir)}: missing package.json")
        return warnings
    try:
        pkg_data = json.loads(pkg_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warnings.append(f"{_rel(pkg_dir)}: invalid package.json")
        return warnings

    dev_deps = pkg_data.get("devDependencies", {})
    if "@vitest/coverage-v8" not in dev_deps:
        warnings.append(
            f"{_rel(pkg_dir)}: @vitest/coverage-v8 missing — "
            f"run: pnpm add -D @vitest/coverage-v8 --filter {filter_name}"
        )
    if not (pkg_dir / "vitest.config.ts").exists():
        warnings.append(
            f"{_rel(pkg_dir)}: no vitest.config.ts — create one with "
            "coverage.thresholds to enforce per-package targets"
        )
    return warnings


# ---------------------------------------------------------------------------
# Coverage runners
# ---------------------------------------------------------------------------


def _run_python_coverage(pkg: PyPackage, dry_run: bool) -> CoverageResult:
    """Run pytest --cov for a Python sub-package."""
    pkg_dir = REPO_ROOT / pkg.rel_dir
    config_warnings = _check_python_config(pkg_dir)

    cmd = [
        "uv",
        "run",
        "pytest",
        f"--cov={pkg.src_subdir}",
        "--cov-report=term-missing",
        "--cov-report=json:coverage.json",
        f"--cov-fail-under={pkg.threshold}",
        "-q",
    ]

    print(f"\n[python] {pkg.rel_dir}")
    for w in config_warnings:
        print(f"  WARN: {w}")
    print(f"  cmd: {' '.join(cmd)}")

    if dry_run:
        return CoverageResult(
            rel_dir=pkg.rel_dir,
            lang="python",
            passed=True,
            threshold=pkg.threshold,
            config_warnings=config_warnings,
        )

    try:
        result = subprocess.run(
            cmd,
            cwd=str(pkg_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        coverage_pct: float | None = None
        cov_json = pkg_dir / "coverage.json"
        if cov_json.exists():
            try:
                data = json.loads(cov_json.read_text(encoding="utf-8"))
                totals = data.get("totals", {})
                coverage_pct = float(totals.get("percent_covered", 0))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        passed = result.returncode == 0
        if not passed:
            sys.stdout.write(result.stdout[-2000:] if result.stdout else "")
            sys.stderr.write(result.stderr[-500:] if result.stderr else "")

        return CoverageResult(
            rel_dir=pkg.rel_dir,
            lang="python",
            passed=passed,
            coverage_pct=coverage_pct,
            threshold=pkg.threshold,
            config_warnings=config_warnings,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return CoverageResult(
            rel_dir=pkg.rel_dir,
            lang="python",
            passed=False,
            error=str(exc),
            threshold=pkg.threshold,
            config_warnings=config_warnings,
        )


def _run_ts_coverage(pkg: TsPackage, dry_run: bool) -> CoverageResult:
    """Run vitest --coverage for a TypeScript package."""
    pkg_dir = REPO_ROOT / pkg.rel_dir
    config_warnings = _check_ts_config(pkg_dir, pkg.filter_name)

    cmd = [
        "pnpm",
        "--filter",
        pkg.filter_name,
        "run",
        "test",
        "--",
        "--coverage",
        "--coverage.reporter=json-summary",
        "--coverage.reporter=text",
    ]

    print(f"\n[typescript] {pkg.rel_dir}")
    for w in config_warnings:
        print(f"  WARN: {w}")
    print(f"  cmd: {' '.join(cmd)}")

    if dry_run:
        return CoverageResult(
            rel_dir=pkg.rel_dir,
            lang="typescript",
            passed=True,
            threshold=pkg.threshold,
            config_warnings=config_warnings,
        )

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        coverage_pct: float | None = None
        cov_json = pkg_dir / "coverage" / "coverage-summary.json"
        if cov_json.exists():
            try:
                data = json.loads(cov_json.read_text(encoding="utf-8"))
                lines_info = data.get("total", {}).get("lines", {})
                coverage_pct = float(lines_info.get("pct", 0))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        passed = result.returncode == 0
        if not passed:
            sys.stdout.write(result.stdout[-2000:] if result.stdout else "")
            sys.stderr.write(result.stderr[-500:] if result.stderr else "")

        return CoverageResult(
            rel_dir=pkg.rel_dir,
            lang="typescript",
            passed=passed,
            coverage_pct=coverage_pct,
            threshold=pkg.threshold,
            config_warnings=config_warnings,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return CoverageResult(
            rel_dir=pkg.rel_dir,
            lang="typescript",
            passed=False,
            error=str(exc),
            threshold=pkg.threshold,
            config_warnings=config_warnings,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Scan all registered packages for coverage gaps and print a summary."""
    parser = argparse.ArgumentParser(
        description="Scan EndogenAI packages for test coverage gaps."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print coverage commands without running them. Always exits 0.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("Coverage commands that would run (dry-run mode):")

    results: list[CoverageResult] = []
    for pkg in PYTHON_PACKAGES:
        results.append(_run_python_coverage(pkg, dry_run=args.dry_run))
    for pkg in TS_PACKAGES:
        results.append(_run_ts_coverage(pkg, dry_run=args.dry_run))

    print("\n--- Coverage Summary ---")
    failures = 0
    total_config_issues = 0
    for r in results:
        pct_str = f"{r.coverage_pct:.1f}%" if r.coverage_pct is not None else "n/a"
        status = "PASS" if r.passed else "FAIL"
        print(
            f"  [{status}] {r.lang:10s} {r.rel_dir:<45s}"
            f" coverage={pct_str} (threshold={r.threshold}%)"
        )
        if r.error:
            print(f"           error: {r.error}")
        total_config_issues += len(r.config_warnings)
        if not r.passed:
            failures += 1

    if total_config_issues:
        print(f"\n{total_config_issues} configuration issue(s) found.")
        print("Run with --dry-run to see all setup instructions.")

    if args.dry_run:
        print("\ndry-run complete \u2014 no tests were executed.")
        return 0

    if failures:
        print(f"\n{failures} package(s) below coverage threshold. Fix and re-run.")
        return 1

    print("\nAll packages meet their coverage thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
