"""Genuine offline G185 -> G178 -> G196 composition evidence only.

This keeps W6 TESTS_ONLY. It is not deterministic verification, reader or MT4
activation, ReplayRunner staging, execution authority, or trading permission.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path

import pytest

from app.services import canonical_gold_market_facts_docs_fixture_integration as g185
from app.services import canonical_gold_market_facts_snapshot_projector as g178
from app.services import canonical_gold_volatility_structure_facts as g196


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
    "timeframes",
    "total_pair_count",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
TIMEFRAME_FIELDS = (
    "timeframe",
    "period_seconds",
    "source_bar_count",
    "pair_count",
    "bar_pairs",
)
PAIR_FIELDS = (
    "previous_open_time_utc",
    "current_open_time_utc",
    "previous_range_decimal",
    "current_range_decimal",
    "true_range_decimal",
    "body_signed_decimal",
    "body_absolute_decimal",
    "upper_wick_decimal",
    "lower_wick_decimal",
    "close_change_decimal",
    "high_change_decimal",
    "low_change_decimal",
    "direction_code",
    "range_relation_code",
    "range_containment_code",
    "current_high_vs_previous_high_code",
    "current_low_vs_previous_low_code",
    "current_close_vs_previous_range_code",
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
    "1.0",
    "demo-bundle-000000000001",
    1,
    "XAUUSD",
    "GOLD",
    "2026-07-10T02:30:05.000000Z",
)
EXPECTED_TIMEFRAMES = (
    ("M15", 900, 2, 1),
    ("H1", 3600, 2, 1),
    ("H4", 14400, 2, 1),
    ("D1", 86400, 2, 1),
)
EXPECTED_PAIRS = (
    (
        "2026-07-10T02:00:00Z",
        "2026-07-10T02:15:00Z",
        "2.20",
        "1.60",
        "1.60",
        "0.60",
        "0.60",
        "0.60",
        "0.40",
        "0.60",
        "0.30",
        "0.90",
        "UP",
        "CONTRACTED",
        "SHIFTED_UP",
        "ABOVE_PREVIOUS_HIGH",
        "ABOVE_PREVIOUS_LOW",
        "INSIDE_PREVIOUS_RANGE",
    ),
    (
        "2026-07-10T00:00:00Z",
        "2026-07-10T01:00:00Z",
        "4.80",
        "2.50",
        "2.50",
        "1.10",
        "1.10",
        "0.60",
        "0.80",
        "1.10",
        "0.70",
        "3.00",
        "UP",
        "CONTRACTED",
        "SHIFTED_UP",
        "ABOVE_PREVIOUS_HIGH",
        "ABOVE_PREVIOUS_LOW",
        "ABOVE_PREVIOUS_HIGH",
    ),
    (
        "2026-07-09T16:00:00Z",
        "2026-07-09T20:00:00Z",
        "10.30",
        "5.50",
        "5.50",
        "4.40",
        "4.40",
        "0.60",
        "0.50",
        "4.40",
        "3.20",
        "8.00",
        "UP",
        "CONTRACTED",
        "SHIFTED_UP",
        "ABOVE_PREVIOUS_HIGH",
        "ABOVE_PREVIOUS_LOW",
        "ABOVE_PREVIOUS_HIGH",
    ),
    (
        "2026-07-08T00:00:00Z",
        "2026-07-09T00:00:00Z",
        "14.20",
        "22.60",
        "22.60",
        "18.20",
        "18.20",
        "1.80",
        "2.60",
        "18.20",
        "17.20",
        "8.80",
        "UP",
        "EXPANDED",
        "SHIFTED_UP",
        "ABOVE_PREVIOUS_HIGH",
        "ABOVE_PREVIOUS_LOW",
        "ABOVE_PREVIOUS_HIGH",
    ),
)


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueFixtureState:
    entries: tuple[tuple[tuple[str, ...], str, bytes, int], ...]

    def matches(self, other: object) -> bool:
        return type(other) is _OpaqueFixtureState and self.entries == other.entries

    def __repr__(self) -> str:
        return "<fixture-state:redacted>"


def test_real_fixture_composes_g185_g178_g196_once_without_patching() -> None:
    fixture_before = _fixture_state()

    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    source_before = deepcopy(source_result.source)
    snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    assert source_result.source == source_before
    snapshot_before = deepcopy(snapshot)
    result = g196.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )

    assert fixture_before.matches(_fixture_state())
    assert snapshot == snapshot_before
    _assert_ready_source_result(source_result)
    _assert_ready_snapshot(snapshot)
    _assert_ready_result(result, snapshot)
    assert _snapshot_identity(snapshot) == _result_identity(result) == IDENTITY
    assert _object_graph_ids(snapshot).isdisjoint(_object_graph_ids(result))
    _assert_no_sensitive_output(source_result, snapshot, result)


def test_repeated_real_composition_is_equal_fresh_detached_and_non_mutating() -> None:
    fixture_before = _fixture_state()
    runs = tuple(_compose_once() for _ in range(3))

    assert fixture_before.matches(_fixture_state())
    assert runs[0][2] == runs[1][2] == runs[2][2]
    for index, (source, snapshot, result) in enumerate(runs):
        _assert_ready_result(result, snapshot)
        assert _object_graph_ids(source).isdisjoint(_object_graph_ids(snapshot))
        assert _object_graph_ids(snapshot).isdisjoint(_object_graph_ids(result))
        for later_source, later_snapshot, later_result in runs[index + 1 :]:
            assert _object_graph_ids(source).isdisjoint(
                _object_graph_ids(later_source)
            )
            assert _object_graph_ids(snapshot).isdisjoint(
                _object_graph_ids(later_snapshot)
            )
            assert _object_graph_ids(result).isdisjoint(
                _object_graph_ids(later_result)
            )


def test_delegating_spies_confirm_one_ordered_call_after_genuine_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_before = _fixture_state()
    genuine_source, genuine_snapshot, genuine_result = _compose_once()
    _assert_ready_result(genuine_result, genuine_snapshot)

    original_source = g185.build_canonical_gold_market_facts_docs_fixture_source_v1
    original_projector = g178.build_canonical_gold_market_facts_snapshot_v1
    original_builder = g196.build_canonical_gold_volatility_structure_facts_v1
    calls: list[str] = []
    observed_authority: list[tuple[object, ...]] = []

    def source_wrapper() -> object:
        calls.append("G185")
        return original_source()

    def projector_wrapper(*, validated_source: object) -> object:
        calls.append("G178")
        observed_authority.append(_source_identity(validated_source))
        return original_projector(validated_source=validated_source)

    def builder_wrapper(*, market_facts_snapshot: object) -> object:
        calls.append("G196")
        observed_authority.append(_snapshot_identity(market_facts_snapshot))
        return original_builder(market_facts_snapshot=market_facts_snapshot)

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
            g196,
            "build_canonical_gold_volatility_structure_facts_v1",
            builder_wrapper,
        )
        source, snapshot, result = _compose_once()

    assert calls == ["G185", "G178", "G196"]
    assert observed_authority == [IDENTITY, IDENTITY]
    assert (source, snapshot, result) == (
        genuine_source,
        genuine_snapshot,
        genuine_result,
    )
    assert fixture_before.matches(_fixture_state())


def test_primary_anchor_is_exact_unpatched_and_scope_is_non_activating() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_fixture_composes_g185_g178_g196_once_without_patching"
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
            "build_canonical_gold_volatility_structure_facts_v1",
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
        "build_canonical_gold_volatility_structure_facts_v1",
    )
    assert names.isdisjoint({"monkeypatch", "patch", "Mock", "MagicMock", "spy"})
    assert attributes.isdisjoint({"setattr", "setitem"})
    assert "genuine offline g185 -> g178 -> g196 composition evidence only" in scope
    assert "keeps w6 tests_only" in scope
    assert "not deterministic verification" in scope
    assert "reader or mt4 activation" in scope
    assert "replayrunner staging" in scope
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


def _compose_once() -> tuple[object, object, object]:
    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert source_result.source is not None
    source_before = deepcopy(source_result.source)
    snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    assert source_result.source == source_before
    snapshot_before = deepcopy(snapshot)
    result = g196.build_canonical_gold_volatility_structure_facts_v1(
        market_facts_snapshot=snapshot
    )
    assert snapshot == snapshot_before
    return source_result.source, snapshot, result


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


def _assert_ready_source_result(result: object) -> None:
    assert type(result) is g185.CanonicalGoldMarketFactsSourceAdapterResultV1
    assert tuple(field.name for field in fields(type(result))) == SOURCE_RESULT_FIELDS
    assert result.passed is True
    assert result.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_READY"
    assert result.reason_codes == ()
    assert result.warning_codes == ()
    assert result.source_available is True
    assert type(result.source) is g178.CanonicalGoldMarketFactsSourceV1
    assert tuple(field.name for field in fields(type(result.source))) == SOURCE_FIELDS
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected


def _assert_ready_snapshot(snapshot: object) -> None:
    assert type(snapshot) is g178.CanonicalGoldMarketFactsSnapshotV1
    assert tuple(field.name for field in fields(type(snapshot))) == SNAPSHOT_FIELDS
    assert snapshot.passed is True
    assert snapshot.status_code == "CANONICAL_GOLD_MARKET_FACTS_READY"
    assert snapshot.reason_codes == ()
    assert snapshot.warning_codes == ()
    assert snapshot.identity_available is True
    assert type(snapshot.timeframes) is tuple and len(snapshot.timeframes) == 4
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(snapshot, name) is expected


def _assert_ready_result(result: object, snapshot: object) -> None:
    assert type(result) is g196.CanonicalGoldVolatilityStructureFactsV1
    assert tuple(field.name for field in fields(type(result))) == RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.facts_profile_version == (
        "canonical_gold_volatility_structure_profile_v1"
    )
    assert result.passed is True
    assert result.status_code == "CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY"
    assert result.reason_codes == ()
    assert result.warning_codes == ()
    assert result.identity_available is True
    assert result.total_pair_count == 4
    assert tuple(
        (
            timeframe.timeframe,
            timeframe.period_seconds,
            timeframe.source_bar_count,
            timeframe.pair_count,
        )
        for timeframe in result.timeframes
    ) == EXPECTED_TIMEFRAMES
    assert all(
        tuple(field.name for field in fields(type(timeframe))) == TIMEFRAME_FIELDS
        for timeframe in result.timeframes
    )
    assert tuple(
        tuple(getattr(timeframe.bar_pairs[0], name) for name in PAIR_FIELDS)
        for timeframe in result.timeframes
    ) == EXPECTED_PAIRS
    assert all(
        tuple(field.name for field in fields(type(timeframe.bar_pairs[0])))
        == PAIR_FIELDS
        for timeframe in result.timeframes
    )
    assert tuple(
        (pair.previous_open_time_utc, pair.current_open_time_utc)
        for timeframe in result.timeframes
        for pair in timeframe.bar_pairs
    ) == tuple(
        (timeframe.bars[0].open_time_utc, timeframe.bars[1].open_time_utc)
        for timeframe in snapshot.timeframes
    )
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected


def _source_identity(source: object) -> tuple[object, ...]:
    return (
        source.contract_version,
        source.bundle_schema_version,
        source.bundle_id,
        source.sequence,
        source.canonical_symbol,
        source.broker_symbol,
        source.reference_time_utc,
    )


def _snapshot_identity(snapshot: object) -> tuple[object, ...]:
    return (
        snapshot.contract_version,
        snapshot.bundle_schema_version,
        snapshot.bundle_id,
        snapshot.sequence,
        snapshot.canonical_symbol,
        snapshot.broker_symbol,
        snapshot.reference_time_utc,
    )


def _result_identity(result: object) -> tuple[object, ...]:
    return (
        result.source_contract_version,
        result.bundle_schema_version,
        result.bundle_id,
        result.sequence,
        result.canonical_symbol,
        result.broker_symbol,
        result.reference_time_utc,
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
    rendered = " ".join(repr(value).casefold() for value in values)
    for forbidden in (
        "absolute_path",
        "bundle_dir",
        "checksum",
        "raw_payload",
        "traceback",
        "exception_message",
        "authority_token",
        "internal_source_status",
    ):
        assert forbidden not in rendered
