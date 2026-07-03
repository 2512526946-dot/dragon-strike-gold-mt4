from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.services.mt4_diagnostics import Mt4DiagnosticsResult


class Mt4DiagnosticsResponse(BaseModel):
    stage: str
    status_code: str
    data_quality_passed: bool
    can_proceed_to_read_only_analysis: bool
    is_tradable: bool
    note: str
    read_summary: dict[str, Any]
    metadata_status: dict[str, Any]
    freshness_status: dict[str, Any]
    gate_v0_result: dict[str, Any]
    required_fields_status: dict[str, Any]
    field_types_status: dict[str, Any]
    numeric_ranges_status: dict[str, Any]
    cross_field_status: dict[str, Any]
    gate_v1_result: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


def mt4_diagnostics_response(
    result: Mt4DiagnosticsResult,
) -> Mt4DiagnosticsResponse:
    return Mt4DiagnosticsResponse(
        stage=result.stage,
        status_code=result.status_code,
        data_quality_passed=result.data_quality_passed,
        can_proceed_to_read_only_analysis=(
            result.can_proceed_to_read_only_analysis
        ),
        is_tradable=False,
        note=result.note,
        read_summary=_read_summary(result),
        metadata_status=_metadata_status(result),
        freshness_status=_freshness_status(result),
        gate_v0_result=_gate_v0_result(result),
        required_fields_status=_required_fields_status(result),
        field_types_status=_field_types_status(result),
        numeric_ranges_status=_numeric_ranges_status(result),
        cross_field_status=_cross_field_status(result),
        gate_v1_result=_gate_v1_result(result),
    )


def _read_summary(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    summary = result.read_summary
    return {
        "total_files": summary.total_files,
        "present_file_count": summary.present_file_count,
        "readable_object_count": summary.readable_object_count,
        "missing_files": summary.missing_files,
        "not_file_paths": summary.not_file_paths,
        "invalid_json_files": summary.invalid_json_files,
        "not_object_files": summary.not_object_files,
        "read_error_files": summary.read_error_files,
        "all_files_present": summary.all_files_present,
        "all_json_valid": summary.all_json_valid,
        "all_objects": summary.all_objects,
        "can_proceed_to_metadata_checks": summary.can_proceed_to_metadata_checks,
        "status_code": summary.status_code,
    }


def _metadata_status(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.metadata_status
    return {
        "all_metadata_present": status.all_metadata_present,
        "all_file_types_match": status.all_file_types_match,
        "all_sources_match": status.all_sources_match,
        "can_proceed_to_freshness_checks": (
            status.can_proceed_to_freshness_checks
        ),
        "status_code": status.status_code,
        "files": {
            "live_tick": _metadata_file(status.live_tick),
            "latest_bars": _metadata_file(status.latest_bars),
            "symbol_spec": _metadata_file(status.symbol_spec),
            "account_snapshot": _metadata_file(status.account_snapshot),
        },
    }


def _metadata_file(status: Any) -> dict[str, Any]:
    return {
        "file_name": status.file_name,
        "expected_file_type": status.expected_file_type,
        "actual_file_type": status.actual_file_type,
        "has_schema_version": status.has_schema_version,
        "has_file_type": status.has_file_type,
        "has_source": status.has_source,
        "has_generated_at": status.has_generated_at,
        "file_type_matches": status.file_type_matches,
        "source_matches": status.source_matches,
        "can_proceed_to_freshness_checks": (
            status.can_proceed_to_freshness_checks
        ),
        "status_code": status.status_code,
        "error_codes": status.error_codes,
    }


def _freshness_status(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.freshness_status
    return {
        "all_generated_at_parseable": status.all_generated_at_parseable,
        "all_files_fresh": status.all_files_fresh,
        "any_file_stale": status.any_file_stale,
        "any_file_from_future": status.any_file_from_future,
        "can_proceed_to_data_quality_gate": (
            status.can_proceed_to_data_quality_gate
        ),
        "status_code": status.status_code,
        "files": {
            "live_tick": _freshness_file(status.live_tick),
            "latest_bars": _freshness_file(status.latest_bars),
            "symbol_spec": _freshness_file(status.symbol_spec),
            "account_snapshot": _freshness_file(status.account_snapshot),
        },
    }


def _freshness_file(status: Any) -> dict[str, Any]:
    return {
        "file_name": status.file_name,
        "generated_at": status.generated_at,
        "age_seconds": status.age_seconds,
        "max_age_seconds": status.max_age_seconds,
        "max_future_skew_seconds": status.max_future_skew_seconds,
        "is_parseable": status.is_parseable,
        "is_fresh": status.is_fresh,
        "is_stale": status.is_stale,
        "is_from_future": status.is_from_future,
        "can_proceed_to_data_quality_gate": (
            status.can_proceed_to_data_quality_gate
        ),
        "status_code": status.status_code,
        "error_codes": status.error_codes,
    }


def _gate_v0_result(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.gate_v0_result
    return {
        "stage": status.stage,
        "status_code": status.status_code,
        "can_proceed_to_schema_checks": status.can_proceed_to_schema_checks,
        "blocked_by_read_status": status.blocked_by_read_status,
        "blocked_by_metadata": status.blocked_by_metadata,
        "blocked_by_freshness": status.blocked_by_freshness,
        "reasons": status.reasons,
        "source_read_status_code": status.source_read_status_code,
        "source_metadata_status_code": status.source_metadata_status_code,
        "source_freshness_status_code": status.source_freshness_status_code,
        "is_tradable": False,
        "note": status.note,
    }


def _required_fields_status(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.required_fields_status
    return {
        "all_required_fields_present": status.all_required_fields_present,
        "can_proceed_to_value_checks": status.can_proceed_to_value_checks,
        "status_code": status.status_code,
        "reasons": status.reasons,
        "is_tradable": False,
        "note": status.note,
        "files": {
            "live_tick": _required_fields_file(status.live_tick),
            "latest_bars": _required_fields_file(status.latest_bars),
            "symbol_spec": _required_fields_file(status.symbol_spec),
            "account_snapshot": _required_fields_file(status.account_snapshot),
        },
    }


def _required_fields_file(status: Any) -> dict[str, Any]:
    return {
        "file_name": status.file_name,
        "required_fields": status.required_fields,
        "present_fields": status.present_fields,
        "missing_fields": status.missing_fields,
        "null_fields": status.null_fields,
        "all_required_fields_present": status.all_required_fields_present,
        "can_proceed_to_value_checks": status.can_proceed_to_value_checks,
        "status_code": status.status_code,
        "error_codes": status.error_codes,
    }


def _field_types_status(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.field_types_status
    return {
        "all_field_types_valid": status.all_field_types_valid,
        "can_proceed_to_value_checks": status.can_proceed_to_value_checks,
        "status_code": status.status_code,
        "reasons": status.reasons,
        "is_tradable": False,
        "note": status.note,
        "files": {
            "live_tick": _field_types_file(status.live_tick),
            "latest_bars": _field_types_file(status.latest_bars),
            "symbol_spec": _field_types_file(status.symbol_spec),
            "account_snapshot": _field_types_file(status.account_snapshot),
        },
    }


def _field_types_file(status: Any) -> dict[str, Any]:
    return {
        "file_name": status.file_name,
        "expected_field_types": status.expected_field_types,
        "valid_type_fields": status.valid_type_fields,
        "wrong_type_fields": status.wrong_type_fields,
        "type_issues": [
            {
                "field_path": issue.field_path,
                "expected_type": issue.expected_type,
                "actual_type": issue.actual_type,
            }
            for issue in status.type_issues
        ],
        "all_field_types_valid": status.all_field_types_valid,
        "can_proceed_to_value_checks": status.can_proceed_to_value_checks,
        "status_code": status.status_code,
        "error_codes": status.error_codes,
    }


def _numeric_ranges_status(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.numeric_ranges_status
    return {
        "all_numeric_ranges_valid": status.all_numeric_ranges_valid,
        "can_proceed_to_cross_field_checks": (
            status.can_proceed_to_cross_field_checks
        ),
        "status_code": status.status_code,
        "reasons": status.reasons,
        "is_tradable": False,
        "note": status.note,
        "files": {
            "live_tick": _numeric_ranges_file(status.live_tick),
            "latest_bars": _numeric_ranges_file(status.latest_bars),
            "symbol_spec": _numeric_ranges_file(status.symbol_spec),
            "account_snapshot": _numeric_ranges_file(status.account_snapshot),
        },
    }


def _numeric_ranges_file(status: Any) -> dict[str, Any]:
    return {
        "file_name": status.file_name,
        "checked_fields": status.checked_fields,
        "invalid_fields": status.invalid_fields,
        "range_issues": [
            {
                "field_path": issue.field_path,
                "rule": issue.rule,
            }
            for issue in status.range_issues
        ],
        "all_numeric_ranges_valid": status.all_numeric_ranges_valid,
        "can_proceed_to_cross_field_checks": (
            status.can_proceed_to_cross_field_checks
        ),
        "status_code": status.status_code,
        "error_codes": status.error_codes,
    }


def _cross_field_status(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.cross_field_status
    return {
        "all_cross_field_checks_valid": status.all_cross_field_checks_valid,
        "can_proceed_to_data_quality_gate_finalization": (
            status.can_proceed_to_data_quality_gate_finalization
        ),
        "status_code": status.status_code,
        "reasons": status.reasons,
        "is_tradable": False,
        "note": status.note,
        "files": {
            "live_tick": _cross_field_file(status.live_tick),
            "latest_bars": _cross_field_file(status.latest_bars),
            "symbol_spec": _cross_field_file(status.symbol_spec),
            "account_snapshot": _cross_field_file(status.account_snapshot),
        },
    }


def _cross_field_file(status: Any) -> dict[str, Any]:
    return {
        "file_name": status.file_name,
        "checked_rules": status.checked_rules,
        "violated_rules": status.violated_rules,
        "cross_field_issues": [
            {
                "rule_name": issue.rule_name,
                "field_paths": issue.field_paths,
                "message": issue.message,
            }
            for issue in status.cross_field_issues
        ],
        "all_cross_field_checks_valid": status.all_cross_field_checks_valid,
        "can_proceed_to_data_quality_gate_finalization": (
            status.can_proceed_to_data_quality_gate_finalization
        ),
        "status_code": status.status_code,
        "error_codes": status.error_codes,
    }


def _gate_v1_result(result: Mt4DiagnosticsResult) -> dict[str, Any]:
    status = result.gate_v1_result
    return {
        "stage": status.stage,
        "status_code": status.status_code,
        "data_quality_passed": status.data_quality_passed,
        "can_proceed_to_read_only_analysis": (
            status.can_proceed_to_read_only_analysis
        ),
        "blocked_by_gate_v0": status.blocked_by_gate_v0,
        "blocked_by_required_fields": status.blocked_by_required_fields,
        "blocked_by_field_types": status.blocked_by_field_types,
        "blocked_by_numeric_ranges": status.blocked_by_numeric_ranges,
        "blocked_by_cross_field_checks": status.blocked_by_cross_field_checks,
        "reasons": status.reasons,
        "source_gate_v0_status_code": status.source_gate_v0_status_code,
        "source_required_fields_status_code": (
            status.source_required_fields_status_code
        ),
        "source_field_types_status_code": status.source_field_types_status_code,
        "source_numeric_ranges_status_code": (
            status.source_numeric_ranges_status_code
        ),
        "source_cross_field_status_code": status.source_cross_field_status_code,
        "is_tradable": False,
        "note": status.note,
    }
