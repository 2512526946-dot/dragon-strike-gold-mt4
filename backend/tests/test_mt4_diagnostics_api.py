from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

import app.api.mt4 as legacy_api
from app.main import app
from app.schemas.mt4_diagnostics import Mt4DiagnosticsResponse
from app.services import mt4_demo_readonly_source_config_guard as source_guard
from app.services.data_quality_gate import BLOCKED_BY_GATE_V0, DATA_QUALITY_PASSED


EXPECTED_RESPONSE_KEYS = frozenset(Mt4DiagnosticsResponse.model_fields)
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
    "ordersend",
    "orderclose",
    "ordermodify",
    "orderdelete",
)


class _StringSubclass(str):
    pass


class _DictSubclass(dict):
    pass


def test_default_legacy_diagnostics_uses_real_canonical_docs_chain() -> None:
    response = TestClient(app).get("/api/mt4/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert set(data) == EXPECTED_RESPONSE_KEYS
    assert data["stage"] == "mt4_diagnostics_v1"
    assert data["status_code"] == DATA_QUALITY_PASSED
    assert data["data_quality_passed"] is True
    assert data["can_proceed_to_read_only_analysis"] is True
    assert data["is_tradable"] is False
    assert data["gate_v1_result"]["warning_reasons"] == []
    _assert_safe_response(data)


def test_blocked_guard_does_not_call_canonical_docs_producer(monkeypatch) -> None:
    blocked = source_guard.validate_demo_readonly_source_config(
        {
            "source_mode": source_guard.MT4_DEMO_READONLY_FILE_BRIDGE_SOURCE_MODE,
            "mt4_demo_readonly_file_bridge_enabled": False,
            "mt4_demo_readonly_bridge_dir": "server-owned-approved-location",
            "allow_request_override": False,
        }
    )

    def fail_if_called() -> None:
        raise AssertionError("blocked source guard must not call the producer")

    monkeypatch.setattr(
        legacy_api,
        "validate_demo_readonly_source_config",
        lambda _config: blocked,
    )
    monkeypatch.setattr(
        legacy_api,
        "build_demo_readonly_canonical_docs_fixture_diagnostics_summary",
        fail_if_called,
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_guard_exception_is_sanitized_to_fixed_blocked_response(monkeypatch) -> None:
    def raise_guard_exception(_config: object) -> None:
        raise RuntimeError("private guard failure")

    monkeypatch.setattr(
        legacy_api,
        "validate_demo_readonly_source_config",
        raise_guard_exception,
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_polluted_guard_output_does_not_call_producer(monkeypatch) -> None:
    polluted = source_guard.validate_demo_readonly_source_config({})
    polluted["raw_payload"] = {"bridge_dir": "private-location"}
    polluted["is_tradable"] = True

    def fail_if_called() -> None:
        raise AssertionError("polluted source guard must not call the producer")

    monkeypatch.setattr(
        legacy_api,
        "validate_demo_readonly_source_config",
        lambda _config: polluted,
    )
    monkeypatch.setattr(
        legacy_api,
        "build_demo_readonly_canonical_docs_fixture_diagnostics_summary",
        fail_if_called,
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_producer_exception_is_sanitized_to_fixed_blocked_response(monkeypatch) -> None:
    def raise_producer_exception() -> None:
        raise RuntimeError("private producer failure")

    monkeypatch.setattr(
        legacy_api,
        "build_demo_readonly_canonical_docs_fixture_diagnostics_summary",
        raise_producer_exception,
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_polluted_producer_summary_is_rejected_by_real_adapter(monkeypatch) -> None:
    monkeypatch.setattr(
        legacy_api,
        "build_demo_readonly_canonical_docs_fixture_diagnostics_summary",
        lambda: {
            "passed": True,
            "raw_payload": {
                "checksum": "private-checksum",
                "traceback": "private-traceback",
            },
        },
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_adapter_exception_is_sanitized_to_fixed_blocked_response(monkeypatch) -> None:
    def raise_adapter_exception(*, canonical_summary: object) -> None:
        raise RuntimeError("private adapter failure")

    monkeypatch.setattr(
        legacy_api,
        "adapt_canonical_summary_to_legacy_mt4_diagnostics_response",
        raise_adapter_exception,
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_polluted_adapter_output_is_sanitized_to_fixed_blocked_response(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        legacy_api,
        "adapt_canonical_summary_to_legacy_mt4_diagnostics_response",
        lambda *, canonical_summary: {
            "raw_payload": {
                "bridge_dir": "private-location",
                "checksum": "private-checksum",
                "traceback": "private-traceback",
            }
        },
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_exact_key_adapter_pollution_is_sanitized_to_fixed_blocked_response(
    monkeypatch,
) -> None:
    real_adapter = (
        legacy_api.adapt_canonical_summary_to_legacy_mt4_diagnostics_response
    )

    def polluted_adapter(*, canonical_summary: object) -> dict[str, Any]:
        result = real_adapter(canonical_summary=canonical_summary)
        result["note"] = "private traceback and bridge_dir must not leak"
        result["gate_v1_result"]["warning_reasons"] = ["UNKNOWN_PRIVATE_WARNING"]
        return result

    monkeypatch.setattr(
        legacy_api,
        "adapt_canonical_summary_to_legacy_mt4_diagnostics_response",
        polluted_adapter,
    )

    data = _get_diagnostics()
    _assert_fixed_blocked_response(data)
    assert "private" not in json.dumps(data, ensure_ascii=False).casefold()


def test_adapter_type_subclasses_are_sanitized_to_fixed_blocked_response(
    monkeypatch,
) -> None:
    real_adapter = (
        legacy_api.adapt_canonical_summary_to_legacy_mt4_diagnostics_response
    )

    def polluted_adapter(*, canonical_summary: object) -> dict[str, Any]:
        result = real_adapter(canonical_summary=canonical_summary)
        result["stage"] = _StringSubclass(result["stage"])
        result["read_summary"] = _DictSubclass(result["read_summary"])
        return result

    monkeypatch.setattr(
        legacy_api,
        "adapt_canonical_summary_to_legacy_mt4_diagnostics_response",
        polluted_adapter,
    )

    _assert_fixed_blocked_response(_get_diagnostics())


def test_legacy_diagnostics_note_never_grants_trading_permission() -> None:
    data = _get_diagnostics()

    assert "Diagnostics are read-only." in data["note"]
    assert "Diagnostics are not trading permission." in data["note"]
    assert "Diagnostics do not generate trading signals." in data["note"]
    assert data["is_tradable"] is False
    _assert_safe_response(data)


def _get_diagnostics() -> dict[str, Any]:
    response = TestClient(app).get("/api/mt4/diagnostics")
    assert response.status_code == 200
    return response.json()


def _assert_fixed_blocked_response(data: dict[str, Any]) -> None:
    assert set(data) == EXPECTED_RESPONSE_KEYS
    assert data["stage"] == "mt4_diagnostics_v1"
    assert data["status_code"] == BLOCKED_BY_GATE_V0
    assert data["data_quality_passed"] is False
    assert data["can_proceed_to_read_only_analysis"] is False
    assert data["is_tradable"] is False
    assert data["gate_v1_result"]["warning_reasons"] == []
    _assert_safe_response(data)


def _assert_safe_response(payload: dict[str, Any]) -> None:
    assert not (_collect_keys(payload) & FORBIDDEN_RESPONSE_KEYS)
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
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
