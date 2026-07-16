"""Deterministic offline composition verification only; never activation.

This verifies the integrated G185 -> G178 -> G191 facts composition. W6 remains
TESTS_ONLY. It does not verify a ReplayRunner W6 stage, activate a reader or
MT4, or grant EA, order, execution, or trading permission.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path

import pytest

from app.services import canonical_gold_market_facts_docs_fixture_integration as g185
from app.services import canonical_gold_market_facts_snapshot_projector as g178
from app.services import canonical_gold_session_spread_freshness_facts as g191


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
SNAPSHOT_FIELDS = (
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
FACTS_FIELDS = (
    "contract_version",
    "facts_profile_version",
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
    "session",
    "spread",
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
IDENTITY = (
    "1.0",
    "demo-bundle-000000000001",
    1,
    "XAUUSD",
    "GOLD",
    "2026-07-10T02:30:05.000000Z",
)
REAL_RUN_COUNT = 5
FAILURE_RUN_COUNT = 3


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueFixtureState:
    entries: tuple[tuple[tuple[str, ...], str, bytes, int], ...]

    def matches(self, other: object) -> bool:
        return type(other) is _OpaqueFixtureState and self.entries == other.entries

    def __repr__(self) -> str:
        return "<fixture-state:redacted>"


def test_real_composition_is_deterministic_detached_and_fresh_for_five_runs(
) -> None:
    fixture_before = _fixture_state()
    fixed_paths = g185._FIXED_PATHS
    fixed_identity = g185._FIXTURE_IDENTITY
    reference_time = g185._REFERENCE_TIME
    session_windows = g191._SESSION_WINDOWS
    runs = []

    for _ in range(REAL_RUN_COUNT):
        source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
        assert source_result.source is not None
        snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
            validated_source=source_result.source
        )
        result = g191.build_canonical_gold_session_spread_freshness_facts_v1(
            market_facts_snapshot=snapshot
        )
        runs.append((source_result, snapshot, result))

    assert all(run == runs[0] for run in runs)
    graph_ids = tuple(_detached_graph_ids(run) for run in runs)
    assert all(len(ids) == len(graph_ids[0]) for ids in graph_ids)
    for left_index, left in enumerate(graph_ids):
        for right in graph_ids[left_index + 1 :]:
            assert left.isdisjoint(right)

    for source_result, snapshot, result in runs:
        _assert_exact_ready_source_result(source_result)
        _assert_exact_ready_snapshot(snapshot)
        _assert_exact_ready_facts(result)
        assert (
            _source_identity(source_result.source)
            == _snapshot_identity(snapshot)
            == _facts_identity(result)
            == IDENTITY
        )
        _assert_no_sensitive_output(source_result, snapshot, result)

    assert fixture_before.matches(_fixture_state())
    assert g185._FIXED_PATHS is fixed_paths
    assert g185._FIXTURE_IDENTITY is fixed_identity
    assert g185._REFERENCE_TIME is reference_time
    assert g191._SESSION_WINDOWS is session_windows


def test_tampering_with_detached_run_cannot_change_later_real_composition() -> None:
    fixture_before = _fixture_state()
    first = _run_real_composition()
    expected = deepcopy(first)
    source_result, snapshot, result = first
    assert source_result.source is not None
    assert result.session is not None

    object.__setattr__(source_result.source, "bundle_id", "caller-local-source")
    object.__setattr__(snapshot, "bundle_id", "caller-local-snapshot")
    object.__setattr__(result, "status_code", "CALLER_LOCAL_RESULT")
    object.__setattr__(result.session, "session_bucket_code", "CALLER_LOCAL_SESSION")

    subsequent = _run_real_composition()

    assert first != expected
    assert subsequent == expected
    assert _detached_graph_ids(subsequent).isdisjoint(_detached_graph_ids(first))
    _assert_exact_ready_source_result(subsequent[0])
    _assert_exact_ready_snapshot(subsequent[1])
    _assert_exact_ready_facts(subsequent[2])
    _assert_no_sensitive_output(*subsequent)
    assert fixture_before.matches(_fixture_state())


def test_delegating_spies_confirm_one_ordered_call_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = _fixture_state()
    genuine_anchor = _run_real_composition()
    original_source_builder = (
        g185.build_canonical_gold_market_facts_docs_fixture_source_v1
    )
    original_projector = g178.build_canonical_gold_market_facts_snapshot_v1
    original_facts_builder = (
        g191.build_canonical_gold_session_spread_freshness_facts_v1
    )
    calls: list[str] = []

    def source_spy() -> object:
        calls.append("G185")
        return original_source_builder()

    def projector_spy(*, validated_source: object) -> object:
        calls.append("G178")
        return original_projector(validated_source=validated_source)  # type: ignore[arg-type]

    def facts_spy(*, market_facts_snapshot: object) -> object:
        calls.append("G191")
        return original_facts_builder(  # type: ignore[arg-type]
            market_facts_snapshot=market_facts_snapshot
        )

    with monkeypatch.context() as context:
        context.setattr(
            g185,
            "build_canonical_gold_market_facts_docs_fixture_source_v1",
            source_spy,
        )
        context.setattr(
            g178,
            "build_canonical_gold_market_facts_snapshot_v1",
            projector_spy,
        )
        context.setattr(
            g191,
            "build_canonical_gold_session_spread_freshness_facts_v1",
            facts_spy,
        )
        observed = _run_real_composition()

    assert calls == ["G185", "G178", "G191"]
    assert observed == genuine_anchor
    assert _detached_graph_ids(observed).isdisjoint(
        _detached_graph_ids(genuine_anchor)
    )
    assert fixture_before.matches(_fixture_state())


def test_invalid_inputs_are_deterministic_sanitized_and_fresh() -> None:
    results = tuple(
        g191.build_canonical_gold_session_spread_freshness_facts_v1(
            market_facts_snapshot=object()  # type: ignore[arg-type]
        )
        for _ in range(FAILURE_RUN_COUNT)
    )

    assert all(result == results[0] for result in results)
    assert len({id(result) for result in results}) == FAILURE_RUN_COUNT
    for result in results:
        _assert_exact_failure(
            result,
            status="CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_INPUT_INVALID",
            reason="GOLD_SESSION_SPREAD_FRESHNESS_INPUT_TYPE_INVALID",
        )
        _assert_no_sensitive_output(result)


def test_post_anchor_exceptions_are_deterministic_sanitized_and_fresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = _fixture_state()
    source_result, snapshot, genuine_anchor = _run_real_composition()
    frozen_snapshot = deepcopy(snapshot)
    _assert_exact_ready_facts(genuine_anchor)
    exception_calls: list[tuple[object, ...]] = []

    def raising_ready_result(*_: object) -> object:
        exception_calls.append(_)
        raise RuntimeError("sensitive composition failure detail")

    with monkeypatch.context() as context:
        context.setattr(g191, "_ready_result", raising_ready_result)
        failures = tuple(
            g191.build_canonical_gold_session_spread_freshness_facts_v1(
                market_facts_snapshot=snapshot
            )
            for _ in range(FAILURE_RUN_COUNT)
        )

    assert snapshot == frozen_snapshot
    assert len(exception_calls) == FAILURE_RUN_COUNT
    assert all(call[0] is snapshot and len(call) == 2 for call in exception_calls)
    assert all(result == failures[0] for result in failures)
    assert len({id(result) for result in failures}) == FAILURE_RUN_COUNT
    for result in failures:
        _assert_exact_failure(
            result,
            status="CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_SAFE_FAILURE",
            reason="GOLD_SESSION_SPREAD_FRESHNESS_EXCEPTION_SANITIZED",
        )
        _assert_no_sensitive_output(result)

    subsequent = _run_real_composition()
    assert subsequent == (source_result, snapshot, genuine_anchor)
    assert _detached_graph_ids(subsequent).isdisjoint(
        _detached_graph_ids((source_result, snapshot, genuine_anchor))
    )
    assert fixture_before.matches(_fixture_state())


def test_primary_verification_anchor_has_exact_unpatched_call_order() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_composition_is_deterministic_detached_and_fresh_for_five_runs"
    )
    production_calls = tuple(
        node.func.attr
        for node in ast.walk(primary)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "build_canonical_gold_market_facts_docs_fixture_source_v1",
            "build_canonical_gold_market_facts_snapshot_v1",
            "build_canonical_gold_session_spread_freshness_facts_v1",
        }
    )
    names = {node.id for node in ast.walk(primary) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(primary) if isinstance(node, ast.Attribute)
    }

    assert production_calls == (
        "build_canonical_gold_market_facts_docs_fixture_source_v1",
        "build_canonical_gold_market_facts_snapshot_v1",
        "build_canonical_gold_session_spread_freshness_facts_v1",
    )
    assert names.isdisjoint(
        {"monkeypatch", "patch", "Mock", "MagicMock", "spy"}
    )
    assert attributes.isdisjoint({"setattr", "setitem"})


def test_verification_scope_is_offline_non_activating_and_bounded() -> None:
    scope = " ".join((__doc__ or "").casefold().split())
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
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

    assert "deterministic offline composition verification only" in scope
    assert "w6 remains tests_only" in scope
    assert "does not verify a replayrunner w6 stage" in scope
    assert "activate a reader or mt4" in scope
    assert "ea, order, execution, or trading permission" in scope
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


def _run_real_composition() -> tuple[object, object, object]:
    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    result = g191.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=snapshot
    )
    return source_result, snapshot, result


def _fixture_state() -> _OpaqueFixtureState:
    fixture_dir = g185._FIXED_PATHS[2]
    entries = sorted(
        fixture_dir.rglob("*"),
        key=lambda entry: entry.relative_to(fixture_dir).as_posix(),
    )
    return _OpaqueFixtureState(
        tuple(_fixture_entry_state(entry, fixture_dir) for entry in entries)
    )


def _fixture_entry_state(
    entry: Path,
    fixture_dir: Path,
) -> tuple[tuple[str, ...], str, bytes, int]:
    relative_parts = entry.relative_to(fixture_dir).parts
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
    return relative_parts, kind, content, stat.st_mtime_ns


def _detached_graph_ids(value: object) -> frozenset[int]:
    identifiers: set[int] = set()
    visited: set[int] = set()

    def visit(node: object) -> None:
        node_id = id(node)
        if node_id in visited:
            return
        if is_dataclass(node) and not isinstance(node, type):
            visited.add(node_id)
            identifiers.add(node_id)
            for field in fields(node):
                visit(getattr(node, field.name))
        elif type(node) is tuple and node:
            visited.add(node_id)
            identifiers.add(node_id)
            for item in node:
                visit(item)

    visit(value)
    return frozenset(identifiers)


def _assert_exact_ready_source_result(result: object) -> None:
    assert type(result) is g185.CanonicalGoldMarketFactsSourceAdapterResultV1
    assert tuple(field.name for field in fields(type(result))) == SOURCE_RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.passed is True
    assert result.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_READY"
    assert result.reason_codes == ()
    assert result.warning_codes == ()
    assert result.source_available is True
    assert type(result.source) is g178.CanonicalGoldMarketFactsSourceV1
    assert tuple(field.name for field in fields(type(result.source))) == SOURCE_FIELDS
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected


def _assert_exact_ready_snapshot(snapshot: object) -> None:
    assert type(snapshot) is g178.CanonicalGoldMarketFactsSnapshotV1
    assert tuple(field.name for field in fields(type(snapshot))) == SNAPSHOT_FIELDS
    assert snapshot.contract_version == "1.0"
    assert snapshot.passed is True
    assert snapshot.status_code == "CANONICAL_GOLD_MARKET_FACTS_READY"
    assert snapshot.reason_codes == ()
    assert snapshot.warning_codes == ()
    assert snapshot.identity_available is True
    assert type(snapshot.quote) is g178.CanonicalGoldQuoteFactsV1
    assert type(snapshot.timeframes) is tuple and len(snapshot.timeframes) == 4
    assert type(snapshot.symbol_spec) is g178.CanonicalGoldSymbolFactsV1
    assert type(snapshot.freshness) is g178.CanonicalGoldFreshnessFactsV1
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(snapshot, name) is expected


def _assert_exact_ready_facts(result: object) -> None:
    assert type(result) is g191.CanonicalGoldSessionSpreadFreshnessFactsV1
    assert tuple(field.name for field in fields(type(result))) == FACTS_FIELDS
    assert result.contract_version == "1.0"
    assert result.facts_profile_version == (
        "canonical_gold_session_spread_freshness_profile_v1"
    )
    assert result.passed is True
    assert result.status_code == "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY"
    assert result.reason_codes == ()
    assert result.warning_codes == ()
    assert result.identity_available is True
    assert result.session == g191.CanonicalGoldSessionFactsV1(
        utc_weekday_code="FRIDAY",
        utc_second_of_day=9005,
        session_bucket_code="ASIA_UTC",
        window_start_second_utc=0,
        window_end_second_utc=28800,
        seconds_since_window_start=9005,
        seconds_until_window_end=19795,
        observed_writer_session_status_label="unknown",
    )
    assert result.spread == g191.CanonicalGoldSpreadFactsV1(
        bid_decimal="2300.50",
        ask_decimal="2300.80",
        mid_decimal="2300.650",
        spread_decimal="0.30",
        spread_points=30,
        digits=2,
        point_decimal="0.01",
        spread_to_mid_ppm_decimal="130.397931",
    )
    assert result.freshness == g191.CanonicalGoldSourceFreshnessFactsV1(
        tick_age_microseconds=5_000_000,
        bars_payload_age_microseconds=5_000_000,
        symbol_spec_age_microseconds=5_000_000,
        maximum_source_age_microseconds=5_000_000,
        oldest_source_component_code="TICK",
    )
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected


def _assert_exact_failure(result: object, *, status: str, reason: str) -> None:
    assert type(result) is g191.CanonicalGoldSessionSpreadFreshnessFactsV1
    assert tuple(field.name for field in fields(type(result))) == FACTS_FIELDS
    assert result.contract_version == "1.0"
    assert result.facts_profile_version == (
        "canonical_gold_session_spread_freshness_profile_v1"
    )
    assert result.passed is False
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.warning_codes == ()
    assert result.identity_available is False
    assert (
        result.bundle_schema_version,
        result.bundle_id,
        result.sequence,
        result.canonical_symbol,
        result.broker_symbol,
        result.reference_time_utc,
    ) == (None, None, None, None, None, None)
    assert result.session is None
    assert result.spread is None
    assert result.freshness is None
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected


def _source_identity(source: object) -> tuple[object, ...]:
    return (
        source.bundle_schema_version,
        source.bundle_id,
        source.sequence,
        source.canonical_symbol,
        source.broker_symbol,
        source.reference_time_utc,
    )


def _snapshot_identity(snapshot: object) -> tuple[object, ...]:
    return (
        snapshot.bundle_schema_version,
        snapshot.bundle_id,
        snapshot.sequence,
        snapshot.canonical_symbol,
        snapshot.broker_symbol,
        snapshot.reference_time_utc,
    )


def _facts_identity(result: object) -> tuple[object, ...]:
    return (
        result.bundle_schema_version,
        result.bundle_id,
        result.sequence,
        result.canonical_symbol,
        result.broker_symbol,
        result.reference_time_utc,
    )


def _assert_no_sensitive_output(*values: object) -> None:
    rendered = " ".join(repr(value).casefold() for value in values)
    forbidden = (
        str(g185._FIXED_PATHS[1]).casefold(),
        str(g185._FIXED_PATHS[2]).casefold(),
        "snapshot_manifest.json",
        "live_tick.json",
        "latest_bars.json",
        "symbol_spec.json",
        "account_snapshot.json",
        "raw_payload",
        "payloads_by_filename",
        "digest",
        "checksum",
        "traceback",
        "exception_text",
        "sensitive composition failure detail",
        "private_token",
        "attempt_token",
        "internal_source_status",
        "execution_payload",
        "order_ticket",
    )
    assert not any(value in rendered for value in forbidden)
