"""Unit tests for scripts/docs/scaffold_doc.py.

Verifies scaffold logic and --dry-run behaviour without touching the real workspace.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the scripts/docs directory is importable
SCRIPTS_DOCS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

import scaffold_doc  # noqa: E402


# ---------------------------------------------------------------------------
# _title_from_path
# ---------------------------------------------------------------------------


def test_title_from_path_hyphenated(tmp_path: Path) -> None:
    d = tmp_path / "signal-processing"
    assert scaffold_doc._title_from_path(d) == "Signal Processing"


def test_title_from_path_underscored(tmp_path: Path) -> None:
    d = tmp_path / "working_memory"
    assert scaffold_doc._title_from_path(d) == "Working Memory"


# ---------------------------------------------------------------------------
# _purpose_from_registry
# ---------------------------------------------------------------------------


def test_purpose_from_registry_match() -> None:
    registry = {"collections": [{"name": "brain.signal", "description": "raw signal"}]}
    result = scaffold_doc._purpose_from_registry("signal", registry)
    assert "brain.signal" in result


def test_purpose_from_registry_no_match() -> None:
    result = scaffold_doc._purpose_from_registry("unknown", {})
    assert "TODO" in result


# ---------------------------------------------------------------------------
# _scaffold_module — file writing
# ---------------------------------------------------------------------------


def test_scaffold_module_creates_readme(tmp_path: Path) -> None:
    """Should write README.md when it does not exist."""
    module_dir = tmp_path / "my-module"
    module_dir.mkdir()

    scaffolded = scaffold_doc._scaffold_module(module_dir, dry_run=False, registry={})

    readme = module_dir / "README.md"
    assert readme.exists()
    assert len(scaffolded) == 1
    content = readme.read_text()
    assert "## Purpose" in content
    assert "## Interface" in content


def test_scaffold_module_skips_existing_readme(tmp_path: Path) -> None:
    """Should not overwrite an existing README.md."""
    module_dir = tmp_path / "my-module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# existing")

    scaffolded = scaffold_doc._scaffold_module(module_dir, dry_run=False, registry={})

    assert scaffolded == []
    assert readme.read_text() == "# existing"


# ---------------------------------------------------------------------------
# dry-run mode
# ---------------------------------------------------------------------------


def test_dry_run_does_not_write(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--dry-run must not write any files."""
    module_dir = tmp_path / "dry-module"
    module_dir.mkdir()

    scaffold_doc._scaffold_module(module_dir, dry_run=True, registry={})

    readme = module_dir / "README.md"
    assert not readme.exists()
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


def test_main_dry_run_exits_0() -> None:
    """main() with --dry-run must exit 0 regardless of workspace state."""
    # Patch MODULES_DIR and INFRA_DIR to point at non-existent tmp dirs
    with patch.object(scaffold_doc, "MODULES_DIR", Path("/does/not/exist")):
        with patch.object(scaffold_doc, "INFRA_DIR", Path("/does/not/exist")):
            exit_code = scaffold_doc.main(["--dry-run"])
    assert exit_code == 0


def test_main_module_filter_no_match_exits_0() -> None:
    """--module with no match should exit 0 (nothing to scaffold)."""
    with patch.object(scaffold_doc, "MODULES_DIR", Path("/does/not/exist")):
        with patch.object(scaffold_doc, "INFRA_DIR", Path("/does/not/exist")):
            exit_code = scaffold_doc.main(["--module", "nonexistent"])
    assert exit_code == 0
