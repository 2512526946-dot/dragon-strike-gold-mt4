"""Genuine offline G185 -> G178 -> G191 composition evidence only.

This keeps W6 TESTS_ONLY. It is not deterministic verification, reader or MT4
activation, execution authority, or trading permission.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from pathlib import Path

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


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueFixtureState:
    entries: tuple[tuple[tuple[str, ...], str, bytes, int], ...]

    def matches(self, other: object) -> bool:
        return type(other) is _OpaqueFixtureState and self.entries == other.entries

    def __repr__(self) -> str:
        return "<fixture-state:redacted>"


def test_real_fixture_composes_g185_g178_g191_once_without_patching() -> None:
    fixture_before = _fixture_state()

    source_result = g185.build_canonical_gold_market_facts_docs_fixture_source_v1()
    snapshot = g178.build_canonical_gold_market_facts_snapshot_v1(
        validated_source=source_result.source
    )
    result = g191.build_canonical_gold_session_spread_freshness_facts_v1(
        market_facts_snapshot=snapshot
    )

    assert fixture_before.matches(_fixture_state())
    _assert_ready_source_result(source_result)
    _assert_ready_snapshot(snapshot)
    _assert_ready_session_spread_freshness(result)
    assert (
        _source_identity(source_result.source)
        == _snapshot_identity(snapshot)
        == _facts_identity(result)
        == IDENTITY
    )
    assert snapshot.quote is not source_result.source.live_tick
    assert snapshot.symbol_spec is not source_result.source.symbol_spec
    assert snapshot.freshness is not source_result.source
    assert snapshot.timeframes is not source_result.source.timeframes
    for source_timeframe, snapshot_timeframe in zip(
        source_result.source.timeframes,
        snapshot.timeframes,
        strict=True,
    ):
        assert snapshot_timeframe is not source_timeframe
        assert snapshot_timeframe.bars is not source_timeframe.bars
        assert all(
            snapshot_bar is not source_bar
            for source_bar, snapshot_bar in zip(
                source_timeframe.bars,
                snapshot_timeframe.bars,
                strict=True,
            )
        )
    assert result.session is not snapshot
    assert result.spread is not snapshot.quote
    assert result.freshness is not snapshot.freshness
    _assert_no_sensitive_output(source_result, snapshot, result)


def test_primary_composition_call_order_is_exact_and_unpatched() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_fixture_composes_g185_g178_g191_once_without_patching"
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
    assert names.isdisjoint({"monkeypatch", "patch", "Mock", "MagicMock", "spy"})
    assert attributes.isdisjoint({"setattr", "setitem"})


def test_composition_evidence_scope_remains_non_activating() -> None:
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

    assert "genuine offline g185 -> g178 -> g191 composition evidence only" in scope
    assert "keeps w6 tests_only" in scope
    assert "not deterministic verification" in scope
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


def _assert_ready_source_result(
    result: object,
) -> None:
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


def _assert_ready_snapshot(snapshot: object) -> None:
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


def _assert_ready_session_spread_freshness(result: object) -> None:
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


def _source_identity(source: g178.CanonicalGoldMarketFactsSourceV1) -> tuple[
    str,
    str,
    int,
    str,
    str,
    str,
]:
    return (
        source.bundle_schema_version,
        source.bundle_id,
        source.sequence,
        source.canonical_symbol,
        source.broker_symbol,
        source.reference_time_utc,
    )


def _snapshot_identity(snapshot: g178.CanonicalGoldMarketFactsSnapshotV1) -> tuple[
    str | None,
    str | None,
    int | None,
    str | None,
    str | None,
    str | None,
]:
    return (
        snapshot.bundle_schema_version,
        snapshot.bundle_id,
        snapshot.sequence,
        snapshot.canonical_symbol,
        snapshot.broker_symbol,
        snapshot.reference_time_utc,
    )


def _facts_identity(
    result: g191.CanonicalGoldSessionSpreadFreshnessFactsV1,
) -> tuple[str | None, str | None, int | None, str | None, str | None, str | None]:
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
