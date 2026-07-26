from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from app.services import canonical_gold_economic_calendar_source_adapter as adapter


_FIXTURE_PATH = (
    Path(adapter.__file__).resolve().parents[3]
    / "docs"
    / "architecture"
    / "fixtures"
    / "canonical-gold-economic-calendar-v1"
    / "economic_calendar.json"
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


def test_real_fixed_fixture_adapter_integration_is_ready_fresh_and_detached() -> None:
    fixture_before = _FIXTURE_PATH.read_bytes()
    authority = _authority()
    authority_before = adapter._authority_snapshot(authority)

    first = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )
    second = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )

    assert first == second
    assert first is not second
    assert type(first) is adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1
    assert type(second) is adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1
    assert first.passed is first.snapshot_available is True
    assert first.status_code == "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
    assert first.reason_codes == first.warning_codes == ()
    assert first.snapshot is not None
    assert second.snapshot is not None
    assert first.snapshot is not second.snapshot
    assert first.snapshot.events is not second.snapshot.events
    assert first.snapshot.upstream_evidence is not second.snapshot.upstream_evidence
    assert all(
        left is not right
        for left, right in zip(
            first.snapshot.events,
            second.snapshot.events,
            strict=True,
        )
    )
    _assert_snapshot(first.snapshot)
    _assert_snapshot(second.snapshot)
    _assert_safety(first)
    _assert_safety(second)
    _assert_no_sensitive_values(first)
    _assert_no_sensitive_values(second)
    assert _FIXTURE_PATH.read_bytes() == fixture_before
    assert adapter._authority_snapshot(authority) == authority_before


def test_fixed_fixture_document_is_exact_ordered_ascii_and_bounded() -> None:
    fixture_bytes = _FIXTURE_PATH.read_bytes()
    fixture_text = fixture_bytes.decode("ascii")
    document = json.loads(fixture_text)

    assert not fixture_bytes.startswith(b"\xef\xbb\xbf")
    assert 1 <= len(fixture_bytes) <= adapter._READ_POLICY.maximum_fixture_bytes
    assert tuple(document) == _FIXTURE_FIELDS
    assert tuple(tuple(event) for event in document["events"]) == (
        _EVENT_FIELDS,
        _EVENT_FIELDS,
    )
    assert document == {
        "fixture_contract_version": "1.0",
        "calendar_schema_version": "1.0",
        "calendar_snapshot_id": (
            "canonical-gold-economic-calendar-docs-fixture-v1"
        ),
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


def test_real_anchor_then_delegating_spies_confirm_one_ordered_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority()
    anchor = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )
    assert anchor.passed is True

    calls: list[str] = []
    original_reader = adapter._read_fixture_bytes
    original_parser = adapter._parse_fixture_document
    original_validator = (
        adapter._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1
    )

    def read_once(*, authority: object) -> bytes:
        calls.append("read")
        assert authority is authority_reference
        return original_reader(authority=authority)

    def parse_once(*, fixture_bytes: bytes) -> object:
        calls.append("parse")
        return original_parser(fixture_bytes=fixture_bytes)

    def validate_once(*, adapter_result: object, authority: object) -> bool:
        calls.append("validate")
        assert authority is authority_reference
        return original_validator(
            adapter_result=adapter_result,
            authority=authority,
        )

    authority_reference = authority
    monkeypatch.setattr(adapter, "_read_fixture_bytes", read_once)
    monkeypatch.setattr(adapter, "_parse_fixture_document", parse_once)
    monkeypatch.setattr(
        adapter,
        "_is_safe_canonical_gold_economic_calendar_source_adapter_result_v1",
        validate_once,
    )

    result = adapter.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
        authority=authority
    )

    assert result == anchor
    assert result is not anchor
    assert calls == ["read", "parse", "validate"]


def test_primary_success_anchor_has_no_patch_mock_or_spy() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_fixed_fixture_adapter_integration_is_ready_fresh_and_detached"
    )
    names = {
        node.id.casefold()
        for node in ast.walk(primary)
        if isinstance(node, ast.Name)
    }
    attributes = {
        node.attr.casefold()
        for node in ast.walk(primary)
        if isinstance(node, ast.Attribute)
    }
    assert names.isdisjoint({"monkeypatch", "mock", "patch", "spy"})
    assert attributes.isdisjoint({"setattr", "patch", "mock"})


def test_fixture_integration_remains_isolated_from_later_runtime_surfaces() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    assert all(ord(character) < 128 for character in source)
    prohibited = (
        "canonical_gold_economic_" + "window_facts",
        "canonical_bundle_" + "replay_runner",
        "Meta" + "Trader",
        "order_" + "send",
    )
    assert all(token not in source for token in prohibited)
    assert "allowed_to_call_ea" + "=True" not in source.replace(" ", "")


def _authority() -> adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1:
    return adapter._CanonicalGoldEconomicCalendarSourceAuthorityV1(
        authority_token=adapter._AUTHORITY_TOKEN,
        allowed_root=adapter._EXPECTED_ALLOWED_ROOT,
        fixture_path=adapter._EXPECTED_FIXTURE_PATH,
        reference_time_utc=datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC),
        expected_identity=adapter._EXPECTED_IDENTITY,
        read_policy=adapter._READ_POLICY,
        calendar_schema_version="1.0",
        source_profile_version="canonical_gold_economic_calendar_source_v1",
    )


def _assert_snapshot(
    snapshot: adapter.CanonicalGoldEconomicCalendarSnapshotV1,
) -> None:
    assert type(snapshot) is adapter.CanonicalGoldEconomicCalendarSnapshotV1
    assert snapshot.contract_version == "1.0"
    assert snapshot.calendar_schema_version == "1.0"
    assert snapshot.calendar_snapshot_id == (
        "canonical-gold-economic-calendar-docs-fixture-v1"
    )
    assert snapshot.source_profile_version == (
        "canonical_gold_economic_calendar_source_v1"
    )
    assert snapshot.generated_at_utc == "2026-07-10T02:30:04.900000Z"
    assert snapshot.coverage_start_utc == "2026-07-09T02:30:05Z"
    assert snapshot.coverage_end_utc == "2026-07-11T02:30:05.000001Z"
    assert tuple(event.event_id for event in snapshot.events) == (
        "event.001",
        "event.002",
    )
    assert tuple(event.event_category_code for event in snapshot.events) == (
        "US_CPI",
        "US_PCE",
    )
    assert tuple(event.impact_code for event in snapshot.events) == (
        "HIGH",
        "MEDIUM",
    )
    assert tuple(event.source_revision for event in snapshot.events) == (1, 2)
    assert snapshot.upstream_evidence.adapter_passed is True
    assert snapshot.upstream_evidence.adapter_status_code == (
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
    )
    assert snapshot.upstream_evidence.warning_codes == ()
    assert snapshot.upstream_evidence.raw_payload_discarded is True
    assert snapshot.read_only is snapshot.demo_only is True
    assert snapshot.contains_raw_provider_payload is False


def _assert_safety(
    result: adapter.CanonicalGoldEconomicCalendarSourceAdapterResultV1,
) -> None:
    assert result.read_only is result.demo_only is True
    assert result.is_tradable is result.can_execute is False
    assert result.is_trading_permission is result.is_execution_instruction is False
    assert result.allowed_to_call_ea is result.allowed_to_modify_risk is False


def _assert_no_sensitive_values(value: object) -> None:
    leaves = _walk(value=value, seen=set())
    assert all(not isinstance(item, Path) for item in leaves)
    text_values = tuple(item.casefold() for item in leaves if type(item) is str)
    assert all(
        all(token not in item for item in text_values)
        for token in (
            "economic_calendar.json",
            "payload",
            "checksum",
            "traceback",
        )
    )


def _walk(*, value: object, seen: set[int]) -> tuple[object, ...]:
    if id(value) in seen:
        return ()
    seen.add(id(value))
    if is_dataclass(value):
        return tuple(
            child
            for field in fields(value)
            for child in _walk(value=getattr(value, field.name), seen=seen)
        )
    if type(value) is tuple:
        return tuple(
            child
            for item in value
            for child in _walk(value=item, seen=seen)
        )
    return (value,)
