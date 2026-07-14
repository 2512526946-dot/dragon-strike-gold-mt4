from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from types import MappingProxyType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_market_facts_source_adapter_contract.md"
)
SNAPSHOT_CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_market_facts_snapshot_v1_contract.md"
)
TEST_PATH = Path(__file__).resolve()


@dataclass(frozen=True, slots=True)
class FieldVector:
    field: str
    exact_type: str
    source: str


@dataclass(frozen=True, slots=True)
class CallAccountingVector:
    outcome: str
    reader_calls: tuple[int, ...]
    gate_calls: tuple[int, ...]
    value_validator_calls: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class StatusReasonVector:
    condition: str
    passed: bool
    status_code: str
    reason_code: str | None
    source_available: bool


@dataclass(frozen=True, slots=True)
class InvalidShapeVector:
    name: str
    record: str
    expected_fields: tuple[str, ...]
    observed_fields: tuple[str, ...]
    expected_container: str
    observed_container: str
    accounting_outcome: str
    expected_status: str
    expected_reason: str
    reader_calls: tuple[int, ...]
    gate_calls: tuple[int, ...]
    value_validator_calls: tuple[int, ...]
    source_available: bool
    source_is_none: bool
    accepted: bool


@dataclass(frozen=True, slots=True)
class CallerOverrideVector:
    name: str
    attempted_authority: str
    accounting_outcome: str
    expected_status: str
    expected_reason: str
    reader_calls: tuple[int, ...]
    gate_calls: tuple[int, ...]
    value_validator_calls: tuple[int, ...]
    source_available: bool
    source_is_none: bool
    accepted: bool


AUTHORITY_FIELDS = (
    FieldVector(
        "authority_token",
        "exact built-in `object` identity",
        "Module-private singleton",
    ),
    FieldVector(
        "allowed_root",
        "exact concrete platform path: `pathlib.WindowsPath` on Windows or "
        "`pathlib.PosixPath` on POSIX",
        "Server configuration",
    ),
    FieldVector(
        "bundle_dir",
        "same exact concrete platform path type as `allowed_root`",
        "Server configuration inside allowed root",
    ),
    FieldVector(
        "reference_time_utc",
        "exact `datetime.datetime`",
        "Server-owned aware UTC time",
    ),
    FieldVector(
        "previous_identity",
        "`_CanonicalBundlePreviousIdentityV1` or `None`",
        "Server-owned prior accepted identity",
    ),
    FieldVector(
        "read_policy",
        "exact existing `CanonicalMt4DemoReadonlyBundleV1ReadPolicy`",
        "Server policy",
    ),
    FieldVector(
        "filesystem_policy",
        "exact existing `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy`",
        "Server policy",
    ),
    FieldVector(
        "data_quality_policy",
        "exact existing `CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy`",
        "Server policy",
    ),
    FieldVector(
        "policy_profile_version",
        "exact built-in `str`",
        "Fixed `canonical_gold_market_facts_policy_v1`",
    ),
)

PREVIOUS_IDENTITY_FIELDS = (
    FieldVector("bundle_id", "exact built-in `str`", "Previous accepted identity"),
    FieldVector("sequence", "exact built-in `int`", "Previous accepted identity"),
)

PREVIOUS_IDENTITY_ORACLE = (
    ("bundle_id", "exact built-in `str`", "Previous accepted identity"),
    ("sequence", "exact built-in `int`", "Previous accepted identity"),
)

PUBLIC_INTERFACE_LINES = (
    "@dataclass(frozen=True, slots=True)",
    "class CanonicalGoldMarketFactsSourceAdapterResultV1:",
    "    ...",
    "",
    "def build_server_owned_canonical_gold_market_facts_source_v1(",
    "    *,",
    "    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,",
    ") -> CanonicalGoldMarketFactsSourceAdapterResultV1:",
    "    ...",
)

ACCEPTED_ATTEMPT_FIELDS = (
    FieldVector(
        "attempt_token",
        "exact built-in `object` identity",
        "Fresh reader-owned singleton for one call",
    ),
    FieldVector(
        "manifest",
        "exact `_CanonicalJsonObjectV1`",
        "Accepted manifest from this attempt",
    ),
    FieldVector(
        "payloads_by_filename",
        "exact built-in `tuple[tuple[str, _CanonicalJsonObjectV1], ...]`",
        "Four accepted payloads from this attempt",
    ),
)

RESULT_FIELDS = (
    FieldVector("contract_version", "built-in `str`, exactly `1.0`", "Adapter"),
    FieldVector("passed", "built-in `bool`", "Adapter"),
    FieldVector("status_code", "built-in `str`", "Adapter"),
    FieldVector("reason_codes", "exact built-in `tuple[str, ...]`", "Adapter"),
    FieldVector("warning_codes", "exact built-in `tuple[str, ...]`", "Adapter"),
    FieldVector("source_available", "built-in `bool`", "Adapter"),
    FieldVector(
        "source",
        "exact `CanonicalGoldMarketFactsSourceV1` or `None`",
        "Adapter",
    ),
    FieldVector("read_only", "built-in `bool`", "Fixed safety envelope"),
    FieldVector("demo_only", "built-in `bool`", "Fixed safety envelope"),
    FieldVector("is_tradable", "built-in `bool`", "Fixed safety envelope"),
    FieldVector("can_execute", "built-in `bool`", "Fixed safety envelope"),
    FieldVector(
        "is_trading_permission",
        "built-in `bool`",
        "Fixed safety envelope",
    ),
    FieldVector(
        "is_execution_instruction",
        "built-in `bool`",
        "Fixed safety envelope",
    ),
    FieldVector(
        "allowed_to_call_ea",
        "built-in `bool`",
        "Fixed safety envelope",
    ),
    FieldVector(
        "allowed_to_modify_risk",
        "built-in `bool`",
        "Fixed safety envelope",
    ),
)

SOURCE_PROVENANCE = (
    FieldVector("contract_version", "built-in `str`", "Adapter constant `1.0`"),
    FieldVector(
        "bundle_schema_version",
        "built-in `str`",
        "Adapter projection of accepted capsule `manifest.schema_version`",
    ),
    FieldVector(
        "bundle_id",
        "built-in `str`",
        "Adapter projection of accepted capsule `manifest.bundle_id`",
    ),
    FieldVector(
        "sequence",
        "built-in `int`",
        "Adapter projection of accepted capsule `manifest.sequence`",
    ),
    FieldVector(
        "canonical_symbol",
        "built-in `str`",
        "Adapter projection of accepted capsule `manifest.canonical_symbol`, "
        "required to equal `XAUUSD`",
    ),
    FieldVector(
        "broker_symbol",
        "built-in `str`",
        "Adapter projection of accepted capsule `manifest.broker_symbol`, "
        "required to equal `GOLD` in v1",
    ),
    FieldVector(
        "reference_time_utc",
        "built-in `str`",
        "Authority `reference_time_utc`, converted only by the exact "
        "six-fractional-digit UTC `Z` algorithm in section 5.1",
    ),
    FieldVector(
        "policy_profile_version",
        "built-in `str`",
        "Authority constant `canonical_gold_market_facts_policy_v1`",
    ),
    FieldVector(
        "upstream_evidence",
        "`CanonicalGoldUpstreamEvidenceV1`",
        "Fresh record from the exact reader and Gate envelopes in this call",
    ),
    FieldVector(
        "live_tick",
        "`CanonicalGoldTickSourceV1`",
        "Fresh G175 record projected by the adapter from frozen accepted "
        "`live_tick.json` evidence",
    ),
    FieldVector(
        "bars_generated_at_utc",
        "built-in `str`",
        "Adapter projection of frozen accepted "
        "`latest_bars.json.generated_at_utc` evidence",
    ),
    FieldVector(
        "timeframes",
        "exact tuple of four `CanonicalGoldTimeframeSourceV1`",
        "Fresh G175 records projected by the adapter from frozen accepted "
        "`latest_bars.json.timeframes` evidence",
    ),
    FieldVector(
        "symbol_spec",
        "`CanonicalGoldSymbolSpecSourceV1`",
        "Fresh G175 record projected by the adapter from frozen accepted "
        "`symbol_spec.json` evidence",
    ),
)

UPSTREAM_PROVENANCE = (
    FieldVector(
        "reader_passed",
        "built-in `bool`",
        "Exact reader envelope `passed`, required true",
    ),
    FieldVector(
        "reader_status_code",
        "built-in `str`",
        "Exact reader envelope status, required "
        "`CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID`",
    ),
    FieldVector(
        "value_status_code",
        "built-in `str`",
        "Exact reader upstream value status, required "
        "`CANONICAL_MT4_BUNDLE_V1_VALUE_VALID`",
    ),
    FieldVector(
        "data_quality_passed",
        "built-in `bool`",
        "Exact Gate envelope `passed`, required true",
    ),
    FieldVector(
        "data_quality_status_code",
        "built-in `str`",
        "Exact Gate status, required "
        "`CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED`",
    ),
    FieldVector(
        "ready_for_readonly_analysis",
        "built-in `bool`",
        "Exact Gate readiness, required true",
    ),
    FieldVector(
        "warning_codes",
        "exact built-in `tuple[str, ...]`",
        "Exact empty built-in tuple after both envelopes prove empty warnings",
    ),
    FieldVector(
        "same_attempt_identity_bound",
        "built-in `bool`",
        "True only after all same-stack identity checks pass",
    ),
)

NESTED_SOURCE_FIELDS = MappingProxyType(
    {
        "CanonicalGoldTickSourceV1": (
            FieldVector(
                "bid",
                "built-in `int` or built-in `float`",
                "accepted `live_tick.json.bid`",
            ),
            FieldVector(
                "ask",
                "built-in `int` or built-in `float`",
                "accepted `live_tick.json.ask`",
            ),
            FieldVector(
                "spread",
                "built-in `int` or built-in `float`",
                "accepted `live_tick.json.spread`",
            ),
            FieldVector(
                "spread_points",
                "built-in `int`",
                "accepted `live_tick.json.spread_points`",
            ),
            FieldVector(
                "digits",
                "built-in `int`",
                "accepted `live_tick.json.digits`",
            ),
            FieldVector(
                "point",
                "built-in `int` or built-in `float`",
                "accepted `live_tick.json.point`",
            ),
            FieldVector(
                "tick_time_utc",
                "built-in `str`",
                "accepted `live_tick.json.tick_time_utc`",
            ),
        ),
        "CanonicalGoldTimeframeSourceV1": (
            FieldVector(
                "timeframe",
                "built-in `str`",
                "accepted `latest_bars.json.timeframes[*].timeframe`",
            ),
            FieldVector(
                "period_seconds",
                "built-in `int`",
                "accepted `latest_bars.json.timeframes[*].period_seconds`",
            ),
            FieldVector(
                "bars",
                "exact built-in `tuple[CanonicalGoldBarSourceV1, ...]`",
                "accepted `latest_bars.json.timeframes[*].bars`",
            ),
        ),
        "CanonicalGoldBarSourceV1": (
            FieldVector(
                "open_time_utc",
                "built-in `str`",
                "accepted `latest_bars.json.timeframes[*].bars[*].open_time_utc`",
            ),
            FieldVector(
                "open",
                "built-in `int` or built-in `float`",
                "accepted `latest_bars.json.timeframes[*].bars[*].open`",
            ),
            FieldVector(
                "high",
                "built-in `int` or built-in `float`",
                "accepted `latest_bars.json.timeframes[*].bars[*].high`",
            ),
            FieldVector(
                "low",
                "built-in `int` or built-in `float`",
                "accepted `latest_bars.json.timeframes[*].bars[*].low`",
            ),
            FieldVector(
                "close",
                "built-in `int` or built-in `float`",
                "accepted `latest_bars.json.timeframes[*].bars[*].close`",
            ),
            FieldVector(
                "tick_volume",
                "built-in `int`",
                "accepted `latest_bars.json.timeframes[*].bars[*].tick_volume`",
            ),
            FieldVector(
                "spread_points",
                "built-in `int`",
                "accepted `latest_bars.json.timeframes[*].bars[*].spread_points`",
            ),
        ),
        "CanonicalGoldSymbolSpecSourceV1": (
            FieldVector(
                "spec_time_utc",
                "built-in `str`",
                "accepted `symbol_spec.json.spec_time_utc`",
            ),
            FieldVector(
                "digits",
                "built-in `int`",
                "accepted `symbol_spec.json.digits`",
            ),
            FieldVector(
                "point",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.point`",
            ),
            FieldVector(
                "tick_size",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.tick_size`",
            ),
            FieldVector(
                "tick_value",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.tick_value`",
            ),
            FieldVector(
                "contract_size",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.contract_size`",
            ),
            FieldVector(
                "min_lot",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.min_lot`",
            ),
            FieldVector(
                "lot_step",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.lot_step`",
            ),
            FieldVector(
                "max_lot",
                "built-in `int` or built-in `float`",
                "accepted `symbol_spec.json.max_lot`",
            ),
            FieldVector(
                "base_currency",
                "built-in `str`",
                "accepted `symbol_spec.json.base_currency`",
            ),
            FieldVector(
                "profit_currency",
                "built-in `str`",
                "accepted `symbol_spec.json.profit_currency`",
            ),
            FieldVector(
                "margin_currency",
                "built-in `str`",
                "accepted `symbol_spec.json.margin_currency`",
            ),
            FieldVector(
                "trade_mode_readonly_label",
                "built-in `str`",
                "accepted `symbol_spec.json.trade_mode_readonly_label`",
            ),
            FieldVector(
                "session_status_readonly_label",
                "built-in `str`",
                "accepted `symbol_spec.json.session_status_readonly_label`",
            ),
        ),
    }
)

IMMUTABLE_JSON_ALIAS_ORACLE = (
    "_CanonicalJsonScalarV1 = exact built-in str | int | float | bool | None",
    "_CanonicalJsonObjectV1 = exact built-in "
    "tuple[tuple[str, _CanonicalJsonValueV1], ...]",
    "_CanonicalJsonArrayV1 = exact built-in tuple[_CanonicalJsonValueV1, ...]",
    "_CanonicalJsonValueV1 = _CanonicalJsonScalarV1 | "
    "_CanonicalJsonObjectV1 | _CanonicalJsonArrayV1",
)
IMMUTABLE_JSON_ALIASES = tuple(IMMUTABLE_JSON_ALIAS_ORACLE)

PAYLOAD_ORDER = (
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
TIMEFRAME_ORDER = ("M15", "H1", "H4", "D1")

CALL_ACCOUNTING = (
    CallAccountingVector(
        "Authority invalid or dependency unavailable before reader call",
        (0,),
        (0,),
        (0,),
    ),
    CallAccountingVector("Reader blocks before value validation", (1,), (0,), (0,)),
    CallAccountingVector("Reader blocks at value validation", (1,), (0,), (1,)),
    CallAccountingVector("Reader exception", (1,), (0,), (0, 1)),
    CallAccountingVector(
        "Invalid reader envelope or capsule return",
        (1,),
        (0,),
        (0, 1),
    ),
    CallAccountingVector("Reader warning rejected", (1,), (0,), (1,)),
    CallAccountingVector("Gate blocked", (1,), (1,), (1,)),
    CallAccountingVector("Invalid Gate envelope", (1,), (1,), (1,)),
    CallAccountingVector("Gate exception", (1,), (1,), (1,)),
    CallAccountingVector(
        "Same-attempt identity or source construction invalid",
        (1,),
        (1,),
        (1,),
    ),
    CallAccountingVector("Ready", (1,), (1,), (1,)),
)

STATUS_REASON_VECTORS = (
    StatusReasonVector(
        "Exact successful source construction",
        True,
        "CANONICAL_GOLD_SOURCE_ADAPTER_READY",
        None,
        True,
    ),
    StatusReasonVector(
        "Authority capsule, token, policy, time, or dependency invalid before reader call",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        False,
    ),
    StatusReasonVector(
        "Reader returned an exact internally consistent blocked envelope and no capsule",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_READER_BLOCKED",
        "GOLD_SOURCE_READER_NOT_READY",
        False,
    ),
    StatusReasonVector(
        "Reader return fails exact envelope/capsule pairing, type, field, or consistency checks, including a passed envelope without one capsule or a blocked envelope with a capsule",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_READER_RESULT_INVALID",
        False,
    ),
    StatusReasonVector(
        "Reader returned any warning",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_WARNING_BLOCKED",
        "GOLD_SOURCE_UPSTREAM_WARNING_REJECTED",
        False,
    ),
    StatusReasonVector(
        "Gate blocked or was not exactly ready",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_DATA_QUALITY_BLOCKED",
        "GOLD_SOURCE_DATA_QUALITY_NOT_READY",
        False,
    ),
    StatusReasonVector(
        "Gate return fails exact envelope, type, field, or consistency checks",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
        False,
    ),
    StatusReasonVector(
        "Attempt capsule, identity binding, or post-call drift invalid",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
        "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
        False,
    ),
    StatusReasonVector(
        "Exact source type or construction consistency invalid",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID",
        "GOLD_SOURCE_CONSTRUCTION_INVALID",
        False,
    ),
    StatusReasonVector(
        "Unexpected reader, Gate, mapping, or boundary exception",
        False,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_EXCEPTION_SANITIZED",
        False,
    ),
)

SAFETY_FLAGS = MappingProxyType(
    {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
)

AUTHORITY_OVERRIDES = (
    CallerOverrideVector(
        "path_override",
        "allowed root or bundle directory",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "clock_override",
        "reference time or clock",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "identity_override",
        "previous bundle identity",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "policy_override",
        "filesystem, freshness, future-skew, or DataQualityGate policy",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "profile_override",
        "policy-profile version",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "symbol_override",
        "canonical or broker symbol mapping",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "dependency_override",
        "reader, validator, Gate, adapter, or fallback dependency",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    CallerOverrideVector(
        "oracle_override",
        "expected result, status, reason, or oracle",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
)

AUTHORITY_FIELD_NAMES = tuple(vector.field for vector in AUTHORITY_FIELDS)
ACCEPTED_FIELD_NAMES = tuple(vector.field for vector in ACCEPTED_ATTEMPT_FIELDS)
SOURCE_FIELD_NAMES = tuple(vector.field for vector in SOURCE_PROVENANCE)

INVALID_SHAPE_VECTORS = (
    InvalidShapeVector(
        "missing_authority_field",
        "authority",
        AUTHORITY_FIELD_NAMES,
        AUTHORITY_FIELD_NAMES[:-1],
        "tuple",
        "tuple",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "extra_reader_envelope_field",
        "reader_envelope",
        ("passed", "status_code", "reason_codes", "warning_codes"),
        ("passed", "status_code", "reason_codes", "warning_codes", "path"),
        "tuple",
        "tuple",
        "Invalid reader envelope or capsule return",
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_READER_RESULT_INVALID",
        (1,),
        (0,),
        (0, 1),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "reordered_gate_envelope",
        "gate_envelope",
        ("passed", "status_code", "reason_codes", "warning_codes"),
        ("status_code", "passed", "reason_codes", "warning_codes"),
        "tuple",
        "tuple",
        "Invalid Gate envelope",
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
        (1,),
        (1,),
        (1,),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "duplicate_source_field",
        "source",
        SOURCE_FIELD_NAMES,
        SOURCE_FIELD_NAMES + ("bundle_id",),
        "tuple",
        "tuple",
        "Same-attempt identity or source construction invalid",
        "CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID",
        "GOLD_SOURCE_CONSTRUCTION_INVALID",
        (1,),
        (1,),
        (1,),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "aliased_capsule_field",
        "accepted_attempt",
        ACCEPTED_FIELD_NAMES,
        ("attempt_token", "manifest_alias", "payloads_by_filename"),
        "tuple",
        "tuple",
        "Invalid reader envelope or capsule return",
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_READER_RESULT_INVALID",
        (1,),
        (0,),
        (0, 1),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "case_changed_gate_field",
        "gate_envelope",
        ("passed", "status_code", "reason_codes", "warning_codes"),
        ("Passed", "status_code", "reason_codes", "warning_codes"),
        "tuple",
        "tuple",
        "Invalid Gate envelope",
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
        (1,),
        (1,),
        (1,),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "subclassed_authority",
        "authority",
        AUTHORITY_FIELD_NAMES,
        AUTHORITY_FIELD_NAMES,
        "exact authority dataclass",
        "authority subclass",
        "Authority invalid or dependency unavailable before reader call",
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
        (0,),
        (0,),
        (0,),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "wrong_container_payloads",
        "accepted_attempt.payloads_by_filename",
        PAYLOAD_ORDER,
        PAYLOAD_ORDER,
        "tuple",
        "list",
        "Invalid reader envelope or capsule return",
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_READER_RESULT_INVALID",
        (1,),
        (0,),
        (0, 1),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "mixed_attempt_token",
        "same_attempt",
        ("reader_token", "gate_reader_object", "post_call_token"),
        ("reader_token", "different_reader_object", "different_token"),
        "identity tuple",
        "identity tuple",
        "Same-attempt identity or source construction invalid",
        "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
        "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
        (1,),
        (1,),
        (1,),
        False,
        True,
        False,
    ),
    InvalidShapeVector(
        "post_call_mutation",
        "same_attempt",
        ("frozen_authority", "frozen_reader", "frozen_capsule"),
        ("frozen_authority", "mutated_reader", "frozen_capsule"),
        "identity tuple",
        "identity tuple",
        "Same-attempt identity or source construction invalid",
        "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
        "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
        (1,),
        (1,),
        (1,),
        False,
        True,
        False,
    ),
)

INVALID_SHAPE_ORACLE = MappingProxyType(
    {
        "missing_authority_field": (
            "authority",
            AUTHORITY_FIELD_NAMES,
            AUTHORITY_FIELD_NAMES[:-1],
            "tuple",
            "tuple",
            "Authority invalid or dependency unavailable before reader call",
            "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
            "GOLD_SOURCE_AUTHORITY_INVALID",
            (0,),
            (0,),
            (0,),
            False,
            True,
            False,
        ),
        "extra_reader_envelope_field": (
            "reader_envelope",
            ("passed", "status_code", "reason_codes", "warning_codes"),
            ("passed", "status_code", "reason_codes", "warning_codes", "path"),
            "tuple",
            "tuple",
            "Invalid reader envelope or capsule return",
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
            (1,),
            (0,),
            (0, 1),
            False,
            True,
            False,
        ),
        "reordered_gate_envelope": (
            "gate_envelope",
            ("passed", "status_code", "reason_codes", "warning_codes"),
            ("status_code", "passed", "reason_codes", "warning_codes"),
            "tuple",
            "tuple",
            "Invalid Gate envelope",
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
            (1,),
            (1,),
            (1,),
            False,
            True,
            False,
        ),
        "duplicate_source_field": (
            "source",
            SOURCE_FIELD_NAMES,
            SOURCE_FIELD_NAMES + ("bundle_id",),
            "tuple",
            "tuple",
            "Same-attempt identity or source construction invalid",
            "CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID",
            "GOLD_SOURCE_CONSTRUCTION_INVALID",
            (1,),
            (1,),
            (1,),
            False,
            True,
            False,
        ),
        "aliased_capsule_field": (
            "accepted_attempt",
            ACCEPTED_FIELD_NAMES,
            ("attempt_token", "manifest_alias", "payloads_by_filename"),
            "tuple",
            "tuple",
            "Invalid reader envelope or capsule return",
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
            (1,),
            (0,),
            (0, 1),
            False,
            True,
            False,
        ),
        "case_changed_gate_field": (
            "gate_envelope",
            ("passed", "status_code", "reason_codes", "warning_codes"),
            ("Passed", "status_code", "reason_codes", "warning_codes"),
            "tuple",
            "tuple",
            "Invalid Gate envelope",
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
            (1,),
            (1,),
            (1,),
            False,
            True,
            False,
        ),
        "subclassed_authority": (
            "authority",
            AUTHORITY_FIELD_NAMES,
            AUTHORITY_FIELD_NAMES,
            "exact authority dataclass",
            "authority subclass",
            "Authority invalid or dependency unavailable before reader call",
            "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
            "GOLD_SOURCE_AUTHORITY_INVALID",
            (0,),
            (0,),
            (0,),
            False,
            True,
            False,
        ),
        "wrong_container_payloads": (
            "accepted_attempt.payloads_by_filename",
            PAYLOAD_ORDER,
            PAYLOAD_ORDER,
            "tuple",
            "list",
            "Invalid reader envelope or capsule return",
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
            (1,),
            (0,),
            (0, 1),
            False,
            True,
            False,
        ),
        "mixed_attempt_token": (
            "same_attempt",
            ("reader_token", "gate_reader_object", "post_call_token"),
            ("reader_token", "different_reader_object", "different_token"),
            "identity tuple",
            "identity tuple",
            "Same-attempt identity or source construction invalid",
            "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
            "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
            (1,),
            (1,),
            (1,),
            False,
            True,
            False,
        ),
        "post_call_mutation": (
            "same_attempt",
            ("frozen_authority", "frozen_reader", "frozen_capsule"),
            ("frozen_authority", "mutated_reader", "frozen_capsule"),
            "identity tuple",
            "identity tuple",
            "Same-attempt identity or source construction invalid",
            "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
            "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
            (1,),
            (1,),
            (1,),
            False,
            True,
            False,
        ),
    }
)

_AUTHORITY_OVERRIDE_RESULT = (
    "Authority invalid or dependency unavailable before reader call",
    "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
    "GOLD_SOURCE_AUTHORITY_INVALID",
    (0,),
    (0,),
    (0,),
    False,
    True,
    False,
)

AUTHORITY_OVERRIDE_ORACLE = MappingProxyType(
    {
        "path_override": (
            "allowed root or bundle directory",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
        "clock_override": ("reference time or clock", *_AUTHORITY_OVERRIDE_RESULT),
        "identity_override": (
            "previous bundle identity",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
        "policy_override": (
            "filesystem, freshness, future-skew, or DataQualityGate policy",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
        "profile_override": (
            "policy-profile version",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
        "symbol_override": (
            "canonical or broker symbol mapping",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
        "dependency_override": (
            "reader, validator, Gate, adapter, or fallback dependency",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
        "oracle_override": (
            "expected result, status, reason, or oracle",
            *_AUTHORITY_OVERRIDE_RESULT,
        ),
    }
)

SENSITIVE_TERMS = (
    "filesystem path",
    "raw payload",
    "digest",
    "checksum",
    "account fact",
    "exception text",
    "traceback",
    "internal attempt token",
    "source status detail",
    "policy object",
    "dependency",
    "strategy",
    "risk decision",
    "order",
    "execution field",
)

FAIL_CLOSED_CONDITIONS = (
    "missing, extra, reordered, subclassed, aliased, or wrong-container authority, reader, Gate, capsule, source, or result fields;",
    "authority token mismatch or non-server-owned configuration;",
    "path, time, policy, dependency, symbol mapping, or oracle override;",
    "reader or Gate dependency unavailable before its permitted call;",
    "reader/Gate status, reason, warning, readiness, component, or safety-envelope inconsistency;",
    "no accepted-attempt capsule, an extra capsule, or a capsule from another call;",
    "a manifest/payload identity mismatch reported by W1, warning, mixed attempt, polluted evidence, post-call mutation, or ambiguous provenance;",
    "account, path, payload, checksum, exception, or internal state entering a source or result;",
    "source construction mismatch or any unexpected exception.",
)

FORBIDDEN_BEHAVIORS = (
    "copy or reimplement G148 reader, W1 validators, G149 Gate, G151 adapter, G153 pipeline, G170/G171 summary validator, or G178 projector logic;",
    "expose or persist the private capsule or authority object;",
    "call a public diagnostics endpoint or use a diagnostics result as facts;",
    "read environment variables, ambient clock, settings, network, database, cache, frontend state, or runtime data outside the approved reader call;",
    "retry, fallback, reread, sort, round, repair, infer, switch source, or call a second dependency;",
    "return a partial source; or",
    "call the projector, ReplayRunner, API, MT4, EA, order, execution, or trading component.",
)

STAGED_DELIVERY = (
    "immutable tests-only contract vectors for this adapter boundary;",
    "private accepted-attempt reader seam and source-adapter production types;",
    "bounded adapter behavior using the existing reader, value validator, and DataQualityGate;",
    "offline canonical-fixture integration evidence;",
    "deterministic non-activating verification;",
    "separate contracts and vectors for remaining W6 facts and features; and",
    "a separately versioned ReplayRunner W6 stage before W7.",
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _snapshot_contract_text() -> str:
    return SNAPSHOT_CONTRACT_PATH.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _markdown_tables(
    text: str,
    start: str,
    end: str,
) -> tuple[tuple[tuple[str, ...], tuple[tuple[str, ...], ...]], ...]:
    table_groups: list[list[str]] = []
    current_group: list[str] = []
    for line in _section(text, start, end).splitlines():
        if line.startswith("|"):
            current_group.append(line)
        elif current_group:
            table_groups.append(current_group)
            current_group = []
    if current_group:
        table_groups.append(current_group)

    parsed_tables = []
    for lines in table_groups:
        assert len(lines) >= 2
        rows = tuple(
            tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            for line in lines
        )
        assert all(len(row) == len(rows[0]) for row in rows)
        assert all(
            cell and set(cell.replace(" ", "")) <= {"-", ":"}
            for cell in rows[1]
        )
        parsed_tables.append((rows[0], rows[2:]))
    return tuple(parsed_tables)


def _markdown_table(
    text: str,
    start: str,
    end: str,
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    tables = _markdown_tables(text, start, end)
    assert len(tables) == 1
    return tables[0]


def _bullet_items(text: str, start: str, end: str) -> tuple[str, ...]:
    items: list[str] = []
    current = ""
    for line in _section(text, start, end).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            if current:
                items.append(_normalize_whitespace(current))
            current = stripped[2:]
        elif current and stripped:
            current += " " + stripped
    if current:
        items.append(_normalize_whitespace(current))
    return tuple(items)


def _fenced_block_lines(
    text: str,
    start: str,
    end: str,
    *,
    language: str,
) -> tuple[str, ...]:
    section = _section(text, start, end)
    opening = f"```{language}\n"
    block_start = section.index(opening) + len(opening)
    block_end = section.index("\n```", block_start)
    return tuple(section[block_start:block_end].splitlines())


def _numbered_items(text: str, start: str, end: str) -> tuple[str, ...]:
    items: list[str] = []
    ordinals: list[int] = []
    current = ""
    for line in _section(text, start, end).splitlines():
        stripped = line.strip()
        marker, separator, content = stripped.partition(". ")
        if separator and marker.isascii() and marker.isdigit():
            if current:
                items.append(_normalize_whitespace(current))
            ordinals.append(int(marker))
            current = content
        elif current and stripped:
            current += " " + stripped
    if current:
        items.append(_normalize_whitespace(current))
    assert tuple(ordinals) == tuple(range(1, len(items) + 1))
    return tuple(items)


def _field_table(
    header: tuple[str, ...],
    vectors: tuple[FieldVector, ...],
    *,
    include_source: bool,
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    rows = tuple(
        (
            str(index),
            f"`{vector.field}`",
            vector.exact_type,
            *((vector.source,) if include_source else ()),
        )
        for index, vector in enumerate(vectors, start=1)
    )
    return header, rows


def _oxford_backticks(fields: tuple[FieldVector, ...]) -> str:
    names = tuple(f"`{vector.field}`" for vector in fields)
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def _call_cell(values: tuple[int, ...]) -> str:
    if values == (0, 1):
        return "0 or 1, as reached internally"
    return " or ".join(str(value) for value in values)


def test_vectors_are_immutable_and_have_exact_counts() -> None:
    assert len(AUTHORITY_FIELDS) == 9
    assert len(PREVIOUS_IDENTITY_FIELDS) == 2
    assert tuple(
        (vector.field, vector.exact_type, vector.source)
        for vector in PREVIOUS_IDENTITY_FIELDS
    ) == PREVIOUS_IDENTITY_ORACLE
    assert len(ACCEPTED_ATTEMPT_FIELDS) == 3
    assert len(RESULT_FIELDS) == 15
    assert len(SOURCE_PROVENANCE) == 13
    assert len(UPSTREAM_PROVENANCE) == 8
    assert len(CALL_ACCOUNTING) == 11
    assert len(STATUS_REASON_VECTORS) == 10
    assert len(SAFETY_FLAGS) == 8
    assert len(AUTHORITY_OVERRIDES) == 8
    assert len(INVALID_SHAPE_VECTORS) == 10
    assert len(IMMUTABLE_JSON_ALIASES) == 4
    assert IMMUTABLE_JSON_ALIASES == IMMUTABLE_JSON_ALIAS_ORACLE
    assert len(STAGED_DELIVERY) == 7
    assert tuple(len(fields) for fields in NESTED_SOURCE_FIELDS.values()) == (
        7,
        3,
        7,
        14,
    )

    assert type(AUTHORITY_FIELDS) is tuple
    assert type(PREVIOUS_IDENTITY_FIELDS) is tuple
    assert type(IMMUTABLE_JSON_ALIASES) is tuple
    assert type(STAGED_DELIVERY) is tuple
    assert type(NESTED_SOURCE_FIELDS) is MappingProxyType
    assert type(SAFETY_FLAGS) is MappingProxyType
    with pytest.raises(FrozenInstanceError):
        AUTHORITY_FIELDS[0].field = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        SAFETY_FLAGS["read_only"] = False  # type: ignore[index]


def test_contract_locks_internal_interface_and_authority_ownership() -> None:
    text = _contract_text()
    assert "Status: CONTRACT_ONLY" in text
    assert "Scope: W6 server-owned same-attempt source authority" in text
    assert "Contract version: 1.0" in text
    assert "Default posture: Demo-only, Read-only, fail-closed" in text
    assert (
        "backend/app/services/canonical_gold_market_facts_source_adapter.py"
        in text
    )
    assert _fenced_block_lines(
        text,
        "It may expose exactly these production names:",
        "`_CanonicalGoldMarketFactsSourceAuthorityV1` and every accepted-attempt type",
        language="python",
    ) == PUBLIC_INTERFACE_LINES
    assert "are private. They must not be exported through `__all__`" in text
    assert "The function must reject a subclassed or look-alike authority object." in text
    assert "Only an approved server integration may create the private authority capsule." in text
    assert "The canonical filesystem reader owns the accepted-attempt capsule." in text
    assert "W1 does not\nimport the W6 adapter" in text
    assert "Only the W6 adapter performs the one-way projection" in text


def test_exact_authority_attempt_and_result_tables_match_contract() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    assert _markdown_table(text, "### 5.1 Authority capsule", "### 5.2") == (
        _field_table(
            ("Order", "Field", "Exact type", "Authority"),
            AUTHORITY_FIELDS,
            include_source=True,
        )
    )
    assert _markdown_table(text, "### 5.2 Accepted-attempt capsule", "### 5.3") == (
        _field_table(
            ("Order", "Field", "Exact type", "Source"),
            ACCEPTED_ATTEMPT_FIELDS,
            include_source=True,
        )
    )
    assert _markdown_table(text, "### 5.3 Adapter result", "## 6.") == _field_table(
        ("Order", "Field", "Exact type"),
        RESULT_FIELDS,
        include_source=False,
    )
    assert tuple(
        (vector.field, vector.exact_type, vector.source)
        for vector in PREVIOUS_IDENTITY_FIELDS
    ) == PREVIOUS_IDENTITY_ORACLE
    assert (
        "`_CanonicalBundlePreviousIdentityV1` is frozen and slotted with exact "
        "built-in\n`str bundle_id` followed by exact built-in `int sequence`."
        in text
    )
    assert "`max_manifest_consistency_retries` to exact built-in integer\nzero" in text
    assert "Built-in strings, `PurePath`, the factory `Path` class itself" in normalized
    assert "a concrete-path subclass, a wrong-platform path" in normalized
    assert (
        "On success, `source_available` is true and `source` is exact type "
        "`CanonicalGoldMarketFactsSourceV1`. On every non-passed result, "
        "`source_available` is false and `source` is `None`."
        in normalized
    )
    assert (
        "No result may contain a path, filename, raw payload, digest, checksum, "
        "account fact, exception text, traceback, internal attempt token, source "
        "status detail, policy object, dependency, strategy, risk decision, order, "
        "or execution field."
        in normalized
    )


def test_datetime_json_payload_and_same_attempt_rules_are_exact() -> None:
    text = _contract_text()
    utc_algorithm = (
        "reference_time_utc.astimezone(datetime.UTC).isoformat(\n"
        "    timespec=\"microseconds\"\n"
        ").replace(\"+00:00\", \"Z\")"
    )
    assert utc_algorithm in text
    assert "six fractional digits and terminal `Z`" in text
    assert "The replacement must occur exactly once at the terminal suffix." in text
    assert IMMUTABLE_JSON_ALIASES == IMMUTABLE_JSON_ALIAS_ORACLE
    assert _fenced_block_lines(
        text,
        "The W1 reader owns these private recursive immutable JSON aliases:",
        "Every object member is an exact built-in two-item tuple",
        language="text",
    ) == IMMUTABLE_JSON_ALIAS_ORACLE
    assert (
        "`payloads_by_filename` has exactly four exact built-in two-item tuples "
        "in this\norder: `live_tick.json`, `latest_bars.json`, "
        "`symbol_spec.json`, then\n`account_snapshot.json`."
        in text
    )
    assert PAYLOAD_ORDER == (
        "live_tick.json",
        "latest_bars.json",
        "symbol_spec.json",
        "account_snapshot.json",
    )
    assert "(reader_envelope, accepted_attempt_or_none)" in text
    assert "same capsule returned atomically with the reader envelope" in text
    assert "same reader-envelope object supplied to the Gate" in text
    assert "checks remain exclusively inside W1" in text


def test_call_accounting_and_no_retry_rules_match_exactly() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    expected_table = (
        ("Outcome", "Reader calls", "Gate calls", "Value-validator calls"),
        tuple(
            (
                vector.outcome,
                _call_cell(vector.reader_calls),
                _call_cell(vector.gate_calls),
                _call_cell(vector.value_validator_calls),
            )
            for vector in CALL_ACCOUNTING
        ),
    )
    assert _markdown_table(text, "### 6.1 Call accounting", "## 7.") == (
        expected_table
    )
    assert CALL_ACCOUNTING[0].reader_calls == (0,)
    assert CALL_ACCOUNTING[-1].reader_calls == (1,)
    assert CALL_ACCOUNTING[-1].gate_calls == (1,)
    assert CALL_ACCOUNTING[-1].value_validator_calls == (1,)
    assert "An exception after a call begins consumes that call." in text
    assert "No outcome permits a\nretry or second invocation." in text
    assert "The adapter never calls the value validator directly." in normalized
    assert "Do not call the public reader in addition." in normalized


def test_source_and_nested_provenance_is_complete_and_ordered() -> None:
    text = _contract_text()
    snapshot_text = _snapshot_contract_text()
    normalized = _normalize_whitespace(text)
    assert _markdown_table(text, "### 7.1 Top-level 13 fields", "### 7.2") == (
        (
            ("Order", "G175 source field", "Exact source"),
            tuple(
                (str(index), f"`{vector.field}`", vector.source)
                for index, vector in enumerate(SOURCE_PROVENANCE, start=1)
            ),
        )
    )
    assert _markdown_table(text, "### 7.2 Upstream evidence", "### 7.3") == (
        (
            ("Order", "Field", "Exact source or value"),
            tuple(
                (str(index), f"`{vector.field}`", vector.source)
                for index, vector in enumerate(UPSTREAM_PROVENANCE, start=1)
            ),
        )
    )

    source_type_table = _markdown_table(
        snapshot_text,
        "## 6. Source Type",
        "### 6.1 Upstream evidence",
    )
    assert source_type_table[0] == ("Order", "Field", "Exact type", "Authority")
    assert tuple(row[:3] for row in source_type_table[1]) == _field_table(
        ("Order", "Field", "Exact type"),
        SOURCE_PROVENANCE,
        include_source=False,
    )[1]
    assert len(source_type_table[1]) == len(SOURCE_PROVENANCE)

    upstream_type_table = _markdown_table(
        snapshot_text,
        "### 6.1 Upstream evidence",
        "### 6.2 Tick source",
    )
    assert upstream_type_table[0] == (
        "Order",
        "Field",
        "Exact type",
        "Exact value or rule",
    )
    assert tuple(row[:3] for row in upstream_type_table[1]) == _field_table(
        ("Order", "Field", "Exact type"),
        UPSTREAM_PROVENANCE,
        include_source=False,
    )[1]
    assert len(upstream_type_table[1]) == len(UPSTREAM_PROVENANCE)

    assert _markdown_table(
        snapshot_text,
        "### 6.2 Tick source",
        "### 6.3 Timeframe and bar source",
    ) == _field_table(
        ("Order", "Field", "Exact type"),
        NESTED_SOURCE_FIELDS["CanonicalGoldTickSourceV1"],
        include_source=False,
    )
    assert _markdown_tables(
        snapshot_text,
        "### 6.3 Timeframe and bar source",
        "### 6.4 Symbol source",
    ) == (
        _field_table(
            ("Order", "Field", "Exact type"),
            NESTED_SOURCE_FIELDS["CanonicalGoldTimeframeSourceV1"],
            include_source=False,
        ),
        _field_table(
            ("Order", "Field", "Exact type"),
            NESTED_SOURCE_FIELDS["CanonicalGoldBarSourceV1"],
            include_source=False,
        ),
    )
    assert _markdown_table(
        snapshot_text,
        "### 6.4 Symbol source",
        "## 7. Result Type",
    ) == _field_table(
        ("Order", "Field", "Exact type"),
        NESTED_SOURCE_FIELDS["CanonicalGoldSymbolSpecSourceV1"],
        include_source=False,
    )

    assert TIMEFRAME_ORDER == ("M15", "H1", "H4", "D1")
    assert (
        f"`CanonicalGoldTickSourceV1`: "
        f"{_oxford_backticks(NESTED_SOURCE_FIELDS['CanonicalGoldTickSourceV1'])} "
        "come from the exact accepted `live_tick.json` fields in that order."
        in normalized
    )
    assert (
        "The four timeframe records come from exact accepted "
        "`latest_bars.json.timeframes` in `M15`, `H1`, `H4`, `D1` order. Each "
        "carries `timeframe`, `period_seconds`, and an exact tuple of bars."
        in normalized
    )
    assert (
        f"Each `CanonicalGoldBarSourceV1` carries "
        f"{_oxford_backticks(NESTED_SOURCE_FIELDS['CanonicalGoldBarSourceV1'])} "
        "from the accepted bar in that order."
        in normalized
    )
    assert (
        f"`CanonicalGoldSymbolSpecSourceV1` carries "
        f"{_oxford_backticks(NESTED_SOURCE_FIELDS['CanonicalGoldSymbolSpecSourceV1'])} "
        "from exact accepted `symbol_spec.json` fields in that order."
        in normalized
    )
    assert tuple(
        vector.source
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldTickSourceV1"]
    ) == tuple(
        f"accepted `live_tick.json.{vector.field}`"
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldTickSourceV1"]
    )
    assert tuple(
        vector.source
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldTimeframeSourceV1"]
    ) == tuple(
        f"accepted `latest_bars.json.timeframes[*].{vector.field}`"
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldTimeframeSourceV1"]
    )
    assert tuple(
        vector.source
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldBarSourceV1"]
    ) == tuple(
        f"accepted `latest_bars.json.timeframes[*].bars[*].{vector.field}`"
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldBarSourceV1"]
    )
    assert tuple(
        vector.source
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldSymbolSpecSourceV1"]
    ) == tuple(
        f"accepted `symbol_spec.json.{vector.field}`"
        for vector in NESTED_SOURCE_FIELDS["CanonicalGoldSymbolSpecSourceV1"]
    )
    assert "`bar_count` is validation evidence only and is not copied into G175" in normalized
    assert "No adapter stage converts values to Decimal" in text


def test_status_reason_pairs_preserve_first_failure_order() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    expected_table = (
        ("Condition", "`passed`", "Status", "Exact reason"),
        tuple(
            (
                vector.condition,
                "true" if vector.passed else "false",
                f"`{vector.status_code}`",
                "none" if vector.reason_code is None else f"`{vector.reason_code}`",
            )
            for vector in STATUS_REASON_VECTORS
        ),
    )
    assert _markdown_table(text, "## 8. Result Status", "## 9.") == expected_table
    assert STATUS_REASON_VECTORS[0].source_available is True
    assert all(
        vector.source_available is False for vector in STATUS_REASON_VECTORS[1:]
    )
    assert STATUS_REASON_VECTORS[2].reason_code == "GOLD_SOURCE_READER_NOT_READY"
    assert STATUS_REASON_VECTORS[3].reason_code == "GOLD_SOURCE_READER_RESULT_INVALID"
    assert STATUS_REASON_VECTORS[5].reason_code == "GOLD_SOURCE_DATA_QUALITY_NOT_READY"
    assert STATUS_REASON_VECTORS[6].reason_code == "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID"
    assert "A blocked result has exactly\none reason." in text
    assert "A ready result has no reason. Warning codes are always empty in v1." in text
    assert "the first reached step in\nsection 6 wins" in text
    assert "must not continue to collect, reorder, or combine\nreasons" in text
    assert (
        "Passed-with-warning reader or Gate results are rejected. Warning codes "
        "are not copied into a passed source."
        in normalized
    )


def test_invalid_shape_and_caller_override_vectors_are_concrete() -> None:
    names = tuple(vector.name for vector in INVALID_SHAPE_VECTORS)
    assert names == (
        "missing_authority_field",
        "extra_reader_envelope_field",
        "reordered_gate_envelope",
        "duplicate_source_field",
        "aliased_capsule_field",
        "case_changed_gate_field",
        "subclassed_authority",
        "wrong_container_payloads",
        "mixed_attempt_token",
        "post_call_mutation",
    )
    assert names == tuple(INVALID_SHAPE_ORACLE)
    assert tuple(
        (
            vector.name,
            (
                vector.record,
                vector.expected_fields,
                vector.observed_fields,
                vector.expected_container,
                vector.observed_container,
                vector.accounting_outcome,
                vector.expected_status,
                vector.expected_reason,
                vector.reader_calls,
                vector.gate_calls,
                vector.value_validator_calls,
                vector.source_available,
                vector.source_is_none,
                vector.accepted,
            ),
        )
        for vector in INVALID_SHAPE_VECTORS
    ) == tuple(INVALID_SHAPE_ORACLE.items())
    assert all(
        (vector.expected_fields, vector.expected_container)
        != (vector.observed_fields, vector.observed_container)
        for vector in INVALID_SHAPE_VECTORS
    )
    assert len(
        {
            (vector.record, vector.observed_fields, vector.observed_container)
            for vector in INVALID_SHAPE_VECTORS
        }
    ) == len(INVALID_SHAPE_VECTORS)

    accounting_by_outcome = {vector.outcome: vector for vector in CALL_ACCOUNTING}
    result_pairs = {
        (vector.status_code, vector.reason_code)
        for vector in STATUS_REASON_VECTORS
        if vector.passed is False
    }
    for vector in INVALID_SHAPE_VECTORS:
        accounting = accounting_by_outcome[vector.accounting_outcome]
        assert vector.reader_calls == accounting.reader_calls
        assert vector.gate_calls == accounting.gate_calls
        assert vector.value_validator_calls == accounting.value_validator_calls
        assert (vector.expected_status, vector.expected_reason) in result_pairs
        assert vector.source_available is False
        assert vector.source_is_none is True
        assert vector.accepted is False

    assert all(vector.accepted is False for vector in INVALID_SHAPE_VECTORS)
    assert INVALID_SHAPE_VECTORS[0].observed_fields != AUTHORITY_FIELD_NAMES
    assert len(INVALID_SHAPE_VECTORS[1].observed_fields) == 5
    assert INVALID_SHAPE_VECTORS[2].observed_fields != (
        "passed",
        "status_code",
        "reason_codes",
        "warning_codes",
    )
    assert INVALID_SHAPE_VECTORS[3].observed_fields.count("bundle_id") == 2
    assert INVALID_SHAPE_VECTORS[7].observed_container == "list"

    assert tuple(vector.name for vector in AUTHORITY_OVERRIDES) == (
        "path_override",
        "clock_override",
        "identity_override",
        "policy_override",
        "profile_override",
        "symbol_override",
        "dependency_override",
        "oracle_override",
    )
    assert tuple(vector.name for vector in AUTHORITY_OVERRIDES) == tuple(
        AUTHORITY_OVERRIDE_ORACLE
    )
    assert tuple(
        (
            vector.name,
            (
                vector.attempted_authority,
                vector.accounting_outcome,
                vector.expected_status,
                vector.expected_reason,
                vector.reader_calls,
                vector.gate_calls,
                vector.value_validator_calls,
                vector.source_available,
                vector.source_is_none,
                vector.accepted,
            ),
        )
        for vector in AUTHORITY_OVERRIDES
    ) == tuple(AUTHORITY_OVERRIDE_ORACLE.items())
    assert len(
        {vector.attempted_authority for vector in AUTHORITY_OVERRIDES}
    ) == len(AUTHORITY_OVERRIDES)
    for vector in AUTHORITY_OVERRIDES:
        accounting = accounting_by_outcome[vector.accounting_outcome]
        assert accounting.reader_calls == vector.reader_calls == (0,)
        assert accounting.gate_calls == vector.gate_calls == (0,)
        assert accounting.value_validator_calls == vector.value_validator_calls == (0,)
        assert (
            vector.expected_status,
            vector.expected_reason,
        ) == (
            "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
            "GOLD_SOURCE_AUTHORITY_INVALID",
        )
        assert (vector.expected_status, vector.expected_reason) in result_pairs
        assert vector.source_available is False
        assert vector.source_is_none is True
        assert vector.accepted is False


def test_safety_isolation_and_staged_delivery_remain_closed() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    assert dict(SAFETY_FLAGS) == {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
    assert _markdown_table(text, "## 9. Fixed Safety Envelope", "## 10.") == (
        ("Field", "Value"),
        tuple(
            (f"`{field}`", f"`{'true' if value else 'false'}`")
            for field, value in SAFETY_FLAGS.items()
        ),
    )
    assert (
        "Every adapter result, including ready, has these exact built-in values:"
        in text
    )
    assert _bullet_items(
        text,
        "The adapter must fail closed when any of the following occurs:",
        "The adapter must not:",
    ) == FAIL_CLOSED_CONDITIONS
    assert _bullet_items(text, "The adapter must not:", "## 11.") == (
        FORBIDDEN_BEHAVIORS
    )
    for term in SENSITIVE_TERMS:
        assert term in normalized

    assert _numbered_items(
        text,
        "Later work must remain separately planned and approved:",
        "No stage silently includes the next.",
    ) == STAGED_DELIVERY
    assert "No stage silently includes the next." in text
    assert "Contract is not tests, tests are not implementation" in normalized
    assert "W6 remains `TESTS_ONLY`." in text
    assert "Reader activation, real MT4, EA, order, execution" in normalized
    assert "deployment, and trading remain prohibited" in normalized


def test_closed_oracles_reject_the_four_reviewed_mutations() -> None:
    text = _contract_text()

    renamed_previous_identity = (
        ("bundle_identifier", "exact built-in `str`", "Previous accepted identity"),
        PREVIOUS_IDENTITY_ORACLE[1],
    )
    assert renamed_previous_identity != PREVIOUS_IDENTITY_ORACLE
    assert IMMUTABLE_JSON_ALIASES[:-1] != IMMUTABLE_JSON_ALIAS_ORACLE

    expanded_signature = text.replace(
        "    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,\n",
        "    authority: _CanonicalGoldMarketFactsSourceAuthorityV1,\n"
        "    caller_override: object,\n",
        1,
    )
    assert _fenced_block_lines(
        expanded_signature,
        "It may expose exactly these production names:",
        "`_CanonicalGoldMarketFactsSourceAuthorityV1` and every accepted-attempt type",
        language="python",
    ) != PUBLIC_INTERFACE_LINES

    expanded_stage = text.replace(
        "1. immutable tests-only contract vectors for this adapter boundary;",
        "1. immutable tests-only contract vectors and production implementation "
        "for this adapter boundary;",
        1,
    )
    assert _numbered_items(
        expanded_stage,
        "Later work must remain separately planned and approved:",
        "No stage silently includes the next.",
    ) != STAGED_DELIVERY


def test_static_vectors_do_not_import_or_implement_runtime_adapter() -> None:
    source = TEST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports == {
        "__future__",
        "ast",
        "dataclasses",
        "pathlib",
        "types",
        "pytest",
    }
    assert "app" not in imports

    production_names = {
        "CanonicalGoldMarketFactsSourceAdapterResultV1",
        "_CanonicalGoldMarketFactsSourceAuthorityV1",
        "_CanonicalMt4DemoReadonlyAcceptedAttemptV1",
        "build_server_owned_canonical_gold_market_facts_source_v1",
    }
    defined_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert production_names.isdisjoint(defined_names)

    text = _contract_text()
    assert "This document defines a future boundary only." in text
    assert "Excluded:\n\n- contract vectors or production implementation" in text
    assert "static vectors do not prove implementation" in text
    assert "integration, activation, or verification" in text
