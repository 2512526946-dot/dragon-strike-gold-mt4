from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from app.schemas import demo_readonly_diagnostics as response_schema
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    read_and_validate_canonical_mt4_demo_readonly_bundle_v1,
)
from app.services.data_quality_gate import (
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy,
    evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate,
)
from app.services.demo_readonly_docs_fixture_validation_summary import (
    summarize_demo_readonly_docs_fixture_validation,
)
from app.services.mt4_demo_readonly_source_config_guard import (
    MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
    validate_demo_readonly_source_config,
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
SAFE_BRIDGE_DIR = "mt4_demo_readonly_bridge"

RESPONSE_KEYS = {
    "api_version",
    "endpoint",
    "generated_at",
    "passed",
    "status_code",
    "source_scope",
    "source_mode",
    "source_status",
    "source_config_status_code",
    "source_config_passed",
    "reader_status",
    "reader_passed",
    "reader_status_code",
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
FORBIDDEN_OUTPUT_KEYS = {
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "raw_payload",
    "path",
    "traceback",
    "checksum_checked",
    "checksum_passed",
    "bridge_dir",
    "candidate_path",
    "password",
    "secret",
    "token",
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


def test_canonical_scope_contract_matches_g151_adapter() -> None:
    assert adapter.SOURCE_SCOPE == (
        response_schema.CANONICAL_MT4_DEMO_READONLY_DATA_QUALITY_SOURCE_SCOPE
    )


def test_blocked_status_reason_contract_matches_g151_adapter() -> None:
    assert response_schema._CANONICAL_DATA_QUALITY_BLOCKED_REASON_CODES == (
        adapter._BLOCKED_STATUS_REASON_CODES
    )


def test_real_canonical_success_maps_to_ready_response(tmp_path: Path) -> None:
    data_quality_result, summary = _real_summary(tmp_path)
    source_config = _reader_source_config_result()

    result = _render(summary, source_config)

    assert data_quality_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
    )
    assert set(result) == RESPONSE_KEYS
    assert result["passed"] is True
    assert result["status_code"] == response_schema.DEMO_READONLY_DIAGNOSTICS_READY
    assert result["source_scope"] == adapter.SOURCE_SCOPE
    assert result["source_mode"] == MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE
    assert result["source_config_passed"] is True
    assert result["reader_status"] == response_schema.READER_STATUS_READY
    assert result["reader_passed"] is True
    assert result["reader_status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
    assert result["validation_stage"] == adapter.VALIDATION_STAGE
    assert result["warning_reasons"] == []
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


def test_real_canonical_warning_maps_to_ready_with_warning_response(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    manifest = _load_json(bundle / "snapshot_manifest.json")
    reader_result = _read(
        root,
        bundle,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        },
    )
    data_quality_result = _evaluate(reader_result)
    summary = _adapt(data_quality_result)

    result = _render(summary, _reader_source_config_result())

    assert data_quality_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
    )
    assert result["passed"] is True
    assert result["reader_status"] == response_schema.READER_STATUS_READY
    assert result["reader_passed"] is True
    assert result["reader_status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
    )
    assert result["warning_reasons"] == ["IDEMPOTENT_REPEAT"]
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


def test_real_canonical_stale_result_maps_to_blocked_response(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    reader_result = _read(root, bundle, now_utc=NOW_UTC + timedelta(days=1))
    data_quality_result = _evaluate(reader_result)
    summary = _adapt(data_quality_result)

    result = _render(summary, _reader_source_config_result())

    assert data_quality_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED
    )
    assert result["passed"] is False
    assert result["status_code"] == response_schema.DEMO_READONLY_DIAGNOSTICS_BLOCKED
    assert result["reader_status"] == response_schema.READER_STATUS_BLOCKED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    )
    assert result["next_allowed_stage"] == []
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


def test_canonical_summary_with_docs_source_config_fails_closed(
    tmp_path: Path,
) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)

    result = _render(summary, validate_demo_readonly_source_config({}))

    assert result["passed"] is False
    assert result["status_code"] == (
        response_schema.DEMO_READONLY_SAFETY_FIELD_VIOLATION
    )
    assert result["reader_status"] == response_schema.READER_STATUS_NOT_CALLED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        response_schema.READER_STATUS_CODE_NOT_CALLED
    )
    assert response_schema.SUMMARY_SOURCE_CONFIG_MISMATCH_REASON in result[
        "block_reasons"
    ]
    _assert_fixed_safety(result)


def test_docs_summary_with_reader_source_config_fails_closed() -> None:
    docs_summary = summarize_demo_readonly_docs_fixture_validation()

    result = _render(docs_summary, _reader_source_config_result())

    assert result["passed"] is False
    assert result["status_code"] == (
        response_schema.DEMO_READONLY_SAFETY_FIELD_VIOLATION
    )
    assert result["reader_status"] == response_schema.READER_STATUS_BLOCKED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        response_schema.READER_STATUS_CODE_UNAVAILABLE
    )
    assert response_schema.SUMMARY_SOURCE_CONFIG_MISMATCH_REASON in result[
        "block_reasons"
    ]
    _assert_fixed_safety(result)


def test_default_docs_summary_behavior_is_unchanged() -> None:
    docs_summary = summarize_demo_readonly_docs_fixture_validation()

    result = _render(docs_summary, validate_demo_readonly_source_config({}))

    assert result["passed"] is True
    assert result["status_code"] == response_schema.DEMO_READONLY_DIAGNOSTICS_READY
    assert result["source_scope"] == response_schema.SOURCE_SCOPE
    assert result["source_mode"] == response_schema.SOURCE_SCOPE
    assert result["reader_status"] == response_schema.READER_STATUS_NOT_CALLED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        response_schema.READER_STATUS_CODE_NOT_CALLED
    )
    _assert_fixed_safety(result)


def test_polluted_canonical_summary_is_sanitized_and_safety_blocked(
    tmp_path: Path,
) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)
    summary["secret"] = "must-not-leak"

    result = _render(summary, _reader_source_config_result())

    assert result["passed"] is False
    assert result["status_code"] == (
        response_schema.DEMO_READONLY_SAFETY_FIELD_VIOLATION
    )
    assert result["reader_status"] == response_schema.READER_STATUS_SAFETY_BLOCKED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        response_schema.READER_STATUS_CODE_SAFETY_BLOCKED
    )
    assert "must-not-leak" not in json.dumps(result)
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


@pytest.mark.parametrize(
    "updates",
    [
        {"status_code": adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED},
        {"passed": False},
        {"status_code": "CANONICAL_DIAGNOSTICS_SUMMARY_UNKNOWN"},
        {
            "status_code": (
                adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
            )
        },
        {"warning_reasons": ["IDEMPOTENT_REPEAT"]},
        {"block_reasons": ["READER_DATA_STALE"]},
    ],
)
def test_real_canonical_success_with_inconsistent_envelope_fails_closed(
    tmp_path: Path,
    updates: dict[str, Any],
) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)
    summary.update(copy.deepcopy(updates))

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert response_schema.CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON in result[
        "block_reasons"
    ]
    _assert_fixed_safety(result)


def test_real_canonical_blocked_summary_without_reason_fails_closed(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    summary = _adapt(
        _evaluate(_read(root, bundle, now_utc=NOW_UTC + timedelta(days=1)))
    )
    summary["block_reasons"] = []

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert response_schema.CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON in result[
        "block_reasons"
    ]


def test_real_stale_summary_with_wrong_reason_fails_closed(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    summary = _adapt(
        _evaluate(_read(root, bundle, now_utc=NOW_UTC + timedelta(days=1)))
    )
    _set_summary_block_reasons(summary, ["READER_STRUCTURE_INVALID"])

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert response_schema.CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON in result[
        "block_reasons"
    ]


def test_real_rejected_summary_without_warning_fails_closed(
    tmp_path: Path,
) -> None:
    summary = _real_rejected_warning_summary(tmp_path)
    _set_summary_warning_reasons(summary, [])

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert response_schema.CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON in result[
        "block_reasons"
    ]


def test_real_rejected_summary_with_warning_remains_blocked_not_invalid(
    tmp_path: Path,
) -> None:
    summary = _real_rejected_warning_summary(tmp_path)

    result = _render(summary, _reader_source_config_result())

    assert result["passed"] is False
    assert result["status_code"] == response_schema.DEMO_READONLY_DIAGNOSTICS_BLOCKED
    assert result["reader_status"] == response_schema.READER_STATUS_BLOCKED
    assert result["warning_reasons"] == ["IDEMPOTENT_REPEAT"]
    _assert_fixed_safety(result)


@pytest.mark.parametrize("blocked_kind", ["input", "policy"])
def test_blocked_status_that_forbids_warning_fails_closed(
    tmp_path: Path,
    blocked_kind: str,
) -> None:
    if blocked_kind == "input":
        data_quality_result = _evaluate({"unexpected": "reader envelope"})
    else:
        root, bundle = _create_bundle(tmp_path)
        data_quality_result = (
            evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate(
                reader_result=_read(root, bundle),
                policy=object(),  # type: ignore[arg-type]
            )
        )
    summary = _adapt(data_quality_result)
    _set_summary_warning_reasons(summary, ["IDEMPOTENT_REPEAT"])

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert response_schema.CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON in result[
        "block_reasons"
    ]


def test_real_canonical_summary_with_unknown_nested_status_fails_closed(
    tmp_path: Path,
) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)
    unknown_status = "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_UNKNOWN"
    summary["bundle_validation_status"]["status_code"] = unknown_status
    summary["component_statuses"]["canonical_data_quality_gate"][
        "status_code"
    ] = unknown_status

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert response_schema.CANONICAL_SUMMARY_ENVELOPE_INVALID_REASON in result[
        "block_reasons"
    ]


def test_real_adapter_input_invalid_summary_maps_to_blocked_response() -> None:
    summary = _adapt({"unexpected": "value"})

    result = _render(summary, _reader_source_config_result())

    assert summary["status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID
    )
    assert result["passed"] is False
    assert result["status_code"] == response_schema.DEMO_READONLY_DIAGNOSTICS_BLOCKED
    assert result["reader_status"] == response_schema.READER_STATUS_BLOCKED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID
    )


def test_real_adapter_safe_failure_summary_maps_to_blocked_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_safely(_value: object) -> None:
        raise RuntimeError("must be sanitized")

    monkeypatch.setattr(adapter, "_parse_data_quality_result", fail_safely)
    summary = _adapt({})

    result = _render(summary, _reader_source_config_result())

    assert summary["status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE
    )
    assert result["passed"] is False
    assert result["status_code"] == response_schema.DEMO_READONLY_DIAGNOSTICS_BLOCKED
    assert result["reader_status"] == response_schema.READER_STATUS_BLOCKED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE
    )


def test_checksum_key_pollution_is_safety_blocked(tmp_path: Path) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)
    summary["checksum_checked"] = True

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert "checksum" not in json.dumps(result).casefold()
    _assert_no_forbidden_output(result)


def test_checksum_text_pollution_is_redacted_and_safety_blocked(
    tmp_path: Path,
) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)
    summary["readiness_notes"] = ["checksum detail must remain private"]

    result = _render(summary, _reader_source_config_result())

    _assert_reader_safety_blocked(result)
    assert "checksum" not in json.dumps(result).casefold()
    _assert_no_forbidden_output(result)


def test_summary_and_source_config_inputs_are_not_mutated(tmp_path: Path) -> None:
    _data_quality_result, summary = _real_summary(tmp_path)
    source_config = _reader_source_config_result()
    summary_before = copy.deepcopy(summary)
    source_config_before = copy.deepcopy(source_config)

    _render(summary, source_config)

    assert summary == summary_before
    assert source_config == source_config_before


def test_response_integration_is_pure_memory_and_does_not_call_api_or_reader() -> None:
    source = inspect.getsource(response_schema)

    assert "read_and_validate_canonical_mt4_demo_readonly_bundle_v1(" not in source
    assert "Path(" not in source
    assert "open(" not in source
    assert "app.api" not in source
    assert "fastapi" not in source.casefold()
    assert "os.environ" not in source


def _real_summary(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root, bundle = _create_bundle(tmp_path)
    data_quality_result = _evaluate(_read(root, bundle))
    return data_quality_result, _adapt(data_quality_result)


def _real_rejected_warning_summary(tmp_path: Path) -> dict[str, Any]:
    root, bundle = _create_bundle(tmp_path)
    manifest = _load_json(bundle / "snapshot_manifest.json")
    reader_result = _read(
        root,
        bundle,
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        },
    )
    return _adapt(
        _evaluate(
            reader_result,
            policy=CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy(
                allow_upstream_warnings=False
            ),
        )
    )


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
) -> dict[str, Any]:
    return read_and_validate_canonical_mt4_demo_readonly_bundle_v1(
        allowed_root=allowed_root,
        bundle_dir=bundle_dir,
        now_utc=now_utc,
        previous_identity=previous_identity,
    )


def _evaluate(
    reader_result: object,
    *,
    policy: CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy | None = None,
) -> dict[str, Any]:
    return evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate(
        reader_result=reader_result,
        policy=policy,
    )


def _adapt(data_quality_result: object) -> dict[str, Any]:
    return (
        adapter.adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary(
            data_quality_result=data_quality_result,
        )
    )


def _reader_source_config_result() -> dict[str, Any]:
    return validate_demo_readonly_source_config(
        {
            "source_mode": MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
            "mt4_demo_readonly_file_bridge_enabled": True,
            "mt4_demo_readonly_bridge_dir": SAFE_BRIDGE_DIR,
            "allow_request_override": False,
        }
    )


def _render(summary: object, source_config: object) -> dict[str, Any]:
    return response_schema.demo_readonly_diagnostics_response(
        summary,
        source_config_guard_result=source_config,
    ).model_dump()


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _assert_fixed_safety(result: dict[str, Any]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False


def _assert_reader_safety_blocked(result: dict[str, Any]) -> None:
    assert result["passed"] is False
    assert result["status_code"] == (
        response_schema.DEMO_READONLY_SAFETY_FIELD_VIOLATION
    )
    assert result["reader_status"] == response_schema.READER_STATUS_SAFETY_BLOCKED
    assert result["reader_passed"] is False
    assert result["reader_status_code"] == (
        response_schema.READER_STATUS_CODE_SAFETY_BLOCKED
    )


def _set_summary_block_reasons(
    summary: dict[str, Any],
    block_reasons: list[str],
) -> None:
    summary["block_reasons"] = list(block_reasons)
    summary["bundle_validation_status"]["block_reasons"] = list(block_reasons)
    summary["component_statuses"]["canonical_data_quality_gate"][
        "block_reasons"
    ] = list(block_reasons)


def _set_summary_warning_reasons(
    summary: dict[str, Any],
    warning_reasons: list[str],
) -> None:
    summary["warning_reasons"] = list(warning_reasons)
    summary["bundle_validation_status"]["warning_reasons"] = list(
        warning_reasons
    )
    summary["component_statuses"]["canonical_data_quality_gate"][
        "warning_reasons"
    ] = list(warning_reasons)


def _assert_no_forbidden_output(result: dict[str, Any]) -> None:
    assert not _contains_forbidden_key(result)


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key.casefold() in FORBIDDEN_OUTPUT_KEYS or _contains_forbidden_key(child)
            for key, child in value.items()
            if isinstance(key, str)
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
