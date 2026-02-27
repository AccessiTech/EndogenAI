#!/usr/bin/env python3
"""Generate documentation scaffolds for EndogenAI modules and packages.

Derivations:
  - Module names and structure from readme.md File Directory.
  - Schema field names from shared/schemas/ and shared/types/.
  - Collection names from shared/vector-store/collection-registry.json.

What is scaffolded:
  - Missing README.md files for modules/ and infrastructure/ packages.
  - Missing JSDoc /** */ stubs for exported TypeScript functions and class methods
    in infrastructure/*/src/ and modules/*/src/ directories.

Usage:
  uv run python scripts/docs/scaffold_doc.py [--module <name>] [--dry-run]

Options:
  --module  Scope to one module (matched against directory names under modules/).
  --dry-run Print generated content to stdout without writing any files.

Exit codes:
  0  Success (or dry-run complete).
  1  Error (missing source file, invalid argument, etc.)."""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODULES_DIR = REPO_ROOT / "modules"
INFRA_DIR = REPO_ROOT / "infrastructure"
SHARED_DIR = REPO_ROOT / "shared"
COLLECTION_REGISTRY = SHARED_DIR / "vector-store" / "collection-registry.json"

MODULE_README_TEMPLATE = """\
# {title}

<!-- TODO: expand -->

## Purpose

{purpose}

## Interface

<!-- TODO: list public functions / classes and link to source -->

## Configuration

<!-- TODO: document environment variables and config schema -->

## Deployment

<!-- TODO: describe how to run locally and in production -->

## References

- [`shared/schemas/`](../../../shared/schemas/) — shared contract definitions
- [`shared/vector-store/collection-registry.json`](../../../shared/vector-store/collection-registry.json)
"""

INFRA_README_TEMPLATE = """\
# {title}

<!-- TODO: expand -->

## Purpose

{purpose}

## Architecture

<!-- TODO: describe component diagram -->

## API

<!-- TODO: list exported symbols and link to source -->

## Running locally

```bash
pnpm install
pnpm run test
```

## Tests

<!-- TODO: describe test strategy -->

## References

- [`shared/schemas/`](../../shared/schemas/) — shared contracts
"""


# ---------------------------------------------------------------------------
# JSDoc patterns
# ---------------------------------------------------------------------------

# Matches exported top-level functions: export [async] function name(params): ReturnType
_EXPORT_FN_RE = re.compile(
    r"^(?P<indent>\s*)export\s+(?:async\s+)?function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)"
    r"(?:\s*:\s*(?P<ret>[^{;\n]+))?",
    re.MULTILINE,
)

# Matches public (or undecorated) class methods — not constructors, not private
_CLASS_METHOD_RE = re.compile(
    r"^(?P<indent>  +)(?:public\s+)?(?:static\s+)?(?:async\s+)?(?P<name>[a-z]\w+)"
    r"\s*\((?P<params>[^)]*)\)(?:\s*:\s*(?P<ret>[^{;\n]+))?(?:\s*\{|;)",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rel(path: Path) -> str:
    """Return path relative to repo root, or the full path if outside the repo."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_collection_registry() -> dict[str, object]:
    """Load collection-registry.json; return empty dict on missing file."""
    if COLLECTION_REGISTRY.exists():
        return json.loads(COLLECTION_REGISTRY.read_text(encoding="utf-8"))  # type: ignore[return-value]
    return {}


def _title_from_path(path: Path) -> str:
    """Convert a directory name to a title-cased heading."""
    return path.name.replace("-", " ").replace("_", " ").title()


def _purpose_from_registry(name: str, registry: dict[str, object]) -> str:
    """Return a purpose hint derived from the collection registry, or a placeholder."""
    collections = registry.get("collections", [])
    if isinstance(collections, list):
        for entry in collections:
            if isinstance(entry, dict) and name in str(entry.get("name", "")):
                return (
                    f"Handles the `{entry.get('name')}` collection — "
                    "see `shared/vector-store/collection-registry.json` for details."
                )
    return "<!-- TODO: describe the module's purpose and brain-region analogy -->"


def _extract_param_names(params_str: str) -> list[str]:
    """Return a list of parameter names from a TypeScript parameter-list string.

    Handles optional markers (?), type annotations (:), default values (=),
    and rest parameters (...).
    """
    if not params_str.strip():
        return []
    names: list[str] = []
    for token in params_str.split(","):
        token = token.strip()
        # Strip rest (...), take the part before : or = or whitespace
        bare = re.split(r"[:\s=?]", token.lstrip("."))[0].strip()
        if bare:
            names.append(bare)
    return names


def _has_jsdoc_above(lines: list[str], line_idx: int) -> bool:
    """Return True if the source line at *line_idx* is preceded by a /** */ block."""
    i = line_idx - 1
    # Skip blank lines
    while i >= 0 and not lines[i].strip():
        i -= 1
    return i >= 0 and lines[i].rstrip().endswith("*/")


def _make_jsdoc_stub(params: list[str], return_type: str | None, indent: str) -> str:
    """Return a JSDoc stub comment string.

    Generates @param tags for every parameter and a @returns tag when the
    inferred return type is not void.  All descriptions are TODO placeholders.
    """
    _VOID_RETURNS = {"void", "Promise<void>", "never", ""}
    stub_lines = [f"{indent}/**"]
    stub_lines.append(f"{indent} * <!-- TODO: describe -->")
    for param in params:
        stub_lines.append(f"{indent} * @param {param} <!-- TODO -->")
    ret = (return_type or "").strip()
    if ret not in _VOID_RETURNS:
        stub_lines.append(f"{indent} * @returns <!-- TODO -->")
    stub_lines.append(f"{indent} */")
    return "\n".join(stub_lines)


def _scaffold_jsdoc(src_file: Path, dry_run: bool) -> list[str]:
    """Insert missing JSDoc stubs into a TypeScript source file.

    Scans *src_file* for exported functions and public class methods that lack
    a preceding /** */ block, then either prints the stubs (dry_run=True) or
    inserts them into the file in place.  Returns a list of modified file paths.
    """
    original = src_file.read_text(encoding="utf-8")
    lines = original.splitlines()

    insertions: list[tuple[int, str]] = []  # (line_index_before, stub_text)

    for pattern in (_EXPORT_FN_RE, _CLASS_METHOD_RE):
        for match in pattern.finditer(original):
            # Convert character offset to line index
            line_idx = original[: match.start()].count("\n")
            if _has_jsdoc_above(lines, line_idx):
                continue
            indent = match.group("indent")
            params = _extract_param_names(match.group("params") or "")
            ret = match.groupdict().get("ret")
            stub = _make_jsdoc_stub(params, ret, indent)
            # Avoid duplicate insertions at the same line
            if not any(li == line_idx for li, _ in insertions):
                insertions.append((line_idx, stub))

    if not insertions:
        return []

    if dry_run:
        print(f"[dry-run] Would insert {len(insertions)} JSDoc stub(s) into: {_rel(src_file)}")
        for line_idx, stub in sorted(insertions):
            fn_line = lines[line_idx] if line_idx < len(lines) else ""
            print(f"  before line {line_idx + 1}: {fn_line.strip()[:60]}")
            print(stub)
        print("---")
    else:
        # Apply insertions in reverse order so line indices stay valid
        for line_idx, stub in sorted(insertions, reverse=True):
            lines.insert(line_idx, stub)
        src_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"JSDoc stubs added: {_rel(src_file)} ({len(insertions)} stub(s))")

    return [str(src_file)]


def _scaffold_module(module_dir: Path, dry_run: bool, registry: dict[str, object]) -> list[str]:
    """Scaffold README.md and JSDoc stubs for a module directory.

    Returns a list of paths that were written (or would be written in dry-run mode).
    """
    readme_path = module_dir / "README.md"
    if readme_path.exists():
        return []

    title = _title_from_path(module_dir)
    purpose = _purpose_from_registry(module_dir.name, registry)
    content = MODULE_README_TEMPLATE.format(title=title, purpose=purpose)

    if dry_run:
        print(f"[dry-run] Would write: {_rel(readme_path)}")
        print(content)
        print("---")
    else:
        readme_path.write_text(content, encoding="utf-8")
        print(f"Scaffolded: {_rel(readme_path)}")

    written = [str(readme_path)]

    # JSDoc stubs for TypeScript src/ files in this module
    src_dir = module_dir / "src"
    if src_dir.is_dir():
        for ts_file in sorted(src_dir.rglob("*.ts")):
            written.extend(_scaffold_jsdoc(ts_file, dry_run))

    return written


def _scaffold_infra(pkg_dir: Path, dry_run: bool) -> list[str]:
    """Scaffold README.md and JSDoc stubs for an infrastructure package.

    Returns a list of paths that were written (or would be written in dry-run mode).
    """
    readme_path = pkg_dir / "README.md"
    if readme_path.exists():
        return []

    title = _title_from_path(pkg_dir)
    purpose = "<!-- TODO: describe the package's role in the communication infrastructure -->"
    content = INFRA_README_TEMPLATE.format(title=title, purpose=purpose)

    if dry_run:
        print(f"[dry-run] Would write: {_rel(readme_path)}")
        print(content)
        print("---")
    else:
        readme_path.write_text(content, encoding="utf-8")
        print(f"Scaffolded: {_rel(readme_path)}")

    written = [str(readme_path)]

    # JSDoc stubs for TypeScript src/ files in this package
    src_dir = pkg_dir / "src"
    if src_dir.is_dir():
        for ts_file in sorted(src_dir.rglob("*.ts")):
            written.extend(_scaffold_jsdoc(ts_file, dry_run))

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the scaffold_doc CLI.

    Scaffolds missing README.md files and JSDoc stubs across modules/ and
    infrastructure/ packages.  Respects --module to scope to a single module
    and --dry-run to preview output without writing any files.

    Returns 0 on success.
    """
    parser = argparse.ArgumentParser(
        description="Scaffold missing documentation files for EndogenAI modules."
    )
    parser.add_argument(
        "--module",
        metavar="NAME",
        help="Scope to a single module by directory name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without creating any files.",
    )
    args = parser.parse_args(argv)

    registry = _load_collection_registry()
    scaffolded: list[str] = []

    # --- Modules ---
    if MODULES_DIR.exists():
        for group_dir in sorted(MODULES_DIR.iterdir()):
            if not group_dir.is_dir():
                continue
            for module_dir in sorted(group_dir.iterdir()):
                if not module_dir.is_dir():
                    continue
                if args.module and module_dir.name != args.module:
                    continue
                scaffolded.extend(_scaffold_module(module_dir, args.dry_run, registry))

    # --- Infrastructure packages ---
    if not args.module and INFRA_DIR.exists():
        for pkg_dir in sorted(INFRA_DIR.iterdir()):
            if pkg_dir.is_dir() and not pkg_dir.name.startswith("."):
                scaffolded.extend(_scaffold_infra(pkg_dir, args.dry_run))

    if not scaffolded:
        print("Nothing to scaffold — all README.md files are present.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
