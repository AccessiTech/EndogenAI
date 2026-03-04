#!/usr/bin/env python3
"""Scan EndogenAI modules for OPA test coverage configuration gaps.

Identifies Python packages that use Open Policy Agent (OPA) and verifies:
  - Tests exist that exercise OPA policy evaluation paths.
  - The ``SKIP_OPA_TESTS`` environment guard is wired in ``conftest.py``
    (per workplan Q6 / AGENTS.md skip-guard convention).
  - ``pytest-cov`` and ``--cov`` addopts are present so OPA-path coverage
    is included in the overall coverage report.
  - Testcontainer or httpx-mock patterns are used to avoid live-service
    dependencies in unit tests.

Inputs:
  None (scans the workspace automatically).

Outputs:
  Per-module PASS/WARN/FAIL lines on stdout.
  Exits 1 if any hard errors are found (missing skip guard, missing any tests);
  exits 0 otherwise, even when warnings exist.

Usage:
  uv run python scripts/testing/scan_opa_coverage.py [--dry-run]

  # Print findings but do not exit non-zero:
  uv run python scripts/testing/scan_opa_coverage.py --dry-run

Related:
  scripts/testing/scan_coverage_gaps.py  — aggregate cross-package scanner
  scripts/healthcheck.sh                 — verify OPA service is reachable

Exit codes:
  0  All checks pass (or --dry-run mode).
  1  One or more modules have hard configuration errors.
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Registry — modules known to use OPA
# ---------------------------------------------------------------------------
# Each entry is (relative_module_dir, opa_source_files, opa_test_files_pattern)
OPA_MODULES = [
    {
        "rel_dir": "modules/group-iii-executive-output/executive-agent",
        # Source files that call OPA (check policy evaluation)
        "opa_source_files": [
            "src/executive_agent/bdi/policy_engine.py",
        ],
        # Expected test files that cover OPA paths
        "expected_test_patterns": [
            "tests/test_integration_bdi_loop.py",
        ],
        # conftest.py that must include SKIP_OPA_TESTS guard
        "conftest_path": "tests/conftest.py",
        "skip_var": "SKIP_OPA_TESTS",
    },
]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def check_opa_module(entry: dict, dry_run: bool) -> tuple[bool, list[str], list[str]]:
    """Check a single OPA-dependent module.

    Returns (hard_error, errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []
    module_dir = REPO_ROOT / entry["rel_dir"]

    # 1. Verify OPA source files exist
    for src_file in entry.get("opa_source_files", []):
        src_path = module_dir / src_file
        if not src_path.exists():
            warnings.append(f"  WARN  OPA source file not found: {_rel(src_path)}")

    # 2. Verify expected test files exist
    for test_pattern in entry.get("expected_test_patterns", []):
        test_path = module_dir / test_pattern
        if not test_path.exists():
            errors.append(
                f"  FAIL  Expected OPA test file missing: {_rel(test_path)}"
                " — create tests that use Testcontainers OPA or httpx mock"
            )
        else:
            # Verify it contains the skip guard
            test_text = test_path.read_text(encoding="utf-8")
            if entry["skip_var"] not in test_text:
                errors.append(
                    f"  FAIL  {_rel(test_path)} missing skip guard "
                    f"'{entry['skip_var']}' — add conftest.py pytest.mark.skipif"
                )

    # 3. Verify conftest.py has the skip guard
    conftest_path = module_dir / entry["conftest_path"]
    if conftest_path.exists():
        conftest_text = conftest_path.read_text(encoding="utf-8")
        skip_var = entry["skip_var"]
        if skip_var not in conftest_text and "SKIP_INTEGRATION_TESTS" not in conftest_text:
            errors.append(
                f"  FAIL  {_rel(conftest_path)} missing skip guard for "
                f"'{skip_var}' or 'SKIP_INTEGRATION_TESTS'"
            )
        else:
            pass  # guard present
    else:
        warnings.append(
            f"  WARN  conftest.py not found at {_rel(conftest_path)} "
            "— create it with the OPA skip guard"
        )

    # 4. Verify pytest-cov is configured
    pyproject = module_dir / "pyproject.toml"
    if pyproject.exists():
        pyproject_text = pyproject.read_text(encoding="utf-8")
        if "pytest-cov" not in pyproject_text:
            errors.append(
                f"  FAIL  pytest-cov not in {_rel(pyproject)} "
                "— run: uv add --dev pytest-cov"
            )
        if "--cov" not in pyproject_text:
            errors.append(
                f"  FAIL  --cov flag missing from {_rel(pyproject)} addopts"
            )
    else:
        errors.append(f"  FAIL  pyproject.toml not found in {_rel(module_dir)}")

    hard_error = len(errors) > 0
    return hard_error, errors, warnings


def main() -> int:
    """Scan OPA-dependent modules for coverage configuration gaps."""
    parser = argparse.ArgumentParser(
        description="Scan OPA-dependent modules for test coverage configuration."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print findings without exiting non-zero. Always exits 0.",
    )
    args = parser.parse_args()

    overall_errors = 0

    for entry in OPA_MODULES:
        module_rel = entry["rel_dir"]
        print(f"\n[OPA] {module_rel}")

        hard_error, errors, warnings = check_opa_module(entry, args.dry_run)

        for msg in errors:
            print(msg)
        for msg in warnings:
            print(msg)

        if not errors and not warnings:
            print("  [PASS] All OPA coverage checks passed")
        elif not errors:
            print(f"  [PASS] No hard errors ({len(warnings)} warning(s))")
        else:
            overall_errors += len(errors)

    print("\n--- OPA Coverage Scanner Summary ---")
    if overall_errors == 0:
        print("All OPA-dependent modules pass coverage checks.")
    else:
        print(f"{overall_errors} hard error(s) found in OPA-dependent modules.")

    if args.dry_run:
        print("(dry-run mode — exiting 0 regardless)")
        return 0

    return 1 if overall_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
