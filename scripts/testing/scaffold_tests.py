#!/usr/bin/env python3
"""Generate test file stubs for EndogenAI source files.

Parses TypeScript and Python source files to extract exported symbols
(functions, classes, and class methods) and produces test skeleton files:
  - vitest describe/it blocks for TypeScript (.ts → tests/<name>.test.ts)
  - pytest class/function stubs   for Python  (.py → tests/test_<name>.py)

No business logic is inferred — stubs contain only signatures and TODO markers.

Usage:
  uv run python scripts/testing/scaffold_tests.py [--file <path>] [--dry-run]

Options:
  --file     Absolute or repo-relative path to one source file.
  --dry-run  Print generated content to stdout without writing any files.

Exit codes:
  0  Success or dry-run complete.
  1  Error (file not found, unsupported extension, etc.)
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Regex patterns — TypeScript
# ---------------------------------------------------------------------------
_TS_EXPORT_CLASS_RE = re.compile(
    r"^export\s+(?:abstract\s+|default\s+)?class\s+(\w+)", re.MULTILINE
)
_TS_EXPORT_FN_RE = re.compile(
    r"^export\s+(?:async\s+)?function\s+(\w+)", re.MULTILINE
)
_TS_EXPORT_CONST_FN_RE = re.compile(
    r"^export\s+const\s+(\w+)\s*[=:][^;]*?(?:\(|=>)", re.MULTILINE
)
_TS_METHOD_RE = re.compile(
    r"^\s{2,4}(?:(?:public|private|protected|async|static|override|abstract)\s+)*"
    r"(\w+)\s*(?:<[^>]*>)?\s*\(",
    re.MULTILINE,
)
_TS_SKIP_METHODS = frozenset(
    {"constructor", "if", "for", "while", "switch", "return", "catch", "try", "get", "set"}
)

# ---------------------------------------------------------------------------
# Regex patterns — Python
# ---------------------------------------------------------------------------
_PY_CLASS_RE = re.compile(r"^class\s+(\w+)", re.MULTILINE)
_PY_FN_RE = re.compile(r"^def\s+((?!_)\w+)\s*\(", re.MULTILINE)
_PY_METHOD_RE = re.compile(r"^\s{4}def\s+((?!_)\w+)\s*\(", re.MULTILINE)
_PY_SKIP_METHODS = frozenset({"init", "new", "repr", "str", "len", "eq", "hash"})


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@dataclass
class TsSymbol:
    """An exported TypeScript symbol discovered in a source file."""

    name: str
    kind: str  # 'class' | 'function'
    methods: list[str] = field(default_factory=list)


@dataclass
class PySymbol:
    """A public Python symbol discovered in a source file."""

    name: str
    kind: str  # 'class' | 'function'
    methods: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rel(path: Path) -> str:
    """Return repo-relative path string, or str(path) if outside the repo."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _extract_ts_class_body(src: str, start: int) -> str:
    """Return the text inside the first { ... } block after *start*."""
    i = start
    while i < len(src) and src[i] != "{":
        i += 1
    if i >= len(src):
        return ""
    depth = 1
    i += 1
    body_start = i
    while i < len(src) and depth > 0:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
        i += 1
    return src[body_start : i - 1]


def _extract_py_class_body(src: str, start: int) -> str:
    """Return only the indented body lines of a Python class beginning at *start*."""
    lines = src[start:].splitlines(keepends=True)
    body_lines: list[str] = []
    found_body = False
    for line in lines:
        if not found_body:
            if line.strip():
                found_body = True
                body_lines.append(line)
        else:
            if line and not line[0].isspace() and line.strip():
                break
            body_lines.append(line)
    return "".join(body_lines)


def _extract_ts_symbols(src: str) -> list[TsSymbol]:
    """Extract exported TypeScript classes and functions from source text."""
    symbols: list[TsSymbol] = []

    for fn_match in _TS_EXPORT_FN_RE.finditer(src):
        symbols.append(TsSymbol(name=fn_match.group(1), kind="function"))

    for fn_match in _TS_EXPORT_CONST_FN_RE.finditer(src):
        name = fn_match.group(1)
        if not any(s.name == name for s in symbols):
            symbols.append(TsSymbol(name=name, kind="function"))

    for class_match in _TS_EXPORT_CLASS_RE.finditer(src):
        class_name = class_match.group(1)
        body = _extract_ts_class_body(src, class_match.end())
        methods = [
            m.group(1)
            for m in _TS_METHOD_RE.finditer(body)
            if m.group(1) not in _TS_SKIP_METHODS
        ]
        symbols.append(TsSymbol(name=class_name, kind="class", methods=methods))

    return symbols


def _make_ts_stub(src_file: Path, symbols: list[TsSymbol]) -> str:
    """Build a vitest test stub for a TypeScript source file."""
    stem = src_file.stem
    lines: list[str] = [
        "/**",
        f" * Tests for {src_file.name}",
        " * TODO: implement meaningful assertions — remove all placeholder stubs.",
        " */",
        "",
        "import { describe, it, expect, vi, beforeEach } from 'vitest';",
        f"// TODO: import the symbols under test",
        f"import {{  }} from '../src/{stem}.js';",
        "",
    ]

    for sym in symbols:
        if sym.kind == "class":
            lines.append(f"describe('{sym.name}', () => {{")
            lines.append(f"  // TODO: construct {sym.name} in beforeEach")
            lines.append("")
            for method in sym.methods:
                lines += [
                    f"  it('{method} \u2014 TODO: describe expected behaviour', () => {{",
                    "    // ARRANGE",
                    "    // ACT",
                    "    // ASSERT",
                    "    expect(true).toBe(false); // TODO: replace with real assertion",
                    "  });",
                    "",
                ]
            lines.append("});")
            lines.append("")
        elif sym.kind == "function":
            lines += [
                f"describe('{sym.name}', () => {{",
                f"  it('{sym.name} \u2014 TODO: describe expected behaviour', () => {{",
                "    // ARRANGE",
                "    // ACT",
                "    // ASSERT",
                "    expect(true).toBe(false); // TODO: replace with real assertion",
                "  });",
                "});",
                "",
            ]

    return "\n".join(lines) + "\n"


def _extract_py_symbols(src: str) -> list[PySymbol]:
    """Extract public Python classes and module-level functions from source text."""
    symbols: list[PySymbol] = []

    for fn_match in _PY_FN_RE.finditer(src):
        symbols.append(PySymbol(name=fn_match.group(1), kind="function"))

    for class_match in _PY_CLASS_RE.finditer(src):
        class_name = class_match.group(1)
        body = _extract_py_class_body(src, class_match.end())
        methods = [
            m.group(1)
            for m in _PY_METHOD_RE.finditer(body)
            if m.group(1) not in _PY_SKIP_METHODS
        ]
        symbols.append(PySymbol(name=class_name, kind="class", methods=methods))

    return symbols


def _make_py_stub(src_file: Path, symbols: list[PySymbol]) -> str:
    """Build a pytest test stub for a Python source file."""
    lines: list[str] = [
        f'"""Tests for {_rel(src_file)} \u2014 TODO: implement all stubs."""',
        "import pytest",
        "",
    ]

    for sym in symbols:
        if sym.kind == "class":
            lines.append(f"class Test{sym.name}:")
            if not sym.methods:
                lines += [
                    "    def test_placeholder(self) -> None:",
                    "        # TODO: implement",
                    '        assert False, "stub \u2014 replace with real assertion"',
                ]
            for method in sym.methods:
                lines += [
                    f"    def test_{method}(self) -> None:",
                    "        # TODO: implement",
                    '        assert False, "stub \u2014 replace with real assertion"',
                    "",
                ]
            lines.append("")
        elif sym.kind == "function":
            lines += [
                f"def test_{sym.name}() -> None:",
                "    # TODO: implement",
                '    assert False, "stub \u2014 replace with real assertion"',
                "",
            ]

    return "\n".join(lines) + "\n"


def _get_test_output_path(src_file: Path) -> Path | None:
    """Derive the expected test file path for a given source file.

    Returns None if the source file is not in a recognised src/ layout.
    """
    src_file = src_file.resolve()
    parts = src_file.parts
    try:
        # Walk from the right to find the innermost 'src' directory component
        src_idx = len(parts) - 1 - list(reversed(parts)).index("src")
    except ValueError:
        return None

    pkg_root = Path(*parts[:src_idx])
    tests_dir = pkg_root / "tests"
    stem = src_file.stem

    if src_file.suffix == ".ts":
        return tests_dir / f"{stem}.test.ts"
    if src_file.suffix == ".py":
        return tests_dir / f"test_{stem}.py"
    return None


def _scaffold_file(src_file: Path, dry_run: bool) -> list[str]:
    """Scaffold a test stub for a single source file.

    Returns a list of file paths written (or that would be written in dry-run).
    """
    src_file = src_file.resolve()

    if not src_file.exists():
        print(f"ERROR: source file not found: {_rel(src_file)}", file=sys.stderr)
        return []

    out_path = _get_test_output_path(src_file)
    if out_path is None:
        print(f"SKIP: {_rel(src_file)} \u2014 not in a recognised src/ layout")
        return []

    if out_path.exists():
        print(f"SKIP: {_rel(out_path)} already exists")
        return []

    src = src_file.read_text(encoding="utf-8")

    if src_file.suffix == ".ts":
        symbols = _extract_ts_symbols(src)
        content = _make_ts_stub(src_file, symbols)
    elif src_file.suffix == ".py":
        symbols_py = _extract_py_symbols(src)
        content = _make_py_stub(src_file, symbols_py)
    else:
        print(f"SKIP: {_rel(src_file)} \u2014 unsupported extension {src_file.suffix}", file=sys.stderr)
        return []

    if dry_run:
        print(f"--- {_rel(out_path)} (dry-run) ---")
        print(content)
        return [str(out_path)]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"wrote {_rel(out_path)}")
    return [str(out_path)]


def _find_source_files() -> list[Path]:
    """Discover all TypeScript and Python source files under known src/ directories."""
    files: list[Path] = []
    search_roots = [
        REPO_ROOT / "infrastructure",
        REPO_ROOT / "modules",
        REPO_ROOT / "shared",
    ]
    for root in search_roots:
        for src_dir in root.rglob("src"):
            if not src_dir.is_dir():
                continue
            files.extend(src_dir.glob("*.ts"))
            files.extend(src_dir.glob("*.py"))
    return sorted(files)


def main() -> int:
    """Entry point — parse arguments and scaffold test stubs."""
    parser = argparse.ArgumentParser(
        description="Generate test file stubs from source file interfaces."
    )
    parser.add_argument("--file", metavar="PATH", help="Scope to one source file.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print without writing any files."
    )
    args = parser.parse_args()

    if args.file:
        src_files = [Path(args.file)]
    else:
        src_files = _find_source_files()

    if not src_files:
        print("No source files found.")
        return 0

    written: list[str] = []
    for src_file in src_files:
        written.extend(_scaffold_file(src_file, dry_run=args.dry_run))

    if args.dry_run:
        print(f"\ndry-run: {len(written)} file(s) would be written.")
    else:
        print(f"\nScaffolded {len(written)} test file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
