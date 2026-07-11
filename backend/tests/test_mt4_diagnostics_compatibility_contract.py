from __future__ import annotations

from datetime import UTC, datetime
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

import app.api.mt4 as mt4_api
from app.main import app
from app.services import demo_readonly_canonical_diagnostics_pipeline as canonical_pipeline
from app.services.data_quality_gate import DATA_QUALITY_PASSED
from app.services.mt4_file_reader import INVALID_JSON
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


EXPECTED_RESPONSE_KEYS = {
    "stage",
    "status_code",
    "data_quality_passed",
    "can_proceed_to_read_only_analysis",
    "is_tradable",
    "note",
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
FORBIDDEN_RESPONSE_KEYS = {
    "account_number",
    "allow_trade",
    "api_key",
    "base_dir",
    "bridge_dir",
    "candidate_path",
    "can_trade",
    "checksum",
    "checksum_checked",
    "checksum_passed",
    "credential",
    "ea_command",
    "execute_trade",
    "final_lot",
    "login",
    "lot",
    "order",
    "order_close",
    "order_delete",
    "order_id",
    "order_modify",
    "order_send",
    "password",
    "position",
    "raw_payload",
    "secret",
    "signal",
    "should_buy",
    "should_sell",
    "stack_trace",
    "suggested_lot",
    "ticket",
    "token",
    "traceback",
    "trade_signal",
    "trading_action",
}
FORBIDDEN_RESPONSE_TEXT = {
    "raw_payload",
    "password",
    "credential",
    "token",
    "secret",
    "traceback",
    "stack trace",
    "checksum_checked",
    "checksum_passed",
}


def test_legacy_endpoint_preserves_compatible_read_only_response(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_temp_settings(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path)

    data = _get_diagnostics()

    assert set(data) == EXPECTED_RESPONSE_KEYS
    assert data["stage"] == "mt4_diagnostics_v1"
    assert data["status_code"] == DATA_QUALITY_PASSED
    assert data["data_quality_passed"] is True
    assert data["can_proceed_to_read_only_analysis"] is True
    assert data["is_tradable"] is False
    assert "Diagnostics are read-only." in data["note"]
    assert "Diagnostics are not trading permission." in data["note"]
    assert "Diagnostics do not generate trading signals." in data["note"]
    assert "demo_only" not in _collect_keys(data)
    _assert_safe_response(data, tmp_path)


def test_legacy_endpoint_blocks_missing_files_without_execution_semantics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_temp_settings(tmp_path, monkeypatch)

    data = _get_diagnostics()

    assert data["data_quality_passed"] is False
    assert data["can_proceed_to_read_only_analysis"] is False
    assert data["is_tradable"] is False
    assert set(data["read_summary"]["missing_files"]) == {
        LIVE_TICK_FILE,
        LATEST_BARS_FILE,
        SYMBOL_SPEC_FILE,
        ACCOUNT_SNAPSHOT_FILE,
    }
    _assert_safe_response(data, tmp_path)


def test_legacy_endpoint_reports_invalid_json_without_raw_content_leak(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_temp_settings(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path, omit={LIVE_TICK_FILE})
    (tmp_path / LIVE_TICK_FILE).write_text(
        "{bad json SECRET_INVALID_PAYLOAD",
        encoding="utf-8",
    )

    data = _get_diagnostics()
    serialized = json.dumps(data, ensure_ascii=False)

    assert data["data_quality_passed"] is False
    assert data["can_proceed_to_read_only_analysis"] is False
    assert data["read_summary"]["invalid_json_files"] == [LIVE_TICK_FILE]
    assert INVALID_JSON in serialized
    assert "SECRET_INVALID_PAYLOAD" not in serialized
    _assert_safe_response(data, tmp_path)


def test_client_inputs_do_not_change_legacy_endpoint_safety_semantics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_temp_settings(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path)
    client = TestClient(app)

    baseline = client.get("/api/mt4/diagnostics")
    client.cookies.update(
        {
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "bridge_dir": "client-cookie-path",
        }
    )
    injected = client.request(
        "GET",
        "/api/mt4/diagnostics",
        params={
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "bridge_dir": "client-query-path",
            "base_dir": "client-base-path",
            "candidate_path": "client-candidate-path",
        },
        headers={
            "X-Source-Mode": "mt4_demo_readonly_file_bridge_enabled",
            "X-Bridge-Dir": "client-header-path",
        },
        json={
            "source_mode": "mt4_demo_readonly_file_bridge_enabled",
            "bridge_dir": "client-body-path",
            "raw_payload": {"password": "client-secret"},
        },
    )

    assert baseline.status_code == injected.status_code == 200
    baseline_data = baseline.json()
    injected_data = injected.json()
    assert set(baseline_data) == set(injected_data) == EXPECTED_RESPONSE_KEYS
    for key in (
        "stage",
        "status_code",
        "data_quality_passed",
        "can_proceed_to_read_only_analysis",
        "is_tradable",
        "note",
    ):
        assert injected_data[key] == baseline_data[key]
    _assert_safe_response(injected_data, tmp_path)
    assert "source_mode" not in _collect_keys(injected_data)


def test_legacy_endpoint_does_not_call_canonical_pipeline(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_temp_settings(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path)

    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("legacy endpoint must not call canonical pipeline")

    monkeypatch.setattr(
        canonical_pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        fail_if_called,
    )

    data = _get_diagnostics()

    assert data["stage"] == "mt4_diagnostics_v1"
    assert data["is_tradable"] is False
    assert "canonical_diagnostics" not in inspect.getsource(mt4_api)
    _assert_safe_response(data, tmp_path)


def test_legacy_endpoint_contract_does_not_use_environment_or_real_data_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_temp_settings(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path)

    data = _get_diagnostics()
    source = inspect.getsource(mt4_api)

    assert str(tmp_path) not in json.dumps(data, ensure_ascii=False)
    assert "os.environ" not in source
    assert "os.getenv" not in source
    assert "MT4_DATA_DIR" not in source
    assert "data/mt4" not in source.replace("\\", "/")
    _assert_safe_response(data, tmp_path)


def _use_temp_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        mt4_api,
        "get_settings",
        lambda: SimpleNamespace(mt4_data_path=tmp_path),
    )


def _get_diagnostics() -> dict[str, Any]:
    response = TestClient(app).get("/api/mt4/diagnostics")
    assert response.status_code == 200
    return response.json()


def _write_snapshot_files(
    base_dir: Path,
    *,
    omit: set[str] | None = None,
) -> None:
    omitted_files = omit or set()
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    payloads = {
        LIVE_TICK_FILE: {
            "schema_version": "1.0",
            "file_type": "live_tick",
            "source": "mt4_file_bridge",
            "generated_at": generated_at,
            "symbol": "XAUUSD",
            "bid": 2030.12,
            "ask": 2030.42,
            "spread": 0.30,
            "is_tradable": False,
        },
        LATEST_BARS_FILE: {
            "schema_version": "1.0",
            "file_type": "latest_bars",
            "source": "mt4_file_bridge",
            "generated_at": generated_at,
            "symbol": "XAUUSD",
            "timeframes": {"M15": {}, "H1": {}, "H4": {}, "D1": {}},
            "is_tradable": False,
        },
        SYMBOL_SPEC_FILE: {
            "schema_version": "1.0",
            "file_type": "symbol_spec",
            "source": "mt4_file_bridge",
            "generated_at": generated_at,
            "symbol": "XAUUSD",
            "tick_size": 0.01,
            "tick_value": 1.0,
            "lot_size": 100,
            "min_lot": 0.01,
            "lot_step": 0.01,
            "max_lot": 50,
            "is_tradable": False,
        },
        ACCOUNT_SNAPSHOT_FILE: {
            "schema_version": "1.0",
            "file_type": "account_snapshot",
            "source": "mt4_file_bridge",
            "generated_at": generated_at,
            "account_currency": "USD",
            "balance": 10000,
            "equity": 10000,
            "free_margin": 9000,
            "daily_loss_pct": 0,
            "risk_limits": {
                "max_single_trade_loss_pct": 1.0,
                "max_daily_loss_pct": 3.0,
                "no_overnight": True,
            },
            "is_tradable": False,
        },
    }
    for file_name, payload in payloads.items():
        if file_name in omitted_files:
            continue
        (base_dir / file_name).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


def _assert_safe_response(data: dict[str, Any], tmp_path: Path) -> None:
    keys = _collect_keys(data)
    assert not (keys & FORBIDDEN_RESPONSE_KEYS)
    serialized = json.dumps(data, ensure_ascii=False).casefold()
    assert str(tmp_path).casefold() not in serialized
    for forbidden_text in FORBIDDEN_RESPONSE_TEXT:
        assert forbidden_text.casefold() not in serialized


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
