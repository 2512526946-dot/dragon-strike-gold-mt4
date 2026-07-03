from app.services.data_quality_gate import (
    BLOCKED_BY_CROSS_FIELD_CHECKS,
    BLOCKED_BY_FIELD_TYPES,
    BLOCKED_BY_GATE_V0,
    BLOCKED_BY_MULTIPLE_REASONS,
    BLOCKED_BY_NUMERIC_RANGES,
    BLOCKED_BY_READ_STATUS,
    BLOCKED_BY_REQUIRED_FIELDS,
    DATA_QUALITY_GATE_V0_NOTE,
    DATA_QUALITY_GATE_V0_STAGE,
    DATA_QUALITY_GATE_V1_STAGE,
    DATA_QUALITY_PASSED,
    READY_FOR_SCHEMA_CHECKS,
    DataQualityGateV0Result,
    DataQualityGateV1Result,
    evaluate_data_quality_gate_v1,
)
from app.services.mt4_cross_field_checks import (
    ALL_CROSS_FIELD_CHECKS_VALID,
    CROSS_FIELD_CHECKS_OK,
    CROSS_FIELD_RULE_VIOLATION,
    SOME_CROSS_FIELD_CHECKS_INVALID,
    Mt4FileCrossFieldStatus,
    Mt4SnapshotCrossFieldStatus,
)
from app.services.mt4_field_types import (
    ALL_FIELD_TYPES_VALID,
    FIELD_TYPE_MISMATCH,
    FIELD_TYPES_OK,
    SOME_FIELD_TYPES_INVALID,
    Mt4FileFieldTypesStatus,
    Mt4SnapshotFieldTypesStatus,
)
from app.services.mt4_numeric_ranges import (
    ALL_NUMERIC_RANGES_VALID,
    NUMERIC_RANGE_VIOLATION,
    NUMERIC_RANGES_OK,
    SOME_NUMERIC_RANGES_INVALID,
    Mt4FileNumericRangesStatus,
    Mt4SnapshotNumericRangesStatus,
)
from app.services.mt4_required_fields import (
    ALL_REQUIRED_FIELDS_PRESENT,
    MISSING_REQUIRED_FIELDS,
    REQUIRED_FIELDS_OK,
    SOME_REQUIRED_FIELDS_MISSING,
    Mt4FileRequiredFieldsStatus,
    Mt4SnapshotRequiredFieldsStatus,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


def _gate_v0(*, can_proceed: bool = True) -> DataQualityGateV0Result:
    return DataQualityGateV0Result(
        stage=DATA_QUALITY_GATE_V0_STAGE,
        status_code=READY_FOR_SCHEMA_CHECKS if can_proceed else BLOCKED_BY_READ_STATUS,
        can_proceed_to_schema_checks=can_proceed,
        blocked_by_read_status=not can_proceed,
        blocked_by_metadata=False,
        blocked_by_freshness=False,
        reasons=[] if can_proceed else [f"read_status:{BLOCKED_BY_READ_STATUS}"],
        source_read_status_code=READY_FOR_SCHEMA_CHECKS
        if can_proceed
        else BLOCKED_BY_READ_STATUS,
        source_metadata_status_code=None,
        source_freshness_status_code=None,
        is_tradable=False,
        note=DATA_QUALITY_GATE_V0_NOTE,
    )


def _required_fields(*, can_proceed: bool = True) -> Mt4SnapshotRequiredFieldsStatus:
    file_statuses = tuple(
        _required_file(file_name, can_proceed=can_proceed)
        for file_name in _file_names()
    )
    return Mt4SnapshotRequiredFieldsStatus(
        live_tick=file_statuses[0],
        latest_bars=file_statuses[1],
        symbol_spec=file_statuses[2],
        account_snapshot=file_statuses[3],
        all_required_fields_present=can_proceed,
        can_proceed_to_value_checks=can_proceed,
        status_code=ALL_REQUIRED_FIELDS_PRESENT
        if can_proceed
        else SOME_REQUIRED_FIELDS_MISSING,
        reasons=[] if can_proceed else [f"{LIVE_TICK_FILE}:{MISSING_REQUIRED_FIELDS}:bid"],
        is_tradable=False,
        note="Required field presence checks are not trading permission.",
    )


def _field_types(*, can_proceed: bool = True) -> Mt4SnapshotFieldTypesStatus:
    file_statuses = tuple(
        _field_type_file(file_name, can_proceed=can_proceed)
        for file_name in _file_names()
    )
    return Mt4SnapshotFieldTypesStatus(
        live_tick=file_statuses[0],
        latest_bars=file_statuses[1],
        symbol_spec=file_statuses[2],
        account_snapshot=file_statuses[3],
        all_field_types_valid=can_proceed,
        can_proceed_to_value_checks=can_proceed,
        status_code=ALL_FIELD_TYPES_VALID if can_proceed else SOME_FIELD_TYPES_INVALID,
        reasons=[] if can_proceed else [f"{LIVE_TICK_FILE}:{FIELD_TYPE_MISMATCH}:bid"],
        is_tradable=False,
        note="Field type checks are not trading permission.",
    )


def _numeric_ranges(*, can_proceed: bool = True) -> Mt4SnapshotNumericRangesStatus:
    file_statuses = tuple(
        _numeric_range_file(file_name, can_proceed=can_proceed)
        for file_name in _file_names()
    )
    return Mt4SnapshotNumericRangesStatus(
        live_tick=file_statuses[0],
        latest_bars=file_statuses[1],
        symbol_spec=file_statuses[2],
        account_snapshot=file_statuses[3],
        all_numeric_ranges_valid=can_proceed,
        can_proceed_to_cross_field_checks=can_proceed,
        status_code=ALL_NUMERIC_RANGES_VALID
        if can_proceed
        else SOME_NUMERIC_RANGES_INVALID,
        reasons=[] if can_proceed else [f"{LIVE_TICK_FILE}:{NUMERIC_RANGE_VIOLATION}:bid"],
        is_tradable=False,
        note="Numeric range checks are not trading permission.",
    )


def _cross_fields(*, can_proceed: bool = True) -> Mt4SnapshotCrossFieldStatus:
    file_statuses = tuple(
        _cross_field_file(file_name, can_proceed=can_proceed)
        for file_name in _file_names()
    )
    return Mt4SnapshotCrossFieldStatus(
        live_tick=file_statuses[0],
        latest_bars=file_statuses[1],
        symbol_spec=file_statuses[2],
        account_snapshot=file_statuses[3],
        all_cross_field_checks_valid=can_proceed,
        can_proceed_to_data_quality_gate_finalization=can_proceed,
        status_code=ALL_CROSS_FIELD_CHECKS_VALID
        if can_proceed
        else SOME_CROSS_FIELD_CHECKS_INVALID,
        reasons=[] if can_proceed else [f"{LIVE_TICK_FILE}:{CROSS_FIELD_RULE_VIOLATION}:ask_gte_bid"],
        is_tradable=False,
        note="Cross field checks are not trading permission.",
    )


def _required_file(
    file_name: str,
    *,
    can_proceed: bool,
) -> Mt4FileRequiredFieldsStatus:
    return Mt4FileRequiredFieldsStatus(
        file_name=file_name,
        required_fields=[],
        present_fields=[],
        missing_fields=[] if can_proceed else ["bid"],
        null_fields=[],
        all_required_fields_present=can_proceed,
        can_proceed_to_value_checks=can_proceed,
        status_code=REQUIRED_FIELDS_OK if can_proceed else MISSING_REQUIRED_FIELDS,
        error_codes=[] if can_proceed else [MISSING_REQUIRED_FIELDS],
    )


def _field_type_file(
    file_name: str,
    *,
    can_proceed: bool,
) -> Mt4FileFieldTypesStatus:
    return Mt4FileFieldTypesStatus(
        file_name=file_name,
        expected_field_types={},
        valid_type_fields=[],
        wrong_type_fields=[] if can_proceed else ["bid"],
        type_issues=[],
        all_field_types_valid=can_proceed,
        can_proceed_to_value_checks=can_proceed,
        status_code=FIELD_TYPES_OK if can_proceed else FIELD_TYPE_MISMATCH,
        error_codes=[] if can_proceed else [FIELD_TYPE_MISMATCH],
    )


def _numeric_range_file(
    file_name: str,
    *,
    can_proceed: bool,
) -> Mt4FileNumericRangesStatus:
    return Mt4FileNumericRangesStatus(
        file_name=file_name,
        checked_fields=[],
        invalid_fields=[] if can_proceed else ["bid"],
        range_issues=[],
        all_numeric_ranges_valid=can_proceed,
        can_proceed_to_cross_field_checks=can_proceed,
        status_code=NUMERIC_RANGES_OK if can_proceed else NUMERIC_RANGE_VIOLATION,
        error_codes=[] if can_proceed else [NUMERIC_RANGE_VIOLATION],
    )


def _cross_field_file(
    file_name: str,
    *,
    can_proceed: bool,
) -> Mt4FileCrossFieldStatus:
    return Mt4FileCrossFieldStatus(
        file_name=file_name,
        checked_rules=[],
        violated_rules=[] if can_proceed else ["ask_gte_bid"],
        cross_field_issues=[],
        all_cross_field_checks_valid=can_proceed,
        can_proceed_to_data_quality_gate_finalization=can_proceed,
        status_code=CROSS_FIELD_CHECKS_OK if can_proceed else CROSS_FIELD_RULE_VIOLATION,
        error_codes=[] if can_proceed else [CROSS_FIELD_RULE_VIOLATION],
    )


def _file_names() -> tuple[str, str, str, str]:
    return (
        LIVE_TICK_FILE,
        LATEST_BARS_FILE,
        SYMBOL_SPEC_FILE,
        ACCOUNT_SNAPSHOT_FILE,
    )


def _evaluate(
    *,
    gate_v0: bool = True,
    required_fields: bool = True,
    field_types: bool = True,
    numeric_ranges: bool = True,
    cross_fields: bool = True,
) -> DataQualityGateV1Result:
    return evaluate_data_quality_gate_v1(
        _gate_v0(can_proceed=gate_v0),
        _required_fields(can_proceed=required_fields),
        _field_types(can_proceed=field_types),
        _numeric_ranges(can_proceed=numeric_ranges),
        _cross_fields(can_proceed=cross_fields),
    )


def test_data_quality_gate_v1_passes_when_all_layers_pass() -> None:
    result = _evaluate()

    assert isinstance(result, DataQualityGateV1Result)
    assert result.stage == DATA_QUALITY_GATE_V1_STAGE
    assert result.status_code == DATA_QUALITY_PASSED
    assert result.data_quality_passed is True
    assert result.can_proceed_to_read_only_analysis is True
    assert result.is_tradable is False
    assert result.reasons == []


def test_data_quality_gate_v1_blocked_by_gate_v0() -> None:
    result = _evaluate(gate_v0=False)

    assert result.blocked_by_gate_v0 is True
    assert result.status_code == BLOCKED_BY_GATE_V0
    assert result.data_quality_passed is False
    assert result.can_proceed_to_read_only_analysis is False


def test_data_quality_gate_v1_blocked_by_required_fields() -> None:
    result = _evaluate(required_fields=False)

    assert result.blocked_by_required_fields is True
    assert result.status_code == BLOCKED_BY_REQUIRED_FIELDS
    assert result.data_quality_passed is False


def test_data_quality_gate_v1_blocked_by_field_types() -> None:
    result = _evaluate(field_types=False)

    assert result.blocked_by_field_types is True
    assert result.status_code == BLOCKED_BY_FIELD_TYPES
    assert result.data_quality_passed is False


def test_data_quality_gate_v1_blocked_by_numeric_ranges() -> None:
    result = _evaluate(numeric_ranges=False)

    assert result.blocked_by_numeric_ranges is True
    assert result.status_code == BLOCKED_BY_NUMERIC_RANGES
    assert result.data_quality_passed is False


def test_data_quality_gate_v1_blocked_by_cross_field_checks() -> None:
    result = _evaluate(cross_fields=False)

    assert result.blocked_by_cross_field_checks is True
    assert result.status_code == BLOCKED_BY_CROSS_FIELD_CHECKS
    assert result.data_quality_passed is False


def test_data_quality_gate_v1_blocked_by_multiple_reasons() -> None:
    result = _evaluate(
        gate_v0=False,
        required_fields=False,
        numeric_ranges=False,
    )

    assert result.status_code == BLOCKED_BY_MULTIPLE_REASONS
    assert result.data_quality_passed is False
    assert result.reasons == [
        f"gate_v0:{BLOCKED_BY_READ_STATUS}",
        f"required_fields:{SOME_REQUIRED_FIELDS_MISSING}",
        f"numeric_ranges:{SOME_NUMERIC_RANGES_INVALID}",
    ]


def test_data_quality_gate_v1_note_and_tradable_boundary() -> None:
    result = _evaluate()

    assert result.is_tradable is False
    assert "DataQualityGate v1 is not a trading permission." in result.note
    assert "It does not generate trading signals." in result.note
    assert "It only allows proceeding to read-only analysis." in result.note


def test_data_quality_gate_v1_source_status_codes_are_preserved() -> None:
    result = _evaluate()

    assert result.source_gate_v0_status_code == READY_FOR_SCHEMA_CHECKS
    assert result.source_required_fields_status_code == ALL_REQUIRED_FIELDS_PRESENT
    assert result.source_field_types_status_code == ALL_FIELD_TYPES_VALID
    assert result.source_numeric_ranges_status_code == ALL_NUMERIC_RANGES_VALID
    assert result.source_cross_field_status_code == ALL_CROSS_FIELD_CHECKS_VALID


def test_data_quality_gate_v1_uses_constructed_results_only(tmp_path) -> None:
    result = _evaluate()

    assert result.status_code == DATA_QUALITY_PASSED
    assert "data/mt4" not in str(tmp_path).replace("\\", "/")
