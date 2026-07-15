from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
import inspect
from pathlib import Path
from typing import get_type_hints

import pytest

import app.services.canonical_gold_market_facts_source_adapter as adapter_module
import app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader as reader_module
import app.services.data_quality_gate as gate_module
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldMarketFactsSourceV1,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
)
from app.services.data_quality_gate import (
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy,
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
COMPONENT_NAMES = (
    "filesystem_boundary",
    "snapshot_manifest",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
    "manifest_consistency",
    "checksum",
    "upstream_value_validation",
)


def test_production_types_and_public_interface_are_exact() -> None:
    identity = adapter_module._CanonicalBundlePreviousIdentityV1(
        bundle_id="previous-bundle-1",
        sequence=1,
    )
    authority = _authority(previous_identity=identity)
    result = _blocked_result()

    assert tuple(field.name for field in fields(type(identity))) == (
        "bundle_id",
        "sequence",
    )
    assert get_type_hints(type(identity)) == {"bundle_id": str, "sequence": int}
    assert tuple(field.name for field in fields(type(authority))) == (
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
    assert tuple(field.name for field in fields(type(result))) == RESULT_FIELDS
    assert get_type_hints(type(result)) == {
        "contract_version": str,
        "passed": bool,
        "status_code": str,
        "reason_codes": tuple[str, ...],
        "warning_codes": tuple[str, ...],
        "source_available": bool,
        "source": CanonicalGoldMarketFactsSourceV1 | None,
        "read_only": bool,
        "demo_only": bool,
        "is_tradable": bool,
        "can_execute": bool,
        "is_trading_permission": bool,
        "is_execution_instruction": bool,
        "allowed_to_call_ea": bool,
        "allowed_to_modify_risk": bool,
    }
    assert str(
        inspect.signature(
            adapter_module.build_server_owned_canonical_gold_market_facts_source_v1
        )
    ) == (
        "(*, authority: "
        "'_CanonicalGoldMarketFactsSourceAuthorityV1') -> "
        "'CanonicalGoldMarketFactsSourceAdapterResultV1'"
    )
    assert not hasattr(identity, "__dict__")
    assert not hasattr(authority, "__dict__")
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.passed = True  # type: ignore[misc]


def test_private_result_authority_interfaces_and_safe_failure_are_exact() -> None:
    assert str(
        inspect.signature(
            adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1
        )
    ) == "(*, result: 'object') -> 'bool'"
    assert str(
        inspect.signature(
            adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1
        )
    ) == "() -> 'CanonicalGoldMarketFactsSourceAdapterResultV1'"

    first = (
        adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
    )
    second = (
        adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
    )
    assert first == second
    assert first is not second
    _assert_blocked(
        first,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_EXCEPTION_SANITIZED",
    )
    assert (
        adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=first
        )
        is True
    )
    assert first._is_fixed_sanitized_failure_v1() is True


def test_fixed_sanitized_failure_rejects_semantically_invalid_exact_results() -> None:
    failure = (
        adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
    )
    ready = _run_ready()
    assert ready.source is not None

    invalid_results = (
        replace(failure, passed=True),
        replace(failure, status_code="CANONICAL_GOLD_SOURCE_ADAPTER_READY"),
        replace(failure, reason_codes=()),
        replace(failure, source_available=True, source=ready.source),
        replace(failure, can_execute=True),
    )
    for invalid in invalid_results:
        assert type(invalid) is type(failure)
        assert invalid._is_fixed_sanitized_failure_v1() is False


def test_private_result_validator_fails_closed_on_polluted_envelopes() -> None:
    ready = _run_ready()
    blocked = (
        adapter_module._build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
    )
    assert ready.source is not None
    polluted_source = replace(
        ready.source,
        timeframes=list(ready.source.timeframes),  # type: ignore[arg-type]
    )
    polluted_evidence = replace(
        ready.source.upstream_evidence,
        warning_codes=("UNEXPECTED_WARNING",),
    )
    result_subclass = type(
        "ResultSubclass",
        (adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1,),
        {},
    )
    subclassed_result = result_subclass(
        **{field.name: getattr(ready, field.name) for field in fields(type(ready))}
    )

    assert (
        adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=ready
        )
        is True
    )
    invalid_results = (
        object(),
        subclassed_result,
        replace(ready, contract_version="2.0"),
        replace(ready, passed=1),  # type: ignore[arg-type]
        replace(ready, status_code="CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE"),
        replace(ready, reason_codes=("GOLD_SOURCE_EXCEPTION_SANITIZED",)),
        replace(ready, warning_codes=["UNEXPECTED_WARNING"]),  # type: ignore[arg-type]
        replace(ready, source_available=False),
        replace(ready, source=polluted_source),
        replace(
            ready,
            source=replace(ready.source, upstream_evidence=polluted_evidence),
        ),
        replace(ready, allowed_to_call_ea=True),
        replace(blocked, passed=True),
        replace(blocked, source_available=True),
        replace(blocked, status_code="CANONICAL_GOLD_SOURCE_ADAPTER_READER_BLOCKED"),
        replace(blocked, reason_codes=("GOLD_SOURCE_READER_NOT_READY", "EXTRA")),
    )
    for invalid in invalid_results:
        assert (
            adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
                result=invalid
            )
            is False
        )


def test_private_result_validator_rejects_g175_invalid_ready_sources() -> None:
    ready = _run_ready()
    assert ready.source is not None
    first_timeframe = ready.source.timeframes[0]
    first_bar = first_timeframe.bars[0]

    invalid_sources = (
        replace(ready.source, reference_time_utc="2026-07-10T02:30:05+00:00"),
        replace(
            ready.source,
            live_tick=replace(ready.source.live_tick, bid=float("nan")),
        ),
        replace(
            ready.source,
            live_tick=replace(ready.source.live_tick, tick_time_utc="not-a-time"),
        ),
        replace(
            ready.source,
            timeframes=(
                replace(first_timeframe, bars=()),
                *ready.source.timeframes[1:],
            ),
        ),
        replace(
            ready.source,
            timeframes=(
                replace(
                    first_timeframe,
                    bars=list(first_timeframe.bars),  # type: ignore[arg-type]
                ),
                *ready.source.timeframes[1:],
            ),
        ),
        replace(
            ready.source,
            timeframes=(
                replace(first_timeframe, bars=(first_bar,) * 501),
                *ready.source.timeframes[1:],
            ),
        ),
        replace(
            ready.source,
            timeframes=(
                replace(
                    first_timeframe,
                    bars=(replace(first_bar, open_time_utc="2026-07-10"),),
                ),
                *ready.source.timeframes[1:],
            ),
        ),
        replace(
            ready.source,
            symbol_spec=replace(ready.source.symbol_spec, max_lot=float("inf")),
        ),
    )
    for invalid_source in invalid_sources:
        assert (
            adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
                result=replace(ready, source=invalid_source)
            )
            is False
        )


def test_private_result_validator_accepts_only_closed_blocked_mappings() -> None:
    valid_pairs = (
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
            "GOLD_SOURCE_AUTHORITY_INVALID",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_READER_BLOCKED",
            "GOLD_SOURCE_READER_NOT_READY",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_WARNING_BLOCKED",
            "GOLD_SOURCE_UPSTREAM_WARNING_REJECTED",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_DATA_QUALITY_BLOCKED",
            "GOLD_SOURCE_DATA_QUALITY_NOT_READY",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
            "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID",
            "GOLD_SOURCE_CONSTRUCTION_INVALID",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
        ),
        (
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_EXCEPTION_SANITIZED",
        ),
    )
    for status, reason in valid_pairs:
        result = adapter_module._blocked(status, reason)
        assert (
            adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
                result=result
            )
            is True
        )

    mismatched = adapter_module._blocked(*valid_pairs[0])
    mismatched = replace(
        mismatched,
        reason_codes=("GOLD_SOURCE_READER_NOT_READY",),
    )
    assert (
        adapter_module._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=mismatched
        )
        is False
    )


def test_ready_path_calls_reader_and_gate_once_and_builds_fresh_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority(
        previous_identity=adapter_module._CanonicalBundlePreviousIdentityV1(
            bundle_id="previous-bundle-1",
            sequence=6,
        )
    )
    capsule = _capsule()
    reader_envelope = _ready_reader_envelope()
    gate_result = _ready_gate_result()
    calls: list[tuple[str, dict[str, object]]] = []

    def reader_spy(**kwargs: object) -> tuple[dict[str, object], object]:
        calls.append(("reader", kwargs))
        return reader_envelope, capsule

    def gate_spy(**kwargs: object) -> dict[str, object]:
        calls.append(("gate", kwargs))
        return gate_result

    monkeypatch.setattr(adapter_module, "_read_accepted_attempt", reader_spy)
    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)
    original_reader = deepcopy(reader_envelope)
    original_manifest = capsule.manifest
    original_payloads = capsule.payloads_by_filename

    first = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=authority
    )
    second = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=authority
    )

    assert [name for name, _ in calls] == ["reader", "gate", "reader", "gate"]
    reader_kwargs = calls[0][1]
    assert reader_kwargs == {
        "allowed_root": authority.allowed_root,
        "bundle_dir": authority.bundle_dir,
        "now_utc": authority.reference_time_utc,
        "previous_identity": {"bundle_id": "previous-bundle-1", "sequence": 6},
        "read_policy": authority.read_policy,
        "filesystem_policy": authority.filesystem_policy,
    }
    assert calls[1][1]["reader_result"] is reader_envelope
    assert calls[1][1]["policy"] is authority.data_quality_policy
    assert first.passed is True
    assert first.status_code == "CANONICAL_GOLD_SOURCE_ADAPTER_READY"
    assert first.reason_codes == ()
    assert first.warning_codes == ()
    assert first.source_available is True
    assert type(first.source) is CanonicalGoldMarketFactsSourceV1
    assert first.source == second.source
    assert first is not second
    assert first.source is not second.source
    assert first.source.upstream_evidence is not second.source.upstream_evidence
    assert first.source.live_tick is not second.source.live_tick
    assert first.source.timeframes is not second.source.timeframes
    assert first.source.symbol_spec is not second.source.symbol_spec
    assert reader_envelope == original_reader
    assert capsule.manifest == original_manifest
    assert capsule.payloads_by_filename == original_payloads
    _assert_safety(first)


def test_ready_source_has_exact_same_attempt_provenance() -> None:
    result = _run_ready()
    source = result.source
    assert source is not None
    assert tuple(field.name for field in fields(type(source))) == (
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
        "demo-bundle-000000000007",
        7,
        "XAUUSD",
        "GOLD",
        "2026-07-14T00:00:00.000000Z",
        "canonical_gold_market_facts_policy_v1",
    )
    assert source.upstream_evidence.reader_passed is True
    assert (
        source.upstream_evidence.reader_status_code
        == "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID"
    )
    assert (
        source.upstream_evidence.value_status_code
        == "CANONICAL_MT4_BUNDLE_V1_VALUE_VALID"
    )
    assert source.upstream_evidence.data_quality_passed is True
    assert (
        source.upstream_evidence.data_quality_status_code
        == "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED"
    )
    assert source.upstream_evidence.ready_for_readonly_analysis is True
    assert source.upstream_evidence.warning_codes == ()
    assert source.upstream_evidence.same_attempt_identity_bound is True
    assert (
        source.live_tick.bid,
        source.live_tick.ask,
        source.live_tick.spread,
        source.live_tick.spread_points,
        source.live_tick.digits,
        source.live_tick.point,
        source.live_tick.tick_time_utc,
    ) == (2300.5, 2300.8, 0.3, 30, 2, 0.01, "2026-07-14T00:00:00Z")
    assert source.bars_generated_at_utc == "2026-07-14T00:00:00Z"
    assert tuple(item.timeframe for item in source.timeframes) == (
        "M15",
        "H1",
        "H4",
        "D1",
    )
    assert tuple(item.period_seconds for item in source.timeframes) == (
        900,
        3600,
        14400,
        86400,
    )
    assert all(len(item.bars) == 1 for item in source.timeframes)
    assert source.symbol_spec.base_currency == "XAU"
    assert source.symbol_spec.profit_currency == "USD"
    assert source.symbol_spec.margin_currency == "USD"
    assert not hasattr(source, "__dict__")
    with pytest.raises(FrozenInstanceError):
        source.sequence = 8  # type: ignore[misc]


def test_invalid_authority_stops_before_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"reader": 0, "gate": 0}

    def reader_spy(**_: object) -> object:
        calls["reader"] += 1
        raise AssertionError("reader must not run")

    def gate_spy(**_: object) -> object:
        calls["gate"] += 1
        raise AssertionError("gate must not run")

    monkeypatch.setattr(adapter_module, "_read_accepted_attempt", reader_spy)
    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)
    invalid_authorities = (
        object(),
        replace(_authority(), authority_token=object()),
        replace(_authority(), policy_profile_version="caller-policy"),
        replace(
            _authority(),
            filesystem_policy=CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
                max_manifest_consistency_retries=1
            ),
        ),
        replace(_authority(), reference_time_utc=datetime(2026, 7, 14)),
    )

    for authority in invalid_authorities:
        result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
            authority=authority  # type: ignore[arg-type]
        )
        _assert_blocked(
            result,
            "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
            "GOLD_SOURCE_AUTHORITY_INVALID",
        )
    assert calls == {"reader": 0, "gate": 0}


@pytest.mark.parametrize("missing_dependency", ("reader", "gate"))
def test_unavailable_dependency_stops_before_reader(
    monkeypatch: pytest.MonkeyPatch,
    missing_dependency: str,
) -> None:
    reader_calls = 0

    def reader_spy(**_: object) -> object:
        nonlocal reader_calls
        reader_calls += 1
        raise AssertionError("reader must not run")

    monkeypatch.setattr(adapter_module, "_read_accepted_attempt", reader_spy)
    if missing_dependency == "reader":
        monkeypatch.setattr(adapter_module, "_read_accepted_attempt", None)
    else:
        monkeypatch.setattr(adapter_module, "_evaluate_data_quality", None)

    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=_authority()
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_AUTHORITY_INVALID",
        "GOLD_SOURCE_AUTHORITY_INVALID",
    )
    assert reader_calls == 0


def test_reader_block_warning_and_invalid_pairing_stop_before_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate_calls = 0

    def gate_spy(**_: object) -> object:
        nonlocal gate_calls
        gate_calls += 1
        raise AssertionError("gate must not run")

    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)
    vectors = (
        (
            (_blocked_reader_envelope(), None),
            "CANONICAL_GOLD_SOURCE_ADAPTER_READER_BLOCKED",
            "GOLD_SOURCE_READER_NOT_READY",
        ),
        (
            (_warning_reader_envelope(), _capsule()),
            "CANONICAL_GOLD_SOURCE_ADAPTER_WARNING_BLOCKED",
            "GOLD_SOURCE_UPSTREAM_WARNING_REJECTED",
        ),
        (
            (_ready_reader_envelope(), None),
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
        ),
        (
            (_blocked_reader_envelope(), _capsule()),
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
        ),
        (
            (_reordered(_ready_reader_envelope()), _capsule()),
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
        ),
    )
    for reader_return, status, reason in vectors:
        monkeypatch.setattr(
            adapter_module,
            "_read_accepted_attempt",
            lambda reader_return=reader_return, **_: reader_return,
        )
        result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
            authority=_authority()
        )
        _assert_blocked(result, status, reason)
    assert gate_calls == 0


def test_forged_reader_status_reason_and_component_status_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate_calls = 0

    def gate_spy(**_: object) -> object:
        nonlocal gate_calls
        gate_calls += 1
        raise AssertionError("gate must not run")

    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)
    forged_pair = _blocked_reader_envelope()
    forged_pair["reason_codes"] = ["FILESYSTEM_POLICY_INVALID"]
    forged_pair["component_statuses"][1]["reason_codes"] = [
        "FILESYSTEM_POLICY_INVALID"
    ]
    forged_component = _ready_reader_envelope()
    forged_component["component_statuses"][0]["status_code"] = (
        "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FORGED_VALID"
    )

    for envelope, capsule in (
        (forged_pair, None),
        (forged_component, _capsule()),
    ):
        monkeypatch.setattr(
            adapter_module,
            "_read_accepted_attempt",
            lambda envelope=envelope, capsule=capsule, **_: (envelope, capsule),
        )
        result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
            authority=_authority()
        )
        _assert_blocked(
            result,
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
        )
    assert gate_calls == 0


def test_forged_reader_component_reason_ownership_and_duplicates_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong_owner = _blocked_reader_envelope()
    wrong_owner["component_statuses"][0].update(
        {
            "passed": False,
            "status_code": (
                "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_"
                "FILESYSTEM_BOUNDARY_INVALID"
            ),
            "reason_codes": ["FILE_NOT_FOUND"],
            "warning_codes": [],
        }
    )
    wrong_owner["component_statuses"][1].update(
        {
            "passed": False,
            "status_code": (
                "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_"
                "SNAPSHOT_MANIFEST_NOT_CHECKED"
            ),
            "reason_codes": [],
            "warning_codes": [],
        }
    )

    duplicated_reason = _blocked_reader_envelope()
    duplicated_reason["component_statuses"][2].update(
        {
            "passed": False,
            "status_code": (
                "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_LIVE_TICK_INVALID"
            ),
            "reason_codes": ["FILE_NOT_FOUND"],
            "warning_codes": [],
        }
    )

    gate_calls = 0

    def gate_spy(**_: object) -> object:
        nonlocal gate_calls
        gate_calls += 1
        raise AssertionError("gate must not run")

    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)
    for envelope in (wrong_owner, duplicated_reason):
        monkeypatch.setattr(
            adapter_module,
            "_read_accepted_attempt",
            lambda envelope=envelope, **_: (envelope, None),
        )
        result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
            authority=_authority()
        )
        _assert_blocked(
            result,
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_READER_RESULT_INVALID",
        )
    assert gate_calls == 0


@pytest.mark.parametrize("mutation", ("reordered", "extra"))
def test_nested_capsule_shape_drift_fails_before_gate(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    capsule = _capsule()
    payloads = list(capsule.payloads_by_filename)
    live_tick = payloads[0][1]
    if mutation == "reordered":
        changed_live_tick = tuple(reversed(live_tick))
    else:
        changed_live_tick = (*live_tick, ("unexpected", "polluted"))
    payloads[0] = (payloads[0][0], changed_live_tick)
    changed_capsule = type(capsule)(
        attempt_token=capsule.attempt_token,
        manifest=capsule.manifest,
        payloads_by_filename=tuple(payloads),
    )
    gate_calls = 0

    def gate_spy(**_: object) -> object:
        nonlocal gate_calls
        gate_calls += 1
        raise AssertionError("gate must not run")

    monkeypatch.setattr(
        adapter_module,
        "_read_accepted_attempt",
        lambda **_: (_ready_reader_envelope(), changed_capsule),
    )
    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)

    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=_authority()
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_READER_RESULT_INVALID",
    )
    assert gate_calls == 0


def test_gate_block_warning_and_invalid_result_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capsule = _capsule()
    reader_envelope = _ready_reader_envelope()
    reader_calls = 0
    gate_calls = 0

    def reader_spy(**_: object) -> tuple[dict[str, object], object]:
        nonlocal reader_calls
        reader_calls += 1
        return reader_envelope, capsule

    monkeypatch.setattr(adapter_module, "_read_accepted_attempt", reader_spy)
    vectors = (
        (
            _blocked_gate_result(),
            "CANONICAL_GOLD_SOURCE_ADAPTER_DATA_QUALITY_BLOCKED",
            "GOLD_SOURCE_DATA_QUALITY_NOT_READY",
        ),
        (
            _warning_gate_result(),
            "CANONICAL_GOLD_SOURCE_ADAPTER_DATA_QUALITY_BLOCKED",
            "GOLD_SOURCE_DATA_QUALITY_NOT_READY",
        ),
        (
            _reordered(_ready_gate_result()),
            "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
            "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
        ),
    )
    for gate_result, status, reason in vectors:
        def gate_spy(**_: object) -> dict[str, object]:
            nonlocal gate_calls
            gate_calls += 1
            return gate_result

        monkeypatch.setattr(adapter_module, "_evaluate_data_quality", gate_spy)
        result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
            authority=_authority()
        )
        _assert_blocked(result, status, reason)
    assert reader_calls == 3
    assert gate_calls == 3


def test_forged_gate_status_reason_pair_is_result_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate_result = _blocked_gate_result()
    gate_result["reason_codes"] = ["DATA_QUALITY_POLICY_INVALID"]
    monkeypatch.setattr(
        adapter_module,
        "_read_accepted_attempt",
        lambda **_: (_ready_reader_envelope(), _capsule()),
    )
    monkeypatch.setattr(
        adapter_module,
        "_evaluate_data_quality",
        lambda **_: gate_result,
    )

    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=_authority()
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_DATA_QUALITY_RESULT_INVALID",
    )


def test_post_call_drift_is_identity_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader_envelope = _ready_reader_envelope()
    capsule = _capsule()
    monkeypatch.setattr(
        adapter_module,
        "_read_accepted_attempt",
        lambda **_: (reader_envelope, capsule),
    )

    def drifting_gate(**_: object) -> dict[str, object]:
        result = _ready_gate_result()
        reader_envelope["reader_status"] = "changed_after_call"
        return result

    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", drifting_gate)
    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=_authority()
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
        "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
    )


def test_previous_identity_scalar_drift_is_identity_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous_identity = adapter_module._CanonicalBundlePreviousIdentityV1(
        bundle_id="previous-bundle-1",
        sequence=6,
    )
    authority = _authority(previous_identity=previous_identity)
    monkeypatch.setattr(
        adapter_module,
        "_read_accepted_attempt",
        lambda **_: (_ready_reader_envelope(), _capsule()),
    )

    def drifting_gate(**_: object) -> dict[str, object]:
        object.__setattr__(previous_identity, "sequence", 7)
        return _ready_gate_result()

    monkeypatch.setattr(adapter_module, "_evaluate_data_quality", drifting_gate)
    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=authority
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_IDENTITY_INVALID",
        "GOLD_SOURCE_SAME_ATTEMPT_IDENTITY_INVALID",
    )


def test_polluted_selected_payload_is_source_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capsule = _capsule(live_tick_override={"bid": True})
    monkeypatch.setattr(
        adapter_module,
        "_read_accepted_attempt",
        lambda **_: (_ready_reader_envelope(), capsule),
    )
    monkeypatch.setattr(
        adapter_module,
        "_evaluate_data_quality",
        lambda **_: _ready_gate_result(),
    )

    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=_authority()
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SOURCE_INVALID",
        "GOLD_SOURCE_CONSTRUCTION_INVALID",
    )


@pytest.mark.parametrize("failure_stage", ("reader", "gate", "mapping"))
def test_unexpected_exceptions_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    if failure_stage == "reader":
        monkeypatch.setattr(
            adapter_module,
            "_read_accepted_attempt",
            lambda **_: (_ for _ in ()).throw(RuntimeError("sensitive reader")),
        )
    else:
        monkeypatch.setattr(
            adapter_module,
            "_read_accepted_attempt",
            lambda **_: (_ready_reader_envelope(), _capsule()),
        )
        if failure_stage == "gate":
            monkeypatch.setattr(
                adapter_module,
                "_evaluate_data_quality",
                lambda **_: (_ for _ in ()).throw(ValueError("sensitive gate")),
            )
        else:
            monkeypatch.setattr(
                adapter_module,
                "_evaluate_data_quality",
                lambda **_: _ready_gate_result(),
            )
            monkeypatch.setattr(
                adapter_module,
                "_build_source",
                lambda **_: (_ for _ in ()).throw(OverflowError("sensitive mapping")),
            )

    result = adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
        authority=_authority()
    )
    _assert_blocked(
        result,
        "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "GOLD_SOURCE_EXCEPTION_SANITIZED",
    )
    rendered = repr(result)
    assert "sensitive" not in rendered
    assert "traceback" not in rendered.casefold()


def test_module_is_bounded_to_approved_dependencies_and_has_no_ambient_io() -> None:
    path = Path(adapter_module.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_names = {name for name in vars(adapter_module) if not name.startswith("_")}
    public_names.discard("annotations")

    assert public_names == {
        "CanonicalGoldMarketFactsSourceAdapterResultV1",
        "build_server_owned_canonical_gold_market_facts_source_v1",
    }
    assert "build_canonical_gold_market_facts_snapshot_v1" not in source
    assert "canonical_bundle_replay_runner" not in source
    assert "docs_fixture" not in source
    assert "app.api" not in source
    assert "os.environ" not in source
    assert "get_settings" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "exec", "eval"}
        for node in ast.walk(tree)
    )


def _run_ready() -> adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1:
    original_reader = adapter_module._read_accepted_attempt
    original_gate = adapter_module._evaluate_data_quality
    try:
        adapter_module._read_accepted_attempt = (  # type: ignore[assignment]
            lambda **_: (_ready_reader_envelope(), _capsule())
        )
        adapter_module._evaluate_data_quality = (  # type: ignore[assignment]
            lambda **_: _ready_gate_result()
        )
        return adapter_module.build_server_owned_canonical_gold_market_facts_source_v1(
            authority=_authority()
        )
    finally:
        adapter_module._read_accepted_attempt = original_reader
        adapter_module._evaluate_data_quality = original_gate


def _authority(
    *,
    previous_identity: object | None = None,
) -> adapter_module._CanonicalGoldMarketFactsSourceAuthorityV1:
    return adapter_module._CanonicalGoldMarketFactsSourceAuthorityV1(
        authority_token=adapter_module._AUTHORITY_TOKEN,
        allowed_root=Path("server-root"),
        bundle_dir=Path("server-root") / "bundle",
        reference_time_utc=datetime(2026, 7, 14, tzinfo=UTC),
        previous_identity=previous_identity,
        read_policy=CanonicalMt4DemoReadonlyBundleV1ReadPolicy(),
        filesystem_policy=CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
            max_manifest_consistency_retries=0,
        ),
        data_quality_policy=CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy(),
        policy_profile_version="canonical_gold_market_facts_policy_v1",
    )


def _capsule(
    *,
    live_tick_override: dict[str, object] | None = None,
) -> object:
    live_tick = {
        "bid": 2300.5,
        "ask": 2300.8,
        "spread": 0.3,
        "spread_points": 30,
        "digits": 2,
        "point": 0.01,
        "tick_time_utc": "2026-07-14T00:00:00Z",
    }
    live_tick.update(live_tick_override or {})
    bar = {
        "open_time_utc": "2026-07-13T23:45:00Z",
        "open": 2299.0,
        "high": 2301.0,
        "low": 2298.0,
        "close": 2300.0,
        "tick_volume": 10,
        "spread_points": 30,
    }
    timeframes = [
        {
            "timeframe": name,
            "period_seconds": period,
            "bar_count": 1,
            "bars": [bar],
        }
        for name, period in (("M15", 900), ("H1", 3600), ("H4", 14400), ("D1", 86400))
    ]
    symbol_spec = {
        "spec_time_utc": "2026-07-14T00:00:00Z",
        "digits": 2,
        "point": 0.01,
        "tick_size": 0.01,
        "tick_value": 1.0,
        "contract_size": 100.0,
        "min_lot": 0.01,
        "lot_step": 0.01,
        "max_lot": 100.0,
        "base_currency": "XAU",
        "profit_currency": "USD",
        "margin_currency": "USD",
        "trade_mode_readonly_label": "readonly_metadata_only",
        "session_status_readonly_label": "session_metadata_only",
    }
    manifest = {
        "schema_version": "1.0",
        "manifest_type": "canonical_mt4_demo_readonly_bundle_v1",
        "bundle_id": "demo-bundle-000000000007",
        "sequence": 7,
        "generated_at_utc": "2026-07-14T00:00:00Z",
        "committed_at_utc": "2026-07-14T00:00:00Z",
        "writer_heartbeat_at_utc": "2026-07-14T00:00:00Z",
        "source_id": "docs_fixture_only",
        "writer_version": "1.0",
        "terminal_id_masked": "terminal-masked",
        "account_mode": "demo",
        "is_demo_account": True,
        "is_live_account": False,
        "canonical_symbol": "XAUUSD",
        "broker_symbol": "GOLD",
        "commit_state": "committed",
        "required_files": [],
        "optional_files": [],
        "compatible_reader_schema_versions": ["1.0"],
        **SAFETY_FLAGS,
    }

    def payload_envelope(file_type: str) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "file_type": file_type,
            "bundle_id": "demo-bundle-000000000007",
            "sequence": 7,
            "generated_at_utc": "2026-07-14T00:00:00Z",
            "source_id": "docs_fixture_only",
            "writer_version": "1.0",
            "terminal_id_masked": "terminal-masked",
            "account_mode": "demo",
            "is_demo_account": True,
            "is_live_account": False,
            **SAFETY_FLAGS,
        }

    payloads = (
        (
            "live_tick.json",
            _freeze_json(
                {
                    **payload_envelope("live_tick"),
                    "canonical_symbol": "XAUUSD",
                    "broker_symbol": "GOLD",
                    **live_tick,
                }
            ),
        ),
        (
            "latest_bars.json",
            _freeze_json(
                {
                    **payload_envelope("latest_bars"),
                    "canonical_symbol": "XAUUSD",
                    "broker_symbol": "GOLD",
                    "timeframes": timeframes,
                }
            ),
        ),
        (
            "symbol_spec.json",
            _freeze_json(
                {
                    **payload_envelope("symbol_spec"),
                    "canonical_symbol": "XAUUSD",
                    "broker_symbol": "GOLD",
                    **symbol_spec,
                }
            ),
        ),
        (
            "account_snapshot.json",
            _freeze_json(
                {
                    **payload_envelope("account_snapshot"),
                    "snapshot_time_utc": "2026-07-14T00:00:00Z",
                    "account_alias_masked": "demo-account",
                    "server_name_masked": "demo-server",
                    "account_currency": "USD",
                    "balance": 10000.0,
                    "equity": 10000.0,
                    "margin": 0.0,
                    "free_margin": 10000.0,
                    "margin_level": 0.0,
                    "leverage": 100,
                    "positions_count": 0,
                    "pending_orders_count": 0,
                    "daily_realized_pnl": 0.0,
                    "daily_floating_pnl": 0.0,
                }
            ),
        ),
    )
    return reader_module._CanonicalMt4DemoReadonlyAcceptedAttemptV1(
        attempt_token=object(),
        manifest=_freeze_json(manifest),
        payloads_by_filename=payloads,
    )


def _freeze_json(value: object) -> object:
    if type(value) is dict:
        return tuple((key, _freeze_json(child)) for key, child in value.items())
    if type(value) is list:
        return tuple(_freeze_json(child) for child in value)
    return value


def _ready_reader_envelope() -> dict[str, object]:
    components = [
        {
            "component_name": name,
            "passed": True,
            "status_code": (
                "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_"
                f"{name.upper()}_VALID"
            ),
            "reason_codes": [],
            "warning_codes": [],
        }
        for name in COMPONENT_NAMES
    ]
    return {
        "passed": True,
        "status_code": reader_module.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
        "validation_stage": reader_module.VALIDATION_STAGE,
        "contract_version": reader_module.CONTRACT_VERSION,
        "reader_status": "validated_isolated",
        "reason_codes": [],
        "warning_codes": [],
        "component_statuses": components,
        "manifest_consistency_checked": True,
        "manifest_consistency_passed": True,
        "checksum_checked": True,
        "checksum_passed": True,
        "upstream_value_passed": True,
        "upstream_value_status_code": CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        "ready_for_readonly_analysis": False,
        "next_allowed_stage": ["canonical_data_quality_gate_integration"],
        "next_blocked_stage": [
            "api_reader_activation",
            "readonly_analysis",
            "execution_chain",
        ],
        **SAFETY_FLAGS,
    }


def _warning_reader_envelope() -> dict[str, object]:
    result = _ready_reader_envelope()
    result["status_code"] = (
        reader_module.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
    )
    result["warning_codes"] = ["SEQUENCE_GAP"]
    result["upstream_value_status_code"] = (
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
    )
    result["component_statuses"][-1]["warning_codes"] = ["SEQUENCE_GAP"]
    return result


def _blocked_reader_envelope() -> dict[str, object]:
    result = _ready_reader_envelope()
    result["passed"] = False
    result["status_code"] = reader_module.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING
    result["reader_status"] = "blocked"
    result["reason_codes"] = ["FILE_NOT_FOUND"]
    result["component_statuses"][1].update(
        {
            "passed": False,
            "status_code": "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SNAPSHOT_MANIFEST_INVALID",
            "reason_codes": ["FILE_NOT_FOUND"],
        }
    )
    for component in result["component_statuses"][2:]:
        component.update(
            {
                "passed": False,
                "status_code": (
                    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_"
                    f"{component['component_name'].upper()}_NOT_CHECKED"
                ),
                "reason_codes": [],
                "warning_codes": [],
            }
        )
    result["manifest_consistency_checked"] = False
    result["manifest_consistency_passed"] = False
    result["checksum_checked"] = False
    result["checksum_passed"] = False
    result["upstream_value_passed"] = False
    result["upstream_value_status_code"] = None
    result["next_allowed_stage"] = []
    return result


def _ready_gate_result() -> dict[str, object]:
    return {
        "passed": True,
        "status_code": gate_module.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
        "validation_stage": gate_module.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STAGE,
        "contract_version": gate_module.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_CONTRACT_VERSION,
        "reader_status": "validated_isolated",
        "source_reader_status_code": reader_module.CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
        "source_upstream_value_status_code": CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        "data_quality_status": "passed",
        "reason_codes": [],
        "warning_codes": [],
        "ready_for_readonly_analysis": True,
        "next_allowed_stage": ["canonical_diagnostics_integration"],
        "next_blocked_stage": ["api_reader_activation", "execution_chain"],
        **SAFETY_FLAGS,
    }


def _warning_gate_result() -> dict[str, object]:
    result = _ready_gate_result()
    result["status_code"] = (
        gate_module.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
    )
    result["data_quality_status"] = "passed_with_warnings"
    result["warning_codes"] = ["SEQUENCE_GAP"]
    return result


def _blocked_gate_result() -> dict[str, object]:
    result = _ready_gate_result()
    result["passed"] = False
    result["status_code"] = (
        gate_module.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED
    )
    result["reader_status"] = "blocked"
    result["data_quality_status"] = "blocked"
    result["reason_codes"] = ["READER_BLOCKED"]
    result["ready_for_readonly_analysis"] = False
    result["next_allowed_stage"] = []
    result["next_blocked_stage"] = [
        "canonical_diagnostics_integration",
        "api_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    return result


def _reordered(value: dict[str, object]) -> dict[str, object]:
    return dict(reversed(tuple(value.items())))


def _blocked_result() -> adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1:
    return adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1(
        contract_version="1.0",
        passed=False,
        status_code="CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        reason_codes=("GOLD_SOURCE_EXCEPTION_SANITIZED",),
        warning_codes=(),
        source_available=False,
        source=None,
        **SAFETY_FLAGS,
    )


def _assert_blocked(
    result: adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1,
    status: str,
    reason: str,
) -> None:
    assert result.contract_version == "1.0"
    assert result.passed is False
    assert result.status_code == status
    assert result.reason_codes == (reason,)
    assert result.warning_codes == ()
    assert result.source_available is False
    assert result.source is None
    _assert_safety(result)


def _assert_safety(
    result: adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1,
) -> None:
    for field, expected in SAFETY_FLAGS.items():
        assert getattr(result, field) is expected
