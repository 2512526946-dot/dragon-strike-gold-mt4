from __future__ import annotations

from pathlib import Path

import pytest

from app.services.demo_readonly_fixture_path_guard import (
    ALLOWED_DEMO_READONLY_FIXTURE_PATHS,
    PATH_ALLOWED,
    PATH_BLOCKED,
    DemoReadOnlyFixturePathGuardResult,
    validate_demo_readonly_fixture_path,
)


def _validate(path: str | Path | None) -> DemoReadOnlyFixturePathGuardResult:
    return validate_demo_readonly_fixture_path(path)


def _assert_safety_fields(result: DemoReadOnlyFixturePathGuardResult) -> None:
    assert result.read_only is True
    assert result.demo_only is True
    assert result.is_tradable is False
    assert result.can_execute is False


@pytest.mark.parametrize("fixture_path", sorted(ALLOWED_DEMO_READONLY_FIXTURE_PATHS))
def test_allowed_docs_fixture_paths_pass(fixture_path: str) -> None:
    result = _validate(fixture_path)

    assert result.passed is True
    assert result.status_code == PATH_ALLOWED
    assert result.relative_path == fixture_path
    assert result.resolved_path is not None
    assert result.block_reasons == []
    assert result.warning_reasons == []
    _assert_safety_fields(result)


@pytest.mark.parametrize("fixture_path", sorted(ALLOWED_DEMO_READONLY_FIXTURE_PATHS))
def test_backslash_allowed_docs_fixture_paths_are_normalized(
    fixture_path: str,
) -> None:
    result = _validate(fixture_path.replace("/", "\\"))

    assert result.passed is True
    assert result.relative_path == fixture_path
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/demo_account_readonly_snapshot.example.json",
        r"C:\temp\demo_account_readonly_snapshot.example.json",
        r"\\server\share\demo_account_readonly_snapshot.example.json",
    ],
)
def test_absolute_paths_are_blocked(path: str) -> None:
    result = _validate(path)

    assert result.passed is False
    assert result.status_code == PATH_BLOCKED
    assert "absolute paths are not allowed" in result.block_reasons
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "path",
    [
        "../docs/implementation_plans/demo_account_readonly_snapshot.example.json",
        "docs/../implementation_plans/demo_account_readonly_snapshot.example.json",
        "docs/implementation_plans/..hidden/demo_account_readonly_snapshot.example.json",
    ],
)
def test_path_traversal_is_blocked(path: str) -> None:
    result = _validate(path)

    assert result.passed is False
    assert "path traversal is not allowed" in result.block_reasons
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".git/config.json",
        "docs/.hidden/demo_account_readonly_snapshot.example.json",
        ".pytest_cache/cache.json",
    ],
)
def test_hidden_files_and_directories_are_blocked(path: str) -> None:
    result = _validate(path)

    assert result.passed is False
    assert "hidden files or directories are not allowed" in result.block_reasons
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    ("path", "expected_reason"),
    [
        ("data/demo_account_readonly_snapshot.example.json", "data directory is not allowed"),
        ("logs/demo_account_readonly_snapshot.example.json", "logs directory is not allowed"),
        ("frontend/dist/demo_account_readonly_snapshot.example.json", "frontend/dist directory is not allowed"),
        ("frontend/node_modules/demo_account_readonly_snapshot.example.json", "frontend/node_modules directory is not allowed"),
        ("models/demo_account_readonly_snapshot.example.json", "models directory is not allowed"),
        ("backend/__pycache__/demo_account_readonly_snapshot.example.json", "__pycache__ directory is not allowed"),
    ],
)
def test_blocked_directories_are_rejected(path: str, expected_reason: str) -> None:
    result = _validate(path)

    assert result.passed is False
    assert expected_reason in result.block_reasons
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "keyword",
    [
        "password",
        "credential",
        "secret",
        "token",
        "key",
        "login",
        "real_account",
        "live_account",
    ],
)
def test_sensitive_keyword_paths_are_rejected(keyword: str) -> None:
    result = _validate(f"docs/implementation_plans/{keyword}.example.json")

    assert result.passed is False
    assert f"path must not contain sensitive keyword: {keyword}" in result.block_reasons
    _assert_safety_fields(result)


@pytest.mark.parametrize(
    "path",
    [
        "docs/implementation_plans/demo_account_readonly_snapshot.example.jsonl",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.csv",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.parquet",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.db",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.sqlite",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.duckdb",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.log",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.env",
    ],
)
def test_non_json_extensions_are_rejected(path: str) -> None:
    result = _validate(path)

    assert result.passed is False
    assert "path must use a .json extension" in result.block_reasons
    _assert_safety_fields(result)


def test_json_path_outside_whitelist_is_rejected() -> None:
    result = _validate("docs/implementation_plans/dragon_decision_report.example.json")

    assert result.passed is False
    assert "path must be one of the allowed demo readonly fixtures" in result.block_reasons
    _assert_safety_fields(result)


@pytest.mark.parametrize("path", ["", "   ", None])
def test_empty_or_none_path_is_rejected(path: str | None) -> None:
    result = _validate(path)

    assert result.passed is False
    assert result.relative_path is None
    assert "path must be a non-empty relative path" in result.block_reasons
    _assert_safety_fields(result)


def test_resolved_path_stays_inside_project_root(tmp_path: Path) -> None:
    fixture_path = "docs/implementation_plans/demo_market_symbol_readonly.example.json"

    result = validate_demo_readonly_fixture_path(
        fixture_path,
        project_root=tmp_path,
    )

    assert result.passed is True
    assert result.resolved_path is not None
    assert Path(result.resolved_path).is_relative_to(tmp_path)
    _assert_safety_fields(result)


def test_path_guard_does_not_need_fixture_file_contents(tmp_path: Path) -> None:
    fixture_path = "docs/implementation_plans/demo_account_readonly_snapshot.example.json"
    missing_fixture_path = tmp_path / fixture_path
    assert missing_fixture_path.exists() is False

    result = validate_demo_readonly_fixture_path(
        fixture_path,
        project_root=tmp_path,
    )

    assert result.passed is True
    assert result.relative_path == fixture_path
    _assert_safety_fields(result)
