#!/usr/bin/env python3
"""Generate documentation scaffolds for EndogenAI modules and packages.

Derivations:
  - Module names and structure from readme.md File Directory.
  - Schema field names from shared/schemas/ and shared/types/.
  - Collection names from shared/vector-store/collection-registry.json.

Usage:
  uv run python scripts/docs/scaffold_doc.py [--module <name>] [--dry-run]

Options:
  --module  Scope to one module (matched against directory names under modules/).
  --dry-run Print generated content to stdout without writing any files.

Exit codes:
  0  Success (or dry-run complete).
  1  Error (missing source file, invalid argument, etc.).
"""

import argparse
import json
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


def _scaffold_module(module_dir: Path, dry_run: bool, registry: dict[str, object]) -> list[str]:
    """Return a list of (path, content) tuples that would be written."""
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

    return [str(readme_path)]


def _scaffold_infra(pkg_dir: Path, dry_run: bool) -> list[str]:
    """Scaffold README.md for an infrastructure package if missing."""
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

    return [str(readme_path)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
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
