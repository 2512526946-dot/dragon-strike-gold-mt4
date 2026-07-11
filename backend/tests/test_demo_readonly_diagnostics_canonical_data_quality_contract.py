from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api.demo_readonly as demo_readonly_api
from app.main import app
from app.schemas.demo_readonly_diagnostics import (
    DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
)
from app.services import data_quality_gate, mt4_demo_readonly_reader


MT4_SOURCE_MODE = "mt4_demo_readonly_file_bridge_enabled"
CANONICAL_GATE_FIELD = "canonical_data_quality_gate"

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

FORBIDDEN_RESPONSE_KEYS = {
    "raw_payload",
    "path",
    "relative_path",
    "resolved_path",
    "system_path",
    "traceback",
    "stack_trace",
    "checksum",
    "checksum_checked",
    "checksum_passed",
    "manifest_checksum",
    "bridge_dir",
    "base_dir",
    "candidate_path",
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "order",
    "order_id",
    "order_send",
    "order_close",
    "order_modify",
    "order_delete",
    "lot",
    "lot_size",
    "suggested_lot",
    "signal",
    "trade_signal",
    "action",
    "trading_action",
    "ea_command",
    "can_trade",
    "allow_trade",
    "should_buy",
    "should_sell",
}

FORBIDDEN_RESPONSE_TEXT = {
    "source_reader_status_code",
    "source_upstream_value_status_code",
    "raw_payload",
    "bridge_dir",
    "base_dir",
    "candidate_path",
    "traceback",
    "checksum_checked",
    "checksum_passed",
    "ordersend",
    "orderclose",
    "ordermodify",
    "orderdelete",
}


@pytest.fixture()
def canonical_boundary_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, list[str], list[str]]:
    forbidden_calls: list[str] = []
    docs_fixture_reads: list[str] = []
    project_root = Path(__file__).resolve().parents[2]
    original_read_text = Path.read_text

    def fail_reader(*_args: object, **_kwargs: object) -> None:
        forbidden_calls.append("reader")
        raise AssertionError("canonical diagnostics contract must not call reader")

    def fail_canonical_gate(*_args: object, **_kwargs: object) -> None:
        forbidden_calls.append("canonical_data_quality_gate")
        raise AssertionError(
            "canonical diagnostics contract must not activate DataQualityGate"
        )

    def docs_fixture_read_text(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        relative_path = path.resolve().relative_to(project_root)
        assert relative_path.parts[:2] == ("docs", "implementation_plans")
        docs_fixture_reads.append(relative_path.as_posix())
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(
        mt4_demo_readonly_reader,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_reader,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "read_mt4_demo_readonly_source_summary_from_dir",
        fail_reader,
        raising=False,
    )
    monkeypatch.setattr(
        data_quality_gate,
        "evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate",
        fail_canonical_gate,
    )
    monkeypatch.setattr(
        demo_readonly_api,
        "evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate",
        fail_canonical_gate,
        raising=False,
    )
    monkeypatch.setattr(Path, "read_text", docs_fixture_read_text)

    return TestClient(app), forbidden_calls, docs_fixture_reads


def test_default_diagnostics_remains_docs_fixture_with_reader_not_called(
    canonical_boundary_harness: tuple[TestClient, list[str], list[str]],
) -> None:
    client, forbidden_calls, docs_fixture_reads = canonical_boundary_harness

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert forbidden_calls == []
    assert docs_fixture_reads
    assert all(
        fixture_path.startswith("docs/implementation_plans/")
        for fixture_path in docs_fixture_reads
    )
    assert data["source_scope"] == "docs_fixture_only"
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["reader_status"] == "not_called"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_NOT_CALLED"
    assert data["validation_stage"] == "docs_fixture_bundle_summary"
    _assert_current_contract(data)


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {
            "params": {
                "source_mode": MT4_SOURCE_MODE,
                CANONICAL_GATE_FIELD: "true",
                "bridge_dir": r"C:\Users\hidden\bridge",
                "base_dir": "/home/hidden/base",
                "candidate_path": "/home/hidden/candidate.json",
            }
        },
        {
            "headers": {
                "X-Source-Mode": MT4_SOURCE_MODE,
                "X-Canonical-Data-Quality-Gate": "true",
                "X-Bridge-Dir": r"C:\Users\hidden\bridge",
                "X-Base-Dir": "/home/hidden/base",
                "X-Candidate-Path": "/home/hidden/candidate.json",
            }
        },
        {
            "json": {
                "source_mode": MT4_SOURCE_MODE,
                CANONICAL_GATE_FIELD: True,
                "bridge_dir": r"C:\Users\hidden\bridge",
                "base_dir": "/home/hidden/base",
                "candidate_path": "/home/hidden/candidate.json",
                "raw_payload": {"secret": "hidden"},
            }
        },
    ],
)
def test_client_input_cannot_activate_reader_or_canonical_data_quality_gate(
    canonical_boundary_harness: tuple[TestClient, list[str], list[str]],
    request_kwargs: dict[str, Any],
) -> None:
    client, forbidden_calls, docs_fixture_reads = canonical_boundary_harness

    response = client.request(
        "GET",
        DEMO_READONLY_DIAGNOSTICS_ENDPOINT,
        **request_kwargs,
    )

    assert response.status_code == 200
    data = response.json()
    assert forbidden_calls == []
    assert docs_fixture_reads
    assert data["source_mode"] == "docs_fixture_only"
    assert data["source_status"] == "docs_fixture_only_ready"
    assert data["reader_status"] == "not_called"
    assert data["reader_passed"] is False
    assert data["reader_status_code"] == "READER_NOT_CALLED"
    assert data["validation_stage"] == "docs_fixture_bundle_summary"
    _assert_current_contract(data)


def test_diagnostics_response_does_not_expose_canonical_gate_or_reader_internals(
    canonical_boundary_harness: tuple[TestClient, list[str], list[str]],
) -> None:
    client, forbidden_calls, _docs_fixture_reads = canonical_boundary_harness

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert forbidden_calls == []
    _assert_forbidden_keys_absent(data)
    serialized = json.dumps(data, ensure_ascii=True).casefold()
    for marker in FORBIDDEN_RESPONSE_TEXT:
        assert marker.casefold() not in serialized


def test_diagnostics_readiness_is_never_trading_or_execution_permission(
    canonical_boundary_harness: tuple[TestClient, list[str], list[str]],
) -> None:
    client, forbidden_calls, _docs_fixture_reads = canonical_boundary_harness

    response = client.get(DEMO_READONLY_DIAGNOSTICS_ENDPOINT)

    assert response.status_code == 200
    data = response.json()
    assert forbidden_calls == []
    assert data["passed"] is True
    assert data["source_config_passed"] is True
    assert data["reader_passed"] is False
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value
    assert any("not trading permission" in note for note in data["readiness_notes"])
    assert any("not execution permission" in note for note in data["readiness_notes"])
    _assert_current_contract(data)


def _assert_current_contract(data: dict[str, Any]) -> None:
    assert set(data) == EXPECTED_TOP_LEVEL_KEYS
    assert data["api_version"] == "1.0"
    assert data["endpoint"] == DEMO_READONLY_DIAGNOSTICS_ENDPOINT
    for field_name, expected_value in SAFE_FLAGS.items():
        assert data[field_name] is expected_value
    _assert_forbidden_keys_absent(data)


def _assert_forbidden_keys_absent(value: Any) -> None:
    if isinstance(value, dict):
        normalized_keys = {
            key.casefold() for key in value if isinstance(key, str)
        }
        assert normalized_keys.isdisjoint(FORBIDDEN_RESPONSE_KEYS)
        for child in value.values():
            _assert_forbidden_keys_absent(child)
        return
    if isinstance(value, list):
        for child in value:
            _assert_forbidden_keys_absent(child)
