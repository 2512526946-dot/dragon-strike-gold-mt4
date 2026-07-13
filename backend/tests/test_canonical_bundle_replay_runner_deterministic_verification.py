"""Offline ReplayRunner v1 verification only; never activation or W6-W21 authority."""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

from app.services import canonical_bundle_replay_runner as replay_runner


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
FIXTURE_DIR = FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
FIXTURE_FILENAMES = (
    "snapshot_manifest.json",
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
RESULT_FIELDS = (
    "replay_contract_version",
    "registry_version",
    "pipeline_contract_version",
    "policy_profile_version",
    "case_id",
    "fixture_id",
    "passed",
    "status_code",
    "canonical_summary",
    "replay_reason_codes",
    "canonical_block_reasons",
    "canonical_warning_codes",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_execution_instruction",
    "allowed_to_call_ea",
)
SUMMARY_FIELDS = (
    "passed",
    "status_code",
    "source_scope",
    "validation_stage",
    "fixture_source",
    "bundle_validation_status",
    "component_statuses",
    "block_reasons",
    "warning_reasons",
    "readiness_notes",
    "next_allowed_stage",
    "next_blocked_stage",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)
STATUS_FIELDS = (
    "passed",
    "status_code",
    "block_reasons",
    "warning_reasons",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
)
RESULT_SAFETY_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
}
SUMMARY_SAFETY_FLAGS = {
    **RESULT_SAFETY_FLAGS,
    "is_trading_permission": False,
    "allowed_to_modify_risk": False,
}
REAL_REPLAY_COUNT = 5
INVALID_REPLAY_COUNT = 3


def test_real_ready_replay_is_deterministic_and_returns_fresh_snapshots() -> None:
    replay_case = _ready_case()
    case_before = deepcopy(replay_case)
    registry_before = replay_runner._REGISTRY
    registry_state_before = replay_runner._registry_state(registry_before)
    fixture_before = _fixture_state()

    assert type(registry_before) is tuple
    assert len(registry_before) == 1
    registry_record = registry_before[0]
    assert registry_record.allowed_root == FIXTURE_ROOT
    assert registry_record.bundle_dir == FIXTURE_DIR
    assert registry_record.reference_time_utc.isoformat() == "2026-07-10T02:30:05+00:00"
    assert registry_record.registry_version == replay_runner.REGISTRY_VERSION
    assert (
        registry_record.pipeline_contract_version
        == replay_runner.PIPELINE_CONTRACT_VERSION
    )
    assert registry_record.policy_profile_version == replay_runner.POLICY_PROFILE_VERSION
    assert registry_record.expected_outcome == "READY"
    assert registry_record.expected_status_code == "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
    assert registry_record.expected_block_reasons == ()
    assert registry_record.expected_warning_codes == ()

    results = tuple(
        replay_runner.run_canonical_bundle_replay_case(replay_case=replay_case)
        for _ in range(REAL_REPLAY_COUNT)
    )

    assert all(result == results[0] for result in results)
    assert len({id(result) for result in results}) == REAL_REPLAY_COUNT
    mutable_snapshot_ids = tuple(_mutable_snapshot_ids(result) for result in results)
    for position in range(len(mutable_snapshot_ids[0])):
        assert (
            len({snapshot_ids[position] for snapshot_ids in mutable_snapshot_ids})
            == REAL_REPLAY_COUNT
        )
    for result in results:
        _assert_exact_ready_result(result)
        _assert_no_sensitive_output(result)

    assert replay_case == case_before
    assert replay_runner._REGISTRY is registry_before
    assert replay_runner._registry_state(replay_runner._REGISTRY) == registry_state_before
    assert _fixture_state() == fixture_before


def test_mutating_one_detached_summary_cannot_change_subsequent_real_replay() -> None:
    replay_case = _ready_case()
    fixture_before = _fixture_state()
    registry_before = replay_runner._REGISTRY
    registry_state_before = replay_runner._registry_state(registry_before)
    first = replay_runner.run_canonical_bundle_replay_case(replay_case=replay_case)
    expected = deepcopy(first)

    first.canonical_summary["readiness_notes"].append("caller-local mutation")
    first.canonical_summary["bundle_validation_status"]["passed"] = False
    first.canonical_summary["component_statuses"][
        "canonical_data_quality_gate"
    ]["warning_reasons"].append("caller-local mutation")

    subsequent = replay_runner.run_canonical_bundle_replay_case(replay_case=replay_case)

    assert subsequent == expected
    assert subsequent is not first
    assert subsequent.canonical_summary is not first.canonical_summary
    _assert_exact_ready_result(subsequent)
    _assert_no_sensitive_output(subsequent)
    assert replay_case == _ready_case()
    assert replay_runner._REGISTRY is registry_before
    assert replay_runner._registry_state(replay_runner._REGISTRY) == registry_state_before
    assert _fixture_state() == fixture_before


def test_public_invalid_cases_are_deterministic_sanitized_and_fresh() -> None:
    fixture_before = _fixture_state()
    registry_before = replay_runner._REGISTRY
    registry_state_before = replay_runner._registry_state(registry_before)
    invalid_cases = (
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version="unsupported_replay_contract",
            case_id="caller_private_payload",
            fixture_id="caller_checksum_secret",
        ),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
            case_id="unregistered_case",
            fixture_id="unregistered_fixture",
        ),
    )

    for replay_case in invalid_cases:
        case_before = deepcopy(replay_case)
        results = tuple(
            replay_runner.run_canonical_bundle_replay_case(replay_case=replay_case)
            for _ in range(INVALID_REPLAY_COUNT)
        )

        assert all(result == results[0] for result in results)
        assert len({id(result) for result in results}) == INVALID_REPLAY_COUNT
        assert (
            len({id(result.canonical_summary) for result in results})
            == INVALID_REPLAY_COUNT
        )
        for result in results:
            _assert_exact_invalid_result(result)
            serialized = repr(result).casefold()
            assert replay_case.case_id.casefold() not in serialized
            assert replay_case.fixture_id.casefold() not in serialized
            _assert_no_sensitive_output(result)
        assert replay_case == case_before

    assert replay_runner._REGISTRY is registry_before
    assert replay_runner._registry_state(replay_runner._REGISTRY) == registry_state_before
    assert _fixture_state() == fixture_before


def test_verification_module_has_no_runtime_control_or_activation_dependencies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert imported == {
        "__future__",
        "ast",
        "copy",
        "dataclasses",
        "pathlib",
        "app.services",
    }
    assert imported.isdisjoint(
        {
            "datetime",
            "os",
            "random",
            "socket",
            "subprocess",
            "tempfile",
            "time",
            "requests",
            "httpx",
        }
    )
    forbidden_calls = {
        "open",
        "patch",
        "setattr",
        "setitem",
        "sleep",
        "system",
        "urlopen",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    referenced_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    assert called_names.isdisjoint(forbidden_calls)
    assert called_attributes.isdisjoint(forbidden_calls)
    assert referenced_names.isdisjoint(
        {
            "monkeypatch",
            "Mock",
            "MagicMock",
            "random",
            "tempfile",
        }
    )
    assert called_attributes.isdisjoint({"now", "utcnow", "getenv"})


def test_verification_scope_does_not_claim_activation_or_later_mvp_stages() -> None:
    scope = (__doc__ or "").casefold()

    assert "offline" in scope
    assert "verification only" in scope
    assert "never activation" in scope
    assert "w6-w21" in scope


def _ready_case() -> replay_runner.CanonicalBundleReplayCaseV1:
    return replay_runner.CanonicalBundleReplayCaseV1(
        replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
    )


def _fixture_state() -> tuple[tuple[str, bytes, int], ...]:
    return tuple(
        (
            filename,
            (FIXTURE_DIR / filename).read_bytes(),
            (FIXTURE_DIR / filename).stat().st_mtime_ns,
        )
        for filename in FIXTURE_FILENAMES
    )


def _mutable_snapshot_ids(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> tuple[int, ...]:
    summary = result.canonical_summary
    component_statuses = summary["component_statuses"]
    return (
        id(summary),
        id(summary["bundle_validation_status"]),
        id(component_statuses),
        id(component_statuses["canonical_data_quality_gate"]),
        id(summary["block_reasons"]),
        id(summary["warning_reasons"]),
        id(summary["readiness_notes"]),
        id(summary["next_allowed_stage"]),
        id(summary["next_blocked_stage"]),
    )


def _assert_exact_ready_result(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    _assert_exact_result_shape(result)
    assert result.replay_contract_version == replay_runner.REPLAY_CONTRACT_VERSION
    assert result.registry_version == replay_runner.REGISTRY_VERSION
    assert result.pipeline_contract_version == replay_runner.PIPELINE_CONTRACT_VERSION
    assert result.policy_profile_version == replay_runner.POLICY_PROFILE_VERSION
    assert result.case_id == "canonical_docs_ready"
    assert result.fixture_id == "canonical_docs_fixture_v1"
    assert result.passed is True
    assert result.status_code == replay_runner.CANONICAL_BUNDLE_REPLAY_MATCHED
    assert result.replay_reason_codes == ()
    assert result.canonical_block_reasons == ()
    assert result.canonical_warning_codes == ()

    summary = result.canonical_summary
    assert tuple(summary) == SUMMARY_FIELDS
    assert summary["passed"] is True
    assert summary["status_code"] == "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
    assert (
        summary["source_scope"]
        == "canonical_mt4_demo_readonly_data_quality_summary_only"
    )
    assert (
        summary["validation_stage"]
        == "canonical_bundle_v1_diagnostics_summary_adapter"
    )
    assert (
        summary["fixture_source"]
        == "canonical_bundle_v1_data_quality_gate_result"
    )
    assert summary["block_reasons"] == []
    assert summary["warning_reasons"] == []
    assert summary["readiness_notes"] == [
        "Canonical DataQualityGate passed for read-only diagnostics adaptation.",
        "Readiness is not trading permission.",
        "This summary is read-only and cannot execute orders.",
    ]
    assert summary["next_allowed_stage"] == [
        "demo_readonly_diagnostics_response_integration"
    ]
    assert summary["next_blocked_stage"] == [
        "api_reader_activation",
        "execution_chain",
    ]
    for field_name, expected in SUMMARY_SAFETY_FLAGS.items():
        assert summary[field_name] is expected

    bundle_status = summary["bundle_validation_status"]
    component_statuses = summary["component_statuses"]
    assert type(bundle_status) is dict
    assert tuple(bundle_status) == STATUS_FIELDS
    assert type(component_statuses) is dict
    assert tuple(component_statuses) == ("canonical_data_quality_gate",)
    component_status = component_statuses["canonical_data_quality_gate"]
    assert type(component_status) is dict
    assert tuple(component_status) == STATUS_FIELDS
    assert bundle_status == component_status
    assert bundle_status == {
        "passed": True,
        "status_code": "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
        "block_reasons": [],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }


def _assert_exact_invalid_result(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    _assert_exact_result_shape(result)
    assert (
        result.registry_version,
        result.pipeline_contract_version,
        result.policy_profile_version,
        result.case_id,
        result.fixture_id,
    ) == ("unavailable",) * 5
    assert result.passed is False
    assert result.status_code == replay_runner.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID
    assert result.replay_reason_codes == (replay_runner.REPLAY_CASE_INPUT_INVALID,)
    assert result.canonical_summary == {}
    assert result.canonical_block_reasons == ()
    assert result.canonical_warning_codes == ()


def _assert_exact_result_shape(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    assert type(result) is replay_runner.CanonicalBundleReplayResultV1
    assert tuple(field.name for field in fields(result)) == RESULT_FIELDS
    assert type(result.canonical_summary) is dict
    assert type(result.replay_reason_codes) is tuple
    assert type(result.canonical_block_reasons) is tuple
    assert type(result.canonical_warning_codes) is tuple
    for field_name, expected in RESULT_SAFETY_FLAGS.items():
        assert getattr(result, field_name) is expected


def _assert_no_sensitive_output(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    serialized = repr(result).casefold()
    forbidden = (
        str(FIXTURE_ROOT).casefold(),
        str(FIXTURE_DIR).casefold(),
        *FIXTURE_FILENAMES,
        "raw_payload",
        "digest",
        "checksum",
        "traceback",
        "exception_text",
        "source_status",
        "reader_status",
        "execution_payload",
        "order_ticket",
    )

    assert not any(value in serialized for value in forbidden)
