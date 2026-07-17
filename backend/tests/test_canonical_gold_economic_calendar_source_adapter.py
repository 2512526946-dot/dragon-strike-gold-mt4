from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
import inspect
import json
from pathlib import Path

import pytest

from app.services import canonical_gold_economic_calendar_source_adapter as adapter
from app.services import canonical_gold_economic_window_facts as economic_facts


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


class StrictStringSubclass(str):
    pass


class StrictIntSubclass(int):
    pass


def test_production_types_exports_and_interfaces_are_exact() -> None:
    assert adapter.__all__ == (
        "CanonicalGoldEconomicCalendarSourceAdapterResultV1",
        "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
    )
    expected = {
        adapter._CanonicalGoldEconomicCalendarExpectedIdentityV1: (
            "calendar_snapshot_id",
        ),
        adapter._CanonicalGoldEconomicCalendarReadPolicyV1: (
            "maximum_fixture_bytes",
            "maximum_calendar_events",
            "maximum_calendar_age_microseconds",
            "maximum_coverage_span_microseconds",
            "search_horizon_microseconds",
            "maximum_read_attempts",
        ),
        adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1: (
            "authority_token",
            "allowed_root",
            "fixture_path",
            "reference_time_utc",
            "expected_identity",
            "read_policy",
            "calendar_schema_version",
            "source_profile_version",
        ),
        adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1: _RESULT_FIELDS,
    }
    samples = {
        adapter._CanonicalGoldEconomicCalendarExpectedIdentityV1: (
            adapter._EXPECTED_IDENTITY
        ),
        adapter._CanonicalGoldEconomicCalendarReadPolicyV1: adapter._READ_POLICY,
        adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1: _authority(),
        adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1: (
            adapter._build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1()
        ),
    }
    annotations = {
        adapter._CanonicalGoldEconomicCalendarExpectedIdentityV1: ("str",),
        adapter._CanonicalGoldEconomicCalendarReadPolicyV1: ("int",) * 6,
        adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1: (
            "object",
            "_Path",
            "_Path",
            "datetime",
            "_CanonicalGoldEconomicCalendarExpectedIdentityV1",
            "_CanonicalGoldEconomicCalendarReadPolicyV1",
            "str",
            "str",
        ),
        adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1: (
            "str",
            "bool",
            "str",
            "tuple[str, ...]",
            "tuple[str, ...]",
            "bool",
            "CanonicalGoldEconomicCalendarSnapshotV1 | None",
            "bool",
            "bool",
            "bool",
            "bool",
            "bool",
            "bool",
            "bool",
            "bool",
        ),
    }
    for production_type, field_names in expected.items():
        assert tuple(field.name for field in fields(production_type)) == field_names
        assert production_type.__slots__ == field_names
        assert tuple(production_type.__annotations__.values()) == annotations[production_type]
        assert not hasattr(samples[production_type], "__dict__")
        with pytest.raises(FrozenInstanceError):
            setattr(samples[production_type], field_names[0], "changed")

    public_signature = inspect.signature(
        adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1
    )
    assert tuple(public_signature.parameters) == ("authority",)
    assert public_signature.parameters["authority"].kind is inspect.Parameter.KEYWORD_ONLY
    assert str(public_signature.return_annotation) == (
        "CanonicalGoldEconomicCalendarSourceAdapterResultV1"
    )
    validator_signature = inspect.signature(
        adapter._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1
    )
    assert tuple(validator_signature.parameters) == ("adapter_result", "authority")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in validator_signature.parameters.values()
    )
    assert inspect.signature(
        adapter._build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1
    ).parameters == {}


def test_ready_path_is_single_attempt_fresh_detached_and_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority()
    fixture_bytes = _fixture_bytes()
    fixture_before = bytes(fixture_bytes)
    authority_before = _authority_values(authority)
    calls: list[str] = []
    original_parser = adapter._parse_fixture_document
    original_validator = (
        adapter._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1
    )

    def read_once(*, authority: object) -> bytes:
        assert authority is _authority_reference
        calls.append("read")
        return fixture_bytes

    def parse_once(*, fixture_bytes: bytes) -> object:
        calls.append("parse")
        return original_parser(fixture_bytes=fixture_bytes)

    def validate_once(*, adapter_result: object, authority: object) -> bool:
        calls.append("validate")
        assert authority is _authority_reference
        return original_validator(adapter_result=adapter_result, authority=authority)

    _authority_reference = authority
    monkeypatch.setattr(adapter, "_read_fixture_bytes", read_once)
    monkeypatch.setattr(adapter, "_parse_fixture_document", parse_once)
    monkeypatch.setattr(
        adapter,
        "_is_safe_canonical_gold_economic_calendar_source_adapter_result_v1",
        validate_once,
    )
    first = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )
    second = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )

    assert calls == ["read", "parse", "validate", "read", "parse", "validate"]
    assert first == second
    assert first is not second
    assert first.passed is first.snapshot_available is True
    assert first.status_code == "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
    assert first.reason_codes == first.warning_codes == ()
    assert type(first.snapshot) is economic_facts.CanonicalGoldEconomicCalendarSnapshotV1
    assert type(second.snapshot) is economic_facts.CanonicalGoldEconomicCalendarSnapshotV1
    assert first.snapshot is not second.snapshot
    assert first.snapshot.events is not second.snapshot.events
    assert first.snapshot.upstream_evidence is not second.snapshot.upstream_evidence
    assert all(
        left is not right
        for left, right in zip(first.snapshot.events, second.snapshot.events, strict=True)
    )
    assert fixture_bytes == fixture_before
    assert _authority_values(authority) == authority_before
    assert first.snapshot.calendar_snapshot_id == (
        "canonical-gold-economic-calendar-docs-fixture-v1"
    )
    assert first.snapshot.source_profile_version == (
        "canonical_gold_economic_calendar_source_v1"
    )
    assert first.snapshot.events[0].event_id == "event.001"
    _assert_safety(first)
    _assert_no_sensitive_values(first)


def test_authority_and_unavailable_fail_before_parse_or_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"read": 0, "parse": 0, "validate": 0}

    def reader(*, authority: object) -> bytes:
        calls["read"] += 1
        raise adapter._FixtureUnavailable

    def parser(*, fixture_bytes: bytes) -> object:
        calls["parse"] += 1
        return fixture_bytes

    def validator(*, adapter_result: object, authority: object) -> bool:
        calls["validate"] += 1
        return True

    monkeypatch.setattr(adapter, "_read_fixture_bytes", reader)
    monkeypatch.setattr(adapter, "_parse_fixture_document", parser)
    monkeypatch.setattr(
        adapter,
        "_is_safe_canonical_gold_economic_calendar_source_adapter_result_v1",
        validator,
    )
    invalid = replace(_authority(), authority_token=object())
    authority_result = (
        adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=invalid
        )
    )
    _assert_failure(authority_result, 0)
    assert calls == {"read": 0, "parse": 0, "validate": 0}

    unavailable = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(unavailable, 1)
    assert calls == {"read": 1, "parse": 0, "validate": 0}


def test_authority_types_values_and_lexical_paths_are_strict_before_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def reader(**_kwargs: object) -> bytes:
        nonlocal calls
        calls += 1
        return _fixture_bytes()

    monkeypatch.setattr(adapter, "_read_fixture_bytes", reader)
    authority = _authority()
    invalid_authorities = (
        replace(authority, allowed_root=str(authority.allowed_root)),
        replace(authority, fixture_path=authority.fixture_path.with_name("other.json")),
        replace(authority, reference_time_utc=datetime(2026, 7, 10, 2, 30, 5)),
        replace(
            authority,
            expected_identity=replace(
                authority.expected_identity,
                calendar_snapshot_id=StrictStringSubclass(
                    "canonical-gold-economic-calendar-docs-fixture-v1"
                ),
            ),
        ),
        replace(
            authority,
            read_policy=replace(
                authority.read_policy,
                maximum_calendar_events=StrictIntSubclass(512),
            ),
        ),
        replace(authority, calendar_schema_version="v1"),
        replace(authority, source_profile_version="caller-profile"),
    )
    for invalid in invalid_authorities:
        result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=invalid
        )
        _assert_failure(result, 0)
    assert calls == 0


@pytest.mark.parametrize(
    ("mutation", "priority"),
    (
        (lambda document: document.update(fixture_contract_version=1), 2),
        (lambda document: document.update(calendar_schema_version="v1"), 3),
        (lambda document: document.update(generated_at_utc="2026-02-30T00:00:00Z"), 4),
        (lambda document: document.update(coverage_end_utc="2026-07-11T02:30:04Z"), 5),
        (lambda document: document["events"][0].update(impact_code="CRITICAL"), 6),
        (lambda document: document["events"][0].update(source_revision=-1), 6),
    ),
)
def test_ordered_fixture_failures_stop_before_result_validation(
    monkeypatch: pytest.MonkeyPatch,
    mutation: object,
    priority: int,
) -> None:
    document = _fixture_document()
    mutation(document)
    calls = {"read": 0, "parse": 0, "validate": 0}
    original_parser = adapter._parse_fixture_document

    def reader(*, authority: object) -> bytes:
        calls["read"] += 1
        return _fixture_bytes(document)

    def parser(*, fixture_bytes: bytes) -> object:
        calls["parse"] += 1
        return original_parser(fixture_bytes=fixture_bytes)

    def validator(*, adapter_result: object, authority: object) -> bool:
        calls["validate"] += 1
        return True

    monkeypatch.setattr(adapter, "_read_fixture_bytes", reader)
    monkeypatch.setattr(adapter, "_parse_fixture_document", parser)
    monkeypatch.setattr(
        adapter,
        "_is_safe_canonical_gold_economic_calendar_source_adapter_result_v1",
        validator,
    )
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(result, priority)
    assert calls == {"read": 1, "parse": 1, "validate": 0}


@pytest.mark.parametrize(
    "fixture_bytes",
    (
        b"{} trailing",
        b"\xef\xbb\xbf{}",
        b'{"fixture_contract_version":NaN}',
        b'{"fixture_contract_version":"1.0","fixture_contract_version":"1.0"}',
    ),
)
def test_decode_json_duplicate_and_nonfinite_fail_as_fixture_invalid(
    monkeypatch: pytest.MonkeyPatch,
    fixture_bytes: bytes,
) -> None:
    monkeypatch.setattr(adapter, "_read_fixture_bytes", lambda **_kwargs: fixture_bytes)
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(result, 2)


def test_event_duplicate_key_order_count_and_coverage_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents = []
    duplicate_event = _fixture_bytes().decode("utf-8").replace(
        '"event_id":"event.001"',
        '"event_id":"event.001","event_id":"event.duplicate"',
        1,
    )
    documents.append(duplicate_event.encode("utf-8"))
    reversed_events = _fixture_document()
    reversed_events["events"] = list(reversed(reversed_events["events"]))
    documents.append(_fixture_bytes(reversed_events))
    too_many = _fixture_document()
    too_many["events"] = [too_many["events"][0]] * 513
    documents.append(_fixture_bytes(too_many))
    outside = _fixture_document()
    outside["events"][0]["scheduled_at_utc"] = "2026-07-11T02:30:05.000001Z"
    documents.append(_fixture_bytes(outside))
    reordered_event = _fixture_document()
    reordered_event["events"][0] = dict(
        reversed(tuple(reordered_event["events"][0].items()))
    )
    documents.append(_fixture_bytes(reordered_event))

    for payload in documents:
        monkeypatch.setattr(adapter, "_read_fixture_bytes", lambda **_kwargs: payload)
        result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=_authority()
        )
        _assert_failure(result, 6)


def test_top_level_key_reordering_is_fixture_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = dict(reversed(tuple(_fixture_document().items())))
    monkeypatch.setattr(
        adapter,
        "_read_fixture_bytes",
        lambda **_kwargs: _fixture_bytes(document),
    )
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(result, 2)


def test_g202_zero_512_and_inclusive_horizon_bounds_are_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty = _fixture_document()
    empty["events"] = []
    monkeypatch.setattr(
        adapter,
        "_read_fixture_bytes",
        lambda **_kwargs: _fixture_bytes(empty),
    )
    empty_result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    assert empty_result.passed is True
    assert empty_result.snapshot is not None
    assert empty_result.snapshot.events == ()

    maximum = _fixture_document()
    start = datetime(2026, 7, 10, 0, 0, tzinfo=UTC)
    maximum["coverage_end_utc"] = "2026-07-11T02:30:05Z"
    maximum["events"] = [
        {
            "event_id": f"event.{index:04d}",
            "scheduled_at_utc": (start + timedelta(seconds=index)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "country_code": "US",
            "currency_code": "USD",
            "event_category_code": "US_CPI",
            "impact_code": "HIGH",
            "source_revision": 0 if index == 0 else index,
            "event_status_code": "SCHEDULED",
        }
        for index in range(512)
    ]
    monkeypatch.setattr(
        adapter,
        "_read_fixture_bytes",
        lambda **_kwargs: _fixture_bytes(maximum),
    )
    maximum_result = (
        adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=_authority()
        )
    )
    assert maximum_result.passed is True
    assert maximum_result.snapshot is not None
    assert len(maximum_result.snapshot.events) == 512
    assert maximum_result.snapshot.events[0].source_revision == 0


def test_result_validator_is_called_once_and_false_maps_only_to_result_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def validator(*, adapter_result: object, authority: object) -> bool:
        nonlocal calls
        calls += 1
        return False

    monkeypatch.setattr(adapter, "_read_fixture_bytes", lambda **_kwargs: _fixture_bytes())
    monkeypatch.setattr(
        adapter,
        "_is_safe_canonical_gold_economic_calendar_source_adapter_result_v1",
        validator,
    )
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(result, 7)
    assert calls == 1


def test_private_validator_and_sanitizer_close_all_result_mappings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority()
    monkeypatch.setattr(adapter, "_read_fixture_bytes", lambda **_kwargs: _fixture_bytes())
    ready = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )
    validator = adapter._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1
    assert validator(adapter_result=ready, authority=authority) is True
    for status, reason in adapter._FAILURES:
        assert validator(
            adapter_result=adapter._failure(status, reason),
            authority=authority,
        ) is True
    assert validator(
        adapter_result=replace(ready, warning_codes=("warning",)),
        authority=authority,
    ) is False
    assert validator(
        adapter_result=replace(ready, status_code="FORGED"),
        authority=authority,
    ) is False
    assert validator(
        adapter_result=ready,
        authority=replace(authority, authority_token=object()),
    ) is False
    assert validator(adapter_result=object(), authority=authority) is False
    assert ready.snapshot is not None
    polluted_snapshot = replace(ready.snapshot, contains_raw_provider_payload=True)
    assert validator(
        adapter_result=replace(ready, snapshot=polluted_snapshot),
        authority=authority,
    ) is False

    safe = adapter._build_canonical_gold_economic_calendar_source_adapter_safe_failure_v1()
    _assert_failure(safe, 8)
    assert adapter._fixed_safe_failure_is_valid(safe) is True

    def raise_unexpected(**_kwargs: object) -> bool:
        raise ValueError

    monkeypatch.setattr(
        adapter,
        "_is_safe_canonical_gold_economic_calendar_snapshot_v1",
        raise_unexpected,
    )
    assert validator(adapter_result=ready, authority=authority) is False


def test_post_read_authority_drift_is_identity_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority()

    def drift(*, authority: object) -> bytes:
        object.__setattr__(
            authority.expected_identity,
            "calendar_snapshot_id",
            "canonical-gold-economic-calendar-drift-v1",
        )
        return _fixture_bytes()

    monkeypatch.setattr(adapter, "_read_fixture_bytes", drift)
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )
    _assert_failure(result, 3)


@pytest.mark.parametrize(
    "dependency",
    (
        "_read_fixture_bytes",
        "_parse_fixture_document",
        "_valid_fixture_identity",
        "_valid_freshness",
        "_valid_coverage",
        "_freeze_fixture_events",
        "_document_snapshot",
        "_build_snapshot",
    ),
)
def test_unexpected_dependency_exceptions_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    dependency: str,
) -> None:
    monkeypatch.setattr(adapter, "_read_fixture_bytes", lambda **_kwargs: _fixture_bytes())

    def raise_unexpected(**_kwargs: object) -> object:
        raise RuntimeError

    monkeypatch.setattr(adapter, dependency, raise_unexpected)
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(result, 8)
    _assert_no_sensitive_values(result)


def test_sanitizer_exception_uses_closed_terminal_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_unexpected(**_kwargs: object) -> object:
        raise RuntimeError

    monkeypatch.setattr(adapter, "_read_fixture_bytes", raise_unexpected)
    monkeypatch.setattr(adapter, "_safe_failure", raise_unexpected)
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=_authority()
    )
    _assert_failure(result, 8)


def test_filesystem_reader_has_one_fixed_missing_fixture_boundary() -> None:
    authority = _authority()
    assert authority.fixture_path == (
        Path(adapter.__file__).resolve().parents[3]
        / "docs"
        / "architecture"
        / "fixtures"
        / "canonical-gold-economic-calendar-v1"
        / "economic_calendar.json"
    )
    assert authority.fixture_path.exists() is False
    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )
    _assert_failure(result, 1)


def test_modules_are_ascii_and_isolated_from_future_runtime_surfaces() -> None:
    adapter_path = Path(adapter.__file__)
    economic_path = Path(economic_facts.__file__)
    adapter_source = adapter_path.read_text(encoding="utf-8")
    economic_source = economic_path.read_text(encoding="utf-8")
    assert all(ord(character) < 128 for character in adapter_source + economic_source)
    tree = ast.parse(adapter_source)
    imports = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    imports.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert imports == {
        "__future__",
        "dataclasses",
        "datetime",
        "json",
        "pathlib",
        "re",
        "stat",
        "app.services.canonical_gold_economic_window_facts",
    }
    forbidden_modules = (
        "canonical_gold_market_facts_docs_fixture_integration",
        "canonical_gold_market_facts_snapshot_projector",
        "replay_runner",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "mt4",
        "order_execution",
    )
    assert all(
        token not in imported.casefold()
        for imported in imports
        for token in forbidden_modules
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint({"getenv", "environ", "system", "popen"})
    assert "allowed_to_call_ea=True" not in adapter_source.replace(" ", "")


def _authority() -> adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1:
    return adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1(
        authority_token=adapter._AUTHORITY_TOKEN,
        allowed_root=adapter._EXPECTED_ALLOWED_ROOT,
        fixture_path=adapter._EXPECTED_FIXTURE_PATH,
        reference_time_utc=datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC),
        expected_identity=adapter._CanonicalGoldEconomicCalendarExpectedIdentityV1(
            calendar_snapshot_id=(
                "canonical-gold-economic-calendar-docs-fixture-v1"
            ),
        ),
        read_policy=adapter._CanonicalGoldEconomicCalendarReadPolicyV1(
            maximum_fixture_bytes=1_048_576,
            maximum_calendar_events=512,
            maximum_calendar_age_microseconds=300_000_000,
            maximum_coverage_span_microseconds=259_200_000_000,
            search_horizon_microseconds=86_400_000_000,
            maximum_read_attempts=1,
        ),
        calendar_schema_version="1.0",
        source_profile_version="canonical_gold_economic_calendar_source_v1",
    )


def _fixture_document() -> dict[str, object]:
    return {
        "fixture_contract_version": "1.0",
        "calendar_schema_version": "1.0",
        "calendar_snapshot_id": "canonical-gold-economic-calendar-docs-fixture-v1",
        "generated_at_utc": "2026-07-10T02:30:04.900000Z",
        "coverage_start_utc": "2026-07-09T02:30:05Z",
        "coverage_end_utc": "2026-07-11T02:30:05.000001Z",
        "events": [
            {
                "event_id": "event.001",
                "scheduled_at_utc": "2026-07-10T03:00:00Z",
                "country_code": "US",
                "currency_code": "USD",
                "event_category_code": "US_CPI",
                "impact_code": "HIGH",
                "source_revision": 1,
                "event_status_code": "SCHEDULED",
            },
            {
                "event_id": "event.002",
                "scheduled_at_utc": "2026-07-10T04:00:00Z",
                "country_code": "US",
                "currency_code": "USD",
                "event_category_code": "US_PCE",
                "impact_code": "MEDIUM",
                "source_revision": 2,
                "event_status_code": "SCHEDULED",
            },
        ],
    }


def _fixture_bytes(document: dict[str, object] | None = None) -> bytes:
    return json.dumps(
        _fixture_document() if document is None else document,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _authority_values(
    authority: adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1,
) -> tuple[object, ...]:
    return adapter._authority_snapshot(authority)


def _assert_failure(
    result: adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1,
    priority: int,
) -> None:
    status, reason = adapter._FAILURES[priority]
    assert result.passed is result.snapshot_available is False
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.warning_codes == ()
    assert result.snapshot is None
    _assert_safety(result)


def _assert_safety(
    result: adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1,
) -> None:
    assert result.read_only is result.demo_only is True
    assert result.is_tradable is result.can_execute is False
    assert result.is_trading_permission is result.is_execution_instruction is False
    assert result.allowed_to_call_ea is result.allowed_to_modify_risk is False


def _assert_no_sensitive_values(value: object) -> None:
    seen: set[int] = set()

    def walk(current: object) -> tuple[object, ...]:
        if id(current) in seen:
            return ()
        seen.add(id(current))
        if is_dataclass(current):
            return tuple(
                child
                for field in fields(current)
                for child in walk(getattr(current, field.name))
            )
        if type(current) is tuple:
            return tuple(child for item in current for child in walk(item))
        return (current,)

    leaves = walk(value)
    assert all(not isinstance(item, Path) for item in leaves)
    text_values = tuple(item.casefold() for item in leaves if type(item) is str)
    assert all(
        all(token not in item for item in text_values)
        for token in ("economic_calendar.json", "payload", "checksum", "traceback")
    )
