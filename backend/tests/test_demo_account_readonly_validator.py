from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.services.demo_account_readonly_validator import (
    DEMO_ACCOUNT_READONLY_INVALID,
    DEMO_ACCOUNT_READONLY_VALID,
    DemoAccountReadOnlyValidationResult,
    validate_demo_account_readonly_snapshot,
)


DOCS_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "implementation_plans"
    / "demo_account_readonly_snapshot.example.json"
)


def _example_payload() -> dict[str, Any]:
    with DOCS_EXAMPLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _validate(payload: dict[str, Any]) -> DemoAccountReadOnlyValidationResult:
    return validate_demo_account_readonly_snapshot(payload)


def test_docs_example_json_passes_validation() -> None:
    result = _validate(_example_payload())

    assert isinstance(result, DemoAccountReadOnlyValidationResult)
    assert result.passed is True
    assert result.status_code == DEMO_ACCOUNT_READONLY_VALID
    assert result.block_reasons == []
    assert result.warning_reasons == []
    assert result.is_tradable is False
    assert result.can_execute is False
    assert "read-only" in result.note.lower()
    assert "not trading permission" in result.note.lower()


def test_validator_blocks_non_demo_only_account_mode() -> None:
    payload = _example_payload()
    payload["account_mode"] = "live"

    result = _validate(payload)

    assert result.passed is False
    assert result.status_code == DEMO_ACCOUNT_READONLY_INVALID
    assert "account_mode must be demo_only" in result.block_reasons


def test_validator_blocks_live_account() -> None:
    payload = _example_payload()
    payload["demo_account"]["is_live_account"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "demo_account.is_live_account must be false" in result.block_reasons


def test_validator_blocks_account_number() -> None:
    payload = _example_payload()
    payload["demo_account"]["account_number"] = 123456

    result = _validate(payload)

    assert result.passed is False
    assert "demo_account.account_number must be null" in result.block_reasons


def test_validator_blocks_contains_password() -> None:
    payload = _example_payload()
    payload["safety_flags"]["contains_password"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "safety_flags.contains_password must be false" in result.block_reasons


def test_validator_blocks_contains_credentials() -> None:
    payload = _example_payload()
    payload["safety_flags"]["contains_credentials"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "safety_flags.contains_credentials must be false" in result.block_reasons


def test_validator_blocks_is_tradable() -> None:
    payload = _example_payload()
    payload["safety_flags"]["is_tradable"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "safety_flags.is_tradable must be false" in result.block_reasons
    assert result.is_tradable is False


def test_validator_blocks_can_execute() -> None:
    payload = _example_payload()
    payload["safety_flags"]["can_execute"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "safety_flags.can_execute must be false" in result.block_reasons
    assert result.can_execute is False


def test_validator_blocks_read_only_false() -> None:
    payload = _example_payload()
    payload["bridge_status"]["read_only"] = False

    result = _validate(payload)

    assert result.passed is False
    assert "bridge_status.read_only must be true" in result.block_reasons


def test_validator_blocks_ask_below_bid() -> None:
    payload = _example_payload()
    payload["symbol_snapshot"]["bid"] = 2300.8
    payload["symbol_snapshot"]["ask"] = 2300.5

    result = _validate(payload)

    assert result.passed is False
    assert (
        "symbol_snapshot.ask must be greater than or equal to bid"
        in result.block_reasons
    )


def test_validator_blocks_negative_spread() -> None:
    payload = _example_payload()
    payload["symbol_snapshot"]["spread"] = -0.1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "symbol_snapshot.spread must be greater than or equal to 0"
        in result.block_reasons
    )


def test_validator_blocks_missing_equity() -> None:
    payload = _example_payload()
    payload["demo_account"].pop("equity")

    result = _validate(payload)

    assert result.passed is False
    assert "demo_account.equity must be a number" in result.block_reasons


def test_validator_blocks_non_xauusd_symbol() -> None:
    payload = _example_payload()
    payload["symbol_snapshot"]["symbol"] = "EURUSD"

    result = _validate(payload)

    assert result.passed is False
    assert "symbol_snapshot.symbol must be XAUUSD" in result.block_reasons


def test_validator_blocks_missing_required_identity_and_safety_fields() -> None:
    payload = deepcopy(_example_payload())
    payload.pop("generated_at")
    payload["record_type"] = "other"
    payload["demo_account"]["is_demo_account"] = False
    payload["safety_flags"]["demo_only"] = False
    payload["safety_flags"]["contains_live_account"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "record_type must be demo_account_readonly_snapshot" in result.block_reasons
    assert "generated_at must exist" in result.block_reasons
    assert "demo_account.is_demo_account must be true" in result.block_reasons
    assert "safety_flags.demo_only must be true" in result.block_reasons
    assert "safety_flags.contains_live_account must be false" in result.block_reasons


def test_validator_blocks_unsafe_note() -> None:
    payload = _example_payload()
    payload["note"] = "example only"

    result = _validate(payload)

    assert result.passed is False
    assert "note must mention read-only" in result.block_reasons
    assert "note must mention not trading advice" in result.block_reasons
    assert "note must mention not trading permission" in result.block_reasons


def test_validator_reads_docs_example_not_data_runtime_files() -> None:
    result = _validate(_example_payload())

    assert result.passed is True
    assert "docs/implementation_plans" in str(DOCS_EXAMPLE_PATH).replace("\\", "/")
    assert "data/mt4" not in str(DOCS_EXAMPLE_PATH).replace("\\", "/")
