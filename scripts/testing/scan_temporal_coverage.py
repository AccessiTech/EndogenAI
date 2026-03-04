#!/usr/bin/env python3
"""Scan EndogenAI modules for Temporal workflow test coverage configuration gaps.

Identifies Python packages that use Temporal (or its Prefect fallback) and
verifies:
  - Tests exist for workflow and worker code paths (``workflow.py``,
    ``worker.py``, ``prefect_fallback.py``).
  - The ``SKIP_TEMPORAL_TESTS`` and ``SKIP_INTEGRATION_TESTS`` environment
    guards are wired in ``conftest.py`` (per workplan Q6 decision).
  - ``temporalio.testing.WorkflowEnvironment.start_time_skipping()`` is used
    for integration tests so no live Temporal dev server is required.
  - ``pytest-cov`` and ``--cov`` addopts are present in ``pyproject.toml``.
  - The Prefect fallback (``prefect_fallback.py``) is covered by unit tests
    using mocked ``httpx`` without any external dependencies.

Inputs:
  None (scans the workspace automatically).

Outputs:
  Per-module PASS/WARN/FAIL lines on stdout.
  Exits 1 if any hard errors are found (missing tests, missing skip guards,
  missing coverage config); exits 0 otherwise.

Usage:
  uv run python scripts/testing/scan_temporal_coverage.py [--dry-run]

  # Print findings but do not exit non-zero:
  uv run python scripts/testing/scan_temporal_coverage.py --dry-run

Related:
  scripts/testing/scan_coverage_gaps.py  — aggregate cross-package scanner
  scripts/testing/scan_opa_coverage.py   — OPA specialist scanner
  scripts/healthcheck.sh                 — verify backing services

Exit codes:
  0  All checks pass (or --dry-run mode).
  1  One or more modules have hard configuration errors.
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Registry — modules known to use Temporal or Prefect
# ---------------------------------------------------------------------------
TEMPORAL_MODULES = [
    {
        "rel_dir": "modules/group-iii-executive-output/agent-runtime",
        # Source files that implement Temporal workflows/workers
        "temporal_source_files": [
            "src/agent_runtime/workflow.py",
            "src/agent_runtime/worker.py",
            "src/agent_runtime/prefect_fallback.py",
        ],
        # Expected test files that cover Temporal paths
        "expected_test_files": [
            "tests/test_orchestrator.py",
        ],
        # conftest.py that must include skip guard
        "conftest_path": "tests/conftest.py",
        "skip_vars": ["SKIP_TEMPORAL_TESTS", "SKIP_INTEGRATION_TESTS"],
        # Patterns that indicate correct in-process testing approach
        "preferred_test_patterns": [
            "start_time_skipping",      # temporalio in-process env
            "WorkflowEnvironment",      # temporalio testing module
        ],
        # Patterns indicating correct prefect unit test approach
        "prefect_unit_patterns": [
            "_run_sequential",          # mocked prefect_fallback unit test
            "httpx",                    # mock pattern
        ],
    },
]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def check_temporal_module(entry: dict, dry_run: bool) -> tuple[bool, list[str], list[str]]:
    """Check a single Temporal-dependent module.

    Returns (hard_error_flag, error_messages, warning_messages).
    """
    errors: list[str] = []
    warnings: list[str] = []
    module_dir = REPO_ROOT / entry["rel_dir"]

    # 1. Verify Temporal/Prefect source files exist
    for src_file in entry.get("temporal_source_files", []):
        src_path = module_dir / src_file
        if not src_path.exists():
            warnings.append(
                f"  WARN  Temporal source file not found: {_rel(src_path)}"
                " (may not be implemented yet)"
            )

    # 2. Verify expected test files exist and contain correct patterns
    for test_file in entry.get("expected_test_files", []):
        test_path = module_dir / test_file
        if not test_path.exists():
            errors.append(
                f"  FAIL  Expected Temporal test file missing: {_rel(test_path)}"
                " — create orchestrator/workflow tests"
            )
        else:
            test_text = test_path.read_text(encoding="utf-8")
            # Check for preferred in-process testing pattern
            preferred = entry.get("preferred_test_patterns", [])
            has_preferred = any(p in test_text for p in preferred)
            if not has_preferred:
                warnings.append(
                    f"  WARN  {_rel(test_path)} does not use"
                    " WorkflowEnvironment.start_time_skipping() — prefer"
                    " in-process temporal testing over live dev server"
                )

    # 3. Check prefect_fallback has unit tests (no external deps)
    prefect_src = module_dir / "src/agent_runtime/prefect_fallback.py"
    if prefect_src.exists():
        # Look for a test file that covers prefect_fallback
        prefect_test_candidates = list(module_dir.glob("tests/test_*prefect*.py"))
        if not prefect_test_candidates:
            # Also check if prefect is covered in any test file
            all_test_texts = ""
            for tf in module_dir.glob("tests/test_*.py"):
                all_test_texts += tf.read_text(encoding="utf-8")
            if "prefect_fallback" not in all_test_texts and "_run_sequential" not in all_test_texts:
                errors.append(
                    f"  FAIL  prefect_fallback.py has no unit tests covering"
                    " _run_sequential() — create mocked-httpx unit tests"
                    " (no external deps required)"
                )

    # 4. Verify conftest.py has the skip guards
    conftest_path = module_dir / entry["conftest_path"]
    if conftest_path.exists():
        conftest_text = conftest_path.read_text(encoding="utf-8")
        skip_vars = entry.get("skip_vars", [])
        missing_guards = [v for v in skip_vars if v not in conftest_text]
        if missing_guards:
            # It's acceptable if SKIP_INTEGRATION_TESTS covers Temporal tests too
            if "SKIP_INTEGRATION_TESTS" in conftest_text:
                warnings.append(
                    f"  WARN  {_rel(conftest_path)} uses SKIP_INTEGRATION_TESTS"
                    " but is missing fine-grained SKIP_TEMPORAL_TESTS guard."
                    " Add it for per-service control."
                )
            else:
                errors.append(
                    f"  FAIL  {_rel(conftest_path)} missing all skip guards"
                    f" {skip_vars} — add pytest.mark.skipif guards"
                )
    else:
        errors.append(
            f"  FAIL  conftest.py not found at {_rel(conftest_path)}"
            " — create it with SKIP_TEMPORAL_TESTS + SKIP_INTEGRATION_TESTS guards"
        )

    # 5. Verify pytest-cov is configured
    pyproject = module_dir / "pyproject.toml"
    if pyproject.exists():
        pyproject_text = pyproject.read_text(encoding="utf-8")
        if "pytest-cov" not in pyproject_text:
            errors.append(
                f"  FAIL  pytest-cov not in {_rel(pyproject)}"
                " — run: uv add --dev pytest-cov"
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
    """Scan Temporal/Prefect-dependent modules for coverage configuration gaps."""
    parser = argparse.ArgumentParser(
        description="Scan Temporal-dependent modules for test coverage configuration."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print findings without exiting non-zero. Always exits 0.",
    )
    args = parser.parse_args()

    overall_errors = 0

    for entry in TEMPORAL_MODULES:
        module_rel = entry["rel_dir"]
        print(f"\n[Temporal] {module_rel}")

        hard_error, errors, warnings = check_temporal_module(entry, args.dry_run)

        for msg in errors:
            print(msg)
        for msg in warnings:
            print(msg)

        if not errors and not warnings:
            print("  [PASS] All Temporal coverage checks passed")
        elif not errors:
            print(f"  [PASS] No hard errors ({len(warnings)} warning(s))")
        else:
            overall_errors += len(errors)

    print("\n--- Temporal Coverage Scanner Summary ---")
    if overall_errors == 0:
        print("All Temporal-dependent modules pass coverage checks.")
    else:
        print(f"{overall_errors} hard error(s) found in Temporal-dependent modules.")

    if args.dry_run:
        print("(dry-run mode — exiting 0 regardless)")
        return 0

    return 1 if overall_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
