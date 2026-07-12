"""Contract and integration tests for the legacy diagnostics API boundary.

The default route uses the checked-in canonical docs fixture only. Canonical
reader activation and real MT4 access remain outside this boundary.
"""

from __future__ import annotations

from dataclasses import asdict
import copy
import inspect
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api.mt4 as legacy_api
from app.main import app
from app.schemas.mt4_diagnostics import Mt4DiagnosticsResponse
from app.services import data_quality_gate as gate
from app.services import demo_readonly_docs_fixture_validation_summary as docs_summary
from app.services import (
    demo_readonly_canonical_diagnostics_summary_adapter as canonical_summary,
)
from app.services import mt4_demo_readonly_source_config_guard as source_guard
from app.services import mt4_diagnostics_legacy_compatibility_adapter as legacy_adapter


LEGACY_RESPONSE_KEYS = frozenset(Mt4DiagnosticsResponse.model_fields)
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
FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
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
)
FORBIDDEN_OUTPUT_TEXT = frozenset(
    {
        "raw_payload",
        "checksum",
        "traceback",
        "bridge_dir",
        "candidate_path",
        "source_reader_status_code",
        "source_upstream_value_status_code",
        "OrderSend",
        "OrderClose",
        "OrderModify",
        "OrderDelete",
    }
)


def test_server_side_empty_config_defaults_to_docs_fixture_only() -> None:
    result = source_guard.validate_demo_readonly_source_config({})

    assert result["passed"] is True
    assert (
        result["status_code"]
        == source_guard.MT4_DEMO_READONLY_SOURCE_CONFIG_DEFAULT_READY
    )
    assert result["selected_source_mode"] == source_guard.DOCS_FIXTURE_ONLY_SOURCE_MODE
    assert result["default_source_mode"] == source_guard.DOCS_FIXTURE_ONLY_SOURCE_MODE
    assert result["request_override_allowed"] is False
    assert result["block_reasons"] == []
    for field, expected in SAFE_FLAGS.items():
        assert result[field] is expected


def test_client_surfaces_cannot_change_server_source_authority() -> None:
    server_config: dict[str, object] = {}
    before = copy.deepcopy(server_config)
    client_surfaces = {
        "query": {"source_mode": "mt4_demo_readonly_file_bridge_enabled"},
        "header": {"X-Source-Mode": "mt4_demo_readonly_file_bridge_enabled"},
        "body": {"bridge_dir": "client-supplied-location"},
        "cookie": {"candidate_path": "client-supplied-location"},
        "frontend_state": {"base_dir": "client-supplied-location"},
    }

    result = source_guard.validate_demo_readonly_source_config(server_config)

    assert server_config == before == {}
    assert result["selected_source_mode"] == source_guard.DOCS_FIXTURE_ONLY_SOURCE_MODE
    assert result["request_override_allowed"] is False
    assert all(key not in server_config for surface in client_surfaces.values() for key in surface)


def test_existing_docs_fixture_summary_is_not_g151_summary() -> None:
    docs = _docs_fixture_summary()
    docs_fields = frozenset(docs.__dataclass_fields__)

    assert len(G151_SUMMARY_KEYS) == 20
    assert docs_fields != G151_SUMMARY_KEYS
    assert frozenset(asdict(docs)) != G151_SUMMARY_KEYS
    assert docs.source_scope == docs_summary.SOURCE_SCOPE
    assert docs.validation_stage == docs_summary.VALIDATION_STAGE
    assert docs.source_scope != canonical_summary.SOURCE_SCOPE
    assert docs.validation_stage != canonical_summary.VALIDATION_STAGE


def test_docs_summary_cannot_enter_g158_as_canonical_summary() -> None:
    result = legacy_adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=_docs_fixture_summary()
    )

    _assert_fixed_blocked_legacy_response(result)


@pytest.mark.parametrize(
    "summary_factory",
    [
        lambda: _g151_summary(),
        lambda: _g151_summary(
            status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
            source_status_code=gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
            warning_reasons=["IDEMPOTENT_REPEAT"],
        ),
    ],
)
def test_only_genuine_g151_summary_can_produce_readonly_success(summary_factory) -> None:
    summary = summary_factory()

    assert set(summary) == G151_SUMMARY_KEYS
    result = legacy_adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=summary
    )

    assert set(result) == LEGACY_RESPONSE_KEYS
    assert result["data_quality_passed"] is True
    assert result["can_proceed_to_read_only_analysis"] is True
    assert result["is_tradable"] is False
    _assert_legacy_shape_and_safety(result)


@pytest.mark.parametrize("case", ["invalid", "blocked", "unknown", "missing", "extra", "contradictory"])
def test_invalid_or_blocked_summary_is_fixed_legacy_blocked(case: str) -> None:
    summary: object
    if case == "invalid":
        summary = object()
    else:
        summary = _g151_summary(passed=False)
        if case == "unknown":
            summary["status_code"] = "UNKNOWN_CANONICAL_DIAGNOSTICS_STATUS"
        elif case == "missing":
            summary.pop("fixture_source")
        elif case == "extra":
            summary["unexpected_secret"] = "must-not-leak"
        elif case == "contradictory":
            summary["passed"] = True

    result = legacy_adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=summary
    )

    _assert_fixed_blocked_legacy_response(result)


def test_blocked_source_config_cannot_become_a_g158_success_input() -> None:
    blocked_config = {
        "source_mode": source_guard.MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
        "mt4_demo_readonly_file_bridge_enabled": False,
        "mt4_demo_readonly_bridge_dir": "server-owned-approved-location",
        "allow_request_override": False,
    }
    guard_result = source_guard.validate_demo_readonly_source_config(blocked_config)

    assert guard_result["passed"] is False
    assert guard_result["selected_source_mode"] == (
        source_guard.MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE
    )
    result = legacy_adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=guard_result
    )

    _assert_fixed_blocked_legacy_response(result)
    assert result["gate_v1_result"]["warning_reasons"] == []


def test_legacy_output_has_no_trading_permission_or_sensitive_fields() -> None:
    contaminated = _g151_summary()
    contaminated["raw_payload"] = {
        "bridge_dir": "must-not-leak",
        "checksum": "must-not-leak",
        "traceback": "must-not-leak",
        "source_reader_status_code": "must-not-leak",
    }

    result = legacy_adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=contaminated
    )

    _assert_fixed_blocked_legacy_response(result)
    assert result["is_tradable"] is False
    assert "can_execute" not in result
    assert "is_trading_permission" not in result
    assert "source_reader_status_code" not in json.dumps(result)


def test_input_summary_is_not_mutated() -> None:
    summary = _g151_summary(
        status_code=canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
        source_status_code=gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED_WITH_WARNINGS,
        warning_reasons=["SEQUENCE_GAP"],
    )
    before = copy.deepcopy(summary)

    legacy_adapter.adapt_canonical_summary_to_legacy_mt4_diagnostics_response(
        canonical_summary=summary
    )

    assert summary == before


def test_default_endpoint_uses_real_g153_g151_and_g158_chain_once(
    monkeypatch,
) -> None:
    real_guard = legacy_api.validate_demo_readonly_source_config
    real_producer = (
        legacy_api.build_demo_readonly_canonical_docs_fixture_diagnostics_summary
    )
    real_adapter = (
        legacy_api.adapt_canonical_summary_to_legacy_mt4_diagnostics_response
    )
    calls: dict[str, int] = {"guard": 0, "producer": 0, "adapter": 0}
    captured: dict[str, object] = {}

    def guard_spy(config: object) -> dict[str, Any]:
        calls["guard"] += 1
        captured["config"] = copy.deepcopy(config)
        return real_guard(config)

    def producer_spy() -> dict[str, Any]:
        calls["producer"] += 1
        result = real_producer()
        captured["summary"] = result
        return result

    def adapter_spy(*, canonical_summary: object) -> dict[str, Any]:
        calls["adapter"] += 1
        assert canonical_summary is captured["summary"]
        return real_adapter(canonical_summary=canonical_summary)

    monkeypatch.setattr(
        legacy_api,
        "validate_demo_readonly_source_config",
        guard_spy,
    )
    monkeypatch.setattr(
        legacy_api,
        "build_demo_readonly_canonical_docs_fixture_diagnostics_summary",
        producer_spy,
    )
    monkeypatch.setattr(
        legacy_api,
        "adapt_canonical_summary_to_legacy_mt4_diagnostics_response",
        adapter_spy,
    )

    response = TestClient(app).get("/api/mt4/diagnostics")
    data = response.json()
    source = inspect.getsource(legacy_api)

    assert response.status_code == 200
    assert calls == {"guard": 1, "producer": 1, "adapter": 1}
    assert captured["config"] == {}
    assert set(captured["summary"]) == G151_SUMMARY_KEYS
    assert captured["summary"]["passed"] is True
    assert set(data) == LEGACY_RESPONSE_KEYS
    assert data["data_quality_passed"] is True
    assert data["can_proceed_to_read_only_analysis"] is True
    assert data["is_tradable"] is False
    assert "build_mt4_diagnostics" not in source
    assert "get_settings" not in source
    assert "mt4_data_path" not in source
    _assert_legacy_shape_and_safety(data)


def _docs_fixture_summary() -> docs_summary.DemoReadOnlyDocsFixtureValidationSummary:
    safe_status = {
        "passed": True,
        "status_code": docs_summary.SUMMARY_READY,
        "block_reasons": [],
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
    return docs_summary.DemoReadOnlyDocsFixtureValidationSummary(
        passed=True,
        status_code=docs_summary.SUMMARY_READY,
        source_scope=docs_summary.SOURCE_SCOPE,
        validation_stage=docs_summary.VALIDATION_STAGE,
        fixture_source=docs_summary.FIXTURE_SOURCE_NOTE,
        bundle_validation_status=copy.deepcopy(safe_status),
        component_statuses={},
        block_reasons=[],
        warning_reasons=[],
        readiness_notes=list(docs_summary.READINESS_NOTES),
        next_allowed_stage=list(docs_summary.NEXT_ALLOWED_STAGE),
        next_blocked_stage=list(docs_summary.NEXT_BLOCKED_STAGE),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _g151_summary(
    *,
    passed: bool = True,
    status_code: str = canonical_summary.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
    source_status_code: str = gate.CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    block_reasons: list[str] | None = None,
    warning_reasons: list[str] | None = None,
) -> dict[str, Any]:
    blocks = list(block_reasons or ([] if passed else [gate.READER_DATA_STALE]))
    warnings = list(warning_reasons or [])
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
        **SAFE_FLAGS,
    }


def _assert_fixed_blocked_legacy_response(result: dict[str, Any]) -> None:
    assert set(result) == LEGACY_RESPONSE_KEYS
    assert result["stage"] == legacy_adapter.LEGACY_STAGE
    assert result["status_code"] == gate.BLOCKED_BY_GATE_V0
    assert result["data_quality_passed"] is False
    assert result["can_proceed_to_read_only_analysis"] is False
    assert result["is_tradable"] is False
    assert result["gate_v1_result"]["warning_reasons"] == []
    _assert_legacy_shape_and_safety(result)


def _assert_legacy_shape_and_safety(result: dict[str, Any]) -> None:
    assert len(LEGACY_RESPONSE_KEYS) == 15
    assert result["is_tradable"] is False
    assert "Diagnostics are read-only." in result["note"]
    assert "Diagnostics are not trading permission." in result["note"]
    assert "Diagnostics do not generate trading signals." in result["note"]
    assert not (_collect_keys(result) & FORBIDDEN_OUTPUT_KEYS)
    serialized = json.dumps(result, ensure_ascii=False).casefold()
    assert all(marker.casefold() not in serialized for marker in FORBIDDEN_OUTPUT_TEXT)
    Mt4DiagnosticsResponse.model_validate(result)


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
