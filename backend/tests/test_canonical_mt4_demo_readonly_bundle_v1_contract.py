from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "examples"
    / "canonical-mt4-demo-readonly-bundle-v1"
)

SCHEMA_VERSION = "1.0"
SOURCE_ID = "trademax_mt4_demo_readonly_bridge"
CANONICAL_SYMBOL = "XAUUSD"
BROKER_SYMBOL = "GOLD"

MANIFEST_FILE = "snapshot_manifest.example.json"
PAYLOAD_EXAMPLE_FILES = {
    "live_tick": "live_tick.example.json",
    "latest_bars": "latest_bars.example.json",
    "symbol_spec": "symbol_spec.example.json",
    "account_snapshot": "account_snapshot.example.json",
}
EXAMPLE_FILES = (MANIFEST_FILE, *PAYLOAD_EXAMPLE_FILES.values())

REQUIRED_PAYLOADS = {
    "live_tick.json": "live_tick",
    "latest_bars.json": "latest_bars",
    "symbol_spec.json": "symbol_spec",
    "account_snapshot.json": "account_snapshot",
}

PAYLOAD_SAFETY_VALUES = {
    "account_mode": "demo_only",
    "is_demo_account": True,
    "is_live_account": False,
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}

FILE_SIZE_LIMITS = {
    "snapshot_manifest.example.json": 65536,
    "live_tick.example.json": 32768,
    "latest_bars.example.json": 2097152,
    "symbol_spec.example.json": 65536,
    "account_snapshot.example.json": 131072,
}

MANIFEST_KEYS = {
    "schema_version",
    "manifest_type",
    "bundle_id",
    "sequence",
    "generated_at_utc",
    "committed_at_utc",
    "writer_heartbeat_at_utc",
    "source_id",
    "writer_version",
    "terminal_id_masked",
    "account_mode",
    "is_demo_account",
    "is_live_account",
    "canonical_symbol",
    "broker_symbol",
    "commit_state",
    "required_files",
    "optional_files",
    "compatible_reader_schema_versions",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
}

COMMON_PAYLOAD_ENVELOPE_KEYS = {
    "schema_version",
    "file_type",
    "bundle_id",
    "sequence",
    "generated_at_utc",
    "source_id",
    "writer_version",
    "terminal_id_masked",
    "account_mode",
    "is_demo_account",
    "is_live_account",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
}

LIVE_TICK_KEYS = COMMON_PAYLOAD_ENVELOPE_KEYS | {
    "canonical_symbol",
    "broker_symbol",
    "bid",
    "ask",
    "spread",
    "spread_points",
    "digits",
    "point",
    "tick_time_utc",
}

LATEST_BARS_KEYS = COMMON_PAYLOAD_ENVELOPE_KEYS | {
    "canonical_symbol",
    "broker_symbol",
    "timeframes",
}

SYMBOL_SPEC_KEYS = COMMON_PAYLOAD_ENVELOPE_KEYS | {
    "canonical_symbol",
    "broker_symbol",
    "spec_time_utc",
    "digits",
    "point",
    "tick_size",
    "tick_value",
    "contract_size",
    "min_lot",
    "lot_step",
    "max_lot",
    "base_currency",
    "profit_currency",
    "margin_currency",
    "trade_mode_readonly_label",
    "session_status_readonly_label",
}

ACCOUNT_SNAPSHOT_KEYS = COMMON_PAYLOAD_ENVELOPE_KEYS | {
    "snapshot_time_utc",
    "account_alias_masked",
    "server_name_masked",
    "account_currency",
    "balance",
    "equity",
    "margin",
    "free_margin",
    "margin_level",
    "leverage",
    "positions_count",
    "pending_orders_count",
    "daily_realized_pnl",
    "daily_floating_pnl",
}

FORBIDDEN_KEYS = {
    "password",
    "credential",
    "credentials",
    "token",
    "secret",
    "api_key",
    "login",
    "account_number",
    "path",
    "absolute_path",
    "terminal_path",
    "system_path",
    "base_dir",
    "bridge_dir",
    "candidate_path",
    "raw_payload",
    "traceback",
    "stack_trace",
    "ticket",
    "order_id",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "OrderSend",
    "OrderClose",
    "OrderModify",
    "OrderDelete",
    "ea_command",
    "execute_trade",
    "can_trade",
    "allow_trade",
    "trade_allowed",
    "order_allowed",
    "execution_allowed",
    "buy_signal",
    "sell_signal",
    "should_buy",
    "should_sell",
    "entry_price",
    "stop_loss",
    "take_profit",
    "suggested_lot",
    "position_size",
    "trade_plan",
    "execution_plan",
    "override_risk",
    "bypass_gate",
}

SERVER_POLICY_KEYS = {
    "risk_limits",
    "daily_loss_pct",
    "max_single_trade_loss_pct",
    "max_daily_loss_pct",
    "no_overnight",
    "primary_session",
    "leverage_cap",
}

MANIFEST_POLICY_KEYS = {
    "freshness_thresholds_seconds",
    "file_size_limits_bytes",
    "max_total_bundle_bytes",
    "checksum_policy",
}

SAFE_STRING_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
BUNDLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
TIMEFRAME_PERIODS = {
    "M15": 900,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}


def test_canonical_bundle_example_files_exist_and_parse_as_objects() -> None:
    examples = _load_examples()

    assert set(examples) == set(EXAMPLE_FILES)
    for filename, payload in examples.items():
        assert isinstance(payload, dict), f"{filename} must parse as a JSON object"


def test_manifest_matches_canonical_v1_contract() -> None:
    manifest = _load_examples()[MANIFEST_FILE]

    _assert_exact_keys(manifest, MANIFEST_KEYS, MANIFEST_FILE)
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["manifest_type"] == "mt4_demo_readonly_snapshot_manifest"
    assert manifest["source_id"] == SOURCE_ID
    assert manifest["canonical_symbol"] == CANONICAL_SYMBOL
    assert manifest["broker_symbol"] == BROKER_SYMBOL
    assert manifest["commit_state"] == "complete"
    assert manifest["optional_files"] == []
    assert manifest["compatible_reader_schema_versions"] == [SCHEMA_VERSION]
    _assert_positive_int(manifest["sequence"], f"{MANIFEST_FILE}.sequence")
    _assert_demo_readonly_safety_values(manifest, MANIFEST_FILE)


def test_manifest_required_file_descriptors_are_exact() -> None:
    manifest = _load_examples()[MANIFEST_FILE]
    descriptors = manifest["required_files"]

    assert isinstance(descriptors, list)
    assert len(descriptors) == len(REQUIRED_PAYLOADS)
    filenames = [descriptor["filename"] for descriptor in descriptors]
    assert filenames == list(REQUIRED_PAYLOADS)
    assert len(set(filenames)) == len(filenames)

    for descriptor in descriptors:
        _assert_exact_keys(
            descriptor,
            {"filename", "file_type", "schema_version", "content_sha256"},
            f"{MANIFEST_FILE}.required_files[]",
        )
        filename = descriptor["filename"]
        assert "/" not in filename
        assert "\\" not in filename
        assert ".." not in filename
        assert descriptor["file_type"] == REQUIRED_PAYLOADS[filename]
        assert descriptor["schema_version"] == SCHEMA_VERSION
        assert descriptor["content_sha256"] is None


def test_bundle_identity_is_consistent_across_manifest_and_payloads() -> None:
    examples = _load_examples()
    manifest = examples[MANIFEST_FILE]
    identity_fields = {
        "bundle_id",
        "sequence",
        "source_id",
        "writer_version",
        "terminal_id_masked",
        "account_mode",
        "is_demo_account",
        "is_live_account",
    }
    expected_identity = {field: manifest[field] for field in identity_fields}

    assert isinstance(manifest["bundle_id"], str)
    assert 16 <= len(manifest["bundle_id"]) <= 64
    assert BUNDLE_ID_PATTERN.fullmatch(manifest["bundle_id"])
    _assert_positive_int(manifest["sequence"], f"{MANIFEST_FILE}.sequence")

    for file_type, filename in PAYLOAD_EXAMPLE_FILES.items():
        payload = examples[filename]
        assert payload["file_type"] == file_type
        observed_identity = {field: payload[field] for field in identity_fields}
        assert observed_identity == expected_identity, filename


def test_payload_common_envelope_is_exact_and_safe() -> None:
    examples = _load_examples()

    for file_type, filename in PAYLOAD_EXAMPLE_FILES.items():
        payload = examples[filename]
        assert COMMON_PAYLOAD_ENVELOPE_KEYS.issubset(payload), filename
        assert payload["file_type"] == file_type
        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["source_id"] == SOURCE_ID
        _assert_positive_int(payload["sequence"], f"{filename}.sequence")
        _parse_utc_z(payload["generated_at_utc"], f"{filename}.generated_at_utc")
        _assert_demo_readonly_safety_values(payload, filename)


def test_manifest_is_demo_only_readonly_and_non_executable() -> None:
    manifest = _load_examples()[MANIFEST_FILE]

    _assert_demo_readonly_safety_values(manifest, MANIFEST_FILE)
    assert manifest["is_tradable"] is False
    assert manifest["can_execute"] is False
    assert manifest["is_trading_permission"] is False
    assert manifest["is_execution_instruction"] is False


def test_live_tick_example_obeys_quote_contract() -> None:
    live_tick = _load_examples()[PAYLOAD_EXAMPLE_FILES["live_tick"]]

    _assert_exact_keys(live_tick, LIVE_TICK_KEYS, "live_tick")
    assert live_tick["canonical_symbol"] == CANONICAL_SYMBOL
    assert live_tick["broker_symbol"] == BROKER_SYMBOL
    _assert_finite_number(live_tick["bid"], "live_tick.bid")
    _assert_finite_number(live_tick["ask"], "live_tick.ask")
    _assert_finite_number(live_tick["spread"], "live_tick.spread")
    _assert_finite_number(live_tick["point"], "live_tick.point")
    assert live_tick["bid"] > 0
    assert live_tick["ask"] >= live_tick["bid"]
    assert live_tick["spread"] >= 0
    assert math.isclose(
        live_tick["spread"],
        live_tick["ask"] - live_tick["bid"],
        rel_tol=0,
        abs_tol=1e-9,
    )
    _assert_non_negative_int(live_tick["spread_points"], "live_tick.spread_points")
    _assert_digits(live_tick["digits"], "live_tick.digits")
    assert live_tick["point"] > 0
    _parse_utc_z(live_tick["tick_time_utc"], "live_tick.tick_time_utc")


def test_latest_bars_example_contains_completed_ordered_bars() -> None:
    latest_bars = _load_examples()[PAYLOAD_EXAMPLE_FILES["latest_bars"]]

    _assert_exact_keys(latest_bars, LATEST_BARS_KEYS, "latest_bars")
    assert latest_bars["canonical_symbol"] == CANONICAL_SYMBOL
    assert latest_bars["broker_symbol"] == BROKER_SYMBOL
    timeframes = latest_bars["timeframes"]
    assert isinstance(timeframes, list)
    assert [item["timeframe"] for item in timeframes] == list(TIMEFRAME_PERIODS)

    for timeframe in timeframes:
        _assert_exact_keys(
            timeframe,
            {"timeframe", "period_seconds", "bar_count", "bars"},
            "latest_bars.timeframes[]",
        )
        timeframe_name = timeframe["timeframe"]
        assert timeframe["period_seconds"] == TIMEFRAME_PERIODS[timeframe_name]
        _assert_positive_int(
            timeframe["bar_count"],
            f"latest_bars.{timeframe_name}.bar_count",
        )
        assert timeframe["bar_count"] <= 500
        bars = timeframe["bars"]
        assert isinstance(bars, list)
        assert len(bars) == timeframe["bar_count"]
        assert bars
        open_times: list[datetime] = []
        for bar in bars:
            _assert_completed_bar(bar, timeframe_name)
            open_times.append(
                _parse_utc_z(
                    bar["open_time_utc"],
                    f"latest_bars.{timeframe_name}.open_time_utc",
                )
            )
        assert open_times == sorted(open_times)
        assert len(set(open_times)) == len(open_times)


def test_symbol_spec_example_contains_only_readonly_broker_facts() -> None:
    symbol_spec = _load_examples()[PAYLOAD_EXAMPLE_FILES["symbol_spec"]]

    _assert_exact_keys(symbol_spec, SYMBOL_SPEC_KEYS, "symbol_spec")
    assert symbol_spec["canonical_symbol"] == CANONICAL_SYMBOL
    assert symbol_spec["broker_symbol"] == BROKER_SYMBOL
    _parse_utc_z(symbol_spec["spec_time_utc"], "symbol_spec.spec_time_utc")
    _assert_digits(symbol_spec["digits"], "symbol_spec.digits")
    for field in (
        "point",
        "tick_size",
        "tick_value",
        "contract_size",
        "min_lot",
        "lot_step",
        "max_lot",
    ):
        _assert_finite_number(symbol_spec[field], f"symbol_spec.{field}")
        assert symbol_spec[field] > 0
    assert symbol_spec["min_lot"] <= symbol_spec["max_lot"]
    assert symbol_spec["lot_step"] <= symbol_spec["max_lot"]
    assert symbol_spec["base_currency"] == "XAU"
    assert symbol_spec["profit_currency"] == "USD"
    _assert_safe_non_empty_string(symbol_spec["margin_currency"], "margin_currency")
    _assert_safe_non_empty_string(
        symbol_spec["trade_mode_readonly_label"],
        "trade_mode_readonly_label",
    )
    _assert_safe_non_empty_string(
        symbol_spec["session_status_readonly_label"],
        "session_status_readonly_label",
    )
    assert symbol_spec["is_tradable"] is False
    assert symbol_spec["can_execute"] is False


def test_account_snapshot_contains_facts_not_server_risk_policy() -> None:
    account_snapshot = _load_examples()[PAYLOAD_EXAMPLE_FILES["account_snapshot"]]

    _assert_exact_keys(account_snapshot, ACCOUNT_SNAPSHOT_KEYS, "account_snapshot")
    _parse_utc_z(
        account_snapshot["snapshot_time_utc"],
        "account_snapshot.snapshot_time_utc",
    )
    _assert_safe_non_empty_string(
        account_snapshot["account_alias_masked"],
        "account_alias_masked",
    )
    _assert_safe_non_empty_string(
        account_snapshot["server_name_masked"],
        "server_name_masked",
    )
    assert account_snapshot["account_currency"] == "USD"
    for field in ("balance", "equity", "margin"):
        _assert_finite_number(account_snapshot[field], f"account_snapshot.{field}")
        assert account_snapshot[field] >= 0
    _assert_finite_number(account_snapshot["free_margin"], "account_snapshot.free_margin")
    margin_level = account_snapshot["margin_level"]
    if margin_level is not None:
        _assert_finite_number(margin_level, "account_snapshot.margin_level")
        assert margin_level >= 0
    _assert_finite_number(account_snapshot["leverage"], "account_snapshot.leverage")
    assert account_snapshot["leverage"] > 0
    _assert_non_negative_int(
        account_snapshot["positions_count"],
        "account_snapshot.positions_count",
    )
    _assert_non_negative_int(
        account_snapshot["pending_orders_count"],
        "account_snapshot.pending_orders_count",
    )
    _assert_finite_number(
        account_snapshot["daily_realized_pnl"],
        "account_snapshot.daily_realized_pnl",
    )
    _assert_finite_number(
        account_snapshot["daily_floating_pnl"],
        "account_snapshot.daily_floating_pnl",
    )
    assert _collect_keys(account_snapshot).isdisjoint(SERVER_POLICY_KEYS)


def test_examples_contain_no_forbidden_fields_at_any_depth() -> None:
    examples = _load_examples()

    forbidden = {key.casefold() for key in FORBIDDEN_KEYS}
    for filename, payload in examples.items():
        observed_keys = _collect_keys(payload)
        assert observed_keys.isdisjoint(forbidden), filename


def test_symbols_are_consistent_across_manifest_and_market_payloads() -> None:
    examples = _load_examples()
    symbol_files = (
        MANIFEST_FILE,
        PAYLOAD_EXAMPLE_FILES["live_tick"],
        PAYLOAD_EXAMPLE_FILES["latest_bars"],
        PAYLOAD_EXAMPLE_FILES["symbol_spec"],
    )

    for filename in symbol_files:
        assert examples[filename]["canonical_symbol"] == CANONICAL_SYMBOL
        assert examples[filename]["broker_symbol"] == BROKER_SYMBOL

    account_snapshot = examples[PAYLOAD_EXAMPLE_FILES["account_snapshot"]]
    assert "canonical_symbol" not in account_snapshot
    assert "broker_symbol" not in account_snapshot


def test_all_canonical_timestamps_are_parseable_utc_z() -> None:
    examples = _load_examples()
    manifest = examples[MANIFEST_FILE]

    manifest_generated_at = _parse_utc_z(
        manifest["generated_at_utc"],
        "manifest.generated_at_utc",
    )
    committed_at = _parse_utc_z(
        manifest["committed_at_utc"],
        "manifest.committed_at_utc",
    )
    _parse_utc_z(
        manifest["writer_heartbeat_at_utc"],
        "manifest.writer_heartbeat_at_utc",
    )
    assert committed_at >= manifest_generated_at

    for file_type, filename in PAYLOAD_EXAMPLE_FILES.items():
        payload = examples[filename]
        _parse_utc_z(payload["generated_at_utc"], f"{file_type}.generated_at_utc")

    _parse_utc_z(
        examples[PAYLOAD_EXAMPLE_FILES["live_tick"]]["tick_time_utc"],
        "live_tick.tick_time_utc",
    )
    _parse_utc_z(
        examples[PAYLOAD_EXAMPLE_FILES["symbol_spec"]]["spec_time_utc"],
        "symbol_spec.spec_time_utc",
    )
    _parse_utc_z(
        examples[PAYLOAD_EXAMPLE_FILES["account_snapshot"]]["snapshot_time_utc"],
        "account_snapshot.snapshot_time_utc",
    )

    for timeframe in examples[PAYLOAD_EXAMPLE_FILES["latest_bars"]]["timeframes"]:
        for bar in timeframe["bars"]:
            _parse_utc_z(
                bar["open_time_utc"],
                f"latest_bars.{timeframe['timeframe']}.open_time_utc",
            )


def test_example_files_are_within_server_side_size_defaults() -> None:
    manifest = _load_examples()[MANIFEST_FILE]

    for filename, limit in FILE_SIZE_LIMITS.items():
        path = EXAMPLE_DIR / filename
        assert path.stat().st_size <= limit, filename

    observed_manifest_keys = _collect_keys(manifest)
    assert observed_manifest_keys.isdisjoint(MANIFEST_POLICY_KEYS)


def _load_examples() -> dict[str, dict[str, Any]]:
    examples: dict[str, dict[str, Any]] = {}
    for filename in EXAMPLE_FILES:
        path = EXAMPLE_DIR / filename
        assert path.is_file(), f"{filename} must exist in canonical example dir"
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
        assert isinstance(payload, dict), f"{filename} must parse as a JSON object"
        examples[filename] = payload
    return examples


def _parse_utc_z(value: object, field_name: str) -> datetime:
    assert isinstance(value, str), f"{field_name} must be a UTC Z string"
    assert value.endswith("Z"), f"{field_name} must end with Z"
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, f"{field_name} must be timezone-aware"
    return parsed.astimezone(UTC)


def _is_finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _assert_finite_number(value: object, field_name: str) -> None:
    assert _is_finite_number(value), f"{field_name} must be a finite number"


def _assert_positive_int(value: object, field_name: str) -> None:
    assert not isinstance(value, bool), f"{field_name} must not be bool"
    assert isinstance(value, int), f"{field_name} must be an integer"
    assert value > 0, f"{field_name} must be positive"


def _assert_non_negative_int(value: object, field_name: str) -> None:
    assert not isinstance(value, bool), f"{field_name} must not be bool"
    assert isinstance(value, int), f"{field_name} must be an integer"
    assert value >= 0, f"{field_name} must be non-negative"


def _assert_digits(value: object, field_name: str) -> None:
    assert not isinstance(value, bool), f"{field_name} must not be bool"
    assert isinstance(value, int), f"{field_name} must be an integer"
    assert 0 <= value <= 8, f"{field_name} must be between 0 and 8"


def _assert_safe_non_empty_string(value: object, field_name: str) -> None:
    assert isinstance(value, str), f"{field_name} must be a string"
    assert value, f"{field_name} must not be empty"
    assert SAFE_STRING_PATTERN.fullmatch(value), f"{field_name} must be a safe label"


def _assert_exact_keys(
    payload: dict[str, Any],
    expected: set[str],
    payload_name: str,
) -> None:
    observed = set(payload)
    assert observed == expected, (
        f"{payload_name} keys mismatch; "
        f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
    )


def _assert_demo_readonly_safety_values(
    payload: dict[str, Any],
    payload_name: str,
) -> None:
    for field_name, expected_value in PAYLOAD_SAFETY_VALUES.items():
        assert payload[field_name] == expected_value, f"{payload_name}.{field_name}"


def _assert_completed_bar(bar: dict[str, Any], timeframe_name: str) -> None:
    _assert_exact_keys(
        bar,
        {
            "open_time_utc",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread_points",
        },
        f"latest_bars.{timeframe_name}.bar",
    )
    for field in ("open", "high", "low", "close"):
        _assert_finite_number(bar[field], f"latest_bars.{timeframe_name}.{field}")
        assert bar[field] > 0, f"latest_bars.{timeframe_name}.{field} must be positive"
    assert bar["high"] >= max(bar["open"], bar["close"], bar["low"])
    assert bar["low"] <= min(bar["open"], bar["close"], bar["high"])
    _assert_non_negative_int(
        bar["tick_volume"],
        f"latest_bars.{timeframe_name}.tick_volume",
    )
    _assert_non_negative_int(
        bar["spread_points"],
        f"latest_bars.{timeframe_name}.spread_points",
    )


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = {key.casefold() for key in value}
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()
