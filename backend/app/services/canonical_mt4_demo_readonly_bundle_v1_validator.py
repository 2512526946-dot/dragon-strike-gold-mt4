from __future__ import annotations

import re
from typing import Any


SCHEMA_VERSION = "1.0"
SOURCE_ID = "trademax_mt4_demo_readonly_bridge"
CANONICAL_SYMBOL = "XAUUSD"

REQUIRED_PAYLOADS = {
    "live_tick.json": "live_tick",
    "latest_bars.json": "latest_bars",
    "symbol_spec.json": "symbol_spec",
    "account_snapshot.json": "account_snapshot",
}

SAFETY_VALUES = {
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

CANONICAL_MT4_BUNDLE_V1_VALID = "CANONICAL_MT4_BUNDLE_V1_VALID"
CANONICAL_MT4_BUNDLE_V1_VALID_WITH_WARNINGS = (
    "CANONICAL_MT4_BUNDLE_V1_VALID_WITH_WARNINGS"
)
CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_MANIFEST_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_MANIFEST_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_REQUIRED_FILES_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_REQUIRED_FILES_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_PAYLOAD_SET_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_PAYLOAD_SET_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_PAYLOAD_STRUCTURE_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_PAYLOAD_STRUCTURE_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_SCHEMA_VERSION_UNSUPPORTED = (
    "CANONICAL_MT4_BUNDLE_V1_SCHEMA_VERSION_UNSUPPORTED"
)
CANONICAL_MT4_BUNDLE_V1_SOURCE_ID_REJECTED = (
    "CANONICAL_MT4_BUNDLE_V1_SOURCE_ID_REJECTED"
)
CANONICAL_MT4_BUNDLE_V1_FORBIDDEN_FIELD_DETECTED = (
    "CANONICAL_MT4_BUNDLE_V1_FORBIDDEN_FIELD_DETECTED"
)
CANONICAL_MT4_BUNDLE_V1_SAFETY_FIELD_VIOLATION = (
    "CANONICAL_MT4_BUNDLE_V1_SAFETY_FIELD_VIOLATION"
)
CANONICAL_MT4_BUNDLE_V1_IDENTITY_MISMATCH = (
    "CANONICAL_MT4_BUNDLE_V1_IDENTITY_MISMATCH"
)
CANONICAL_MT4_BUNDLE_V1_SYMBOL_MISMATCH = (
    "CANONICAL_MT4_BUNDLE_V1_SYMBOL_MISMATCH"
)
CANONICAL_MT4_BUNDLE_V1_SEQUENCE_ROLLBACK = (
    "CANONICAL_MT4_BUNDLE_V1_SEQUENCE_ROLLBACK"
)
CANONICAL_MT4_BUNDLE_V1_SEQUENCE_IDENTITY_CONFLICT = (
    "CANONICAL_MT4_BUNDLE_V1_SEQUENCE_IDENTITY_CONFLICT"
)

VALIDATION_STAGE = "canonical_bundle_v1_structure_identity_safety"
READER_STATUS = "not_called"
NEXT_ALLOWED_STAGE = ["canonical_payload_value_validation"]
NEXT_BLOCKED_STAGE = [
    "filesystem_reader_activation",
    "readonly_analysis",
    "execution_chain",
]

_COMPONENTS = (
    "manifest",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
)

_MANIFEST_KEYS = frozenset(
    {
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
)

_COMMON_PAYLOAD_KEYS = frozenset(
    {
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
)

_PAYLOAD_KEYS = {
    "live_tick": _COMMON_PAYLOAD_KEYS
    | {
        "canonical_symbol",
        "broker_symbol",
        "bid",
        "ask",
        "spread",
        "spread_points",
        "digits",
        "point",
        "tick_time_utc",
    },
    "latest_bars": _COMMON_PAYLOAD_KEYS
    | {"canonical_symbol", "broker_symbol", "timeframes"},
    "symbol_spec": _COMMON_PAYLOAD_KEYS
    | {
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
    },
    "account_snapshot": _COMMON_PAYLOAD_KEYS
    | {
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
    },
}

_DESCRIPTOR_KEYS = frozenset(
    {"filename", "file_type", "schema_version", "content_sha256"}
)
_IDENTITY_FIELDS = (
    "bundle_id",
    "sequence",
    "source_id",
    "writer_version",
    "terminal_id_masked",
    "account_mode",
    "is_demo_account",
    "is_live_account",
)
_MARKET_PAYLOADS = frozenset({"live_tick", "latest_bars", "symbol_spec"})

_FORBIDDEN_KEYS = frozenset(
    key.casefold()
    for key in {
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
        "risk_limits",
        "daily_loss_pct",
        "max_single_trade_loss_pct",
        "max_daily_loss_pct",
        "no_overnight",
        "primary_session",
        "leverage_cap",
        "freshness_thresholds_seconds",
        "file_size_limits_bytes",
        "max_total_bundle_bytes",
        "checksum_policy",
    }
)

_BUNDLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_INPUT_REASONS = frozenset(
    {
        "MANIFEST_NOT_OBJECT",
        "PAYLOAD_MAP_NOT_OBJECT",
        "PREVIOUS_IDENTITY_INVALID",
        "NON_STRING_FIELD_NAME",
    }
)
_MANIFEST_REASONS = frozenset(
    {
        "MANIFEST_FIELD_SET_INVALID",
        "MANIFEST_VALUE_INVALID",
        "MANIFEST_SEQUENCE_INVALID",
    }
)
_PAYLOAD_STRUCTURE_REASONS = frozenset(
    {
        "PAYLOAD_NOT_OBJECT",
        "PAYLOAD_FIELD_SET_INVALID",
        "PAYLOAD_VALUE_INVALID",
        "PAYLOAD_SEQUENCE_INVALID",
    }
)


def validate_canonical_mt4_demo_readonly_bundle_v1(
    *,
    manifest: object,
    payloads_by_filename: object,
    previous_identity: object | None = None,
) -> dict[str, Any]:
    """Validate the in-memory canonical v1 structure, identity, and safety boundary."""

    context = _ValidationContext()

    manifest_object = manifest if isinstance(manifest, dict) else None
    payload_map = payloads_by_filename if isinstance(payloads_by_filename, dict) else None

    if manifest_object is None:
        context.add("manifest", "MANIFEST_NOT_OBJECT")
    else:
        _collect_forbidden_fields(manifest_object, "manifest", context)
        _validate_manifest(manifest_object, context)

    if payload_map is None:
        for component_name in _COMPONENTS[1:]:
            context.add(component_name, "PAYLOAD_MAP_NOT_OBJECT")
    else:
        _validate_payload_set(payload_map, context)
        for filename, file_type in REQUIRED_PAYLOADS.items():
            if filename not in payload_map:
                continue
            payload = payload_map[filename]
            if not isinstance(payload, dict):
                context.add(file_type, "PAYLOAD_NOT_OBJECT")
                continue
            _collect_forbidden_fields(payload, file_type, context)
            _validate_payload(payload, file_type, context)

    if manifest_object is not None and payload_map is not None:
        _validate_cross_file_consistency(manifest_object, payload_map, context)

    validated_previous_identity = _validate_previous_identity(previous_identity, context)
    if manifest_object is not None and validated_previous_identity is not False:
        _validate_sequence_history(
            manifest_object,
            validated_previous_identity,
            context,
        )

    return context.result()


def _validate_manifest(manifest: dict[object, object], context: "_ValidationContext") -> None:
    if set(manifest) != _MANIFEST_KEYS:
        context.add("manifest", "MANIFEST_FIELD_SET_INVALID")

    if manifest.get("schema_version") != SCHEMA_VERSION:
        context.add("manifest", "SCHEMA_VERSION_UNSUPPORTED")
    if manifest.get("source_id") != SOURCE_ID:
        context.add("manifest", "SOURCE_ID_REJECTED")
    if manifest.get("manifest_type") != "mt4_demo_readonly_snapshot_manifest":
        context.add("manifest", "MANIFEST_VALUE_INVALID")
    if not _is_safe_bundle_id(manifest.get("bundle_id")):
        context.add("manifest", "MANIFEST_VALUE_INVALID")
    if not _is_positive_int(manifest.get("sequence")):
        context.add("manifest", "MANIFEST_SEQUENCE_INVALID")

    for field_name in (
        "generated_at_utc",
        "committed_at_utc",
        "writer_heartbeat_at_utc",
    ):
        if not _is_utc_z_string(manifest.get(field_name)):
            context.add("manifest", "MANIFEST_VALUE_INVALID")

    for field_name in ("writer_version", "terminal_id_masked", "broker_symbol"):
        if not _is_safe_label(manifest.get(field_name)):
            context.add("manifest", "MANIFEST_VALUE_INVALID")

    if manifest.get("canonical_symbol") != CANONICAL_SYMBOL:
        context.add("manifest", "SYMBOL_MISMATCH")
    if manifest.get("commit_state") != "complete":
        context.add("manifest", "MANIFEST_VALUE_INVALID")
    if manifest.get("optional_files") != []:
        context.add("manifest", "MANIFEST_VALUE_INVALID")
    if manifest.get("compatible_reader_schema_versions") != [SCHEMA_VERSION]:
        context.add("manifest", "MANIFEST_VALUE_INVALID")

    _validate_safety_values(manifest, "manifest", context)
    _validate_required_files(manifest.get("required_files"), context)


def _validate_required_files(value: object, context: "_ValidationContext") -> None:
    expected_items = list(REQUIRED_PAYLOADS.items())
    if not isinstance(value, list) or len(value) != len(expected_items):
        context.add("manifest", "REQUIRED_FILES_INVALID")
        return

    for descriptor, (expected_filename, expected_file_type) in zip(
        value,
        expected_items,
        strict=True,
    ):
        if not isinstance(descriptor, dict) or set(descriptor) != _DESCRIPTOR_KEYS:
            context.add("manifest", "REQUIRED_FILES_INVALID")
            continue

        filename = descriptor.get("filename")
        if (
            filename != expected_filename
            or not _is_safe_basename(filename)
            or descriptor.get("file_type") != expected_file_type
            or descriptor.get("schema_version") != SCHEMA_VERSION
        ):
            context.add("manifest", "REQUIRED_FILES_INVALID")

        checksum = descriptor.get("content_sha256")
        if checksum is not None and (
            not isinstance(checksum, str) or _SHA256_PATTERN.fullmatch(checksum) is None
        ):
            context.add("manifest", "REQUIRED_FILES_INVALID")


def _validate_payload_set(
    payload_map: dict[object, object],
    context: "_ValidationContext",
) -> None:
    expected_filenames = set(REQUIRED_PAYLOADS)
    observed_filenames = set(payload_map)
    if observed_filenames == expected_filenames:
        return

    context.add("manifest", "PAYLOAD_SET_INVALID")
    for filename, file_type in REQUIRED_PAYLOADS.items():
        if filename not in payload_map:
            context.add(file_type, "PAYLOAD_SET_INVALID")


def _validate_payload(
    payload: dict[object, object],
    file_type: str,
    context: "_ValidationContext",
) -> None:
    if set(payload) != _PAYLOAD_KEYS[file_type]:
        context.add(file_type, "PAYLOAD_FIELD_SET_INVALID")
    if payload.get("file_type") != file_type:
        context.add(file_type, "PAYLOAD_VALUE_INVALID")
    if payload.get("schema_version") != SCHEMA_VERSION:
        context.add(file_type, "SCHEMA_VERSION_UNSUPPORTED")
    if payload.get("source_id") != SOURCE_ID:
        context.add(file_type, "SOURCE_ID_REJECTED")
    if not _is_positive_int(payload.get("sequence")):
        context.add(file_type, "PAYLOAD_SEQUENCE_INVALID")
    if not _is_utc_z_string(payload.get("generated_at_utc")):
        context.add(file_type, "PAYLOAD_VALUE_INVALID")
    for field_name in ("writer_version", "terminal_id_masked"):
        if not _is_safe_label(payload.get(field_name)):
            context.add(file_type, "PAYLOAD_VALUE_INVALID")

    if file_type == "latest_bars" and not isinstance(payload.get("timeframes"), list):
        context.add(file_type, "PAYLOAD_VALUE_INVALID")

    _validate_safety_values(payload, file_type, context)


def _validate_safety_values(
    value: dict[object, object],
    component_name: str,
    context: "_ValidationContext",
) -> None:
    for field_name, expected_value in SAFETY_VALUES.items():
        if not _same_typed_value(value.get(field_name), expected_value):
            context.add(component_name, "SAFETY_FIELD_VIOLATION")


def _validate_cross_file_consistency(
    manifest: dict[object, object],
    payload_map: dict[object, object],
    context: "_ValidationContext",
) -> None:
    for filename, file_type in REQUIRED_PAYLOADS.items():
        payload = payload_map.get(filename)
        if not isinstance(payload, dict):
            continue

        for field_name in _IDENTITY_FIELDS:
            if field_name in manifest and field_name in payload and not _same_typed_value(
                manifest[field_name], payload[field_name]
            ):
                context.add(file_type, "IDENTITY_MISMATCH")

        if file_type in _MARKET_PAYLOADS:
            for field_name in ("canonical_symbol", "broker_symbol"):
                if field_name in manifest and field_name in payload and not _same_typed_value(
                    manifest[field_name], payload[field_name]
                ):
                    context.add(file_type, "SYMBOL_MISMATCH")


def _validate_previous_identity(
    value: object | None,
    context: "_ValidationContext",
) -> dict[str, object] | None | bool:
    if value is None:
        return None
    if (
        not isinstance(value, dict)
        or set(value) != {"bundle_id", "sequence"}
        or not _is_safe_bundle_id(value.get("bundle_id"))
        or not _is_positive_int(value.get("sequence"))
    ):
        context.add("manifest", "PREVIOUS_IDENTITY_INVALID")
        return False
    return value


def _validate_sequence_history(
    manifest: dict[object, object],
    previous_identity: dict[str, object] | None,
    context: "_ValidationContext",
) -> None:
    if previous_identity is None:
        return

    current_sequence = manifest.get("sequence")
    current_bundle_id = manifest.get("bundle_id")
    if not _is_positive_int(current_sequence) or not _is_safe_bundle_id(current_bundle_id):
        return

    previous_sequence = previous_identity["sequence"]
    previous_bundle_id = previous_identity["bundle_id"]
    if current_sequence < previous_sequence:
        context.add("manifest", "SEQUENCE_ROLLBACK")
    elif current_sequence == previous_sequence:
        if current_bundle_id != previous_bundle_id:
            context.add("manifest", "SEQUENCE_IDENTITY_CONFLICT")
        else:
            context.warn("IDEMPOTENT_REPEAT")
    elif current_sequence > previous_sequence + 1:
        context.warn("SEQUENCE_GAP")


def _collect_forbidden_fields(
    value: object,
    component_name: str,
    context: "_ValidationContext",
    seen: set[int] | None = None,
) -> None:
    seen = seen if seen is not None else set()
    if isinstance(value, (dict, list)):
        object_id = id(value)
        if object_id in seen:
            return
        seen.add(object_id)

    if isinstance(value, dict):
        for field_name, child_value in value.items():
            if not isinstance(field_name, str):
                context.add(component_name, "NON_STRING_FIELD_NAME")
            elif field_name.casefold() in _FORBIDDEN_KEYS:
                context.add(component_name, "FORBIDDEN_FIELD_DETECTED")
            _collect_forbidden_fields(child_value, component_name, context, seen)
    elif isinstance(value, list):
        for child_value in value:
            _collect_forbidden_fields(child_value, component_name, context, seen)


def _is_safe_basename(value: object) -> bool:
    return (
        isinstance(value, str)
        and value in REQUIRED_PAYLOADS
        and "/" not in value
        and "\\" not in value
        and ".." not in value
    )


def _is_safe_bundle_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and 16 <= len(value) <= 64
        and _BUNDLE_ID_PATTERN.fullmatch(value) is not None
    )


def _is_safe_label(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and _SAFE_LABEL_PATTERN.fullmatch(value) is not None
    )


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_utc_z_string(value: object) -> bool:
    return isinstance(value, str) and len(value) > 1 and value.endswith("Z")


def _same_typed_value(left: object, right: object) -> bool:
    return type(left) is type(right) and left == right


def _select_status_code(reason_codes: list[str], warning_codes: list[str]) -> str:
    if not reason_codes:
        if warning_codes:
            return CANONICAL_MT4_BUNDLE_V1_VALID_WITH_WARNINGS
        return CANONICAL_MT4_BUNDLE_V1_VALID

    reasons = set(reason_codes)
    priority = (
        (_INPUT_REASONS, CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID),
        (
            {"FORBIDDEN_FIELD_DETECTED"},
            CANONICAL_MT4_BUNDLE_V1_FORBIDDEN_FIELD_DETECTED,
        ),
        (
            {"SCHEMA_VERSION_UNSUPPORTED"},
            CANONICAL_MT4_BUNDLE_V1_SCHEMA_VERSION_UNSUPPORTED,
        ),
        ({"SOURCE_ID_REJECTED"}, CANONICAL_MT4_BUNDLE_V1_SOURCE_ID_REJECTED),
        (
            {"SAFETY_FIELD_VIOLATION"},
            CANONICAL_MT4_BUNDLE_V1_SAFETY_FIELD_VIOLATION,
        ),
        (
            {"REQUIRED_FILES_INVALID"},
            CANONICAL_MT4_BUNDLE_V1_REQUIRED_FILES_INVALID,
        ),
        ({"PAYLOAD_SET_INVALID"}, CANONICAL_MT4_BUNDLE_V1_PAYLOAD_SET_INVALID),
        (_PAYLOAD_STRUCTURE_REASONS, CANONICAL_MT4_BUNDLE_V1_PAYLOAD_STRUCTURE_INVALID),
        (_MANIFEST_REASONS, CANONICAL_MT4_BUNDLE_V1_MANIFEST_INVALID),
        ({"SYMBOL_MISMATCH"}, CANONICAL_MT4_BUNDLE_V1_SYMBOL_MISMATCH),
        ({"SEQUENCE_ROLLBACK"}, CANONICAL_MT4_BUNDLE_V1_SEQUENCE_ROLLBACK),
        (
            {"SEQUENCE_IDENTITY_CONFLICT"},
            CANONICAL_MT4_BUNDLE_V1_SEQUENCE_IDENTITY_CONFLICT,
        ),
        ({"IDENTITY_MISMATCH"}, CANONICAL_MT4_BUNDLE_V1_IDENTITY_MISMATCH),
    )
    for matching_reasons, status_code in priority:
        if reasons.intersection(matching_reasons):
            return status_code
    return CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID


class _ValidationContext:
    def __init__(self) -> None:
        self.reason_codes: list[str] = []
        self.warning_codes: list[str] = []
        self.component_reasons: dict[str, list[str]] = {
            component_name: [] for component_name in _COMPONENTS
        }

    def add(self, component_name: str, reason_code: str) -> None:
        if reason_code not in self.reason_codes:
            self.reason_codes.append(reason_code)
        component_reason_codes = self.component_reasons[component_name]
        if reason_code not in component_reason_codes:
            component_reason_codes.append(reason_code)

    def warn(self, warning_code: str) -> None:
        if warning_code not in self.warning_codes:
            self.warning_codes.append(warning_code)

    def result(self) -> dict[str, Any]:
        passed = not self.reason_codes
        component_statuses = []
        for component_name in _COMPONENTS:
            reason_codes = list(self.component_reasons[component_name])
            component_statuses.append(
                {
                    "component_name": component_name,
                    "passed": not reason_codes,
                    "status_code": (
                        f"CANONICAL_MT4_BUNDLE_V1_{component_name.upper()}_VALID"
                        if not reason_codes
                        else f"CANONICAL_MT4_BUNDLE_V1_{component_name.upper()}_INVALID"
                    ),
                    "reason_codes": reason_codes,
                }
            )

        return {
            "passed": passed,
            "status_code": _select_status_code(
                self.reason_codes,
                self.warning_codes,
            ),
            "validation_stage": VALIDATION_STAGE,
            "contract_version": SCHEMA_VERSION,
            "reason_codes": list(self.reason_codes),
            "warning_codes": list(self.warning_codes),
            "component_statuses": component_statuses,
            "reader_status": READER_STATUS,
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
