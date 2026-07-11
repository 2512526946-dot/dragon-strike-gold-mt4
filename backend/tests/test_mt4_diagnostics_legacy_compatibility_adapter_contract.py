"""Contract vectors for the future canonical-to-legacy diagnostics adapter.

These tests deliberately do not import or call an adapter, endpoint, reader,
Gate, or pipeline. They lock the data contract that the later pure adapter
implementation must satisfy.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest


LEGACY_RESPONSE_KEYS = frozenset(
    {
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
)

CANONICAL_STATUS_CASES = (
    MappingProxyType(
        {
            "canonical_status": "READY",
            "legacy_data_quality_passed": True,
            "legacy_readiness": True,
            "expected_outcome": "success",
        }
    ),
    MappingProxyType(
        {
            "canonical_status": "READY_WITH_WARNINGS",
            "legacy_data_quality_passed": True,
            "legacy_readiness": True,
            "expected_outcome": "success_with_allowlisted_warnings",
        }
    ),
    MappingProxyType(
        {
            "canonical_status": "BLOCKED",
            "legacy_data_quality_passed": False,
            "legacy_readiness": False,
            "expected_outcome": "blocked",
        }
    ),
    MappingProxyType(
        {
            "canonical_status": "INPUT_INVALID",
            "legacy_data_quality_passed": False,
            "legacy_readiness": False,
            "expected_outcome": "blocked",
        }
    ),
    MappingProxyType(
        {
            "canonical_status": "SAFE_FAILURE",
            "legacy_data_quality_passed": False,
            "legacy_readiness": False,
            "expected_outcome": "blocked",
        }
    ),
)

FAIL_CLOSED_CASES = (
    MappingProxyType(
        {
            "case": "unknown_status",
            "canonical_status": "UNKNOWN",
        }
    ),
    MappingProxyType(
        {
            "case": "missing_required_key",
            "canonical_status": None,
        }
    ),
    MappingProxyType(
        {
            "case": "unexpected_extra_key",
            "canonical_status": "READY",
        }
    ),
    MappingProxyType(
        {
            "case": "status_passed_mismatch",
            "canonical_status": "READY",
        }
    ),
    MappingProxyType(
        {
            "case": "warning_readiness_mismatch",
            "canonical_status": "READY_WITH_WARNINGS",
        }
    ),
    MappingProxyType(
        {
            "case": "blocked_reason_mismatch",
            "canonical_status": "BLOCKED",
        }
    ),
)

FORBIDDEN_LEGACY_KEYS = frozenset(
    {
        "account_number",
        "allow_trade",
        "api_key",
        "base_dir",
        "bridge_dir",
        "candidate_path",
        "can_execute",
        "can_trade",
        "checksum",
        "checksum_checked",
        "checksum_passed",
        "credential",
        "ea_command",
        "execute_trade",
        "final_lot",
        "lot",
        "order",
        "order_close",
        "order_delete",
        "order_id",
        "order_modify",
        "order_send",
        "password",
        "path",
        "raw_payload",
        "secret",
        "signal",
        "should_buy",
        "should_sell",
        "source_reader_status_code",
        "source_upstream_value_status_code",
        "stack_trace",
        "suggested_lot",
        "ticket",
        "token",
        "traceback",
        "trade_signal",
        "trading_action",
    }
)

FORBIDDEN_LEGACY_TEXT = frozenset(
    {
        "raw payload",
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

UNAVAILABLE_DETAIL_KEYS = frozenset(
    {
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
)


def test_legacy_response_key_contract_is_exact() -> None:
    assert len(LEGACY_RESPONSE_KEYS) == 15
    assert LEGACY_RESPONSE_KEYS == {
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


@pytest.mark.parametrize("case", CANONICAL_STATUS_CASES)
def test_canonical_status_mapping_locks_readonly_legacy_flags(case) -> None:
    assert case["legacy_data_quality_passed"] is (
        case["canonical_status"] in {"READY", "READY_WITH_WARNINGS"}
    )
    assert case["legacy_readiness"] is (
        case["canonical_status"] in {"READY", "READY_WITH_WARNINGS"}
    )
    assert case["legacy_readiness"] is case["legacy_data_quality_passed"]
    assert case["expected_outcome"] in {
        "success",
        "success_with_allowlisted_warnings",
        "blocked",
    }


def test_readiness_is_not_trading_permission() -> None:
    for case in CANONICAL_STATUS_CASES:
        legacy_projection = {
            "data_quality_passed": case["legacy_data_quality_passed"],
            "can_proceed_to_read_only_analysis": case["legacy_readiness"],
            "is_tradable": False,
        }
        assert legacy_projection["is_tradable"] is False
        assert "can_execute" not in legacy_projection
        assert "is_trading_permission" not in legacy_projection


def test_fail_closed_cases_never_define_success() -> None:
    assert {case["case"] for case in FAIL_CLOSED_CASES} == {
        "unknown_status",
        "missing_required_key",
        "unexpected_extra_key",
        "status_passed_mismatch",
        "warning_readiness_mismatch",
        "blocked_reason_mismatch",
    }
    for case in FAIL_CLOSED_CASES:
        assert case["case"]
        assert case["case"] not in {"success", "success_with_allowlisted_warnings"}


def test_legacy_status_code_policy_reuses_existing_vocabulary() -> None:
    legacy_status_policy = MappingProxyType(
        {
            "accepted": True,
            "new_status_codes_allowed": False,
            "unknown_status_is_fail_closed": True,
            "contradictory_status_is_fail_closed": True,
        }
    )

    assert legacy_status_policy["accepted"] is True
    assert legacy_status_policy["new_status_codes_allowed"] is False
    assert legacy_status_policy["unknown_status_is_fail_closed"] is True
    assert legacy_status_policy["contradictory_status_is_fail_closed"] is True


def test_sensitive_and_execution_fields_are_not_legacy_contract_keys() -> None:
    assert FORBIDDEN_LEGACY_KEYS.isdisjoint(LEGACY_RESPONSE_KEYS)
    assert "source_reader_status_code" in FORBIDDEN_LEGACY_KEYS
    assert "source_upstream_value_status_code" in FORBIDDEN_LEGACY_KEYS
    assert "checksum" in FORBIDDEN_LEGACY_KEYS
    assert "raw_payload" in FORBIDDEN_LEGACY_KEYS
    assert "can_execute" in FORBIDDEN_LEGACY_KEYS


def test_sensitive_text_is_negative_filter_input_only() -> None:
    assert FORBIDDEN_LEGACY_TEXT
    assert all(marker not in LEGACY_RESPONSE_KEYS for marker in FORBIDDEN_LEGACY_TEXT)


def test_unavailable_legacy_details_cannot_be_claimed_successful() -> None:
    unavailable_details = {
        key: {"status": "unavailable", "passed": False}
        for key in UNAVAILABLE_DETAIL_KEYS
    }

    assert set(unavailable_details) == UNAVAILABLE_DETAIL_KEYS
    assert all(detail["status"] == "unavailable" for detail in unavailable_details.values())
    assert all(detail["passed"] is False for detail in unavailable_details.values())


def test_contract_vectors_are_immutable() -> None:
    assert type(CANONICAL_STATUS_CASES) is tuple
    assert type(FAIL_CLOSED_CASES) is tuple
    assert type(CANONICAL_STATUS_CASES[0]) is MappingProxyType
    assert type(FAIL_CLOSED_CASES[0]) is MappingProxyType

    with pytest.raises(TypeError):
        CANONICAL_STATUS_CASES[0]["canonical_status"] = "BLOCKED"
    with pytest.raises(TypeError):
        FAIL_CLOSED_CASES[0]["case"] = "success"


def test_contract_scope_does_not_add_runtime_integration_fields() -> None:
    contract_fields = LEGACY_RESPONSE_KEYS | FORBIDDEN_LEGACY_KEYS

    assert "source_mode" not in contract_fields
    assert "bridge_dir" in contract_fields
    assert "candidate_path" in contract_fields
    assert "reader_result" not in LEGACY_RESPONSE_KEYS
    assert "raw_payload" not in LEGACY_RESPONSE_KEYS
