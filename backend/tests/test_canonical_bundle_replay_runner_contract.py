from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass, fields
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

import pytest

from app.services import demo_readonly_canonical_diagnostics_pipeline as pipeline
from app.services import (
    demo_readonly_canonical_diagnostics_summary_adapter as summary_adapter,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_bundle_replay_runner_contract.md"
)
FIXTURE_DIR = (
    REPOSITORY_ROOT
    / "docs"
    / "architecture"
    / "fixtures"
    / "canonical-mt4-demo-readonly-bundle-v1"
)
REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
FIXTURE_FILENAMES = (
    "snapshot_manifest.json",
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)

REPLAY_CONTRACT_VERSION = "canonical_bundle_replay_v1"
REGISTRY_VERSION = "canonical_bundle_replay_registry_v1"
PIPELINE_CONTRACT_VERSION = "canonical_diagnostics_pipeline_g153_v1"
POLICY_PROFILE_VERSION = "canonical_diagnostics_default_policy_v1"
READY_CASE_ID = "canonical_docs_ready"
READY_FIXTURE_ID = "canonical_docs_fixture_v1"
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62})$")
PUBLIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")

PUBLIC_CASE_FIELDS = (
    "replay_contract_version",
    "case_id",
    "fixture_id",
)
RESULT_FIELDS = (
    "replay_contract_version",
    "registry_version",
    "pipeline_contract_version",
    "policy_profile_version",
    "case_id",
    "fixture_id",
    "passed",
    "status_code",
    "canonical_summary",
    "replay_reason_codes",
    "canonical_block_reasons",
    "canonical_warning_codes",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_execution_instruction",
    "allowed_to_call_ea",
)
REGISTRY_FIELDS = (
    "registry_version",
    "fixture_id",
    "case_id",
    "allowed_root",
    "bundle_dir",
    "reference_time_utc",
    "previous_identity",
    "pipeline_contract_version",
    "policy_profile_version",
    "expected_outcome",
    "expected_status_code",
    "expected_block_reasons",
    "expected_warning_codes",
)
G151_SUMMARY_KEYS = frozenset(
    {
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
)
RESULT_SAFETY_FLAGS = MappingProxyType(
    {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
    }
)
G151_SAFETY_FLAGS = MappingProxyType(
    {
        **RESULT_SAFETY_FLAGS,
        "is_trading_permission": False,
        "allowed_to_modify_risk": False,
    }
)

REPLAY_STATUSES = (
    "CANONICAL_BUNDLE_REPLAY_MATCHED",
    "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
    "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
    "CANONICAL_BUNDLE_REPLAY_MISMATCH",
    "CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE",
)
REPLAY_REASONS = (
    "REPLAY_CASE_INPUT_INVALID",
    "REPLAY_CASE_REGISTRY_INVALID",
    "REPLAY_CASE_RESULT_INVALID",
    "REPLAY_CASE_EXPECTATION_MISMATCH",
    "REPLAY_CASE_EXCEPTION_SANITIZED",
)
EXPECTED_OUTCOMES = (
    "READY",
    "READY_WITH_WARNINGS",
    "BLOCKED",
    "INPUT_INVALID",
    "SAFE_FAILURE",
)


@dataclass(frozen=True, slots=True)
class OracleVector:
    name: str
    expected_outcome: str
    canonical_status: str
    block_reasons: tuple[str, ...]
    warning_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReplayCaseVector:
    replay_contract_version: str
    case_id: str
    fixture_id: str


@dataclass(frozen=True, slots=True)
class RegistryRecordVector:
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


@dataclass(frozen=True, slots=True)
class ReplayResultVector:
    replay_contract_version: str
    registry_version: str
    pipeline_contract_version: str
    policy_profile_version: str
    case_id: str
    fixture_id: str
    passed: bool
    status_code: str
    canonical_summary: tuple[tuple[str, object], ...]
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
class ResultCaseVector:
    name: str
    expected_g153_calls: int
    identity_available: bool
    result: ReplayResultVector


@dataclass(frozen=True, slots=True)
class CallerOverrideVector:
    category: str
    field_name: str
    expected_status: str
    expected_reason: str
    expected_g153_calls: int


@dataclass(frozen=True, slots=True)
class CaseShapeVector:
    name: str
    fields: tuple[str, ...]
    exact_builtin_type: bool
    accepted: bool


@dataclass(frozen=True, slots=True)
class InvalidEvidenceVector:
    name: str
    surface: str
    mutation: str
    expected_status: str
    expected_reason: str
    expected_g153_calls: int


READY_G151_SUMMARY = (
    ("passed", True),
    ("status_code", summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY),
    ("source_scope", summary_adapter.SOURCE_SCOPE),
    ("validation_stage", summary_adapter.VALIDATION_STAGE),
    ("fixture_source", summary_adapter.FIXTURE_SOURCE),
    (
        "bundle_validation_status",
        (
            ("passed", True),
            (
                "status_code",
                "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
            ),
            ("block_reasons", ()),
            ("warning_reasons", ()),
            ("read_only", True),
            ("demo_only", True),
            ("is_tradable", False),
            ("can_execute", False),
        ),
    ),
    (
        "component_statuses",
        (
            (
                "canonical_data_quality_gate",
                (
                    ("passed", True),
                    (
                        "status_code",
                        "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
                    ),
                    ("block_reasons", ()),
                    ("warning_reasons", ()),
                    ("read_only", True),
                    ("demo_only", True),
                    ("is_tradable", False),
                    ("can_execute", False),
                ),
            ),
        ),
    ),
    ("block_reasons", ()),
    ("warning_reasons", ()),
    (
        "readiness_notes",
        (
            "Canonical DataQualityGate passed for read-only diagnostics adaptation.",
            "Readiness is not trading permission.",
            "This summary is read-only and cannot execute orders.",
        ),
    ),
    (
        "next_allowed_stage",
        ("demo_readonly_diagnostics_response_integration",),
    ),
    ("next_blocked_stage", ("api_reader_activation", "execution_chain")),
    ("read_only", True),
    ("demo_only", True),
    ("is_tradable", False),
    ("can_execute", False),
    ("is_trading_permission", False),
    ("is_execution_instruction", False),
    ("allowed_to_call_ea", False),
    ("allowed_to_modify_risk", False),
)

PUBLIC_READY_CASE = ReplayCaseVector(
    replay_contract_version=REPLAY_CONTRACT_VERSION,
    case_id=READY_CASE_ID,
    fixture_id=READY_FIXTURE_ID,
)
READY_REGISTRY_RECORD = RegistryRecordVector(
    registry_version=REGISTRY_VERSION,
    fixture_id=READY_FIXTURE_ID,
    case_id=READY_CASE_ID,
    allowed_root=FIXTURE_DIR.parent,
    bundle_dir=FIXTURE_DIR,
    reference_time_utc=REFERENCE_TIME,
    previous_identity=None,
    pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
    policy_profile_version=POLICY_PROFILE_VERSION,
    expected_outcome="READY",
    expected_status_code=summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
    expected_block_reasons=(),
    expected_warning_codes=(),
)

RESULT_CASE_VECTORS = (
    ResultCaseVector(
        name="matched_ready",
        expected_g153_calls=1,
        identity_available=True,
        result=ReplayResultVector(
            replay_contract_version=REPLAY_CONTRACT_VERSION,
            registry_version=REGISTRY_VERSION,
            pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
            policy_profile_version=POLICY_PROFILE_VERSION,
            case_id=READY_CASE_ID,
            fixture_id=READY_FIXTURE_ID,
            passed=True,
            status_code="CANONICAL_BUNDLE_REPLAY_MATCHED",
            canonical_summary=READY_G151_SUMMARY,
            replay_reason_codes=(),
            canonical_block_reasons=(),
            canonical_warning_codes=(),
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
            is_execution_instruction=False,
            allowed_to_call_ea=False,
        ),
    ),
    ResultCaseVector(
        name="input_invalid_before_registry",
        expected_g153_calls=0,
        identity_available=False,
        result=ReplayResultVector(
            replay_contract_version=REPLAY_CONTRACT_VERSION,
            registry_version="unavailable",
            pipeline_contract_version="unavailable",
            policy_profile_version="unavailable",
            case_id="unavailable",
            fixture_id="unavailable",
            passed=False,
            status_code="CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
            canonical_summary=(),
            replay_reason_codes=("REPLAY_CASE_INPUT_INVALID",),
            canonical_block_reasons=(),
            canonical_warning_codes=(),
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
            is_execution_instruction=False,
            allowed_to_call_ea=False,
        ),
    ),
    ResultCaseVector(
        name="result_invalid_after_call",
        expected_g153_calls=1,
        identity_available=True,
        result=ReplayResultVector(
            replay_contract_version=REPLAY_CONTRACT_VERSION,
            registry_version=REGISTRY_VERSION,
            pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
            policy_profile_version=POLICY_PROFILE_VERSION,
            case_id=READY_CASE_ID,
            fixture_id=READY_FIXTURE_ID,
            passed=False,
            status_code="CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
            canonical_summary=(),
            replay_reason_codes=("REPLAY_CASE_RESULT_INVALID",),
            canonical_block_reasons=(),
            canonical_warning_codes=(),
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
            is_execution_instruction=False,
            allowed_to_call_ea=False,
        ),
    ),
    ResultCaseVector(
        name="expectation_mismatch_after_call",
        expected_g153_calls=1,
        identity_available=True,
        result=ReplayResultVector(
            replay_contract_version=REPLAY_CONTRACT_VERSION,
            registry_version=REGISTRY_VERSION,
            pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
            policy_profile_version=POLICY_PROFILE_VERSION,
            case_id=READY_CASE_ID,
            fixture_id=READY_FIXTURE_ID,
            passed=False,
            status_code="CANONICAL_BUNDLE_REPLAY_MISMATCH",
            canonical_summary=(),
            replay_reason_codes=("REPLAY_CASE_EXPECTATION_MISMATCH",),
            canonical_block_reasons=(),
            canonical_warning_codes=(),
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
            is_execution_instruction=False,
            allowed_to_call_ea=False,
        ),
    ),
    ResultCaseVector(
        name="exception_sanitized_after_call",
        expected_g153_calls=1,
        identity_available=True,
        result=ReplayResultVector(
            replay_contract_version=REPLAY_CONTRACT_VERSION,
            registry_version=REGISTRY_VERSION,
            pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
            policy_profile_version=POLICY_PROFILE_VERSION,
            case_id=READY_CASE_ID,
            fixture_id=READY_FIXTURE_ID,
            passed=False,
            status_code="CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE",
            canonical_summary=(),
            replay_reason_codes=("REPLAY_CASE_EXCEPTION_SANITIZED",),
            canonical_block_reasons=(),
            canonical_warning_codes=(),
            read_only=True,
            demo_only=True,
            is_tradable=False,
            can_execute=False,
            is_execution_instruction=False,
            allowed_to_call_ea=False,
        ),
    ),
)

CALLER_OVERRIDE_VECTORS = tuple(
    CallerOverrideVector(
        category=category,
        field_name=field_name,
        expected_status="CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        expected_reason="REPLAY_CASE_INPUT_INVALID",
        expected_g153_calls=0,
    )
    for category, field_name in (
        ("path", "allowed_root"),
        ("path", "bundle_dir"),
        ("clock", "reference_time_utc"),
        ("source", "source_mode"),
        ("policy", "policy_profile_version"),
        ("dependency", "pipeline_dependency"),
        ("oracle", "expected_outcome"),
        ("oracle", "expected_status_code"),
        ("oracle", "expected_block_reasons"),
        ("oracle", "expected_warning_codes"),
    )
)


ORACLE_VECTORS = (
    OracleVector(
        "ready",
        "READY",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
        (),
        (),
    ),
    OracleVector(
        "warning_idempotent_repeat",
        "READY_WITH_WARNINGS",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
        (),
        ("IDEMPOTENT_REPEAT",),
    ),
    OracleVector(
        "warning_sequence_gap",
        "READY_WITH_WARNINGS",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
        (),
        ("SEQUENCE_GAP",),
    ),
    OracleVector(
        "stale_blocked",
        "BLOCKED",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        ("READER_DATA_STALE",),
        (),
    ),
    OracleVector(
        "malformed_structure_blocked",
        "BLOCKED",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        ("READER_STRUCTURE_INVALID",),
        (),
    ),
    OracleVector(
        "mixed_generation_blocked",
        "BLOCKED",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
        ("READER_MIXED_GENERATION_BLOCKED",),
        (),
    ),
    OracleVector(
        "input_invalid",
        "INPUT_INVALID",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID,
        ("CANONICAL_DATA_QUALITY_RESULT_INVALID",),
        (),
    ),
    OracleVector(
        "safe_failure",
        "SAFE_FAILURE",
        summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE,
        ("DATA_QUALITY_GATE_EXCEPTION_SANITIZED",),
        (),
    ),
)

CASE_SHAPE_VECTORS = (
    CaseShapeVector("exact", PUBLIC_CASE_FIELDS, True, True),
    CaseShapeVector("missing", PUBLIC_CASE_FIELDS[:-1], True, False),
    CaseShapeVector(
        "extra_oracle",
        (*PUBLIC_CASE_FIELDS, "expected_outcome"),
        True,
        False,
    ),
    CaseShapeVector(
        "reordered",
        ("case_id", "replay_contract_version", "fixture_id"),
        True,
        False,
    ),
    CaseShapeVector("subclassed", PUBLIC_CASE_FIELDS, False, False),
)

INVALID_EVIDENCE_VECTORS = (
    InvalidEvidenceVector(
        "registry_code_missing",
        "registry",
        "missing required expected_status_code",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_code_extra",
        "registry",
        "extra expected warning code",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_code_duplicate",
        "registry",
        "duplicate expected warning code",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_code_reordered",
        "registry",
        "reordered expected warning codes",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_code_subclassed",
        "registry",
        "non-built-in string code",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_code_unknown",
        "registry",
        "unknown public code",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_code_overlength",
        "registry",
        "public code longer than 128 characters",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "registry_version_mismatch",
        "identity",
        "registry version differs from fixed authority",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "pipeline_version_mismatch",
        "identity",
        "pipeline version differs from fixed authority",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "policy_profile_mismatch",
        "identity",
        "policy profile differs from fixed authority",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_REGISTRY_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "case_identity_mismatch",
        "identity",
        "case id differs from registry authority",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_INPUT_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "fixture_identity_mismatch",
        "identity",
        "fixture id differs from registry authority",
        "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
        "REPLAY_CASE_INPUT_INVALID",
        0,
    ),
    InvalidEvidenceVector(
        "g151_missing_key",
        "g151_summary",
        "missing exact envelope key",
        "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
        "REPLAY_CASE_RESULT_INVALID",
        1,
    ),
    InvalidEvidenceVector(
        "g151_extra_key",
        "g151_summary",
        "extra envelope key",
        "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
        "REPLAY_CASE_RESULT_INVALID",
        1,
    ),
    InvalidEvidenceVector(
        "g151_polluted_text",
        "g151_summary",
        "sensitive text in safe envelope",
        "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
        "REPLAY_CASE_RESULT_INVALID",
        1,
    ),
    InvalidEvidenceVector(
        "g151_contradictory_status",
        "g151_summary",
        "passed and status disagree",
        "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
        "REPLAY_CASE_RESULT_INVALID",
        1,
    ),
    InvalidEvidenceVector(
        "g151_subclassed_container",
        "g151_summary",
        "non-built-in envelope container",
        "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
        "REPLAY_CASE_RESULT_INVALID",
        1,
    ),
    InvalidEvidenceVector(
        "oracle_status_mismatch",
        "oracle_comparison",
        "actual canonical status differs",
        "CANONICAL_BUNDLE_REPLAY_MISMATCH",
        "REPLAY_CASE_EXPECTATION_MISMATCH",
        1,
    ),
    InvalidEvidenceVector(
        "oracle_reason_mismatch",
        "oracle_comparison",
        "actual block reason differs",
        "CANONICAL_BUNDLE_REPLAY_MISMATCH",
        "REPLAY_CASE_EXPECTATION_MISMATCH",
        1,
    ),
    InvalidEvidenceVector(
        "oracle_warning_mismatch",
        "oracle_comparison",
        "actual warning order differs",
        "CANONICAL_BUNDLE_REPLAY_MISMATCH",
        "REPLAY_CASE_EXPECTATION_MISMATCH",
        1,
    ),
)
FORBIDDEN_RESULT_FIELDS = frozenset(
    {
        "deterministic_observations",
        "path",
        "bundle_dir",
        "raw_payload",
        "digest",
        "checksum",
        "traceback",
        "exception_text",
        "source_status",
        "order",
        "execution_payload",
    }
)


def test_contract_declares_exact_public_and_registry_fields() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert _class_fields(contract, "CanonicalBundleReplayCaseV1") == PUBLIC_CASE_FIELDS
    assert _class_fields(contract, "CanonicalBundleReplayResultV1") == RESULT_FIELDS
    assert _registry_fields(contract) == REGISTRY_FIELDS
    assert tuple(field.name for field in fields(ReplayCaseVector)) == PUBLIC_CASE_FIELDS
    assert tuple(field.name for field in fields(ReplayResultVector)) == RESULT_FIELDS
    assert tuple(field.name for field in fields(RegistryRecordVector)) == REGISTRY_FIELDS
    assert len(PUBLIC_CASE_FIELDS) == 3
    assert len(RESULT_FIELDS) == 18
    assert set(RESULT_FIELDS).isdisjoint(FORBIDDEN_RESULT_FIELDS)


def test_contract_fixes_versions_grammars_and_server_owned_authority() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for name, value in (
        ("REPLAY_CONTRACT_VERSION", REPLAY_CONTRACT_VERSION),
        ("REGISTRY_VERSION", REGISTRY_VERSION),
        ("PIPELINE_CONTRACT_VERSION", PIPELINE_CONTRACT_VERSION),
        ("POLICY_PROFILE_VERSION", POLICY_PROFILE_VERSION),
    ):
        assert f"{name} = {value}" in contract
    assert f"IDENTIFIER_PATTERN = {IDENTIFIER_PATTERN.pattern}" in contract
    assert f"PUBLIC_CODE_PATTERN = {PUBLIC_CODE_PATTERN.pattern}" in contract
    assert "The public case contains no expected outcome" in contract
    assert "The registry is code-owned and versioned" in contract
    assert "cannot provide or override paths, reference time" in contract
    for code in (*EXPECTED_OUTCOMES, *REPLAY_STATUSES, *REPLAY_REASONS):
        assert code in contract


@pytest.mark.parametrize(
    ("value", "accepted"),
    (
        ("a", True),
        ("a" * 63, True),
        ("fixture_1-a", True),
        ("", False),
        ("a" * 64, False),
        ("Uppercase", False),
        ("white space", False),
        ("punctuation!", False),
    ),
)
def test_identifier_boundary_vectors_are_exact(value: str, accepted: bool) -> None:
    assert (IDENTIFIER_PATTERN.fullmatch(value) is not None) is accepted


@pytest.mark.parametrize(
    ("value", "accepted"),
    (
        ("A", True),
        ("A" * 128, True),
        ("READY_WITH_WARNINGS", True),
        ("", False),
        ("A" * 129, False),
        ("lowercase", False),
        ("HAS-HYPHEN", False),
        ("HAS SPACE", False),
    ),
)
def test_public_code_boundary_vectors_are_exact(value: str, accepted: bool) -> None:
    assert (PUBLIC_CODE_PATTERN.fullmatch(value) is not None) is accepted


def test_public_case_shape_vectors_lock_missing_extra_order_and_strict_type() -> None:
    assert tuple(vector.name for vector in CASE_SHAPE_VECTORS) == (
        "exact",
        "missing",
        "extra_oracle",
        "reordered",
        "subclassed",
    )
    assert tuple(vector.accepted for vector in CASE_SHAPE_VECTORS) == (
        True,
        False,
        False,
        False,
        False,
    )
    assert CASE_SHAPE_VECTORS[0].fields == PUBLIC_CASE_FIELDS
    assert CASE_SHAPE_VECTORS[-1].exact_builtin_type is False


def test_public_case_and_registry_vectors_lock_server_owned_authority() -> None:
    assert PUBLIC_READY_CASE == ReplayCaseVector(
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        case_id=READY_CASE_ID,
        fixture_id=READY_FIXTURE_ID,
    )
    assert all(
        type(getattr(PUBLIC_READY_CASE, field_name)) is str
        for field_name in PUBLIC_CASE_FIELDS
    )
    assert READY_REGISTRY_RECORD == RegistryRecordVector(
        registry_version=REGISTRY_VERSION,
        fixture_id=READY_FIXTURE_ID,
        case_id=READY_CASE_ID,
        allowed_root=FIXTURE_DIR.parent,
        bundle_dir=FIXTURE_DIR,
        reference_time_utc=REFERENCE_TIME,
        previous_identity=None,
        pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
        policy_profile_version=POLICY_PROFILE_VERSION,
        expected_outcome="READY",
        expected_status_code=summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
        expected_block_reasons=(),
        expected_warning_codes=(),
    )
    assert type(READY_REGISTRY_RECORD.reference_time_utc) is datetime
    assert READY_REGISTRY_RECORD.reference_time_utc.tzinfo is UTC
    assert READY_REGISTRY_RECORD.allowed_root == FIXTURE_DIR.parent
    assert READY_REGISTRY_RECORD.bundle_dir == FIXTURE_DIR
    assert READY_REGISTRY_RECORD.previous_identity is None
    assert READY_REGISTRY_RECORD.pipeline_contract_version == PIPELINE_CONTRACT_VERSION
    assert READY_REGISTRY_RECORD.policy_profile_version == POLICY_PROFILE_VERSION
    for field_name in (
        "registry_version",
        "fixture_id",
        "case_id",
        "pipeline_contract_version",
        "policy_profile_version",
        "expected_outcome",
        "expected_status_code",
    ):
        assert type(getattr(READY_REGISTRY_RECORD, field_name)) is str
    assert type(READY_REGISTRY_RECORD.expected_block_reasons) is tuple
    assert type(READY_REGISTRY_RECORD.expected_warning_codes) is tuple


def test_caller_override_vectors_fail_closed_before_g153() -> None:
    assert tuple(
        (vector.category, vector.field_name)
        for vector in CALLER_OVERRIDE_VECTORS
    ) == (
        ("path", "allowed_root"),
        ("path", "bundle_dir"),
        ("clock", "reference_time_utc"),
        ("source", "source_mode"),
        ("policy", "policy_profile_version"),
        ("dependency", "pipeline_dependency"),
        ("oracle", "expected_outcome"),
        ("oracle", "expected_status_code"),
        ("oracle", "expected_block_reasons"),
        ("oracle", "expected_warning_codes"),
    )
    assert all(
        (
            vector.expected_status,
            vector.expected_reason,
            vector.expected_g153_calls,
        )
        == (
            "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
            "REPLAY_CASE_INPUT_INVALID",
            0,
        )
        for vector in CALLER_OVERRIDE_VECTORS
    )
    assert all(type(vector.field_name) is str for vector in CALLER_OVERRIDE_VECTORS)


def test_oracle_vectors_cover_all_canonical_outcomes_and_warning_order() -> None:
    assert tuple(
        (
            vector.name,
            vector.expected_outcome,
            vector.canonical_status,
            vector.block_reasons,
            vector.warning_codes,
        )
        for vector in ORACLE_VECTORS
    ) == (
        (
            "ready",
            "READY",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY,
            (),
            (),
        ),
        (
            "warning_idempotent_repeat",
            "READY_WITH_WARNINGS",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
            (),
            ("IDEMPOTENT_REPEAT",),
        ),
        (
            "warning_sequence_gap",
            "READY_WITH_WARNINGS",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS,
            (),
            ("SEQUENCE_GAP",),
        ),
        (
            "stale_blocked",
            "BLOCKED",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
            ("READER_DATA_STALE",),
            (),
        ),
        (
            "malformed_structure_blocked",
            "BLOCKED",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
            ("READER_STRUCTURE_INVALID",),
            (),
        ),
        (
            "mixed_generation_blocked",
            "BLOCKED",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED,
            ("READER_MIXED_GENERATION_BLOCKED",),
            (),
        ),
        (
            "input_invalid",
            "INPUT_INVALID",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_INPUT_INVALID,
            ("CANONICAL_DATA_QUALITY_RESULT_INVALID",),
            (),
        ),
        (
            "safe_failure",
            "SAFE_FAILURE",
            summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_SAFE_FAILURE,
            ("DATA_QUALITY_GATE_EXCEPTION_SANITIZED",),
            (),
        ),
    )
    assert {vector.expected_outcome for vector in ORACLE_VECTORS} == set(EXPECTED_OUTCOMES)
    for vector in ORACLE_VECTORS:
        assert type(vector.expected_outcome) is str
        assert PUBLIC_CODE_PATTERN.fullmatch(vector.expected_outcome)
        assert PUBLIC_CODE_PATTERN.fullmatch(vector.canonical_status)
        assert len(vector.block_reasons) == len(set(vector.block_reasons))
        assert len(vector.warning_codes) == len(set(vector.warning_codes))
        assert all(type(code) is str for code in vector.block_reasons)
        assert all(type(code) is str for code in vector.warning_codes)


def test_full_result_vectors_lock_exact_status_reason_identity_and_calls() -> None:
    assert tuple(
        (
            vector.name,
            vector.result.status_code,
            vector.result.replay_reason_codes,
            vector.result.passed,
            vector.expected_g153_calls,
            vector.identity_available,
        )
        for vector in RESULT_CASE_VECTORS
    ) == (
        ("matched_ready", "CANONICAL_BUNDLE_REPLAY_MATCHED", (), True, 1, True),
        (
            "input_invalid_before_registry",
            "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID",
            ("REPLAY_CASE_INPUT_INVALID",),
            False,
            0,
            False,
        ),
        (
            "result_invalid_after_call",
            "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
            ("REPLAY_CASE_RESULT_INVALID",),
            False,
            1,
            True,
        ),
        (
            "expectation_mismatch_after_call",
            "CANONICAL_BUNDLE_REPLAY_MISMATCH",
            ("REPLAY_CASE_EXPECTATION_MISMATCH",),
            False,
            1,
            True,
        ),
        (
            "exception_sanitized_after_call",
            "CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE",
            ("REPLAY_CASE_EXCEPTION_SANITIZED",),
            False,
            1,
            True,
        ),
    )
    for vector in RESULT_CASE_VECTORS:
        result = vector.result
        assert tuple(field.name for field in fields(result)) == RESULT_FIELDS
        assert type(result.passed) is bool
        for field_name in (
            "replay_contract_version",
            "registry_version",
            "pipeline_contract_version",
            "policy_profile_version",
            "case_id",
            "fixture_id",
            "status_code",
        ):
            assert type(getattr(result, field_name)) is str
        assert type(result.replay_reason_codes) is tuple
        assert type(result.canonical_summary) is tuple
        assert type(result.canonical_block_reasons) is tuple
        assert type(result.canonical_warning_codes) is tuple
        for codes in (
            result.replay_reason_codes,
            result.canonical_block_reasons,
            result.canonical_warning_codes,
        ):
            assert all(type(code) is str for code in codes)
            assert len(codes) == len(set(codes))
        for field_name, expected in RESULT_SAFETY_FLAGS.items():
            assert getattr(result, field_name) is expected
        if result.status_code == "CANONICAL_BUNDLE_REPLAY_MATCHED":
            assert result.canonical_summary == READY_G151_SUMMARY
            assert result.replay_reason_codes == ()
        else:
            assert result.canonical_summary == ()
            assert result.canonical_block_reasons == ()
            assert result.canonical_warning_codes == ()
            assert len(result.replay_reason_codes) == 1
        identity = (
            result.registry_version,
            result.pipeline_contract_version,
            result.policy_profile_version,
            result.case_id,
            result.fixture_id,
        )
        assert identity == (
            (
                REGISTRY_VERSION,
                PIPELINE_CONTRACT_VERSION,
                POLICY_PROFILE_VERSION,
                READY_CASE_ID,
                READY_FIXTURE_ID,
            )
            if vector.identity_available
            else ("unavailable",) * 5
        )


def test_invalid_evidence_vectors_lock_fail_closed_status_reason_and_calls() -> None:
    assert len({vector.name for vector in INVALID_EVIDENCE_VECTORS}) == len(
        INVALID_EVIDENCE_VECTORS
    )
    assert {vector.surface for vector in INVALID_EVIDENCE_VECTORS} == {
        "registry",
        "identity",
        "g151_summary",
        "oracle_comparison",
    }
    assert {
        vector.name
        for vector in INVALID_EVIDENCE_VECTORS
        if vector.surface == "registry"
    } == {
        "registry_code_missing",
        "registry_code_extra",
        "registry_code_duplicate",
        "registry_code_reordered",
        "registry_code_subclassed",
        "registry_code_unknown",
        "registry_code_overlength",
    }
    for vector in INVALID_EVIDENCE_VECTORS:
        assert type(vector.mutation) is str and vector.mutation
        assert vector.expected_status in REPLAY_STATUSES
        assert vector.expected_reason in REPLAY_REASONS
        assert vector.expected_g153_calls in {0, 1}
        if vector.expected_g153_calls == 0:
            assert vector.expected_status == "CANONICAL_BUNDLE_REPLAY_INPUT_INVALID"
        else:
            assert vector.expected_status in {
                "CANONICAL_BUNDLE_REPLAY_RESULT_INVALID",
                "CANONICAL_BUNDLE_REPLAY_MISMATCH",
            }


def test_matched_replay_is_distinct_from_canonical_readiness() -> None:
    matched_outcomes = tuple(vector.expected_outcome for vector in ORACLE_VECTORS)

    assert "BLOCKED" in matched_outcomes
    assert "INPUT_INVALID" in matched_outcomes
    assert "SAFE_FAILURE" in matched_outcomes
    assert "CANONICAL_BUNDLE_REPLAY_MATCHED" == REPLAY_STATUSES[0]
    assert all(vector.canonical_status != REPLAY_STATUSES[0] for vector in ORACLE_VECTORS)


def test_nonmatched_result_contract_is_fresh_empty_and_sanitized() -> None:
    safe_unavailable = MappingProxyType(
        {
            "registry_version": "unavailable",
            "pipeline_contract_version": "unavailable",
            "policy_profile_version": "unavailable",
            "case_id": "unavailable",
            "fixture_id": "unavailable",
            "canonical_summary": MappingProxyType({}),
            "canonical_block_reasons": (),
            "canonical_warning_codes": (),
        }
    )

    assert set(safe_unavailable) == {
        "registry_version",
        "pipeline_contract_version",
        "policy_profile_version",
        "case_id",
        "fixture_id",
        "canonical_summary",
        "canonical_block_reasons",
        "canonical_warning_codes",
    }
    assert all(safe_unavailable[name] == "unavailable" for name in RESULT_FIELDS[1:6])
    assert not (set(safe_unavailable) & FORBIDDEN_RESULT_FIELDS)


def test_real_fixture_anchor_runs_g153_to_genuine_g151_without_mutation() -> None:
    fixture_before = _fixture_state()

    result = pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=FIXTURE_DIR.parent,
        bundle_dir=FIXTURE_DIR,
        now_utc=REFERENCE_TIME,
    )
    result_snapshot = deepcopy(result)

    assert _fixture_state() == fixture_before
    assert result == result_snapshot
    assert type(result) is dict
    assert set(result) == G151_SUMMARY_KEYS
    assert result["passed"] is True
    assert result["status_code"] == summary_adapter.CANONICAL_DIAGNOSTICS_SUMMARY_READY
    assert result["block_reasons"] == []
    assert result["warning_reasons"] == []
    assert _freeze_contract_value(result) == READY_G151_SUMMARY
    assert RESULT_CASE_VECTORS[0].result.canonical_summary == READY_G151_SUMMARY
    for field_name, expected in G151_SAFETY_FLAGS.items():
        assert result[field_name] is expected
    _assert_no_forbidden_content(result)


def test_real_fixture_anchor_is_repeatable_for_the_fixed_reference_time() -> None:
    first = pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=FIXTURE_DIR.parent,
        bundle_dir=FIXTURE_DIR,
        now_utc=REFERENCE_TIME,
    )
    second = pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=FIXTURE_DIR.parent,
        bundle_dir=FIXTURE_DIR,
        now_utc=REFERENCE_TIME,
    )

    assert first == second
    assert first is not second


def test_contract_vectors_are_frozen_and_do_not_claim_runtime_delivery() -> None:
    with pytest.raises(FrozenInstanceError):
        ORACLE_VECTORS[0].expected_outcome = "BLOCKED"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        PUBLIC_READY_CASE.case_id = "replacement"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        READY_REGISTRY_RECORD.expected_outcome = "BLOCKED"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        RESULT_CASE_VECTORS[0].result.passed = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        CALLER_OVERRIDE_VECTORS[0].expected_g153_calls = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        CASE_SHAPE_VECTORS[0].accepted = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        INVALID_EVIDENCE_VECTORS[0].expected_g153_calls = 1  # type: ignore[misc]

    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "tests, implementation, integration, activation, and verification" in contract
    assert "This document is a contract, not runtime evidence" in contract


def test_ast_has_no_replay_runtime_or_ambient_io_imports() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert not any("replay_runner" in name for name in imported_modules)
    assert not any("api" in name.split(".") for name in imported_modules)
    assert not any("filesystem_reader" in name for name in imported_modules)
    assert not any("data_quality_gate" in name for name in imported_modules)
    assert imported_modules.isdisjoint({"os", "socket", "subprocess", "tempfile"})


def test_contract_result_has_exact_safety_flags_and_no_free_text_field() -> None:
    assert dict(RESULT_SAFETY_FLAGS) == {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
    }
    assert "deterministic_observations" not in RESULT_FIELDS
    assert not (set(RESULT_FIELDS) & FORBIDDEN_RESULT_FIELDS)


def _class_fields(contract: str, class_name: str) -> tuple[str, ...]:
    match = re.search(
        rf"class {class_name}:\n(?P<body>(?:    [a-z_]+: [^\n]+\n)+)",
        contract,
    )
    assert match is not None
    return tuple(
        line.strip().split(":", maxsplit=1)[0]
        for line in match.group("body").splitlines()
    )


def _registry_fields(contract: str) -> tuple[str, ...]:
    match = re.search(
        r"Each registry entry owns, as one immutable record:\n\n```text\n"
        r"(?P<body>.*?)\n```",
        contract,
        flags=re.DOTALL,
    )
    assert match is not None
    return tuple(match.group("body").splitlines())


def _fixture_state() -> dict[str, tuple[bytes, int]]:
    return {
        filename: (
            (FIXTURE_DIR / filename).read_bytes(),
            (FIXTURE_DIR / filename).stat().st_mtime_ns,
        )
        for filename in FIXTURE_FILENAMES
    }


def _freeze_contract_value(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _freeze_contract_value(child))
            for key, child in value.items()
        )
    if type(value) is list:
        return tuple(_freeze_contract_value(child) for child in value)
    return value


def _assert_no_forbidden_content(value: object) -> None:
    if isinstance(value, dict):
        assert {str(key).casefold() for key in value}.isdisjoint(
            {key.casefold() for key in FORBIDDEN_RESULT_FIELDS}
        )
        for child in value.values():
            _assert_no_forbidden_content(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_no_forbidden_content(child)
    elif isinstance(value, str):
        serialized = json.dumps(value).casefold()
        assert str(FIXTURE_DIR).casefold() not in serialized
