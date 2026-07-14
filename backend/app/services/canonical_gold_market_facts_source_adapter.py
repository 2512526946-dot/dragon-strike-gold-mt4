from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import UTC as _UTC
from datetime import datetime as _datetime
from datetime import timedelta as _timedelta
from pathlib import Path as _Path
import math as _math
import re as _re

import app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader as _reader
import app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator as _value
import app.services.data_quality_gate as _gate
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldBarSourceV1 as _CanonicalGoldBarSourceV1,
    CanonicalGoldMarketFactsSourceV1 as _CanonicalGoldMarketFactsSourceV1,
    CanonicalGoldSymbolSpecSourceV1 as _CanonicalGoldSymbolSpecSourceV1,
    CanonicalGoldTickSourceV1 as _CanonicalGoldTickSourceV1,
    CanonicalGoldTimeframeSourceV1 as _CanonicalGoldTimeframeSourceV1,
    CanonicalGoldUpstreamEvidenceV1 as _CanonicalGoldUpstreamEvidenceV1,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy as _FilesystemPolicy,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy as _ReadPolicy,
)
from app.services.data_quality_gate import (
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy as _DataQualityPolicy,
)


_AUTHORITY_TOKEN = object()

_CONTRACT_VERSION = "1.0"
_POLICY_PROFILE_VERSION = "canonical_gold_market_facts_policy_v1"
_CANONICAL_SYMBOL = "XAUUSD"
_BROKER_SYMBOL = "GOLD"

_READY_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_READY"
_AUTHORITY_INVALID_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID"
_READER_BLOCKED_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_READER_BLOCKED"
_WARNING_BLOCKED_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_WARNING_BLOCKED"
_DATA_QUALITY_BLOCKED_STATUS = (
    "CANONICAL_GOLD_SOURCE_ADAPTER_DATA_QUALITY_BLOCKED"
)
_IDENTITY_INVALID_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID"
_SOURCE_INVALID_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID"
_SAFE_FAILURE_STATUS = "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE"

_AUTHORITY_INVALID = "GOLD_SOURCE_AUTHORITY_INVALID"
_READER_NOT_READY = "GOLD_SOURCE_READER_NOT_READY"
_READER_RESULT_INVALID = "GOLD_SOURCE_READER_RESULT_INVALID"
_UPSTREAM_WARNING_REJECTED = "GOLD_SOURCE_UPSTREAM_WARNING_REJECTED"
_DATA_QUALITY_NOT_READY = "GOLD_SOURCE_DATA_QUALITY_NOT_READY"
_DATA_QUALITY_RESULT_INVALID = "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID"
_SAME_ATTEMPT_IDENTITY_INVALID = "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID"
_CONSTRUCTION_INVALID = "GOLD_SOURCE_CONSTRUCTION_INVALID"
_EXCEPTION_SANITIZED = "GOLD_SOURCE_EXCEPTION_SANITIZED"

_READER_RESULT_KEYS = (
    "passed",
    "status_code",
    "validation_stage",
    "contract_version",
    "reader_status",
    "reason_codes",
    "warning_codes",
    "component_statuses",
    "manifest_consistency_checked",
    "manifest_consistency_passed",
    "checksum_checked",
    "checksum_passed",
    "upstream_value_passed",
    "upstream_value_status_code",
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
)
_READER_COMPONENT_KEYS = (
    "component_name",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
)
_READER_COMPONENT_NAMES = (
    "filesystem_boundary",
    "snapshot_manifest",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
    "manifest_consistency",
    "checksum",
    "upstream_value_validation",
)
_READER_FILE_COMPONENT_NAMES = frozenset(
    {
        "snapshot_manifest",
        "live_tick",
        "latest_bars",
        "symbol_spec",
        "account_snapshot",
    }
)
_READER_REASON_COMPONENTS = {
    "ALLOWED_ROOT_INPUT_INVALID": frozenset({"filesystem_boundary"}),
    "BUNDLE_DIRECTORY_INPUT_INVALID": frozenset({"filesystem_boundary"}),
    "FILESYSTEM_POLICY_INVALID": frozenset({"filesystem_boundary"}),
    "ALLOWED_ROOT_REJECTED": frozenset({"filesystem_boundary"}),
    "BUNDLE_DIRECTORY_REJECTED": frozenset({"filesystem_boundary"}),
    "PATH_ESCAPE_BLOCKED": frozenset(
        {"filesystem_boundary", *_READER_FILE_COMPONENT_NAMES}
    ),
    "SYMLINK_BLOCKED": frozenset(
        {"filesystem_boundary", *_READER_FILE_COMPONENT_NAMES}
    ),
    "FILE_NOT_FOUND": _READER_FILE_COMPONENT_NAMES,
    "FILE_SIZE_LIMIT_EXCEEDED": _READER_FILE_COMPONENT_NAMES,
    "FILE_UNREADABLE": _READER_FILE_COMPONENT_NAMES,
    "UTF8_BOM_REJECTED": _READER_FILE_COMPONENT_NAMES,
    "UTF8_DECODE_INVALID": _READER_FILE_COMPONENT_NAMES,
    "JSON_DUPLICATE_KEY": _READER_FILE_COMPONENT_NAMES,
    "JSON_INVALID": _READER_FILE_COMPONENT_NAMES,
    "JSON_NOT_OBJECT": _READER_FILE_COMPONENT_NAMES,
    "MANIFEST_CHANGED_DURING_READ": frozenset({"manifest_consistency"}),
    "MANIFEST_UNSTABLE": frozenset({"manifest_consistency"}),
    "CHECKSUM_MISMATCH": frozenset({"checksum"}),
    "UPSTREAM_VALUE_VALIDATION_BLOCKED": frozenset(
        {"upstream_value_validation"}
    ),
    "FILESYSTEM_READER_EXCEPTION_SANITIZED": frozenset(
        {"filesystem_boundary", "upstream_value_validation"}
    ),
}
_READER_NEXT_ALLOWED = ("canonical_data_quality_gate_integration",)
_READER_NEXT_BLOCKED = (
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
)

_GATE_RESULT_KEYS = (
    "passed",
    "status_code",
    "validation_stage",
    "contract_version",
    "reader_status",
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "data_quality_status",
    "reason_codes",
    "warning_codes",
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
)
_GATE_NEXT_ALLOWED = ("canonical_diagnostics_integration",)
_GATE_SUCCESS_NEXT_BLOCKED = ("api_reader_activation", "execution_chain")
_GATE_BLOCKED_NEXT = (
    "canonical_diagnostics_integration",
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
)

_PAYLOAD_ORDER = (
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
_TIMEFRAME_PERIODS = (
    ("M15", 900),
    ("H1", 3600),
    ("H4", 14400),
    ("D1", 86400),
)
_SAFE_CODE = _re.compile(r"^[A-Z][A-Z0-9_]*$")
_BUNDLE_ID = _re.compile(r"^[A-Za-z0-9._-]{16,64}$")

_READER_STATUS_CODES = frozenset(
    value
    for name, value in vars(_reader).items()
    if name.startswith("CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_")
    and type(value) is str
)
_VALUE_STATUS_CODES = frozenset(
    value
    for name, value in vars(_value).items()
    if name.startswith("CANONICAL_MT4_BUNDLE_V1_") and type(value) is str
)
_GATE_STATUS_CODES = frozenset(
    value
    for name, value in vars(_gate).items()
    if name.startswith("CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_")
    and type(value) is str
    and name
    not in {
        "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STAGE",
        "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_CONTRACT_VERSION",
    }
)

_READER_BLOCKED_REASONS_BY_STATUS = {
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID: frozenset(
        {
            ("ALLOWED_ROOT_INPUT_INVALID",),
            ("BUNDLE_DIRECTORY_INPUT_INVALID",),
        }
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID: frozenset(
        {("FILESYSTEM_POLICY_INVALID",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED: frozenset(
        {("ALLOWED_ROOT_REJECTED",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED: frozenset(
        {("BUNDLE_DIRECTORY_REJECTED",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED: frozenset(
        {("PATH_ESCAPE_BLOCKED",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED: frozenset(
        {("SYMLINK_BLOCKED",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING: frozenset(
        {("FILE_NOT_FOUND",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE: frozenset(
        {("FILE_SIZE_LIMIT_EXCEEDED",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE: frozenset(
        {("FILE_UNREADABLE",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID: frozenset(
        {("UTF8_BOM_REJECTED",), ("UTF8_DECODE_INVALID",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID: frozenset(
        {("JSON_DUPLICATE_KEY",), ("JSON_INVALID",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT: frozenset(
        {("JSON_NOT_OBJECT",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE: frozenset(
        {("MANIFEST_CHANGED_DURING_READ", "MANIFEST_UNSTABLE")}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH: frozenset(
        {("CHECKSUM_MISMATCH",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED: frozenset(
        {("UPSTREAM_VALUE_VALIDATION_BLOCKED",)}
    ),
    _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE: frozenset(
        {("FILESYSTEM_READER_EXCEPTION_SANITIZED",)}
    ),
}

_GATE_BLOCKED_REASON_BY_STATUS = {
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID: frozenset(
        {
            _gate.DATA_QUALITY_INPUT_NOT_OBJECT,
            _gate.DATA_QUALITY_REQUIRED_READER_KEY_MISSING,
            _gate.DATA_QUALITY_UNEXPECTED_READER_KEY,
            _gate.DATA_QUALITY_READER_FIELD_TYPE_INVALID,
            _gate.DATA_QUALITY_COMPONENT_STATUS_INVALID,
        }
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID: frozenset(
        {_gate.DATA_QUALITY_POLICY_INVALID}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED: frozenset(
        {
            _gate.READER_SAFETY_ENVELOPE_INVALID,
            _gate.READER_RESULT_INCONSISTENT,
            _gate.READER_WARNING_CODES_INVALID,
        }
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED: frozenset(
        {_gate.READER_MIXED_GENERATION_BLOCKED}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED: frozenset(
        {_gate.READER_INTEGRITY_INVALID}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED: frozenset(
        {_gate.READER_DATA_STALE}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED: frozenset(
        {_gate.READER_STRUCTURE_INVALID}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED: frozenset(
        {_gate.READER_VALUE_INVALID}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED: frozenset(
        {_gate.READER_BLOCKED}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED: frozenset(
        {_gate.UPSTREAM_WARNINGS_REJECTED_BY_POLICY}
    ),
    _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE: frozenset(
        {_gate.DATA_QUALITY_GATE_EXCEPTION_SANITIZED}
    ),
}

_MANIFEST_KEYS = (
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
)
_COMMON_PAYLOAD_KEYS = (
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
)
_PAYLOAD_KEYS_BY_FILENAME = {
    "live_tick.json": _COMMON_PAYLOAD_KEYS
    + (
        "canonical_symbol",
        "broker_symbol",
        "bid",
        "ask",
        "spread",
        "spread_points",
        "digits",
        "point",
        "tick_time_utc",
    ),
    "latest_bars.json": _COMMON_PAYLOAD_KEYS
    + ("canonical_symbol", "broker_symbol", "timeframes"),
    "symbol_spec.json": _COMMON_PAYLOAD_KEYS
    + (
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
    ),
    "account_snapshot.json": _COMMON_PAYLOAD_KEYS
    + (
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
    ),
}
_TIMEFRAME_KEYS = ("timeframe", "period_seconds", "bar_count", "bars")
_BAR_KEYS = (
    "open_time_utc",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread_points",
)

_read_accepted_attempt = (
    _reader._read_and_validate_canonical_mt4_demo_readonly_bundle_v1_with_accepted_attempt
)
_evaluate_data_quality = (
    _gate.evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate
)


@_dataclass(frozen=True, slots=True)
class _CanonicalBundlePreviousIdentityV1:
    bundle_id: str
    sequence: int


@_dataclass(frozen=True, slots=True)
class _CanonicalGoldMarketFactsSourceAuthorityV1:
    authority_token: object
    allowed_root: _Path
    bundle_dir: _Path
    reference_time_utc: _datetime
    previous_identity: _CanonicalBundlePreviousIdentityV1 | None
    read_policy: _ReadPolicy
    filesystem_policy: _FilesystemPolicy
    data_quality_policy: _DataQualityPolicy
    policy_profile_version: str


@_dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSourceAdapterResultV1:
    contract_version: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    source_available: bool
    source: _CanonicalGoldMarketFactsSourceV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


def build_server_owned_canonical_gold_market_facts_source_v1(
    *,
    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    """Build one bounded, server-owned market-facts source attempt."""

    if not _valid_authority(authority) or not _dependencies_are_available():
        return _blocked(_AUTHORITY_INVALID_STATUS, _AUTHORITY_INVALID)

    authority_snapshot = _authority_snapshot(authority)
    previous_identity = _reader_previous_identity(authority.previous_identity)
    try:
        reader_return = _read_accepted_attempt(
            allowed_root=authority.allowed_root,
            bundle_dir=authority.bundle_dir,
            now_utc=authority.reference_time_utc,
            previous_identity=previous_identity,
            read_policy=authority.read_policy,
            filesystem_policy=authority.filesystem_policy,
        )
    except Exception:
        return _blocked(_SAFE_FAILURE_STATUS, _EXCEPTION_SANITIZED)

    reader_state = _reader_state(reader_return)
    if reader_state is None:
        return _blocked(_SAFE_FAILURE_STATUS, _READER_RESULT_INVALID)
    state, reader_envelope, capsule = reader_state
    if state == "warning":
        return _blocked(_WARNING_BLOCKED_STATUS, _UPSTREAM_WARNING_REJECTED)
    if state == "blocked":
        return _blocked(_READER_BLOCKED_STATUS, _READER_NOT_READY)

    reader_snapshot = _freeze_runtime_value(reader_envelope)
    capsule_snapshot = _capsule_snapshot(capsule)
    if reader_snapshot is None or capsule_snapshot is None:
        return _blocked(_SAFE_FAILURE_STATUS, _READER_RESULT_INVALID)

    try:
        gate_result = _evaluate_data_quality(
            reader_result=reader_envelope,
            policy=authority.data_quality_policy,
        )
    except Exception:
        return _blocked(_SAFE_FAILURE_STATUS, _EXCEPTION_SANITIZED)

    gate_state = _gate_state(
        gate_result,
        reader_status_code=capsule_snapshot.reader_status_code,
        value_status_code=capsule_snapshot.value_status_code,
    )
    if gate_state is None:
        return _blocked(_SAFE_FAILURE_STATUS, _DATA_QUALITY_RESULT_INVALID)
    if gate_state == "blocked":
        return _blocked(_DATA_QUALITY_BLOCKED_STATUS, _DATA_QUALITY_NOT_READY)

    if not _same_attempt_unchanged(
        authority=authority,
        authority_snapshot=authority_snapshot,
        reader_envelope=reader_envelope,
        reader_snapshot=reader_snapshot,
        capsule=capsule,
        capsule_snapshot=capsule_snapshot,
    ):
        return _blocked(_IDENTITY_INVALID_STATUS, _SAME_ATTEMPT_IDENTITY_INVALID)

    try:
        source = _build_source(
            authority=authority,
            reader_envelope=reader_envelope,
            gate_result=gate_result,
            capsule=capsule,
        )
    except _SourceConstructionInvalid:
        return _blocked(_SOURCE_INVALID_STATUS, _CONSTRUCTION_INVALID)
    except Exception:
        return _blocked(_SAFE_FAILURE_STATUS, _EXCEPTION_SANITIZED)

    if type(source) is not _CanonicalGoldMarketFactsSourceV1:
        return _blocked(_SOURCE_INVALID_STATUS, _CONSTRUCTION_INVALID)
    return _ready(source)


@_dataclass(frozen=True, slots=True)
class _CapsuleSnapshot:
    attempt_token: object
    manifest: object
    payloads_by_filename: object
    reader_status_code: str
    value_status_code: str


def _valid_authority(value: object) -> bool:
    try:
        if type(value) is not _CanonicalGoldMarketFactsSourceAuthorityV1:
            return False
        concrete_path_type = type(_Path())
        if value.authority_token is not _AUTHORITY_TOKEN:
            return False
        if type(value.allowed_root) is not concrete_path_type:
            return False
        if type(value.bundle_dir) is not concrete_path_type:
            return False
        if type(value.reference_time_utc) is not _datetime:
            return False
        if value.reference_time_utc.tzinfo is None:
            return False
        if value.reference_time_utc.utcoffset() != _timedelta(0):
            return False
        if not _valid_previous_identity(value.previous_identity):
            return False
        if not _valid_read_policy(value.read_policy):
            return False
        if not _valid_filesystem_policy(value.filesystem_policy):
            return False
        if not _valid_data_quality_policy(value.data_quality_policy):
            return False
        return (
            type(value.policy_profile_version) is str
            and value.policy_profile_version == _POLICY_PROFILE_VERSION
        )
    except Exception:
        return False


def _valid_previous_identity(value: object) -> bool:
    if value is None:
        return True
    return (
        type(value) is _CanonicalBundlePreviousIdentityV1
        and type(value.bundle_id) is str
        and _BUNDLE_ID.fullmatch(value.bundle_id) is not None
        and type(value.sequence) is int
        and value.sequence > 0
    )


def _dependencies_are_available() -> bool:
    return callable(_read_accepted_attempt) and callable(_evaluate_data_quality)


def _valid_read_policy(value: object) -> bool:
    if type(value) is not _ReadPolicy:
        return False
    thresholds = (
        value.writer_heartbeat_max_age_seconds,
        value.live_tick_max_age_seconds,
        value.latest_bars_max_age_seconds,
        value.symbol_spec_max_age_seconds,
        value.account_snapshot_max_age_seconds,
    )
    return all(type(item) is int and item > 0 for item in thresholds) and (
        type(value.max_future_skew_seconds) is int
        and value.max_future_skew_seconds >= 0
    )


def _valid_filesystem_policy(value: object) -> bool:
    if type(value) is not _FilesystemPolicy:
        return False
    size_limits = (
        value.manifest_max_bytes,
        value.live_tick_max_bytes,
        value.latest_bars_max_bytes,
        value.symbol_spec_max_bytes,
        value.account_snapshot_max_bytes,
    )
    return all(type(item) is int and item > 0 for item in size_limits) and (
        type(value.max_manifest_consistency_retries) is int
        and value.max_manifest_consistency_retries == 0
    )


def _valid_data_quality_policy(value: object) -> bool:
    return (
        type(value) is _DataQualityPolicy
        and type(value.allow_upstream_warnings) is bool
    )


def _reader_previous_identity(
    value: _CanonicalBundlePreviousIdentityV1 | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    return {"bundle_id": value.bundle_id, "sequence": value.sequence}


def _authority_snapshot(value: _CanonicalGoldMarketFactsSourceAuthorityV1) -> tuple:
    return (
        value.authority_token,
        value.allowed_root,
        value.bundle_dir,
        value.reference_time_utc,
        _previous_identity_snapshot(value.previous_identity),
        tuple(vars(value.read_policy).items()),
        tuple(vars(value.filesystem_policy).items()),
        tuple(vars(value.data_quality_policy).items()),
        value.policy_profile_version,
    )


def _previous_identity_snapshot(value: object) -> tuple[str, int] | None:
    if value is None:
        return None
    return value.bundle_id, value.sequence


def _reader_state(
    value: object,
) -> tuple[str, dict[str, object], object | None] | None:
    try:
        if type(value) is not tuple or len(value) != 2:
            return None
        envelope, capsule = value
        if not _reader_envelope_shape_is_valid(envelope):
            return None

        passed = envelope["passed"]
        warnings = envelope["warning_codes"]
        if passed:
            if type(capsule) is not _reader._CanonicalMt4DemoReadonlyAcceptedAttemptV1:
                return None
            if not _capsule_shape_is_valid(capsule):
                return None
            if not _reader_success_is_consistent(envelope):
                return None
            if warnings:
                return "warning", envelope, capsule
            return "ready", envelope, capsule

        if capsule is not None or not _reader_blocked_is_consistent(envelope):
            return None
        if warnings:
            return "warning", envelope, None
        return "blocked", envelope, None
    except Exception:
        return None


def _reader_envelope_shape_is_valid(value: object) -> bool:
    if type(value) is not dict or tuple(value) != _READER_RESULT_KEYS:
        return False
    bool_fields = (
        "passed",
        "manifest_consistency_checked",
        "manifest_consistency_passed",
        "checksum_checked",
        "checksum_passed",
        "upstream_value_passed",
        "ready_for_readonly_analysis",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
        "is_trading_permission",
        "is_execution_instruction",
        "allowed_to_call_ea",
        "allowed_to_modify_risk",
    )
    string_fields = (
        "status_code",
        "validation_stage",
        "contract_version",
        "reader_status",
    )
    if any(type(value[field]) is not bool for field in bool_fields):
        return False
    if any(type(value[field]) is not str for field in string_fields):
        return False
    if value["status_code"] not in _READER_STATUS_CODES:
        return False
    if value["validation_stage"] != _reader.VALIDATION_STAGE:
        return False
    if value["contract_version"] != _reader.CONTRACT_VERSION:
        return False
    upstream_status = value["upstream_value_status_code"]
    if upstream_status is not None and (
        type(upstream_status) is not str or upstream_status not in _VALUE_STATUS_CODES
    ):
        return False
    for field in (
        "reason_codes",
        "warning_codes",
        "next_allowed_stage",
        "next_blocked_stage",
    ):
        if not _strict_code_or_stage_list(value[field], codes=field.endswith("codes")):
            return False
    if not _reader_components_are_valid(value["component_statuses"]):
        return False
    return _fixed_safety_flags(value)


def _reader_components_are_valid(value: object) -> bool:
    if type(value) is not list or len(value) != len(_READER_COMPONENT_NAMES):
        return False
    for expected_name, component in zip(_READER_COMPONENT_NAMES, value, strict=True):
        if type(component) is not dict or tuple(component) != _READER_COMPONENT_KEYS:
            return False
        if type(component["component_name"]) is not str:
            return False
        if component["component_name"] != expected_name:
            return False
        if type(component["passed"]) is not bool:
            return False
        if not _strict_code_or_stage_list(component["reason_codes"], codes=True):
            return False
        if any(
            expected_name not in _READER_REASON_COMPONENTS.get(reason, ())
            for reason in component["reason_codes"]
        ):
            return False
        if not _strict_code_or_stage_list(component["warning_codes"], codes=True):
            return False
        if any(
            warning not in _gate.CANONICAL_MT4_BUNDLE_V1_WARNING_CODES
            for warning in component["warning_codes"]
        ):
            return False
        if not _reader_component_status_is_consistent(expected_name, component):
            return False
    return True


def _reader_component_status_is_consistent(
    component_name: str,
    component: dict[str, object],
) -> bool:
    status_code = component["status_code"]
    if type(status_code) is not str:
        return False
    status_prefix = (
        "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_" f"{component_name.upper()}_"
    )
    if component["passed"]:
        allowed_statuses = {status_prefix + "VALID"}
        if component_name == "checksum":
            allowed_statuses.add(status_prefix + "NOT_REQUIRED")
        return not component["reason_codes"] and status_code in allowed_statuses
    if component["reason_codes"]:
        return status_code == status_prefix + "INVALID"
    return status_code == status_prefix + "NOT_CHECKED" and not component[
        "warning_codes"
    ]


def _reader_success_is_consistent(value: dict[str, object]) -> bool:
    component_reasons, component_warnings = _component_codes(
        value["component_statuses"]
    )
    if value["reason_codes"] != list(component_reasons):
        return False
    if value["warning_codes"] != list(component_warnings):
        return False
    if value["reason_codes"]:
        return False
    if not all(component["passed"] for component in value["component_statuses"]):
        return False
    expected_with_warnings = bool(value["warning_codes"])
    expected_status = (
        _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
        if expected_with_warnings
        else _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID
    )
    expected_value_status = (
        _value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
        if expected_with_warnings
        else _value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID
    )
    return (
        value["status_code"] == expected_status
        and value["reader_status"] == "validated_isolated"
        and value["manifest_consistency_checked"] is True
        and value["manifest_consistency_passed"] is True
        and value["checksum_checked"] is True
        and value["checksum_passed"] is True
        and value["upstream_value_passed"] is True
        and value["upstream_value_status_code"] == expected_value_status
        and value["ready_for_readonly_analysis"] is False
        and value["next_allowed_stage"] == list(_READER_NEXT_ALLOWED)
        and value["next_blocked_stage"] == list(_READER_NEXT_BLOCKED)
    )


def _reader_blocked_is_consistent(value: dict[str, object]) -> bool:
    if value["status_code"] in {
        _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
        _reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
    }:
        return False
    component_reasons, component_warnings = _component_codes(
        value["component_statuses"]
    )
    return (
        value["reader_status"] == "blocked"
        and bool(value["reason_codes"])
        and _reader_blocked_status_reason_is_consistent(value)
        and value["reason_codes"] == list(component_reasons)
        and value["warning_codes"] == list(component_warnings)
        and value["ready_for_readonly_analysis"] is False
        and value["next_allowed_stage"] == []
        and value["next_blocked_stage"] == list(_READER_NEXT_BLOCKED)
        and not (
            value["manifest_consistency_passed"]
            and not value["manifest_consistency_checked"]
        )
        and not (value["checksum_passed"] and not value["checksum_checked"])
    )


def _reader_blocked_status_reason_is_consistent(value: dict[str, object]) -> bool:
    allowed_reasons = _READER_BLOCKED_REASONS_BY_STATUS.get(value["status_code"])
    return allowed_reasons is not None and tuple(value["reason_codes"]) in allowed_reasons


def _component_codes(value: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
    reasons: list[str] = []
    warnings: list[str] = []
    for component in value:
        reasons.extend(component["reason_codes"])
        warnings.extend(component["warning_codes"])
    return tuple(reasons), tuple(warnings)


def _strict_code_or_stage_list(value: object, *, codes: bool) -> bool:
    if type(value) is not list:
        return False
    if any(type(item) is not str or not item for item in value):
        return False
    if len(value) != len(set(value)):
        return False
    return not codes or all(_SAFE_CODE.fullmatch(item) is not None for item in value)


def _capsule_shape_is_valid(value: object) -> bool:
    return (
        type(value) is _reader._CanonicalMt4DemoReadonlyAcceptedAttemptV1
        and type(value.attempt_token) is object
        and _json_object_has_exact_keys(value.manifest, _MANIFEST_KEYS)
        and _payloads_are_valid(value.payloads_by_filename)
    )


def _payloads_are_valid(value: object) -> bool:
    if type(value) is not tuple or len(value) != len(_PAYLOAD_ORDER):
        return False
    for expected_name, item in zip(_PAYLOAD_ORDER, value, strict=True):
        if type(item) is not tuple or len(item) != 2:
            return False
        name, payload = item
        if type(name) is not str or name != expected_name:
            return False
        expected_keys = _PAYLOAD_KEYS_BY_FILENAME[expected_name]
        if not _json_object_has_exact_keys(payload, expected_keys):
            return False
        if expected_name == "latest_bars.json" and not _timeframes_are_valid(payload):
            return False
    return True


def _json_object_has_exact_keys(value: object, expected_keys: tuple[str, ...]) -> bool:
    return _is_json_object(value) and tuple(key for key, _ in value) == expected_keys


def _timeframes_are_valid(value: object) -> bool:
    timeframes = _json_object_value(value, "timeframes")
    if type(timeframes) is not tuple:
        return False
    for timeframe in timeframes:
        if not _json_object_has_exact_keys(timeframe, _TIMEFRAME_KEYS):
            return False
        bars = _json_object_value(timeframe, "bars")
        if type(bars) is not tuple or not all(
            _json_object_has_exact_keys(bar, _BAR_KEYS) for bar in bars
        ):
            return False
    return True


def _json_object_value(value: object, field: str) -> object | None:
    if type(value) is not tuple:
        return None
    for name, child in value:
        if name == field:
            return child
    return None


def _is_json_object(value: object) -> bool:
    if type(value) is not tuple:
        return False
    keys: list[str] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            return False
        key, child = item
        if type(key) is not str or not key or key in keys:
            return False
        if not _is_json_value(child):
            return False
        keys.append(key)
    return True


def _is_json_value(value: object) -> bool:
    if value is None or type(value) in {str, int, bool}:
        return True
    if type(value) is float:
        return _math.isfinite(value)
    if type(value) is not tuple:
        return False
    if not value:
        return True
    if all(
        type(item) is tuple and len(item) == 2 and type(item[0]) is str
        for item in value
    ):
        return _is_json_object(value)
    return all(_is_json_value(item) for item in value)


def _capsule_snapshot(value: object) -> _CapsuleSnapshot | None:
    try:
        if not _capsule_shape_is_valid(value):
            return None
        return _CapsuleSnapshot(
            attempt_token=value.attempt_token,
            manifest=value.manifest,
            payloads_by_filename=value.payloads_by_filename,
            reader_status_code=_reader.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
            value_status_code=_value.CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        )
    except Exception:
        return None


def _gate_state(
    value: object,
    *,
    reader_status_code: str,
    value_status_code: str,
) -> str | None:
    try:
        if type(value) is not dict or tuple(value) != _GATE_RESULT_KEYS:
            return None
        bool_fields = (
            "passed",
            "ready_for_readonly_analysis",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        )
        string_fields = (
            "status_code",
            "validation_stage",
            "contract_version",
            "reader_status",
            "data_quality_status",
        )
        if any(type(value[field]) is not bool for field in bool_fields):
            return None
        if any(type(value[field]) is not str for field in string_fields):
            return None
        if value["status_code"] not in _GATE_STATUS_CODES:
            return None
        if value["validation_stage"] != _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STAGE:
            return None
        if value["contract_version"] != _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_CONTRACT_VERSION:
            return None
        if value["source_reader_status_code"] != reader_status_code:
            return None
        if value["source_upstream_value_status_code"] != value_status_code:
            return None
        for field in (
            "reason_codes",
            "warning_codes",
            "next_allowed_stage",
            "next_blocked_stage",
        ):
            if not _strict_code_or_stage_list(
                value[field], codes=field.endswith("codes")
            ):
                return None
        if not _fixed_safety_flags(value):
            return None

        if value["passed"]:
            has_warnings = bool(value["warning_codes"])
            expected_status = (
                _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
                if has_warnings
                else _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
            )
            expected_quality_status = (
                "passed_with_warnings" if has_warnings else "passed"
            )
            if not (
                value["status_code"] == expected_status
                and value["reader_status"] == "validated_isolated"
                and value["data_quality_status"] == expected_quality_status
                and value["reason_codes"] == []
                and value["ready_for_readonly_analysis"] is True
                and value["next_allowed_stage"] == list(_GATE_NEXT_ALLOWED)
                and value["next_blocked_stage"]
                == list(_GATE_SUCCESS_NEXT_BLOCKED)
            ):
                return None
            return "blocked" if has_warnings else "ready"

        if not (
            value["status_code"]
            not in {
                _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
                _gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
            }
            and value["reader_status"] == "blocked"
            and value["data_quality_status"] == "blocked"
            and len(value["reason_codes"]) == 1
            and _gate_blocked_status_reason_is_consistent(value)
            and value["warning_codes"] == []
            and value["ready_for_readonly_analysis"] is False
            and value["next_allowed_stage"] == []
            and value["next_blocked_stage"] == list(_GATE_BLOCKED_NEXT)
        ):
            return None
        return "blocked"
    except Exception:
        return None


def _gate_blocked_status_reason_is_consistent(value: dict[str, object]) -> bool:
    allowed_reasons = _GATE_BLOCKED_REASON_BY_STATUS.get(value["status_code"])
    return allowed_reasons is not None and value["reason_codes"][0] in allowed_reasons


def _same_attempt_unchanged(
    *,
    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,
    authority_snapshot: tuple,
    reader_envelope: object,
    reader_snapshot: object,
    capsule: object,
    capsule_snapshot: _CapsuleSnapshot,
) -> bool:
    try:
        return (
            _authority_snapshot(authority) == authority_snapshot
            and _freeze_runtime_value(reader_envelope) == reader_snapshot
            and type(capsule) is _reader._CanonicalMt4DemoReadonlyAcceptedAttemptV1
            and capsule.attempt_token is capsule_snapshot.attempt_token
            and capsule.manifest == capsule_snapshot.manifest
            and capsule.payloads_by_filename
            == capsule_snapshot.payloads_by_filename
        )
    except Exception:
        return False


def _freeze_runtime_value(value: object) -> object | None:
    if value is None or type(value) in {str, int, float, bool}:
        return (type(value).__name__ if value is not None else "none", value)
    if type(value) is list:
        frozen = tuple(_freeze_runtime_value(item) for item in value)
        return None if any(item is None for item in frozen) else ("list", frozen)
    if type(value) is dict:
        frozen_items = tuple(
            (key, _freeze_runtime_value(child)) for key, child in value.items()
        )
        if any(type(key) is not str or child is None for key, child in frozen_items):
            return None
        return "dict", frozen_items
    return None


def _build_source(
    *,
    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,
    reader_envelope: dict[str, object],
    gate_result: dict[str, object],
    capsule: object,
) -> _CanonicalGoldMarketFactsSourceV1:
    manifest = capsule.manifest
    payloads = _payload_map(capsule.payloads_by_filename)

    bundle_schema_version = _exact_str(_object_field(manifest, "schema_version"))
    bundle_id = _exact_str(_object_field(manifest, "bundle_id"))
    sequence = _exact_int(_object_field(manifest, "sequence"))
    canonical_symbol = _exact_str(_object_field(manifest, "canonical_symbol"))
    broker_symbol = _exact_str(_object_field(manifest, "broker_symbol"))
    if (
        bundle_schema_version != _CONTRACT_VERSION
        or _BUNDLE_ID.fullmatch(bundle_id) is None
        or sequence <= 0
        or canonical_symbol != _CANONICAL_SYMBOL
        or broker_symbol != _BROKER_SYMBOL
    ):
        raise _SourceConstructionInvalid

    live_tick = _build_tick(payloads["live_tick.json"])
    bars_generated_at_utc, timeframes = _build_timeframes(
        payloads["latest_bars.json"]
    )
    symbol_spec = _build_symbol_spec(payloads["symbol_spec.json"])
    upstream = _CanonicalGoldUpstreamEvidenceV1(
        reader_passed=True,
        reader_status_code=_exact_str(reader_envelope["status_code"]),
        value_status_code=_exact_str(
            reader_envelope["upstream_value_status_code"]
        ),
        data_quality_passed=True,
        data_quality_status_code=_exact_str(gate_result["status_code"]),
        ready_for_readonly_analysis=True,
        warning_codes=(),
        same_attempt_identity_bound=True,
    )
    return _CanonicalGoldMarketFactsSourceV1(
        contract_version=_CONTRACT_VERSION,
        bundle_schema_version=bundle_schema_version,
        bundle_id=bundle_id,
        sequence=sequence,
        canonical_symbol=canonical_symbol,
        broker_symbol=broker_symbol,
        reference_time_utc=_format_reference_time(authority.reference_time_utc),
        policy_profile_version=_POLICY_PROFILE_VERSION,
        upstream_evidence=upstream,
        live_tick=live_tick,
        bars_generated_at_utc=bars_generated_at_utc,
        timeframes=timeframes,
        symbol_spec=symbol_spec,
    )


def _payload_map(value: object) -> dict[str, object]:
    if not _payloads_are_valid(value):
        raise _SourceConstructionInvalid
    return {name: payload for name, payload in value}


def _build_tick(value: object) -> _CanonicalGoldTickSourceV1:
    return _CanonicalGoldTickSourceV1(
        bid=_exact_number(_object_field(value, "bid")),
        ask=_exact_number(_object_field(value, "ask")),
        spread=_exact_number(_object_field(value, "spread")),
        spread_points=_exact_int(_object_field(value, "spread_points")),
        digits=_exact_int(_object_field(value, "digits")),
        point=_exact_number(_object_field(value, "point")),
        tick_time_utc=_exact_str(_object_field(value, "tick_time_utc")),
    )


def _build_timeframes(
    value: object,
) -> tuple[str, tuple[_CanonicalGoldTimeframeSourceV1, ...]]:
    generated_at = _exact_str(_object_field(value, "generated_at_utc"))
    raw_timeframes = _exact_tuple(_object_field(value, "timeframes"))
    if len(raw_timeframes) != len(_TIMEFRAME_PERIODS):
        raise _SourceConstructionInvalid
    timeframes: list[_CanonicalGoldTimeframeSourceV1] = []
    for raw_timeframe, (expected_name, expected_period) in zip(
        raw_timeframes,
        _TIMEFRAME_PERIODS,
        strict=True,
    ):
        name = _exact_str(_object_field(raw_timeframe, "timeframe"))
        period = _exact_int(_object_field(raw_timeframe, "period_seconds"))
        if name != expected_name or period != expected_period:
            raise _SourceConstructionInvalid
        raw_bars = _exact_tuple(_object_field(raw_timeframe, "bars"))
        bars = tuple(_build_bar(raw_bar) for raw_bar in raw_bars)
        timeframes.append(
            _CanonicalGoldTimeframeSourceV1(
                timeframe=name,
                period_seconds=period,
                bars=bars,
            )
        )
    return generated_at, tuple(timeframes)


def _build_bar(value: object) -> _CanonicalGoldBarSourceV1:
    return _CanonicalGoldBarSourceV1(
        open_time_utc=_exact_str(_object_field(value, "open_time_utc")),
        open=_exact_number(_object_field(value, "open")),
        high=_exact_number(_object_field(value, "high")),
        low=_exact_number(_object_field(value, "low")),
        close=_exact_number(_object_field(value, "close")),
        tick_volume=_exact_int(_object_field(value, "tick_volume")),
        spread_points=_exact_int(_object_field(value, "spread_points")),
    )


def _build_symbol_spec(value: object) -> _CanonicalGoldSymbolSpecSourceV1:
    return _CanonicalGoldSymbolSpecSourceV1(
        spec_time_utc=_exact_str(_object_field(value, "spec_time_utc")),
        digits=_exact_int(_object_field(value, "digits")),
        point=_exact_number(_object_field(value, "point")),
        tick_size=_exact_number(_object_field(value, "tick_size")),
        tick_value=_exact_number(_object_field(value, "tick_value")),
        contract_size=_exact_number(_object_field(value, "contract_size")),
        min_lot=_exact_number(_object_field(value, "min_lot")),
        lot_step=_exact_number(_object_field(value, "lot_step")),
        max_lot=_exact_number(_object_field(value, "max_lot")),
        base_currency=_exact_str(_object_field(value, "base_currency")),
        profit_currency=_exact_str(_object_field(value, "profit_currency")),
        margin_currency=_exact_str(_object_field(value, "margin_currency")),
        trade_mode_readonly_label=_exact_str(
            _object_field(value, "trade_mode_readonly_label")
        ),
        session_status_readonly_label=_exact_str(
            _object_field(value, "session_status_readonly_label")
        ),
    )


def _object_field(value: object, field: str) -> object:
    if not _is_json_object(value):
        raise _SourceConstructionInvalid
    for name, child in value:
        if name == field:
            return child
    raise _SourceConstructionInvalid


def _exact_tuple(value: object) -> tuple:
    if type(value) is not tuple:
        raise _SourceConstructionInvalid
    return value


def _exact_str(value: object) -> str:
    if type(value) is not str:
        raise _SourceConstructionInvalid
    return value


def _exact_int(value: object) -> int:
    if type(value) is not int:
        raise _SourceConstructionInvalid
    return value


def _exact_number(value: object) -> int | float:
    if type(value) not in {int, float}:
        raise _SourceConstructionInvalid
    if type(value) is float and not _math.isfinite(value):
        raise _SourceConstructionInvalid
    return value


def _format_reference_time(value: _datetime) -> str:
    return value.astimezone(_UTC).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _fixed_safety_flags(value: dict[str, object]) -> bool:
    return (
        value["read_only"] is True
        and value["demo_only"] is True
        and value["is_tradable"] is False
        and value["can_execute"] is False
        and value["is_trading_permission"] is False
        and value["is_execution_instruction"] is False
        and value["allowed_to_call_ea"] is False
        and value["allowed_to_modify_risk"] is False
    )


def _ready(
    source: _CanonicalGoldMarketFactsSourceV1,
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    return CanonicalGoldMarketFactsSourceAdapterResultV1(
        contract_version=_CONTRACT_VERSION,
        passed=True,
        status_code=_READY_STATUS,
        reason_codes=(),
        warning_codes=(),
        source_available=True,
        source=source,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _blocked(
    status_code: str,
    reason_code: str,
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    return CanonicalGoldMarketFactsSourceAdapterResultV1(
        contract_version=_CONTRACT_VERSION,
        passed=False,
        status_code=status_code,
        reason_codes=(reason_code,),
        warning_codes=(),
        source_available=False,
        source=None,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


class _SourceConstructionInvalid(Exception):
    pass
