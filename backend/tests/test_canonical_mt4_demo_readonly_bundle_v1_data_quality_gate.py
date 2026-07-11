from __future__ import annotations

import copy
from dataclasses import replace
from datetime import UTC, datetime
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import app.services.data_quality_gate as gate_module
import app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader as reader_module
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
    read_and_validate_canonical_mt4_demo_readonly_bundle_v1,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
    CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS,
)
from app.services.data_quality_gate import (
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED,
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy,
    DATA_QUALITY_COMPONENT_STATUS_INVALID,
    DATA_QUALITY_GATE_EXCEPTION_SANITIZED,
    DATA_QUALITY_INPUT_NOT_OBJECT,
    DATA_QUALITY_POLICY_INVALID,
    DATA_QUALITY_READER_FIELD_TYPE_INVALID,
    DATA_QUALITY_REQUIRED_READER_KEY_MISSING,
    DATA_QUALITY_UNEXPECTED_READER_KEY,
    READER_BLOCKED,
    READER_DATA_STALE,
    READER_INTEGRITY_INVALID,
    READER_MIXED_GENERATION_BLOCKED,
    READER_RESULT_INCONSISTENT,
    READER_SAFETY_ENVELOPE_INVALID,
    READER_STRUCTURE_INVALID,
    READER_VALUE_INVALID,
    READER_WARNING_CODES_INVALID,
    UPSTREAM_WARNINGS_REJECTED_BY_POLICY,
    evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "examples"
    / "canonical-mt4-demo-readonly-bundle-v1"
)
EXAMPLE_FILES = {
    "snapshot_manifest.json": "snapshot_manifest.example.json",
    "live_tick.json": "live_tick.example.json",
    "latest_bars.json": "latest_bars.example.json",
    "symbol_spec.json": "symbol_spec.example.json",
    "account_snapshot.json": "account_snapshot.example.json",
}
NOW_UTC = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)

OUTPUT_KEYS = {
    "passed",
    "status_code",
    "validation_stage",
    "contract_version",
    "reader_status",
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "data_quality_status",
    "reason_codes",
    "warning_codes",
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


def test_real_g148_result_passes_and_has_exact_safe_output(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)

    result = _evaluate(reader_result)

    assert set(result) == OUTPUT_KEYS
    assert result["passed"] is True
    assert result["status_code"] == CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
    assert result["validation_stage"] == "canonical_bundle_v1_data_quality_gate"
    assert result["contract_version"] == "1.0"
    assert result["reader_status"] == "validated_isolated"
    assert result["source_reader_status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID
    )
    assert result["source_upstream_value_status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID
    )
    assert result["data_quality_status"] == "passed"
    assert result["reason_codes"] == []
    assert result["warning_codes"] == []
    _assert_success_envelope(result)


def test_checksum_not_required_is_a_valid_success_result(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)

    assert reader_result["checksum_checked"] is False
    assert reader_result["checksum_passed"] is True
    assert _evaluate(reader_result)["passed"] is True


@pytest.mark.parametrize(
    ("sequence_delta", "warning_code"),
    [(0, "IDEMPOTENT_REPEAT"), (-2, "SEQUENCE_GAP")],
)
def test_exact_warning_whitelist_is_safely_propagated(
    tmp_path: Path,
    sequence_delta: int,
    warning_code: str,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    if warning_code == "SEQUENCE_GAP":
        _set_bundle_sequence(bundle, 3)
    manifest = _load_json(bundle / "snapshot_manifest.json")
    previous_identity = {
        "bundle_id": manifest["bundle_id"],
        "sequence": manifest["sequence"] + sequence_delta,
    }
    reader_result = _read(root, bundle, previous_identity=previous_identity)

    result = _evaluate(reader_result)

    assert reader_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
    )
    assert result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
    )
    assert result["data_quality_status"] == "passed_with_warnings"
    assert result["warning_codes"] == [warning_code]
    _assert_success_envelope(result)


def test_valid_warning_can_be_rejected_by_typed_policy(tmp_path: Path) -> None:
    reader_result = _warning_reader_result(tmp_path)
    policy = CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy(
        allow_upstream_warnings=False
    )

    result = _evaluate(reader_result, policy=policy)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
        UPSTREAM_WARNINGS_REJECTED_BY_POLICY,
    )
    assert result["warning_codes"] == ["IDEMPOTENT_REPEAT"]


def test_actual_missing_file_is_reader_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / "live_tick.json").unlink()

    result = _evaluate(_read(root, bundle))

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
        READER_BLOCKED,
    )


def test_actual_invalid_json_is_structure_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / "live_tick.json").write_text("{", encoding="utf-8")

    result = _evaluate(_read(root, bundle))

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STRUCTURE_BLOCKED,
        READER_STRUCTURE_INVALID,
    )


def test_actual_stale_bundle_is_stale_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    stale_now = datetime(2026, 7, 10, 2, 31, 0, tzinfo=UTC)

    result = _evaluate(_read(root, bundle, now_utc=stale_now))

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
        READER_DATA_STALE,
    )


def test_actual_invalid_value_is_value_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    live_tick = _load_json(bundle / "live_tick.json")
    live_tick["ask"] = live_tick["bid"] - 1
    _write_json(bundle / "live_tick.json", live_tick)

    result = _evaluate(_read(root, bundle))

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_VALUE_BLOCKED,
        READER_VALUE_INVALID,
    )


def test_actual_checksum_mismatch_is_integrity_not_mixed_generation(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    _set_checksum(bundle, "live_tick.json", "0" * 64)
    reader_result = _read(root, bundle)

    result = _evaluate(reader_result)

    assert reader_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH
    )
    assert reader_result["checksum_checked"] is True
    assert reader_result["checksum_passed"] is False
    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INTEGRITY_BLOCKED,
        READER_INTEGRITY_INVALID,
    )
    assert READER_MIXED_GENERATION_BLOCKED not in result["reason_codes"]


def test_actual_unstable_manifest_is_the_only_mixed_generation_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    stable = (bundle / "snapshot_manifest.json").read_bytes()
    changed_data = json.loads(stable.decode("utf-8"))
    changed_data["committed_at_utc"] = "2026-07-10T02:30:02Z"
    versions = iter([stable, json.dumps(changed_data).encode("utf-8")])
    original_reader = reader_module._read_file_bytes

    def changing_manifest(path: Path) -> bytes:
        if path.name == "snapshot_manifest.json":
            return next(versions)
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", changing_manifest)
    filesystem_policy = CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
        max_manifest_consistency_retries=0
    )
    reader_result = _read(root, bundle, filesystem_policy=filesystem_policy)

    result = _evaluate(reader_result)

    assert reader_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE
    )
    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_MIXED_GENERATION_BLOCKED,
        READER_MIXED_GENERATION_BLOCKED,
    )


class _ReaderResultSubclass(dict[str, Any]):
    pass


@pytest.mark.parametrize("value", [None, [], _ReaderResultSubclass()])
def test_reader_result_must_be_a_strict_dict(value: object) -> None:
    result = _evaluate(value)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        DATA_QUALITY_INPUT_NOT_OBJECT,
    )
    assert result["source_reader_status_code"] is None
    assert result["source_upstream_value_status_code"] is None


def test_missing_reader_key_is_blocked(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    del reader_result["checksum_checked"]

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        DATA_QUALITY_REQUIRED_READER_KEY_MISSING,
    )


def test_extra_secret_key_is_blocked_and_not_leaked(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result["secret"] = "must-not-leak"

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        DATA_QUALITY_UNEXPECTED_READER_KEY,
    )
    assert "must-not-leak" not in json.dumps(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("passed", 1),
        ("status_code", 1),
        ("upstream_value_status_code", 1),
        ("reason_codes", ()),
        ("warning_codes", {}),
        ("next_allowed_stage", "canonical_data_quality_gate_integration"),
        ("next_blocked_stage", None),
    ],
)
def test_top_level_field_types_are_strict(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result[field] = value

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        DATA_QUALITY_READER_FIELD_TYPE_INVALID,
    )


@pytest.mark.parametrize("value", [{}, ["not-a-dict"]])
def test_component_statuses_must_be_strict_list_of_dicts(
    tmp_path: Path,
    value: object,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result["component_statuses"] = value

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        DATA_QUALITY_COMPONENT_STATUS_INVALID,
    )


def test_component_with_extra_key_is_blocked(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result["component_statuses"][0]["secret"] = "hidden"

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        DATA_QUALITY_COMPONENT_STATUS_INVALID,
    )
    assert "hidden" not in json.dumps(result)


def test_component_passed_true_requires_empty_reasons(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result["component_statuses"][0]["reason_codes"] = ["INCONSISTENT"]

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_RESULT_INCONSISTENT,
    )


def test_top_warning_codes_must_equal_ordered_component_union(tmp_path: Path) -> None:
    reader_result = _warning_reader_result(tmp_path)
    reader_result["component_statuses"][-1]["warning_codes"] = []

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_WARNING_CODES_INVALID,
    )
    assert result["warning_codes"] == []


def test_unknown_uppercase_warning_is_blocked(tmp_path: Path) -> None:
    reader_result = _warning_reader_result(tmp_path)
    reader_result["warning_codes"] = ["UNKNOWN_WARNING"]
    reader_result["component_statuses"][-1]["warning_codes"] = [
        "UNKNOWN_WARNING"
    ]

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_WARNING_CODES_INVALID,
    )
    assert result["warning_codes"] == []


@pytest.mark.parametrize(
    ("field", "unknown_value", "reader_status_expected", "upstream_expected"),
    [
        (
            "status_code",
            "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UNKNOWN",
            None,
            CANONICAL_MT4_BUNDLE_V1_VALUE_VALID,
        ),
        (
            "upstream_value_status_code",
            "CANONICAL_MT4_BUNDLE_V1_VALUE_UNKNOWN",
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
            None,
        ),
    ],
)
def test_unknown_source_status_is_safety_blocked(
    tmp_path: Path,
    field: str,
    unknown_value: str,
    reader_status_expected: str | None,
    upstream_expected: str | None,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result[field] = unknown_value

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_SAFETY_ENVELOPE_INVALID,
    )
    assert result["source_reader_status_code"] == reader_status_expected
    assert result["source_upstream_value_status_code"] == upstream_expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("passed", False),
        ("reader_status", "blocked"),
        ("ready_for_readonly_analysis", True),
        ("next_allowed_stage", []),
        ("checksum_passed", False),
    ],
)
def test_success_status_combinations_must_be_consistent(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result[field] = value

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_RESULT_INCONSISTENT,
    )


def test_warning_status_combination_must_be_consistent(tmp_path: Path) -> None:
    reader_result = _warning_reader_result(tmp_path)
    reader_result["upstream_value_status_code"] = (
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID
    )

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_RESULT_INCONSISTENT,
    )


def test_checksum_failure_combination_must_be_consistent(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    _set_checksum(bundle, "live_tick.json", "0" * 64)
    reader_result = _read(root, bundle)
    reader_result["checksum_checked"] = False

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_RESULT_INCONSISTENT,
    )


def test_fixed_safety_flags_cannot_be_relaxed(tmp_path: Path) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result["is_tradable"] = True

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_SAFETY_ENVELOPE_INVALID,
    )
    _assert_safe_flags(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("validation_stage", "other_stage"),
        ("contract_version", "2.0"),
    ],
)
def test_source_stage_and_contract_version_are_fixed(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    reader_result[field] = value

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFETY_BLOCKED,
        READER_SAFETY_ENVELOPE_INVALID,
    )


@pytest.mark.parametrize(
    "policy",
    [
        object(),
        CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy(
            allow_upstream_warnings=1  # type: ignore[arg-type]
        ),
    ],
)
def test_policy_must_be_typed_and_strict(
    tmp_path: Path,
    policy: object,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)

    result = _evaluate(reader_result, policy=policy)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
        DATA_QUALITY_POLICY_INVALID,
    )
    assert result["source_reader_status_code"] is None
    assert result["source_upstream_value_status_code"] is None


def test_reader_result_and_policy_are_not_mutated(tmp_path: Path) -> None:
    reader_result = _warning_reader_result(tmp_path)
    before = copy.deepcopy(reader_result)
    policy = CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy()
    policy_before = replace(policy)

    result = _evaluate(reader_result, policy=policy)
    result["warning_codes"].append("LOCAL_MUTATION")

    assert reader_result == before
    assert policy == policy_before
    assert "LOCAL_MUTATION" not in reader_result["warning_codes"]


def test_unexpected_exception_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    secret_message = "secret path and balance must not leak"

    def explode(*_: object, **__: object) -> str | None:
        raise RuntimeError(secret_message)

    monkeypatch.setattr(gate_module, "_canonical_reader_safety_reason", explode)

    result = _evaluate(reader_result)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_SAFE_FAILURE,
        DATA_QUALITY_GATE_EXCEPTION_SANITIZED,
    )
    assert secret_message not in json.dumps(result)


def test_output_does_not_leak_reader_payload_or_sensitive_values(
    tmp_path: Path,
) -> None:
    reader_result = _read_valid_bundle(tmp_path)
    serialized = json.dumps(_evaluate(reader_result), sort_keys=True)

    assert "component_statuses" not in serialized
    assert "snapshot_manifest" not in serialized
    assert "2300.5" not in serialized
    assert "10000.0" not in serialized
    assert "2026-07-10T" not in serialized
    assert "content_sha256" not in serialized


def test_production_gate_is_pure_memory_and_does_not_call_reader() -> None:
    source = inspect.getsource(gate_module)

    assert "read_and_validate_canonical_mt4_demo_readonly_bundle_v1" not in source
    assert "Path(" not in source
    assert "open(" not in source
    assert "app.api" not in source
    assert "fastapi" not in source.casefold()


def _read_valid_bundle(tmp_path: Path) -> dict[str, Any]:
    root, bundle = _create_bundle(tmp_path)
    return _read(root, bundle)


def _warning_reader_result(tmp_path: Path) -> dict[str, Any]:
    root, bundle = _create_bundle(tmp_path)
    manifest = _load_json(bundle / "snapshot_manifest.json")
    previous_identity = {
        "bundle_id": manifest["bundle_id"],
        "sequence": manifest["sequence"],
    }
    result = _read(root, bundle, previous_identity=previous_identity)
    assert result["warning_codes"] == ["IDEMPOTENT_REPEAT"]
    assert result["upstream_value_status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_VALUE_VALID_WITH_WARNINGS
    )
    return result


def _create_bundle(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "allowed"
    bundle = root / "bundle"
    bundle.mkdir(parents=True)
    for target_name, example_name in EXAMPLE_FILES.items():
        (bundle / target_name).write_bytes((EXAMPLE_DIR / example_name).read_bytes())
    return root, bundle


def _read(
    allowed_root: object,
    bundle_dir: object,
    *,
    now_utc: object = NOW_UTC,
    previous_identity: object | None = None,
    filesystem_policy: object = None,
) -> dict[str, Any]:
    return read_and_validate_canonical_mt4_demo_readonly_bundle_v1(
        allowed_root=allowed_root,
        bundle_dir=bundle_dir,
        now_utc=now_utc,
        previous_identity=previous_identity,
        filesystem_policy=filesystem_policy,
    )


def _evaluate(
    reader_result: object,
    *,
    policy: object = None,
) -> dict[str, Any]:
    return evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate(
        reader_result=reader_result,
        policy=policy,  # type: ignore[arg-type]
    )


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _set_checksum(bundle: Path, filename: str, digest: str) -> None:
    manifest_path = bundle / "snapshot_manifest.json"
    manifest = _load_json(manifest_path)
    for descriptor in manifest["required_files"]:
        if descriptor["filename"] == filename:
            descriptor["content_sha256"] = digest
    _write_json(manifest_path, manifest)


def _set_bundle_sequence(bundle: Path, sequence: int) -> None:
    for filename in EXAMPLE_FILES:
        path = bundle / filename
        payload = _load_json(path)
        payload["sequence"] = sequence
        _write_json(path, payload)


def _assert_success_envelope(result: dict[str, Any]) -> None:
    assert result["reader_status"] == "validated_isolated"
    assert result["ready_for_readonly_analysis"] is True
    assert result["next_allowed_stage"] == ["canonical_diagnostics_integration"]
    assert result["next_blocked_stage"] == [
        "api_reader_activation",
        "execution_chain",
    ]
    _assert_safe_flags(result)


def _assert_blocked(
    result: dict[str, Any],
    status_code: str,
    reason_code: str,
) -> None:
    assert set(result) == OUTPUT_KEYS
    assert result["passed"] is False
    assert result["status_code"] == status_code
    assert result["data_quality_status"] == "blocked"
    assert result["reason_codes"] == [reason_code]
    assert result["reader_status"] == "blocked"
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == []
    assert result["next_blocked_stage"] == [
        "canonical_diagnostics_integration",
        "api_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    _assert_safe_flags(result)


def _assert_safe_flags(result: dict[str, Any]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False
