"""Contract vectors and committed assets for the future docs-fixture producer.

These tests compare approved authoring examples with immutable canonical fixture
assets. One asset acceptance test calls the existing G153 pipeline directly; no
future producer, compatibility adapter, API, or filesystem writer is involved.
"""

from __future__ import annotations

from datetime import UTC, datetime
import inspect
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
)
from app.services import demo_readonly_canonical_diagnostics_pipeline as pipeline
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORING_EXAMPLE_DIR = (
    REPOSITORY_ROOT
    / "docs"
    / "architecture"
    / "examples"
    / "canonical-mt4-demo-readonly-bundle-v1"
)
CANONICAL_FIXTURE_DIR = (
    REPOSITORY_ROOT
    / "docs"
    / "architecture"
    / "fixtures"
    / "canonical-mt4-demo-readonly-bundle-v1"
)
CANONICAL_FILENAMES = (
    "snapshot_manifest.json",
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
AUTHORING_FILENAMES = tuple(
    filename.replace(".json", ".example.json")
    for filename in CANONICAL_FILENAMES
)
FIXTURE_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)

PRODUCER_CONTRACT = MappingProxyType(
    {
        "function_name": "build_demo_readonly_canonical_docs_fixture_diagnostics_summary",
        "parameters": (),
        "return_type": "dict[str, Any]",
        "source_authority": "server_owned_fixed_repository_fixture",
    }
)
G153_CALL_CONTRACT = MappingProxyType(
    {
        "allowed_root": "fixed_fixture_root",
        "bundle_dir": "fixed_fixture_bundle_dir",
        "now_utc": "fixed_fixture_reference_time",
    }
)
FORBIDDEN_PRODUCER_ARGUMENTS = frozenset(
    {
        "source_mode",
        "allowed_root_from_request",
        "bundle_dir_from_request",
        "now_utc_from_request",
        "read_policy",
        "filesystem_policy",
        "data_quality_policy",
        "previous_identity",
        "manifest",
        "payload",
    }
)
G151_SUMMARY_KEYS = frozenset(
    {
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
    }
)
SAFE_FLAGS = MappingProxyType(
    {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
)
FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
        "source_reader_status_code",
        "source_upstream_value_status_code",
        "raw_payload",
        "path",
        "traceback",
        "checksum",
        "checksum_checked",
        "checksum_passed",
        "bridge_dir",
        "base_dir",
        "candidate_path",
        "can_trade",
        "allow_trade",
        "should_buy",
        "should_sell",
        "suggested_lot",
        "order",
        "signal",
        "action",
        "ea_command",
    }
)
FAIL_CLOSED_CASES = (
    MappingProxyType({"case": "fixture_root_missing", "result": "blocked"}),
    MappingProxyType({"case": "fixture_bundle_missing", "result": "blocked"}),
    MappingProxyType({"case": "required_file_missing", "result": "blocked"}),
    MappingProxyType({"case": "renamed_required_file", "result": "blocked"}),
    MappingProxyType({"case": "unexpected_extra_file", "result": "blocked"}),
    MappingProxyType({"case": "symlink_or_path_escape", "result": "blocked"}),
    MappingProxyType({"case": "invalid_or_duplicate_json", "result": "blocked"}),
    MappingProxyType({"case": "manifest_unstable", "result": "blocked"}),
    MappingProxyType({"case": "integrity_mismatch", "result": "blocked"}),
    MappingProxyType({"case": "stale_fixture", "result": "blocked"}),
    MappingProxyType({"case": "unexpected_exception", "result": "blocked"}),
)
FORBIDDEN_FALLBACKS = frozenset(
    {
        "DemoReadOnlyDocsFixtureValidationSummary",
        "old_mt4_diagnostics_reader",
        "old_mt4_diagnostics_service",
        "three_file_demo_reader",
        "parallel_data_quality_gate",
        "data/ runtime directory",
        "real MT4 directory",
    }
)
FORBIDDEN_RUNTIME_SIDE_EFFECTS = frozenset(
    {
        "copy_example_files",
        "rename_example_files",
        "runtime_temporary_directory",
        "write_file",
        "delete_file",
        "create_symlink",
        "download_fixture",
    }
)


def test_future_producer_is_zero_argument_and_server_owned() -> None:
    assert PRODUCER_CONTRACT["function_name"] == (
        "build_demo_readonly_canonical_docs_fixture_diagnostics_summary"
    )
    assert PRODUCER_CONTRACT["parameters"] == ()
    assert PRODUCER_CONTRACT["return_type"] == "dict[str, Any]"
    assert PRODUCER_CONTRACT["source_authority"] == (
        "server_owned_fixed_repository_fixture"
    )
    assert not (set(PRODUCER_CONTRACT) & FORBIDDEN_PRODUCER_ARGUMENTS)


def test_source_layout_uses_canonical_filenames_and_separates_authoring_examples() -> None:
    assert CANONICAL_FIXTURE_DIR != AUTHORING_EXAMPLE_DIR
    assert CANONICAL_FIXTURE_DIR.name == "canonical-mt4-demo-readonly-bundle-v1"
    assert CANONICAL_FILENAMES == (
        "snapshot_manifest.json",
        "live_tick.json",
        "latest_bars.json",
        "symbol_spec.json",
        "account_snapshot.json",
    )
    assert all(filename.endswith(".example.json") for filename in AUTHORING_FILENAMES)
    assert set(CANONICAL_FILENAMES).isdisjoint(AUTHORING_FILENAMES)

    entries = tuple(sorted(CANONICAL_FIXTURE_DIR.iterdir()))
    assert [entry.name for entry in entries] == sorted(CANONICAL_FILENAMES)
    assert all(entry.is_file() for entry in entries)
    assert all(not entry.is_symlink() for entry in entries)


def test_canonical_fixture_assets_match_approved_authoring_examples() -> None:
    for canonical_name, authoring_name in zip(
        CANONICAL_FILENAMES,
        AUTHORING_FILENAMES,
        strict=True,
    ):
        assert _read_fixture_json(canonical_name) == _read_example_json(authoring_name)


def test_authoring_manifest_declares_the_canonical_required_files() -> None:
    manifest_path = AUTHORING_EXAMPLE_DIR / "snapshot_manifest.example.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_files = manifest["required_files"]

    assert [descriptor["filename"] for descriptor in required_files] == [
        "live_tick.json",
        "latest_bars.json",
        "symbol_spec.json",
        "account_snapshot.json",
    ]
    assert manifest["is_demo_account"] is True
    assert manifest["is_live_account"] is False
    assert manifest["read_only"] is True
    assert manifest["demo_only"] is True
    assert manifest["is_tradable"] is False
    assert manifest["can_execute"] is False


def test_fixed_reference_time_is_utc_and_within_current_read_policy() -> None:
    policy = CanonicalMt4DemoReadonlyBundleV1ReadPolicy()
    assert FIXTURE_REFERENCE_TIME.tzinfo is UTC
    assert FIXTURE_REFERENCE_TIME == datetime(
        2026, 7, 10, 2, 30, 5, tzinfo=UTC
    )

    generated_at = _read_example_timestamp("live_tick.example.json")
    latest_bars_at = _read_example_timestamp("latest_bars.example.json")
    symbol_spec_at = _read_example_timestamp("symbol_spec.example.json")
    account_snapshot_at = _read_example_timestamp("account_snapshot.example.json")
    manifest = _read_example_json("snapshot_manifest.example.json")
    heartbeat_at = _parse_timestamp(manifest["writer_heartbeat_at_utc"])

    assert _age_seconds(generated_at) <= policy.live_tick_max_age_seconds
    assert _age_seconds(latest_bars_at) <= policy.latest_bars_max_age_seconds
    assert _age_seconds(symbol_spec_at) <= policy.symbol_spec_max_age_seconds
    assert _age_seconds(account_snapshot_at) <= policy.account_snapshot_max_age_seconds
    assert _age_seconds(heartbeat_at) <= policy.writer_heartbeat_max_age_seconds
    assert all(
        timestamp <= FIXTURE_REFERENCE_TIME
        for timestamp in (
            generated_at,
            latest_bars_at,
            symbol_spec_at,
            account_snapshot_at,
            heartbeat_at,
        )
    )


def test_g153_delegation_shape_has_only_fixed_source_inputs() -> None:
    signature = inspect.signature(
        pipeline.build_demo_readonly_canonical_diagnostics_summary
    )
    assert {"allowed_root", "bundle_dir", "now_utc"}.issubset(signature.parameters)
    assert set(G153_CALL_CONTRACT) == {"allowed_root", "bundle_dir", "now_utc"}
    assert not (set(G153_CALL_CONTRACT) & FORBIDDEN_PRODUCER_ARGUMENTS)
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_g151_output_contract_is_exact_and_readonly() -> None:
    assert len(G151_SUMMARY_KEYS) == 20
    assert "source_reader_status_code" not in G151_SUMMARY_KEYS
    assert "source_upstream_value_status_code" not in G151_SUMMARY_KEYS
    assert "raw_payload" not in G151_SUMMARY_KEYS
    assert set(SAFE_FLAGS) <= G151_SUMMARY_KEYS
    assert SAFE_FLAGS["read_only"] is True
    assert SAFE_FLAGS["demo_only"] is True
    assert SAFE_FLAGS["is_tradable"] is False
    assert SAFE_FLAGS["can_execute"] is False


def test_committed_fixture_runs_real_g153_to_exact_safe_g151_ready_summary() -> None:
    before = _fixture_state()

    result = pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=CANONICAL_FIXTURE_DIR.parent,
        bundle_dir=CANONICAL_FIXTURE_DIR,
        now_utc=FIXTURE_REFERENCE_TIME,
    )

    assert _fixture_state() == before
    assert set(result) == G151_SUMMARY_KEYS
    assert result["passed"] is True
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
    assert result["source_scope"] == adapter.SOURCE_SCOPE
    assert result["validation_stage"] == adapter.VALIDATION_STAGE
    assert result["fixture_source"] == adapter.FIXTURE_SOURCE
    assert result["block_reasons"] == []
    assert result["warning_reasons"] == []
    assert result["next_allowed_stage"] == [
        "demo_readonly_diagnostics_response_integration"
    ]
    assert result["next_blocked_stage"] == [
        "api_reader_activation",
        "execution_chain",
    ]
    for field_name, expected in SAFE_FLAGS.items():
        assert result[field_name] is expected
    _assert_forbidden_output_keys_absent(result)

    serialized = json.dumps(result, sort_keys=True).casefold()
    assert str(CANONICAL_FIXTURE_DIR).casefold() not in serialized
    assert FIXTURE_REFERENCE_TIME.isoformat().casefold() not in serialized


def test_fail_closed_cases_are_explicit_and_immutable() -> None:
    assert type(FAIL_CLOSED_CASES) is tuple
    assert {case["case"] for case in FAIL_CLOSED_CASES} == {
        "fixture_root_missing",
        "fixture_bundle_missing",
        "required_file_missing",
        "renamed_required_file",
        "unexpected_extra_file",
        "symlink_or_path_escape",
        "invalid_or_duplicate_json",
        "manifest_unstable",
        "integrity_mismatch",
        "stale_fixture",
        "unexpected_exception",
    }
    assert all(case["result"] == "blocked" for case in FAIL_CLOSED_CASES)
    with pytest.raises(TypeError):
        FAIL_CLOSED_CASES[0]["result"] = "ready"


def test_no_fallbacks_or_runtime_file_side_effects_are_allowed() -> None:
    assert "DemoReadOnlyDocsFixtureValidationSummary" in FORBIDDEN_FALLBACKS
    assert "old_mt4_diagnostics_reader" in FORBIDDEN_FALLBACKS
    assert "parallel_data_quality_gate" in FORBIDDEN_FALLBACKS
    assert "data/ runtime directory" in FORBIDDEN_FALLBACKS
    assert "real MT4 directory" in FORBIDDEN_FALLBACKS
    assert "copy_example_files" in FORBIDDEN_RUNTIME_SIDE_EFFECTS
    assert "rename_example_files" in FORBIDDEN_RUNTIME_SIDE_EFFECTS
    assert "runtime_temporary_directory" in FORBIDDEN_RUNTIME_SIDE_EFFECTS
    assert "write_file" in FORBIDDEN_RUNTIME_SIDE_EFFECTS
    assert "download_fixture" in FORBIDDEN_RUNTIME_SIDE_EFFECTS


def test_existing_g153_module_is_not_api_activation_code() -> None:
    source = inspect.getsource(pipeline)

    assert "app.api" not in source
    assert "fastapi" not in source.casefold()
    assert "demo_readonly_diagnostics_response(" not in source
    assert "os.environ" not in source
    assert "mt4_demo_readonly_source_summary_from_dir" not in source


def test_fixture_assets_do_not_claim_runtime_implementation() -> None:
    assert CANONICAL_FIXTURE_DIR.is_dir()
    assert "producer_implementation" not in G153_CALL_CONTRACT
    assert "api_activation" not in G153_CALL_CONTRACT
    assert "reader_activation" not in G153_CALL_CONTRACT


def _read_example_json(filename: str) -> dict[str, object]:
    loaded = json.loads((AUTHORING_EXAMPLE_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _read_fixture_json(filename: str) -> dict[str, object]:
    loaded = json.loads((CANONICAL_FIXTURE_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _read_example_timestamp(filename: str) -> datetime:
    payload = _read_example_json(filename)
    return _parse_timestamp(payload["generated_at_utc"])


def _parse_timestamp(value: object) -> datetime:
    assert isinstance(value, str)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    return parsed.astimezone(UTC)


def _age_seconds(observed_at: datetime) -> float:
    return (FIXTURE_REFERENCE_TIME - observed_at).total_seconds()


def _fixture_state() -> dict[str, tuple[bytes, int]]:
    return {
        filename: (
            (CANONICAL_FIXTURE_DIR / filename).read_bytes(),
            (CANONICAL_FIXTURE_DIR / filename).stat().st_mtime_ns,
        )
        for filename in CANONICAL_FILENAMES
    }


def _assert_forbidden_output_keys_absent(value: object) -> None:
    if isinstance(value, dict):
        assert {str(key).casefold() for key in value}.isdisjoint(
            FORBIDDEN_OUTPUT_KEYS
        )
        for child in value.values():
            _assert_forbidden_output_keys_absent(child)
    elif isinstance(value, list):
        for child in value:
            _assert_forbidden_output_keys_absent(child)
