from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    read_and_validate_canonical_mt4_demo_readonly_bundle_v1,
)
from app.services.data_quality_gate import (
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
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
STATUS_KEYS = {
    "passed",
    "status_code",
    "block_reasons",
    "warning_reasons",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
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


def test_real_g148_and_g149_success_adapts_to_exact_safe_summary(
    tmp_path: Path,
) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)

    result = _adapt(data_quality_result)

    assert data_quality_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
    )
    assert set(result) == OUTPUT_KEYS
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
    _assert_statuses(result, expected_source_status=data_quality_result["status_code"])
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


def test_real_g148_warning_and_real_g149_warning_are_safely_propagated(
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

    result = _adapt(data_quality_result)

    assert data_quality_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
    )
    assert result["passed"] is True
    assert result["status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS
    )
    assert result["warning_reasons"] == ["IDEMPOTENT_REPEAT"]
    _assert_statuses(result, expected_source_status=data_quality_result["status_code"])
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


def test_real_g148_stale_result_and_real_g149_block_are_preserved(
    tmp_path: Path,
) -> None:
    root, bundle = _create_bundle(tmp_path)
    reader_result = _read(root, bundle, now_utc=NOW_UTC + timedelta(days=1))
    data_quality_result = _evaluate(reader_result)

    result = _adapt(data_quality_result)

    assert data_quality_result["status_code"] == (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED
    )
    assert result["passed"] is False
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    assert result["block_reasons"] == data_quality_result["reason_codes"]
    assert result["next_allowed_stage"] == []
    assert result["next_blocked_stage"] == [
        "demo_readonly_diagnostics_response_integration",
        "api_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    _assert_statuses(result, expected_source_status=data_quality_result["status_code"])
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


@pytest.mark.parametrize("invalid_input", [None, [], "invalid", 1, True])
def test_non_dict_input_fails_closed(invalid_input: object) -> None:
    result = _adapt(invalid_input)

    _assert_input_invalid(result)


def test_dict_subclass_fails_closed(tmp_path: Path) -> None:
    class DictSubclass(dict[str, Any]):
        pass

    data_quality_result = _real_data_quality_result(tmp_path)

    result = _adapt(DictSubclass(data_quality_result))

    _assert_input_invalid(result)


@pytest.mark.parametrize("mutation", ["missing", "extra", "wrong_type"])
def test_exact_input_envelope_is_required(tmp_path: Path, mutation: str) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)
    if mutation == "missing":
        data_quality_result.pop("contract_version")
    elif mutation == "extra":
        data_quality_result["secret"] = "must-not-leak"
    else:
        data_quality_result["passed"] = 1

    result = _adapt(data_quality_result)

    _assert_input_invalid(result)
    _assert_no_forbidden_output(result)


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("read_only", False),
        ("demo_only", False),
        ("is_tradable", True),
        ("can_execute", True),
        ("is_trading_permission", True),
        ("is_execution_instruction", True),
        ("allowed_to_call_ea", True),
        ("allowed_to_modify_risk", True),
    ],
)
def test_unsafe_data_quality_flags_fail_closed(
    tmp_path: Path,
    field: str,
    unsafe_value: bool,
) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)
    data_quality_result[field] = unsafe_value

    result = _adapt(data_quality_result)

    _assert_input_invalid(result)
    _assert_fixed_safety(result)


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("status_code", "UNKNOWN_DATA_QUALITY_STATUS"),
        ("source_reader_status_code", "UNKNOWN_READER_STATUS"),
        ("source_upstream_value_status_code", "UNKNOWN_VALUE_STATUS"),
        ("warning_codes", ["UNKNOWN_WARNING"]),
        ("reason_codes", ["UNKNOWN_REASON"]),
    ],
)
def test_unknown_codes_fail_closed(
    tmp_path: Path,
    field: str,
    unsafe_value: object,
) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)
    data_quality_result[field] = unsafe_value

    _assert_input_invalid(_adapt(data_quality_result))


def test_blocked_status_and_reason_must_match(tmp_path: Path) -> None:
    root, bundle = _create_bundle(tmp_path)
    data_quality_result = _evaluate(
        _read(root, bundle, now_utc=NOW_UTC + timedelta(days=1))
    )
    data_quality_result["reason_codes"] = ["READER_VALUE_INVALID"]

    _assert_input_invalid(_adapt(data_quality_result))


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("passed", False),
        ("reader_status", "blocked"),
        ("data_quality_status", "blocked"),
        ("reason_codes", ["READER_BLOCKED"]),
        ("ready_for_readonly_analysis", False),
        ("next_allowed_stage", []),
        ("next_blocked_stage", ["execution_chain"]),
    ],
)
def test_inconsistent_success_envelope_fails_closed(
    tmp_path: Path,
    field: str,
    unsafe_value: object,
) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)
    data_quality_result[field] = unsafe_value

    _assert_input_invalid(_adapt(data_quality_result))


def test_adapter_does_not_mutate_input(tmp_path: Path) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)
    before = copy.deepcopy(data_quality_result)

    _adapt(data_quality_result)

    assert data_quality_result == before


def test_unexpected_adapter_exception_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_safely(_: object) -> None:
        raise RuntimeError("sensitive exception text")

    monkeypatch.setattr(adapter, "_parse_data_quality_result", raise_safely)

    result = _adapt({})

    assert result["passed"] is False
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE
    assert result["block_reasons"] == [
        "CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED"
    ]
    assert "sensitive exception text" not in json.dumps(result)
    _assert_fixed_safety(result)
    _assert_no_forbidden_output(result)


def test_output_drops_internal_source_statuses_and_sensitive_input(
    tmp_path: Path,
) -> None:
    data_quality_result = _real_data_quality_result(tmp_path)
    data_quality_result["secret"] = "must-not-leak"

    result = _adapt(data_quality_result)

    serialized = json.dumps(result)
    assert "must-not-leak" not in serialized
    assert "source_reader_status_code" not in serialized
    assert "source_upstream_value_status_code" not in serialized
    _assert_no_forbidden_output(result)


def test_adapter_is_pure_memory_and_does_not_call_reader_or_api() -> None:
    source = inspect.getsource(adapter)

    assert "read_and_validate_canonical_mt4_demo_readonly_bundle_v1(" not in source
    assert "Path(" not in source
    assert "open(" not in source
    assert "app.api" not in source
    assert "fastapi" not in source.casefold()
    assert "os.environ" not in source


def _assert_input_invalid(result: dict[str, Any]) -> None:
    assert set(result) == OUTPUT_KEYS
    assert result["passed"] is False
    assert result["status_code"] == (
        adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID
    )
    assert result["block_reasons"] == ["CANONICAL_DATA_QUALITY_RESULT_INVALID"]
    assert result["warning_reasons"] == []
    _assert_statuses(
        result,
        expected_source_status="CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE",
    )
    _assert_fixed_safety(result)


def _assert_statuses(
    result: dict[str, Any],
    *,
    expected_source_status: str,
) -> None:
    assert set(result["bundle_validation_status"]) == STATUS_KEYS
    assert set(result["component_statuses"]) == {"canonical_data_quality_gate"}
    component = result["component_statuses"]["canonical_data_quality_gate"]
    assert set(component) == STATUS_KEYS
    assert result["bundle_validation_status"]["status_code"] == (
        expected_source_status
    )
    assert component == result["bundle_validation_status"]


def _assert_fixed_safety(result: dict[str, Any]) -> None:
    assert result["read_only"] is True
    assert result["demo_only"] is True
    assert result["is_tradable"] is False
    assert result["can_execute"] is False
    assert result["is_trading_permission"] is False
    assert result["is_execution_instruction"] is False
    assert result["allowed_to_call_ea"] is False
    assert result["allowed_to_modify_risk"] is False
    for status in (
        result["bundle_validation_status"],
        result["component_statuses"]["canonical_data_quality_gate"],
    ):
        assert status["read_only"] is True
        assert status["demo_only"] is True
        assert status["is_tradable"] is False
        assert status["can_execute"] is False


def _assert_no_forbidden_output(result: dict[str, Any]) -> None:
    assert not _contains_forbidden_key(result)


def _contains_forbidden_key(value_to_check: object) -> bool:
    if isinstance(value_to_check, dict):
        return any(
            key.casefold() in FORBIDDEN_OUTPUT_KEYS
            or _contains_forbidden_key(child)
            for key, child in value_to_check.items()
            if isinstance(key, str)
        )
    if isinstance(value_to_check, list):
        return any(_contains_forbidden_key(item) for item in value_to_check)
    return False


def _real_data_quality_result(tmp_path: Path) -> dict[str, Any]:
    root, bundle = _create_bundle(tmp_path)
    return _evaluate(_read(root, bundle))


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


def _evaluate(reader_result: object) -> dict[str, Any]:
    return evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate(
        reader_result=reader_result,
    )


def _adapt(data_quality_result: object) -> dict[str, Any]:
    return adapter.adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary(
        data_quality_result=data_quality_result,
    )


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded
