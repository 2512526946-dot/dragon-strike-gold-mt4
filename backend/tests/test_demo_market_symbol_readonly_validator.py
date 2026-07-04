from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.demo_market_symbol_readonly_validator import (
    DEMO_MARKET_SYMBOL_READONLY_INVALID,
    DEMO_MARKET_SYMBOL_READONLY_VALID,
    DemoMarketSymbolReadOnlyValidationResult,
    validate_demo_market_symbol_readonly,
)


DOCS_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "implementation_plans"
    / "demo_market_symbol_readonly.example.json"
)


def _example_payload() -> dict[str, Any]:
    with DOCS_EXAMPLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _validate(payload: dict[str, Any]) -> DemoMarketSymbolReadOnlyValidationResult:
    return validate_demo_market_symbol_readonly(payload)


def test_docs_example_json_passes_validation() -> None:
    result = _validate(_example_payload())

    assert isinstance(result, DemoMarketSymbolReadOnlyValidationResult)
    assert result.passed is True
    assert result.status_code == DEMO_MARKET_SYMBOL_READONLY_VALID
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
    assert result.status_code == DEMO_MARKET_SYMBOL_READONLY_INVALID
    assert "record_type must be demo_market_symbol_readonly" in result.block_reasons


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


def test_validator_blocks_non_xauusd_symbol() -> None:
    payload = _example_payload()
    payload["symbol"] = "EURUSD"

    result = _validate(payload)

    assert result.passed is False
    assert "symbol must be XAUUSD" in result.block_reasons


def test_validator_blocks_ask_below_bid() -> None:
    payload = _example_payload()
    payload["quote"]["bid"] = 2300.8
    payload["quote"]["ask"] = 2300.5

    result = _validate(payload)

    assert result.passed is False
    assert "quote.ask must be greater than or equal to bid" in result.block_reasons


def test_validator_blocks_negative_spread() -> None:
    payload = _example_payload()
    payload["quote"]["spread"] = -0.1

    result = _validate(payload)

    assert result.passed is False
    assert "quote.spread must be greater than or equal to 0" in result.block_reasons


def test_validator_blocks_negative_spread_points() -> None:
    payload = _example_payload()
    payload["quote"]["spread_points"] = -1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "quote.spread_points must be greater than or equal to 0"
        in result.block_reasons
    )


def test_validator_blocks_negative_last_update_age_seconds() -> None:
    payload = _example_payload()
    payload["quote"]["last_update_age_seconds"] = -1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "quote.last_update_age_seconds must be greater than or equal to 0"
        in result.block_reasons
    )


def test_validator_blocks_tick_size_not_positive() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["tick_size"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "symbol_spec.tick_size must be greater than 0" in result.block_reasons


def test_validator_blocks_tick_value_not_positive() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["tick_value"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "symbol_spec.tick_value must be greater than 0" in result.block_reasons


def test_validator_blocks_contract_size_not_positive() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["contract_size"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "symbol_spec.contract_size must be greater than 0" in result.block_reasons


def test_validator_blocks_min_lot_not_positive() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["min_lot"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "symbol_spec.min_lot must be greater than 0" in result.block_reasons


def test_validator_blocks_max_lot_below_min_lot() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["min_lot"] = 0.1
    payload["symbol_spec"]["max_lot"] = 0.01

    result = _validate(payload)

    assert result.passed is False
    assert (
        "symbol_spec.max_lot must be greater than or equal to min_lot"
        in result.block_reasons
    )


def test_validator_blocks_lot_step_not_positive() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["lot_step"] = 0

    result = _validate(payload)

    assert result.passed is False
    assert "symbol_spec.lot_step must be greater than 0" in result.block_reasons


def test_validator_blocks_negative_stop_level_points() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["stop_level_points"] = -1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "symbol_spec.stop_level_points must be greater than or equal to 0"
        in result.block_reasons
    )


def test_validator_blocks_negative_freeze_level_points() -> None:
    payload = _example_payload()
    payload["symbol_spec"]["freeze_level_points"] = -1

    result = _validate(payload)

    assert result.passed is False
    assert (
        "symbol_spec.freeze_level_points must be greater than or equal to 0"
        in result.block_reasons
    )


def test_validator_blocks_market_open_not_boolean() -> None:
    payload = _example_payload()
    payload["market_session"]["market_open"] = "true"

    result = _validate(payload)

    assert result.passed is False
    assert "market_session.market_open must be boolean" in result.block_reasons


def test_validator_blocks_trade_allowed_by_broker_not_boolean() -> None:
    payload = _example_payload()
    payload["market_session"]["trade_allowed_by_broker"] = "true"

    result = _validate(payload)

    assert result.passed is False
    assert (
        "market_session.trade_allowed_by_broker must be boolean"
        in result.block_reasons
    )


def test_validator_blocks_missing_note() -> None:
    payload = _example_payload()
    payload.pop("note")

    result = _validate(payload)

    assert result.passed is False
    assert "note must exist" in result.block_reasons


def test_validator_blocks_missing_identity_and_market_fields() -> None:
    payload = _example_payload()
    payload.pop("generated_at")
    payload["demo_account"]["is_demo_account"] = False
    payload["safety_flags"]["demo_only"] = False
    payload["safety_flags"]["contains_live_account"] = True
    payload["safety_flags"]["is_trade_signal"] = True
    payload["safety_flags"]["is_trade_plan"] = True
    payload["safety_flags"]["is_execution_permission"] = True
    payload["quote"].pop("last_tick_time")
    payload["symbol_spec"]["digits"] = -1
    payload["market_session"]["is_major_news_window"] = "false"
    payload["market_session"]["is_rollover_window"] = "false"
    payload["market_session"]["is_weekend"] = "false"

    result = _validate(payload)

    assert result.passed is False
    assert "generated_at must exist" in result.block_reasons
    assert "demo_account.is_demo_account must be true" in result.block_reasons
    assert "safety_flags.demo_only must be true" in result.block_reasons
    assert "safety_flags.contains_live_account must be false" in result.block_reasons
    assert "safety_flags.is_trade_signal must be false" in result.block_reasons
    assert "safety_flags.is_trade_plan must be false" in result.block_reasons
    assert "safety_flags.is_execution_permission must be false" in result.block_reasons
    assert "quote.last_tick_time must exist" in result.block_reasons
    assert "symbol_spec.digits must be a non-negative integer" in result.block_reasons
    assert "market_session.is_major_news_window must be boolean" in result.block_reasons
    assert "market_session.is_rollover_window must be boolean" in result.block_reasons
    assert "market_session.is_weekend must be boolean" in result.block_reasons


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
