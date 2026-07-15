"""Deterministic offline verification only; never activation or later W6 authority.

This verifies the integrated G185 -> G182 -> W1 docs-fixture boundary. W6 remains
TESTS_ONLY. It does not verify a ReplayRunner W6 stage, activate a reader or MT4,
or grant EA, order, execution, or trading permission.
"""

from __future__ import annotations

import ast
from copy import deepcopy
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
REAL_RUN_COUNT = 5
FAILURE_RUN_COUNT = 3


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueFixtureState:
    _entries: tuple[tuple[tuple[str, ...], str, bytes, int], ...]

    def matches(self, other: object) -> bool:
        return type(other) is _OpaqueFixtureState and self._entries == other._entries

    def __repr__(self) -> str:
        return "<fixture-state:redacted>"


@dataclass(frozen=True, slots=True, repr=False)
class _OpaqueAuthorityState:
    _snapshot: tuple[object, ...]

    def matches(self, other: object) -> bool:
        return (
            type(other) is _OpaqueAuthorityState
            and self._snapshot == other._snapshot
        )

    def __repr__(self) -> str:
        return "<authority-state:redacted>"


def test_real_fixture_boundary_is_deterministic_and_fresh_for_five_runs() -> None:
    fixture_before = _fixture_state()
    authority_before = _authority_state()
    fixed_paths = integration._FIXED_PATHS
    fixed_identity = integration._FIXTURE_IDENTITY
    reference_time = integration._REFERENCE_TIME

    results = tuple(
        integration.build_canonical_gold_market_facts_docs_fixture_source_v1()
        for _ in range(REAL_RUN_COUNT)
    )

    assert all(result == results[0] for result in results)
    object_ids = tuple(_detached_object_ids(result) for result in results)
    assert all(len(ids) == len(object_ids[0]) for ids in object_ids)
    for position in range(len(object_ids[0])):
        assert len({ids[position] for ids in object_ids}) == REAL_RUN_COUNT
    for result in results:
        _assert_exact_ready_result(result)
        _assert_no_sensitive_output(result)

    assert fixture_before.matches(_fixture_state())
    assert authority_before.matches(_authority_state())
    assert integration._FIXED_PATHS is fixed_paths
    assert integration._FIXTURE_IDENTITY is fixed_identity
    assert integration._REFERENCE_TIME is reference_time


def test_tampering_with_one_detached_result_cannot_change_a_later_real_run() -> None:
    fixture_before = _fixture_state()
    authority_before = _authority_state()
    first = integration.build_canonical_gold_market_facts_docs_fixture_source_v1()
    expected = deepcopy(first)
    assert first.source is not None

    object.__setattr__(first, "status_code", "CALLER_LOCAL_MUTATION")
    object.__setattr__(first.source, "bundle_id", "caller-local-mutation")

    subsequent = integration.build_canonical_gold_market_facts_docs_fixture_source_v1()

    assert first != expected
    assert subsequent == expected
    assert subsequent is not first
    assert subsequent.source is not first.source
    _assert_exact_ready_result(subsequent)
    _assert_no_sensitive_output(subsequent)
    assert fixture_before.matches(_fixture_state())
    assert authority_before.matches(_authority_state())


def test_exception_failures_are_deterministic_sanitized_and_fresh_after_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    genuine_anchor = (
        integration.build_canonical_gold_market_facts_docs_fixture_source_v1()
    )
    _assert_exact_ready_result(genuine_anchor)
    fixture_before = _fixture_state()
    authority_before = _authority_state()
    calls: list[str] = []

    def raising_adapter(**_: object) -> object:
        calls.append("adapter")
        raise RuntimeError("sensitive failure detail")

    with monkeypatch.context() as context:
        context.setattr(
            integration,
            "build_server_owned_canonical_gold_market_facts_source_v1",
            raising_adapter,
        )
        context.setattr(integration, "_EXPECTED_BUILD_ADAPTER", raising_adapter)
        failures = tuple(
            integration.build_canonical_gold_market_facts_docs_fixture_source_v1()
            for _ in range(FAILURE_RUN_COUNT)
        )

    assert calls == ["adapter"] * FAILURE_RUN_COUNT
    assert all(result == failures[0] for result in failures)
    assert len({id(result) for result in failures}) == FAILURE_RUN_COUNT
    for result in failures:
        _assert_exact_sanitized_failure(result)
        _assert_no_sensitive_output(result)

    subsequent = integration.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert subsequent == genuine_anchor
    assert subsequent is not genuine_anchor
    assert subsequent.source is not genuine_anchor.source
    _assert_exact_ready_result(subsequent)
    assert fixture_before.matches(_fixture_state())
    assert authority_before.matches(_authority_state())


def test_primary_verification_anchor_has_no_main_chain_patch() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_real_fixture_boundary_is_deterministic_and_fresh_for_five_runs"
    )
    names = {node.id for node in ast.walk(primary) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(primary) if isinstance(node, ast.Attribute)
    }

    assert names.isdisjoint(
        {
            "monkeypatch",
            "patch",
            "Mock",
            "MagicMock",
            "adapter_spy",
            "reader_spy",
            "gate_spy",
        }
    )
    assert attributes.isdisjoint({"setattr", "setitem"})


def test_verification_scope_is_offline_non_activating_and_bounded() -> None:
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
    production_source = Path(integration.__file__).read_text(encoding="utf-8")

    assert "deterministic offline verification only" in scope
    assert "w6 remains" in scope and "tests_only" in scope
    assert "does not verify a replayrunner w6 stage" in scope
    assert "activate a reader or mt4" in scope
    assert "execution" in scope and "trading permission" in scope
    assert not any(
        forbidden in imported
        for forbidden in (
            "fastapi",
            "requests",
            "httpx",
            "socket",
            "subprocess",
        )
        for imported in imports
    )
    assert "canonical_bundle_replay_runner" not in production_source
    assert "app.api" not in production_source
    assert "os.environ" not in production_source
    assert "get_settings" not in production_source


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


def _authority_state() -> _OpaqueAuthorityState:
    snapshot = integration._authority_snapshot(integration._build_fresh_authority())
    assert type(snapshot) is tuple
    return _OpaqueAuthorityState(snapshot)


def _detached_object_ids(
    result: adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> tuple[int, ...]:
    source = result.source
    assert source is not None
    objects: list[object] = [
        result,
        source,
        source.upstream_evidence,
        source.live_tick,
        source.timeframes,
        source.symbol_spec,
    ]
    for timeframe in source.timeframes:
        objects.extend((timeframe, timeframe.bars, *timeframe.bars))
    return tuple(id(value) for value in objects)


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


def _assert_exact_sanitized_failure(
    result: adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> None:
    assert type(result) is adapter.CanonicalGoldMarketFactsSourceAdapterResultV1
    assert tuple(field.name for field in fields(type(result))) == RESULT_FIELDS
    assert result.contract_version == "1.0"
    assert result.passed is False
    assert result.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE"
    assert result.reason_codes == ("GOLD_SOURCE_EXCEPTION_SANITIZED",)
    assert result.warning_codes == ()
    assert result.source_available is False
    assert result.source is None
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected


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
        "sensitive failure detail",
        "private_token",
        "attempt_token",
        "execution_payload",
        "order_ticket",
    )
    assert not any(value in serialized for value in forbidden)
