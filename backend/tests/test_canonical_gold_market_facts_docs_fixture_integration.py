from __future__ import annotations

import ast
from dataclasses import fields
from datetime import UTC, datetime
import inspect
from pathlib import Path

import pytest

import app.services.canonical_gold_market_facts_docs_fixture_integration as integration_module
import app.services.canonical_gold_market_facts_source_adapter as adapter_module
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldBarSourceV1,
    CanonicalGoldMarketFactsSourceV1,
    CanonicalGoldSymbolSpecSourceV1,
    CanonicalGoldTickSourceV1,
    CanonicalGoldTimeframeSourceV1,
    CanonicalGoldUpstreamEvidenceV1,
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


def test_public_interface_and_fixed_authority_are_exact() -> None:
    assert integration_module.__all__ == (
        "build_canonical_gold_market_facts_docs_fixture_source_v1",
    )
    assert str(
        inspect.signature(
            integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1
        )
    ) == "() -> 'CanonicalGoldMarketFactsSourceAdapterResultV1'"

    repository_root, allowed_root, bundle_dir = integration_module._FIXED_PATHS
    assert repository_root == Path(integration_module.__file__).resolve().parents[3]
    assert allowed_root == repository_root / "docs" / "architecture" / "fixtures"
    assert bundle_dir == allowed_root / "canonical-mt4-demo-readonly-bundle-v1"
    assert type(repository_root) is type(allowed_root) is type(bundle_dir)
    assert integration_module._REFERENCE_TIME == datetime(
        2026, 7, 10, 2, 30, 5, tzinfo=UTC
    )
    assert integration_module._REFERENCE_TIME.tzinfo is UTC
    assert integration_module._FIXTURE_IDENTITY == (
        "1.0",
        "demo-bundle-000000000001",
        1,
        "XAUUSD",
        "GOLD",
    )

    first = integration_module._build_fresh_authority()
    second = integration_module._build_fresh_authority()
    assert tuple(field.name for field in fields(type(first))) == (
        "authority_token",
        "allowed_root",
        "bundle_dir",
        "reference_time_utc",
        "previous_identity",
        "read_policy",
        "filesystem_policy",
        "data_quality_policy",
        "policy_profile_version",
    )
    assert first is not second
    assert first.read_policy is not second.read_policy
    assert first.filesystem_policy is not second.filesystem_policy
    assert first.data_quality_policy is not second.data_quality_policy
    assert first.authority_token is adapter_module._AUTHORITY_TOKEN
    assert first.allowed_root == allowed_root
    assert first.bundle_dir == bundle_dir
    assert first.reference_time_utc == integration_module._REFERENCE_TIME
    assert first.previous_identity is None
    assert (
        first.read_policy.writer_heartbeat_max_age_seconds,
        first.read_policy.live_tick_max_age_seconds,
        first.read_policy.latest_bars_max_age_seconds,
        first.read_policy.symbol_spec_max_age_seconds,
        first.read_policy.account_snapshot_max_age_seconds,
        first.read_policy.max_future_skew_seconds,
    ) == (15, 10, 60, 86400, 30, 5)
    assert (
        first.filesystem_policy.manifest_max_bytes,
        first.filesystem_policy.live_tick_max_bytes,
        first.filesystem_policy.latest_bars_max_bytes,
        first.filesystem_policy.symbol_spec_max_bytes,
        first.filesystem_policy.account_snapshot_max_bytes,
        first.filesystem_policy.max_manifest_consistency_retries,
    ) == (65536, 32768, 2097152, 65536, 131072, 0)
    assert first.data_quality_policy.allow_upstream_warnings is False
    assert first.policy_profile_version == "canonical_gold_market_facts_policy_v1"

    with pytest.raises(TypeError):
        integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1(
            caller_path="forbidden"  # type: ignore[call-arg]
        )


def test_valid_ready_and_blocked_results_are_returned_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for expected in (_ready_result(), _blocked_result()):
        calls: list[str] = []

        def adapter_spy(**_: object) -> object:
            calls.append("adapter")
            return expected

        def validator_spy(*, result: object) -> bool:
            calls.append("validator")
            return adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
                result=result
            )

        def sanitizer_spy() -> object:
            calls.append("sanitizer")
            return (
                adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
            )

        _install_controlled_dependencies(
            monkeypatch,
            adapter=adapter_spy,
            validator=validator_spy,
            sanitizer=sanitizer_spy,
        )
        observed = (
            integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
        )
        assert observed is expected
        assert calls == ["adapter", "validator"]
        _assert_safety(observed)


@pytest.mark.parametrize("failure_kind", ("invalid", "exception", "validator_exception"))
def test_invalid_and_exceptional_adapter_results_are_sanitized_once(
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
) -> None:
    calls: list[str] = []

    def adapter_spy(**_: object) -> object:
        calls.append("adapter")
        if failure_kind == "exception":
            raise RuntimeError("sensitive adapter detail")
        return object()

    def validator_spy(*, result: object) -> bool:
        calls.append("validator")
        if failure_kind == "validator_exception":
            raise ValueError("sensitive validator detail")
        return adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=result
        )

    def sanitizer_spy() -> object:
        calls.append("sanitizer")
        return adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()

    _install_controlled_dependencies(
        monkeypatch,
        adapter=adapter_spy,
        validator=validator_spy,
        sanitizer=sanitizer_spy,
    )
    result = integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
    _assert_sanitized(result)
    expected_calls = (
        ["adapter", "sanitizer"]
        if failure_kind == "exception"
        else ["adapter", "validator", "sanitizer"]
    )
    assert calls == expected_calls
    assert "sensitive" not in repr(result)


def test_ready_identity_mismatch_and_post_call_drift_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for outcome in ("identity", "authority_drift"):
        calls: list[str] = []
        ready = _ready_result(
            bundle_id=(
                "demo-bundle-000000000999"
                if outcome == "identity"
                else "demo-bundle-000000000001"
            )
        )

        def adapter_spy(*, authority: object) -> object:
            calls.append("adapter")
            if outcome == "authority_drift":
                object.__setattr__(
                    authority.read_policy,
                    "live_tick_max_age_seconds",
                    11,
                )
            return ready

        def validator_spy(*, result: object) -> bool:
            calls.append("validator")
            return adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
                result=result
            )

        def sanitizer_spy() -> object:
            calls.append("sanitizer")
            return (
                adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
            )

        _install_controlled_dependencies(
            monkeypatch,
            adapter=adapter_spy,
            validator=validator_spy,
            sanitizer=sanitizer_spy,
        )
        result = (
            integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
        )
        _assert_sanitized(result)
        assert calls == (
            ["adapter", "validator", "sanitizer"]
            if outcome == "identity"
            else ["adapter", "sanitizer"]
        )


def test_pre_call_dependency_and_constant_drift_use_zero_adapter_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def changed_adapter(**_: object) -> object:
        calls.append("adapter")
        raise AssertionError("changed adapter must not run")

    def sanitizer_spy() -> object:
        calls.append("sanitizer")
        return adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()

    monkeypatch.setattr(
        integration_module,
        "build_server_owned_canonical_gold_market_facts_source_v1",
        changed_adapter,
    )
    monkeypatch.setattr(
        integration_module,
        "_build_canonical_gold_market_facts_source_adapter_safe_failure_v1",
        sanitizer_spy,
    )
    monkeypatch.setattr(
        integration_module,
        "_EXPECTED_BUILD_SAFE_FAILURE",
        sanitizer_spy,
    )
    result = integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
    _assert_sanitized(result)
    assert calls == ["sanitizer"]

    monkeypatch.setattr(
        integration_module,
        "build_server_owned_canonical_gold_market_facts_source_v1",
        integration_module._EXPECTED_BUILD_ADAPTER,
    )
    monkeypatch.setattr(
        integration_module,
        "_FIXED_PATHS",
        tuple([*integration_module._EXPECTED_FIXED_PATHS]),
    )
    calls.clear()
    result = integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
    _assert_sanitized(result)
    assert calls == ["sanitizer"]


def test_post_call_dependency_drift_stops_before_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    ready = _ready_result()

    def adapter_spy(**_: object) -> object:
        calls.append("adapter")
        monkeypatch.setattr(
            integration_module,
            "_is_safe_canonical_gold_market_facts_source_adapter_result_v1",
            lambda **__: True,
        )
        return ready

    def validator_spy(*, result: object) -> bool:
        calls.append("validator")
        return adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=result
        )

    def sanitizer_spy() -> object:
        calls.append("sanitizer")
        return adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()

    _install_controlled_dependencies(
        monkeypatch,
        adapter=adapter_spy,
        validator=validator_spy,
        sanitizer=sanitizer_spy,
    )
    result = integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
    _assert_sanitized(result)
    assert calls == ["adapter", "sanitizer"]


def test_unavailable_sanitizer_returns_no_source_and_calls_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        integration_module,
        "_build_canonical_gold_market_facts_source_adapter_safe_failure_v1",
        None,
    )
    assert (
        integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
        is None
    )


def test_invalid_sanitizer_result_returns_no_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def adapter_spy(**_: object) -> object:
        calls.append("adapter")
        raise RuntimeError("sensitive adapter detail")

    def validator_spy(*, result: object) -> bool:
        calls.append("validator")
        return True

    def invalid_sanitizer_spy() -> object:
        calls.append("sanitizer")
        return object()

    _install_controlled_dependencies(
        monkeypatch,
        adapter=adapter_spy,
        validator=validator_spy,
        sanitizer=invalid_sanitizer_spy,
    )
    assert (
        integration_module.build_canonical_gold_market_facts_docs_fixture_source_v1()
        is None
    )
    assert calls == ["adapter", "sanitizer"]


def test_module_has_no_parallel_runtime_or_ambient_authority() -> None:
    source = Path(integration_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    adapter_imports = tuple(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "app.services.canonical_gold_market_facts_source_adapter"
        for alias in node.names
    )
    assert adapter_imports == (
        "_AUTHORITY_TOKEN",
        "_CanonicalGoldMarketFactsSourceAuthorityV1",
        "_build_canonical_gold_market_facts_source_adapter_safe_failure_v1",
        "_is_safe_canonical_gold_market_facts_source_adapter_result_v1",
        "CanonicalGoldMarketFactsSourceAdapterResultV1",
        "build_server_owned_canonical_gold_market_facts_source_v1",
    )
    assert "canonical_gold_market_facts_snapshot_projector" not in source
    assert "canonical_bundle_replay_runner" not in source
    assert "demo_readonly_canonical_docs_fixture_diagnostics_summary_producer" not in source
    assert "app.api" not in source
    assert "os.environ" not in source
    assert "get_settings" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "exec", "eval"}
        for node in ast.walk(tree)
    )


def _install_controlled_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    adapter: object,
    validator: object,
    sanitizer: object,
) -> None:
    pairs = (
        (
            "build_server_owned_canonical_gold_market_facts_source_v1",
            "_EXPECTED_BUILD_ADAPTER",
            adapter,
        ),
        (
            "_is_safe_canonical_gold_market_facts_source_adapter_result_v1",
            "_EXPECTED_VALIDATE_RESULT",
            validator,
        ),
        (
            "_build_canonical_gold_market_facts_source_adapter_safe_failure_v1",
            "_EXPECTED_BUILD_SAFE_FAILURE",
            sanitizer,
        ),
    )
    for active_name, expected_name, value in pairs:
        monkeypatch.setattr(integration_module, active_name, value)
        monkeypatch.setattr(integration_module, expected_name, value)


def _ready_result(
    *,
    bundle_id: str = "demo-bundle-000000000001",
) -> adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1:
    bar = CanonicalGoldBarSourceV1(
        open_time_utc="2026-07-10T02:15:00Z",
        open=2300.0,
        high=2301.0,
        low=2299.0,
        close=2300.5,
        tick_volume=10,
        spread_points=30,
    )
    source = CanonicalGoldMarketFactsSourceV1(
        contract_version="1.0",
        bundle_schema_version="1.0",
        bundle_id=bundle_id,
        sequence=1,
        canonical_symbol="XAUUSD",
        broker_symbol="GOLD",
        reference_time_utc="2026-07-10T02:30:05.000000Z",
        policy_profile_version="canonical_gold_market_facts_policy_v1",
        upstream_evidence=CanonicalGoldUpstreamEvidenceV1(
            reader_passed=True,
            reader_status_code="CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID",
            value_status_code="CANONICAL_MT4_BUNDLE_V1_VALUE_VALID",
            data_quality_passed=True,
            data_quality_status_code="CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
            ready_for_readonly_analysis=True,
            warning_codes=(),
            same_attempt_identity_bound=True,
        ),
        live_tick=CanonicalGoldTickSourceV1(
            bid=2300.5,
            ask=2300.8,
            spread=0.3,
            spread_points=30,
            digits=2,
            point=0.01,
            tick_time_utc="2026-07-10T02:30:00Z",
        ),
        bars_generated_at_utc="2026-07-10T02:30:00Z",
        timeframes=tuple(
            CanonicalGoldTimeframeSourceV1(
                timeframe=timeframe,
                period_seconds=period_seconds,
                bars=(bar,),
            )
            for timeframe, period_seconds in (
                ("M15", 900),
                ("H1", 3600),
                ("H4", 14400),
                ("D1", 86400),
            )
        ),
        symbol_spec=CanonicalGoldSymbolSpecSourceV1(
            spec_time_utc="2026-07-10T02:30:00Z",
            digits=2,
            point=0.01,
            tick_size=0.01,
            tick_value=1.0,
            contract_size=100.0,
            min_lot=0.01,
            lot_step=0.01,
            max_lot=100.0,
            base_currency="XAU",
            profit_currency="USD",
            margin_currency="USD",
            trade_mode_readonly_label="readonly_metadata_only",
            session_status_readonly_label="session_metadata_only",
        ),
    )
    return adapter_module._ready(source)


def _blocked_result() -> adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1:
    return adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()


def _assert_sanitized(result: object) -> None:
    assert type(result) is adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1
    assert result.passed is False
    assert result.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE"
    assert result.reason_codes == ("GOLD_SOURCE_EXCEPTION_SANITIZED",)
    assert result.warning_codes == ()
    assert result.source_available is False
    assert result.source is None
    _assert_safety(result)


def _assert_safety(
    result: adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> None:
    for name, expected in SAFETY_FLAGS.items():
        assert getattr(result, name) is expected
