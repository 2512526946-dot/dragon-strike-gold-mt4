from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.data_quality_gate import (
    BLOCKED_BY_GATE_V0,
    BLOCKED_BY_MULTIPLE_REASONS,
    DATA_QUALITY_PASSED,
)
from app.services.mt4_cross_field_checks import ASK_GTE_BID
from app.services.mt4_diagnostics import (
    MT4_DIAGNOSTICS_NOTE,
    MT4_DIAGNOSTICS_STAGE,
    Mt4DiagnosticsResult,
    build_mt4_diagnostics,
)
from app.services.mt4_field_types import FIELD_TYPE_MISMATCH
from app.services.mt4_numeric_ranges import NUMERIC_RANGE_VIOLATION
from app.services.mt4_required_fields import MISSING_REQUIRED_FIELDS
from app.services.mt4_snapshot_freshness import GENERATED_AT_STALE
from app.services.mt4_snapshot_metadata import UNEXPECTED_FILE_TYPE
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


NOW_UTC = datetime(2026, 7, 4, 10, 15, 30, tzinfo=UTC)
FRESH_GENERATED_AT = "2026-07-04T10:15:25Z"
STALE_GENERATED_AT = "2026-07-04T10:14:00Z"


def test_diagnostics_passes_for_valid_fresh_snapshot(tmp_path: Path) -> None:
    _write_snapshot_files(tmp_path)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert isinstance(result, Mt4DiagnosticsResult)
    assert result.stage == MT4_DIAGNOSTICS_STAGE
    assert result.status_code == DATA_QUALITY_PASSED
    assert result.data_quality_passed is True
    assert result.can_proceed_to_read_only_analysis is True
    assert result.gate_v1_result.status_code == DATA_QUALITY_PASSED
    assert result.is_tradable is False


def test_diagnostics_reports_missing_file_without_reading_real_mt4_path(
    tmp_path: Path,
) -> None:
    _write_snapshot_files(tmp_path, omit={LIVE_TICK_FILE})

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.read_summary.missing_files == [LIVE_TICK_FILE]
    assert result.data_quality_passed is False
    assert result.can_proceed_to_read_only_analysis is False
    assert result.gate_v1_result.status_code == BLOCKED_BY_MULTIPLE_REASONS
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")


def test_diagnostics_reports_invalid_json_for_one_file_only(
    tmp_path: Path,
) -> None:
    _write_snapshot_files(tmp_path, omit={LIVE_TICK_FILE})
    (tmp_path / LIVE_TICK_FILE).write_text("{bad json", encoding="utf-8")

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.read_summary.invalid_json_files == [LIVE_TICK_FILE]
    assert result.read_summary.missing_files == []
    assert result.data_quality_passed is False
    assert result.gate_v1_result.status_code == BLOCKED_BY_MULTIPLE_REASONS


def test_diagnostics_reports_unexpected_file_type(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[LIVE_TICK_FILE]["file_type"] = "latest_bars"
    _write_snapshot_files(tmp_path, payloads=payloads)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.metadata_status.live_tick.status_code == UNEXPECTED_FILE_TYPE
    assert result.gate_v0_result.blocked_by_metadata is True
    assert result.data_quality_passed is False
    assert result.gate_v1_result.status_code == BLOCKED_BY_GATE_V0


def test_diagnostics_reports_stale_generated_at(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[LIVE_TICK_FILE]["generated_at"] = STALE_GENERATED_AT
    _write_snapshot_files(tmp_path, payloads=payloads)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.freshness_status.live_tick.status_code == GENERATED_AT_STALE
    assert result.gate_v0_result.blocked_by_freshness is True
    assert result.data_quality_passed is False
    assert result.gate_v1_result.status_code == BLOCKED_BY_GATE_V0


def test_diagnostics_reports_missing_required_field(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[LIVE_TICK_FILE].pop("bid")
    _write_snapshot_files(tmp_path, payloads=payloads)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert "bid" in result.required_fields_status.live_tick.missing_fields
    assert result.required_fields_status.live_tick.status_code == MISSING_REQUIRED_FIELDS
    assert result.data_quality_passed is False


def test_diagnostics_reports_field_type_mismatch(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[LIVE_TICK_FILE]["bid"] = "2030.12"
    _write_snapshot_files(tmp_path, payloads=payloads)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.field_types_status.live_tick.status_code == FIELD_TYPE_MISMATCH
    assert "bid" in result.field_types_status.live_tick.wrong_type_fields
    assert result.gate_v1_result.status_code == BLOCKED_BY_MULTIPLE_REASONS
    assert result.gate_v1_result.blocked_by_field_types is True


def test_diagnostics_reports_numeric_range_violation(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[LIVE_TICK_FILE]["bid"] = 0
    _write_snapshot_files(tmp_path, payloads=payloads)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.numeric_ranges_status.live_tick.status_code == NUMERIC_RANGE_VIOLATION
    assert "bid" in result.numeric_ranges_status.live_tick.invalid_fields
    assert result.gate_v1_result.status_code == BLOCKED_BY_MULTIPLE_REASONS
    assert result.gate_v1_result.blocked_by_numeric_ranges is True


def test_diagnostics_reports_cross_field_violation(tmp_path: Path) -> None:
    payloads = _valid_payloads()
    payloads[LIVE_TICK_FILE]["ask"] = 2020.0
    _write_snapshot_files(tmp_path, payloads=payloads)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.cross_field_status.live_tick.violated_rules == [ASK_GTE_BID]
    assert result.data_quality_passed is False


def test_diagnostics_preserves_read_only_note_and_tradable_boundary(
    tmp_path: Path,
) -> None:
    _write_snapshot_files(tmp_path)

    result = build_mt4_diagnostics(tmp_path, NOW_UTC)

    assert result.is_tradable is False
    assert result.note == MT4_DIAGNOSTICS_NOTE
    assert "Diagnostics are read-only." in result.note
    assert "Diagnostics are not trading permission." in result.note
    assert "Diagnostics do not generate trading signals." in result.note


def _write_snapshot_files(
    base_dir: Path,
    *,
    payloads: dict[str, dict[str, Any]] | None = None,
    omit: set[str] | None = None,
) -> None:
    omitted_files = omit or set()
    snapshot_payloads = payloads or _valid_payloads()

    for file_name, payload in snapshot_payloads.items():
        if file_name in omitted_files:
            continue
        (base_dir / file_name).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


def _valid_payloads() -> dict[str, dict[str, Any]]:
    return copy.deepcopy(
        {
            LIVE_TICK_FILE: {
                "schema_version": "1.0",
                "file_type": "live_tick",
                "source": "mt4_file_bridge",
                "generated_at": FRESH_GENERATED_AT,
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
                "generated_at": FRESH_GENERATED_AT,
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
                "generated_at": FRESH_GENERATED_AT,
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
                "generated_at": FRESH_GENERATED_AT,
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
    )
