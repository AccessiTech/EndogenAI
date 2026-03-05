#!/usr/bin/env python3
"""
Script to rename brAIn => frankenbrAIn throughout the EndogenAI repository.

Usage:
    python scripts/rename_brain_to_frankenbrain.py [--dry-run]

Replaces all occurrences of the string 'brAIn' with 'frankenbrAIn' in all
text files in the repository, excluding binary files and generated/dependency
directories.
"""

import os
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "dist",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
}

SKIP_FILES = {
    "pnpm-lock.yaml",
    "uv.lock",
}

OLD = "brAIn"
NEW = "frankenbrAIn"


def is_binary(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except OSError:
        return True


def process_file(path: str, dry_run: bool) -> bool:
    if is_binary(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError):
        return False

    if OLD not in content:
        return False

    new_content = content.replace(OLD, NEW)
    if dry_run:
        print(f"[dry-run] Would update: {os.path.relpath(path, REPO_ROOT)}")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated: {os.path.relpath(path, REPO_ROOT)}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Rename brAIn => frankenbrAIn")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    changed = 0
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # Prune skipped directories in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if filename in SKIP_FILES:
                continue
            filepath = os.path.join(dirpath, filename)
            if process_file(filepath, args.dry_run):
                changed += 1

    action = "Would update" if args.dry_run else "Updated"
    print(f"\n{action} {changed} file(s).")


if __name__ == "__main__":
    main()
