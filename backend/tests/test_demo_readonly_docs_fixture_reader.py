from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from app.services.demo_readonly_docs_fixture_reader import (
    ACCOUNT_SNAPSHOT,
    DEMO_READONLY_FIXTURE_PATHS,
    DEMO_READONLY_FIXTURES_READ_FAILED,
    DEMO_READONLY_FIXTURES_READ_OK,
    FIXTURE_JSON_INVALID,
    FIXTURE_JSON_NOT_OBJECT,
    FIXTURE_READ_BLOCKED,
    FIXTURE_READ_FAILED,
    FIXTURE_READ_OK,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
    DemoReadOnlyDocsFixtureReadResult,
    DemoReadOnlyDocsFixturesReadAllResult,
    read_all_demo_readonly_docs_fixtures,
    read_demo_readonly_docs_fixture,
)
from app.services.demo_readonly_fixture_path_guard import (
    DemoReadOnlyFixturePathGuardResult,
)


def _assert_single_safety_fields(
    result: DemoReadOnlyDocsFixtureReadResult,
) -> None:
    assert result.read_only is True
    assert result.demo_only is True
    assert result.is_tradable is False
    assert result.can_execute is False


def _assert_all_safety_fields(
    result: DemoReadOnlyDocsFixturesReadAllResult,
) -> None:
    assert result.read_only is True
    assert result.demo_only is True
    assert result.is_tradable is False
    assert result.can_execute is False


@pytest.mark.parametrize("fixture_path", sorted(DEMO_READONLY_FIXTURE_PATHS.values()))
def test_allowed_docs_fixture_paths_read_successfully(fixture_path: str) -> None:
    result = read_demo_readonly_docs_fixture(fixture_path)

    assert result.passed is True
    assert result.status_code == FIXTURE_READ_OK
    assert result.relative_path == fixture_path
    assert result.resolved_path is not None
    assert isinstance(result.payload, dict)
    assert result.payload
    assert result.block_reasons == []
    assert result.warning_reasons == []
    assert result.path_guard_result["passed"] is True
    _assert_single_safety_fields(result)


def test_read_all_reads_three_docs_fixtures() -> None:
    result = read_all_demo_readonly_docs_fixtures()

    assert result.passed is True
    assert result.status_code == DEMO_READONLY_FIXTURES_READ_OK
    assert set(result.fixtures) == {
        ACCOUNT_SNAPSHOT,
        POSITIONS_ORDER_HISTORY,
        MARKET_SYMBOL,
    }
    assert isinstance(result.account_snapshot, dict)
    assert isinstance(result.positions_order_history, dict)
    assert isinstance(result.market_symbol, dict)
    assert result.block_reasons == []
    assert result.warning_reasons == []
    _assert_all_safety_fields(result)


@pytest.mark.parametrize(
    "blocked_path",
    [
        "docs/implementation_plans/dragon_decision_report.example.json",
        "data/demo_account_readonly_snapshot.example.json",
        ".env",
        "../docs/implementation_plans/demo_account_readonly_snapshot.example.json",
        "/tmp/demo_account_readonly_snapshot.example.json",
        r"C:\temp\demo_account_readonly_snapshot.example.json",
        "docs/implementation_plans/demo_account_readonly_snapshot.example.jsonl",
    ],
)
def test_path_guard_blocks_disallowed_paths_before_reading(
    blocked_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(self: Path, *args: object, **kwargs: object) -> str:
        raise AssertionError("reader must not read when PathGuard blocks")

    monkeypatch.setattr(Path, "read_text", fail_if_called)

    result = read_demo_readonly_docs_fixture(blocked_path)

    assert result.passed is False
    assert result.status_code == FIXTURE_READ_BLOCKED
    assert result.payload is None
    assert any(
        reason.startswith("PathGuard blocked fixture path:")
        for reason in result.block_reasons
    )
    assert result.path_guard_result["passed"] is False
    _assert_single_safety_fields(result)


def test_missing_file_returns_failed_without_fallback(tmp_path: Path) -> None:
    fixture_path = DEMO_READONLY_FIXTURE_PATHS[ACCOUNT_SNAPSHOT]

    result = read_demo_readonly_docs_fixture(
        fixture_path,
        project_root=tmp_path,
    )

    assert result.passed is False
    assert result.status_code == FIXTURE_READ_FAILED
    assert result.payload is None
    assert any("fixture file does not exist" in reason for reason in result.block_reasons)
    _assert_single_safety_fields(result)


def test_non_file_returns_failed(tmp_path: Path) -> None:
    fixture_path = DEMO_READONLY_FIXTURE_PATHS[MARKET_SYMBOL]
    directory_path = tmp_path / fixture_path
    directory_path.mkdir(parents=True)

    result = read_demo_readonly_docs_fixture(
        fixture_path,
        project_root=tmp_path,
    )

    assert result.passed is False
    assert result.status_code == FIXTURE_READ_FAILED
    assert result.payload is None
    assert any("fixture path is not a file" in reason for reason in result.block_reasons)
    _assert_single_safety_fields(result)


def test_invalid_json_returns_json_invalid(tmp_path: Path) -> None:
    fixture_path = DEMO_READONLY_FIXTURE_PATHS[POSITIONS_ORDER_HISTORY]
    target_path = tmp_path / fixture_path
    target_path.parent.mkdir(parents=True)
    target_path.write_text("{bad json", encoding="utf-8")

    result = read_demo_readonly_docs_fixture(
        fixture_path,
        project_root=tmp_path,
    )

    assert result.passed is False
    assert result.status_code == FIXTURE_JSON_INVALID
    assert result.payload is None
    assert any("fixture JSON is invalid" in reason for reason in result.block_reasons)
    _assert_single_safety_fields(result)


@pytest.mark.parametrize("payload", [[], "text", 123, None, {}])
def test_non_object_or_empty_json_returns_not_object(
    tmp_path: Path,
    payload: object,
) -> None:
    fixture_path = DEMO_READONLY_FIXTURE_PATHS[ACCOUNT_SNAPSHOT]
    target_path = tmp_path / fixture_path
    target_path.parent.mkdir(parents=True)
    target_path.write_text(json.dumps(payload), encoding="utf-8")

    result = read_demo_readonly_docs_fixture(
        fixture_path,
        project_root=tmp_path,
    )

    assert result.passed is False
    assert result.status_code == FIXTURE_JSON_NOT_OBJECT
    assert result.payload is None
    _assert_single_safety_fields(result)


def test_read_all_returns_failure_when_a_fixture_cannot_be_read(
    tmp_path: Path,
) -> None:
    account_path = tmp_path / DEMO_READONLY_FIXTURE_PATHS[ACCOUNT_SNAPSHOT]
    account_path.parent.mkdir(parents=True)
    account_path.write_text('{"record_type": "demo_account_readonly_snapshot"}', encoding="utf-8")

    positions_path = tmp_path / DEMO_READONLY_FIXTURE_PATHS[POSITIONS_ORDER_HISTORY]
    positions_path.parent.mkdir(parents=True, exist_ok=True)
    positions_path.write_text('{"record_type": "demo_positions_order_history"}', encoding="utf-8")

    result = read_all_demo_readonly_docs_fixtures(project_root=tmp_path)

    assert result.passed is False
    assert result.status_code == DEMO_READONLY_FIXTURES_READ_FAILED
    assert isinstance(result.account_snapshot, dict)
    assert isinstance(result.positions_order_history, dict)
    assert result.market_symbol is None
    assert any(
        reason.startswith("market_symbol fixture read failed:")
        for reason in result.block_reasons
    )
    _assert_all_safety_fields(result)


def test_reader_does_not_call_validators_or_validation_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("reader must not call validators or validation bundle")

    monkeypatch.setattr(
        "app.services.demo_account_readonly_validator.validate_demo_account_readonly_snapshot",
        fail_if_called,
    )
    monkeypatch.setattr(
        "app.services.demo_positions_order_history_validator.validate_demo_positions_order_history",
        fail_if_called,
    )
    monkeypatch.setattr(
        "app.services.demo_market_symbol_readonly_validator.validate_demo_market_symbol_readonly",
        fail_if_called,
    )
    monkeypatch.setattr(
        "app.services.demo_readonly_validation_bundle.validate_demo_readonly_bundle",
        fail_if_called,
    )

    result = read_all_demo_readonly_docs_fixtures()

    assert result.passed is True
    _assert_all_safety_fields(result)


def test_reader_uses_path_guard_before_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path_guard_result = DemoReadOnlyFixturePathGuardResult(
        passed=False,
        status_code="PATH_BLOCKED",
        relative_path="docs/implementation_plans/demo_account_readonly_snapshot.example.json",
        resolved_path=None,
        block_reasons=["blocked by test"],
        warning_reasons=[],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )

    monkeypatch.setattr(
        "app.services.demo_readonly_docs_fixture_reader.validate_demo_readonly_fixture_path",
        lambda *args, **kwargs: path_guard_result,
    )

    def fail_if_called(self: Path, *args: object, **kwargs: object) -> str:
        raise AssertionError("reader must not read when PathGuard fails")

    monkeypatch.setattr(Path, "read_text", fail_if_called)

    result = read_demo_readonly_docs_fixture(
        DEMO_READONLY_FIXTURE_PATHS[ACCOUNT_SNAPSHOT],
    )

    assert result.passed is False
    assert result.status_code == FIXTURE_READ_BLOCKED
    assert result.path_guard_result == asdict(path_guard_result)
    _assert_single_safety_fields(result)


def test_reader_does_not_write_files_or_access_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("reader must not write files or access network")

    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "touch", fail_if_called)

    result = read_demo_readonly_docs_fixture(
        DEMO_READONLY_FIXTURE_PATHS[MARKET_SYMBOL],
    )

    assert result.passed is True
    _assert_single_safety_fields(result)
