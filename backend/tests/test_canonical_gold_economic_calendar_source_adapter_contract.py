from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
import re
from types import MappingProxyType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_economic_calendar_source_adapter_contract.md"
)
G199_CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_economic_window_facts_v1_contract.md"
)
G201_MODULE_PATH = (
    REPO_ROOT / "backend" / "app" / "services" / "canonical_gold_economic_window_facts.py"
)
G185_MODULE_PATH = (
    REPO_ROOT
    / "backend"
    / "app"
    / "services"
    / "canonical_gold_market_facts_docs_fixture_integration.py"
)
TEST_PATH = Path(__file__).resolve()


@dataclass(frozen=True, slots=True)
class FieldVector:
    field: str
    contract_cell: str


@dataclass(frozen=True, slots=True)
class CallAccountingVector:
    outcome: str
    fixture_reads: int
    parser_calls: int
    result_validator_calls: int


@dataclass(frozen=True, slots=True)
class StatusReasonVector:
    priority: int
    status: str
    reason: str
    owner: str


@dataclass(frozen=True, slots=True)
class BoundVector:
    name: str
    value: int
    accepted: bool
    expected_priority: int | None


@dataclass(frozen=True, slots=True)
class ShapeMutationVector:
    schema: str
    mutation: str
    expected_fields: tuple[str, ...]
    observed_fields: tuple[str, ...]
    expected_container: str
    observed_container: str
    expected_priority: int
    expected_status: str
    expected_reason: str


@dataclass(frozen=True, slots=True)
class ValueMutationVector:
    name: str
    field_path: tuple[str, ...]
    invalid_value: object
    expected_priority: int
    expected_status: str
    expected_reason: str


@dataclass(frozen=True, slots=True)
class CallerOverrideVector:
    name: str
    attempted_authority: str
    fixture_reads: int
    accepted: bool


@dataclass(frozen=True, slots=True)
class ContractClauseVector:
    name: str
    required_text: str
    invalid_text: str


@dataclass(frozen=True, slots=True)
class ExceptionBoundaryVector:
    name: str
    validator_result: bool | None
    expected_status: str
    expected_reason: str
    snapshot_available: bool
    snapshot: None
    leaks_internal_state: bool


class StrictStringSubclass(str):
    pass


class StrictIntSubclass(int):
    pass


class StrictTupleSubclass(tuple):
    pass


PUBLIC_EXPORTS = (
    "CanonicalGoldEconomicCalendarSourceAdapterResultV1",
    "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
)

PUBLIC_INTERFACE = """def build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
    *,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    ..."""

VALIDATOR_INTERFACE = """def _is_safe_canonical_gold_economic_calendar_source_adapter_result_v1(
    *,
    adapter_result: object,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> bool:
    ..."""

SANITIZER_INTERFACE = """def _build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1(
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    ..."""

EXPECTED_IDENTITY_FIELDS = (
    FieldVector("calendar_snapshot_id", "built-in `str`"),
)

READ_POLICY_FIELDS = (
    FieldVector("maximum_fixture_bytes", "`1048576`"),
    FieldVector("maximum_calendar_events", "`512`"),
    FieldVector("maximum_calendar_age_microseconds", "`300000000`"),
    FieldVector("maximum_coverage_span_microseconds", "`259200000000`"),
    FieldVector("search_horizon_microseconds", "`86400000000`"),
    FieldVector("maximum_read_attempts", "`1`"),
)

AUTHORITY_FIELDS = (
    FieldVector(
        "authority_token",
        "exact built-in `object` identity held by the module",
    ),
    FieldVector("allowed_root", "exact concrete platform `WindowsPath` or `PosixPath`"),
    FieldVector(
        "fixture_path",
        "same exact concrete platform path type as `allowed_root`",
    ),
    FieldVector("reference_time_utc", "exact aware UTC `datetime.datetime`"),
    FieldVector(
        "expected_identity",
        "exact `_CanonicalGoldEconomicCalendarExpectedIdentityV1`",
    ),
    FieldVector(
        "read_policy",
        "exact `_CanonicalGoldEconomicCalendarReadPolicyV1`",
    ),
    FieldVector("calendar_schema_version", "built-in `str`, exactly `\"1.0\"`"),
    FieldVector(
        "source_profile_version",
        "built-in `str`, exactly `\"canonical_gold_economic_calendar_source_v1\"`",
    ),
)

FIXTURE_FIELDS = (
    FieldVector("fixture_contract_version", "string, exactly `\"1.0\"`"),
    FieldVector("calendar_schema_version", "string, exactly `\"1.0\"`"),
    FieldVector("calendar_snapshot_id", "G199-valid ASCII identifier string"),
    FieldVector("generated_at_utc", "strict canonical UTC `Z` string"),
    FieldVector("coverage_start_utc", "strict canonical UTC `Z` string"),
    FieldVector("coverage_end_utc", "strict canonical UTC `Z` string"),
    FieldVector(
        "events",
        "exact JSON array; count and elements are validated only under EVENT_INVALID",
    ),
)

EVENT_FIELDS = (
    FieldVector("event_id", "G199-valid ASCII identifier string"),
    FieldVector("scheduled_at_utc", "strict canonical UTC `Z` string"),
    FieldVector("country_code", "string from the closed G199 enum"),
    FieldVector("currency_code", "string from the closed G199 enum"),
    FieldVector("event_category_code", "string from the closed G199 enum"),
    FieldVector("impact_code", "string from the closed G199 enum"),
    FieldVector("source_revision", "built-in JSON integer, zero or greater"),
    FieldVector("event_status_code", "string from the closed G199 enum"),
)

SNAPSHOT_FIELDS = (
    FieldVector("contract_version", "adapter constant `\"1.0\"`"),
    FieldVector(
        "calendar_schema_version",
        "exact validated authority and fixture value `\"1.0\"`",
    ),
    FieldVector(
        "calendar_snapshot_id",
        "exact validated expected-identity value",
    ),
    FieldVector(
        "source_profile_version",
        "authority constant `\"canonical_gold_economic_calendar_source_v1\"`",
    ),
    FieldVector("generated_at_utc", "exact validated fixture string"),
    FieldVector("coverage_start_utc", "exact validated fixture string"),
    FieldVector("coverage_end_utc", "exact validated fixture string"),
    FieldVector("events", "fresh exact tuple of fresh G201 event records"),
    FieldVector("upstream_evidence", "fresh record from section 8.2"),
    FieldVector("read_only", "exact built-in `True`"),
    FieldVector("demo_only", "exact built-in `True`"),
    FieldVector("contains_raw_provider_payload", "exact built-in `False`"),
)

UPSTREAM_FIELDS = (
    FieldVector("adapter_passed", "built-in `True`"),
    FieldVector(
        "adapter_status_code",
        "`\"CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY\"`",
    ),
    FieldVector("schema_validated", "built-in `True`"),
    FieldVector("identity_validated", "built-in `True`"),
    FieldVector(
        "timestamps_normalized",
        "built-in `True` after exact canonical UTC validation, without rewriting",
    ),
    FieldVector(
        "same_snapshot_bound",
        "built-in `True` after the single-attempt and drift checks",
    ),
    FieldVector("warning_codes", "exact empty built-in tuple"),
    FieldVector(
        "raw_payload_discarded",
        "built-in `True` only when no raw object is reachable from output",
    ),
)

RESULT_FIELDS = (
    FieldVector("contract_version", "built-in `str`, exactly `\"1.0\"`"),
    FieldVector("passed", "built-in `bool`"),
    FieldVector("status_code", "built-in `str`"),
    FieldVector("reason_codes", "exact built-in `tuple[str, ...]`"),
    FieldVector("warning_codes", "exact built-in `tuple[str, ...]`"),
    FieldVector("snapshot_available", "built-in `bool`"),
    FieldVector(
        "snapshot",
        "exact G201 `CanonicalGoldEconomicCalendarSnapshotV1` or `None`",
    ),
    FieldVector("read_only", "built-in `bool`"),
    FieldVector("demo_only", "built-in `bool`"),
    FieldVector("is_tradable", "built-in `bool`"),
    FieldVector("can_execute", "built-in `bool`"),
    FieldVector("is_trading_permission", "built-in `bool`"),
    FieldVector("is_execution_instruction", "built-in `bool`"),
    FieldVector("allowed_to_call_ea", "built-in `bool`"),
    FieldVector("allowed_to_modify_risk", "built-in `bool`"),
)

PUBLIC_SCHEMAS = MappingProxyType(
    {
        "_CanonicalGoldEconomicCalendarExpectedIdentityV1": EXPECTED_IDENTITY_FIELDS,
        "_CanonicalGoldEconomicCalendarReadPolicyV1": READ_POLICY_FIELDS,
        "_CanonicalGoldEconomicCalendarSourceAuthorityV1": AUTHORITY_FIELDS,
        "fixture_document": FIXTURE_FIELDS,
        "fixture_event": EVENT_FIELDS,
        "CanonicalGoldEconomicCalendarSnapshotV1": SNAPSHOT_FIELDS,
        "CanonicalGoldEconomicCalendarUpstreamEvidenceV1": UPSTREAM_FIELDS,
        "CanonicalGoldEconomicCalendarSourceAdapterResultV1": RESULT_FIELDS,
    }
)

FIXED_AUTHORITY = MappingProxyType(
    {
        "calendar_snapshot_id": "canonical-gold-economic-calendar-docs-fixture-v1",
        "calendar_schema_version": "1.0",
        "source_profile_version": "canonical_gold_economic_calendar_source_v1",
        "reference_time_utc": "datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)",
        "maximum_fixture_bytes": 1048576,
        "maximum_calendar_events": 512,
        "maximum_calendar_age_microseconds": 300000000,
        "maximum_coverage_span_microseconds": 259200000000,
        "search_horizon_microseconds": 86400000000,
        "maximum_read_attempts": 1,
    }
)

FIXED_PATH_PARTS = (
    "docs",
    "architecture",
    "fixtures",
    "canonical-gold-economic-calendar-v1",
    "economic_calendar.json",
)

EVENT_CATEGORY_CODES = (
    "FOMC_RATE_DECISION",
    "FOMC_STATEMENT",
    "FOMC_PRESS_CONFERENCE",
    "US_CPI",
    "US_CORE_CPI",
    "US_PCE",
    "US_CORE_PCE",
    "US_NONFARM_PAYROLLS",
    "US_UNEMPLOYMENT_RATE",
    "US_GDP",
    "US_RETAIL_SALES",
    "US_ISM_MANUFACTURING",
    "US_ISM_SERVICES",
)
COUNTRY_CODES = ("US",)
CURRENCY_CODES = ("USD",)
IMPACT_CODES = ("LOW", "MEDIUM", "HIGH")
EVENT_STATUS_CODES = ("SCHEDULED", "CANCELLED")

CALL_ACCOUNTING = (
    CallAccountingVector("Authority or path invalid", 0, 0, 0),
    CallAccountingVector("Fixture state unavailable or bounded read fails", 1, 0, 0),
    CallAccountingVector("Decode or parse fails", 1, 1, 0),
    CallAccountingVector("Top-level fixture shape validation fails", 1, 1, 0),
    CallAccountingVector("Snapshot identity validation fails", 1, 1, 0),
    CallAccountingVector("Generated-time freshness validation fails", 1, 1, 0),
    CallAccountingVector("Coverage validation fails", 1, 1, 0),
    CallAccountingVector(
        "Event count, shape, value, order, or coverage-membership validation fails",
        1,
        1,
        0,
    ),
    CallAccountingVector("Construction or post-read drift fails", 1, 1, 0),
    CallAccountingVector("Constructed result is invalid", 1, 1, 1),
    CallAccountingVector("READY", 1, 1, 1),
)

STATUS_REASON_VECTORS = (
    StatusReasonVector(
        1,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_AUTHORITY_INVALID",
        "GOLD_ECONOMIC_CALENDAR_AUTHORITY_INVALID",
        "authority_or_lexical_path",
    ),
    StatusReasonVector(
        2,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FIXTURE_UNAVAILABLE",
        "GOLD_ECONOMIC_CALENDAR_FIXTURE_UNAVAILABLE",
        "single_filesystem_attempt",
    ),
    StatusReasonVector(
        3,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FIXTURE_INVALID",
        "GOLD_ECONOMIC_CALENDAR_FIXTURE_INPUT_INVALID",
        "top_level_or_events_container",
    ),
    StatusReasonVector(
        4,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_IDENTITY_INVALID",
        "GOLD_ECONOMIC_CALENDAR_IDENTITY_INVALID",
        "schema_or_snapshot_identity",
    ),
    StatusReasonVector(
        5,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FRESHNESS_INVALID",
        "GOLD_ECONOMIC_CALENDAR_FRESHNESS_INVALID",
        "generated_time",
    ),
    StatusReasonVector(
        6,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_COVERAGE_INVALID",
        "GOLD_ECONOMIC_CALENDAR_COVERAGE_INVALID",
        "coverage_time_or_policy",
    ),
    StatusReasonVector(
        7,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_EVENT_INVALID",
        "GOLD_ECONOMIC_CALENDAR_EVENT_INPUT_INVALID",
        "event_count_shape_value_or_order",
    ),
    StatusReasonVector(
        8,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_RESULT_INVALID",
        "GOLD_ECONOMIC_CALENDAR_RESULT_INVALID",
        "constructed_source_or_result",
    ),
    StatusReasonVector(
        9,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_SAFE_FAILURE",
        "GOLD_ECONOMIC_CALENDAR_EXCEPTION_SANITIZED",
        "unexpected_exception",
    ),
)

READY_MAPPING = MappingProxyType(
    {
        "passed": True,
        "status_code": "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY",
        "reason_codes": (),
        "warning_codes": (),
        "snapshot_available": True,
    }
)

FAILURE_CLEARING = MappingProxyType(
    {
        "passed": False,
        "reason_count": 1,
        "warning_codes": (),
        "snapshot_available": False,
        "snapshot": None,
    }
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

BOUND_VECTORS = (
    BoundVector("fixture_bytes_empty", 0, False, 2),
    BoundVector("fixture_bytes_minimum", 1, True, None),
    BoundVector("fixture_bytes_maximum", 1048576, True, None),
    BoundVector("fixture_bytes_overflow", 1048577, False, 2),
    BoundVector("event_count_zero", 0, True, None),
    BoundVector("event_count_maximum", 512, True, None),
    BoundVector("event_count_overflow", 513, False, 7),
    BoundVector("calendar_age_zero", 0, True, None),
    BoundVector("calendar_age_maximum", 300000000, True, None),
    BoundVector("calendar_age_stale", 300000001, False, 5),
    BoundVector("calendar_age_future", -1, False, 5),
    BoundVector("coverage_span_maximum", 259200000000, True, None),
    BoundVector("coverage_span_overflow", 259200000001, False, 6),
    BoundVector("coverage_start_exact_horizon", -86400000000, True, None),
    BoundVector("coverage_start_short", -86399999999, False, 6),
    BoundVector("coverage_end_exact_horizon", 86400000000, True, None),
    BoundVector("coverage_end_short", 86399999999, False, 6),
)

CALLER_OVERRIDE_VECTORS = (
    CallerOverrideVector("caller_path", "fixture_path", 0, False),
    CallerOverrideVector("caller_clock", "reference_time_utc", 0, False),
    CallerOverrideVector("caller_identity", "expected_identity", 0, False),
    CallerOverrideVector("caller_profile", "source_profile_version", 0, False),
    CallerOverrideVector("caller_policy", "read_policy", 0, False),
    CallerOverrideVector("caller_parser", "parser", 0, False),
    CallerOverrideVector("caller_provider", "provider", 0, False),
    CallerOverrideVector("caller_oracle", "expected_status_or_reason", 0, False),
)


def _field_names(vectors: tuple[FieldVector, ...]) -> tuple[str, ...]:
    return tuple(vector.field for vector in vectors)


def _shape_mutations(
    *,
    schema: str,
    vectors: tuple[FieldVector, ...],
    priority: int,
    status: str,
    reason: str,
    container: str,
) -> tuple[ShapeMutationVector, ...]:
    fields = _field_names(vectors)
    return (
        ShapeMutationVector(
            schema,
            "missing",
            fields,
            fields[:-1],
            container,
            container,
            priority,
            status,
            reason,
        ),
        ShapeMutationVector(
            schema,
            "extra",
            fields,
            fields + ("unexpected",),
            container,
            container,
            priority,
            status,
            reason,
        ),
        *(
            (
                ShapeMutationVector(
                    schema,
                    "reordered",
                    fields,
                    fields[::-1],
                    container,
                    container,
                    priority,
                    status,
                    reason,
                ),
            )
            if len(fields) > 1
            else ()
        ),
        ShapeMutationVector(
            schema,
            "duplicate",
            fields,
            fields + (fields[0],),
            container,
            container,
            priority,
            status,
            reason,
        ),
        ShapeMutationVector(
            schema,
            "alias",
            fields,
            (fields[0] + "_alias",) + fields[1:],
            container,
            container,
            priority,
            status,
            reason,
        ),
        ShapeMutationVector(
            schema,
            "case_change",
            fields,
            (fields[0].upper(),) + fields[1:],
            container,
            container,
            priority,
            status,
            reason,
        ),
        ShapeMutationVector(
            schema,
            "wrong_container",
            fields,
            fields,
            container,
            "list" if container != "list" else "tuple",
            priority,
            status,
            reason,
        ),
    )


SHAPE_MUTATION_VECTORS = (
    *_shape_mutations(
        schema="expected_identity",
        vectors=EXPECTED_IDENTITY_FIELDS,
        priority=1,
        status=STATUS_REASON_VECTORS[0].status,
        reason=STATUS_REASON_VECTORS[0].reason,
        container="frozen_slotted_dataclass",
    ),
    *_shape_mutations(
        schema="read_policy",
        vectors=READ_POLICY_FIELDS,
        priority=1,
        status=STATUS_REASON_VECTORS[0].status,
        reason=STATUS_REASON_VECTORS[0].reason,
        container="frozen_slotted_dataclass",
    ),
    *_shape_mutations(
        schema="authority",
        vectors=AUTHORITY_FIELDS,
        priority=1,
        status=STATUS_REASON_VECTORS[0].status,
        reason=STATUS_REASON_VECTORS[0].reason,
        container="frozen_slotted_dataclass",
    ),
    *_shape_mutations(
        schema="fixture_document",
        vectors=FIXTURE_FIELDS,
        priority=3,
        status=STATUS_REASON_VECTORS[2].status,
        reason=STATUS_REASON_VECTORS[2].reason,
        container="json_object_pairs",
    ),
    *_shape_mutations(
        schema="fixture_event",
        vectors=EVENT_FIELDS,
        priority=7,
        status=STATUS_REASON_VECTORS[6].status,
        reason=STATUS_REASON_VECTORS[6].reason,
        container="json_object_pairs",
    ),
    *_shape_mutations(
        schema="calendar_snapshot",
        vectors=SNAPSHOT_FIELDS,
        priority=8,
        status=STATUS_REASON_VECTORS[7].status,
        reason=STATUS_REASON_VECTORS[7].reason,
        container="frozen_slotted_dataclass",
    ),
    *_shape_mutations(
        schema="upstream_evidence",
        vectors=UPSTREAM_FIELDS,
        priority=8,
        status=STATUS_REASON_VECTORS[7].status,
        reason=STATUS_REASON_VECTORS[7].reason,
        container="frozen_slotted_dataclass",
    ),
    *_shape_mutations(
        schema="adapter_result",
        vectors=RESULT_FIELDS,
        priority=8,
        status=STATUS_REASON_VECTORS[7].status,
        reason=STATUS_REASON_VECTORS[7].reason,
        container="frozen_slotted_dataclass",
    ),
)

VALUE_MUTATION_VECTORS = (
    ValueMutationVector(
        "path_string",
        ("authority", "fixture_path"),
        "docs/architecture/fixtures/economic_calendar.json",
        1,
        STATUS_REASON_VECTORS[0].status,
        STATUS_REASON_VECTORS[0].reason,
    ),
    ValueMutationVector(
        "identity_subclass",
        ("authority", "expected_identity", "calendar_snapshot_id"),
        StrictStringSubclass("canonical-gold-economic-calendar-docs-fixture-v1"),
        1,
        STATUS_REASON_VECTORS[0].status,
        STATUS_REASON_VECTORS[0].reason,
    ),
    ValueMutationVector(
        "read_policy_integer_subclass",
        ("authority", "read_policy", "maximum_calendar_events"),
        StrictIntSubclass(512),
        1,
        STATUS_REASON_VECTORS[0].status,
        STATUS_REASON_VECTORS[0].reason,
    ),
    ValueMutationVector(
        "fixture_contract_wrong_type",
        ("fixture", "fixture_contract_version"),
        1,
        3,
        STATUS_REASON_VECTORS[2].status,
        STATUS_REASON_VECTORS[2].reason,
    ),
    ValueMutationVector(
        "calendar_schema_alias",
        ("fixture", "calendar_schema_version"),
        "v1",
        4,
        STATUS_REASON_VECTORS[3].status,
        STATUS_REASON_VECTORS[3].reason,
    ),
    ValueMutationVector(
        "generated_timestamp_invalid_date",
        ("fixture", "generated_at_utc"),
        "2026-02-30T00:00:00Z",
        5,
        STATUS_REASON_VECTORS[4].status,
        STATUS_REASON_VECTORS[4].reason,
    ),
    ValueMutationVector(
        "coverage_timestamp_offset",
        ("fixture", "coverage_start_utc"),
        "2026-07-09T02:30:05+00:00",
        6,
        STATUS_REASON_VECTORS[5].status,
        STATUS_REASON_VECTORS[5].reason,
    ),
    ValueMutationVector(
        "event_revision_bool",
        ("fixture", "events", "source_revision"),
        True,
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_category_case_change",
        ("fixture", "events", "event_category_code"),
        "us_cpi",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_revision_integer_subclass",
        ("fixture", "events", "source_revision"),
        StrictIntSubclass(1),
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_revision_negative",
        ("fixture", "events", "source_revision"),
        -1,
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_timestamp_invalid_date",
        ("fixture", "events", "scheduled_at_utc"),
        "2026-02-30T00:00:00Z",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_country_unknown",
        ("fixture", "events", "country_code"),
        "USA",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_currency_case_change",
        ("fixture", "events", "currency_code"),
        "usd",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_impact_unknown",
        ("fixture", "events", "impact_code"),
        "CRITICAL",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_status_unknown",
        ("fixture", "events", "event_status_code"),
        "POSTPONED",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_duplicate_ids",
        ("fixture", "events"),
        ("event-001", "event-001"),
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_order_descending",
        ("fixture", "events"),
        (
            ("2026-07-10T03:00:00Z", "event-002"),
            ("2026-07-10T02:00:00Z", "event-001"),
        ),
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_tie_order_descending",
        ("fixture", "events"),
        (
            ("2026-07-10T03:00:00Z", "event-002"),
            ("2026-07-10T03:00:00Z", "event-001"),
        ),
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_outside_coverage",
        ("fixture", "events", "scheduled_at_utc"),
        "2026-07-13T02:30:05.000001Z",
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "event_wrong_element",
        ("fixture", "events"),
        ("not-an-event-record",),
        7,
        STATUS_REASON_VECTORS[6].status,
        STATUS_REASON_VECTORS[6].reason,
    ),
    ValueMutationVector(
        "result_reason_tuple_subclass",
        ("result", "reason_codes"),
        StrictTupleSubclass(("GOLD_ECONOMIC_CALENDAR_RESULT_INVALID",)),
        8,
        STATUS_REASON_VECTORS[7].status,
        STATUS_REASON_VECTORS[7].reason,
    ),
    ValueMutationVector(
        "warning_pollution",
        ("result", "warning_codes"),
        ("warning",),
        8,
        STATUS_REASON_VECTORS[7].status,
        STATUS_REASON_VECTORS[7].reason,
    ),
    ValueMutationVector(
        "snapshot_raw_payload_marker",
        ("result", "snapshot", "contains_raw_provider_payload"),
        True,
        8,
        STATUS_REASON_VECTORS[7].status,
        STATUS_REASON_VECTORS[7].reason,
    ),
)

STAGED_DELIVERY = (
    "immutable tests-only contract vectors for G202",
    "production result and private authority types plus bounded adapter",
    "fixed checked-in offline calendar fixture and controlled adapter tests",
    "genuine offline G185-G178-calendar-adapter-G201 composition",
    "deterministic non-activating verification of exact composition",
    "separately contracted later W6 facts and features",
    "separately versioned ReplayRunner W6 stage before W7",
)

SENSITIVE_TERMS = (
    "path",
    "filename",
    "provider",
    "raw payload",
    "source bytes",
    "checksum",
    "digest",
    "exception",
    "traceback",
    "private token",
    "credential",
    "account",
    "order",
    "execution instruction",
)

FROZEN_SLOTTED_CLAUSES = (
    ContractClauseVector(
        "expected_identity_frozen_slotted",
        "`_CanonicalGoldEconomicCalendarExpectedIdentityV1` is a frozen, slotted",
        "`_CanonicalGoldEconomicCalendarExpectedIdentityV1` is mutable and unslotted",
    ),
    ContractClauseVector(
        "read_policy_frozen_slotted",
        "`_CanonicalGoldEconomicCalendarReadPolicyV1` is a frozen, slotted dataclass",
        "`_CanonicalGoldEconomicCalendarReadPolicyV1` is a mutable dataclass",
    ),
    ContractClauseVector(
        "authority_frozen_slotted",
        "`_CanonicalGoldEconomicCalendarSourceAuthorityV1` is a frozen, slotted",
        "`_CanonicalGoldEconomicCalendarSourceAuthorityV1` is mutable and unslotted",
    ),
    ContractClauseVector(
        "result_frozen_slotted",
        "`CanonicalGoldEconomicCalendarSourceAdapterResultV1` is a frozen, slotted",
        "`CanonicalGoldEconomicCalendarSourceAdapterResultV1` is mutable and unslotted",
    ),
)

EVENT_INVARIANT_CLAUSES = (
    ContractClauseVector(
        "canonical_event_order",
        "Events must already be in the exact G199 canonical order by\n`(scheduled_at_utc, event_id)`.",
        "Events may arrive in arbitrary order.",
    ),
    ContractClauseVector(
        "unique_event_ids",
        "Event IDs are unique.",
        "Event IDs may repeat.",
    ),
    ContractClauseVector(
        "ascii_tie_order",
        "Equal scheduled times\nuse ASCII event-ID order.",
        "Equal scheduled times may use source order.",
    ),
    ContractClauseVector(
        "event_utc_codes_and_revision",
        "ASCII values, real UTC timestamp,\n   valid closed codes, and non-negative exact revision.",
        "ASCII values, approximate timestamps, open codes, and signed revisions are accepted.",
    ),
    ContractClauseVector(
        "event_coverage_membership",
        "canonical event order, unique IDs, coverage membership",
        "canonical event order and unique IDs",
    ),
)

EXCEPTION_BOUNDARY_CLAUSES = (
    ContractClauseVector(
        "validator_exception_returns_false",
        "returns false on every invalid input or internal validation exception.",
        "propagates internal validation exceptions.",
    ),
    ContractClauseVector(
        "sanitizer_returns_empty_safe_failure",
        "sanitizer returns a fresh exact SAFE_FAILURE result with no snapshot.",
        "sanitizer returns SAFE_FAILURE with the partial snapshot.",
    ),
    ContractClauseVector(
        "exception_state_is_not_exposed",
        "Unexpected exception type, message, traceback, path, fixture bytes, parsed\ncontent, token, or source status must not enter the result or a log.",
        "Unexpected exception details may enter the result.",
    ),
)

EXCEPTION_BOUNDARY_VECTORS = (
    ExceptionBoundaryVector(
        "validator_internal_exception_then_sanitizer",
        False,
        STATUS_REASON_VECTORS[8].status,
        STATUS_REASON_VECTORS[8].reason,
        False,
        None,
        False,
    ),
    ExceptionBoundaryVector(
        "sanitizer_internal_exception_boundary",
        None,
        STATUS_REASON_VECTORS[8].status,
        STATUS_REASON_VECTORS[8].reason,
        False,
        None,
        False,
    ),
)

SAFE_FAILURE_MAPPING = MappingProxyType(
    {
        "passed": False,
        "status_code": STATUS_REASON_VECTORS[8].status,
        "reason_codes": (STATUS_REASON_VECTORS[8].reason,),
        "warning_codes": (),
        "snapshot_available": False,
        "snapshot": None,
        **SAFETY_FLAGS,
    }
)


def _section(text: str, start: str, end: str) -> str:
    return text[text.index(start) : text.index(end)]


def _table_rows(block: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (field, cell.strip())
        for field, cell in re.findall(
            r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|$",
            block,
            re.MULTILINE,
        )
    )


def _vector_rows(vectors: tuple[FieldVector, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((vector.field, vector.contract_cell) for vector in vectors)


def _status_rows(text: str) -> tuple[tuple[int, str, str], ...]:
    block = _section(
        text,
        "## 10. Status, Reason, and First-Failure Mapping",
        "## 11. Fixed Safety Envelope",
    )
    return tuple(
        (int(priority), status, reason)
        for priority, status, reason in re.findall(
            r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
            block,
            re.MULTILINE,
        )
    )


def _contract_oracle(candidate: str) -> bool:
    try:
        expected_identity = _table_rows(
            _section(candidate, "### 5.1 Expected identity", "### 5.2 Read policy")
        )
        statuses = _status_rows(candidate)
        stages = tuple(
            int(value)
            for value in re.findall(
                r"^(\d+)\.\s",
                _section(
                    candidate,
                    "## 14. Required Staged Delivery",
                    "## 15. WBS and Capability Boundaries",
                ),
                re.MULTILINE,
            )
        )
        return (
            expected_identity == _vector_rows(EXPECTED_IDENTITY_FIELDS)
            and PUBLIC_INTERFACE in candidate
            and VALIDATOR_INTERFACE in candidate
            and SANITIZER_INTERFACE in candidate
            and statuses
            == tuple(
                (vector.priority, vector.status, vector.reason)
                for vector in STATUS_REASON_VECTORS
            )
            and "Failure returns AUTHORITY_INVALID with zero reads." in candidate
            and "Any failure returns FIXTURE_UNAVAILABLE with one\n   read attempt."
            in candidate
            and "No event-record failure may be relabeled as FIXTURE_INVALID."
            in candidate
            and all(
                vector.required_text in candidate
                for vector in (
                    *FROZEN_SLOTTED_CLAUSES,
                    *EVENT_INVARIANT_CLAUSES,
                    *EXCEPTION_BOUNDARY_CLAUSES,
                )
            )
            and stages == tuple(range(1, 8))
        )
    except (ValueError, TypeError):
        return False


def test_vectors_are_frozen_closed_and_have_exact_counts() -> None:
    with pytest.raises(FrozenInstanceError):
        STATUS_REASON_VECTORS[0].priority = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        AUTHORITY_FIELDS[0].field = "replacement"  # type: ignore[misc]
    with pytest.raises(TypeError):
        PUBLIC_SCHEMAS["replacement"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        FIXED_AUTHORITY["maximum_read_attempts"] = 2  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        FROZEN_SLOTTED_CLAUSES[0].name = "replacement"  # type: ignore[misc]
    with pytest.raises(TypeError):
        SAFE_FAILURE_MAPPING["snapshot_available"] = True  # type: ignore[index]

    assert tuple(map(len, PUBLIC_SCHEMAS.values())) == (1, 6, 8, 7, 8, 12, 8, 15)
    assert len(CALL_ACCOUNTING) == 11
    assert len(STATUS_REASON_VECTORS) == 9
    assert len(BOUND_VECTORS) == 17
    assert len(SHAPE_MUTATION_VECTORS) == 55
    assert len(VALUE_MUTATION_VECTORS) == 24
    assert len(EXCEPTION_BOUNDARY_VECTORS) == 2
    assert len(STAGED_DELIVERY) == 7


def test_contract_locks_exports_interfaces_and_exact_schema_rows() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "Status: G202 contract only." in text
    assert PUBLIC_INTERFACE in text
    assert VALIDATOR_INTERFACE in text
    assert SANITIZER_INTERFACE in text
    assert (
        '__all__ = (\n'
        '    "CanonicalGoldEconomicCalendarSourceAdapterResultV1",\n'
        '    "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",\n'
        ")"
    ) in text

    identity_block = _section(text, "### 5.1 Expected identity", "### 5.2 Read policy")
    policy_block = _section(text, "### 5.2 Read policy", "### 5.3 Authority capsule")
    authority_block = _section(text, "### 5.3 Authority capsule", "## 6. Private Fixture Schema")
    fixture_block = _section(
        text,
        "The top-level fixture document contains exactly these seven keys in order:",
        "Each event object contains exactly these eight keys in order:",
    )
    event_block = _section(
        text,
        "Each event object contains exactly these eight keys in order:",
        "The parser freezes one private detached document record",
    )
    snapshot_block = _section(text, "### 8.1 Calendar snapshot", "### 8.2 Upstream evidence")
    upstream_block = _section(text, "### 8.2 Upstream evidence", "### 8.3 Event source")
    result_block = _section(
        text,
        "## 9. Adapter Result Contract",
        "## 10. Status, Reason, and First-Failure Mapping",
    )

    assert _table_rows(identity_block) == _vector_rows(EXPECTED_IDENTITY_FIELDS)
    assert _table_rows(policy_block) == _vector_rows(READ_POLICY_FIELDS)
    assert _table_rows(authority_block) == _vector_rows(AUTHORITY_FIELDS)
    assert _table_rows(fixture_block) == _vector_rows(FIXTURE_FIELDS)
    assert _table_rows(event_block) == _vector_rows(EVENT_FIELDS)
    assert _table_rows(snapshot_block) == _vector_rows(SNAPSHOT_FIELDS)
    assert _table_rows(upstream_block) == _vector_rows(UPSTREAM_FIELDS)
    assert _table_rows(result_block) == _vector_rows(RESULT_FIELDS)
    assert all(vector.required_text in text for vector in FROZEN_SLOTTED_CLAUSES)


def test_server_owned_authority_path_policy_and_override_rules_are_exact() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    for part in FIXED_PATH_PARTS:
        assert f'    "{part}",' in text
    for key, value in FIXED_AUTHORITY.items():
        if key == "reference_time_utc":
            assert value.replace("tzinfo=UTC", "tzinfo=datetime.UTC") in text
        elif type(value) is int:
            assert f"`{value}`" in text or str(value) in text
        else:
            assert str(value) in text

    assert "generated_at_utc`, `coverage_start_utc`, and `coverage_end_utc` are source" in text
    assert "facts, not identity authority" in text
    assert "An exact path-type, expected-value, parent, name, extension," in text
    assert "or lexical-containment failure remains AUTHORITY_INVALID with zero attempts." in text
    assert "Every such failure is\nFIXTURE_UNAVAILABLE with exactly one read attempt." in text
    assert all(vector.fixture_reads == 0 and not vector.accepted for vector in CALLER_OVERRIDE_VECTORS)
    assert tuple(vector.attempted_authority for vector in CALLER_OVERRIDE_VECTORS) == (
        "fixture_path",
        "reference_time_utc",
        "expected_identity",
        "source_profile_version",
        "read_policy",
        "parser",
        "provider",
        "expected_status_or_reason",
    )


def test_fixture_parser_call_accounting_and_bounds_are_closed() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    accounting_block = _section(
        text,
        "### 7.1 Call accounting",
        "## 8. Exact G201 Source Construction",
    )
    for vector in CALL_ACCOUNTING:
        row = (
            f"| {vector.outcome} | {vector.fixture_reads} | {vector.parser_calls} | "
            f"{vector.result_validator_calls} |"
        )
        assert row in accounting_block

    assert "structured JSON parser that preserves object\npairs long enough to reject duplicate keys" in text
    assert "Reject a byte-order mark, trailing content," in text
    assert "duplicate keys, non-finite numeric tokens, or parser\n   ambiguity" in text
    assert "No outcome permits a\nsecond read, parser call, validator call, source, or attempt." in text

    by_name = {vector.name: vector for vector in BOUND_VECTORS}
    assert by_name["fixture_bytes_maximum"].accepted
    assert by_name["fixture_bytes_overflow"].expected_priority == 2
    assert by_name["event_count_zero"].accepted
    assert by_name["event_count_maximum"].accepted
    assert by_name["event_count_overflow"].expected_priority == 7
    assert by_name["calendar_age_maximum"].accepted
    assert by_name["calendar_age_stale"].expected_priority == 5
    assert by_name["coverage_span_maximum"].accepted
    assert by_name["coverage_span_overflow"].expected_priority == 6
    assert by_name["coverage_start_short"].expected_priority == 6
    assert by_name["coverage_end_short"].expected_priority == 6


def test_g199_codes_and_g201_source_provenance_match_real_ownership() -> None:
    contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
    g199_text = G199_CONTRACT_PATH.read_text(encoding="utf-8")
    g201_tree = ast.parse(G201_MODULE_PATH.read_text(encoding="utf-8"))
    classes = {
        node.name: node for node in g201_tree.body if isinstance(node, ast.ClassDef)
    }

    def annotation_fields(name: str) -> tuple[str, ...]:
        return tuple(
            node.target.id
            for node in classes[name].body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        )

    def has_frozen_slotted_dataclass(name: str) -> bool:
        return any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "dataclass"
            and {
                keyword.arg: keyword.value.value
                for keyword in decorator.keywords
                if keyword.arg in {"frozen", "slots"}
                and isinstance(keyword.value, ast.Constant)
            }
            == {"frozen": True, "slots": True}
            for decorator in classes[name].decorator_list
        )

    assert annotation_fields("CanonicalGoldEconomicCalendarSnapshotV1") == _field_names(
        SNAPSHOT_FIELDS
    )
    assert annotation_fields(
        "CanonicalGoldEconomicCalendarUpstreamEvidenceV1"
    ) == _field_names(UPSTREAM_FIELDS)
    assert annotation_fields("CanonicalGoldEconomicEventSourceV1") == _field_names(
        EVENT_FIELDS
    )
    assert all(
        has_frozen_slotted_dataclass(name)
        for name in (
            "CanonicalGoldEconomicCalendarSnapshotV1",
            "CanonicalGoldEconomicCalendarUpstreamEvidenceV1",
            "CanonicalGoldEconomicEventSourceV1",
        )
    )

    for code in (
        *EVENT_CATEGORY_CODES,
        *COUNTRY_CODES,
        *CURRENCY_CODES,
        *IMPACT_CODES,
        *EVENT_STATUS_CODES,
    ):
        assert code in g199_text
    for vector in EVENT_INVARIANT_CLAUSES:
        assert vector.required_text in contract_text
    assert "The adapter validates this order and never sorts," in contract_text
    assert "parser-owned container or raw document may be reachable from the result." in contract_text

    g185_text = G185_MODULE_PATH.read_text(encoding="utf-8")
    assert "_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)" in g185_text
    assert FIXED_AUTHORITY["reference_time_utc"].replace("tzinfo=UTC", "tzinfo=datetime.UTC") in contract_text


def test_status_reason_priority_reachability_and_failure_clearing_are_exact() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert _status_rows(text) == tuple(
        (vector.priority, vector.status, vector.reason)
        for vector in STATUS_REASON_VECTORS
    )
    assert tuple(vector.priority for vector in STATUS_REASON_VECTORS) == tuple(range(1, 10))
    assert len({vector.status for vector in STATUS_REASON_VECTORS}) == 9
    assert len({vector.reason for vector in STATUS_REASON_VECTORS}) == 9
    assert len({vector.owner for vector in STATUS_REASON_VECTORS}) == 9

    reachability = _section(
        text,
        "The nine categories are mutually exclusive and reachable in the frozen order:",
        "The only success mapping is:",
    )
    for phrase in (
        "exact path-value or authority mutations stop at priority 1 with zero reads",
        "filesystem-state mutations stop at priority 2 after one consumed attempt",
        "top-level document or events-container mutations stop at priority 3",
        "schema or snapshot-ID mutations stop at priority 4",
        "generated-time mutations stop at priority 5",
        "coverage-time or coverage-policy mutations stop at priority 6",
        "at priority 7",
        "independently invalid constructed source or result values stop at priority",
        "unexpected exceptions stop at priority 9",
    ):
        assert phrase in reachability

    assert "No timestamp is part of expected identity" in reachability
    assert "no event-record shape is a\ntop-level fixture-shape failure" in reachability
    assert "no filesystem-state failure is a zero-read\nauthority failure" in reachability
    assert READY_MAPPING == {
        "passed": True,
        "status_code": "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY",
        "reason_codes": (),
        "warning_codes": (),
        "snapshot_available": True,
    }
    assert FAILURE_CLEARING["snapshot"] is None
    assert FAILURE_CLEARING["snapshot_available"] is False
    assert FAILURE_CLEARING["warning_codes"] == ()


def test_shape_and_value_mutations_are_concrete_and_fail_closed() -> None:
    assert {vector.schema for vector in SHAPE_MUTATION_VECTORS} == {
        "expected_identity",
        "read_policy",
        "authority",
        "fixture_document",
        "fixture_event",
        "calendar_snapshot",
        "upstream_evidence",
        "adapter_result",
    }
    for schema in {vector.schema for vector in SHAPE_MUTATION_VECTORS}:
        vectors = [vector for vector in SHAPE_MUTATION_VECTORS if vector.schema == schema]
        expected_mutations = {
            "missing",
            "extra",
            "duplicate",
            "alias",
            "case_change",
            "wrong_container",
        }
        if schema != "expected_identity":
            expected_mutations.add("reordered")
        assert {vector.mutation for vector in vectors} == expected_mutations
        missing = next(vector for vector in vectors if vector.mutation == "missing")
        assert missing.observed_fields == missing.expected_fields[:-1]
        reordered = [vector for vector in vectors if vector.mutation == "reordered"]
        assert all(vector.observed_fields != vector.expected_fields for vector in reordered)
        assert all(
            len(vector.observed_fields) == len(vector.expected_fields)
            for vector in reordered
        )
        assert all(
            vector.observed_fields != ()
            for vector in vectors
            if vector.mutation != "missing"
        )
        assert all(vector.expected_status.startswith("CANONICAL_GOLD_") for vector in vectors)
        assert all(vector.expected_reason.startswith("GOLD_ECONOMIC_CALENDAR_") for vector in vectors)

    by_name = {vector.name: vector for vector in VALUE_MUTATION_VECTORS}
    assert type(by_name["identity_subclass"].invalid_value) is StrictStringSubclass
    assert type(by_name["read_policy_integer_subclass"].invalid_value) is StrictIntSubclass
    assert type(by_name["event_revision_bool"].invalid_value) is bool
    assert type(by_name["event_revision_integer_subclass"].invalid_value) is StrictIntSubclass
    assert type(by_name["result_reason_tuple_subclass"].invalid_value) is StrictTupleSubclass
    assert {
        "event_revision_negative",
        "event_timestamp_invalid_date",
        "event_country_unknown",
        "event_currency_case_change",
        "event_category_case_change",
        "event_impact_unknown",
        "event_status_unknown",
        "event_duplicate_ids",
        "event_order_descending",
        "event_tie_order_descending",
        "event_outside_coverage",
        "event_wrong_element",
    }.issubset(by_name)
    assert {vector.expected_priority for vector in VALUE_MUTATION_VECTORS} == {
        1,
        3,
        4,
        5,
        6,
        7,
        8,
    }
    for vector in VALUE_MUTATION_VECTORS:
        expected = STATUS_REASON_VECTORS[vector.expected_priority - 1]
        assert vector.expected_status == expected.status
        assert vector.expected_reason == expected.reason


def test_safety_sensitive_output_and_detached_object_rules_are_closed() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    safety_block = _section(text, "## 11. Fixed Safety Envelope", "## 12. Fail-Closed and Isolation Rules")
    for field, value in SAFETY_FLAGS.items():
        assert f"| `{field}` | `{value}` |" in safety_block
    assert "contains_raw_provider_payload is False" in safety_block
    assert "Every failure\nhas `snapshot_available is False` and `snapshot is None`." in text
    assert "Warning codes are\nalways the exact empty built-in tuple." in text
    assert "Every returned\nresult, snapshot, upstream record, event tuple, and event record is fresh and\ndetached." in text
    assert "must be equal but must not share result or nested object identity." in text
    normalized_text = " ".join(text.split())
    for term in SENSITIVE_TERMS:
        assert term in normalized_text
    assert "must not enter the result or a log" in text
    assert all(
        vector.required_text in text for vector in EXCEPTION_BOUNDARY_CLAUSES
    )
    assert SAFE_FAILURE_MAPPING == {
        "passed": False,
        "status_code": "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_SAFE_FAILURE",
        "reason_codes": ("GOLD_ECONOMIC_CALENDAR_EXCEPTION_SANITIZED",),
        "warning_codes": (),
        "snapshot_available": False,
        "snapshot": None,
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
    for vector in EXCEPTION_BOUNDARY_VECTORS:
        assert vector.expected_status == SAFE_FAILURE_MAPPING["status_code"]
        assert vector.expected_reason == SAFE_FAILURE_MAPPING["reason_codes"][0]
        assert vector.snapshot_available is False
        assert vector.snapshot is None
        assert vector.leaks_internal_state is False


def test_contract_oracle_rejects_authority_ownership_mapping_and_stage_bypasses() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert _contract_oracle(text)

    identity_row = "| 1 | `calendar_snapshot_id` | built-in `str` |"
    timestamp_row = "| 2 | `generated_at_utc` | built-in `str` |"
    mutations = (
        text.replace(identity_row, identity_row + "\n" + timestamp_row, 1),
        text.replace(
            "Failure returns AUTHORITY_INVALID with zero reads.",
            "Failure returns AUTHORITY_INVALID with one read.",
            1,
        ),
        text.replace(
            "No event-record failure may be relabeled as FIXTURE_INVALID.",
            "Event-record failures may be relabeled as FIXTURE_INVALID.",
            1,
        ),
        text.replace(
            "    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,\n) -> bool:",
            ") -> bool:",
            1,
        ),
        text.replace(
            STATUS_REASON_VECTORS[4].status,
            STATUS_REASON_VECTORS[5].status,
            1,
        ),
        *(
            text.replace(vector.required_text, vector.invalid_text, 1)
            for vector in (
                *FROZEN_SLOTTED_CLAUSES,
                *EVENT_INVARIANT_CLAUSES,
                *EXCEPTION_BOUNDARY_CLAUSES,
            )
        ),
        text.replace(
            "7. a separately versioned ReplayRunner W6 stage before W7.",
            "8. provider activation.",
            1,
        ),
    )
    assert all(candidate != text for candidate in mutations)
    assert all(not _contract_oracle(candidate) for candidate in mutations)


def test_staged_delivery_isolation_and_no_runtime_import_remain_closed() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    staged_block = _section(
        text,
        "## 14. Required Staged Delivery",
        "## 15. WBS and Capability Boundaries",
    )
    assert tuple(
        int(value) for value in re.findall(r"^(\d+)\.\s", staged_block, re.MULTILINE)
    ) == tuple(range(1, 8))
    for phrase in (
        "immutable tests-only contract vectors for G202",
        "production result and private authority types plus the bounded adapter",
        "fixed checked-in offline calendar fixture and controlled adapter tests",
        "genuine offline composition through G185 -> G178",
        "deterministic non-activating verification of that exact composition",
        "separately contracted later W6 facts and features",
        "separately versioned ReplayRunner W6 stage before W7",
    ):
        assert phrase in staged_block

    assert "No stage silently includes the next." in staged_block
    assert "W6 remains `TESTS_ONLY`." in text
    assert "Reader activation, provider activation, real MT4, EA, order, execution," in text
    assert "vectors, implementation, fixture evidence, composition, verification," in text
    assert "ReplayRunner W6, activation, and later features remain unimplemented" in text

    tree = ast.parse(TEST_PATH.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert all(not module.startswith("app") for module in imported_modules)
    assert "canonical_gold_economic_calendar_source_adapter" not in imported_modules

    defined_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert "build_server_owned_canonical_gold_economic_calendar_snapshot_v1" not in defined_names
    assert "CanonicalGoldEconomicCalendarSourceAdapterResultV1" not in defined_names
    assert "_CanonicalGoldEconomicCalendarSourceAuthorityV1" not in defined_names
    assert "_is_safe_canonical_gold_economic_calendar_source_adapter_result_v1" not in defined_names
    assert "_build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1" not in defined_names

    source = TEST_PATH.read_text(encoding="utf-8")
    source.encode("ascii")
    assert "unittest.mock" not in imported_modules
    assert "importlib" not in imported_modules
    argument_names = {
        argument.arg
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
    }
    assert "monkeypatch" not in argument_names
