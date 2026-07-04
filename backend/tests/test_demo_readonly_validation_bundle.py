from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.services.demo_readonly_validation_bundle import (
    ACCOUNT_SNAPSHOT,
    DEMO_READONLY_BUNDLE_INVALID,
    DEMO_READONLY_BUNDLE_VALID,
    MARKET_SYMBOL,
    POSITIONS_ORDER_HISTORY,
    DemoReadOnlyValidationBundleResult,
    validate_demo_readonly_bundle,
)


DOCS_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "implementation_plans"
)

ACCOUNT_EXAMPLE_PATH = DOCS_DIR / "demo_account_readonly_snapshot.example.json"
POSITIONS_EXAMPLE_PATH = DOCS_DIR / "demo_positions_order_history.example.json"
MARKET_EXAMPLE_PATH = DOCS_DIR / "demo_market_symbol_readonly.example.json"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _example_bundle() -> dict[str, dict[str, Any]]:
    return {
        ACCOUNT_SNAPSHOT: _read_json(ACCOUNT_EXAMPLE_PATH),
        POSITIONS_ORDER_HISTORY: _read_json(POSITIONS_EXAMPLE_PATH),
        MARKET_SYMBOL: _read_json(MARKET_EXAMPLE_PATH),
    }


def _validate(bundle: dict[str, Any]) -> DemoReadOnlyValidationBundleResult:
    return validate_demo_readonly_bundle(bundle)


def test_docs_examples_pass_bundle_validation() -> None:
    result = _validate(_example_bundle())

    assert isinstance(result, DemoReadOnlyValidationBundleResult)
    assert result.passed is True
    assert result.status_code == DEMO_READONLY_BUNDLE_VALID
    assert result.block_reasons == []
    assert result.warning_reasons == []
    assert result.is_tradable is False
    assert result.can_execute is False
    assert result.cross_checks["demo_only_consistent"] is True
    assert result.cross_checks["live_account_absent"] is True
    assert result.cross_checks["symbol_consistent"] is True
    assert result.cross_checks["account_alias_consistent"] is True
    assert result.component_results[ACCOUNT_SNAPSHOT]["passed"] is True
    assert result.component_results[POSITIONS_ORDER_HISTORY]["passed"] is True
    assert result.component_results[MARKET_SYMBOL]["passed"] is True


def test_bundle_fails_when_account_snapshot_missing() -> None:
    bundle = _example_bundle()
    bundle.pop(ACCOUNT_SNAPSHOT)

    result = _validate(bundle)

    assert result.passed is False
    assert result.status_code == DEMO_READONLY_BUNDLE_INVALID
    assert "account_snapshot must exist" in result.block_reasons
    assert result.is_tradable is False
    assert result.can_execute is False


def test_bundle_fails_when_positions_order_history_missing() -> None:
    bundle = _example_bundle()
    bundle.pop(POSITIONS_ORDER_HISTORY)

    result = _validate(bundle)

    assert result.passed is False
    assert "positions_order_history must exist" in result.block_reasons


def test_bundle_fails_when_market_symbol_missing() -> None:
    bundle = _example_bundle()
    bundle.pop(MARKET_SYMBOL)

    result = _validate(bundle)

    assert result.passed is False
    assert "market_symbol must exist" in result.block_reasons


def test_bundle_fails_when_account_snapshot_validator_fails() -> None:
    bundle = _example_bundle()
    bundle[ACCOUNT_SNAPSHOT]["symbol_snapshot"]["ask"] = 2299.0

    result = _validate(bundle)

    assert result.passed is False
    assert any(
        reason.startswith("account_snapshot validator failed:")
        for reason in result.block_reasons
    )


def test_bundle_fails_when_positions_order_history_validator_fails() -> None:
    bundle = _example_bundle()
    bundle[POSITIONS_ORDER_HISTORY]["open_positions"][0].pop("stop_loss")

    result = _validate(bundle)

    assert result.passed is False
    assert any(
        reason.startswith("positions_order_history validator failed:")
        for reason in result.block_reasons
    )


def test_bundle_fails_when_market_symbol_validator_fails() -> None:
    bundle = _example_bundle()
    bundle[MARKET_SYMBOL]["quote"]["spread"] = -0.1

    result = _validate(bundle)

    assert result.passed is False
    assert any(
        reason.startswith("market_symbol validator failed:")
        for reason in result.block_reasons
    )


def test_bundle_fails_when_any_account_mode_is_not_demo_only() -> None:
    bundle = _example_bundle()
    bundle[POSITIONS_ORDER_HISTORY]["account_mode"] = "live"

    result = _validate(bundle)

    assert result.passed is False
    assert "all components account_mode must be demo_only" in result.block_reasons


def test_bundle_fails_when_any_component_is_live_account() -> None:
    bundle = _example_bundle()
    bundle[MARKET_SYMBOL]["demo_account"]["is_live_account"] = True

    result = _validate(bundle)

    assert result.passed is False
    assert (
        "all components demo_account.is_live_account must be false"
        in result.block_reasons
    )


def test_bundle_fails_when_any_component_contains_password() -> None:
    bundle = _example_bundle()
    bundle[ACCOUNT_SNAPSHOT]["safety_flags"]["contains_password"] = True

    result = _validate(bundle)

    assert result.passed is False
    assert "all components must not contain passwords" in result.block_reasons


def test_bundle_fails_when_any_component_contains_credentials() -> None:
    bundle = _example_bundle()
    bundle[MARKET_SYMBOL]["safety_flags"]["contains_credentials"] = True

    result = _validate(bundle)

    assert result.passed is False
    assert "all components must not contain credentials" in result.block_reasons


def test_bundle_fails_when_any_component_can_execute() -> None:
    bundle = _example_bundle()
    bundle[POSITIONS_ORDER_HISTORY]["safety_flags"]["can_execute"] = True

    result = _validate(bundle)

    assert result.passed is False
    assert (
        "all components safety_flags.can_execute must be false"
        in result.block_reasons
    )
    assert result.cross_checks["can_execute"] is False
    assert result.can_execute is False


def test_bundle_fails_when_any_component_is_tradable() -> None:
    bundle = _example_bundle()
    bundle[ACCOUNT_SNAPSHOT]["safety_flags"]["is_tradable"] = True

    result = _validate(bundle)

    assert result.passed is False
    assert (
        "all components safety_flags.is_tradable must be false"
        in result.block_reasons
    )
    assert result.cross_checks["is_tradable"] is False
    assert result.is_tradable is False


def test_bundle_fails_when_symbol_is_inconsistent() -> None:
    bundle = _example_bundle()
    bundle[POSITIONS_ORDER_HISTORY]["closed_orders"][0]["symbol"] = "EURUSD"

    result = _validate(bundle)

    assert result.passed is False
    assert "symbols must be consistent and XAUUSD" in result.block_reasons


def test_bundle_fails_when_account_alias_is_inconsistent() -> None:
    bundle = _example_bundle()
    bundle[MARKET_SYMBOL]["demo_account"]["account_alias"] = "other-demo-account"

    result = _validate(bundle)

    assert result.passed is False
    assert "account_alias must be consistent across components" in result.block_reasons


def test_bundle_output_is_never_tradable_or_executable_for_invalid_input() -> None:
    bundle = deepcopy(_example_bundle())
    bundle[ACCOUNT_SNAPSHOT]["safety_flags"]["is_tradable"] = True
    bundle[MARKET_SYMBOL]["safety_flags"]["can_execute"] = True

    result = _validate(bundle)

    assert result.passed is False
    assert result.is_tradable is False
    assert result.can_execute is False
    assert result.cross_checks["is_tradable"] is False
    assert result.cross_checks["can_execute"] is False


def test_bundle_reads_docs_examples_not_data_runtime_files() -> None:
    result = _validate(_example_bundle())

    assert result.passed is True
    for path in (ACCOUNT_EXAMPLE_PATH, POSITIONS_EXAMPLE_PATH, MARKET_EXAMPLE_PATH):
        normalized_path = str(path).replace("\\", "/")
        assert "docs/implementation_plans" in normalized_path
        assert "data/" not in normalized_path
