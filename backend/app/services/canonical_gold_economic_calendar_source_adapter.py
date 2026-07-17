from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path as _Path
import re
import stat

from app.services.canonical_gold_economic_window_facts import (
    CanonicalGoldEconomicCalendarSnapshotV1,
    CanonicalGoldEconomicCalendarUpstreamEvidenceV1,
    CanonicalGoldEconomicEventSourceV1,
    _is_safe_canonical_gold_economic_calendar_snapshot_v1,
)


@dataclass(frozen=True, slots=True)
class _CanonicalGoldEconomicCalendarExpectedIdentityV1:
    calendar_snapshot_id: str


@dataclass(frozen=True, slots=True)
class _CanonicalGoldEconomicCalendarReadPolicyV1:
    maximum_fixture_bytes: int
    maximum_calendar_events: int
    maximum_calendar_age_microseconds: int
    maximum_coverage_span_microseconds: int
    search_horizon_microseconds: int
    maximum_read_attempts: int


@dataclass(frozen=True, slots=True)
class _CanonicalGoldEconomicCalendarSourceAuthorityV1:
    authority_token: object
    allowed_root: _Path
    fixture_path: _Path
    reference_time_utc: datetime
    expected_identity: _CanonicalGoldEconomicCalendarExpectedIdentityV1
    read_policy: _CanonicalGoldEconomicCalendarReadPolicyV1
    calendar_schema_version: str
    source_profile_version: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    contract_version: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    snapshot_available: bool
    snapshot: CanonicalGoldEconomicCalendarSnapshotV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


@dataclass(frozen=True, slots=True)
class _JsonObjectV1:
    pairs: tuple[tuple[str, object], ...]


@dataclass(frozen=True, slots=True)
class _FixtureDocumentV1:
    fixture_contract_version: str
    calendar_schema_version: str
    calendar_snapshot_id: str
    generated_at_utc: str
    coverage_start_utc: str
    coverage_end_utc: str
    events: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class _FixtureEventV1:
    event_id: str
    scheduled_at_utc: str
    country_code: str
    currency_code: str
    event_category_code: str
    impact_code: str
    source_revision: int
    event_status_code: str


__all__ = (
    "CanonicalGoldEconomicCalendarSourceAdapterResultV1",
    "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
)


_CONTRACT_VERSION = "1.0"
_SOURCE_PROFILE_VERSION = "canonical_gold_economic_calendar_source_v1"
_READY_STATUS = "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
_FIXED_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
_FIXED_PATH_PARTS = (
    "docs",
    "architecture",
    "fixtures",
    "canonical-gold-economic-calendar-v1",
    "economic_calendar.json",
)
_REPOSITORY_ROOT = _Path(__file__).resolve().parents[3]
_EXPECTED_ALLOWED_ROOT = _REPOSITORY_ROOT.joinpath(*_FIXED_PATH_PARTS[:3])
_EXPECTED_FIXTURE_PATH = _REPOSITORY_ROOT.joinpath(*_FIXED_PATH_PARTS)
_AUTHORITY_TOKEN = object()
_EXPECTED_IDENTITY = _CanonicalGoldEconomicCalendarExpectedIdentityV1(
    calendar_snapshot_id="canonical-gold-economic-calendar-docs-fixture-v1",
)
_READ_POLICY = _CanonicalGoldEconomicCalendarReadPolicyV1(
    maximum_fixture_bytes=1_048_576,
    maximum_calendar_events=512,
    maximum_calendar_age_microseconds=300_000_000,
    maximum_coverage_span_microseconds=259_200_000_000,
    search_horizon_microseconds=86_400_000_000,
    maximum_read_attempts=1,
)

_FAILURES = (
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_AUTHORITY_INVALID",
        "GOLD_ECONOMIC_CALENDAR_AUTHORITY_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FIXTURE_UNAVAILABLE",
        "GOLD_ECONOMIC_CALENDAR_FIXTURE_UNAVAILABLE",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FIXTURE_INVALID",
        "GOLD_ECONOMIC_CALENDAR_FIXTURE_INPUT_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_IDENTITY_INVALID",
        "GOLD_ECONOMIC_CALENDAR_IDENTITY_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_FRESHNESS_INVALID",
        "GOLD_ECONOMIC_CALENDAR_FRESHNESS_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_COVERAGE_INVALID",
        "GOLD_ECONOMIC_CALENDAR_COVERAGE_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_EVENT_INVALID",
        "GOLD_ECONOMIC_CALENDAR_EVENT_INPUT_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_RESULT_INVALID",
        "GOLD_ECONOMIC_CALENDAR_RESULT_INVALID",
    ),
    (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_SAFE_FAILURE",
        "GOLD_ECONOMIC_CALENDAR_EXCEPTION_SANITIZED",
    ),
)

_AUTHORITY_FIELDS = (
    "authority_token",
    "allowed_root",
    "fixture_path",
    "reference_time_utc",
    "expected_identity",
    "read_policy",
    "calendar_schema_version",
    "source_profile_version",
)
_EXPECTED_IDENTITY_FIELDS = ("calendar_snapshot_id",)
_READ_POLICY_FIELDS = (
    "maximum_fixture_bytes",
    "maximum_calendar_events",
    "maximum_calendar_age_microseconds",
    "maximum_coverage_span_microseconds",
    "search_horizon_microseconds",
    "maximum_read_attempts",
)
_RESULT_FIELDS = (
    "contract_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "snapshot_available",
    "snapshot",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
_FIXTURE_FIELDS = (
    "fixture_contract_version",
    "calendar_schema_version",
    "calendar_snapshot_id",
    "generated_at_utc",
    "coverage_start_utc",
    "coverage_end_utc",
    "events",
)
_EVENT_FIELDS = (
    "event_id",
    "scheduled_at_utc",
    "country_code",
    "currency_code",
    "event_category_code",
    "impact_code",
    "source_revision",
    "event_status_code",
)
_EVENT_CATEGORIES = (
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
_IMPACT_CODES = ("LOW", "MEDIUM", "HIGH")
_EVENT_STATUS_CODES = ("SCHEDULED", "CANCELLED")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$", re.ASCII)
_UTC_Z_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$",
    re.ASCII,
)


def build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
    *,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    try:
        return _build_bounded_adapter_result(authority=authority)
    except Exception:
        try:
            return _safe_failure()
        except Exception:
            return _failure(*_FAILURES[8])


def _build_bounded_adapter_result(
    *,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    if not _valid_authority(authority):
        return _failure(*_FAILURES[0])
    authority_before = _authority_snapshot(authority)
    try:
        fixture_bytes = _read_fixture_bytes(authority=authority)
    except _FixtureUnavailable:
        return _failure(*_FAILURES[1])
    except Exception:
        return _safe_failure()
    try:
        parsed = _parse_fixture_document(fixture_bytes=fixture_bytes)
        document = _freeze_fixture_document(parsed=parsed)
    except _FixtureInvalid:
        return _failure(*_FAILURES[2])
    except Exception:
        return _safe_failure()

    if not _valid_fixture_identity(document=document, authority=authority):
        return _failure(*_FAILURES[3])
    generated = _parse_utc_z(document.generated_at_utc)
    if not _valid_freshness(generated=generated, authority=authority):
        return _failure(*_FAILURES[4])
    coverage_start = _parse_utc_z(document.coverage_start_utc)
    coverage_end = _parse_utc_z(document.coverage_end_utc)
    if not _valid_coverage(
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        authority=authority,
    ):
        return _failure(*_FAILURES[5])
    try:
        events = _freeze_fixture_events(
            values=document.events,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            maximum_events=authority.read_policy.maximum_calendar_events,
        )
    except _EventInvalid:
        return _failure(*_FAILURES[6])
    except Exception:
        return _safe_failure()

    document_before = _document_snapshot(document=document, events=events)
    if (
        _authority_snapshot(authority) != authority_before
        or _document_snapshot(document=document, events=events) != document_before
    ):
        return _failure(*_FAILURES[3])
    try:
        snapshot = _build_snapshot(
            authority=authority,
            document=document,
            events=events,
        )
        if (
            _authority_snapshot(authority) != authority_before
            or _document_snapshot(document=document, events=events) != document_before
        ):
            return _failure(*_FAILURES[3])
        result = _ready(snapshot=snapshot)
        valid = _is_safe_canonical_gold_economic_calendar_source_adapter_result_v1(
            adapter_result=result,
            authority=authority,
        )
    except Exception:
        return _safe_failure()
    return result if valid is True else _failure(*_FAILURES[7])


def _valid_authority(value: object) -> bool:
    try:
        concrete_path_type = type(_Path())
        if not (
            _is_exact_record(value, _CanonicalGoldEconomicCalendarSourceAuthorityV1, _AUTHORITY_FIELDS)
            and value.authority_token is _AUTHORITY_TOKEN
            and type(value.authority_token) is object
            and type(value.allowed_root) is concrete_path_type
            and type(value.fixture_path) is concrete_path_type
            and value.allowed_root == _EXPECTED_ALLOWED_ROOT
            and value.fixture_path == _EXPECTED_FIXTURE_PATH
            and value.fixture_path.parent == _EXPECTED_FIXTURE_PATH.parent
            and value.fixture_path.name == "economic_calendar.json"
            and value.fixture_path.suffix == ".json"
            and value.fixture_path.relative_to(value.allowed_root)
            == _Path(*_FIXED_PATH_PARTS[3:])
            and type(value.reference_time_utc) is datetime
            and value.reference_time_utc == _FIXED_REFERENCE_TIME
            and value.reference_time_utc.tzinfo is not None
            and value.reference_time_utc.utcoffset() == timedelta(0)
            and _is_exact_record(
                value.expected_identity,
                _CanonicalGoldEconomicCalendarExpectedIdentityV1,
                _EXPECTED_IDENTITY_FIELDS,
            )
            and type(value.expected_identity.calendar_snapshot_id) is str
            and value.expected_identity == _EXPECTED_IDENTITY
            and _is_identifier(value.expected_identity.calendar_snapshot_id, 16, 64)
            and _is_exact_record(
                value.read_policy,
                _CanonicalGoldEconomicCalendarReadPolicyV1,
                _READ_POLICY_FIELDS,
            )
            and value.read_policy == _READ_POLICY
            and all(
                type(getattr(value.read_policy, field)) is int
                for field in _READ_POLICY_FIELDS
            )
            and type(value.calendar_schema_version) is str
            and value.calendar_schema_version == _CONTRACT_VERSION
            and type(value.source_profile_version) is str
            and value.source_profile_version == _SOURCE_PROFILE_VERSION
        ):
            return False
        return True
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def _authority_snapshot(
    value: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> tuple[object, ...]:
    return (
        value.authority_token,
        type(value.allowed_root),
        value.allowed_root,
        type(value.fixture_path),
        value.fixture_path,
        type(value.reference_time_utc),
        value.reference_time_utc,
        type(value.expected_identity),
        value.expected_identity.calendar_snapshot_id,
        type(value.read_policy),
        *(getattr(value.read_policy, field) for field in _READ_POLICY_FIELDS),
        value.calendar_schema_version,
        value.source_profile_version,
    )


def _read_fixture_bytes(
    *,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> bytes:
    try:
        root_status = authority.allowed_root.lstat()
        if authority.allowed_root.is_symlink() or _is_reparse_point(root_status):
            raise _FixtureUnavailable
        canonical_root = authority.allowed_root.resolve(strict=True)
        relative = authority.fixture_path.relative_to(authority.allowed_root)
        current = authority.allowed_root
        for part in relative.parts:
            current = current / part
            status = current.lstat()
            if current.is_symlink() or _is_reparse_point(status):
                raise _FixtureUnavailable
        before = authority.fixture_path.stat()
        canonical_fixture = authority.fixture_path.resolve(strict=True)
        if (
            not canonical_fixture.is_relative_to(canonical_root)
            or not stat.S_ISREG(before.st_mode)
            or not 1 <= before.st_size <= authority.read_policy.maximum_fixture_bytes
        ):
            raise _FixtureUnavailable
        with authority.fixture_path.open("rb") as handle:
            payload = handle.read(authority.read_policy.maximum_fixture_bytes + 1)
        after = authority.fixture_path.stat()
        canonical_root_after = authority.allowed_root.resolve(strict=True)
        canonical_fixture_after = authority.fixture_path.resolve(strict=True)
        if (
            type(payload) is not bytes
            or not 1 <= len(payload) <= authority.read_policy.maximum_fixture_bytes
            or len(payload) != before.st_size
            or _file_identity(before) != _file_identity(after)
            or canonical_root_after != canonical_root
            or canonical_fixture_after != canonical_fixture
            or authority.fixture_path.is_symlink()
            or _is_reparse_point(after)
        ):
            raise _FixtureUnavailable
        return payload
    except _FixtureUnavailable:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        raise _FixtureUnavailable from None


def _file_identity(value: object) -> tuple[object, ...]:
    return (
        getattr(value, "st_dev", None),
        getattr(value, "st_ino", None),
        getattr(value, "st_size", None),
        getattr(value, "st_mtime_ns", None),
        getattr(value, "st_mode", None),
    )


def _is_reparse_point(value: object) -> bool:
    attributes = getattr(value, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return type(attributes) is int and reparse_flag != 0 and bool(attributes & reparse_flag)


def _parse_fixture_document(*, fixture_bytes: bytes) -> object:
    if type(fixture_bytes) is not bytes or fixture_bytes.startswith(b"\xef\xbb\xbf"):
        raise _FixtureInvalid
    try:
        text = fixture_bytes.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_json_object,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise _FixtureInvalid from None


def _json_object(pairs: list[tuple[str, object]]) -> _JsonObjectV1:
    return _JsonObjectV1(pairs=tuple(pairs))


def _reject_non_finite(_value: str) -> object:
    raise ValueError


def _freeze_fixture_document(*, parsed: object) -> _FixtureDocumentV1:
    if type(parsed) is not _JsonObjectV1 or _json_keys(parsed) != _FIXTURE_FIELDS:
        raise _FixtureInvalid
    values = tuple(value for _, value in parsed.pairs)
    if not (
        all(type(value) is str for value in values[:6])
        and type(values[6]) is list
        and values[0] == _CONTRACT_VERSION
    ):
        raise _FixtureInvalid
    return _FixtureDocumentV1(
        fixture_contract_version=values[0],
        calendar_schema_version=values[1],
        calendar_snapshot_id=values[2],
        generated_at_utc=values[3],
        coverage_start_utc=values[4],
        coverage_end_utc=values[5],
        events=tuple(values[6]),
    )


def _valid_fixture_identity(
    *,
    document: _FixtureDocumentV1,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> bool:
    return (
        document.calendar_schema_version == authority.calendar_schema_version
        and document.calendar_snapshot_id
        == authority.expected_identity.calendar_snapshot_id
        and _is_identifier(document.calendar_snapshot_id, 16, 64)
        and authority.source_profile_version == _SOURCE_PROFILE_VERSION
    )


def _valid_freshness(
    *,
    generated: datetime | None,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> bool:
    if generated is None:
        return False
    age = _microseconds_between(authority.reference_time_utc, generated)
    return 0 <= age <= authority.read_policy.maximum_calendar_age_microseconds


def _valid_coverage(
    *,
    coverage_start: datetime | None,
    coverage_end: datetime | None,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> bool:
    if coverage_start is None or coverage_end is None or coverage_start >= coverage_end:
        return False
    try:
        horizon = timedelta(microseconds=authority.read_policy.search_horizon_microseconds)
        required_start = authority.reference_time_utc - horizon
        required_end = authority.reference_time_utc + horizon
    except OverflowError:
        return False
    return (
        coverage_start <= required_start
        and coverage_end >= required_end
        and _microseconds_between(coverage_end, coverage_start)
        <= authority.read_policy.maximum_coverage_span_microseconds
    )


def _freeze_fixture_events(
    *,
    values: tuple[object, ...],
    coverage_start: datetime | None,
    coverage_end: datetime | None,
    maximum_events: int,
) -> tuple[_FixtureEventV1, ...]:
    if (
        type(values) is not tuple
        or type(maximum_events) is not int
        or coverage_start is None
        or coverage_end is None
        or len(values) > maximum_events
    ):
        raise _EventInvalid
    output: list[_FixtureEventV1] = []
    previous_key: tuple[datetime, str] | None = None
    event_ids: set[str] = set()
    for value in values:
        event = _freeze_fixture_event(value=value)
        scheduled = _parse_utc_z(event.scheduled_at_utc)
        if not (
            _is_identifier(event.event_id, 8, 64)
            and scheduled is not None
            and coverage_start <= scheduled < coverage_end
            and event.country_code == "US"
            and event.currency_code == "USD"
            and event.event_category_code in _EVENT_CATEGORIES
            and event.impact_code in _IMPACT_CODES
            and event.source_revision >= 0
            and event.event_status_code in _EVENT_STATUS_CODES
            and event.event_id not in event_ids
        ):
            raise _EventInvalid
        key = (scheduled, event.event_id)
        if previous_key is not None and key <= previous_key:
            raise _EventInvalid
        output.append(event)
        previous_key = key
        event_ids.add(event.event_id)
    return tuple(output)


def _freeze_fixture_event(*, value: object) -> _FixtureEventV1:
    if type(value) is not _JsonObjectV1 or _json_keys(value) != _EVENT_FIELDS:
        raise _EventInvalid
    values = tuple(child for _, child in value.pairs)
    if not (
        all(type(child) is str for child in values[:6])
        and type(values[6]) is int
        and type(values[7]) is str
    ):
        raise _EventInvalid
    return _FixtureEventV1(*values)


def _json_keys(value: _JsonObjectV1) -> tuple[str, ...]:
    return tuple(key for key, _ in value.pairs)


def _document_snapshot(
    *,
    document: _FixtureDocumentV1,
    events: tuple[_FixtureEventV1, ...],
) -> tuple[object, ...]:
    return (
        document.fixture_contract_version,
        document.calendar_schema_version,
        document.calendar_snapshot_id,
        document.generated_at_utc,
        document.coverage_start_utc,
        document.coverage_end_utc,
        tuple(tuple(getattr(event, field) for field in _EVENT_FIELDS) for event in events),
    )


def _build_snapshot(
    *,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
    document: _FixtureDocumentV1,
    events: tuple[_FixtureEventV1, ...],
) -> CanonicalGoldEconomicCalendarSnapshotV1:
    source_events = tuple(
        CanonicalGoldEconomicEventSourceV1(
            event_id=event.event_id,
            scheduled_at_utc=event.scheduled_at_utc,
            country_code=event.country_code,
            currency_code=event.currency_code,
            event_category_code=event.event_category_code,
            impact_code=event.impact_code,
            source_revision=event.source_revision,
            event_status_code=event.event_status_code,
        )
        for event in events
    )
    upstream = CanonicalGoldEconomicCalendarUpstreamEvidenceV1(
        adapter_passed=True,
        adapter_status_code=_READY_STATUS,
        schema_validated=True,
        identity_validated=True,
        timestamps_normalized=True,
        same_snapshot_bound=True,
        warning_codes=(),
        raw_payload_discarded=True,
    )
    return CanonicalGoldEconomicCalendarSnapshotV1(
        contract_version=_CONTRACT_VERSION,
        calendar_schema_version=authority.calendar_schema_version,
        calendar_snapshot_id=authority.expected_identity.calendar_snapshot_id,
        source_profile_version=authority.source_profile_version,
        generated_at_utc=document.generated_at_utc,
        coverage_start_utc=document.coverage_start_utc,
        coverage_end_utc=document.coverage_end_utc,
        events=source_events,
        upstream_evidence=upstream,
        read_only=True,
        demo_only=True,
        contains_raw_provider_payload=False,
    )


def _is_safe_canonical_gold_economic_calendar_source_adapter_result_v1(
    *,
    adapter_result: object,
    authority: _CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> bool:
    try:
        if not (
            _valid_authority(authority)
            and _is_exact_record(
                adapter_result,
                CanonicalGoldEconomicCalendarSourceAdapterResultV1,
                _RESULT_FIELDS,
            )
            and type(adapter_result.contract_version) is str
            and type(adapter_result.passed) is bool
            and type(adapter_result.status_code) is str
            and _is_string_tuple(adapter_result.reason_codes)
            and _is_string_tuple(adapter_result.warning_codes)
            and type(adapter_result.snapshot_available) is bool
            and (
                adapter_result.snapshot is None
                or type(adapter_result.snapshot)
                is CanonicalGoldEconomicCalendarSnapshotV1
            )
            and all(
                type(getattr(adapter_result, field)) is bool
                for field in _RESULT_FIELDS[7:]
            )
            and adapter_result.contract_version == _CONTRACT_VERSION
            and adapter_result.warning_codes == ()
            and _has_safety_flags(adapter_result)
        ):
            return False
        if adapter_result.passed is True:
            return (
                adapter_result.status_code == _READY_STATUS
                and adapter_result.reason_codes == ()
                and adapter_result.snapshot_available is True
                and type(adapter_result.snapshot)
                is CanonicalGoldEconomicCalendarSnapshotV1
                and _is_safe_canonical_gold_economic_calendar_snapshot_v1(
                    economic_calendar_snapshot=adapter_result.snapshot,
                    reference_time_utc=authority.reference_time_utc,
                    expected_calendar_snapshot_id=(
                        authority.expected_identity.calendar_snapshot_id
                    ),
                    expected_calendar_schema_version=(
                        authority.calendar_schema_version
                    ),
                    expected_source_profile_version=authority.source_profile_version,
                    maximum_calendar_age_microseconds=(
                        authority.read_policy.maximum_calendar_age_microseconds
                    ),
                    maximum_coverage_span_microseconds=(
                        authority.read_policy.maximum_coverage_span_microseconds
                    ),
                    search_horizon_microseconds=(
                        authority.read_policy.search_horizon_microseconds
                    ),
                    maximum_calendar_events=(
                        authority.read_policy.maximum_calendar_events
                    ),
                )
            )
        return (
            adapter_result.passed is False
            and adapter_result.snapshot_available is False
            and adapter_result.snapshot is None
            and len(adapter_result.reason_codes) == 1
            and (adapter_result.status_code, adapter_result.reason_codes[0])
            in _FAILURES
        )
    except Exception:
        return False


def _build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1(
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    return _failure(*_FAILURES[8])


def _ready(
    *,
    snapshot: CanonicalGoldEconomicCalendarSnapshotV1,
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    return CanonicalGoldEconomicCalendarSourceAdapterResultV1(
        contract_version=_CONTRACT_VERSION,
        passed=True,
        status_code=_READY_STATUS,
        reason_codes=(),
        warning_codes=(),
        snapshot_available=True,
        snapshot=snapshot,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _failure(
    status: str,
    reason: str,
) -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    return CanonicalGoldEconomicCalendarSourceAdapterResultV1(
        contract_version=_CONTRACT_VERSION,
        passed=False,
        status_code=status,
        reason_codes=(reason,),
        warning_codes=(),
        snapshot_available=False,
        snapshot=None,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )


def _safe_failure() -> CanonicalGoldEconomicCalendarSourceAdapterResultV1:
    try:
        result = _build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1()
        if _fixed_safe_failure_is_valid(result):
            return result
    except Exception:
        pass
    return _failure(*_FAILURES[8])


def _fixed_safe_failure_is_valid(value: object) -> bool:
    try:
        return (
            _is_exact_record(
                value,
                CanonicalGoldEconomicCalendarSourceAdapterResultV1,
                _RESULT_FIELDS,
            )
            and value.contract_version == _CONTRACT_VERSION
            and value.passed is False
            and (value.status_code, value.reason_codes) == (
                _FAILURES[8][0],
                (_FAILURES[8][1],),
            )
            and value.warning_codes == ()
            and value.snapshot_available is False
            and value.snapshot is None
            and _has_safety_flags(value)
        )
    except Exception:
        return False


def _has_safety_flags(value: object) -> bool:
    return (
        value.read_only is True
        and value.demo_only is True
        and value.is_tradable is False
        and value.can_execute is False
        and value.is_trading_permission is False
        and value.is_execution_instruction is False
        and value.allowed_to_call_ea is False
        and value.allowed_to_modify_risk is False
    )


def _is_exact_record(value: object, expected: type[object], fields: tuple[str, ...]) -> bool:
    return type(value) is expected and getattr(type(value), "__slots__", None) == fields


def _is_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _parse_utc_z(value: object) -> datetime | None:
    if (
        type(value) is not str
        or not value.isascii()
        or _UTC_Z_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    return parsed.astimezone(UTC)


def _microseconds_between(later: datetime, earlier: datetime) -> int:
    delta = later - earlier
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _is_identifier(value: object, minimum: int, maximum: int) -> bool:
    return (
        type(value) is str
        and value.isascii()
        and minimum <= len(value) <= maximum
        and _IDENTIFIER_PATTERN.fullmatch(value) is not None
    )


class _FixtureUnavailable(Exception):
    pass


class _FixtureInvalid(Exception):
    pass


class _EventInvalid(Exception):
    pass
