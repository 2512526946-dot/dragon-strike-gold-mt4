from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from app.services.demo_readonly_fixture_path_guard import (
    DemoReadOnlyFixturePathGuardResult,
    validate_demo_readonly_fixture_path,
)


FIXTURE_READ_OK = "FIXTURE_READ_OK"
FIXTURE_READ_BLOCKED = "FIXTURE_READ_BLOCKED"
FIXTURE_JSON_INVALID = "FIXTURE_JSON_INVALID"
FIXTURE_JSON_NOT_OBJECT = "FIXTURE_JSON_NOT_OBJECT"
FIXTURE_READ_FAILED = "FIXTURE_READ_FAILED"

DEMO_READONLY_FIXTURES_READ_OK = "DEMO_READONLY_FIXTURES_READ_OK"
DEMO_READONLY_FIXTURES_READ_FAILED = "DEMO_READONLY_FIXTURES_READ_FAILED"

ACCOUNT_SNAPSHOT = "account_snapshot"
POSITIONS_ORDER_HISTORY = "positions_order_history"
MARKET_SYMBOL = "market_symbol"

DEMO_READONLY_FIXTURE_PATHS = {
    ACCOUNT_SNAPSHOT: "docs/implementation_plans/demo_account_readonly_snapshot.example.json",
    POSITIONS_ORDER_HISTORY: "docs/implementation_plans/demo_positions_order_history.example.json",
    MARKET_SYMBOL: "docs/implementation_plans/demo_market_symbol_readonly.example.json",
}


@dataclass(frozen=True)
class DemoReadOnlyDocsFixtureReadResult:
    passed: bool
    status_code: str
    relative_path: str | None
    resolved_path: str | None
    payload: dict[str, Any] | None
    block_reasons: list[str]
    warning_reasons: list[str]
    path_guard_result: dict[str, Any]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool


@dataclass(frozen=True)
class DemoReadOnlyDocsFixturesReadAllResult:
    passed: bool
    status_code: str
    fixtures: dict[str, dict[str, Any]]
    account_snapshot: dict[str, Any] | None
    positions_order_history: dict[str, Any] | None
    market_symbol: dict[str, Any] | None
    block_reasons: list[str]
    warning_reasons: list[str]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool


def read_demo_readonly_docs_fixture(
    relative_path: str | Path | None,
    *,
    project_root: Path | str | None = None,
) -> DemoReadOnlyDocsFixtureReadResult:
    path_guard_result = validate_demo_readonly_fixture_path(
        relative_path,
        project_root=project_root,
    )

    if not path_guard_result.passed:
        return _blocked_read_result(
            FIXTURE_READ_BLOCKED,
            path_guard_result,
            [f"PathGuard blocked fixture path: {reason}" for reason in path_guard_result.block_reasons],
        )

    if path_guard_result.resolved_path is None:
        return _blocked_read_result(
            FIXTURE_READ_FAILED,
            path_guard_result,
            ["PathGuard did not provide a resolved path"],
        )

    fixture_path = Path(path_guard_result.resolved_path)
    try:
        if not fixture_path.exists():
            return _blocked_read_result(
                FIXTURE_READ_FAILED,
                path_guard_result,
                [f"fixture file does not exist: {path_guard_result.relative_path}"],
            )
        if not fixture_path.is_file():
            return _blocked_read_result(
                FIXTURE_READ_FAILED,
                path_guard_result,
                [f"fixture path is not a file: {path_guard_result.relative_path}"],
            )

        parsed_payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        return _blocked_read_result(
            FIXTURE_JSON_INVALID,
            path_guard_result,
            [f"fixture JSON is invalid: {exc.msg}"],
        )
    except (OSError, UnicodeDecodeError) as exc:
        return _blocked_read_result(
            FIXTURE_READ_FAILED,
            path_guard_result,
            [f"fixture read failed: {exc}"],
        )
    except Exception as exc:  # Defensive: reader must fail closed on unexpected errors.
        return _blocked_read_result(
            FIXTURE_READ_FAILED,
            path_guard_result,
            [f"fixture read failed unexpectedly: {exc}"],
        )

    if not isinstance(parsed_payload, dict):
        return _blocked_read_result(
            FIXTURE_JSON_NOT_OBJECT,
            path_guard_result,
            ["fixture JSON must be an object"],
        )

    if not parsed_payload:
        return _blocked_read_result(
            FIXTURE_JSON_NOT_OBJECT,
            path_guard_result,
            ["fixture JSON object must not be empty"],
        )

    return DemoReadOnlyDocsFixtureReadResult(
        passed=True,
        status_code=FIXTURE_READ_OK,
        relative_path=path_guard_result.relative_path,
        resolved_path=path_guard_result.resolved_path,
        payload=parsed_payload,
        block_reasons=[],
        warning_reasons=[],
        path_guard_result=asdict(path_guard_result),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def read_all_demo_readonly_docs_fixtures(
    *,
    project_root: Path | str | None = None,
) -> DemoReadOnlyDocsFixturesReadAllResult:
    fixture_results: dict[str, dict[str, Any]] = {}
    block_reasons: list[str] = []
    payloads: dict[str, dict[str, Any] | None] = {
        ACCOUNT_SNAPSHOT: None,
        POSITIONS_ORDER_HISTORY: None,
        MARKET_SYMBOL: None,
    }

    for fixture_key, relative_path in DEMO_READONLY_FIXTURE_PATHS.items():
        result = read_demo_readonly_docs_fixture(
            relative_path,
            project_root=project_root,
        )
        fixture_results[fixture_key] = asdict(result)
        payloads[fixture_key] = result.payload

        if result.passed:
            continue

        for reason in result.block_reasons:
            block_reasons.append(f"{fixture_key} fixture read failed: {reason}")

    passed = not block_reasons

    return DemoReadOnlyDocsFixturesReadAllResult(
        passed=passed,
        status_code=DEMO_READONLY_FIXTURES_READ_OK
        if passed
        else DEMO_READONLY_FIXTURES_READ_FAILED,
        fixtures=fixture_results,
        account_snapshot=payloads[ACCOUNT_SNAPSHOT],
        positions_order_history=payloads[POSITIONS_ORDER_HISTORY],
        market_symbol=payloads[MARKET_SYMBOL],
        block_reasons=block_reasons,
        warning_reasons=[],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _blocked_read_result(
    status_code: str,
    path_guard_result: DemoReadOnlyFixturePathGuardResult,
    block_reasons: list[str],
) -> DemoReadOnlyDocsFixtureReadResult:
    return DemoReadOnlyDocsFixtureReadResult(
        passed=False,
        status_code=status_code,
        relative_path=path_guard_result.relative_path,
        resolved_path=path_guard_result.resolved_path,
        payload=None,
        block_reasons=block_reasons,
        warning_reasons=[],
        path_guard_result=asdict(path_guard_result),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )
