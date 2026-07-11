from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from app.services import (
    demo_readonly_canonical_diagnostics_summary_adapter as adapter,
)
from app.services import (
    demo_readonly_canonical_docs_fixture_diagnostics_summary_producer as producer,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
FIXTURE_BUNDLE_DIR = FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
FIXTURE_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
CANONICAL_FILENAMES = (
    "snapshot_manifest.json",
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
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


def test_public_producer_is_strictly_zero_argument() -> None:
    signature = inspect.signature(
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary
    )

    assert signature.parameters == {}
    assert str(signature.return_annotation) == "dict[str, Any]"


def test_real_producer_returns_exact_safe_g151_ready_summary() -> None:
    before = _fixture_state()

    result = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )

    assert _fixture_state() == before
    _assert_ready_summary(result)


def test_producer_source_is_independent_of_current_working_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPOSITORY_ROOT.parent)

    result = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )

    _assert_ready_summary(result)


def test_producer_calls_g153_once_with_only_fixed_inputs_and_returns_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    sentinel = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )

    def capture_call(**kwargs: object) -> dict[str, Any]:
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(
        producer,
        "build_demo_readonly_canonical_diagnostics_summary",
        capture_call,
    )

    result = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )

    assert result is sentinel
    assert calls == [
        {
            "allowed_root": FIXTURE_ROOT,
            "bundle_dir": FIXTURE_BUNDLE_DIR,
            "now_utc": FIXTURE_REFERENCE_TIME,
        }
    ]


def test_real_missing_fixture_result_remains_safe_blocked_g151_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(producer, "_FIXTURE_BUNDLE_DIR", tmp_path / "missing")

    result = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )

    assert set(result) == OUTPUT_KEYS
    assert result["passed"] is False
    assert result["status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    assert result["next_allowed_stage"] == []
    for field_name, expected in SAFE_FLAGS.items():
        assert result[field_name] is expected
    _assert_forbidden_keys_absent(result)


def test_dependency_exception_returns_fresh_empty_plain_dict_without_leakage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(**_: object) -> dict[str, Any]:
        raise RuntimeError("traceback C:/private/raw_payload/checksum")

    monkeypatch.setattr(
        producer,
        "build_demo_readonly_canonical_diagnostics_summary",
        explode,
    )

    first = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    second = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()

    assert type(first) is dict
    assert type(second) is dict
    assert first == {}
    assert second == {}
    assert first is not second


class _DictSubclass(dict[str, Any]):
    pass


class _StringSubclass(str):
    pass


@pytest.mark.parametrize("invalid_result", [None, [], _DictSubclass()])
def test_non_plain_dict_dependency_results_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    invalid_result: object,
) -> None:
    monkeypatch.setattr(
        producer,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_: invalid_result,
    )

    result = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()

    assert type(result) is dict
    assert result == {}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.pop("status_code"),
        lambda value: value.__setitem__("secret", "raw_payload"),
        lambda value: value.__setitem__("passed", 1),
        lambda value: value.__setitem__("status_code", "UNKNOWN_STATUS"),
        lambda value: value.__setitem__("can_execute", True),
        lambda value: value.__setitem__("passed", False),
        lambda value: value.__setitem__("warning_reasons", ["UNKNOWN_WARNING"]),
        lambda value: value.__setitem__("block_reasons", "NOT_A_LIST"),
        lambda value: value.__setitem__("component_statuses", []),
        lambda value: value["bundle_validation_status"].__setitem__(
            "traceback", "private"
        ),
        lambda value: value["readiness_notes"].__setitem__(
            0, str(FIXTURE_BUNDLE_DIR)
        ),
        lambda value: value["readiness_notes"].__setitem__(
            0, FIXTURE_REFERENCE_TIME.isoformat()
        ),
        lambda value: _set_blocked_status(
            value,
            source_status="CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED",
            block_reason="READER_VALUE_INVALID",
            warning_reasons=[],
        ),
        lambda value: _set_blocked_status(
            value,
            source_status="CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID",
            block_reason="DATA_QUALITY_INPUT_NOT_OBJECT",
            warning_reasons=["IDEMPOTENT_REPEAT"],
        ),
        lambda value: _set_blocked_status(
            value,
            source_status="CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED",
            block_reason="UPSTREAM_WARNINGS_REJECTED_BY_POLICY",
            warning_reasons=[],
        ),
        lambda value: _replace_key(value, "passed"),
        lambda value: _replace_key(value["bundle_validation_status"], "passed"),
        lambda value: _replace_key(
            value["component_statuses"],
            "canonical_data_quality_gate",
        ),
        lambda value: _replace_key(
            value["component_statuses"]["canonical_data_quality_gate"],
            "passed",
        ),
    ],
    ids=(
        "missing-key",
        "extra-secret-key",
        "wrong-bool-type",
        "unknown-summary-status",
        "unsafe-execution-flag",
        "contradictory-passed-status",
        "unknown-warning",
        "wrong-list-type",
        "wrong-component-shape",
        "nested-sensitive-key",
        "path-text",
        "timestamp-text",
        "blocked-status-reason-mismatch",
        "input-invalid-with-warning",
        "rejected-without-warning",
        "top-level-key-subclass",
        "bundle-status-key-subclass",
        "component-container-key-subclass",
        "component-status-key-subclass",
    ),
)
def test_malformed_or_contaminated_dependency_results_fail_closed_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    mutation: Any,
) -> None:
    candidate = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )
    mutation(candidate)
    before = deepcopy(candidate)
    monkeypatch.setattr(
        producer,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_: candidate,
    )

    result = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()

    assert candidate == before
    assert type(result) is dict
    assert result == {}


def test_validation_exception_returns_fresh_empty_dict_without_mutating_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )
    before = deepcopy(candidate)

    def explode(_: object) -> bool:
        raise RuntimeError("private validation exception")

    monkeypatch.setattr(
        producer,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_: candidate,
    )
    monkeypatch.setattr(producer, "_is_safe_summary", explode)

    first = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    second = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()

    assert type(first) is dict
    assert type(second) is dict
    assert first == {}
    assert second == {}
    assert first is not second
    assert candidate == before


def test_safe_dependency_result_is_not_copied_or_rewritten(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safe_result = (
        producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()
    )
    before = deepcopy(safe_result)
    monkeypatch.setattr(
        producer,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_: safe_result,
    )

    result = producer.build_demo_readonly_canonical_docs_fixture_diagnostics_summary()

    assert result is safe_result
    assert safe_result == before


def test_producer_module_has_no_api_configuration_or_execution_dependencies() -> None:
    source = inspect.getsource(producer)
    normalized = source.casefold()

    assert "app.api" not in source
    assert "fastapi" not in normalized
    assert "testclient" not in normalized
    assert "os.environ" not in source
    assert "os.getenv" not in source
    assert "settings" not in normalized
    assert "mt4_data_path" not in normalized
    assert "mt4_diagnostics_legacy_compatibility_adapter" not in source
    assert "read_and_validate_canonical" not in source
    assert "evaluate_canonical_mt4" not in source
    assert "adapt_canonical_data_quality_gate" not in source


def _assert_ready_summary(result: dict[str, Any]) -> None:
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
    for field_name, expected in SAFE_FLAGS.items():
        assert result[field_name] is expected
    _assert_forbidden_keys_absent(result)

    serialized = json.dumps(result, sort_keys=True).casefold()
    assert str(FIXTURE_ROOT).casefold() not in serialized
    assert str(FIXTURE_BUNDLE_DIR).casefold() not in serialized
    assert FIXTURE_REFERENCE_TIME.isoformat().casefold() not in serialized


def _replace_key(value: dict[str, Any], key: str) -> None:
    field_value = value.pop(key)
    value[_StringSubclass(key)] = field_value


def _set_blocked_status(
    value: dict[str, Any],
    *,
    source_status: str,
    block_reason: str,
    warning_reasons: list[str],
) -> None:
    value["passed"] = False
    value["status_code"] = adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    value["block_reasons"] = [block_reason]
    value["warning_reasons"] = list(warning_reasons)
    value["readiness_notes"] = [
        "Canonical DataQualityGate blocked read-only diagnostics adaptation.",
        "Readiness is not trading permission.",
        "This summary is read-only and cannot execute orders.",
    ]
    value["next_allowed_stage"] = []
    value["next_blocked_stage"] = [
        "demo_readonly_diagnostics_response_integration",
        "api_reader_activation",
        "readonly_analysis",
        "execution_chain",
    ]
    for status in (
        value["bundle_validation_status"],
        value["component_statuses"]["canonical_data_quality_gate"],
    ):
        status["passed"] = False
        status["status_code"] = source_status
        status["block_reasons"] = [block_reason]
        status["warning_reasons"] = list(warning_reasons)


def _fixture_state() -> dict[str, tuple[bytes, int]]:
    return {
        filename: (
            (FIXTURE_BUNDLE_DIR / filename).read_bytes(),
            (FIXTURE_BUNDLE_DIR / filename).stat().st_mtime_ns,
        )
        for filename in CANONICAL_FILENAMES
    }


def _assert_forbidden_keys_absent(value: object) -> None:
    if isinstance(value, dict):
        assert {str(key).casefold() for key in value}.isdisjoint(FORBIDDEN_KEYS)
        for child in value.values():
            _assert_forbidden_keys_absent(child)
    elif isinstance(value, list):
        for child in value:
            _assert_forbidden_keys_absent(child)
