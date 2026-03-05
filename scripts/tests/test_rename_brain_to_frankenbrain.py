"""Unit tests for scripts/rename_brain_to_frankenbrain.py.

Verifies binary detection, per-file processing, dry-run behaviour, and the
main() walk summary without touching the real repository tree.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make the scripts/ root importable so `import rename_brain_to_frankenbrain` works.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import rename_brain_to_frankenbrain as rbt  # noqa: E402


# ---------------------------------------------------------------------------
# is_binary
# ---------------------------------------------------------------------------


def test_is_binary_detects_null_byte(tmp_path: Path) -> None:
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello\x00world")
    assert rbt.is_binary(str(f)) is True


def test_is_binary_text_file(tmp_path: Path) -> None:
    f = tmp_path / "readme.md"
    f.write_text("# Hello frankenbrAIn\n", encoding="utf-8")
    assert rbt.is_binary(str(f)) is False


def test_is_binary_missing_file() -> None:
    assert rbt.is_binary("/nonexistent/path/file.bin") is True


# ---------------------------------------------------------------------------
# process_file
# ---------------------------------------------------------------------------


def test_process_file_replaces_old_string(tmp_path: Path) -> None:
    f = tmp_path / "notes.md"
    f.write_text("The brAIn is the project name.\n", encoding="utf-8")
    changed = rbt.process_file(str(f), dry_run=False)
    assert changed is True
    assert f.read_text(encoding="utf-8") == "The frankenbrAIn is the project name.\n"


def test_process_file_no_change_when_old_absent(tmp_path: Path) -> None:
    f = tmp_path / "notes.md"
    original = "Nothing to replace here.\n"
    f.write_text(original, encoding="utf-8")
    changed = rbt.process_file(str(f), dry_run=False)
    assert changed is False
    assert f.read_text(encoding="utf-8") == original


def test_process_file_dry_run_does_not_write(tmp_path: Path) -> None:
    f = tmp_path / "notes.md"
    original = "The brAIn lives here.\n"
    f.write_text(original, encoding="utf-8")
    changed = rbt.process_file(str(f), dry_run=True)
    assert changed is True
    # File must be untouched in dry-run mode
    assert f.read_text(encoding="utf-8") == original


def test_process_file_skips_binary(tmp_path: Path) -> None:
    f = tmp_path / "image.bin"
    f.write_bytes(b"\x00binary content brAIn")
    changed = rbt.process_file(str(f), dry_run=False)
    assert changed is False


def test_process_file_replaces_multiple_occurrences(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text("brAIn + brAIn = 2x brAIn\n", encoding="utf-8")
    rbt.process_file(str(f), dry_run=False)
    assert f.read_text(encoding="utf-8") == "frankenbrAIn + frankenbrAIn = 2x frankenbrAIn\n"


def test_process_file_handles_unreadable_encoding(tmp_path: Path) -> None:
    f = tmp_path / "latin.txt"
    f.write_bytes(b"\xff\xfe latin1 data")
    # Should return False without raising
    changed = rbt.process_file(str(f), dry_run=False)
    assert changed is False


# ---------------------------------------------------------------------------
# main() via patched os.walk
# ---------------------------------------------------------------------------


def test_main_dry_run_prints_summary(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """main() --dry-run should report the count of files it would update."""
    (tmp_path / "a.md").write_text("brAIn here\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("nothing here\n", encoding="utf-8")

    def fake_walk(root):
        yield str(tmp_path), [], ["a.md", "b.md"]

    with (
        patch.object(rbt, "REPO_ROOT", str(tmp_path)),
        patch("os.walk", fake_walk),
        patch("sys.argv", ["rename_brain_to_frankenbrain.py", "--dry-run"]),
    ):
        rbt.main()

    captured = capsys.readouterr()
    assert "Would update" in captured.out
    assert "1 file" in captured.out


def test_main_applies_changes(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """main() without --dry-run should write changes to disk."""
    target = tmp_path / "target.md"
    target.write_text("brAIn is great\n", encoding="utf-8")

    def fake_walk(root):
        yield str(tmp_path), [], ["target.md"]

    with (
        patch.object(rbt, "REPO_ROOT", str(tmp_path)),
        patch("os.walk", fake_walk),
        patch("sys.argv", ["rename_brain_to_frankenbrain.py"]),
    ):
        rbt.main()

    assert target.read_text(encoding="utf-8") == "frankenbrAIn is great\n"
    captured = capsys.readouterr()
    assert "Updated" in captured.out
    assert "1 file" in captured.out


def test_main_skips_skip_dirs(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Directories in SKIP_DIRS must be pruned from the walk."""
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.md").write_text("brAIn\n", encoding="utf-8")

    real_dirnames: list[str] = ["node_modules"]

    def fake_walk(root):
        yield str(tmp_path), real_dirnames, []

    with (
        patch.object(rbt, "REPO_ROOT", str(tmp_path)),
        patch("os.walk", fake_walk),
        patch("sys.argv", ["rename_brain_to_frankenbrain.py"]),
    ):
        rbt.main()

    # SKIP_DIRS pruning modifies dirnames in-place; node_modules must be removed
    assert "node_modules" not in real_dirnames


def test_main_skips_lockfiles(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Files listed in SKIP_FILES must not be processed."""
    lockfile = tmp_path / "pnpm-lock.yaml"
    original = "brAIn in lockfile\n"
    lockfile.write_text(original, encoding="utf-8")

    def fake_walk(root):
        yield str(tmp_path), [], ["pnpm-lock.yaml"]

    with (
        patch.object(rbt, "REPO_ROOT", str(tmp_path)),
        patch("os.walk", fake_walk),
        patch("sys.argv", ["rename_brain_to_frankenbrain.py"]),
    ):
        rbt.main()

    assert lockfile.read_text(encoding="utf-8") == original
    captured = capsys.readouterr()
    assert "Updated 0 file" in captured.out
