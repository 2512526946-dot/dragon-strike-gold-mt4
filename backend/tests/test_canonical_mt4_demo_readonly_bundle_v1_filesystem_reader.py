from __future__ import annotations

import copy
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader as reader_module
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID,
    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS,
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
    read_and_validate_canonical_mt4_demo_readonly_bundle_v1,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
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
    "reason_codes",
    "warning_codes",
    "component_statuses",
    "manifest_consistency_checked",
    "manifest_consistency_passed",
    "checksum_checked",
    "checksum_passed",
    "upstream_value_passed",
    "upstream_value_status_code",
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
COMPONENT_KEYS = {
    "component_name",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
}
COMPONENT_NAMES = [
    "filesystem_boundary",
    "snapshot_manifest",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
    "manifest_consistency",
    "checksum",
    "upstream_value_validation",
]


def test_valid_temporary_bundle_passes_isolated_filesystem_validation(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert result["status_code"] == CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID
    assert result["reason_codes"] == []
    assert result["warning_codes"] == []
    assert result["upstream_value_passed"] is True


def test_success_has_exact_safe_shape_and_is_not_analysis_ready(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _read(root, bundle)

    assert set(result) == OUTPUT_KEYS
    assert result["validation_stage"] == (
        "canonical_bundle_v1_isolated_filesystem_reader"
    )
    assert result["contract_version"] == "1.0"
    assert result["reader_status"] == "validated_isolated"
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == [
        "canonical_data_quality_gate_integration"
    ]
    assert result["next_blocked_stage"] == [
        "api_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    _assert_safe_flags(result)


def test_success_reports_only_whitelisted_components(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)

    components = _read(root, bundle)["component_statuses"]

    assert [component["component_name"] for component in components] == COMPONENT_NAMES
    assert all(set(component) == COMPONENT_KEYS for component in components)
    assert all(component["passed"] is True for component in components)


@pytest.mark.parametrize("value", [None, 1, "", "  ", " root"])
def test_invalid_allowed_root_input_is_rejected(tmp_path: Path, value: object) -> None:
    _, bundle = _create_bundle(tmp_path)

    result = _read(value, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID)
    assert result["reason_codes"] == ["ALLOWED_ROOT_INPUT_INVALID"]


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_existing_directory_is_required_for_allowed_root(
    tmp_path: Path,
    kind: str,
) -> None:
    _, bundle = _create_bundle(tmp_path)
    candidate = tmp_path / "bad-root"
    if kind == "file":
        candidate.write_text("not a directory", encoding="utf-8")

    result = _read(candidate, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED)
    assert result["reason_codes"] == ["ALLOWED_ROOT_REJECTED"]


@pytest.mark.parametrize("value", [None, 1, "", " bundle", "bundle "])
def test_invalid_bundle_directory_input_is_rejected(
    tmp_path: Path,
    value: object,
) -> None:
    root, _ = _create_bundle(tmp_path)

    result = _read(root, value)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID)
    assert result["reason_codes"] == ["BUNDLE_DIRECTORY_INPUT_INVALID"]


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_existing_directory_is_required_for_bundle_dir(
    tmp_path: Path,
    kind: str,
) -> None:
    root, _ = _create_bundle(tmp_path)
    candidate = root / "bad-bundle"
    if kind == "file":
        candidate.write_text("not a directory", encoding="utf-8")

    result = _read(root, candidate)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED)
    assert result["reason_codes"] == ["BUNDLE_DIRECTORY_REJECTED"]


def test_bundle_directory_escape_is_blocked(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    _, outside_bundle = _create_bundle(tmp_path, root_name="outside")

    result = _read(root, outside_bundle)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
    )
    assert result["reason_codes"] == ["PATH_ESCAPE_BLOCKED"]


def test_bundle_directory_symlink_is_blocked(tmp_path: Path) -> None:
    root, real_bundle = _create_bundle(tmp_path)
    link = root / "bundle-link"
    _make_symlink_or_skip(link, real_bundle, target_is_directory=True)

    result = _read(root, link)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED)
    assert result["reason_codes"] == ["SYMLINK_BLOCKED"]


def test_payload_file_symlink_is_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    payload = bundle / "live_tick.json"
    target = bundle / "live_tick-target.json"
    payload.replace(target)
    _make_symlink_or_skip(payload, target, target_is_directory=False)

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED)
    assert result["reason_codes"] == ["SYMLINK_BLOCKED"]


def test_missing_manifest_is_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / "snapshot_manifest.json").unlink()

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING)
    assert result["reason_codes"] == ["FILE_NOT_FOUND"]


@pytest.mark.parametrize(
    "filename",
    [
        "live_tick.json",
        "latest_bars.json",
        "symbol_spec.json",
        "account_snapshot.json",
    ],
)
def test_each_missing_payload_is_blocked(tmp_path: Path, filename: str) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / filename).unlink()

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING)
    assert result["reason_codes"] == ["FILE_NOT_FOUND"]


def test_manifest_size_is_checked_before_full_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = bundle / "snapshot_manifest.json"
    manifest.write_bytes(b"x" * 33)
    calls: list[Path] = []
    monkeypatch.setattr(reader_module, "_read_file_bytes", lambda path: calls.append(path))
    policy = CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
        manifest_max_bytes=32
    )

    result = _read(root, bundle, filesystem_policy=policy)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE)
    assert result["reason_codes"] == ["FILE_SIZE_LIMIT_EXCEEDED"]
    assert calls == []


@pytest.mark.parametrize(
    ("filename", "policy_field"),
    [
        ("live_tick.json", "live_tick_max_bytes"),
        ("latest_bars.json", "latest_bars_max_bytes"),
        ("symbol_spec.json", "symbol_spec_max_bytes"),
        ("account_snapshot.json", "account_snapshot_max_bytes"),
    ],
)
def test_each_payload_size_limit_is_enforced(
    tmp_path: Path,
    filename: str,
    policy_field: str,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / filename).write_bytes(b"x" * 33)
    policy = replace(
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(),
        **{policy_field: 32},
    )

    result = _read(root, bundle, filesystem_policy=policy)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE)
    assert result["reason_codes"] == ["FILE_SIZE_LIMIT_EXCEEDED"]


def test_actual_byte_length_is_checked_after_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = bundle / "snapshot_manifest.json"
    original = manifest.read_bytes()
    original_reader = reader_module._read_file_bytes

    def read_larger(path: Path) -> bytes:
        if path.name == "snapshot_manifest.json":
            return original + b" "
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", read_larger)
    policy = CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
        manifest_max_bytes=len(original)
    )

    result = _read(root, bundle, filesystem_policy=policy)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE)
    assert result["reason_codes"] == ["FILE_SIZE_LIMIT_EXCEEDED"]


@pytest.mark.parametrize("filename", ["snapshot_manifest.json", "live_tick.json"])
def test_utf8_bom_is_rejected(tmp_path: Path, filename: str) -> None:
    root, bundle = _create_bundle(tmp_path)
    path = bundle / filename
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID)
    assert result["reason_codes"] == ["UTF8_BOM_REJECTED"]


@pytest.mark.parametrize("filename", ["snapshot_manifest.json", "symbol_spec.json"])
def test_invalid_utf8_is_rejected(tmp_path: Path, filename: str) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / filename).write_bytes(b"{\xff}")

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID)
    assert result["reason_codes"] == ["UTF8_DECODE_INVALID"]


@pytest.mark.parametrize("filename", ["snapshot_manifest.json", "latest_bars.json"])
def test_invalid_json_is_rejected(tmp_path: Path, filename: str) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / filename).write_text('{"broken":}', encoding="utf-8")

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_INVALID"]


def test_manifest_top_level_duplicate_key_is_rejected(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = bundle / "snapshot_manifest.json"
    _replace_raw_json_once(
        manifest,
        '  "commit_state": "complete",',
        '  "commit_state": "complete",\n  "commit_state": "complete",',
    )

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_DUPLICATE_KEY"]
    assert result["ready_for_readonly_analysis"] is False


def test_payload_top_level_duplicate_safety_key_is_rejected(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    live_tick = bundle / "live_tick.json"
    _replace_raw_json_once(
        live_tick,
        '  "is_tradable": false,',
        '  "is_tradable": true,\n  "is_tradable": false,',
    )

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_DUPLICATE_KEY"]


def test_nested_bar_duplicate_key_is_rejected(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    latest_bars = bundle / "latest_bars.json"
    _replace_raw_json_once(
        latest_bars,
        '          "close": 2300.2,',
        '          "close": 2300.1,\n          "close": 2300.2,',
    )

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_DUPLICATE_KEY"]


def test_manifest_descriptor_duplicate_key_is_rejected(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = bundle / "snapshot_manifest.json"
    _replace_raw_json_once(
        manifest,
        '      "filename": "live_tick.json",',
        (
            '      "filename": "account_snapshot.json",\n'
            '      "filename": "live_tick.json",'
        ),
    )

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_DUPLICATE_KEY"]


def test_duplicate_key_failure_does_not_leak_key_value_path_or_exception(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    live_tick = bundle / "live_tick.json"
    _replace_raw_json_once(
        live_tick,
        '  "is_tradable": false,',
        (
            '  "is_tradable": "SUPER_SECRET_DUPLICATE_VALUE",\n'
            '  "is_tradable": false,'
        ),
    )

    result = _read(root, bundle)
    serialized = json.dumps(result, sort_keys=True)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_DUPLICATE_KEY"]
    assert "SUPER_SECRET_DUPLICATE_VALUE" not in serialized
    assert '\"is_tradable\": \"SUPER_SECRET_DUPLICATE_VALUE\"' not in serialized
    assert str(root) not in serialized
    assert str(bundle) not in serialized
    assert "_DuplicateJsonKeyDetected" not in serialized


def test_non_standard_json_constants_are_rejected(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / "live_tick.json").write_text('{"value": NaN}', encoding="utf-8")

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID)
    assert result["reason_codes"] == ["JSON_INVALID"]


@pytest.mark.parametrize("filename", ["snapshot_manifest.json", "account_snapshot.json"])
def test_json_top_level_must_be_object(tmp_path: Path, filename: str) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / filename).write_text("[]", encoding="utf-8")

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT)
    assert result["reason_codes"] == ["JSON_NOT_OBJECT"]


def test_tmp_files_are_ignored(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    tmp_file = bundle / "snapshot_manifest.tmp"
    tmp_file.write_bytes(b"not-json-and-must-not-be-read")

    result = _read(root, bundle)

    assert result["passed"] is True
    assert tmp_file.read_bytes() == b"not-json-and-must-not-be-read"


def test_stable_manifest_is_read_twice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, bundle = _create_bundle(tmp_path)
    original_reader = reader_module._read_file_bytes
    manifest_reads = 0

    def record_reads(path: Path) -> bytes:
        nonlocal manifest_reads
        if path.name == "snapshot_manifest.json":
            manifest_reads += 1
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", record_reads)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert manifest_reads == 2
    assert result["manifest_consistency_checked"] is True
    assert result["manifest_consistency_passed"] is True


def test_manifest_change_retries_entire_read_once_and_can_recover(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    original_reader = reader_module._read_file_bytes
    stable = (bundle / "snapshot_manifest.json").read_bytes()
    changed_data = json.loads(stable.decode("utf-8"))
    changed_data["committed_at_utc"] = "2026-07-10T02:30:02Z"
    changed = json.dumps(changed_data).encode("utf-8")
    manifest_versions = iter([stable, changed, stable, stable])
    payload_reads = 0

    def changing_manifest(path: Path) -> bytes:
        nonlocal payload_reads
        if path.name == "snapshot_manifest.json":
            return next(manifest_versions)
        payload_reads += 1
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", changing_manifest)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert payload_reads == 8
    assert result["manifest_consistency_passed"] is True


def test_manifest_change_is_blocked_when_retry_is_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    stable, changed = _manifest_versions(bundle)
    versions = iter([stable, changed])
    original_reader = reader_module._read_file_bytes

    def changing_manifest(path: Path) -> bytes:
        if path.name == "snapshot_manifest.json":
            return next(versions)
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", changing_manifest)
    policy = CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
        max_manifest_consistency_retries=0
    )

    result = _read(root, bundle, filesystem_policy=policy)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE)
    assert result["reason_codes"] == [
        "MANIFEST_CHANGED_DURING_READ",
        "MANIFEST_UNSTABLE",
    ]


def test_continuously_changing_manifest_is_blocked_after_one_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    stable, changed = _manifest_versions(bundle)
    versions = iter([stable, changed, stable, changed])
    original_reader = reader_module._read_file_bytes

    def changing_manifest(path: Path) -> bytes:
        if path.name == "snapshot_manifest.json":
            return next(versions)
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", changing_manifest)

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE)
    assert result["reason_codes"] == [
        "MANIFEST_CHANGED_DURING_READ",
        "MANIFEST_UNSTABLE",
    ]
    assert result["manifest_consistency_checked"] is True
    assert result["manifest_consistency_passed"] is False


def test_null_checksums_are_not_calculated_or_required(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert result["checksum_checked"] is False
    assert result["checksum_passed"] is True


def test_matching_sha256_checksum_passes(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    payload = bundle / "live_tick.json"
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    _set_checksum(bundle, "live_tick.json", digest)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert result["checksum_checked"] is True
    assert result["checksum_passed"] is True


def test_mismatched_sha256_checksum_is_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    _set_checksum(bundle, "live_tick.json", "0" * 64)

    result = _read(root, bundle)

    _assert_blocked(
        result,
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH,
    )
    assert result["reason_codes"] == ["CHECKSUM_MISMATCH"]
    assert result["checksum_checked"] is True
    assert result["checksum_passed"] is False
    assert result["upstream_value_status_code"] is None


def test_g147_stale_result_is_safely_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    stale_now = datetime(2026, 7, 10, 2, 31, 0, tzinfo=UTC)

    result = _read(root, bundle, now_utc=stale_now)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED)
    assert result["reason_codes"] == ["UPSTREAM_VALUE_VALIDATION_BLOCKED"]
    assert result["upstream_value_passed"] is False
    assert result["upstream_value_status_code"] == (
        "CANONICAL_MT4_BUNDLE_V1_DATA_STALE"
    )


def test_g147_invalid_value_result_is_safely_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    live_tick = _load_json(bundle / "live_tick.json")
    live_tick["ask"] = live_tick["bid"] - 1
    _write_json(bundle / "live_tick.json", live_tick)

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED)
    assert result["upstream_value_status_code"] == (
        "CANONICAL_MT4_BUNDLE_V1_LIVE_TICK_INVALID"
    )


def test_g147_sequence_warning_is_preserved(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = _load_json(bundle / "snapshot_manifest.json")
    previous_identity = {
        "bundle_id": manifest["bundle_id"],
        "sequence": manifest["sequence"],
    }

    result = _read(root, bundle, previous_identity=previous_identity)

    assert result["passed"] is True
    assert result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
    )
    assert result["warning_codes"] == ["IDEMPOTENT_REPEAT"]


def test_filesystem_policy_must_be_typed_dataclass(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _read(root, bundle, filesystem_policy={"manifest_max_bytes": 999999})

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID)
    assert result["reason_codes"] == ["FILESYSTEM_POLICY_INVALID"]


@pytest.mark.parametrize(
    "policy",
    [
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(manifest_max_bytes=0),
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(live_tick_max_bytes=-1),
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(latest_bars_max_bytes=True),
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
            max_manifest_consistency_retries=-1
        ),
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
            max_manifest_consistency_retries=2
        ),
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
            max_manifest_consistency_retries=True
        ),
    ],
)
def test_invalid_filesystem_policy_values_are_blocked(
    tmp_path: Path,
    policy: CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _read(root, bundle, filesystem_policy=policy)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID)
    assert result["reason_codes"] == ["FILESYSTEM_POLICY_INVALID"]


@pytest.mark.parametrize(
    ("now_utc", "read_policy"),
    [
        ("2026-07-10T02:30:05Z", None),
        (NOW_UTC, object()),
    ],
)
def test_invalid_g147_inputs_are_fail_closed(
    tmp_path: Path,
    now_utc: object,
    read_policy: object,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _read(root, bundle, now_utc=now_utc, read_policy=read_policy)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED)
    assert result["reason_codes"] == ["UPSTREAM_VALUE_VALIDATION_BLOCKED"]


def test_reader_does_not_write_delete_rename_or_create_files(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    before = _directory_state(bundle)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert _directory_state(bundle) == before


def test_reader_does_not_mutate_input_policies_or_identity(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    previous_identity = {"bundle_id": "demo-bundle-000000000000", "sequence": 1}
    previous_before = copy.deepcopy(previous_identity)
    read_policy = CanonicalMt4DemoReadonlyBundleV1ReadPolicy()
    filesystem_policy = CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy()

    _read(
        root,
        bundle,
        previous_identity=previous_identity,
        read_policy=read_policy,
        filesystem_policy=filesystem_policy,
    )

    assert previous_identity == previous_before
    assert read_policy == CanonicalMt4DemoReadonlyBundleV1ReadPolicy()
    assert filesystem_policy == CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy()


def test_output_does_not_leak_paths_values_times_or_checksums(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    _set_checksum(
        bundle,
        "live_tick.json",
        hashlib.sha256((bundle / "live_tick.json").read_bytes()).hexdigest(),
    )

    serialized = json.dumps(_read(root, bundle), sort_keys=True)

    assert str(root) not in serialized
    assert str(bundle) not in serialized
    assert "2300.5" not in serialized
    assert "10000.0" not in serialized
    assert "2026-07-10T" not in serialized
    assert hashlib.sha256((bundle / "live_tick.json").read_bytes()).hexdigest() not in serialized
    assert "demo-account-alias-01" not in serialized


def test_unexpected_exception_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    secret_message = f"secret at {bundle} balance=10000"

    def explode(_: Path) -> bytes:
        raise RuntimeError(secret_message)

    monkeypatch.setattr(reader_module, "_read_file_bytes", explode)

    result = _read(root, bundle)
    serialized = json.dumps(result)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE)
    assert result["reason_codes"] == ["FILESYSTEM_READER_EXCEPTION_SANITIZED"]
    assert secret_message not in serialized
    assert str(bundle) not in serialized


def test_unexpected_upstream_exception_is_sanitized_and_scoped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    def explode(**_: object) -> dict[str, Any]:
        raise ValueError(f"upstream secret at {bundle}")

    monkeypatch.setattr(
        reader_module,
        "validate_canonical_mt4_demo_readonly_bundle_v1_values",
        explode,
    )

    result = _read(root, bundle)
    upstream_component = next(
        component
        for component in result["component_statuses"]
        if component["component_name"] == "upstream_value_validation"
    )

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE)
    assert result["reason_codes"] == ["FILESYSTEM_READER_EXCEPTION_SANITIZED"]
    assert upstream_component["reason_codes"] == [
        "FILESYSTEM_READER_EXCEPTION_SANITIZED"
    ]
    assert str(bundle) not in json.dumps(result)


def test_os_read_error_is_safely_classified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    def unreadable(_: Path) -> bytes:
        raise PermissionError("private path must not leak")

    monkeypatch.setattr(reader_module, "_read_file_bytes", unreadable)

    result = _read(root, bundle)

    _assert_blocked(result, CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE)
    assert result["reason_codes"] == ["FILE_UNREADABLE"]
    assert "private path" not in json.dumps(result)


def test_reader_only_reads_five_fixed_canonical_filenames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / "positions_order_history.json").write_text(
        '{"must_not_be_read": true}',
        encoding="utf-8",
    )
    (bundle / ".hidden.json").write_text("not-json", encoding="utf-8")
    (bundle / "live_tick.tmp").write_text("not-json", encoding="utf-8")
    original_reader = reader_module._read_file_bytes
    reads: list[str] = []

    def record(path: Path) -> bytes:
        reads.append(path.name)
        return original_reader(path)

    monkeypatch.setattr(reader_module, "_read_file_bytes", record)

    result = _read(root, bundle)

    assert result["passed"] is True
    assert set(reads) == set(EXAMPLE_FILES)
    assert reads.count("snapshot_manifest.json") == 2
    assert "positions_order_history.json" not in reads
    assert ".hidden.json" not in reads
    assert "live_tick.tmp" not in reads


def test_reader_module_is_isolated_from_api_and_legacy_readers() -> None:
    source = inspect.getsource(reader_module)

    assert "app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator" in source
    assert "app.services.mt4_demo_readonly_reader" not in source
    assert "app.services.mt4_demo_readonly_schema_validator" not in source
    assert "app.services.mt4_demo_readonly_path_guard" not in source
    assert "app.api" not in source
    assert "fastapi" not in source.casefold()
    assert "settings" not in source.casefold()


def _create_bundle(
    tmp_path: Path,
    *,
    root_name: str = "allowed",
) -> tuple[Path, Path]:
    root = tmp_path / root_name
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
    read_policy: object = None,
    filesystem_policy: object = None,
) -> dict[str, Any]:
    return read_and_validate_canonical_mt4_demo_readonly_bundle_v1(
        allowed_root=allowed_root,
        bundle_dir=bundle_dir,
        now_utc=now_utc,
        previous_identity=previous_identity,
        read_policy=read_policy,
        filesystem_policy=filesystem_policy,
    )


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _replace_raw_json_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _set_checksum(bundle: Path, filename: str, digest: str) -> None:
    manifest_path = bundle / "snapshot_manifest.json"
    manifest = _load_json(manifest_path)
    for descriptor in manifest["required_files"]:
        if descriptor["filename"] == filename:
            descriptor["content_sha256"] = digest
    _write_json(manifest_path, manifest)


def _manifest_versions(bundle: Path) -> tuple[bytes, bytes]:
    stable = (bundle / "snapshot_manifest.json").read_bytes()
    changed_data = json.loads(stable.decode("utf-8"))
    changed_data["committed_at_utc"] = "2026-07-10T02:30:02Z"
    changed = json.dumps(changed_data).encode("utf-8")
    return stable, changed


def _directory_state(bundle: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in bundle.iterdir()
        if path.is_file()
    }


def _make_symlink_or_skip(
    link: Path,
    target: Path,
    *,
    target_is_directory: bool,
) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink creation unavailable: {type(exc).__name__}")


def _assert_blocked(result: dict[str, Any], status_code: str) -> None:
    assert result["passed"] is False
    assert result["status_code"] == status_code
    assert result["reader_status"] == "blocked"
    assert result["ready_for_readonly_analysis"] is False
    assert result["next_allowed_stage"] == []
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
