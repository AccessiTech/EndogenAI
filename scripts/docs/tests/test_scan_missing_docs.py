"""Unit tests for scripts/docs/scan_missing_docs.py.

Verifies gap detection logic and exit code behaviour.
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DOCS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

import scan_missing_docs  # noqa: E402


# ---------------------------------------------------------------------------
# _has_section
# ---------------------------------------------------------------------------


def test_has_section_present(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Title\n\n## Purpose\n\nContent.\n")
    assert scan_missing_docs._has_section(readme, "## Purpose") is True


def test_has_section_absent(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Title\n\nNo sections here.\n")
    assert scan_missing_docs._has_section(readme, "## Purpose") is False


def test_has_section_partial_match_not_counted(tmp_path: Path) -> None:
    """A line like '## Purposes' should not match '## Purpose'."""
    readme = tmp_path / "README.md"
    readme.write_text("# Title\n\n## Purposes\n\nContent.\n")
    assert scan_missing_docs._has_section(readme, "## Purpose") is False


# ---------------------------------------------------------------------------
# ScanResult
# ---------------------------------------------------------------------------


def test_scan_result_counts() -> None:
    result = scan_missing_docs.ScanResult()
    result.add("a/b", "README.md missing", "HIGH")
    result.add("a/b", "section missing", "WARN")
    result.add("a/b", "optional", "INFO")
    assert result.high == 1
    assert result.warn == 1
    assert result.info == 1


# ---------------------------------------------------------------------------
# _scan_dir
# ---------------------------------------------------------------------------


def test_scan_dir_detects_missing_readme(tmp_path: Path) -> None:
    pkg = tmp_path / "my-pkg"
    pkg.mkdir()
    result = scan_missing_docs.ScanResult()
    scan_missing_docs._scan_dir(tmp_path, {"## Purpose"}, result, depth=1)
    assert any("README.md missing" in g.item for g in result.gaps)


def test_scan_dir_detects_missing_section(tmp_path: Path) -> None:
    pkg = tmp_path / "my-pkg"
    pkg.mkdir()
    (pkg / "README.md").write_text("# Title\n")
    result = scan_missing_docs.ScanResult()
    scan_missing_docs._scan_dir(tmp_path, {"## Purpose"}, result, depth=1)
    assert any("## Purpose" in g.item for g in result.gaps)


def test_scan_dir_passes_complete_readme(tmp_path: Path) -> None:
    pkg = tmp_path / "my-pkg"
    pkg.mkdir()
    (pkg / "README.md").write_text("# Title\n\n## Purpose\n\nSome content.\n")
    result = scan_missing_docs.ScanResult()
    scan_missing_docs._scan_dir(tmp_path, {"## Purpose"}, result, depth=1)
    assert result.gaps == []


def test_scan_dir_skips_skip_dirs(tmp_path: Path) -> None:
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    result = scan_missing_docs.ScanResult()
    scan_missing_docs._scan_dir(tmp_path, {"## Purpose"}, result, depth=1)
    assert result.gaps == []


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


def test_main_dry_run_exits_0_with_gaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--dry-run must exit 0 even when gaps are found."""
    # Point all scan dirs at a tmp dir with a missing README
    pkg = tmp_path / "infra-pkg"
    pkg.mkdir()

    monkeypatch.setattr(scan_missing_docs, "MODULES_DIR", tmp_path / "modules")
    monkeypatch.setattr(scan_missing_docs, "INFRA_DIR", tmp_path)
    monkeypatch.setattr(scan_missing_docs, "SHARED_DIR", tmp_path / "shared")

    exit_code = scan_missing_docs.main(["--dry-run"])
    assert exit_code == 0


def test_main_exits_1_with_gaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without --dry-run, gaps must cause exit code 1."""
    pkg = tmp_path / "infra-pkg"
    pkg.mkdir()

    monkeypatch.setattr(scan_missing_docs, "MODULES_DIR", tmp_path / "modules")
    monkeypatch.setattr(scan_missing_docs, "INFRA_DIR", tmp_path)
    monkeypatch.setattr(scan_missing_docs, "SHARED_DIR", tmp_path / "shared")

    exit_code = scan_missing_docs.main([])
    assert exit_code == 1


def test_main_exits_0_no_gaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exit 0 when all required documentation is present."""
    pkg = tmp_path / "infra-pkg"
    pkg.mkdir()
    (pkg / "README.md").write_text(
        "# Infra Pkg\n\n## Purpose\n\nX.\n## Architecture\n\nY.\n## API\n\nZ.\n## Running locally\n\nW.\n"
    )

    monkeypatch.setattr(scan_missing_docs, "MODULES_DIR", tmp_path / "modules")
    monkeypatch.setattr(scan_missing_docs, "INFRA_DIR", tmp_path)
    monkeypatch.setattr(scan_missing_docs, "SHARED_DIR", tmp_path / "shared")

    exit_code = scan_missing_docs.main([])
    assert exit_code == 0
