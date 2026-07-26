"""Genuine offline G185 -> G178 -> G204 -> G201 composition evidence only.

This keeps W6 TESTS_ONLY. It is not deterministic verification, ReplayRunner
staging, reader or MT4 activation, execution authority, or trading permission.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path

import pytest

from app.services import canonical_gold_economic_calendar_source_adapter as g204
from app.services import canonical_gold_economic_window_facts as g201
from app.services import canonical_gold_market_facts_docs_fixture_integration as g185
from app.services import canonical_gold_market_facts_snapshot_projector as g178


SOURCE_RESULT_FIELDS = (
    "contract_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "source_available",
    "source",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
SOURCE_FIELDS = (
    "contract_version",
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
    "policy_profile_version",
    "upstream_evidence",
    "live_tick",
    "bars_generated_at_utc",
    "timeframes",
    "symbol_spec",
)
MARKET_SNAPSHOT_FIELDS = (
    "contract_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "identity_available",
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
    "quote",
    "timeframes",
    "symbol_spec",
    "freshness",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
CALENDAR_RESULT_FIELDS = (
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
CALENDAR_SNAPSHOT_FIELDS = (
    "contract_version",
    "calendar_schema_version",
    "calendar_snapshot_id",
    "source_profile_version",
    "generated_at_utc",
    "coverage_start_utc",
    "coverage_end_utc",
    "events",
    "upstream_evidence",
    "read_only",
    "demo_only",
    "contains_raw_provider_payload",
)
CALENDAR_EVIDENCE_FIELDS = (
    "adapter_passed",
    "adapter_status_code",
    "schema_validated",
    "identity_validated",
    "timestamps_normalized",
    "same_snapshot_bound",
    "warning_codes",
    "raw_payload_discarded",
)
CALENDAR_EVENT_FIELDS = (
    "event_id",
    "scheduled_at_utc",
    "country_code",
    "currency_code",
    "event_category_code",
    "impact_code",
    "source_revision",
    "event_status_code",
)
RESULT_FIELDS = (
    "contract_version",
    "facts_profile_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "identity_available",
    "source_contract_version",
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
    "calendar_contract_version",
    "calendar_schema_version",
    "calendar_snapshot_id",
    "calendar_source_profile_version",
    "calendar_generated_at_utc",
    "calendar_coverage_start_utc",
    "calendar_coverage_end_utc",
    "event_windows",
    "summary",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
EVENT_WINDOW_FIELDS = (
    "event_id",
    "scheduled_at_utc",
    "country_code",
    "currency_code",
    "event_category_code",
    "impact_code",
    "source_revision",
    "window_start_utc",
    "window_end_utc",
    "event_offset_microseconds",
    "window_start_offset_microseconds",
    "window_end_offset_microseconds",
    "window_relation_code",
    "is_active_observation_window",
)
SUMMARY_FIELDS = (
    "calendar_age_microseconds",
    "relevant_event_count",
    "active_window_count",
    "inside_any_observation_window",
    "active_event_ids",
    "nearest_previous_event_id",
    "nearest_previous_event_offset_microseconds",
    "nearest_next_event_id",
    "nearest_next_event_offset_microseconds",
    "highest_active_impact_code",
)
SAFETY_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}
MARKET_IDENTITY = (
    "1.0",
    "1.0",
    "demo-bundle-000000000001",
    1,
    "XAUUSD",
    "GOLD",
    "2026-07-10T02:30:05.000000Z",
)
CALENDAR_IDENTITY = (
    "1.0",
    "1.0",
    "canonical-gold-economic-calendar-docs-fixture-v1",
    "canonical_gold_economic_calendar_source_v1",
    "2026-07-10T02:30:04.900000Z",
    "2026-07-09T02:30:05Z",
    "2026-07-11T02:30:05.000001Z",
)
EXPECTED_WINDOWS = (
    (
        "event.001",
        "2026-07-10T03:00:00Z",
        "US",
        "USD",
        "US_CPI",
        "HIGH",
        1,
        "2026-07-10T02:30:00Z",
        "2026-07-10T03:30:00Z",
        1_795_000_000,
        -5_000_000,
        3_595_000_000,
        "ACTIVE",
        True,
    ),
    (
        "event.002",
        "2026-07-10T04:00:00Z",
        "US",
        "USD",
        "US_PCE",
        "MEDIUM",
        2,
        "2026-07-10T03:45:00Z",
        "2026-07-10T04:15:00Z",
        5_395_000_000,
        4_495_000_000,
        6_295_000_000,
        "UPCOMING",
        False,
    ),
)
EXPECTED_SUMMARY = (
    100_000,
    2,
    1,
    True,
    ("event.001",),
    None,
    None,
    "event.001",
    1_795_000_000,
    "HIGH",
)


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueFixtureState:
    entries: tuple[tuple[str, tuple[str, ...], str, bytes, int], ...]

    def matches(self, other: object) -> bool:
        return type(other) is _OpaqueFixtureState and self.entries == other.entries

    def __repr__(self) -> str:
        return "<fixture-state:redacted>"


def test_real_fixtures_compose_g185_g178_g204_g201_without_patching() -> None:
    fixture_before = _fixture_state()

    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    source_before = deepcopy(source_result.source)
    market_snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    assert source_result.source == source_before

    authority = _calendar_authority()
    authority_before = g204._authority_snapshot(authority)
    calendar_result = (
        g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=authority
        )
    )
    assert calendar_result.snapshot is not None
    assert g204._authority_snapshot(authority) == authority_before

    market_before = deepcopy(market_snapshot)
    calendar_before = deepcopy(calendar_result.snapshot)
    result = g201.build_canonical_gold_economic_window_facts_v1(
        market_facts_snapshot=market_snapshot,
        economic_calendar_snapshot=calendar_result.snapshot,
    )

    assert fixture_before.matches(_fixture_state())
    assert market_snapshot == market_before
    assert calendar_result.snapshot == calendar_before
    _assert_ready_source_result(source_result)
    _assert_ready_market_snapshot(market_snapshot)
    _assert_ready_calendar_result(calendar_result)
    _assert_ready_result(result)
    assert _market_identity(market_snapshot) == MARKET_IDENTITY
    assert _calendar_identity(calendar_result.snapshot) == CALENDAR_IDENTITY
    assert _result_market_identity(result) == MARKET_IDENTITY
    assert _result_calendar_identity(result) == CALENDAR_IDENTITY
    assert _object_graph_ids(market_snapshot).isdisjoint(_object_graph_ids(result))
    assert _object_graph_ids(calendar_result.snapshot).isdisjoint(
        _object_graph_ids(result)
    )
    _assert_no_sensitive_output(source_result, market_snapshot, calendar_result, result)


def test_repeated_real_composition_is_equal_fresh_detached_and_non_mutating() -> None:
    fixture_before = _fixture_state()
    runs = tuple(_compose_once() for _ in range(3))

    assert fixture_before.matches(_fixture_state())
    assert runs[0][3] == runs[1][3] == runs[2][3]
    for index, (source_result, market_snapshot, calendar_result, result) in enumerate(
        runs
    ):
        _assert_ready_result(result)
        graphs = (
            _object_graph_ids(source_result),
            _object_graph_ids(market_snapshot),
            _object_graph_ids(calendar_result),
            _object_graph_ids(result),
        )
        assert all(
            left.isdisjoint(right)
            for left_index, left in enumerate(graphs)
            for right in graphs[left_index + 1 :]
        )
        for later in runs[index + 1 :]:
            assert all(
                left.isdisjoint(_object_graph_ids(right))
                for left, right in zip(graphs, later, strict=True)
            )


def test_delegating_spies_confirm_one_ordered_call_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = _fixture_state()
    genuine = _compose_once()
    _assert_ready_result(genuine[3])

    original_source = g185.build_canonical_gold_market_facts_docs_fixture_source_v1
    original_projector = g178.build_canonical_gold_market_facts_snapshot_v1
    original_calendar = (
        g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1
    )
    original_builder = g201.build_canonical_gold_economic_window_facts_v1
    calls: list[str] = []
    observed_authority: list[tuple[object, ...]] = []

    def source_wrapper() -> object:
        calls.append("G185")
        return original_source()

    def projector_wrapper(*, validated_source: object) -> object:
        calls.append("G178")
        observed_authority.append(_market_identity(validated_source))
        return original_projector(validated_source=validated_source)

    def calendar_wrapper(*, authority: object) -> object:
        calls.append("G204")
        assert g204._authority_snapshot(authority) == g204._authority_snapshot(
            _calendar_authority()
        )
        return original_calendar(authority=authority)

    def builder_wrapper(
        *,
        market_facts_snapshot: object,
        economic_calendar_snapshot: object,
    ) -> object:
        calls.append("G201")
        observed_authority.extend(
            (
                _market_identity(market_facts_snapshot),
                _calendar_identity(economic_calendar_snapshot),
            )
        )
        return original_builder(
            market_facts_snapshot=market_facts_snapshot,
            economic_calendar_snapshot=economic_calendar_snapshot,
        )

    with monkeypatch.context() as context:
        context.setattr(
            g185,
            "build_canonical_gold_market_facts_docs_fixture_source_v1",
            source_wrapper,
        )
        context.setattr(
            g178,
            "build_canonical_gold_market_facts_snapshot_v1",
            projector_wrapper,
        )
        context.setattr(
            g204,
            "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
            calendar_wrapper,
        )
        context.setattr(
            g201,
            "build_canonical_gold_economic_window_facts_v1",
            builder_wrapper,
        )
        observed = _compose_once()

    assert calls == ["G185", "G178", "G204", "G201"]
    assert observed_authority == [
        MARKET_IDENTITY,
        MARKET_IDENTITY,
        CALENDAR_IDENTITY,
    ]
    assert observed == genuine
    assert all(left is not right for left, right in zip(observed, genuine, strict=True))
    assert fixture_before.matches(_fixture_state())


def test_primary_anchor_is_unpatched_and_scope_is_integration_only() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_fixtures_compose_g185_g178_g204_g201_without_patching"
    )
    calls = tuple(
        node.func.attr
        for node in ast.walk(primary)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "build_canonical_gold_market_facts_docs_fixture_source_v1",
            "build_canonical_gold_market_facts_snapshot_v1",
            "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
            "build_canonical_gold_economic_window_facts_v1",
        }
    )
    names = {node.id for node in ast.walk(primary) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(primary) if isinstance(node, ast.Attribute)
    }
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    scope = " ".join((__doc__ or "").casefold().split())

    assert calls == (
        "build_canonical_gold_market_facts_docs_fixture_source_v1",
        "build_canonical_gold_market_facts_snapshot_v1",
        "build_server_owned_canonical_gold_economic_calendar_snapshot_v1",
        "build_canonical_gold_economic_window_facts_v1",
    )
    assert names.isdisjoint({"monkeypatch", "patch", "Mock", "MagicMock", "spy"})
    assert attributes.isdisjoint({"setattr", "setitem"})
    assert "genuine offline g185 -> g178 -> g204 -> g201 composition evidence only" in scope
    assert "keeps w6 tests_only" in scope
    assert "not deterministic verification" in scope
    assert "replayrunner staging" in scope
    assert "reader or mt4 activation" in scope
    assert "execution authority" in scope
    assert "trading permission" in scope
    assert not any(
        forbidden in imported
        for forbidden in (
            "canonical_bundle_replay_runner",
            "fastapi",
            "requests",
            "httpx",
            "socket",
            "subprocess",
        )
        for imported in imports
    )


def _compose_once() -> tuple[object, object, object, object]:
    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    source_before = deepcopy(source_result.source)
    market_snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    assert source_result.source == source_before

    authority = _calendar_authority()
    authority_before = g204._authority_snapshot(authority)
    calendar_result = (
        g204.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(
            authority=authority
        )
    )
    assert calendar_result.snapshot is not None
    assert g204._authority_snapshot(authority) == authority_before

    market_before = deepcopy(market_snapshot)
    calendar_before = deepcopy(calendar_result.snapshot)
    result = g201.build_canonical_gold_economic_window_facts_v1(
        market_facts_snapshot=market_snapshot,
        economic_calendar_snapshot=calendar_result.snapshot,
    )
    assert market_snapshot == market_before
    assert calendar_result.snapshot == calendar_before
    return source_result, market_snapshot, calendar_result, result


def _calendar_authority() -> g204._CanonicalGoldEconomicCalendarSourceAuthorityV1:
    return g204._CanonicalGoldEconomicCalendarSourceAuthorityV1(
        authority_token=g204._AUTHORITY_TOKEN,
        allowed_root=g204._EXPECTED_ALLOWED_ROOT,
        fixture_path=g204._EXPECTED_FIXTURE_PATH,
        reference_time_utc=g204._FIXED_REFERENCE_TIME,
        expected_identity=g204._EXPECTED_IDENTITY,
        read_policy=g204._READ_POLICY,
        calendar_schema_version="1.0",
        source_profile_version="canonical_gold_economic_calendar_source_v1",
    )


def _fixture_state() -> _OpaqueFixtureState:
    roots = (
        ("market", g185._FIXED_PATHS[2]),
        ("calendar", g204._EXPECTED_FIXTURE_PATH.parent),
    )
    entries: list[tuple[str, tuple[str, ...], str, bytes, int]] = []
    for label, root in roots:
        for entry in sorted(
            root.rglob("*"),
            key=lambda candidate: candidate.relative_to(root).as_posix(),
        ):
            entries.append(_fixture_entry_state(label=label, entry=entry, root=root))
    return _OpaqueFixtureState(tuple(entries))


def _fixture_entry_state(
    *,
    label: str,
    entry: Path,
    root: Path,
) -> tuple[str, tuple[str, ...], str, bytes, int]:
    relative_parts = entry.relative_to(root).parts
    stat = entry.lstat()
    if entry.is_symlink():
        kind = "symlink"
        content = entry.readlink().as_posix().encode("utf-8")
    elif entry.is_file():
        kind = "file"
        content = entry.read_bytes()
    elif entry.is_dir():
        kind = "directory"
        content = b""
    else:
        kind = "other"
        content = b""
    return label, relative_parts, kind, content, stat.st_mtime_ns


def _assert_ready_source_result(result: object) -> None:
    assert type(result) is g185.CanonicalGoldMarketFactsSourceAdapterResultV1
    assert tuple(field.name for field in fields(type(result))) == SOURCE_RESULT_FIELDS
    assert result.passed is result.source_available is True
    assert result.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_READY"
    assert result.reason_codes == result.warning_codes == ()
    assert type(result.source) is g178.CanonicalGoldMarketFactsSourceV1
    assert tuple(field.name for field in fields(type(result.source))) == SOURCE_FIELDS
    _assert_safety(result)


def _assert_ready_market_snapshot(snapshot: object) -> None:
    assert type(snapshot) is g178.CanonicalGoldMarketFactsSnapshotV1
    assert tuple(field.name for field in fields(type(snapshot))) == MARKET_SNAPSHOT_FIELDS
    assert snapshot.passed is snapshot.identity_available is True
    assert snapshot.status_code == "CANONICAL_GOLD_MARKET_FACTS_READY"
    assert snapshot.reason_codes == snapshot.warning_codes == ()
    _assert_safety(snapshot)


def _assert_ready_calendar_result(result: object) -> None:
    assert type(result) is g204.CanonicalGoldEconomicCalendarSourceAdapterResultV1
    assert tuple(field.name for field in fields(type(result))) == CALENDAR_RESULT_FIELDS
    assert result.passed is result.snapshot_available is True
    assert result.status_code == "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY"
    assert result.reason_codes == result.warning_codes == ()
    assert result.snapshot is not None
    assert type(result.snapshot) is g201.CanonicalGoldEconomicCalendarSnapshotV1
    assert (
        tuple(field.name for field in fields(type(result.snapshot)))
        == CALENDAR_SNAPSHOT_FIELDS
    )
    assert (
        tuple(field.name for field in fields(type(result.snapshot.upstream_evidence)))
        == CALENDAR_EVIDENCE_FIELDS
    )
    assert all(
        tuple(field.name for field in fields(type(event))) == CALENDAR_EVENT_FIELDS
        for event in result.snapshot.events
    )
    assert result.snapshot.read_only is result.snapshot.demo_only is True
    assert result.snapshot.contains_raw_provider_payload is False
    assert result.snapshot.upstream_evidence.raw_payload_discarded is True
    _assert_safety(result)


def _assert_ready_result(result: object) -> None:
    assert type(result) is g201.CanonicalGoldEconomicWindowFactsV1
    assert tuple(field.name for field in fields(type(result))) == RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.facts_profile_version == "canonical_gold_economic_window_profile_v1"
    assert result.passed is result.identity_available is True
    assert result.status_code == "CANONICAL_GOLD_ECONOMIC_WINDOW_READY"
    assert result.reason_codes == result.warning_codes == ()
    assert type(result.event_windows) is tuple and len(result.event_windows) == 2
    assert all(
        tuple(field.name for field in fields(type(window))) == EVENT_WINDOW_FIELDS
        for window in result.event_windows
    )
    assert tuple(
        tuple(getattr(window, name) for name in EVENT_WINDOW_FIELDS)
        for window in result.event_windows
    ) == EXPECTED_WINDOWS
    assert type(result.summary) is g201.CanonicalGoldEconomicWindowSummaryV1
    assert tuple(field.name for field in fields(type(result.summary))) == SUMMARY_FIELDS
    assert tuple(getattr(result.summary, name) for name in SUMMARY_FIELDS) == EXPECTED_SUMMARY
    _assert_safety(result)


def _assert_safety(value: object) -> None:
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(value, name) is expected


def _market_identity(value: object) -> tuple[object, ...]:
    return (
        value.contract_version,
        value.bundle_schema_version,
        value.bundle_id,
        value.sequence,
        value.canonical_symbol,
        value.broker_symbol,
        value.reference_time_utc,
    )


def _calendar_identity(value: object) -> tuple[object, ...]:
    return (
        value.contract_version,
        value.calendar_schema_version,
        value.calendar_snapshot_id,
        value.source_profile_version,
        value.generated_at_utc,
        value.coverage_start_utc,
        value.coverage_end_utc,
    )


def _result_market_identity(value: object) -> tuple[object, ...]:
    return (
        value.source_contract_version,
        value.bundle_schema_version,
        value.bundle_id,
        value.sequence,
        value.canonical_symbol,
        value.broker_symbol,
        value.reference_time_utc,
    )


def _result_calendar_identity(value: object) -> tuple[object, ...]:
    return (
        value.calendar_contract_version,
        value.calendar_schema_version,
        value.calendar_snapshot_id,
        value.calendar_source_profile_version,
        value.calendar_generated_at_utc,
        value.calendar_coverage_start_utc,
        value.calendar_coverage_end_utc,
    )


def _object_graph_ids(value: object) -> set[int]:
    identities: set[int] = set()

    def visit(current: object) -> None:
        if is_dataclass(current) and not isinstance(current, type):
            identities.add(id(current))
            for field in fields(current):
                visit(getattr(current, field.name))
        elif type(current) is tuple and any(
            is_dataclass(item) or type(item) is tuple for item in current
        ):
            identities.add(id(current))
            for item in current:
                visit(item)

    visit(value)
    return identities


def _assert_no_sensitive_output(*values: object) -> None:
    leaves = tuple(
        leaf
        for value in values
        for leaf in _walk(value=value, seen=set())
    )
    assert all(type(leaf) is not bytes for leaf in leaves)
    assert all(not isinstance(leaf, Path) for leaf in leaves)
    rendered = " ".join(
        leaf.casefold() for leaf in leaves if type(leaf) is str
    )
    for forbidden in (
        "economic_calendar.json",
        "checksum",
        "traceback",
        "exception_message",
        "authority_token",
        "internal_source_status",
    ):
        assert forbidden not in rendered


def _walk(*, value: object, seen: set[int]) -> tuple[object, ...]:
    if id(value) in seen:
        return ()
    seen.add(id(value))
    if is_dataclass(value) and not isinstance(value, type):
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
