from __future__ import annotations

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
    sentinel: dict[str, Any] = {"sentinel": object()}

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
