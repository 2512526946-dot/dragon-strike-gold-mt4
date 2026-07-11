from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from app.services import demo_readonly_canonical_diagnostics_pipeline as pipeline
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
)
from app.services.data_quality_gate import (
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy,
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
SAFE_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}
FORBIDDEN_KEYS = {
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


def test_real_canonical_chain_returns_exact_ready_summary(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _build(root, bundle)

    assert set(result) == OUTPUT_KEYS
    assert result["passed"] is True
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
    assert result["warning_reasons"] == []
    assert result["next_allowed_stage"] == [
        "demo_readonly_diagnostics_response_integration"
    ]
    _assert_safe(result)


def test_real_canonical_warning_chain_preserves_allowed_warning(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = _load_json(bundle / "snapshot_manifest.json")

    result = _build(
        root,
        bundle,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        },
    )

    assert result["passed"] is True
    assert result["status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
    )
    assert result["warning_reasons"] == ["IDEMPOTENT_REPEAT"]
    _assert_safe(result)


def test_real_stale_chain_is_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)

    result = _build(root, bundle, now_utc=NOW_UTC + timedelta(days=1))

    assert result["passed"] is False
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    assert result["bundle_validation_status"]["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED
    )
    assert result["next_allowed_stage"] == []
    _assert_safe(result)


def test_real_missing_file_chain_is_reader_blocked(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    (bundle / "live_tick.json").unlink()

    result = _build(root, bundle)

    assert result["passed"] is False
    assert result["bundle_validation_status"]["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED
    )
    _assert_safe(result)


def test_warning_policy_rejection_is_preserved(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = _load_json(bundle / "snapshot_manifest.json")

    result = _build(
        root,
        bundle,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        },
        data_quality_policy=CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy(
            allow_upstream_warnings=False
        ),
    )

    assert result["passed"] is False
    assert result["bundle_validation_status"]["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED
    )
    assert result["warning_reasons"] == ["IDEMPOTENT_REPEAT"]
    _assert_safe(result)


def test_reader_dependency_exception_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    def raise_reader(**_kwargs: object) -> dict[str, Any]:
        raise RuntimeError("private reader detail")

    monkeypatch.setattr(
        pipeline.filesystem_reader,
        "read_and_validate_canonical_mt4_demo_readonly_bundle_v1",
        raise_reader,
    )

    result = _build(root, bundle)

    assert result["passed"] is False
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    assert "private reader detail" not in json.dumps(result)
    _assert_safe(result)


def test_gate_dependency_exception_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)

    def raise_gate(**_kwargs: object) -> dict[str, Any]:
        raise RuntimeError("private gate detail")

    monkeypatch.setattr(
        pipeline.data_quality_gate,
        "evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate",
        raise_gate,
    )

    result = _build(root, bundle)

    assert result["passed"] is False
    assert result["status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID
    )
    assert "private gate detail" not in json.dumps(result)
    _assert_safe(result)


def test_pipeline_calls_real_layers_in_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    calls: list[str] = []
    real_reader = (
        pipeline.filesystem_reader.read_and_validate_canonical_mt4_demo_readonly_bundle_v1
    )
    real_gate = (
        pipeline.data_quality_gate.evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate
    )
    real_adapter = (
        pipeline.adapter.adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary
    )

    def read_wrapper(**kwargs: object) -> dict[str, Any]:
        calls.append("reader")
        return real_reader(**kwargs)

    def gate_wrapper(**kwargs: object) -> dict[str, Any]:
        calls.append("gate")
        return real_gate(**kwargs)

    def adapter_wrapper(**kwargs: object) -> dict[str, Any]:
        calls.append("adapter")
        return real_adapter(**kwargs)

    monkeypatch.setattr(
        pipeline.filesystem_reader,
        "read_and_validate_canonical_mt4_demo_readonly_bundle_v1",
        read_wrapper,
    )
    monkeypatch.setattr(
        pipeline.data_quality_gate,
        "evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate",
        gate_wrapper,
    )
    monkeypatch.setattr(
        pipeline.adapter,
        "adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary",
        adapter_wrapper,
    )

    result = _build(root, bundle)

    assert result["passed"] is True
    assert calls == ["reader", "gate", "adapter"]


def test_pipeline_does_not_mutate_inputs(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    previous_identity = {"bundle_id": "different", "sequence": 0}
    read_policy = CanonicalMt4DemoReadonlyBundleV1ReadPolicy()
    filesystem_policy = CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy()
    data_quality_policy = CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy()
    originals = copy.deepcopy(
        (previous_identity, read_policy, filesystem_policy, data_quality_policy)
    )

    _build(
        root,
        bundle,
        previous_identity=previous_identity,
        read_policy=read_policy,
        filesystem_policy=filesystem_policy,
        data_quality_policy=data_quality_policy,
    )

    assert (previous_identity, read_policy, filesystem_policy, data_quality_policy) == (
        originals
    )


def test_pipeline_is_not_api_or_activation_code() -> None:
    source = inspect.getsource(pipeline)

    assert "app.api" not in source
    assert "fastapi" not in source.casefold()
    assert "demo_readonly_diagnostics_response(" not in source
    assert "mt4_demo_readonly_source_summary_from_dir" not in source
    assert "os.environ" not in source
    assert "data/" not in source


def _create_bundle(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "allowed"
    bundle = root / "bundle"
    bundle.mkdir(parents=True)
    for target_name, example_name in EXAMPLE_FILES.items():
        (bundle / target_name).write_bytes((EXAMPLE_DIR / example_name).read_bytes())
    return root, bundle


def _build(
    allowed_root: object,
    bundle_dir: object,
    *,
    now_utc: object = NOW_UTC,
    previous_identity: object | None = None,
    read_policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy | None = None,
    filesystem_policy: CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy | None = None,
    data_quality_policy: CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy | None = None,
) -> dict[str, Any]:
    return pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=allowed_root,
        bundle_dir=bundle_dir,
        now_utc=now_utc,
        previous_identity=previous_identity,
        read_policy=read_policy,
        filesystem_policy=filesystem_policy,
        data_quality_policy=data_quality_policy,
    )


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _assert_safe(result: dict[str, Any]) -> None:
    assert set(result) == OUTPUT_KEYS
    for field_name, expected in SAFE_FLAGS.items():
        assert result[field_name] is expected
    _assert_forbidden_keys_absent(result)


def _assert_forbidden_keys_absent(value: Any) -> None:
    if isinstance(value, dict):
        assert {str(key).casefold() for key in value}.isdisjoint(FORBIDDEN_KEYS)
        for child in value.values():
            _assert_forbidden_keys_absent(child)
    elif isinstance(value, list):
        for child in value:
            _assert_forbidden_keys_absent(child)
