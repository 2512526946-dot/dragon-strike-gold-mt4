from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import math
import re
from typing import Any

from app.services.canonical_mt4_demo_readonly_bundle_v1_validator import (
    validate_canonical_mt4_demo_readonly_bundle_v1,
)


@dataclass(frozen=True)
class CanonicalMt4DemoReadonlyBundleV1ReadPolicy:
    writer_heartbeat_max_age_seconds: int = 15
    live_tick_max_age_seconds: int = 10
    latest_bars_max_age_seconds: int = 60
    symbol_spec_max_age_seconds: int = 86400
    account_snapshot_max_age_seconds: int = 30
    max_future_skew_seconds: int = 5


CANONICAL_MT4_BUNDLE_V1_VALUE_VALID = "CANONICAL_MT4_BUNDLE_V1_VALUE_VALID"
CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS = (
    "CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS"
)
CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE = (
    "CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE"
)
CANONICAL_MT4_BUNDLE_V1_DATA_STALE = "CANONICAL_MT4_BUNDLE_V1_DATA_STALE"
CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID"
)

VALIDATION_STAGE = "canonical_bundle_v1_payload_value_time_freshness"
CONTRACT_VERSION = "1.0"
READER_STATUS = "not_called"
NEXT_ALLOWED_STAGE = ["canonical_filesystem_bundle_reader_validation"]
NEXT_BLOCKED_STAGE = [
    "filesystem_reader_activation",
    "readonly_analysis",
    "execution_chain",
]

_COMPONENTS = (
    "manifest_time",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
    "cross_payload",
)

_PAYLOAD_COMPONENTS = {
    "live_tick.json": "live_tick",
    "latest_bars.json": "latest_bars",
    "symbol_spec.json": "symbol_spec",
    "account_snapshot.json": "account_snapshot",
}

_TIMEFRAME_PERIODS = {
    "M15": 900,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}

_TIMEFRAME_KEYS = frozenset({"timeframe", "period_seconds", "bar_count", "bars"})
_BAR_KEYS = frozenset(
    {
        "open_time_utc",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread_points",
    }
)

_UPSTREAM_WARNING_CODES = frozenset({"IDEMPOTENT_REPEAT", "SEQUENCE_GAP"})
_STALE_REASON_CODES = frozenset(
    {
        "WRITER_HEARTBEAT_STALE",
        "LIVE_TICK_STALE",
        "LATEST_BARS_STALE",
        "SYMBOL_SPEC_STALE",
        "ACCOUNT_SNAPSHOT_STALE",
    }
)
_FRESHNESS_REASON_CODES = _STALE_REASON_CODES | {
    "TIMESTAMP_INVALID",
    "TIMESTAMP_FROM_FUTURE",
    "MANIFEST_TIME_ORDER_INVALID",
    "PAYLOAD_GENERATED_AFTER_COMMIT",
}
_LIVE_TICK_REASON_CODES = frozenset(
    {"LIVE_TICK_VALUE_INVALID", "LIVE_TICK_SPREAD_MISMATCH"}
)
_LATEST_BARS_REASON_CODES = frozenset(
    {
        "TIMEFRAME_SET_INVALID",
        "TIMEFRAME_PERIOD_INVALID",
        "BAR_COUNT_INVALID",
        "BAR_TIME_ORDER_INVALID",
        "BAR_NOT_COMPLETED",
        "BAR_VALUE_INVALID",
        "OHLC_RELATION_INVALID",
    }
)
_SYMBOL_SPEC_REASON_CODES = frozenset(
    {
        "SYMBOL_SPEC_VALUE_INVALID",
        "SYMBOL_SPEC_LOT_RELATION_INVALID",
        "SYMBOL_SPEC_CURRENCY_INVALID",
    }
)
_ACCOUNT_REASON_CODES = frozenset(
    {
        "ACCOUNT_SNAPSHOT_VALUE_INVALID",
        "ACCOUNT_SNAPSHOT_LABEL_INVALID",
        "ACCOUNT_SNAPSHOT_CURRENCY_INVALID",
    }
)
_CROSS_REASON_CODES = frozenset(
    {
        "CROSS_PAYLOAD_DIGITS_MISMATCH",
        "CROSS_PAYLOAD_POINT_MISMATCH",
        "CROSS_PAYLOAD_CURRENCY_MISMATCH",
    }
)

_UTC_Z_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
_SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
_SAFE_UPSTREAM_STATUS_PATTERN = re.compile(r"^CANONICAL_MT4_BUNDLE_V1_[A-Z0-9_]+$")


def validate_canonical_mt4_demo_readonly_bundle_v1_values(
    *,
    manifest: object,
    payloads_by_filename: object,
    now_utc: object,
    previous_identity: object | None = None,
    read_policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy | None = None,
) -> dict[str, Any]:
    """Validate canonical v1 values and time semantics without any I/O."""

    upstream = validate_canonical_mt4_demo_readonly_bundle_v1(
        manifest=manifest,
        payloads_by_filename=payloads_by_filename,
        previous_identity=previous_identity,
    )
    upstream_passed = upstream.get("passed") is True
    upstream_status = _safe_upstream_status(upstream.get("status_code"))
    context = _ValueValidationContext(
        upstream_structure_passed=upstream_passed,
        upstream_structure_status_code=upstream_status,
    )
    for warning_code in _safe_upstream_warnings(upstream.get("warning_codes")):
        context.warn(warning_code)

    if not upstream_passed:
        context.block_all("UPSTREAM_STRUCTURE_VALIDATION_BLOCKED")
        return context.result(freshness_checked=False)

    policy = (
        CanonicalMt4DemoReadonlyBundleV1ReadPolicy()
        if read_policy is None
        else read_policy
    )
    if not _is_valid_read_policy(policy):
        context.block_all("READ_POLICY_INVALID")
        return context.result(freshness_checked=False)

    normalized_now = _normalize_now_utc(now_utc)
    if normalized_now is None:
        context.block_all("NOW_UTC_INVALID")
        return context.result(freshness_checked=False)

    manifest_data = manifest
    payloads = payloads_by_filename
    manifest_times = _validate_manifest_times(
        manifest_data,
        normalized_now,
        policy,
        context,
    )
    payload_generated_times = _validate_payload_generated_times(
        payloads,
        manifest_times.get("committed_at_utc"),
        normalized_now,
        policy,
        context,
    )

    live_tick = payloads["live_tick.json"]
    latest_bars = payloads["latest_bars.json"]
    symbol_spec = payloads["symbol_spec.json"]
    account_snapshot = payloads["account_snapshot.json"]

    _validate_live_tick(
        live_tick,
        normalized_now,
        policy,
        context,
    )
    _validate_latest_bars(
        latest_bars,
        payload_generated_times.get("latest_bars"),
        normalized_now,
        policy,
        context,
    )
    _validate_symbol_spec(
        symbol_spec,
        normalized_now,
        policy,
        context,
    )
    _validate_account_snapshot(
        account_snapshot,
        normalized_now,
        policy,
        context,
    )
    _validate_cross_payload_semantics(
        live_tick,
        symbol_spec,
        account_snapshot,
        context,
    )

    return context.result(freshness_checked=True)


def _is_valid_read_policy(value: object) -> bool:
    if not isinstance(value, CanonicalMt4DemoReadonlyBundleV1ReadPolicy):
        return False
    positive_thresholds = (
        value.writer_heartbeat_max_age_seconds,
        value.live_tick_max_age_seconds,
        value.latest_bars_max_age_seconds,
        value.symbol_spec_max_age_seconds,
        value.account_snapshot_max_age_seconds,
    )
    return all(_is_positive_int(item) for item in positive_thresholds) and (
        _is_non_negative_int(value.max_future_skew_seconds)
    )


def _normalize_now_utc(value: object) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            return None
        return value.astimezone(UTC)
    except (OverflowError, TypeError, ValueError):
        return None


def _parse_utc_z(value: object) -> datetime | None:
    if not isinstance(value, str) or _UTC_Z_PATTERN.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(UTC)
    except (OverflowError, TypeError, ValueError):
        return None


def _validate_manifest_times(
    manifest: dict[str, Any],
    now_utc: datetime,
    policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    context: "_ValueValidationContext",
) -> dict[str, datetime | None]:
    parsed_times = {
        field_name: _validated_timestamp(
            manifest.get(field_name),
            "manifest_time",
            now_utc,
            policy.max_future_skew_seconds,
            context,
        )
        for field_name in (
            "generated_at_utc",
            "committed_at_utc",
            "writer_heartbeat_at_utc",
        )
    }
    generated_at = parsed_times["generated_at_utc"]
    committed_at = parsed_times["committed_at_utc"]
    heartbeat_at = parsed_times["writer_heartbeat_at_utc"]

    if generated_at is not None and committed_at is not None:
        if committed_at < generated_at:
            context.add("manifest_time", "MANIFEST_TIME_ORDER_INVALID")
    if heartbeat_at is not None:
        _check_stale(
            heartbeat_at,
            now_utc,
            policy.writer_heartbeat_max_age_seconds,
            "manifest_time",
            "WRITER_HEARTBEAT_STALE",
            context,
        )
    return parsed_times


def _validate_payload_generated_times(
    payloads: dict[str, dict[str, Any]],
    committed_at: datetime | None,
    now_utc: datetime,
    policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    context: "_ValueValidationContext",
) -> dict[str, datetime | None]:
    parsed_times: dict[str, datetime | None] = {}
    for filename, component_name in _PAYLOAD_COMPONENTS.items():
        generated_at = _validated_timestamp(
            payloads[filename].get("generated_at_utc"),
            component_name,
            now_utc,
            policy.max_future_skew_seconds,
            context,
        )
        parsed_times[component_name] = generated_at
        if generated_at is not None and committed_at is not None:
            if (
                generated_at - committed_at
            ).total_seconds() > policy.max_future_skew_seconds:
                context.add(component_name, "PAYLOAD_GENERATED_AFTER_COMMIT")

    latest_bars_generated = parsed_times["latest_bars"]
    if latest_bars_generated is not None:
        _check_stale(
            latest_bars_generated,
            now_utc,
            policy.latest_bars_max_age_seconds,
            "latest_bars",
            "LATEST_BARS_STALE",
            context,
        )
    return parsed_times


def _validate_live_tick(
    payload: dict[str, Any],
    now_utc: datetime,
    policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    context: "_ValueValidationContext",
) -> None:
    tick_time = _validated_timestamp(
        payload.get("tick_time_utc"),
        "live_tick",
        now_utc,
        policy.max_future_skew_seconds,
        context,
    )
    if tick_time is not None:
        _check_stale(
            tick_time,
            now_utc,
            policy.live_tick_max_age_seconds,
            "live_tick",
            "LIVE_TICK_STALE",
            context,
        )

    bid = payload.get("bid")
    ask = payload.get("ask")
    spread = payload.get("spread")
    point = payload.get("point")
    spread_points = payload.get("spread_points")
    digits = payload.get("digits")

    number_values_valid = all(
        _is_finite_number(value) for value in (bid, ask, spread, point)
    )
    integer_values_valid = _is_non_negative_int(spread_points) and (
        _is_int_between(digits, 0, 8)
    )
    if (
        not number_values_valid
        or not integer_values_valid
        or (number_values_valid and (bid <= 0 or ask < bid or spread < 0 or point <= 0))
    ):
        context.add("live_tick", "LIVE_TICK_VALUE_INVALID")
        return

    tolerance = max(point / 2, 1e-9)
    if not math.isclose(spread, ask - bid, rel_tol=0, abs_tol=tolerance) or not (
        math.isclose(
            spread,
            spread_points * point,
            rel_tol=0,
            abs_tol=tolerance,
        )
    ):
        context.add("live_tick", "LIVE_TICK_SPREAD_MISMATCH")


def _validate_latest_bars(
    payload: dict[str, Any],
    generated_at: datetime | None,
    now_utc: datetime,
    policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    context: "_ValueValidationContext",
) -> None:
    timeframes = payload.get("timeframes")
    if not isinstance(timeframes, list):
        context.add("latest_bars", "TIMEFRAME_SET_INVALID")
        return

    expected_names = list(_TIMEFRAME_PERIODS)
    observed_names = [
        item.get("timeframe") if isinstance(item, dict) else None
        for item in timeframes
    ]
    if len(timeframes) != 4 or observed_names != expected_names:
        context.add("latest_bars", "TIMEFRAME_SET_INVALID")

    for timeframe in timeframes:
        if not isinstance(timeframe, dict) or set(timeframe) != _TIMEFRAME_KEYS:
            context.add("latest_bars", "TIMEFRAME_SET_INVALID")
            continue

        timeframe_name = timeframe.get("timeframe")
        expected_period = (
            _TIMEFRAME_PERIODS.get(timeframe_name)
            if isinstance(timeframe_name, str)
            else None
        )
        period_seconds = timeframe.get("period_seconds")
        if expected_period is None or not _is_positive_int(period_seconds) or (
            period_seconds != expected_period
        ):
            context.add("latest_bars", "TIMEFRAME_PERIOD_INVALID")

        bars = timeframe.get("bars")
        bar_count = timeframe.get("bar_count")
        if (
            not _is_int_between(bar_count, 1, 500)
            or not isinstance(bars, list)
            or not bars
            or (isinstance(bars, list) and bar_count != len(bars))
        ):
            context.add("latest_bars", "BAR_COUNT_INVALID")
        if not isinstance(bars, list):
            continue

        previous_open_time: datetime | None = None
        for bar in bars:
            if not isinstance(bar, dict) or set(bar) != _BAR_KEYS:
                context.add("latest_bars", "BAR_VALUE_INVALID")
                continue

            open_time = _validated_timestamp(
                bar.get("open_time_utc"),
                "latest_bars",
                now_utc,
                policy.max_future_skew_seconds,
                context,
            )
            if open_time is not None:
                if previous_open_time is not None and open_time <= previous_open_time:
                    context.add("latest_bars", "BAR_TIME_ORDER_INVALID")
                previous_open_time = open_time
                if generated_at is not None and expected_period is not None:
                    try:
                        if open_time + timedelta(seconds=expected_period) > generated_at:
                            context.add("latest_bars", "BAR_NOT_COMPLETED")
                    except OverflowError:
                        context.add("latest_bars", "BAR_NOT_COMPLETED")

            ohlc = tuple(bar.get(field_name) for field_name in ("open", "high", "low", "close"))
            if not all(_is_positive_number(value) for value in ohlc):
                context.add("latest_bars", "BAR_VALUE_INVALID")
            else:
                open_value, high, low, close = ohlc
                if high < max(open_value, close, low) or low > min(
                    open_value,
                    close,
                    high,
                ):
                    context.add("latest_bars", "OHLC_RELATION_INVALID")

            if not _is_non_negative_int(bar.get("tick_volume")) or not (
                _is_non_negative_int(bar.get("spread_points"))
            ):
                context.add("latest_bars", "BAR_VALUE_INVALID")


def _validate_symbol_spec(
    payload: dict[str, Any],
    now_utc: datetime,
    policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    context: "_ValueValidationContext",
) -> None:
    spec_time = _validated_timestamp(
        payload.get("spec_time_utc"),
        "symbol_spec",
        now_utc,
        policy.max_future_skew_seconds,
        context,
    )
    if spec_time is not None:
        _check_stale(
            spec_time,
            now_utc,
            policy.symbol_spec_max_age_seconds,
            "symbol_spec",
            "SYMBOL_SPEC_STALE",
            context,
        )

    if not _is_int_between(payload.get("digits"), 0, 8):
        context.add("symbol_spec", "SYMBOL_SPEC_VALUE_INVALID")
    positive_numbers = (
        "point",
        "tick_size",
        "tick_value",
        "contract_size",
        "min_lot",
        "lot_step",
        "max_lot",
    )
    if not all(_is_positive_number(payload.get(field_name)) for field_name in positive_numbers):
        context.add("symbol_spec", "SYMBOL_SPEC_VALUE_INVALID")

    min_lot = payload.get("min_lot")
    lot_step = payload.get("lot_step")
    max_lot = payload.get("max_lot")
    if all(_is_positive_number(value) for value in (min_lot, lot_step, max_lot)):
        if min_lot > max_lot or lot_step > max_lot:
            context.add("symbol_spec", "SYMBOL_SPEC_LOT_RELATION_INVALID")

    if (
        payload.get("base_currency") != "XAU"
        or payload.get("profit_currency") != "USD"
        or not _is_safe_label(payload.get("margin_currency"))
    ):
        context.add("symbol_spec", "SYMBOL_SPEC_CURRENCY_INVALID")
    if not _is_safe_label(payload.get("trade_mode_readonly_label")) or not (
        _is_safe_label(payload.get("session_status_readonly_label"))
    ):
        context.add("symbol_spec", "SYMBOL_SPEC_VALUE_INVALID")


def _validate_account_snapshot(
    payload: dict[str, Any],
    now_utc: datetime,
    policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    context: "_ValueValidationContext",
) -> None:
    snapshot_time = _validated_timestamp(
        payload.get("snapshot_time_utc"),
        "account_snapshot",
        now_utc,
        policy.max_future_skew_seconds,
        context,
    )
    if snapshot_time is not None:
        _check_stale(
            snapshot_time,
            now_utc,
            policy.account_snapshot_max_age_seconds,
            "account_snapshot",
            "ACCOUNT_SNAPSHOT_STALE",
            context,
        )

    if not _is_safe_label(payload.get("account_alias_masked")) or not (
        _is_safe_label(payload.get("server_name_masked"))
    ):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_LABEL_INVALID")
    if payload.get("account_currency") != "USD":
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_CURRENCY_INVALID")

    if not all(
        _is_non_negative_number(payload.get(field_name))
        for field_name in ("balance", "equity", "margin")
    ):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_VALUE_INVALID")
    if not _is_finite_number(payload.get("free_margin")):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_VALUE_INVALID")
    margin_level = payload.get("margin_level")
    if margin_level is not None and not _is_non_negative_number(margin_level):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_VALUE_INVALID")
    if not _is_positive_number(payload.get("leverage")):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_VALUE_INVALID")
    if not all(
        _is_non_negative_int(payload.get(field_name))
        for field_name in ("positions_count", "pending_orders_count")
    ):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_VALUE_INVALID")
    if not all(
        _is_finite_number(payload.get(field_name))
        for field_name in ("daily_realized_pnl", "daily_floating_pnl")
    ):
        context.add("account_snapshot", "ACCOUNT_SNAPSHOT_VALUE_INVALID")


def _validate_cross_payload_semantics(
    live_tick: dict[str, Any],
    symbol_spec: dict[str, Any],
    account_snapshot: dict[str, Any],
    context: "_ValueValidationContext",
) -> None:
    live_digits = live_tick.get("digits")
    spec_digits = symbol_spec.get("digits")
    if _is_int_between(live_digits, 0, 8) and _is_int_between(spec_digits, 0, 8):
        if live_digits != spec_digits:
            context.add("cross_payload", "CROSS_PAYLOAD_DIGITS_MISMATCH")

    live_point = live_tick.get("point")
    spec_point = symbol_spec.get("point")
    if _is_positive_number(live_point) and _is_positive_number(spec_point):
        if not math.isclose(
            live_point,
            spec_point,
            rel_tol=0,
            abs_tol=max(abs(spec_point) * 1e-12, 1e-12),
        ):
            context.add("cross_payload", "CROSS_PAYLOAD_POINT_MISMATCH")

    account_currency = account_snapshot.get("account_currency")
    profit_currency = symbol_spec.get("profit_currency")
    if account_currency != profit_currency or account_currency != "USD":
        context.add("cross_payload", "CROSS_PAYLOAD_CURRENCY_MISMATCH")


def _validated_timestamp(
    value: object,
    component_name: str,
    now_utc: datetime,
    max_future_skew_seconds: int,
    context: "_ValueValidationContext",
) -> datetime | None:
    parsed = _parse_utc_z(value)
    if parsed is None:
        context.add(component_name, "TIMESTAMP_INVALID")
        return None
    if (parsed - now_utc).total_seconds() > max_future_skew_seconds:
        context.add(component_name, "TIMESTAMP_FROM_FUTURE")
    return parsed


def _check_stale(
    observed_at: datetime,
    now_utc: datetime,
    max_age_seconds: int,
    component_name: str,
    reason_code: str,
    context: "_ValueValidationContext",
) -> None:
    if (now_utc - observed_at).total_seconds() > max_age_seconds:
        context.add(component_name, reason_code)


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_positive_number(value: object) -> bool:
    return _is_finite_number(value) and value > 0


def _is_non_negative_number(value: object) -> bool:
    return _is_finite_number(value) and value >= 0


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_int_between(value: object, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def _is_safe_label(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and _SAFE_LABEL_PATTERN.fullmatch(value) is not None
    )


def _safe_upstream_status(value: object) -> str:
    if isinstance(value, str) and _SAFE_UPSTREAM_STATUS_PATTERN.fullmatch(value):
        return value
    return "CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID"


def _safe_upstream_warnings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        warning_code
        for warning_code in value
        if isinstance(warning_code, str) and warning_code in _UPSTREAM_WARNING_CODES
    ]


def _select_status_code(reason_codes: list[str], warning_codes: list[str]) -> str:
    if not reason_codes:
        if warning_codes:
            return CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
        return CANONICAL_MT4_BUNDLE_V1_VALUE_VALID

    reasons = set(reason_codes)
    priority = (
        (
            {"UPSTREAM_STRUCTURE_VALIDATION_BLOCKED"},
            CANONICAL_MT4_BUNDLE_V1_VALUE_UPSTREAM_BLOCKED,
        ),
        ({"READ_POLICY_INVALID"}, CANONICAL_MT4_BUNDLE_V1_READ_POLICY_INVALID),
        ({"NOW_UTC_INVALID"}, CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID),
        ({"TIMESTAMP_INVALID"}, CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID),
        (
            {"TIMESTAMP_FROM_FUTURE"},
            CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_FROM_FUTURE,
        ),
        (
            {"MANIFEST_TIME_ORDER_INVALID"},
            CANONICAL_MT4_BUNDLE_V1_MANIFEST_TIME_INVALID,
        ),
        ({"PAYLOAD_GENERATED_AFTER_COMMIT"}, CANONICAL_MT4_BUNDLE_V1_TIMESTAMP_INVALID),
        (_STALE_REASON_CODES, CANONICAL_MT4_BUNDLE_V1_DATA_STALE),
        (_LIVE_TICK_REASON_CODES, CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID),
        (_LATEST_BARS_REASON_CODES, CANONICAL_MT4_BUNDLE_V1_LATEST_BARS_INVALID),
        (_SYMBOL_SPEC_REASON_CODES, CANONICAL_MT4_BUNDLE_V1_SYMBOL_SPEC_INVALID),
        (_ACCOUNT_REASON_CODES, CANONICAL_MT4_BUNDLE_V1_ACCOUNT_SNAPSHOT_INVALID),
        (_CROSS_REASON_CODES, CANONICAL_MT4_BUNDLE_V1_CROSS_PAYLOAD_INVALID),
    )
    for matching_reasons, status_code in priority:
        if reasons.intersection(matching_reasons):
            return status_code
    return CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID


class _ValueValidationContext:
    def __init__(
        self,
        *,
        upstream_structure_passed: bool,
        upstream_structure_status_code: str,
    ) -> None:
        self.upstream_structure_passed = upstream_structure_passed
        self.upstream_structure_status_code = upstream_structure_status_code
        self.reason_codes: list[str] = []
        self.warning_codes: list[str] = []
        self.component_reasons: dict[str, list[str]] = {
            component_name: [] for component_name in _COMPONENTS
        }
        self.component_warnings: dict[str, list[str]] = {
            component_name: [] for component_name in _COMPONENTS
        }

    def add(self, component_name: str, reason_code: str) -> None:
        if reason_code not in self.reason_codes:
            self.reason_codes.append(reason_code)
        if reason_code not in self.component_reasons[component_name]:
            self.component_reasons[component_name].append(reason_code)

    def block_all(self, reason_code: str) -> None:
        for component_name in _COMPONENTS:
            self.add(component_name, reason_code)

    def warn(self, warning_code: str) -> None:
        if warning_code not in self.warning_codes:
            self.warning_codes.append(warning_code)

    def result(self, *, freshness_checked: bool) -> dict[str, Any]:
        passed = not self.reason_codes
        freshness_passed = freshness_checked and not set(self.reason_codes).intersection(
            _FRESHNESS_REASON_CODES
        )
        component_statuses = []
        for component_name in _COMPONENTS:
            reason_codes = list(self.component_reasons[component_name])
            warning_codes = list(self.component_warnings[component_name])
            component_statuses.append(
                {
                    "component_name": component_name,
                    "passed": not reason_codes,
                    "status_code": (
                        f"CANONICAL_MT4_BUNDLE_V1_VALUE_{component_name.upper()}_VALID"
                        if not reason_codes
                        else f"CANONICAL_MT4_BUNDLE_V1_VALUE_{component_name.upper()}_INVALID"
                    ),
                    "reason_codes": reason_codes,
                    "warning_codes": warning_codes,
                }
            )

        return {
            "passed": passed,
            "status_code": _select_status_code(self.reason_codes, self.warning_codes),
            "validation_stage": VALIDATION_STAGE,
            "contract_version": CONTRACT_VERSION,
            "upstream_structure_passed": self.upstream_structure_passed,
            "upstream_structure_status_code": self.upstream_structure_status_code,
            "reason_codes": list(self.reason_codes),
            "warning_codes": list(self.warning_codes),
            "component_statuses": component_statuses,
            "reader_status": READER_STATUS,
            "freshness_checked": freshness_checked,
            "freshness_passed": freshness_passed,
            "ready_for_readonly_analysis": False,
            "next_allowed_stage": list(NEXT_ALLOWED_STAGE) if passed else [],
            "next_blocked_stage": list(NEXT_BLOCKED_STAGE),
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
            "is_trading_permission": False,
            "is_execution_instruction": False,
            "allowed_to_call_ea": False,
            "allowed_to_modify_risk": False,
        }
