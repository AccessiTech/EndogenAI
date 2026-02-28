"""Unit tests for scripts/testing/scaffold_tests.py.

Verifies symbol extraction, stub generation, and --dry-run behaviour without
touching the real workspace.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the scripts/testing directory is importable
_SCRIPTS_TESTING_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_TESTING_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_TESTING_DIR))

import scaffold_tests  # noqa: E402


# ---------------------------------------------------------------------------
# _extract_ts_symbols
# ---------------------------------------------------------------------------


def test_extract_ts_symbols_exported_class() -> None:
    src = """
export class ContextBroker {
  subscribe(id: string): void {}
  publish(ctx: unknown): Promise<void> {}
}
"""
    syms = scaffold_tests._extract_ts_symbols(src)
    class_sym = next((s for s in syms if s.kind == "class"), None)
    assert class_sym is not None
    assert class_sym.name == "ContextBroker"
    assert "subscribe" in class_sym.methods
    assert "publish" in class_sym.methods


def test_extract_ts_symbols_exported_function() -> None:
    src = "export function validateMCPContext(raw: unknown): MCPContext {}\n"
    syms = scaffold_tests._extract_ts_symbols(src)
    assert any(s.name == "validateMCPContext" and s.kind == "function" for s in syms)


def test_extract_ts_symbols_exported_const_arrow() -> None:
    src = "export const createHandler = (id: string) => {}\n"
    syms = scaffold_tests._extract_ts_symbols(src)
    assert any(s.name == "createHandler" for s in syms)


def test_extract_ts_symbols_skips_constructor() -> None:
    src = """
export class Foo {
  constructor(private x: number) {}
  doWork(): void {}
}
"""
    syms = scaffold_tests._extract_ts_symbols(src)
    class_sym = next(s for s in syms if s.kind == "class")
    assert "constructor" not in class_sym.methods
    assert "doWork" in class_sym.methods


# ---------------------------------------------------------------------------
# _extract_py_symbols
# ---------------------------------------------------------------------------


def test_extract_py_symbols_class_with_methods() -> None:
    src = """
class VectorAdapter:
    def upsert(self, items: list) -> None:
        pass
    def query(self, text: str) -> list:
        pass
    def _private(self) -> None:
        pass
"""
    syms = scaffold_tests._extract_py_symbols(src)
    class_sym = next((s for s in syms if s.kind == "class"), None)
    assert class_sym is not None
    assert class_sym.name == "VectorAdapter"
    assert "upsert" in class_sym.methods
    assert "query" in class_sym.methods
    assert "_private" not in class_sym.methods


def test_extract_py_symbols_module_function() -> None:
    src = "def validate_token(token: str) -> bool:\n    pass\n"
    syms = scaffold_tests._extract_py_symbols(src)
    assert any(s.name == "validate_token" and s.kind == "function" for s in syms)


def test_extract_py_symbols_skips_private_functions() -> None:
    src = "def _internal_helper() -> None:\n    pass\n"
    syms = scaffold_tests._extract_py_symbols(src)
    assert not syms


# ---------------------------------------------------------------------------
# _make_ts_stub
# ---------------------------------------------------------------------------


def test_make_ts_stub_contains_describe_and_it(tmp_path: Path) -> None:
    src_file = tmp_path / "broker.ts"
    src_file.write_text("export class ContextBroker {}\n")
    syms = [
        scaffold_tests.TsSymbol(name="ContextBroker", kind="class", methods=["publish"])
    ]
    content = scaffold_tests._make_ts_stub(src_file, syms)
    assert "describe('ContextBroker'" in content
    assert "it('publish" in content
    assert "from '../src/broker.js'" in content


def test_make_ts_stub_function_symbol(tmp_path: Path) -> None:
    src_file = tmp_path / "validate.ts"
    src_file.write_text("")
    syms = [scaffold_tests.TsSymbol(name="validateCtx", kind="function", methods=[])]
    content = scaffold_tests._make_ts_stub(src_file, syms)
    assert "describe('validateCtx'" in content


# ---------------------------------------------------------------------------
# _make_py_stub
# ---------------------------------------------------------------------------


def test_make_py_stub_class(tmp_path: Path) -> None:
    src_file = tmp_path / "adapter.py"
    src_file.write_text("")
    syms = [
        scaffold_tests.PySymbol(name="ChromaAdapter", kind="class", methods=["upsert"])
    ]
    content = scaffold_tests._make_py_stub(src_file, syms)
    assert "class TestChromaAdapter" in content
    assert "def test_upsert" in content


def test_make_py_stub_function(tmp_path: Path) -> None:
    src_file = tmp_path / "utils.py"
    src_file.write_text("")
    syms = [scaffold_tests.PySymbol(name="parse_config", kind="function", methods=[])]
    content = scaffold_tests._make_py_stub(src_file, syms)
    assert "def test_parse_config" in content


# ---------------------------------------------------------------------------
# _get_test_output_path
# ---------------------------------------------------------------------------


def test_get_test_output_path_ts(tmp_path: Path) -> None:
    pkg = tmp_path / "my-pkg"
    src = pkg / "src"
    src.mkdir(parents=True)
    src_file = src / "broker.ts"
    src_file.write_text("")
    out = scaffold_tests._get_test_output_path(src_file)
    assert out is not None
    assert out.name == "broker.test.ts"
    assert out.parent == pkg / "tests"


def test_get_test_output_path_py(tmp_path: Path) -> None:
    pkg = tmp_path / "my-pkg"
    src = pkg / "src"
    src.mkdir(parents=True)
    src_file = src / "adapter.py"
    src_file.write_text("")
    out = scaffold_tests._get_test_output_path(src_file)
    assert out is not None
    assert out.name == "test_adapter.py"
    assert out.parent == pkg / "tests"


def test_get_test_output_path_no_src_dir(tmp_path: Path) -> None:
    src_file = tmp_path / "no_src" / "broker.ts"
    assert scaffold_tests._get_test_output_path(src_file) is None


# ---------------------------------------------------------------------------
# _scaffold_file
# ---------------------------------------------------------------------------


def test_scaffold_file_writes_test_stub(tmp_path: Path) -> None:
    pkg = tmp_path / "mcp"
    src = pkg / "src"
    src.mkdir(parents=True)
    src_file = src / "broker.ts"
    src_file.write_text("export class ContextBroker {\n  publish(): void {}\n}\n")

    written = scaffold_tests._scaffold_file(src_file, dry_run=False)
    assert len(written) == 1
    out = pkg / "tests" / "broker.test.ts"
    assert out.exists()
    assert "describe('ContextBroker'" in out.read_text()


def test_scaffold_file_skips_existing(tmp_path: Path) -> None:
    pkg = tmp_path / "mcp"
    src = pkg / "src"
    tests = pkg / "tests"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    src_file = src / "broker.ts"
    src_file.write_text("")
    existing = tests / "broker.test.ts"
    existing.write_text("// already exists\n")

    written = scaffold_tests._scaffold_file(src_file, dry_run=False)
    assert written == []
    assert existing.read_text() == "// already exists\n"


def test_scaffold_file_dry_run_does_not_write(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:  # type: ignore[type-arg]
    pkg = tmp_path / "mcp"
    src = pkg / "src"
    src.mkdir(parents=True)
    src_file = src / "broker.ts"
    src_file.write_text("export function doThing(): void {}\n")

    written = scaffold_tests._scaffold_file(src_file, dry_run=True)
    assert len(written) == 1
    out = pkg / "tests" / "broker.test.ts"
    assert not out.exists()
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_dry_run_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["scaffold_tests.py", "--dry-run"])
    with patch.object(scaffold_tests, "_find_source_files", return_value=[]):
        exit_code = scaffold_tests.main()
    assert exit_code == 0


def test_main_dry_run_via_argv(tmp_path: Path) -> None:
    import sys as _sys

    pkg = tmp_path / "pkg"
    (pkg / "src").mkdir(parents=True)
    f = pkg / "src" / "thing.ts"
    f.write_text("export function doThing(): void {}\n")

    old_argv = _sys.argv
    _sys.argv = ["scaffold_tests.py", "--file", str(f), "--dry-run"]
    try:
        exit_code = scaffold_tests.main()
    finally:
        _sys.argv = old_argv
    assert exit_code == 0
