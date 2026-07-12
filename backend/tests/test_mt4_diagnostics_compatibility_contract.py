from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from fastapi.testclient import TestClient

import app.api.mt4 as mt4_api
from app.main import app
from app.schemas.mt4_diagnostics import Mt4DiagnosticsResponse
from app.services import mt4_diagnostics as old_diagnostics
from app.services.data_quality_gate import DATA_QUALITY_PASSED


EXPECTED_RESPONSE_KEYS = frozenset(Mt4DiagnosticsResponse.model_fields)
UNAVAILABLE_DETAIL_KEYS = frozenset({"available", "status", "passed"})
FORBIDDEN_RESPONSE_KEYS = frozenset(
    {
        "account_number",
        "allow_trade",
        "base_dir",
        "bridge_dir",
        "candidate_path",
        "can_execute",
        "can_trade",
        "checksum",
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
FORBIDDEN_RESPONSE_TEXT = (
    "raw_payload",
    "checksum",
    "traceback",
    "bridge_dir",
    "candidate_path",
    "source_reader_status_code",
    "source_upstream_value_status_code",
)
DETAIL_FIELDS = (
    "read_summary",
    "metadata_status",
    "freshness_status",
    "gate_v0_result",
    "required_fields_status",
    "field_types_status",
    "numeric_ranges_status",
    "cross_field_status",
)


def test_legacy_endpoint_preserves_exact_read_only_response_contract() -> None:
    data = _get_diagnostics()

    assert set(data) == EXPECTED_RESPONSE_KEYS
    assert len(EXPECTED_RESPONSE_KEYS) == 15
    assert data["stage"] == "mt4_diagnostics_v1"
    assert data["status_code"] == DATA_QUALITY_PASSED
    assert data["data_quality_passed"] is True
    assert data["can_proceed_to_read_only_analysis"] is True
    assert data["is_tradable"] is False
    assert "Diagnostics are read-only." in data["note"]
    assert "Diagnostics are not trading permission." in data["note"]
    assert "Diagnostics do not generate trading signals." in data["note"]
    _assert_safe_response(data)


def test_unavailable_legacy_details_are_not_fabricated_as_success() -> None:
    data = _get_diagnostics()

    for field in DETAIL_FIELDS:
        assert set(data[field]) == UNAVAILABLE_DETAIL_KEYS
        assert data[field] == {
            "available": False,
            "status": "unavailable",
            "passed": False,
        }
    assert data["gate_v1_result"] == {
        "available": False,
        "status": "unavailable",
        "passed": False,
        "warning_reasons": [],
    }


def test_client_inputs_do_not_change_source_or_safety_semantics() -> None:
    client = TestClient(app)
    baseline = client.get("/api/mt4/diagnostics")
    client.cookies.update(
        {
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "bridge_dir": "client-cookie-location",
        }
    )
    injected = client.request(
        "GET",
        "/api/mt4/diagnostics",
        params={
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "bridge_dir": "client-query-location",
            "base_dir": "client-base-location",
            "candidate_path": "client-candidate-location",
        },
        headers={
            "X-Source-Mode": "mt4_demo_readonly_file_bridge_enabled",
            "X-Bridge-Dir": "client-header-location",
        },
        json={
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "bridge_dir": "client-body-location",
            "raw_payload": {"password": "client-secret"},
        },
    )

    assert baseline.status_code == injected.status_code == 200
    assert baseline.json() == injected.json()
    assert set(injected.json()) == EXPECTED_RESPONSE_KEYS
    _assert_safe_response(injected.json())


def test_legacy_endpoint_never_calls_old_diagnostics_chain(monkeypatch) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("legacy diagnostics chain must remain disconnected")

    monkeypatch.setattr(old_diagnostics, "build_mt4_diagnostics", fail_if_called)

    data = _get_diagnostics()
    source = inspect.getsource(mt4_api)
    tree = ast.parse(source)
    schema_imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.schemas.mt4_diagnostics"
        for alias in node.names
    }

    assert data["data_quality_passed"] is True
    assert "build_mt4_diagnostics" not in source
    assert "mt4_diagnostics_response" not in schema_imports
    assert "get_settings" not in source
    assert "mt4_data_path" not in source
    _assert_safe_response(data)


def test_legacy_endpoint_has_no_runtime_source_or_reader_configuration() -> None:
    source = inspect.getsource(mt4_api)

    assert "validate_demo_readonly_source_config({})" in source
    assert "os.environ" not in source
    assert "os.getenv" not in source
    assert "MT4_DATA_DIR" not in source
    assert "data/mt4" not in source.replace("\\", "/")
    assert "MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE" not in source
    assert "build_demo_readonly_canonical_diagnostics_summary" not in source


def _get_diagnostics() -> dict[str, Any]:
    response = TestClient(app).get("/api/mt4/diagnostics")
    assert response.status_code == 200
    return response.json()


def _assert_safe_response(data: dict[str, Any]) -> None:
    assert not (_collect_keys(data) & FORBIDDEN_RESPONSE_KEYS)
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    assert all(marker not in serialized for marker in FORBIDDEN_RESPONSE_TEXT)


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
