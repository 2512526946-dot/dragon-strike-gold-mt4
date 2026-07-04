from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.services.demo_positions_order_history_validator import (
    DEMO_POSITIONS_ORDER_HISTORY_INVALID,
    DEMO_POSITIONS_ORDER_HISTORY_VALID,
    DemoPositionsOrderHistoryValidationResult,
    validate_demo_positions_order_history,
)


DOCS_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "implementation_plans"
    / "demo_positions_order_history.example.json"
)


def _example_payload() -> dict[str, Any]:
    with DOCS_EXAMPLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _validate(payload: dict[str, Any]) -> DemoPositionsOrderHistoryValidationResult:
    return validate_demo_positions_order_history(payload)


def test_docs_example_json_passes_validation() -> None:
    result = _validate(_example_payload())

    assert isinstance(result, DemoPositionsOrderHistoryValidationResult)
    assert result.passed is True
    assert result.status_code == DEMO_POSITIONS_ORDER_HISTORY_VALID
    assert result.block_reasons == []
    assert result.warning_reasons == []
    assert result.is_tradable is False
    assert result.can_execute is False
    assert "read-only" in result.note.lower()
    assert "not trading permission" in result.note.lower()


def test_validator_blocks_wrong_record_type() -> None:
    payload = _example_payload()
    payload["record_type"] = "other"

    result = _validate(payload)

    assert result.passed is False
    assert result.status_code == DEMO_POSITIONS_ORDER_HISTORY_INVALID
    assert "record_type must be demo_positions_order_history" in result.block_reasons


def test_validator_blocks_non_demo_only_account_mode() -> None:
    payload = _example_payload()
    payload["account_mode"] = "live"

    result = _validate(payload)

    assert result.passed is False
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


def test_validator_blocks_order_instruction_flag() -> None:
    payload = _example_payload()
    payload["safety_flags"]["is_order_instruction"] = True

    result = _validate(payload)

    assert result.passed is False
    assert "safety_flags.is_order_instruction must be false" in result.block_reasons


def test_validator_blocks_open_positions_count_mismatch() -> None:
    payload = _example_payload()
    payload["open_positions_summary"]["open_positions_count"] = 2

    result = _validate(payload)

    assert result.passed is False
    assert (
        "open_positions_summary.open_positions_count must equal open_positions count"
        in result.block_reasons
    )


def test_validator_blocks_open_position_missing_stop_loss() -> None:
    payload = _example_payload()
    payload["open_positions"][0].pop("stop_loss")

    result = _validate(payload)

    assert result.passed is False
    assert "open_positions[0].stop_loss must exist and not be null" in result.block_reasons


def test_validator_blocks_open_position_lot_not_positive() -> None:
    payload = _example_payload()
    payload["open_positions"][0]["lot"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "open_positions[0].lot must be greater than 0" in result.block_reasons


def test_validator_blocks_open_position_symbol_not_xauusd() -> None:
    payload = _example_payload()
    payload["open_positions"][0]["symbol"] = "EURUSD"

    result = _validate(payload)

    assert result.passed is False
    assert "open_positions[0].symbol must be XAUUSD" in result.block_reasons


def test_validator_blocks_open_position_direction_not_long_or_short() -> None:
    payload = _example_payload()
    payload["open_positions"][0]["direction"] = "flat"

    result = _validate(payload)

    assert result.passed is False
    assert "open_positions[0].direction must be long or short" in result.block_reasons


def test_validator_blocks_negative_consecutive_losses() -> None:
    payload = _example_payload()
    payload["order_history_summary"]["consecutive_losses"] = -1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "order_history_summary.consecutive_losses must be a non-negative integer"
        in result.block_reasons
    )


def test_validator_blocks_closed_orders_count_mismatch() -> None:
    payload = _example_payload()
    payload["order_history_summary"]["closed_orders_count"] = 1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "order_history_summary.closed_orders_count must equal closed_orders count"
        in result.block_reasons
    )


def test_validator_blocks_closed_order_missing_closed_pnl() -> None:
    payload = _example_payload()
    payload["closed_orders"][0].pop("closed_pnl")

    result = _validate(payload)

    assert result.passed is False
    assert "closed_orders[0].closed_pnl must be a number" in result.block_reasons


def test_validator_blocks_closed_order_symbol_not_xauusd() -> None:
    payload = _example_payload()
    payload["closed_orders"][0]["symbol"] = "EURUSD"

    result = _validate(payload)

    assert result.passed is False
    assert "closed_orders[0].symbol must be XAUUSD" in result.block_reasons


def test_validator_blocks_closed_order_lot_not_positive() -> None:
    payload = _example_payload()
    payload["closed_orders"][0]["lot"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "closed_orders[0].lot must be greater than 0" in result.block_reasons


def test_validator_blocks_negative_summary_values() -> None:
    payload = deepcopy(_example_payload())
    payload["open_positions_summary"]["open_positions_count"] = -1
    payload["open_positions_summary"]["total_lots"] = -0.01
    payload["order_history_summary"]["orders_count"] = -1
    payload["order_history_summary"]["closed_orders_count"] = -1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "open_positions_summary.open_positions_count must be a non-negative integer"
        in result.block_reasons
    )
    assert (
        "open_positions_summary.total_lots must be a non-negative number"
        in result.block_reasons
    )
    assert (
        "order_history_summary.orders_count must be a non-negative integer"
        in result.block_reasons
    )
    assert (
        "order_history_summary.closed_orders_count must be a non-negative integer"
        in result.block_reasons
    )


def test_validator_blocks_missing_identity_and_safety_fields() -> None:
    payload = deepcopy(_example_payload())
    payload.pop("generated_at")
    payload["demo_account"]["is_demo_account"] = False
    payload["safety_flags"]["demo_only"] = False
    payload["safety_flags"]["contains_live_account"] = True

    result = _validate(payload)

    assert result.passed is False
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
