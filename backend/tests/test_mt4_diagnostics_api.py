from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.data_quality_gate import DATA_QUALITY_PASSED
from app.services.mt4_file_reader import INVALID_JSON
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


FORBIDDEN_RESPONSE_KEYS = {
    "data",
    "can_trade",
    "allow_trade",
    "should_buy",
    "should_sell",
    "suggested_lot",
    "order",
    "position",
    "ticket",
    "OrderSend",
    "OrderClose",
    "OrderModify",
    "OrderDelete",
}


def test_mt4_diagnostics_api_returns_passing_read_only_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_mt4_tmp_dir(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path)
    client = TestClient(app)

    response = client.get("/api/mt4/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "mt4_diagnostics_v1"
    assert data["status_code"] == DATA_QUALITY_PASSED
    assert data["data_quality_passed"] is True
    assert data["can_proceed_to_read_only_analysis"] is True
    assert data["is_tradable"] is False
    assert data["gate_v1_result"]["status_code"] == DATA_QUALITY_PASSED
    assert data["gate_v1_result"]["data_quality_passed"] is True
    assert data["read_summary"]["status_code"] == "ALL_FILES_READABLE_OBJECTS"
    assert data["metadata_status"]["status_code"] == "ALL_METADATA_OK"
    assert data["freshness_status"]["status_code"] == "ALL_FILES_FRESH"
    assert data["required_fields_status"]["status_code"] == (
        "ALL_REQUIRED_FIELDS_PRESENT"
    )
    assert data["field_types_status"]["status_code"] == "ALL_FIELD_TYPES_VALID"
    assert data["numeric_ranges_status"]["status_code"] == "ALL_NUMERIC_RANGES_VALID"
    assert data["cross_field_status"]["status_code"] == "ALL_CROSS_FIELD_CHECKS_VALID"
    _assert_safe_response(data)
    get_settings.cache_clear()


def test_mt4_diagnostics_api_returns_200_when_all_files_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_mt4_tmp_dir(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/mt4/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert data["data_quality_passed"] is False
    assert data["can_proceed_to_read_only_analysis"] is False
    assert sorted(data["read_summary"]["missing_files"]) == sorted(
        [
            LIVE_TICK_FILE,
            LATEST_BARS_FILE,
            SYMBOL_SPEC_FILE,
            ACCOUNT_SNAPSHOT_FILE,
        ]
    )
    assert "gate_v0" in ",".join(data["gate_v1_result"]["reasons"])
    _assert_safe_response(data)
    get_settings.cache_clear()


def test_mt4_diagnostics_api_reports_invalid_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_mt4_tmp_dir(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path, omit={LIVE_TICK_FILE})
    (tmp_path / LIVE_TICK_FILE).write_text("{bad json", encoding="utf-8")
    client = TestClient(app)

    response = client.get("/api/mt4/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert data["data_quality_passed"] is False
    assert data["read_summary"]["invalid_json_files"] == [LIVE_TICK_FILE]
    assert INVALID_JSON in json.dumps(data)
    _assert_safe_response(data)
    get_settings.cache_clear()


def test_mt4_diagnostics_api_note_is_read_only_and_not_trading_permission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _use_mt4_tmp_dir(tmp_path, monkeypatch)
    _write_snapshot_files(tmp_path)
    client = TestClient(app)

    response = client.get("/api/mt4/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert "Diagnostics are read-only." in data["note"]
    assert "Diagnostics are not trading permission." in data["note"]
    assert "Diagnostics do not generate trading signals." in data["note"]
    assert data["is_tradable"] is False
    _assert_safe_response(data)
    get_settings.cache_clear()


def _use_mt4_tmp_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MT4_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()


def _write_snapshot_files(
    base_dir: Path,
    *,
    omit: set[str] | None = None,
) -> None:
    omitted_files = omit or set()
    for file_name, payload in _valid_payloads().items():
        if file_name in omitted_files:
            continue
        (base_dir / file_name).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


def _valid_payloads() -> dict[str, dict[str, Any]]:
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return {
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
            "timeframes": {
                "M15": {},
                "H1": {},
                "H4": {},
                "D1": {},
            },
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


def _assert_safe_response(payload: dict[str, Any]) -> None:
    keys = _collect_keys(payload)
    for forbidden_key in FORBIDDEN_RESPONSE_KEYS:
        assert forbidden_key not in keys


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys: set[str] = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()
