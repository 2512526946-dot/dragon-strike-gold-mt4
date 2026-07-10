from __future__ import annotations

import builtins
import copy
import json
from pathlib import Path
from typing import Any

import pytest

from app.services.canonical_mt4_demo_readonly_bundle_v1_validator import (
    CANONICAL_MT4_BUNDLE_V1_FORBIDDEN_FIELD_DETECTED,
    CANONICAL_MT4_BUNDLE_V1_IDENTITY_MISMATCH,
    CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_MANIFEST_INVALID,
    CANONICAL_MT4_BUNDLE_V1_PAYLOAD_SET_INVALID,
    CANONICAL_MT4_BUNDLE_V1_PAYLOAD_STRUCTURE_INVALID,
    CANONICAL_MT4_BUNDLE_V1_REQUIRED_FILES_INVALID,
    CANONICAL_MT4_BUNDLE_V1_SAFETY_FIELD_VIOLATION,
    CANONICAL_MT4_BUNDLE_V1_SCHEMA_VERSION_UNSUPPORTED,
    CANONICAL_MT4_BUNDLE_V1_SEQUENCE_IDENTITY_CONFLICT,
    CANONICAL_MT4_BUNDLE_V1_SEQUENCE_ROLLBACK,
    CANONICAL_MT4_BUNDLE_V1_SOURCE_ID_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_SYMBOL_MISMATCH,
    CANONICAL_MT4_BUNDLE_V1_VALID,
    CANONICAL_MT4_BUNDLE_V1_VALID_WITH_WARNINGS,
    validate_canonical_mt4_demo_readonly_bundle_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "examples"
    / "canonical-mt4-demo-readonly-bundle-v1"
)

PAYLOAD_EXAMPLES = {
    "live_tick.json": "live_tick.example.json",
    "latest_bars.json": "latest_bars.example.json",
    "symbol_spec.json": "symbol_spec.example.json",
    "account_snapshot.json": "account_snapshot.example.json",
}

OUTPUT_KEYS = {
    "passed",
    "status_code",
    "validation_stage",
    "contract_version",
    "reason_codes",
    "warning_codes",
    "component_statuses",
    "reader_status",
    "ready_for_readonly_analysis",
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

COMPONENT_KEYS = {"component_name", "passed", "status_code", "reason_codes"}


def test_valid_examples_pass_structure_identity_safety_stage() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(manifest, payloads)

    assert result["passed"] is True
    assert result["status_code"] == CANONICAL_MT4_BUNDLE_V1_VALID
    assert result["reason_codes"] == []
    assert result["warning_codes"] == []


def test_valid_result_remains_readonly_not_ready_and_has_exact_safe_shape() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(manifest, payloads)

    assert set(result) == OUTPUT_KEYS
    assert result["validation_stage"] == "canonical_bundle_v1_structure_identity_safety"
    assert result["contract_version"] == "1.0"
    assert result["reader_status"] == "not_called"
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == ["canonical_payload_value_validation"]
    assert result["next_blocked_stage"] == [
        "filesystem_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    _assert_fixed_safe_output(result)
    component_statuses = result["component_statuses"]
    assert [item["component_name"] for item in component_statuses] == [
        "manifest",
        "live_tick",
        "latest_bars",
        "symbol_spec",
        "account_snapshot",
    ]
    assert all(set(item) == COMPONENT_KEYS for item in component_statuses)
    assert all(item["passed"] is True for item in component_statuses)


def test_manifest_must_be_object() -> None:
    _manifest, payloads = _load_bundle()

    result = _validate([], payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID)
    assert "MANIFEST_NOT_OBJECT" in result["reason_codes"]


def test_payload_map_must_be_object() -> None:
    manifest, _payloads = _load_bundle()

    result = _validate(manifest, [])

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID)
    assert "PAYLOAD_MAP_NOT_OBJECT" in result["reason_codes"]


def test_payload_set_rejects_missing_payload() -> None:
    manifest, payloads = _load_bundle()
    payloads.pop("account_snapshot.json")

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_PAYLOAD_SET_INVALID)
    assert "PAYLOAD_SET_INVALID" in result["reason_codes"]


def test_payload_set_rejects_extra_or_path_like_payload() -> None:
    manifest, payloads = _load_bundle()
    payloads["../account_snapshot.json"] = copy.deepcopy(
        payloads["account_snapshot.json"]
    )

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_PAYLOAD_SET_INVALID)


def test_required_descriptors_reject_missing_extra_and_bad_checksum() -> None:
    manifest, payloads = _load_bundle()
    variants = []

    missing = copy.deepcopy(manifest)
    missing["required_files"].pop()
    variants.append(missing)

    extra = copy.deepcopy(manifest)
    extra["required_files"][0]["unexpected"] = True
    variants.append(extra)

    bad_checksum = copy.deepcopy(manifest)
    bad_checksum["required_files"][0]["content_sha256"] = "A" * 64
    variants.append(bad_checksum)

    for variant in variants:
        result = _validate(variant, payloads)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_REQUIRED_FILES_INVALID)
        assert "REQUIRED_FILES_INVALID" in result["reason_codes"]


def test_manifest_rejects_unknown_field_and_invalid_manifest_values() -> None:
    manifest, payloads = _load_bundle()
    variants = []

    unknown = copy.deepcopy(manifest)
    unknown["unexpected"] = True
    variants.append(unknown)

    bad_bundle_id = copy.deepcopy(manifest)
    bad_bundle_id["bundle_id"] = "short"
    variants.append(bad_bundle_id)

    bad_time = copy.deepcopy(manifest)
    bad_time["committed_at_utc"] = "2026-07-10T02:30:01+00:00"
    variants.append(bad_time)

    for variant in variants:
        result = _validate(variant, payloads)
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_MANIFEST_INVALID)


def test_payload_rejects_unknown_field_non_object_and_non_list_timeframes() -> None:
    manifest, payloads = _load_bundle()

    unknown_payloads = copy.deepcopy(payloads)
    unknown_payloads["live_tick.json"]["unexpected"] = True
    unknown_result = _validate(manifest, unknown_payloads)

    non_object_payloads = copy.deepcopy(payloads)
    non_object_payloads["symbol_spec.json"] = []
    non_object_result = _validate(manifest, non_object_payloads)

    bad_timeframes_payloads = copy.deepcopy(payloads)
    bad_timeframes_payloads["latest_bars.json"]["timeframes"] = {}
    bad_timeframes_result = _validate(manifest, bad_timeframes_payloads)

    for result in (unknown_result, non_object_result, bad_timeframes_result):
        _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_PAYLOAD_STRUCTURE_INVALID)


def test_schema_version_error_is_rejected() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["schema_version"] = "2.0"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SCHEMA_VERSION_UNSUPPORTED)
    assert "SCHEMA_VERSION_UNSUPPORTED" in result["reason_codes"]


def test_source_id_error_is_rejected() -> None:
    manifest, payloads = _load_bundle()
    payloads["symbol_spec.json"]["source_id"] = "untrusted_source"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SOURCE_ID_REJECTED)
    assert "SOURCE_ID_REJECTED" in result["reason_codes"]


def test_safety_flag_error_fails_closed_with_typed_boolean_check() -> None:
    manifest, payloads = _load_bundle()
    payloads["account_snapshot.json"]["is_tradable"] = 0

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SAFETY_FIELD_VIOLATION)
    assert "SAFETY_FIELD_VIOLATION" in result["reason_codes"]


def test_nested_forbidden_field_is_case_insensitive() -> None:
    manifest, payloads = _load_bundle()
    payloads["latest_bars.json"]["timeframes"][0]["bars"][0][
        "PaSsWoRd"
    ] = "NEVER_RETURN_THIS_SECRET"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FORBIDDEN_FIELD_DETECTED)
    assert "FORBIDDEN_FIELD_DETECTED" in result["reason_codes"]
    assert "NEVER_RETURN_THIS_SECRET" not in str(result)


def test_bundle_id_mismatch_is_rejected() -> None:
    manifest, payloads = _load_bundle()
    payloads["live_tick.json"]["bundle_id"] = "demo-bundle-000000000999"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_IDENTITY_MISMATCH)
    assert "IDENTITY_MISMATCH" in result["reason_codes"]


def test_sequence_mismatch_is_rejected() -> None:
    manifest, payloads = _load_bundle()
    payloads["latest_bars.json"]["sequence"] = 2

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_IDENTITY_MISMATCH)


def test_symbol_mismatch_is_rejected() -> None:
    manifest, payloads = _load_bundle()
    payloads["symbol_spec.json"]["broker_symbol"] = "XAUUSD.demo"

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SYMBOL_MISMATCH)
    assert "SYMBOL_MISMATCH" in result["reason_codes"]


def test_previous_identity_sequence_rollback_is_rejected() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(
        manifest,
        payloads,
        previous_identity={"bundle_id": "demo-bundle-000000000000", "sequence": 2},
    )

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SEQUENCE_ROLLBACK)
    assert result["reason_codes"] == ["SEQUENCE_ROLLBACK"]


def test_same_sequence_different_bundle_id_is_rejected() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(
        manifest,
        payloads,
        previous_identity={"bundle_id": "demo-bundle-000000000000", "sequence": 1},
    )

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_SEQUENCE_IDENTITY_CONFLICT)
    assert result["reason_codes"] == ["SEQUENCE_IDENTITY_CONFLICT"]


def test_same_sequence_same_bundle_id_is_idempotent_warning() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(
        manifest,
        payloads,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        },
    )

    assert result["passed"] is True
    assert result["status_code"] == CANONICAL_MT4_BUNDLE_V1_VALID_WITH_WARNINGS
    assert result["reason_codes"] == []
    assert result["warning_codes"] == ["IDEMPOTENT_REPEAT"]


def test_sequence_gap_is_warning_not_readonly_readiness() -> None:
    manifest, payloads = _load_bundle()
    _set_sequence(manifest, payloads, 4)

    result = _validate(
        manifest,
        payloads,
        previous_identity={"bundle_id": "demo-bundle-000000000000", "sequence": 1},
    )

    assert result["passed"] is True
    assert result["status_code"] == CANONICAL_MT4_BUNDLE_V1_VALID_WITH_WARNINGS
    assert result["warning_codes"] == ["SEQUENCE_GAP"]
    assert result["ready_for_readonly_analysis"] is False


def test_previous_identity_must_have_exact_safe_shape() -> None:
    manifest, payloads = _load_bundle()

    result = _validate(
        manifest,
        payloads,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": True,
            "extra": "not-allowed",
        },
    )

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_INPUT_INVALID)
    assert "PREVIOUS_IDENTITY_INVALID" in result["reason_codes"]


def test_output_does_not_leak_input_and_validator_is_pure_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, payloads = _load_bundle()
    original_manifest = copy.deepcopy(manifest)
    original_payloads = copy.deepcopy(payloads)
    payloads["live_tick.json"]["raw_payload"] = {
        "token": "SUPER_SECRET_VALUE",
        "candidate_path": "C:/private/bridge/live_tick.json",
    }
    original_payloads = copy.deepcopy(payloads)

    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("validator must not access the filesystem")

    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "read_text", fail_if_called)
    monkeypatch.setattr(Path, "read_bytes", fail_if_called)
    monkeypatch.setattr(Path, "exists", fail_if_called)
    monkeypatch.setattr(Path, "is_file", fail_if_called)

    result = _validate(manifest, payloads)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FORBIDDEN_FIELD_DETECTED)
    assert set(result) == OUTPUT_KEYS
    assert "SUPER_SECRET_VALUE" not in str(result)
    assert "C:/private/bridge/live_tick.json" not in str(result)
    assert manifest == original_manifest
    assert payloads == original_payloads


def _load_bundle() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    with (EXAMPLE_DIR / "snapshot_manifest.example.json").open(encoding="utf-8") as file:
        manifest = json.load(file)

    payloads = {}
    for canonical_filename, example_filename in PAYLOAD_EXAMPLES.items():
        with (EXAMPLE_DIR / example_filename).open(encoding="utf-8") as file:
            payloads[canonical_filename] = json.load(file)
    return manifest, payloads


def _validate(
    manifest: object,
    payloads: object,
    *,
    previous_identity: object | None = None,
) -> dict[str, Any]:
    return validate_canonical_mt4_demo_readonly_bundle_v1(
        manifest=manifest,
        payloads_by_filename=payloads,
        previous_identity=previous_identity,
    )


def _set_sequence(
    manifest: dict[str, Any],
    payloads: dict[str, dict[str, Any]],
    sequence: int,
) -> None:
    manifest["sequence"] = sequence
    for payload in payloads.values():
        payload["sequence"] = sequence


def _assert_blocked(result: dict[str, Any], expected_status: str) -> None:
    assert result["passed"] is False
    assert result["status_code"] == expected_status
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == []
    _assert_fixed_safe_output(result)


def _assert_fixed_safe_output(result: dict[str, Any]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False
