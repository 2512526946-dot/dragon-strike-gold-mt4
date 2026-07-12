from __future__ import annotations

import ast
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import inspect
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from app.services import demo_readonly_canonical_diagnostics_pipeline as pipeline
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter
from app.services import (
    demo_readonly_canonical_diagnostics_summary_validator as validator,
)
from app.services import (
    demo_readonly_canonical_docs_fixture_diagnostics_summary_producer as producer,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
FIXTURE_BUNDLE_DIR = FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
SUMMARY_KEYS = frozenset(
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
STATUS_KEYS = frozenset(
    {
        "passed",
        "status_code",
        "block_reasons",
        "warning_reasons",
        "read_only",
        "demo_only",
        "is_tradable",
        "can_execute",
    }
)
SAFETY_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_trading_permission": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
    "allowed_to_modify_risk": False,
}


class _DictSubclass(dict[str, Any]):
    pass


class _ListSubclass(list[str]):
    pass


class _StringSubclass(str):
    pass


def test_public_validator_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(
        validator.is_safe_demo_readonly_canonical_diagnostics_summary
    )

    assert tuple(signature.parameters) == ("canonical_summary",)
    parameter = signature.parameters["canonical_summary"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert str(parameter.annotation) == "object"
    assert str(signature.return_annotation) == "bool"


def test_real_g153_g151_states_are_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _load_json(FIXTURE_BUNDLE_DIR / "snapshot_manifest.json")
    ready = _build_summary()
    warning = _build_summary(
        previous_identity={
            "bundle_id": manifest["bundle_id"],
            "sequence": manifest["sequence"],
        }
    )
    blocked = _build_summary(now_utc=REFERENCE_TIME + timedelta(days=1))
    input_invalid = (
        adapter.adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary(
            data_quality_result=None,
        )
    )

    def explode(_: object) -> object:
        raise RuntimeError("traceback C:/private/raw_payload/checksum")

    monkeypatch.setattr(adapter, "_parse_data_quality_result", explode)
    safe_failure = (
        adapter.adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary(
            data_quality_result={},
        )
    )

    expected = (
        (ready, adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY, ()),
        (
            warning,
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
            ("IDEMPOTENT_REPEAT",),
        ),
        (blocked, adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED, ()),
        (input_invalid, adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID, ()),
        (safe_failure, adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE, ()),
    )
    for summary, status_code, warning_reasons in expected:
        before = deepcopy(summary)
        assert set(summary) == SUMMARY_KEYS
        assert summary["status_code"] == status_code
        assert tuple(summary["warning_reasons"]) == warning_reasons
        assert validator.is_safe_demo_readonly_canonical_diagnostics_summary(
            canonical_summary=summary,
        )
        assert summary == before
        _assert_exact_statuses(summary)
        _assert_safety_flags(summary)


@pytest.mark.parametrize(
    "invalid_summary",
    [None, [], "invalid", 1, True, _DictSubclass()],
)
def test_non_plain_summary_inputs_fail_closed(invalid_summary: object) -> None:
    assert not validator.is_safe_demo_readonly_canonical_diagnostics_summary(
        canonical_summary=invalid_summary,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.pop("status_code"),
        lambda value: value.__setitem__("raw_payload", "private"),
        lambda value: value.__setitem__("passed", 1),
        lambda value: value.__setitem__("status_code", "UNKNOWN_STATUS"),
        lambda value: value.__setitem__(
            "source_scope",
            _StringSubclass(value["source_scope"]),
        ),
        lambda value: value.__setitem__("can_execute", True),
        lambda value: value.__setitem__("block_reasons", _ListSubclass()),
        lambda value: value.__setitem__(
            "warning_reasons",
            ["IDEMPOTENT_REPEAT", "IDEMPOTENT_REPEAT"],
        ),
        lambda value: value.__setitem__(
            "warning_reasons",
            [_StringSubclass("IDEMPOTENT_REPEAT")],
        ),
        lambda value: value.__setitem__("warning_reasons", ["UNKNOWN_WARNING"]),
        lambda value: value.__setitem__(
            "readiness_notes",
            ["C:/private/raw_payload/checksum"],
        ),
        lambda value: value.__setitem__(
            "bundle_validation_status",
            _DictSubclass(value["bundle_validation_status"]),
        ),
        lambda value: value.__setitem__(
            "component_statuses",
            _DictSubclass(value["component_statuses"]),
        ),
        lambda value: value["component_statuses"].__setitem__("extra", {}),
        lambda value: value["component_statuses"].__setitem__(
            "canonical_data_quality_gate",
            _DictSubclass(value["component_statuses"]["canonical_data_quality_gate"]),
        ),
        lambda value: value["bundle_validation_status"].__setitem__(
            "traceback",
            "private",
        ),
        lambda value: value["bundle_validation_status"].__setitem__("passed", False),
        lambda value: value["component_statuses"][
            "canonical_data_quality_gate"
        ].__setitem__(
            "status_code",
            "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED",
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
        "missing-top-level-key",
        "extra-sensitive-key",
        "wrong-bool-type",
        "unknown-summary-status",
        "string-subclass",
        "unsafe-flag",
        "list-subclass",
        "duplicate-warning",
        "warning-item-subclass",
        "unknown-warning",
        "sensitive-readiness-text",
        "bundle-dict-subclass",
        "component-container-subclass",
        "component-container-extra-key",
        "component-status-subclass",
        "nested-extra-key",
        "nested-passed-mismatch",
        "component-status-mismatch",
        "top-level-key-subclass",
        "bundle-key-subclass",
        "component-container-key-subclass",
        "component-status-key-subclass",
    ),
)
def test_malformed_or_contaminated_summaries_fail_closed_without_mutation(
    mutation: Callable[[dict[str, Any]], object],
) -> None:
    candidate = _build_summary()
    mutation(candidate)
    before = deepcopy(candidate)

    assert not validator.is_safe_demo_readonly_canonical_diagnostics_summary(
        canonical_summary=candidate,
    )
    assert candidate == before


@pytest.mark.parametrize(
    ("container", "field", "unsafe_value"),
    [
        ("summary", "read_only", False),
        ("summary", "demo_only", False),
        ("summary", "is_tradable", True),
        ("summary", "can_execute", True),
        ("summary", "is_trading_permission", True),
        ("summary", "is_execution_instruction", True),
        ("summary", "allowed_to_call_ea", True),
        ("summary", "allowed_to_modify_risk", True),
        ("bundle", "read_only", False),
        ("bundle", "demo_only", False),
        ("bundle", "is_tradable", True),
        ("bundle", "can_execute", True),
        ("component", "read_only", False),
        ("component", "demo_only", False),
        ("component", "is_tradable", True),
        ("component", "can_execute", True),
    ],
)
def test_every_unsafe_summary_or_status_flag_fails_closed(
    container: str,
    field: str,
    unsafe_value: bool,
) -> None:
    candidate = _build_summary()
    target = {
        "summary": candidate,
        "bundle": candidate["bundle_validation_status"],
        "component": candidate["component_statuses"][
            "canonical_data_quality_gate"
        ],
    }[container]
    target[field] = unsafe_value

    assert not validator.is_safe_demo_readonly_canonical_diagnostics_summary(
        canonical_summary=candidate,
    )


@pytest.mark.parametrize(
    ("summary_status", "source_status", "block_reason", "warnings"),
    [
        (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
            "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_STALE_BLOCKED",
            "READER_VALUE_INVALID",
            [],
        ),
        (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
            "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_INPUT_INVALID",
            "DATA_QUALITY_INPUT_NOT_OBJECT",
            ["IDEMPOTENT_REPEAT"],
        ),
        (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
            "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_REJECTED",
            "UPSTREAM_WARNINGS_REJECTED_BY_POLICY",
            [],
        ),
        (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID,
            "CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE",
            "CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED",
            [],
        ),
        (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE,
            "CANONICAL_DATA_QUALITY_STATUS_UNAVAILABLE",
            "CANONICAL_DATA_QUALITY_RESULT_INVALID",
            [],
        ),
    ],
)
def test_status_reason_warning_mismatches_fail_closed(
    summary_status: str,
    source_status: str,
    block_reason: str,
    warnings: list[str],
) -> None:
    candidate = _blocked_summary()
    _set_blocked_state(
        candidate,
        summary_status=summary_status,
        source_status=source_status,
        block_reason=block_reason,
        warnings=warnings,
    )

    assert not validator.is_safe_demo_readonly_canonical_diagnostics_summary(
        canonical_summary=candidate,
    )


def test_validation_exception_is_sanitized_and_input_is_immutable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _build_summary()
    before = deepcopy(candidate)

    def explode(**_: object) -> bool:
        raise RuntimeError("traceback C:/private/raw_payload/checksum")

    monkeypatch.setattr(validator, "_state_is_consistent", explode)

    result = validator.is_safe_demo_readonly_canonical_diagnostics_summary(
        canonical_summary=candidate,
    )

    assert result is False
    assert candidate == before


def test_validator_is_pure_and_producer_has_no_duplicate_algorithm() -> None:
    validator_source = inspect.getsource(validator)
    validator_tree = ast.parse(validator_source)
    imports = {
        node.module
        for node in ast.walk(validator_tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(validator_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    normalized = validator_source.casefold()

    assert imports == {"__future__", "re"}
    for forbidden in (
        "pathlib",
        "open(",
        "read_text",
        "read_bytes",
        "os.environ",
        "os.getenv",
        "requests",
        "socket",
        "build_demo_readonly_canonical_diagnostics_summary",
        "read_and_validate_canonical",
        "evaluate_canonical_mt4",
        "adapt_canonical_data_quality_gate",
    ):
        assert forbidden not in normalized

    producer_source = inspect.getsource(producer)
    assert "is_safe_demo_readonly_canonical_diagnostics_summary" in producer_source
    assert "def _parse_status" not in producer_source
    assert "def _state_is_consistent" not in producer_source
    assert "_BLOCKED_STATUS_REASON_CODES" not in producer_source


def _build_summary(
    *,
    now_utc: datetime = REFERENCE_TIME,
    previous_identity: object | None = None,
) -> dict[str, Any]:
    return pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=FIXTURE_ROOT,
        bundle_dir=FIXTURE_BUNDLE_DIR,
        now_utc=now_utc,
        previous_identity=previous_identity,
    )


def _blocked_summary() -> dict[str, Any]:
    return _build_summary(now_utc=REFERENCE_TIME + timedelta(days=1))


def _replace_key(value: dict[str, Any], key: str) -> None:
    field_value = value.pop(key)
    value[_StringSubclass(key)] = field_value


def _set_blocked_state(
    summary: dict[str, Any],
    *,
    summary_status: str,
    source_status: str,
    block_reason: str,
    warnings: list[str],
) -> None:
    summary["status_code"] = summary_status
    summary["block_reasons"] = [block_reason]
    summary["warning_reasons"] = list(warnings)
    for status in (
        summary["bundle_validation_status"],
        summary["component_statuses"]["canonical_data_quality_gate"],
    ):
        status["status_code"] = source_status
        status["block_reasons"] = [block_reason]
        status["warning_reasons"] = list(warnings)


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert type(loaded) is dict
    return loaded


def _assert_exact_statuses(summary: dict[str, Any]) -> None:
    assert type(summary["bundle_validation_status"]) is dict
    assert set(summary["bundle_validation_status"]) == STATUS_KEYS
    assert type(summary["component_statuses"]) is dict
    assert set(summary["component_statuses"]) == {"canonical_data_quality_gate"}
    component = summary["component_statuses"]["canonical_data_quality_gate"]
    assert type(component) is dict
    assert set(component) == STATUS_KEYS
    assert component == summary["bundle_validation_status"]


def _assert_safety_flags(summary: dict[str, Any]) -> None:
    for field, expected in SAFETY_FLAGS.items():
        assert summary[field] is expected
