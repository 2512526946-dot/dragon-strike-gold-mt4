"""Real G153 integration evidence only; not activation or deterministic verification."""

from __future__ import annotations

import ast
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from app.services import canonical_bundle_replay_runner as replay_runner


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
FIXTURE_DIR = FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
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
SAFETY_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
}


def test_ready_case_traverses_real_replay_runner_g153_g151_chain() -> None:
    fixture_before = _fixture_state()
    replay_case = _ready_case()

    first = replay_runner.run_canonical_bundle_replay_case(replay_case=replay_case)
    second = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert _fixture_state() == fixture_before
    assert first == second
    assert first is not second
    assert first.canonical_summary is not second.canonical_summary
    assert replay_case == _ready_case()

    _assert_exact_ready_result(first)
    _assert_exact_ready_result(second)
    _assert_no_sensitive_output(first)


def test_delegating_spy_observes_one_exact_real_g153_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_g153 = replay_runner.pipeline.build_demo_readonly_canonical_diagnostics_summary
    calls: list[dict[str, object]] = []

    def _delegating_spy(**kwargs: object) -> dict[str, Any]:
        calls.append(kwargs)
        return real_g153(**kwargs)

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _delegating_spy,
    )
    fixture_before = _fixture_state()

    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == [
        {
            "allowed_root": FIXTURE_ROOT,
            "bundle_dir": FIXTURE_DIR,
            "now_utc": REFERENCE_TIME,
        }
    ]
    assert _fixture_state() == fixture_before
    _assert_exact_ready_result(result)


def test_primary_integration_anchor_has_no_main_chain_patch() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    primary = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_ready_case_traverses_real_replay_runner_g153_g151_chain"
    )
    names = {
        node.id
        for node in ast.walk(primary)
        if isinstance(node, ast.Name)
    }
    attributes = {
        node.attr
        for node in ast.walk(primary)
        if isinstance(node, ast.Attribute)
    }

    assert names.isdisjoint({"monkeypatch", "patch", "Mock", "MagicMock"})
    assert attributes.isdisjoint({"setattr", "setitem"})


def test_integration_evidence_does_not_claim_activation_or_verification() -> None:
    scope = (__doc__ or "").casefold()

    assert "integration evidence only" in scope
    assert "not activation" in scope
    assert "not activation or deterministic verification" in scope


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


def _assert_exact_ready_result(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    assert type(result) is replay_runner.CanonicalBundleReplayResultV1
    assert tuple(field.name for field in fields(result)) == RESULT_FIELDS
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
    for field_name, expected in SAFETY_FLAGS.items():
        assert getattr(result, field_name) is expected

    summary = result.canonical_summary
    assert type(summary) is dict
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
    for field_name, expected in {
        **SAFETY_FLAGS,
        "is_trading_permission": False,
        "allowed_to_modify_risk": False,
    }.items():
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


def _assert_no_sensitive_output(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    serialized = repr(result).casefold()
    forbidden = (
        str(FIXTURE_ROOT).casefold(),
        str(FIXTURE_DIR).casefold(),
        "snapshot_manifest.json",
        "live_tick.json",
        "latest_bars.json",
        "symbol_spec.json",
        "account_snapshot.json",
        "raw_payload",
        "payload",
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
