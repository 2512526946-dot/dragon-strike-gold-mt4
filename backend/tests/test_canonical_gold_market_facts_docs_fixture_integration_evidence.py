"""Genuine offline fixture integration evidence only.

This evidence keeps W6 TESTS_ONLY. It is not deterministic verification,
reader or MT4 activation, execution authority, or trading permission.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from pathlib import Path

import pytest

from app.services import canonical_gold_market_facts_docs_fixture_integration as integration
from app.services import canonical_gold_market_facts_source_adapter as adapter
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldBarSourceV1,
    CanonicalGoldMarketFactsSourceV1,
    CanonicalGoldSymbolSpecSourceV1,
    CanonicalGoldTickSourceV1,
    CanonicalGoldTimeframeSourceV1,
    CanonicalGoldUpstreamEvidenceV1,
)


FIXTURE_FILENAMES = (
    "snapshot_manifest.json",
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
RESULT_FIELDS = (
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


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueFixtureState:
    _entries: tuple[tuple[tuple[str, ...], str, bytes, int], ...]

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def matches(self, other: object) -> bool:
        return type(other) is _OpaqueFixtureState and self._entries == other._entries

    def __repr__(self) -> str:
        return "<fixture-state:redacted>"


def test_fixed_fixture_traverses_real_w1_g182_g185_chain() -> None:
    fixture_before = _fixture_state()

    first = integration.build_canonical_gold_market_facts_docs_fixture_source_v1()
    second = integration.build_canonical_gold_market_facts_docs_fixture_source_v1()

    assert fixture_before.matches(_fixture_state())
    assert first == second
    assert first is not second
    _assert_exact_ready_result(first)
    _assert_exact_ready_result(second)
    _assert_fresh_detached_sources(first, second)
    _assert_no_sensitive_output(first)
    _assert_no_sensitive_output(second)


def test_delegating_spies_observe_one_real_adapter_reader_gate_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_adapter = (
        integration.build_server_owned_canonical_gold_market_facts_source_v1
    )
    real_reader = adapter._read_accepted_attempt
    real_gate = adapter._evaluate_data_quality
    calls: list[tuple[str, object]] = []
    observed_reader_result: list[dict[str, object]] = []

    def adapter_spy(
        *,
        authority: adapter._CanonicalGoldMarketFactsSourceAuthorityV1,
    ) -> adapter.CanonicalGoldMarketFactsSourceAdapterResultV1:
        calls.append(("adapter", authority))
        return real_adapter(authority=authority)

    def reader_spy(**kwargs: object) -> tuple[dict[str, object], object]:
        calls.append(("reader", kwargs))
        reader_result, capsule = real_reader(**kwargs)
        observed_reader_result.append(reader_result)
        return reader_result, capsule

    def gate_spy(**kwargs: object) -> dict[str, object]:
        calls.append(("gate", kwargs))
        return real_gate(**kwargs)

    monkeypatch.setattr(
        integration,
        "build_server_owned_canonical_gold_market_facts_source_v1",
        adapter_spy,
    )
    monkeypatch.setattr(integration, "_EXPECTED_BUILD_ADAPTER", adapter_spy)
    monkeypatch.setattr(adapter, "_read_accepted_attempt", reader_spy)
    monkeypatch.setattr(adapter, "_evaluate_data_quality", gate_spy)
    fixture_before = _fixture_state()

    result = integration.build_canonical_gold_market_facts_docs_fixture_source_v1()

    assert fixture_before.matches(_fixture_state())
    assert [name for name, _ in calls] == ["adapter", "reader", "gate"]
    assert len(observed_reader_result) == 1
    authority = calls[0][1]
    assert integration._authority_snapshot(authority) == integration._authority_snapshot(
        integration._build_fresh_authority()
    )
    reader_kwargs = calls[1][1]
    assert type(reader_kwargs) is dict
    assert reader_kwargs == {
        "allowed_root": authority.allowed_root,
        "bundle_dir": authority.bundle_dir,
        "now_utc": authority.reference_time_utc,
        "previous_identity": None,
        "read_policy": authority.read_policy,
        "filesystem_policy": authority.filesystem_policy,
    }
    gate_kwargs = calls[2][1]
    assert type(gate_kwargs) is dict
    assert gate_kwargs == {
        "reader_result": observed_reader_result[0],
        "policy": authority.data_quality_policy,
    }
    checksum = next(
        component
        for component in observed_reader_result[0]["component_statuses"]
        if component["component_name"] == "checksum"
    )
    assert checksum["status_code"] == (
        "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_NOT_REQUIRED"
    )
    assert observed_reader_result[0]["checksum_checked"] is False
    assert observed_reader_result[0]["checksum_passed"] is True
    _assert_exact_ready_result(result)


def test_primary_integration_anchor_has_no_main_chain_patch() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_fixed_fixture_traverses_real_w1_g182_g185_chain"
    )
    names = {node.id for node in ast.walk(primary) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(primary) if isinstance(node, ast.Attribute)
    }

    assert names.isdisjoint(
        {"monkeypatch", "patch", "Mock", "MagicMock", "adapter_spy", "reader_spy", "gate_spy"}
    )
    assert attributes.isdisjoint({"setattr", "setitem"})


def test_fixture_state_evidence_is_opaque_and_covers_complete_tree() -> None:
    fixture_dir = integration._FIXED_PATHS[2]
    state = _fixture_state()

    assert state.entry_count == sum(1 for _ in fixture_dir.rglob("*"))
    assert state.matches(_fixture_state())
    assert repr(state) == "<fixture-state:redacted>"
    assert not any(value in repr(state) for value in FIXTURE_FILENAMES)


def test_integration_evidence_scope_is_non_activating() -> None:
    scope = (__doc__ or "").casefold()
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

    assert "genuine offline fixture integration evidence only" in scope
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
    fixture_dir = integration._FIXED_PATHS[2]
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


def _assert_exact_ready_result(
    result: adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> None:
    assert type(result) is adapter.CanonicalGoldMarketFactsSourceAdapterResultV1
    assert tuple(field.name for field in fields(type(result))) == RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.passed is True
    assert result.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_READY"
    assert result.reason_codes == ()
    assert result.warning_codes == ()
    assert result.source_available is True
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected

    source = result.source
    assert type(source) is CanonicalGoldMarketFactsSourceV1
    assert tuple(field.name for field in fields(type(source))) == SOURCE_FIELDS
    assert (
        source.contract_version,
        source.bundle_schema_version,
        source.bundle_id,
        source.sequence,
        source.canonical_symbol,
        source.broker_symbol,
        source.reference_time_utc,
        source.policy_profile_version,
    ) == (
        "1.0",
        "1.0",
        "demo-bundle-000000000001",
        1,
        "XAUUSD",
        "GOLD",
        "2026-07-10T02:30:05.000000Z",
        "canonical_gold_market_facts_policy_v1",
    )
    assert type(source.upstream_evidence) is CanonicalGoldUpstreamEvidenceV1
    assert (
        source.upstream_evidence.reader_passed,
        source.upstream_evidence.reader_status_code,
        source.upstream_evidence.value_status_code,
        source.upstream_evidence.data_quality_passed,
        source.upstream_evidence.data_quality_status_code,
        source.upstream_evidence.ready_for_readonly_analysis,
        source.upstream_evidence.warning_codes,
        source.upstream_evidence.same_attempt_identity_bound,
    ) == (
        True,
        "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID",
        "CANONICAL_MT4_BUNDLE_V1_VALUE_VALID",
        True,
        "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
        True,
        (),
        True,
    )
    assert type(source.live_tick) is CanonicalGoldTickSourceV1
    assert source.bars_generated_at_utc == "2026-07-10T02:30:00Z"
    assert type(source.timeframes) is tuple
    assert tuple(
        (facts.timeframe, facts.period_seconds, len(facts.bars))
        for facts in source.timeframes
    ) == (
        ("M15", 900, 2),
        ("H1", 3600, 2),
        ("H4", 14400, 2),
        ("D1", 86400, 2),
    )
    assert all(
        type(facts) is CanonicalGoldTimeframeSourceV1
        for facts in source.timeframes
    )
    assert all(type(facts.bars) is tuple for facts in source.timeframes)
    assert all(
        type(bar) is CanonicalGoldBarSourceV1
        for facts in source.timeframes
        for bar in facts.bars
    )
    assert type(source.symbol_spec) is CanonicalGoldSymbolSpecSourceV1


def _assert_fresh_detached_sources(
    first: adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
    second: adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> None:
    first_source = first.source
    second_source = second.source
    assert first_source is not None and second_source is not None
    assert first_source is not second_source
    assert first_source.upstream_evidence is not second_source.upstream_evidence
    assert first_source.live_tick is not second_source.live_tick
    assert first_source.timeframes is not second_source.timeframes
    assert first_source.symbol_spec is not second_source.symbol_spec
    for first_timeframe, second_timeframe in zip(
        first_source.timeframes,
        second_source.timeframes,
        strict=True,
    ):
        assert first_timeframe is not second_timeframe
        assert first_timeframe.bars is not second_timeframe.bars
        assert all(
            first_bar is not second_bar
            for first_bar, second_bar in zip(
                first_timeframe.bars,
                second_timeframe.bars,
                strict=True,
            )
        )


def _assert_no_sensitive_output(
    result: adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> None:
    serialized = repr(result).casefold()
    forbidden = (
        str(integration._FIXED_PATHS[1]).casefold(),
        str(integration._FIXED_PATHS[2]).casefold(),
        *FIXTURE_FILENAMES,
        "raw_payload",
        "payloads_by_filename",
        "digest",
        "checksum",
        "traceback",
        "exception_text",
        "private_token",
        "attempt_token",
        "execution_payload",
        "order_ticket",
    )
    assert not any(value in serialized for value in forbidden)
