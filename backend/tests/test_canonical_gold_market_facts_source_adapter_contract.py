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
    accepted: bool


@dataclass(frozen=True, slots=True)
class CallerOverrideVector:
    name: str
    attempted_authority: str
    expected_reader_calls: int
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
            FieldVector("bid", "built-in `int` or built-in `float`", "Accepted live tick"),
            FieldVector("ask", "built-in `int` or built-in `float`", "Accepted live tick"),
            FieldVector(
                "spread",
                "built-in `int` or built-in `float`",
                "Accepted live tick",
            ),
            FieldVector("spread_points", "built-in `int`", "Accepted live tick"),
            FieldVector("digits", "built-in `int`", "Accepted live tick"),
            FieldVector(
                "point",
                "built-in `int` or built-in `float`",
                "Accepted live tick",
            ),
            FieldVector("tick_time_utc", "built-in `str`", "Accepted live tick"),
        ),
        "CanonicalGoldTimeframeSourceV1": (
            FieldVector("timeframe", "built-in `str`", "Accepted timeframe"),
            FieldVector("period_seconds", "built-in `int`", "Accepted timeframe"),
            FieldVector(
                "bars",
                "exact built-in `tuple[CanonicalGoldBarSourceV1, ...]`",
                "Accepted timeframe bars",
            ),
        ),
        "CanonicalGoldBarSourceV1": (
            FieldVector("open_time_utc", "built-in `str`", "Accepted bar"),
            FieldVector("open", "built-in `int` or built-in `float`", "Accepted bar"),
            FieldVector("high", "built-in `int` or built-in `float`", "Accepted bar"),
            FieldVector("low", "built-in `int` or built-in `float`", "Accepted bar"),
            FieldVector("close", "built-in `int` or built-in `float`", "Accepted bar"),
            FieldVector("tick_volume", "built-in `int`", "Accepted bar"),
            FieldVector("spread_points", "built-in `int`", "Accepted bar"),
        ),
        "CanonicalGoldSymbolSpecSourceV1": (
            FieldVector("spec_time_utc", "built-in `str`", "Accepted symbol spec"),
            FieldVector("digits", "built-in `int`", "Accepted symbol spec"),
            FieldVector(
                "point",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "tick_size",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "tick_value",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "contract_size",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "min_lot",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "lot_step",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "max_lot",
                "built-in `int` or built-in `float`",
                "Accepted symbol spec",
            ),
            FieldVector("base_currency", "built-in `str`", "Accepted symbol spec"),
            FieldVector(
                "profit_currency",
                "built-in `str`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "margin_currency",
                "built-in `str`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "trade_mode_readonly_label",
                "built-in `str`",
                "Accepted symbol spec",
            ),
            FieldVector(
                "session_status_readonly_label",
                "built-in `str`",
                "Accepted symbol spec",
            ),
        ),
    }
)

IMMUTABLE_JSON_ALIASES = (
    "_CanonicalJsonScalarV1 = exact built-in str | int | float | bool | None",
    "_CanonicalJsonObjectV1 = exact built-in "
    "tuple[tuple[str, _CanonicalJsonValueV1], ...]",
    "_CanonicalJsonArrayV1 = exact built-in tuple[_CanonicalJsonValueV1, ...]",
    "_CanonicalJsonValueV1 = _CanonicalJsonScalarV1 | "
    "_CanonicalJsonObjectV1 | _CanonicalJsonArrayV1",
)

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
    CallerOverrideVector("path_override", "allowed root or bundle directory", 0, False),
    CallerOverrideVector("clock_override", "reference time or clock", 0, False),
    CallerOverrideVector("identity_override", "previous bundle identity", 0, False),
    CallerOverrideVector(
        "policy_override",
        "filesystem, freshness, future-skew, or DataQualityGate policy",
        0,
        False,
    ),
    CallerOverrideVector("profile_override", "policy-profile version", 0, False),
    CallerOverrideVector(
        "symbol_override",
        "canonical or broker symbol mapping",
        0,
        False,
    ),
    CallerOverrideVector(
        "dependency_override",
        "reader, validator, Gate, adapter, or fallback dependency",
        0,
        False,
    ),
    CallerOverrideVector(
        "oracle_override",
        "expected result, status, reason, or oracle",
        0,
        False,
    ),
)

AUTHORITY_FIELD_NAMES = tuple(vector.field for vector in AUTHORITY_FIELDS)
ACCEPTED_FIELD_NAMES = tuple(vector.field for vector in ACCEPTED_ATTEMPT_FIELDS)
RESULT_FIELD_NAMES = tuple(vector.field for vector in RESULT_FIELDS)
SOURCE_FIELD_NAMES = tuple(vector.field for vector in SOURCE_PROVENANCE)

INVALID_SHAPE_VECTORS = (
    InvalidShapeVector(
        "missing_authority_field",
        "authority",
        AUTHORITY_FIELD_NAMES,
        AUTHORITY_FIELD_NAMES[:-1],
        "tuple",
        "tuple",
        False,
    ),
    InvalidShapeVector(
        "extra_result_field",
        "result",
        RESULT_FIELD_NAMES,
        RESULT_FIELD_NAMES + ("internal_status",),
        "tuple",
        "tuple",
        False,
    ),
    InvalidShapeVector(
        "reordered_accepted_attempt",
        "accepted_attempt",
        ACCEPTED_FIELD_NAMES,
        ("manifest", "attempt_token", "payloads_by_filename"),
        "tuple",
        "tuple",
        False,
    ),
    InvalidShapeVector(
        "duplicate_source_field",
        "source",
        SOURCE_FIELD_NAMES,
        SOURCE_FIELD_NAMES + ("bundle_id",),
        "tuple",
        "tuple",
        False,
    ),
    InvalidShapeVector(
        "aliased_capsule_field",
        "accepted_attempt",
        ACCEPTED_FIELD_NAMES,
        ("attempt_token", "manifest_alias", "payloads_by_filename"),
        "tuple",
        "tuple",
        False,
    ),
    InvalidShapeVector(
        "case_changed_result_field",
        "result",
        RESULT_FIELD_NAMES,
        ("Contract_version",) + RESULT_FIELD_NAMES[1:],
        "tuple",
        "tuple",
        False,
    ),
    InvalidShapeVector(
        "subclassed_authority",
        "authority",
        AUTHORITY_FIELD_NAMES,
        AUTHORITY_FIELD_NAMES,
        "exact authority dataclass",
        "authority subclass",
        False,
    ),
    InvalidShapeVector(
        "wrong_container_payloads",
        "accepted_attempt.payloads_by_filename",
        PAYLOAD_ORDER,
        PAYLOAD_ORDER,
        "tuple",
        "list",
        False,
    ),
    InvalidShapeVector(
        "mixed_attempt_token",
        "same_attempt",
        ("reader_token", "gate_reader_object", "post_call_token"),
        ("reader_token", "different_reader_object", "different_token"),
        "identity tuple",
        "identity tuple",
        False,
    ),
    InvalidShapeVector(
        "post_call_mutation",
        "same_attempt",
        ("frozen_authority", "frozen_reader", "frozen_capsule"),
        ("frozen_authority", "mutated_reader", "frozen_capsule"),
        "identity tuple",
        "identity tuple",
        False,
    ),
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

STAGED_DELIVERY = (
    "immutable tests-only contract vectors for this adapter boundary",
    "private accepted-attempt reader seam and source-adapter production types",
    "bounded adapter behavior using the existing reader, value validator, and DataQualityGate",
    "offline canonical-fixture integration evidence",
    "deterministic non-activating verification",
    "separate contracts and vectors for remaining W6 facts and features",
    "a separately versioned ReplayRunner W6 stage before W7",
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _snapshot_contract_text() -> str:
    return SNAPSHOT_CONTRACT_PATH.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def _assert_ordered(text: str, fragments: tuple[str, ...]) -> None:
    positions = tuple(text.index(fragment) for fragment in fragments)
    assert positions == tuple(sorted(positions))


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _assert_ordered_normalized(text: str, fragments: tuple[str, ...]) -> None:
    normalized_text = _normalize_whitespace(text)
    positions = tuple(normalized_text.index(fragment) for fragment in fragments)
    assert positions == tuple(sorted(positions))


def _field_table_rows(vectors: tuple[FieldVector, ...]) -> tuple[str, ...]:
    return tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} | {vector.source} |"
        for index, vector in enumerate(vectors, start=1)
    )


def _call_cell(values: tuple[int, ...]) -> str:
    if values == (0, 1):
        return "0 or 1, as reached internally"
    return " or ".join(str(value) for value in values)


def test_vectors_are_immutable_and_have_exact_counts() -> None:
    assert len(AUTHORITY_FIELDS) == 9
    assert len(PREVIOUS_IDENTITY_FIELDS) == 2
    assert len(ACCEPTED_ATTEMPT_FIELDS) == 3
    assert len(RESULT_FIELDS) == 15
    assert len(SOURCE_PROVENANCE) == 13
    assert len(UPSTREAM_PROVENANCE) == 8
    assert len(CALL_ACCOUNTING) == 11
    assert len(STATUS_REASON_VECTORS) == 10
    assert len(SAFETY_FLAGS) == 8
    assert len(AUTHORITY_OVERRIDES) == 8
    assert len(INVALID_SHAPE_VECTORS) == 10
    assert tuple(len(fields) for fields in NESTED_SOURCE_FIELDS.values()) == (
        7,
        3,
        7,
        14,
    )

    assert type(AUTHORITY_FIELDS) is tuple
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
    assert "class CanonicalGoldMarketFactsSourceAdapterResultV1:" in text
    assert "def build_server_owned_canonical_gold_market_facts_source_v1(" in text
    assert "*,\n    authority: _CanonicalGoldMarketFactsSourceAuthorityV1," in text
    assert ") -> CanonicalGoldMarketFactsSourceAdapterResultV1:" in text
    assert "are private. They must not be exported through `__all__`" in text
    assert "The function must reject a subclassed or look-alike authority object." in text
    assert "Only an approved server integration may create the private authority capsule." in text
    assert "The canonical filesystem reader owns the accepted-attempt capsule." in text
    assert "W1 does not\nimport the W6 adapter" in text
    assert "Only the W6 adapter performs the one-way projection" in text


def test_exact_authority_attempt_and_result_tables_match_contract() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    _assert_ordered(text, _field_table_rows(AUTHORITY_FIELDS))
    _assert_ordered(text, _field_table_rows(ACCEPTED_ATTEMPT_FIELDS))

    result_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} |"
        for index, vector in enumerate(RESULT_FIELDS, start=1)
    )
    _assert_ordered(text, result_rows)
    assert (
        "`_CanonicalBundlePreviousIdentityV1` is frozen and slotted with exact "
        "built-in\n`str bundle_id` followed by exact built-in `int sequence`."
        in text
    )
    assert "`max_manifest_consistency_retries` to exact built-in integer\nzero" in text
    assert "Built-in strings, `PurePath`, the factory `Path` class itself" in normalized
    assert "a concrete-path subclass, a wrong-platform path" in normalized


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
    _assert_ordered(text, IMMUTABLE_JSON_ALIASES)
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
    rows = tuple(
        "| "
        + vector.outcome
        + " | "
        + _call_cell(vector.reader_calls)
        + " | "
        + _call_cell(vector.gate_calls)
        + " | "
        + _call_cell(vector.value_validator_calls)
        + " |"
        for vector in CALL_ACCOUNTING
    )
    _assert_ordered(text, rows)
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
    source_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.source} |"
        for index, vector in enumerate(SOURCE_PROVENANCE, start=1)
    )
    upstream_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.source} |"
        for index, vector in enumerate(UPSTREAM_PROVENANCE, start=1)
    )
    _assert_ordered(text, source_rows)
    _assert_ordered(text, upstream_rows)

    source_type_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} |"
        for index, vector in enumerate(SOURCE_PROVENANCE, start=1)
    )
    upstream_type_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} |"
        for index, vector in enumerate(UPSTREAM_PROVENANCE, start=1)
    )
    _assert_ordered(
        _section(snapshot_text, "## 6. Source Type", "### 6.1 Upstream evidence"),
        source_type_rows,
    )
    _assert_ordered(
        _section(snapshot_text, "### 6.1 Upstream evidence", "### 6.2 Tick source"),
        upstream_type_rows,
    )

    tick_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} |"
        for index, vector in enumerate(
            NESTED_SOURCE_FIELDS["CanonicalGoldTickSourceV1"],
            start=1,
        )
    )
    timeframe_and_bar_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} |"
        for fields in (
            NESTED_SOURCE_FIELDS["CanonicalGoldTimeframeSourceV1"],
            NESTED_SOURCE_FIELDS["CanonicalGoldBarSourceV1"],
        )
        for index, vector in enumerate(fields, start=1)
    )
    symbol_rows = tuple(
        f"| {index} | `{vector.field}` | {vector.exact_type} |"
        for index, vector in enumerate(
            NESTED_SOURCE_FIELDS["CanonicalGoldSymbolSpecSourceV1"],
            start=1,
        )
    )
    _assert_ordered(
        _section(snapshot_text, "### 6.2 Tick source", "### 6.3 Timeframe and bar source"),
        tick_rows,
    )
    _assert_ordered(
        _section(snapshot_text, "### 6.3 Timeframe and bar source", "### 6.4 Symbol source"),
        timeframe_and_bar_rows,
    )
    _assert_ordered(
        _section(snapshot_text, "### 6.4 Symbol source", "## 7. Result Type"),
        symbol_rows,
    )

    assert TIMEFRAME_ORDER == ("M15", "H1", "H4", "D1")
    assert "in `M15`, `H1`, `H4`, `D1` order" in text

    assert "`CanonicalGoldTickSourceV1`" in text
    assert "The four timeframe records come from exact accepted" in text
    assert "`CanonicalGoldBarSourceV1`" in text
    assert "`CanonicalGoldSymbolSpecSourceV1`" in text
    assert "`bar_count` is validation evidence only and is not copied into G175" in normalized
    assert "No adapter stage converts values to Decimal" in text


def test_status_reason_pairs_preserve_first_failure_order() -> None:
    text = _contract_text()
    rows = tuple(
        f"| {vector.condition} | {'true' if vector.passed else 'false'} | "
        f"`{vector.status_code}` | "
        + ("none" if vector.reason_code is None else f"`{vector.reason_code}`")
        + " |"
        for vector in STATUS_REASON_VECTORS
    )
    _assert_ordered(text, rows)
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


def test_invalid_shape_and_caller_override_vectors_are_concrete() -> None:
    names = tuple(vector.name for vector in INVALID_SHAPE_VECTORS)
    assert names == (
        "missing_authority_field",
        "extra_result_field",
        "reordered_accepted_attempt",
        "duplicate_source_field",
        "aliased_capsule_field",
        "case_changed_result_field",
        "subclassed_authority",
        "wrong_container_payloads",
        "mixed_attempt_token",
        "post_call_mutation",
    )
    assert all(vector.accepted is False for vector in INVALID_SHAPE_VECTORS)
    assert INVALID_SHAPE_VECTORS[0].observed_fields != AUTHORITY_FIELD_NAMES
    assert len(INVALID_SHAPE_VECTORS[1].observed_fields) == len(RESULT_FIELDS) + 1
    assert INVALID_SHAPE_VECTORS[2].observed_fields != ACCEPTED_FIELD_NAMES
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
    assert all(vector.expected_reader_calls == 0 for vector in AUTHORITY_OVERRIDES)
    assert all(vector.accepted is False for vector in AUTHORITY_OVERRIDES)


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
    for field, value in SAFETY_FLAGS.items():
        assert f"| `{field}` | `{'true' if value else 'false'}` |" in text
    for term in SENSITIVE_TERMS:
        assert term in normalized

    _assert_ordered_normalized(text, STAGED_DELIVERY)
    assert "No stage silently includes the next." in text
    assert "Contract is not tests, tests are not implementation" in normalized
    assert "W6 remains `TESTS_ONLY`." in text
    assert "Reader activation, real MT4, EA, order, execution" in normalized
    assert "deployment, and trading remain prohibited" in normalized


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
