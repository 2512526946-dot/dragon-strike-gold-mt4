from __future__ import annotations

import copy
import inspect
import json
from typing import Any

import pytest

from app.schemas.mt4_diagnostics import Mt4DiagnosticsResponse
from app.services import data_quality_gate as gate
from app.services import (
    demo_readonly_canonical_diagnostics_summary_adapter as canonical_summary,
)
from app.services import mt4_diagnostics_legacy_compatibility_adapter as adapter


EXPECTED_KEYS = set(Mt4DiagnosticsResponse.model_fields)
DETAIL_KEYS = {
    "read_summary",
    "metadata_status",
    "freshness_status",
    "gate_v0_result",
    "required_fields_status",
    "field_types_status",
    "numeric_ranges_status",
    "cross_field_status",
    "gate_v1_result",
}
FORBIDDEN_KEYS = {
    "allow_trade",
    "base_dir",
    "bridge_dir",
    "candidate_path",
    "can_execute",
    "can_trade",
    "checksum",
    "checksum_checked",
    "checksum_passed",
    "ea_command",
    "order",
    "raw_payload",
    "signal",
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "suggested_lot",
    "traceback",
    "trading_action",
}
FORBIDDEN_TEXT = {
    "must-not-leak",
    "raw payload",
    "checksum",
    "traceback",
    "bridge_dir",
    "candidate_path",
    "source_reader_status_code",
    "source_upstream_value_status_code",
}


def test_ready_summary_maps_to_exact_readonly_legacy_response() -> None:
    source = _summary_fixture()

    result = _adapt(source)

    assert set(result) == EXPECTED_KEYS
    assert result["stage"] == "mt4_diagnostics_v1"
    assert result["status_code"] == gate.DATA_QUALITY_PASSED
    assert result["data_quality_passed"] is True
    assert result["can_proceed_to_read_only_analysis"] is True
    _assert_safe_legacy_response(result)


def test_ready_with_warnings_preserves_only_allowlisted_warning_summary() -> None:
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
        source_status_code=(
            gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
        ),
        warning_reasons=["IDEMPOTENT_REPEAT"],
    )

    result = _adapt(source)

    assert result["data_quality_passed"] is True
    assert result["can_proceed_to_read_only_analysis"] is True
    assert result["gate_v1_result"]["warning_reasons"] == ["IDEMPOTENT_REPEAT"]
    _assert_safe_legacy_response(result)


def test_blocked_summary_fails_closed() -> None:
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        source_status_code=gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
        block_reasons=[gate.READER_DATA_STALE],
    )

    result = _adapt(source)

    _assert_blocked(result)


@pytest.mark.parametrize(
    ("status_code", "block_reason"),
    [
        (
            canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID,
            "CANONICAL_DATA_QUALITY_RESULT_INVALID",
        ),
        (
            canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE,
            "CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED",
        ),
    ],
)
def test_input_invalid_and_safe_failure_remain_blocked(
    status_code: str,
    block_reason: str,
) -> None:
    source = _summary_fixture(
        status_code=status_code,
        source_status_code="CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE",
        block_reasons=[block_reason],
    )

    result = _adapt(source)

    _assert_blocked(result)


@pytest.mark.parametrize("invalid_input", [None, [], "invalid", 1, True])
def test_non_dict_input_fails_closed(invalid_input: object) -> None:
    _assert_blocked(_adapt(invalid_input))


def test_dict_subclass_fails_closed() -> None:
    class DictSubclass(dict[str, Any]):
        pass

    _assert_blocked(_adapt(DictSubclass(_summary_fixture())))


@pytest.mark.parametrize("mutation", ["missing", "extra", "wrong_type"])
def test_exact_summary_envelope_is_required(mutation: str) -> None:
    source = _summary_fixture()
    if mutation == "missing":
        source.pop("fixture_source")
    elif mutation == "extra":
        source["raw_payload"] = "must-not-leak"
    else:
        source["passed"] = 1

    result = _adapt(source)

    _assert_blocked(result)
    _assert_no_forbidden_output(result)


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("source_scope", "unexpected_scope"),
        ("validation_stage", 1),
        ("fixture_source", "unexpected_fixture"),
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
def test_fixed_identity_and_safety_fields_are_required(
    field: str,
    unsafe_value: object,
) -> None:
    source = _summary_fixture()
    source[field] = unsafe_value

    _assert_invalid_envelope(_adapt(source))


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("block_reasons", ()),
        ("warning_reasons", [1]),
        ("readiness_notes", ["duplicate", "duplicate"]),
        ("next_allowed_stage", "demo_readonly_diagnostics_response_integration"),
        ("next_blocked_stage", [True]),
    ],
)
def test_summary_string_lists_require_strict_unique_list_values(
    field: str,
    unsafe_value: object,
) -> None:
    source = _summary_fixture()
    source[field] = unsafe_value

    _assert_invalid_envelope(_adapt(source))


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("status_code", "UNKNOWN"),
        ("passed", False),
        ("block_reasons", [gate.READER_DATA_STALE]),
        ("warning_reasons", ["UNKNOWN_WARNING"]),
        ("readiness_notes", ["must-not-leak"]),
        ("next_allowed_stage", []),
        ("next_blocked_stage", ["execution_chain"]),
        ("is_tradable", True),
        ("can_execute", True),
    ],
)
def test_unknown_or_contradictory_summary_fails_closed(
    field: str,
    unsafe_value: object,
) -> None:
    source = _summary_fixture()
    source[field] = unsafe_value
    _synchronize_nested_status(source)

    result = _adapt(source)

    _assert_blocked(result)
    _assert_no_forbidden_output(result)


def test_source_status_and_reason_must_match() -> None:
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        source_status_code=gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED,
        block_reasons=[gate.READER_VALUE_INVALID],
    )

    _assert_blocked(_adapt(source))


def test_rejected_summary_preserves_only_allowlisted_warning() -> None:
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        source_status_code=gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
        block_reasons=[gate.UPSTREAM_WARNINGS_REJECTED_BY_POLICY],
        warning_reasons=["SEQUENCE_GAP"],
    )

    result = _adapt(source)

    _assert_blocked(result)
    assert result["gate_v1_result"]["warning_reasons"] == ["SEQUENCE_GAP"]


def test_rejected_summary_without_warning_fails_closed() -> None:
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        source_status_code=gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED,
        block_reasons=[gate.UPSTREAM_WARNINGS_REJECTED_BY_POLICY],
    )

    result = _adapt(source)

    _assert_blocked(result)
    assert result["gate_v1_result"]["warning_reasons"] == []


@pytest.mark.parametrize(
    "source_status_code",
    [
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID,
        gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_POLICY_INVALID,
    ],
)
def test_input_and_policy_blocked_statuses_reject_warnings(
    source_status_code: str,
) -> None:
    reason = (
        gate.DATA_QUALITY_INPUT_NOT_OBJECT
        if source_status_code
        == gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID
        else gate.DATA_QUALITY_POLICY_INVALID
    )
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        source_status_code=source_status_code,
        block_reasons=[reason],
        warning_reasons=["IDEMPOTENT_REPEAT"],
    )

    result = _adapt(source)

    _assert_blocked(result)
    assert result["gate_v1_result"]["warning_reasons"] == []


def test_nested_statuses_must_be_exact_and_equal() -> None:
    source = _summary_fixture()
    source["component_statuses"]["canonical_data_quality_gate"]["passed"] = False

    _assert_blocked(_adapt(source))


@pytest.mark.parametrize("location", ["bundle", "component"])
@pytest.mark.parametrize(
    "mutation",
    [
        "dict_subclass",
        "missing_key",
        "extra_key",
        "passed_type",
        "status_type",
        "list_container_type",
        "list_item_type",
        "duplicate_list_value",
        "unsafe_flag",
    ],
)
def test_nested_status_requires_exact_strict_safe_envelope(
    location: str,
    mutation: str,
) -> None:
    class DictSubclass(dict[str, Any]):
        pass

    source = _summary_fixture()
    parent = (
        source
        if location == "bundle"
        else source["component_statuses"]
    )
    key = (
        "bundle_validation_status"
        if location == "bundle"
        else "canonical_data_quality_gate"
    )
    status = parent[key]

    if mutation == "dict_subclass":
        parent[key] = DictSubclass(status)
    elif mutation == "missing_key":
        status.pop("status_code")
    elif mutation == "extra_key":
        status["secret"] = "must-not-leak"
    elif mutation == "passed_type":
        status["passed"] = 1
    elif mutation == "status_type":
        status["status_code"] = 1
    elif mutation == "list_container_type":
        status["block_reasons"] = ()
    elif mutation == "list_item_type":
        status["warning_reasons"] = [1]
    elif mutation == "duplicate_list_value":
        status["warning_reasons"] = [
            "IDEMPOTENT_REPEAT",
            "IDEMPOTENT_REPEAT",
        ]
    else:
        status["demo_only"] = False

    _assert_invalid_envelope(_adapt(source))


@pytest.mark.parametrize(
    "mutation",
    ["dict_subclass", "wrong_type", "missing_component", "extra_component"],
)
def test_component_statuses_requires_exact_plain_dict_shape(mutation: str) -> None:
    class DictSubclass(dict[str, Any]):
        pass

    source = _summary_fixture()
    component_statuses = source["component_statuses"]
    if mutation == "dict_subclass":
        source["component_statuses"] = DictSubclass(component_statuses)
    elif mutation == "wrong_type":
        source["component_statuses"] = []
    elif mutation == "missing_component":
        source["component_statuses"] = {}
    else:
        component_statuses["secret"] = {"passed": True}

    _assert_invalid_envelope(_adapt(source))


def test_unknown_nested_source_status_fails_closed() -> None:
    source = _summary_fixture()
    for status in (
        source["bundle_validation_status"],
        source["component_statuses"]["canonical_data_quality_gate"],
    ):
        status["status_code"] = "UNKNOWN_CANONICAL_DATA_QUALITY_STATUS"

    _assert_invalid_envelope(_adapt(source))


@pytest.mark.parametrize(
    "sensitive_key",
    [
        "raw_payload",
        "base_dir",
        "candidate_path",
        "checksum",
        "traceback",
        "source_reader_status_code",
        "source_upstream_value_status_code",
    ],
)
def test_sensitive_extra_key_and_text_are_sanitized(sensitive_key: str) -> None:
    source = _summary_fixture()
    source[sensitive_key] = "must-not-leak"

    result = _adapt(source)

    _assert_blocked(result)
    _assert_no_forbidden_output(result)


def test_sensitive_nested_key_is_sanitized() -> None:
    source = _summary_fixture()
    source["bundle_validation_status"]["raw_payload"] = "must-not-leak"

    result = _adapt(source)

    _assert_blocked(result)
    _assert_no_forbidden_output(result)


def test_unavailable_legacy_details_never_claim_success() -> None:
    result = _adapt(_summary_fixture())

    for key in DETAIL_KEYS:
        detail = result[key]
        assert detail["available"] is False
        assert detail["status"] == "unavailable"
        assert detail["passed"] is False


def test_input_is_not_mutated() -> None:
    source = _summary_fixture(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
        source_status_code=(
            gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS
        ),
        warning_reasons=["SEQUENCE_GAP"],
    )
    before = copy.deepcopy(source)

    _adapt(source)

    assert source == before


def test_unexpected_exception_is_sanitized(monkeypatch) -> None:
    def raise_unexpected(_value: object) -> None:
        raise RuntimeError("must-not-leak")

    monkeypatch.setattr(adapter, "_parse_summary", raise_unexpected)

    result = _adapt(_summary_fixture())

    _assert_blocked(result)
    _assert_no_forbidden_output(result)


def test_production_adapter_has_no_runtime_io_or_pipeline_calls() -> None:
    source = inspect.getsource(adapter)

    for forbidden in (
        "app.api",
        "TestClient",
        "open(",
        "Path(",
        "os.environ",
        "os.getenv",
        "read_and_validate_canonical",
        "evaluate_canonical",
        "build_demo_readonly_canonical",
        "adapt_canonical_data_quality_gate",
    ):
        assert forbidden not in source


def _summary_fixture(
    *,
    status_code: str = canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
    source_status_code: str = gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    block_reasons: list[str] | None = None,
    warning_reasons: list[str] | None = None,
) -> dict[str, Any]:
    blocks = list(block_reasons or [])
    warnings = list(warning_reasons or [])
    passed = status_code in {
        canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
        canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
    }
    safe_status = {
        "passed": passed,
        "status_code": source_status_code,
        "block_reasons": list(blocks),
        "warning_reasons": list(warnings),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
    return {
        "passed": passed,
        "status_code": status_code,
        "source_scope": canonical_summary.SOURCE_SCOPE,
        "validation_stage": canonical_summary.VALIDATION_STAGE,
        "fixture_source": canonical_summary.FIXTURE_SOURCE,
        "bundle_validation_status": copy.deepcopy(safe_status),
        "component_statuses": {
            "canonical_data_quality_gate": copy.deepcopy(safe_status)
        },
        "block_reasons": list(blocks),
        "warning_reasons": list(warnings),
        "readiness_notes": [
            (
                "Canonical DataQualityGate passed for read-only diagnostics adaptation."
                if passed
                else "Canonical DataQualityGate blocked read-only diagnostics adaptation."
            ),
            "Readiness is not trading permission.",
            "This summary is read-only and cannot execute orders.",
        ],
        "next_allowed_stage": (
            ["demo_readonly_diagnostics_response_integration"] if passed else []
        ),
        "next_blocked_stage": (
            ["api_reader_activation", "execution_chain"]
            if passed
            else [
                "demo_readonly_diagnostics_response_integration",
                "api_reader_activation",
                "readonly_analysis",
                "execution_chain",
            ]
        ),
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }


def _synchronize_nested_status(source: dict[str, Any]) -> None:
    for status in (
        source["bundle_validation_status"],
        source["component_statuses"]["canonical_data_quality_gate"],
    ):
        status["passed"] = source["passed"]
        status["block_reasons"] = copy.deepcopy(source["block_reasons"])
        status["warning_reasons"] = copy.deepcopy(source["warning_reasons"])


def _adapt(source: object) -> dict[str, Any]:
    return adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=source
    )


def _assert_blocked(result: dict[str, Any]) -> None:
    assert set(result) == EXPECTED_KEYS
    assert result["status_code"] == gate.BLOCKED_BY_GATE_V0
    assert result["data_quality_passed"] is False
    assert result["can_proceed_to_read_only_analysis"] is False
    assert result["is_tradable"] is False
    Mt4DiagnosticsResponse.model_validate(result)
    _assert_safe_legacy_response(result)


def _assert_invalid_envelope(result: dict[str, Any]) -> None:
    _assert_blocked(result)
    assert result["gate_v1_result"]["warning_reasons"] == []
    _assert_no_forbidden_output(result)


def _assert_safe_legacy_response(result: dict[str, Any]) -> None:
    assert result["is_tradable"] is False
    assert "Diagnostics are read-only." in result["note"]
    assert "Diagnostics are not trading permission." in result["note"]
    assert "Diagnostics do not generate trading signals." in result["note"]
    assert not (_collect_keys(result) & FORBIDDEN_KEYS)
    _assert_no_forbidden_output(result)


def _assert_no_forbidden_output(result: dict[str, Any]) -> None:
    serialized = json.dumps(result, ensure_ascii=False).casefold()
    for forbidden in FORBIDDEN_TEXT:
        assert forbidden.casefold() not in serialized


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()
