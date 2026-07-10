from __future__ import annotations

import builtins
import copy
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pytest

from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID,
    CANONICAL_MT4_BUNDLE_V1_DATA_STALE,
    CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID,
    CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID,
    CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID,
    CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID,
    CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID,
    CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE,
    CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    validate_canonical_mt4_demo_readonly_bundle_v1_values,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "examples"
    / "canonical-mt4-demo-readonly-bundle-v1"
)
PAYLOAD_EXAMPLES = {
    "live_tick.json": "live_tick.example.json",
    "latest_bars.json": "latest_bars.example.json",
    "symbol_spec.json": "symbol_spec.example.json",
    "account_snapshot.json": "account_snapshot.example.json",
}
NOW_UTC = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)

OUTPUT_KEYS = {
    "passed",
    "status_code",
    "validation_stage",
    "contract_version",
    "upstream_structure_passed",
    "upstream_structure_status_code",
    "reason_codes",
    "warning_codes",
    "component_statuses",
    "reader_status",
    "freshness_checked",
    "freshness_passed",
    "ready_for_readonly_analysis",
    "next_allowed_stage",
    "next_blocked_stage",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
}
COMPONENT_KEYS = {
    "component_name",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
}


def test_valid_examples_pass_value_time_and_freshness_validation() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(manifest, payloads)

    assert result["passed"] is True
    assert result["status_code"] == CANONICAL_MT4_BUNDLE_V1_VALUE_VALID
    assert result["reason_codes"] == []
    assert result["warning_codes"] == []
    assert result["freshness_checked"] is True
    assert result["freshness_passed"] is True


def test_valid_result_is_still_not_ready_and_has_exact_safe_shape() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(manifest, payloads)

    assert set(result) == OUTPUT_KEYS
    assert result["validation_stage"] == "canonical_bundle_v1_payload_value_time_freshness"
    assert result["contract_version"] == "1.0"
    assert result["upstream_structure_passed"] is True
    assert result["reader_status"] == "not_called"
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == [
        "canonical_filesystem_bundle_reader_validation"
    ]
    assert result["next_blocked_stage"] == [
        "filesystem_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    _assert_safe_flags(result)
    components = result["component_statuses"]
    assert [item["component_name"] for item in components] == [
        "manifest_time",
        "live_tick",
        "latest_bars",
        "symbol_spec",
        "account_snapshot",
        "cross_payload",
    ]
    assert all(set(item) == COMPONENT_KEYS for item in components)
    assert all(item["passed"] is True for item in components)


def test_g146_upstream_blocked_stops_value_and_freshness_validation() -> None:
    manifest, payloads = _load_bundle()
    manifest["freshness_thresholds_seconds"] = {"live_tick": 999999}

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED)
    assert result["reason_codes"] == ["UPSTREAM_STRUCTURE_VALIDATION_BLOCKED"]
    assert result["upstream_structure_passed"] is False
    assert result["freshness_checked"] is False
    assert result["freshness_passed"] is False


def test_g146_sequence_warnings_are_preserved() -> None:
    manifest, payloads = _load_bundle()

    idempotent = _validate(
        manifest,
        payloads,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        },
    )

    gap_manifest, gap_payloads = _load_bundle()
    _set_sequence(gap_manifest, gap_payloads, 4)
    gap = _validate(
        gap_manifest,
        gap_payloads,
        previous_identity={"bundle_id": "demo-bundle-000000000000", "sequence": 1},
    )

    assert idempotent["passed"] is True
    assert idempotent["status_code"] == CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
    assert idempotent["warning_codes"] == ["IDEMPOTENT_REPEAT"]
    assert gap["passed"] is True
    assert gap["status_code"] == CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
    assert gap["warning_codes"] == ["SEQUENCE_GAP"]


def test_now_utc_must_be_datetime() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(manifest, payloads, now_utc="2026-07-10T02:30:05Z")

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID)
    assert result["reason_codes"] == ["NOW_UTC_INVALID"]
    assert result["freshness_checked"] is False


def test_now_utc_must_be_timezone_aware() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(manifest, payloads, now_utc=datetime(2026, 7, 10, 2, 30, 5))

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID)
    assert result["reason_codes"] == ["NOW_UTC_INVALID"]


def test_read_policy_must_be_typed_dataclass() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(
        manifest,
        payloads,
        read_policy={"live_tick_max_age_seconds": 999999},
    )

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID)
    assert result["reason_codes"] == ["READ_POLICY_INVALID"]
    assert result["freshness_checked"] is False


def test_read_policy_rejects_bool_zero_and_negative_thresholds() -> None:
    manifest, payloads = _load_bundle()
    policies = [
        CanonicalMt4DemoReadonlyBundleV1ReadPolicy(
            writer_heartbeat_max_age_seconds=True
        ),
        CanonicalMt4DemoReadonlyBundleV1ReadPolicy(live_tick_max_age_seconds=0),
        CanonicalMt4DemoReadonlyBundleV1ReadPolicy(latest_bars_max_age_seconds=-1),
        CanonicalMt4DemoReadonlyBundleV1ReadPolicy(max_future_skew_seconds=True),
        CanonicalMt4DemoReadonlyBundleV1ReadPolicy(max_future_skew_seconds=-1),
    ]

    for policy in policies:
        result = _validate(manifest, payloads, read_policy=policy)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID)
        assert result["reason_codes"] == ["READ_POLICY_INVALID"]


def test_typed_read_policy_controls_inclusive_age_boundary() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["tick_time_utc"] = "2026-07-10T02:29:54Z"
    policy = CanonicalMt4DemoReadonlyBundleV1ReadPolicy(
        live_tick_max_age_seconds=11
    )

    result = _validate(manifest, payloads, read_policy=policy)
    huge_policy_result = _validate(
        manifest,
        payloads,
        read_policy=CanonicalMt4DemoReadonlyBundleV1ReadPolicy(
            live_tick_max_age_seconds=10**100
        ),
    )

    assert result["passed"] is True
    assert result["freshness_passed"] is True
    assert "LIVE_TICK_STALE" not in result["reason_codes"]
    assert huge_policy_result["passed"] is True


def test_timestamp_must_be_actual_parseable_utc_z() -> None:
    manifest, payloads = _load_bundle()
    manifest["writer_heartbeat_at_utc"] = "not-a-real-timeZ"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID)
    assert "TIMESTAMP_INVALID" in result["reason_codes"]


def test_manifest_commit_cannot_precede_generated_time() -> None:
    manifest, payloads = _load_bundle()
    manifest["committed_at_utc"] = "2026-07-10T02:29:59Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID)
    assert "MANIFEST_TIME_ORDER_INVALID" in result["reason_codes"]


def test_manifest_timestamp_beyond_future_skew_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    manifest["writer_heartbeat_at_utc"] = "2026-07-10T02:30:11Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE)
    assert "TIMESTAMP_FROM_FUTURE" in result["reason_codes"]


def test_future_skew_boundary_is_inclusive() -> None:
    manifest, payloads = _load_bundle()
    manifest["writer_heartbeat_at_utc"] = "2026-07-10T02:30:10Z"
    payloads["live_tick.json"]["tick_time_utc"] = "2026-07-10T02:30:10Z"

    result = _validate(manifest, payloads)

    assert result["passed"] is True
    assert "TIMESTAMP_FROM_FUTURE" not in result["reason_codes"]


def test_writer_heartbeat_stale_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    manifest["writer_heartbeat_at_utc"] = "2026-07-10T02:29:49Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_DATA_STALE)
    assert "WRITER_HEARTBEAT_STALE" in result["reason_codes"]
    assert result["freshness_passed"] is False


def test_payload_generated_after_commit_plus_skew_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["generated_at_utc"] = "2026-07-10T02:30:07Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID)
    assert "PAYLOAD_GENERATED_AFTER_COMMIT" in result["reason_codes"]


def test_live_tick_stale_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["tick_time_utc"] = "2026-07-10T02:29:54Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_DATA_STALE)
    assert "LIVE_TICK_STALE" in result["reason_codes"]


def test_live_tick_future_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["tick_time_utc"] = "2026-07-10T02:30:11Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE)
    assert "TIMESTAMP_FROM_FUTURE" in result["reason_codes"]


def test_live_tick_rejects_nan_infinity_and_bool_numbers() -> None:
    manifest, payloads = _load_bundle()
    variants = [("bid", math.nan), ("ask", math.inf), ("point", True)]

    for field_name, value in variants:
        candidate = copy.deepcopy(payloads)
        candidate["live_tick.json"][field_name] = value
        result = _validate(manifest, candidate)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID)
        assert "LIVE_TICK_VALUE_INVALID" in result["reason_codes"]


def test_live_tick_rejects_ask_below_bid() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["ask"] = 2300.4

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID)
    assert "LIVE_TICK_VALUE_INVALID" in result["reason_codes"]


def test_live_tick_rejects_quote_spread_mismatch() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["spread"] = 0.1

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID)
    assert "LIVE_TICK_SPREAD_MISMATCH" in result["reason_codes"]


def test_live_tick_rejects_spread_points_mismatch() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["spread_points"] = 10

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID)
    assert "LIVE_TICK_SPREAD_MISMATCH" in result["reason_codes"]


def test_latest_bars_stale_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    payloads["latest_bars.json"]["generated_at_utc"] = "2026-07-10T02:29:04Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_DATA_STALE)
    assert "LATEST_BARS_STALE" in result["reason_codes"]


def test_latest_bars_rejects_missing_duplicate_and_wrong_order_timeframes() -> None:
    manifest, payloads = _load_bundle()
    variants = []

    missing = copy.deepcopy(payloads)
    missing["latest_bars.json"]["timeframes"].pop()
    variants.append(missing)

    duplicate = copy.deepcopy(payloads)
    duplicate["latest_bars.json"]["timeframes"][1]["timeframe"] = "M15"
    variants.append(duplicate)

    wrong_order = copy.deepcopy(payloads)
    wrong_order["latest_bars.json"]["timeframes"][0:2] = reversed(
        wrong_order["latest_bars.json"]["timeframes"][0:2]
    )
    variants.append(wrong_order)

    non_string_name = copy.deepcopy(payloads)
    non_string_name["latest_bars.json"]["timeframes"][0]["timeframe"] = []
    variants.append(non_string_name)

    for candidate in variants:
        result = _validate(manifest, candidate)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
        assert "TIMEFRAME_SET_INVALID" in result["reason_codes"]


def test_latest_bars_rejects_period_mismatch() -> None:
    manifest, payloads = _load_bundle()
    payloads["latest_bars.json"]["timeframes"][0]["period_seconds"] = 60

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
    assert "TIMEFRAME_PERIOD_INVALID" in result["reason_codes"]


def test_latest_bars_rejects_bar_count_mismatch() -> None:
    manifest, payloads = _load_bundle()
    payloads["latest_bars.json"]["timeframes"][0]["bar_count"] = 3

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
    assert "BAR_COUNT_INVALID" in result["reason_codes"]


def test_latest_bars_requires_strictly_increasing_open_times() -> None:
    manifest, payloads = _load_bundle()
    bars = payloads["latest_bars.json"]["timeframes"][0]["bars"]
    bars[1]["open_time_utc"] = bars[0]["open_time_utc"]

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
    assert "BAR_TIME_ORDER_INVALID" in result["reason_codes"]


def test_latest_bars_rejects_unfinished_bar() -> None:
    manifest, payloads = _load_bundle()
    bars = payloads["latest_bars.json"]["timeframes"][0]["bars"]
    bars[-1]["open_time_utc"] = payloads["latest_bars.json"]["generated_at_utc"]

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
    assert "BAR_NOT_COMPLETED" in result["reason_codes"]


def test_latest_bars_rejects_invalid_ohlc_relation() -> None:
    manifest, payloads = _load_bundle()
    bar = payloads["latest_bars.json"]["timeframes"][0]["bars"][0]
    bar["high"] = bar["low"]

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
    assert "OHLC_RELATION_INVALID" in result["reason_codes"]


def test_latest_bars_rejects_invalid_integer_fields() -> None:
    manifest, payloads = _load_bundle()
    variants = [("tick_volume", True), ("spread_points", -1)]

    for field_name, value in variants:
        candidate = copy.deepcopy(payloads)
        bar = candidate["latest_bars.json"]["timeframes"][0]["bars"][0]
        bar[field_name] = value
        result = _validate(manifest, candidate)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID)
        assert "BAR_VALUE_INVALID" in result["reason_codes"]


def test_symbol_spec_stale_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    payloads["symbol_spec.json"]["spec_time_utc"] = "2026-07-09T02:30:04Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_DATA_STALE)
    assert "SYMBOL_SPEC_STALE" in result["reason_codes"]


def test_symbol_spec_rejects_invalid_numeric_and_lot_relations() -> None:
    manifest, payloads = _load_bundle()

    invalid_numeric = copy.deepcopy(payloads)
    invalid_numeric["symbol_spec.json"]["tick_value"] = False
    numeric_result = _validate(manifest, invalid_numeric)

    invalid_lots = copy.deepcopy(payloads)
    invalid_lots["symbol_spec.json"]["min_lot"] = 100.0
    lot_result = _validate(manifest, invalid_lots)

    _assert_blocked(numeric_result, CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID)
    assert "SYMBOL_SPEC_VALUE_INVALID" in numeric_result["reason_codes"]
    _assert_blocked(lot_result, CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID)
    assert "SYMBOL_SPEC_LOT_RELATION_INVALID" in lot_result["reason_codes"]


def test_symbol_spec_rejects_currency_and_unsafe_labels() -> None:
    manifest, payloads = _load_bundle()
    payloads["symbol_spec.json"]["base_currency"] = "EUR"
    payloads["symbol_spec.json"]["trade_mode_readonly_label"] = "unsafe label"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID)
    assert "SYMBOL_SPEC_CURRENCY_INVALID" in result["reason_codes"]
    assert "SYMBOL_SPEC_VALUE_INVALID" in result["reason_codes"]


def test_account_snapshot_stale_is_blocked() -> None:
    manifest, payloads = _load_bundle()
    payloads["account_snapshot.json"]["snapshot_time_utc"] = "2026-07-10T02:29:34Z"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_DATA_STALE)
    assert "ACCOUNT_SNAPSHOT_STALE" in result["reason_codes"]


def test_account_snapshot_rejects_invalid_numeric_and_count_values() -> None:
    manifest, payloads = _load_bundle()
    variants = [
        ("balance", True),
        ("free_margin", math.inf),
        ("positions_count", True),
        ("pending_orders_count", -1),
    ]

    for field_name, value in variants:
        candidate = copy.deepcopy(payloads)
        candidate["account_snapshot.json"][field_name] = value
        result = _validate(manifest, candidate)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID)
        assert "ACCOUNT_SNAPSHOT_VALUE_INVALID" in result["reason_codes"]


def test_cross_payload_digits_point_and_currency_mismatches_are_detected() -> None:
    manifest, payloads = _load_bundle()

    digits = copy.deepcopy(payloads)
    digits["live_tick.json"]["digits"] = 3
    digits_result = _validate(manifest, digits)

    point = copy.deepcopy(payloads)
    point["live_tick.json"]["point"] = 0.02
    point["live_tick.json"]["spread_points"] = 15
    point_result = _validate(manifest, point)

    currency = copy.deepcopy(payloads)
    currency["account_snapshot.json"]["account_currency"] = "EUR"
    currency_result = _validate(manifest, currency)

    _assert_blocked(digits_result, CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID)
    assert "CROSS_PAYLOAD_DIGITS_MISMATCH" in digits_result["reason_codes"]
    _assert_blocked(point_result, CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID)
    assert "CROSS_PAYLOAD_POINT_MISMATCH" in point_result["reason_codes"]
    assert "CROSS_PAYLOAD_CURRENCY_MISMATCH" in currency_result["reason_codes"]


def test_validator_is_pure_memory_preserves_inputs_and_does_not_leak_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["bid"] = "SUPER_SECRET_PRICE"
    payloads["account_snapshot.json"]["account_alias_masked"] = (
        "C:/private/bridge/account.json"
    )
    original_manifest = copy.deepcopy(manifest)
    original_payloads = copy.deepcopy(payloads)

    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("production validator must not access filesystem")

    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "read_text", fail_if_called)
    monkeypatch.setattr(Path, "read_bytes", fail_if_called)
    monkeypatch.setattr(Path, "exists", fail_if_called)
    monkeypatch.setattr(Path, "is_file", fail_if_called)

    result = _validate(manifest, payloads)

    assert result["passed"] is False
    assert set(result) == OUTPUT_KEYS
    assert "SUPER_SECRET_PRICE" not in str(result)
    assert "C:/private/bridge/account.json" not in str(result)
    assert "2300.5" not in str(result)
    assert "10000.0" not in str(result)
    assert "2026-07-10" not in str(result)
    assert manifest == original_manifest
    assert payloads == original_payloads
    _assert_safe_flags(result)


def _load_bundle() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    with (EXAMPLE_DIR / "snapshot_manifest.example.json").open(encoding="utf-8") as file:
        manifest = json.load(file)

    payloads = {}
    for canonical_filename, example_filename in PAYLOAD_EXAMPLES.items():
        with (EXAMPLE_DIR / example_filename).open(encoding="utf-8") as file:
            payloads[canonical_filename] = json.load(file)
    return manifest, payloads


def _validate(
    manifest: object,
    payloads: object,
    *,
    now_utc: object = NOW_UTC,
    previous_identity: object | None = None,
    read_policy: object | None = None,
) -> dict[str, Any]:
    return validate_canonical_mt4_demo_readonly_bundle_v1_values(
        manifest=manifest,
        payloads_by_filename=payloads,
        now_utc=now_utc,
        previous_identity=previous_identity,
        read_policy=read_policy,
    )


def _set_sequence(
    manifest: dict[str, Any],
    payloads: dict[str, dict[str, Any]],
    sequence: int,
) -> None:
    manifest["sequence"] = sequence
    for payload in payloads.values():
        payload["sequence"] = sequence


def _assert_blocked(result: dict[str, Any], expected_status: str) -> None:
    assert result["passed"] is False
    assert result["status_code"] == expected_status
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == []
    _assert_safe_flags(result)


def _assert_safe_flags(result: dict[str, Any]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False
