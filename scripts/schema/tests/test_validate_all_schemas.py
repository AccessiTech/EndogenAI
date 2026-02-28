"""Tests for scripts/schema/validate_all_schemas.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/schema is importable as a plain module
_SCRIPTS_SCHEMA_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_SCHEMA_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_SCHEMA_DIR))

import validate_all_schemas  # noqa: E402
from validate_all_schemas import (  # noqa: E402
    REQUIRED_KEYS,
    SchemaViolation,
    ValidationResult,
    _find_schema_files,
    _validate_file,
    main,
    validate,
)


# ---------------------------------------------------------------------------
# _find_schema_files
# ---------------------------------------------------------------------------

class TestFindSchemaFiles:
    def test_finds_schema_json_files(self, tmp_path: Path) -> None:
        (tmp_path / "foo.schema.json").write_text("{}")
        (tmp_path / "bar.json").write_text("{}")  # ignored
        result = _find_schema_files([tmp_path])
        assert len(result) == 1
        assert result[0].name == "foo.schema.json"

    def test_skips_proto_subdirectory(self, tmp_path: Path) -> None:
        proto_dir = tmp_path / "proto"
        proto_dir.mkdir()
        (proto_dir / "thing.schema.json").write_text("{}")
        result = _find_schema_files([tmp_path])
        assert result == []

    def test_missing_scan_dir_skipped(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        result = _find_schema_files([missing])
        assert result == []

    def test_nested_schema_found(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.schema.json").write_text("{}")
        result = _find_schema_files([tmp_path])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _validate_file
# ---------------------------------------------------------------------------

class TestValidateFile:
    def _make_schema(self, tmp_path: Path, data: dict) -> Path:
        p = tmp_path / "test.schema.json"
        p.write_text(json.dumps(data))
        return p

    def test_all_required_keys_present(self, tmp_path: Path) -> None:
        p = self._make_schema(tmp_path, {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/test",
            "title": "Test",
            "description": "A test schema.",
            "type": "object",
        })
        assert _validate_file(p) is None

    def test_missing_single_key(self, tmp_path: Path) -> None:
        p = self._make_schema(tmp_path, {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/test",
            "title": "Test",
            "description": "A test schema.",
        })
        result = _validate_file(p)
        assert result is not None
        assert result.missing_keys == ["type"]

    def test_missing_multiple_keys(self, tmp_path: Path) -> None:
        p = self._make_schema(tmp_path, {"title": "Bare"})
        result = _validate_file(p)
        assert result is not None
        assert set(result.missing_keys) == {"$schema", "$id", "description", "type"}

    def test_invalid_json_reported(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.schema.json"
        p.write_text("{ not valid json")
        result = _validate_file(p)
        assert result is not None
        assert "invalid JSON" in result.missing_keys[0]

    def test_empty_object_reports_all_missing(self, tmp_path: Path) -> None:
        p = self._make_schema(tmp_path, {})
        result = _validate_file(p)
        assert result is not None
        assert set(result.missing_keys) == set(REQUIRED_KEYS)


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

class TestValidate:
    def _valid_schema(self, tmp_path: Path, name: str = "s.schema.json") -> Path:
        p = tmp_path / name
        p.write_text(json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"https://example.com/{name}",
            "title": name,
            "description": "A valid schema.",
            "type": "object",
        }))
        return p

    def test_all_valid_returns_passed(self, tmp_path: Path) -> None:
        self._valid_schema(tmp_path)
        result = validate(scan_dirs=[tmp_path])
        assert result.passed
        assert len(result.checked) == 1
        assert len(result.violations) == 0

    def test_violation_recorded(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.schema.json"
        p.write_text(json.dumps({"title": "No $id"}))
        result = validate(scan_dirs=[tmp_path])
        assert not result.passed
        assert len(result.violations) == 1

    def test_empty_dir_passes(self, tmp_path: Path) -> None:
        result = validate(scan_dirs=[tmp_path])
        assert result.passed
        assert result.checked == []


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

class TestMain:
    def _valid_dir(self, tmp_path: Path) -> Path:
        (tmp_path / "ok.schema.json").write_text(json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/ok",
            "title": "OK",
            "description": "A valid schema.",
            "type": "object",
        }))
        return tmp_path

    def test_dry_run_exits_0_even_with_violations(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        (tmp_path / "bad.schema.json").write_text(json.dumps({"title": "bare"}))
        monkeypatch.setattr("validate_all_schemas.SCAN_DIRS", [tmp_path])
        monkeypatch.setattr("validate_all_schemas.REPO_ROOT", tmp_path.parent)
        monkeypatch.setattr("sys.argv", ["validate_all_schemas.py", "--dry-run"])
        assert main() == 0

    def test_all_pass_exits_0(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._valid_dir(tmp_path)
        monkeypatch.setattr("validate_all_schemas.SCAN_DIRS", [tmp_path])
        monkeypatch.setattr("validate_all_schemas.REPO_ROOT", tmp_path.parent)
        monkeypatch.setattr("sys.argv", ["validate_all_schemas.py"])
        assert main() == 0

    def test_violation_exits_1(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / "bad.schema.json").write_text(json.dumps({"title": "bare"}))
        monkeypatch.setattr("validate_all_schemas.SCAN_DIRS", [tmp_path])
        monkeypatch.setattr("validate_all_schemas.REPO_ROOT", tmp_path.parent)
        monkeypatch.setattr("sys.argv", ["validate_all_schemas.py"])
        assert main() == 1
