from __future__ import annotations

from datetime import UTC, datetime
import inspect
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api.demo_readonly as demo_readonly_api
from app.main import app
from app.schemas.demo_readonly_diagnostics import (
    DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
    DEMO_READONLY_INTERNAL_ERROR,
)
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter
from app.services import mt4_demo_readonly_reader as legacy_reader
from app.services.data_quality_gate import (
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED,
    CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED,
    READER_BLOCKED,
)


MT4_SOURCE_MODE = "mt4_demo_readonly_file_bridge_enabled"
SAFE_BRIDGE_DIR = "mt4_demo_readonly_bridge"

EXPECTED_TOP_LEVEL_KEYS = {
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
FORBIDDEN_TEXT = {
    "raw_payload",
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "checksum_checked",
    "checksum_passed",
    "bridge_dir",
    "base_dir",
    "candidate_path",
    "traceback",
    "private pipeline detail",
    "can_trade",
    "allow_trade",
    "should_buy",
    "should_sell",
    "suggested_lot",
}


def test_default_docs_fixture_does_not_call_pipeline_or_legacy_reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_no_reader_calls(monkeypatch)

    response = TestClient(app).get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["reader_status"] == "not_called"
    assert data["reader_passed"] is False
    _assert_safe_response(data)


def test_client_input_cannot_activate_canonical_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_no_reader_calls(monkeypatch)
    client = TestClient(app)
    client.cookies.update(
        {"source_mode": MT4_SOURCE_MODE, "bridge_dir": "client-path"}
    )

    response = client.request(
        "GET",
        DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        params={"source_mode": MT4_SOURCE_MODE, "bridge_dir": "client-path"},
        headers={"X-Source-Mode": MT4_SOURCE_MODE, "X-Bridge-Dir": "client-path"},
        json={
            "source_mode": MT4_SOURCE_MODE,
            "bridge_dir": "client-path",
            "raw_payload": {"secret": "client-secret"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source_mode"] == "docs_fixture_only"
    assert data["reader_status"] == "not_called"
    _assert_safe_response(data)


def test_server_config_guard_delegates_only_server_derived_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_pipeline(**kwargs: object) -> dict[str, Any]:
        calls.append(kwargs)
        return _safe_canonical_summary(passed=True)

    _install_server_config(monkeypatch)
    _install_legacy_reader_guard(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        fake_pipeline,
    )
    client = TestClient(app)
    client.cookies.update({"bridge_dir": "client-cookie-path"})

    response = client.request(
        "GET",
        DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        params={"bridge_dir": "client-query-path"},
        headers={"X-Bridge-Dir": "client-header-path"},
        json={"bridge_dir": "client-body-path"},
    )

    assert response.status_code == 200
    _assert_pipeline_call(calls)
    data = response.json()
    assert data["source_mode"] == MT4_SOURCE_MODE
    assert data["reader_status"] == "ready"
    assert data["reader_status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
    _assert_safe_response(data)


def test_blocked_server_config_does_not_call_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_no_reader_calls(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "_get_demo_readonly_server_source_config",
        lambda: {
            "source_mode": MT4_SOURCE_MODE,
            "mt4_demo_readonly_file_bridge_enabled": False,
            "mt4_demo_readonly_bridge_dir": SAFE_BRIDGE_DIR,
            "allow_request_override": False,
        },
    )

    response = TestClient(app).get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["source_config_passed"] is False
    assert data["reader_passed"] is False
    _assert_safe_response(data)


def test_blocked_pipeline_summary_is_safely_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_server_config(monkeypatch)
    _install_legacy_reader_guard(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **_kwargs: _safe_canonical_summary(passed=False),
    )

    response = TestClient(app).get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert data["reader_status"] == "blocked"
    assert data["reader_status_code"] == adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
    _assert_safe_response(data)


def test_pipeline_exception_returns_sanitized_internal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_pipeline(**_kwargs: object) -> dict[str, Any]:
        raise RuntimeError("private pipeline detail")

    _install_server_config(monkeypatch)
    _install_legacy_reader_guard(monkeypatch)
    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        raising_pipeline,
    )

    response = TestClient(app).get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 500
    data = response.json()
    assert data["passed"] is False
    assert data["status_code"] == DEMO_READONLY_INTERNAL_ERROR
    _assert_safe_response(data)


def test_api_source_has_no_legacy_reader_or_external_config_activation() -> None:
    source = inspect.getsource(demo_readonly_api)

    assert "read_mt4_demo_readonly_source_summary_from_dir" not in source
    assert "os.environ" not in source
    assert "dotenv" not in source.casefold()
    assert "configparser" not in source.casefold()


def _install_server_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        demo_readonly_api,
        "_get_demo_readonly_server_source_config",
        lambda: {
            "source_mode": MT4_SOURCE_MODE,
            "mt4_demo_readonly_file_bridge_enabled": True,
            "mt4_demo_readonly_bridge_dir": SAFE_BRIDGE_DIR,
            "allow_request_override": False,
        },
    )


def _install_no_reader_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("reader and canonical pipeline must remain disabled")

    monkeypatch.setattr(
        demo_readonly_api,
        "build_demo_readonly_canonical_diagnostics_summary",
        fail_if_called,
    )
    _install_legacy_reader_guard(monkeypatch)


def _install_legacy_reader_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("legacy reader must not be called")

    monkeypatch.setattr(
        legacy_reader,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_if_called,
        raising=False,
    )


def _safe_canonical_summary(*, passed: bool) -> dict[str, Any]:
    source_status_code = (
        CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED
        if passed
        else CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_READER_BLOCKED
    )
    block_reasons = [] if passed else [READER_BLOCKED]
    status = {
        "passed": passed,
        "status_code": source_status_code,
        "block_reasons": list(block_reasons),
        "warning_reasons": [],
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
    }
    return {
        "passed": passed,
        "status_code": (
            adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
            if passed
            else adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED
        ),
        "source_scope": adapter.SOURCE_SCOPE,
        "validation_stage": adapter.VALIDATION_STAGE,
        "fixture_source": adapter.FIXTURE_SOURCE,
        "bundle_validation_status": dict(status),
        "component_statuses": {"canonical_data_quality_gate": dict(status)},
        "block_reasons": list(block_reasons),
        "warning_reasons": [],
        "readiness_notes": [
            "Canonical diagnostics summary is read-only.",
            "Readiness is not trading permission.",
            "This summary cannot execute orders.",
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


def _assert_pipeline_call(calls: list[dict[str, object]]) -> None:
    assert len(calls) == 1
    call = calls[0]
    assert set(call) == {"allowed_root", "bundle_dir", "now_utc"}
    assert call["allowed_root"] == Path(SAFE_BRIDGE_DIR).parent
    assert call["bundle_dir"] == Path(SAFE_BRIDGE_DIR)
    assert isinstance(call["now_utc"], datetime)
    assert call["now_utc"].tzinfo is UTC


def _assert_safe_response(data: dict[str, Any]) -> None:
    assert set(data) == EXPECTED_TOP_LEVEL_KEYS
    for field_name, expected in SAFE_FLAGS.items():
        assert data[field_name] is expected
    serialized = json.dumps(data, ensure_ascii=True).casefold()
    for marker in FORBIDDEN_TEXT:
        assert marker.casefold() not in serialized
