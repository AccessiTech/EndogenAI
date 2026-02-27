"""Unit tests for scripts/testing/scan_coverage_gaps.py.

Verifies configuration checks, dry-run behaviour, result dataclasses, and
the main() summary exit codes without invoking real subprocesses.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the scripts/testing directory is importable
_SCRIPTS_TESTING_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_TESTING_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_TESTING_DIR))

import scan_coverage_gaps  # noqa: E402


# ---------------------------------------------------------------------------
# _check_python_config
# ---------------------------------------------------------------------------


def test_check_python_config_warns_when_pytest_cov_missing(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\n')
    warnings = scan_coverage_gaps._check_python_config(tmp_path)
    assert any("pytest-cov" in w for w in warnings)


def test_check_python_config_no_warnings_when_configured(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\n[tool.pytest.ini_options]\naddopts = ["--cov=src"]\n# pytest-cov\n')
    warnings = scan_coverage_gaps._check_python_config(tmp_path)
    assert not warnings


def test_check_python_config_warns_missing_pyproject(tmp_path: Path) -> None:
    warnings = scan_coverage_gaps._check_python_config(tmp_path)
    assert any("pyproject.toml" in w for w in warnings)


# ---------------------------------------------------------------------------
# _check_ts_config
# ---------------------------------------------------------------------------


def test_check_ts_config_warns_when_coverage_v8_missing(tmp_path: Path) -> None:
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text(json.dumps({"name": "@test/pkg", "devDependencies": {"vitest": "^1.0.0"}}))
    warnings = scan_coverage_gaps._check_ts_config(tmp_path, "@test/pkg")
    assert any("@vitest/coverage-v8" in w for w in warnings)


def test_check_ts_config_warns_missing_vitest_config(tmp_path: Path) -> None:
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text(
        json.dumps({"name": "@test/pkg", "devDependencies": {"@vitest/coverage-v8": "^1.0.0"}})
    )
    # No vitest.config.ts present
    warnings = scan_coverage_gaps._check_ts_config(tmp_path, "@test/pkg")
    assert any("vitest.config.ts" in w for w in warnings)


def test_check_ts_config_no_warnings_when_fully_configured(tmp_path: Path) -> None:
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text(
        json.dumps({"name": "@test/pkg", "devDependencies": {"@vitest/coverage-v8": "^1.0.0"}})
    )
    (tmp_path / "vitest.config.ts").write_text("export default {};")
    warnings = scan_coverage_gaps._check_ts_config(tmp_path, "@test/pkg")
    assert not warnings


# ---------------------------------------------------------------------------
# CoverageResult dataclass
# ---------------------------------------------------------------------------


def test_coverage_result_defaults() -> None:
    r = scan_coverage_gaps.CoverageResult(rel_dir="shared/vector-store/python", lang="python", passed=True)
    assert r.coverage_pct is None
    assert r.threshold == scan_coverage_gaps.DEFAULT_THRESHOLD
    assert r.error is None
    assert r.config_warnings == []


# ---------------------------------------------------------------------------
# _run_python_coverage (dry-run)
# ---------------------------------------------------------------------------


def test_run_python_coverage_dry_run_always_passes(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "t"\n# pytest-cov\n')
    (tmp_path / "src").mkdir()
    pkg = scan_coverage_gaps.PyPackage(rel_dir=str(tmp_path), src_subdir="src", threshold=80)

    with patch.object(scan_coverage_gaps, "REPO_ROOT", tmp_path.parent):
        # Adjust the pkg rel_dir to be relative
        pkg2 = scan_coverage_gaps.PyPackage(
            rel_dir=tmp_path.name, src_subdir="src", threshold=80
        )
        # Patch REPO_ROOT so pkg_dir resolves correctly
        with patch.object(scan_coverage_gaps, "REPO_ROOT", tmp_path.parent):
            result = scan_coverage_gaps._run_python_coverage(pkg2, dry_run=True)
    assert result.passed is True


# ---------------------------------------------------------------------------
# _run_ts_coverage (dry-run)
# ---------------------------------------------------------------------------


def test_run_ts_coverage_dry_run_always_passes(tmp_path: Path) -> None:
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text(
        json.dumps({"name": "@t/pkg", "devDependencies": {"@vitest/coverage-v8": "^1"}})
    )
    (tmp_path / "vitest.config.ts").write_text("")
    pkg = scan_coverage_gaps.TsPackage(rel_dir=tmp_path.name, filter_name="@t/pkg", threshold=80)
    with patch.object(scan_coverage_gaps, "REPO_ROOT", tmp_path.parent):
        result = scan_coverage_gaps._run_ts_coverage(pkg, dry_run=True)
    assert result.passed is True


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_dry_run_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["scan_coverage_gaps.py", "--dry-run"])
    mock_result = scan_coverage_gaps.CoverageResult(
        rel_dir="test/pkg", lang="python", passed=True
    )
    with patch.object(scan_coverage_gaps, "_run_python_coverage", return_value=mock_result), \
         patch.object(scan_coverage_gaps, "_run_ts_coverage", return_value=mock_result):
        exit_code = scan_coverage_gaps.main()
    assert exit_code == 0


def test_main_exits_1_when_package_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["scan_coverage_gaps.py"])
    fail_result = scan_coverage_gaps.CoverageResult(
        rel_dir="test/pkg", lang="python", passed=False, coverage_pct=60.0, threshold=80
    )
    pass_result = scan_coverage_gaps.CoverageResult(
        rel_dir="test/ts", lang="typescript", passed=True
    )
    with patch.object(scan_coverage_gaps, "_run_python_coverage", return_value=fail_result), \
         patch.object(scan_coverage_gaps, "_run_ts_coverage", return_value=pass_result):
        exit_code = scan_coverage_gaps.main()
    assert exit_code == 1


def test_main_exits_0_all_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["scan_coverage_gaps.py"])
    pass_result = scan_coverage_gaps.CoverageResult(
        rel_dir="test/pkg", lang="python", passed=True, coverage_pct=85.0, threshold=80
    )
    with patch.object(scan_coverage_gaps, "_run_python_coverage", return_value=pass_result), \
         patch.object(scan_coverage_gaps, "_run_ts_coverage", return_value=pass_result):
        exit_code = scan_coverage_gaps.main()
    assert exit_code == 0
