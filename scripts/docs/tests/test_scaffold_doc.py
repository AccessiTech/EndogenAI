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


# ---------------------------------------------------------------------------
# JSDoc helpers
# ---------------------------------------------------------------------------


def test_extract_param_names_basic() -> None:
    assert scaffold_doc._extract_param_names("a: string, b: number") == ["a", "b"]


def test_extract_param_names_empty() -> None:
    assert scaffold_doc._extract_param_names("") == []


def test_extract_param_names_optional_and_rest() -> None:
    result = scaffold_doc._extract_param_names("...args: string[], opt?: boolean")
    assert result == ["args", "opt"]


def test_has_jsdoc_above_true() -> None:
    lines = ["/**", " * doc", " */", "export function foo() {}"]
    assert scaffold_doc._has_jsdoc_above(lines, 3) is True


def test_has_jsdoc_above_false() -> None:
    lines = ["const x = 1;", "", "export function foo() {}"]
    assert scaffold_doc._has_jsdoc_above(lines, 2) is False


def test_make_jsdoc_stub_with_params_and_return() -> None:
    stub = scaffold_doc._make_jsdoc_stub(["name", "value"], "string", "  ")
    assert "@param name" in stub
    assert "@param value" in stub
    assert "@returns" in stub


def test_make_jsdoc_stub_void_no_returns() -> None:
    stub = scaffold_doc._make_jsdoc_stub(["x"], "void", "")
    assert "@returns" not in stub


def test_make_jsdoc_stub_promise_void_no_returns() -> None:
    stub = scaffold_doc._make_jsdoc_stub([], "Promise<void>", "")
    assert "@returns" not in stub


def test_scaffold_jsdoc_inserts_stub(tmp_path: Path) -> None:
    """Should insert a stub for an exported function that has no JSDoc."""
    src = tmp_path / "index.ts"
    src.write_text("export function greet(name: string): string {\n  return name;\n}\n")
    result = scaffold_doc._scaffold_jsdoc(src, dry_run=False)
    assert len(result) == 1
    content = src.read_text()
    assert "/**" in content
    assert "@param name" in content
    assert "@returns" in content


def test_scaffold_jsdoc_skips_existing_jsdoc(tmp_path: Path) -> None:
    """Should not insert a stub when a JSDoc block already exists."""
    src = tmp_path / "index.ts"
    src.write_text("/**\n * Already documented.\n */\nexport function foo(): void {}\n")
    result = scaffold_doc._scaffold_jsdoc(src, dry_run=False)
    assert result == []


def test_scaffold_jsdoc_dry_run_no_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """dry_run=True must print the stub but not modify the file."""
    src = tmp_path / "index.ts"
    original = "export function bar(x: number): number {\n  return x;\n}\n"
    src.write_text(original)
    scaffold_doc._scaffold_jsdoc(src, dry_run=True)
    assert src.read_text() == original
    out = capsys.readouterr().out
    assert "dry-run" in out
