from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
from typing import Any, Final

from app.services import demo_readonly_canonical_diagnostics_pipeline as pipeline
from app.services import demo_readonly_canonical_diagnostics_summary_validator as validator


REPLAY_CONTRACT_VERSION: Final = "canonical_bundle_replay_v1"
REGISTRY_VERSION: Final = "canonical_bundle_replay_registry_v1"
PIPELINE_CONTRACT_VERSION: Final = "canonical_diagnostics_pipeline_g153_v1"
POLICY_PROFILE_VERSION: Final = "canonical_diagnostics_default_policy_v1"

CANONICAL_BUNDLE_REPLAY_MATCHED: Final = "CANONICAL_BUNDLE_REPLAY_MATCHED"
CANONICAL_BUNDLE_REPLAY_INPUT_INVALID: Final = (
    "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID"
)
CANONICAL_BUNDLE_REPLAY_RESULT_INVALID: Final = (
    "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID"
)
CANONICAL_BUNDLE_REPLAY_MISMATCH: Final = "CANONICAL_BUNDLE_REPLAY_MISMATCH"
CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE: Final = (
    "CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE"
)

REPLAY_CASE_INPUT_INVALID: Final = "REPLAY_CASE_INPUT_INVALID"
REPLAY_CASE_REGISTRY_INVALID: Final = "REPLAY_CASE_REGISTRY_INVALID"
REPLAY_CASE_RESULT_INVALID: Final = "REPLAY_CASE_RESULT_INVALID"
REPLAY_CASE_EXPECTATION_MISMATCH: Final = "REPLAY_CASE_EXPECTATION_MISMATCH"
REPLAY_CASE_EXCEPTION_SANITIZED: Final = "REPLAY_CASE_EXCEPTION_SANITIZED"


@dataclass(frozen=True, slots=True)
class CanonicalBundleReplayCaseV1:
    replay_contract_version: str
    case_id: str
    fixture_id: str


@dataclass(frozen=True, slots=True)
class CanonicalBundleReplayResultV1:
    replay_contract_version: str
    registry_version: str
    pipeline_contract_version: str
    policy_profile_version: str
    case_id: str
    fixture_id: str
    passed: bool
    status_code: str
    canonical_summary: dict[str, Any]
    replay_reason_codes: tuple[str, ...]
    canonical_block_reasons: tuple[str, ...]
    canonical_warning_codes: tuple[str, ...]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool


@dataclass(frozen=True, slots=True)
class _CanonicalBundleReplayRegistryRecordV1:
    registry_version: str
    fixture_id: str
    case_id: str
    allowed_root: Path
    bundle_dir: Path
    reference_time_utc: datetime
    previous_identity: None
    pipeline_contract_version: str
    policy_profile_version: str
    expected_outcome: str
    expected_status_code: str
    expected_block_reasons: tuple[str, ...]
    expected_warning_codes: tuple[str, ...]


_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62})$")
_PUBLIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_UNAVAILABLE = "unavailable"

_CANONICAL_READY = "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
_CANONICAL_READY_WITH_WARNINGS = (
    "CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS"
)
_CANONICAL_BLOCKED = "CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED"
_CANONICAL_INPUT_INVALID = "CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID"
_CANONICAL_SAFE_FAILURE = "CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE"
_CANONICAL_STATUS_BY_OUTCOME = {
    "READY": _CANONICAL_READY,
    "READY_WITH_WARNINGS": _CANONICAL_READY_WITH_WARNINGS,
    "BLOCKED": _CANONICAL_BLOCKED,
    "INPUT_INVALID": _CANONICAL_INPUT_INVALID,
    "SAFE_FAILURE": _CANONICAL_SAFE_FAILURE,
}
_CANONICAL_INPUT_INVALID_REASON = "CANONICAL_DATA_QUALITY_RESULT_INVALID"
_CANONICAL_SAFE_FAILURE_REASON = (
    "CANONICAL_DIAGNOSTICS_ADAPTER_EXCEPTION_SANITIZED"
)
_CANONICAL_BLOCK_REASONS = frozenset(
    {
        "DATA_QUALITY_INPUT_NOT_OBJECT",
        "DATA_QUALITY_REQUIRED_READER_KEY_MISSING",
        "DATA_QUALITY_UNEXPECTED_READER_KEY",
        "DATA_QUALITY_READER_FIELD_TYPE_INVALID",
        "DATA_QUALITY_COMPONENT_STATUS_INVALID",
        "DATA_QUALITY_POLICY_INVALID",
        "READER_SAFETY_ENVELOPE_INVALID",
        "READER_RESULT_INCONSISTENT",
        "READER_WARNING_CODES_INVALID",
        "READER_MIXED_GENERATION_BLOCKED",
        "READER_INTEGRITY_INVALID",
        "READER_DATA_STALE",
        "READER_STRUCTURE_INVALID",
        "READER_VALUE_INVALID",
        "READER_BLOCKED",
        "UPSTREAM_WARNINGS_REJECTED_BY_POLICY",
        "DATA_QUALITY_GATE_EXCEPTION_SANITIZED",
    }
)
_CANONICAL_WARNING_ORDER = ("IDEMPOTENT_REPEAT", "SEQUENCE_GAP")

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_ROOT = _REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
_FIXTURE_BUNDLE_DIR = _FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
_FIXTURE_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
_READY_CASE_ID = "canonical_docs_ready"
_READY_FIXTURE_ID = "canonical_docs_fixture_v1"

_REGISTRY = (
    _CanonicalBundleReplayRegistryRecordV1(
        registry_version=REGISTRY_VERSION,
        fixture_id=_READY_FIXTURE_ID,
        case_id=_READY_CASE_ID,
        allowed_root=_FIXTURE_ROOT,
        bundle_dir=_FIXTURE_BUNDLE_DIR,
        reference_time_utc=_FIXTURE_REFERENCE_TIME,
        previous_identity=None,
        pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
        policy_profile_version=POLICY_PROFILE_VERSION,
        expected_outcome="READY",
        expected_status_code=_CANONICAL_READY,
        expected_block_reasons=(),
        expected_warning_codes=(),
    ),
)


def run_canonical_bundle_replay_case(
    *,
    replay_case: CanonicalBundleReplayCaseV1,
) -> CanonicalBundleReplayResultV1:
    """Run one fixed, offline canonical diagnostics replay case."""

    try:
        if not _replay_case_is_safe(replay_case):
            return _failure_result(
                status_code=CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
                reason_code=REPLAY_CASE_INPUT_INVALID,
            )

        registry_snapshot = _REGISTRY
        if not _registry_is_safe(registry_snapshot):
            return _failure_result(
                status_code=CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
                reason_code=REPLAY_CASE_REGISTRY_INVALID,
            )
        registry_state_snapshot = _registry_state(registry_snapshot)

        registry_record = _resolve_registry_record(
            replay_case=replay_case,
            registry=registry_snapshot,
        )
        if registry_record is None:
            return _failure_result(
                status_code=CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
                reason_code=REPLAY_CASE_INPUT_INVALID,
            )
        case_snapshot = (
            replay_case.replay_contract_version,
            replay_case.case_id,
            replay_case.fixture_id,
        )
    except Exception:
        return _failure_result(
            status_code=CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE,
            reason_code=REPLAY_CASE_EXCEPTION_SANITIZED,
        )

    try:
        canonical_summary = pipeline.build_demo_readonly_canonical_diagnostics_summary(
            allowed_root=registry_record.allowed_root,
            bundle_dir=registry_record.bundle_dir,
            now_utc=registry_record.reference_time_utc,
        )
        if not _post_call_evidence_is_unchanged(
            replay_case=replay_case,
            case_snapshot=case_snapshot,
            registry_snapshot=registry_snapshot,
            registry_state_snapshot=registry_state_snapshot,
        ):
            return _failure_result(
                status_code=CANONICAL_BUNDLE_REPLAY_RESULT_INVALID,
                reason_code=REPLAY_CASE_RESULT_INVALID,
                registry_record=registry_record,
            )
        if not validator.is_safe_demo_readonly_canonical_diagnostics_summary(
            canonical_summary=canonical_summary,
        ):
            return _failure_result(
                status_code=CANONICAL_BUNDLE_REPLAY_RESULT_INVALID,
                reason_code=REPLAY_CASE_RESULT_INVALID,
                registry_record=registry_record,
            )

        actual_block_reasons = tuple(canonical_summary["block_reasons"])
        actual_warning_codes = tuple(canonical_summary["warning_reasons"])
        if (
            canonical_summary["status_code"]
            != registry_record.expected_status_code
            or actual_block_reasons != registry_record.expected_block_reasons
            or actual_warning_codes != registry_record.expected_warning_codes
        ):
            return _failure_result(
                status_code=CANONICAL_BUNDLE_REPLAY_MISMATCH,
                reason_code=REPLAY_CASE_EXPECTATION_MISMATCH,
                registry_record=registry_record,
            )

        detached_summary = deepcopy(canonical_summary)
        return _matched_result(
            registry_record=registry_record,
            canonical_summary=detached_summary,
            block_reasons=actual_block_reasons,
            warning_codes=actual_warning_codes,
        )
    except Exception:
        return _failure_result(
            status_code=CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE,
            reason_code=REPLAY_CASE_EXCEPTION_SANITIZED,
            registry_record=registry_record,
        )


def _replay_case_is_safe(replay_case: object) -> bool:
    return (
        type(replay_case) is CanonicalBundleReplayCaseV1
        and type(replay_case.replay_contract_version) is str
        and replay_case.replay_contract_version == REPLAY_CONTRACT_VERSION
        and _identifier_is_safe(replay_case.case_id)
        and _identifier_is_safe(replay_case.fixture_id)
    )


def _registry_is_safe(registry: object) -> bool:
    if type(registry) is not tuple or not registry:
        return False
    if any(
        type(record) is not _CanonicalBundleReplayRegistryRecordV1
        or not _registry_record_is_safe(record)
        for record in registry
    ):
        return False
    identities = tuple((record.fixture_id, record.case_id) for record in registry)
    fixture_ids = tuple(record.fixture_id for record in registry)
    case_ids = tuple(record.case_id for record in registry)
    return (
        len(identities) == len(set(identities))
        and len(fixture_ids) == len(set(fixture_ids))
        and len(case_ids) == len(set(case_ids))
    )


def _registry_record_is_safe(
    record: _CanonicalBundleReplayRegistryRecordV1,
) -> bool:
    if (
        type(record.registry_version) is not str
        or record.registry_version != REGISTRY_VERSION
        or not _identifier_is_safe(record.fixture_id)
        or not _identifier_is_safe(record.case_id)
        or type(record.allowed_root) is not type(_FIXTURE_ROOT)
        or type(record.bundle_dir) is not type(_FIXTURE_BUNDLE_DIR)
        or record.allowed_root != _FIXTURE_ROOT
        or record.bundle_dir != _FIXTURE_BUNDLE_DIR
        or type(record.reference_time_utc) is not datetime
        or record.reference_time_utc != _FIXTURE_REFERENCE_TIME
        or record.reference_time_utc.tzinfo is not UTC
        or record.previous_identity is not None
        or type(record.pipeline_contract_version) is not str
        or record.pipeline_contract_version != PIPELINE_CONTRACT_VERSION
        or type(record.policy_profile_version) is not str
        or record.policy_profile_version != POLICY_PROFILE_VERSION
        or type(record.expected_outcome) is not str
        or record.expected_outcome not in _CANONICAL_STATUS_BY_OUTCOME
        or type(record.expected_status_code) is not str
        or record.expected_status_code
        != _CANONICAL_STATUS_BY_OUTCOME[record.expected_outcome]
        or not _code_tuple_is_safe(record.expected_block_reasons)
        or not _code_tuple_is_safe(record.expected_warning_codes)
        or not _warning_codes_follow_contract_order(record.expected_warning_codes)
    ):
        return False
    return _oracle_is_consistent(record)


def _oracle_is_consistent(
    record: _CanonicalBundleReplayRegistryRecordV1,
) -> bool:
    if record.expected_outcome == "READY":
        return not record.expected_block_reasons and not record.expected_warning_codes
    if record.expected_outcome == "READY_WITH_WARNINGS":
        return (
            not record.expected_block_reasons
            and len(record.expected_warning_codes) == 1
        )
    if record.expected_outcome == "BLOCKED":
        if (
            len(record.expected_block_reasons) != 1
            or record.expected_block_reasons[0] not in _CANONICAL_BLOCK_REASONS
        ):
            return False
        if record.expected_block_reasons == (
            "UPSTREAM_WARNINGS_REJECTED_BY_POLICY",
        ):
            return bool(record.expected_warning_codes)
        return True
    if record.expected_outcome == "INPUT_INVALID":
        return (
            record.expected_block_reasons
            == (_CANONICAL_INPUT_INVALID_REASON,)
            and not record.expected_warning_codes
        )
    return (
        record.expected_block_reasons == (_CANONICAL_SAFE_FAILURE_REASON,)
        and not record.expected_warning_codes
    )


def _resolve_registry_record(
    *,
    replay_case: CanonicalBundleReplayCaseV1,
    registry: tuple[_CanonicalBundleReplayRegistryRecordV1, ...],
) -> _CanonicalBundleReplayRegistryRecordV1 | None:
    for record in registry:
        if (
            record.fixture_id == replay_case.fixture_id
            and record.case_id == replay_case.case_id
        ):
            return record
    return None


def _post_call_evidence_is_unchanged(
    *,
    replay_case: CanonicalBundleReplayCaseV1,
    case_snapshot: tuple[str, str, str],
    registry_snapshot: tuple[_CanonicalBundleReplayRegistryRecordV1, ...],
    registry_state_snapshot: tuple[tuple[object, ...], ...],
) -> bool:
    return (
        _REGISTRY is registry_snapshot
        and _registry_state(_REGISTRY) == registry_state_snapshot
        and (
            replay_case.replay_contract_version,
            replay_case.case_id,
            replay_case.fixture_id,
        )
        == case_snapshot
    )


def _registry_state(
    registry: tuple[_CanonicalBundleReplayRegistryRecordV1, ...],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            record.registry_version,
            record.fixture_id,
            record.case_id,
            record.allowed_root,
            record.bundle_dir,
            record.reference_time_utc,
            record.previous_identity,
            record.pipeline_contract_version,
            record.policy_profile_version,
            record.expected_outcome,
            record.expected_status_code,
            record.expected_block_reasons,
            record.expected_warning_codes,
        )
        for record in registry
    )


def _identifier_is_safe(value: object) -> bool:
    return (
        type(value) is str
        and _IDENTIFIER_PATTERN.fullmatch(value) is not None
    )


def _code_tuple_is_safe(value: object) -> bool:
    return (
        type(value) is tuple
        and len(value) == len(set(value))
        and all(
            type(code) is str
            and _PUBLIC_CODE_PATTERN.fullmatch(code) is not None
            for code in value
        )
    )


def _warning_codes_follow_contract_order(codes: tuple[str, ...]) -> bool:
    return codes == tuple(code for code in _CANONICAL_WARNING_ORDER if code in codes)


def _matched_result(
    *,
    registry_record: _CanonicalBundleReplayRegistryRecordV1,
    canonical_summary: dict[str, Any],
    block_reasons: tuple[str, ...],
    warning_codes: tuple[str, ...],
) -> CanonicalBundleReplayResultV1:
    return CanonicalBundleReplayResultV1(
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        registry_version=registry_record.registry_version,
        pipeline_contract_version=registry_record.pipeline_contract_version,
        policy_profile_version=registry_record.policy_profile_version,
        case_id=registry_record.case_id,
        fixture_id=registry_record.fixture_id,
        passed=True,
        status_code=CANONICAL_BUNDLE_REPLAY_MATCHED,
        canonical_summary=canonical_summary,
        replay_reason_codes=(),
        canonical_block_reasons=block_reasons,
        canonical_warning_codes=warning_codes,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
    )


def _failure_result(
    *,
    status_code: str,
    reason_code: str,
    registry_record: _CanonicalBundleReplayRegistryRecordV1 | None = None,
) -> CanonicalBundleReplayResultV1:
    identity = (
        (
            registry_record.registry_version,
            registry_record.pipeline_contract_version,
            registry_record.policy_profile_version,
            registry_record.case_id,
            registry_record.fixture_id,
        )
        if registry_record is not None
        else (_UNAVAILABLE,) * 5
    )
    return CanonicalBundleReplayResultV1(
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        registry_version=identity[0],
        pipeline_contract_version=identity[1],
        policy_profile_version=identity[2],
        case_id=identity[3],
        fixture_id=identity[4],
        passed=False,
        status_code=status_code,
        canonical_summary={},
        replay_reason_codes=(reason_code,),
        canonical_block_reasons=(),
        canonical_warning_codes=(),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
    )
