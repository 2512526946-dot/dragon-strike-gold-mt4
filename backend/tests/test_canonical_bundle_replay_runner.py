from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path
from typing import Any

import pytest

from app.services import canonical_bundle_replay_runner as replay_runner
from app.services import demo_readonly_canonical_diagnostics_pipeline as pipeline


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
FIXTURE_DIR = FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
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
SAFETY_FLAGS = {
    "read_only": True,
    "demo_only": True,
    "is_tradable": False,
    "can_execute": False,
    "is_execution_instruction": False,
    "allowed_to_call_ea": False,
}
FORBIDDEN_TEXT = (
    "raw_payload",
    "checksum",
    "traceback",
    "exception_text",
    "execution_payload",
)


class _StringSubclass(str):
    pass


def test_public_types_and_function_signature_are_exact_and_frozen() -> None:
    assert tuple(field.name for field in fields(replay_runner.CanonicalBundleReplayCaseV1)) == (
        PUBLIC_CASE_FIELDS
    )
    assert tuple(field.name for field in fields(replay_runner.CanonicalBundleReplayResultV1)) == (
        RESULT_FIELDS
    )
    assert tuple(inspect.signature(replay_runner.run_canonical_bundle_replay_case).parameters) == (
        "replay_case",
    )
    parameter = inspect.signature(
        replay_runner.run_canonical_bundle_replay_case
    ).parameters["replay_case"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY

    replay_case = _ready_case()
    with pytest.raises(FrozenInstanceError):
        replay_case.case_id = "replacement"  # type: ignore[misc]
    assert replay_runner.CanonicalBundleReplayCaseV1.__slots__ == PUBLIC_CASE_FIELDS
    assert replay_runner.CanonicalBundleReplayResultV1.__slots__ == RESULT_FIELDS


def test_server_owned_registry_fixes_source_clock_policy_and_oracle() -> None:
    assert type(replay_runner._REGISTRY) is tuple
    assert len(replay_runner._REGISTRY) == 1
    record = replay_runner._REGISTRY[0]

    assert tuple(field.name for field in fields(record)) == (
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
    assert record.registry_version == replay_runner.REGISTRY_VERSION
    assert record.allowed_root == FIXTURE_ROOT
    assert record.bundle_dir == FIXTURE_DIR
    assert record.reference_time_utc == REFERENCE_TIME
    assert record.previous_identity is None
    assert record.pipeline_contract_version == replay_runner.PIPELINE_CONTRACT_VERSION
    assert record.policy_profile_version == replay_runner.POLICY_PROFILE_VERSION
    assert record.expected_outcome == "READY"
    assert record.expected_status_code == "CANONICAL_DIAGNOSTICS_SUMMARY_READY"
    assert record.expected_block_reasons == ()
    assert record.expected_warning_codes == ()


def test_matched_ready_uses_one_exact_call_and_returns_detached_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready_summary = _build_summary()
    ready_before = deepcopy(ready_summary)
    calls: list[dict[str, object]] = []

    def _spy(**kwargs: object) -> dict[str, Any]:
        calls.append(kwargs)
        return ready_summary

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    replay_case = _ready_case()
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=replay_case)

    assert calls == [
        {
            "allowed_root": FIXTURE_ROOT,
            "bundle_dir": FIXTURE_DIR,
            "now_utc": REFERENCE_TIME,
        }
    ]
    assert result.passed is True
    assert result.status_code == replay_runner.CANONICAL_BUNDLE_REPLAY_MATCHED
    assert result.replay_reason_codes == ()
    assert result.canonical_block_reasons == ()
    assert result.canonical_warning_codes == ()
    assert result.canonical_summary == ready_summary
    assert result.canonical_summary is not ready_summary
    assert ready_summary == ready_before
    assert replay_case == _ready_case()
    _assert_exact_result(result)
    _assert_identity_available(result)


def test_repeated_matched_runs_are_equal_with_fresh_summary_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready_summary = _build_summary()
    calls = 0

    def _spy(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return deepcopy(ready_summary)

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    first = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())
    second = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 2
    assert first == second
    assert first is not second
    assert first.canonical_summary is not second.canonical_summary


@pytest.mark.parametrize(
    "replay_case",
    [
        object(),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version="wrong",
            case_id="canonical_docs_ready",
            fixture_id="canonical_docs_fixture_v1",
        ),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
            case_id="Unknown",
            fixture_id="canonical_docs_fixture_v1",
        ),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
            case_id="a" * 64,
            fixture_id="canonical_docs_fixture_v1",
        ),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
            case_id=_StringSubclass("canonical_docs_ready"),
            fixture_id="canonical_docs_fixture_v1",
        ),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
            case_id="unknown_case",
            fixture_id="canonical_docs_fixture_v1",
        ),
        replay_runner.CanonicalBundleReplayCaseV1(
            replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
            case_id="canonical_docs_ready",
            fixture_id="unknown_fixture",
        ),
    ],
)
def test_invalid_public_case_fails_before_pipeline_without_echo(
    replay_case: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def _unexpected(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {}

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _unexpected,
    )
    result = replay_runner.run_canonical_bundle_replay_case(  # type: ignore[arg-type]
        replay_case=replay_case,
    )

    assert calls == 0
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
        reason=replay_runner.REPLAY_CASE_INPUT_INVALID,
        identity_available=False,
    )


def test_case_subclass_and_caller_override_are_rejected() -> None:
    class _CaseSubclass(replay_runner.CanonicalBundleReplayCaseV1):
        pass

    candidate = _CaseSubclass(
        replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=candidate)

    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
        reason=replay_runner.REPLAY_CASE_INPUT_INVALID,
        identity_available=False,
    )
    with pytest.raises(TypeError):
        replay_runner.run_canonical_bundle_replay_case(  # type: ignore[call-arg]
            replay_case=_ready_case(),
            allowed_root=FIXTURE_ROOT,
        )


@pytest.mark.parametrize(
    "invalid_registry",
    [
        (replace(replay_runner._REGISTRY[0], registry_version="wrong"),),
        (
            replace(
                replay_runner._REGISTRY[0],
                case_id=_StringSubclass("canonical_docs_ready"),
            ),
        ),
        (
            replace(
                replay_runner._REGISTRY[0],
                expected_outcome="READY_WITH_WARNINGS",
                expected_status_code=(
                    "CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS"
                ),
                expected_warning_codes=("IDEMPOTENT_REPEAT", "IDEMPOTENT_REPEAT"),
            ),
        ),
        (
            replace(
                replay_runner._REGISTRY[0],
                expected_outcome="BLOCKED",
                expected_status_code="CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED",
                expected_block_reasons=("READER_DATA_STALE",),
                expected_warning_codes=("SEQUENCE_GAP", "IDEMPOTENT_REPEAT"),
            ),
        ),
        (
            replace(
                replay_runner._REGISTRY[0],
                expected_outcome="READY_WITH_WARNINGS",
                expected_status_code=(
                    "CANONICAL_DIAGNOSTICS_SUMMARY_READY_WITH_WARNINGS"
                ),
                expected_warning_codes=("UNKNOWN_WARNING",),
            ),
        ),
        (
            replace(
                replay_runner._REGISTRY[0],
                allowed_root=FIXTURE_ROOT.parent,
            ),
        ),
        (
            replace(
                replay_runner._REGISTRY[0],
                reference_time_utc=REFERENCE_TIME.replace(tzinfo=None),
            ),
        ),
        (replay_runner._REGISTRY[0], replay_runner._REGISTRY[0]),
    ],
)
def test_invalid_registry_fails_before_pipeline_with_unavailable_identity(
    invalid_registry: tuple[object, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    monkeypatch.setattr(replay_runner, "_REGISTRY", invalid_registry)

    def _unexpected(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {}

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _unexpected,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 0
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID,
        reason=replay_runner.REPLAY_CASE_REGISTRY_INVALID,
        identity_available=False,
    )


def test_unsafe_or_reordered_g151_result_is_rejected_after_one_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready = _build_summary()
    reordered = dict(reversed(tuple(ready.items())))
    calls = 0

    def _spy(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return reordered

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 1
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_RESULT_INVALID,
        reason=replay_runner.REPLAY_CASE_RESULT_INVALID,
        identity_available=True,
    )


def test_safe_blocked_summary_maps_to_mismatch_without_leaking_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blocked = _build_summary(now_utc=REFERENCE_TIME + timedelta(hours=1))
    assert blocked["status_code"] == "CANONICAL_DIAGNOSTICS_SUMMARY_BLOCKED"
    calls = 0

    def _spy(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return blocked

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 1
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_MISMATCH,
        reason=replay_runner.REPLAY_CASE_EXPECTATION_MISMATCH,
        identity_available=True,
    )


def test_pipeline_exception_is_sanitized_after_one_call_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def _raise(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise RuntimeError("private path raw_payload checksum")

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _raise,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 1
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE,
        reason=replay_runner.REPLAY_CASE_EXCEPTION_SANITIZED,
        identity_available=True,
    )


def test_pre_registry_exception_is_sanitized_without_pipeline_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def _registry_raises(value: object) -> bool:
        raise RuntimeError("private registry exception")

    def _unexpected(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {}

    monkeypatch.setattr(replay_runner, "_registry_is_safe", _registry_raises)
    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _unexpected,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 0
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE,
        reason=replay_runner.REPLAY_CASE_EXCEPTION_SANITIZED,
        identity_available=False,
    )


def test_validator_exception_is_sanitized_after_one_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready = _build_summary()
    calls = 0

    def _spy(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return ready

    def _validator_raises(*, canonical_summary: object) -> bool:
        raise RuntimeError("private validator exception")

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    monkeypatch.setattr(
        replay_runner.validator,
        "is_safe_demo_readonly_canonical_diagnostics_summary",
        _validator_raises,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 1
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE,
        reason=replay_runner.REPLAY_CASE_EXCEPTION_SANITIZED,
        identity_available=True,
    )


def test_post_call_registry_drift_is_result_invalid_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready = _build_summary()
    calls = 0

    def _spy(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        replacement = tuple([*replay_runner._REGISTRY])
        assert replacement is not replay_runner._REGISTRY
        monkeypatch.setattr(replay_runner, "_REGISTRY", replacement)
        return ready

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    result = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert calls == 1
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_RESULT_INVALID,
        reason=replay_runner.REPLAY_CASE_RESULT_INVALID,
        identity_available=True,
    )


def test_post_call_public_case_drift_is_result_invalid_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready = _build_summary()
    replay_case = _ready_case()
    calls = 0

    def _spy(**kwargs: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        object.__setattr__(replay_case, "case_id", "changed_during_call")
        return ready

    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        _spy,
    )
    try:
        result = replay_runner.run_canonical_bundle_replay_case(
            replay_case=replay_case,
        )
    finally:
        object.__setattr__(replay_case, "case_id", "canonical_docs_ready")

    assert calls == 1
    _assert_failure(
        result,
        status=replay_runner.CANONICAL_BUNDLE_REPLAY_RESULT_INVALID,
        reason=replay_runner.REPLAY_CASE_RESULT_INVALID,
        identity_available=True,
    )


def test_every_failure_returns_a_fresh_empty_plain_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        replay_runner.pipeline,
        "build_demo_readonly_canonical_diagnostics_summary",
        lambda **kwargs: {},
    )
    first = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())
    second = replay_runner.run_canonical_bundle_replay_case(replay_case=_ready_case())

    assert type(first.canonical_summary) is dict
    assert type(second.canonical_summary) is dict
    assert first.canonical_summary == second.canonical_summary == {}
    assert first.canonical_summary is not second.canonical_summary


def test_production_module_has_only_approved_runtime_dependencies() -> None:
    source_path = Path(replay_runner.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert not any("filesystem_reader" in name for name in imported)
    assert not any("data_quality_gate" in name for name in imported)
    assert not any("summary_adapter" in name for name in imported)
    assert not any("docs_fixture" in name for name in imported)
    assert not any("api" in name.split(".") for name in imported)
    assert imported.isdisjoint(
        {"os", "socket", "subprocess", "tempfile", "requests", "httpx"}
    )
    assert "sorted(" not in source
    assert ".sort(" not in source
    assert "open(" not in source
    assert "getenv" not in source
    assert "environ" not in source


def _ready_case() -> replay_runner.CanonicalBundleReplayCaseV1:
    return replay_runner.CanonicalBundleReplayCaseV1(
        replay_contract_version=replay_runner.REPLAY_CONTRACT_VERSION,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
    )


def _build_summary(
    *,
    now_utc: datetime = REFERENCE_TIME,
) -> dict[str, Any]:
    return pipeline.build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=FIXTURE_ROOT,
        bundle_dir=FIXTURE_DIR,
        now_utc=now_utc,
    )


def _assert_exact_result(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    assert type(result) is replay_runner.CanonicalBundleReplayResultV1
    assert tuple(field.name for field in fields(result)) == RESULT_FIELDS
    assert type(result.canonical_summary) is dict
    assert type(result.replay_reason_codes) is tuple
    assert type(result.canonical_block_reasons) is tuple
    assert type(result.canonical_warning_codes) is tuple
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
    for codes in (
        result.replay_reason_codes,
        result.canonical_block_reasons,
        result.canonical_warning_codes,
    ):
        assert all(type(code) is str for code in codes)
        assert len(codes) == len(set(codes))
    for field_name, expected in SAFETY_FLAGS.items():
        assert getattr(result, field_name) is expected
    lowered = repr(result).lower()
    assert not any(text in lowered for text in FORBIDDEN_TEXT)


def _assert_failure(
    result: replay_runner.CanonicalBundleReplayResultV1,
    *,
    status: str,
    reason: str,
    identity_available: bool,
) -> None:
    _assert_exact_result(result)
    assert result.passed is False
    assert result.status_code == status
    assert result.replay_reason_codes == (reason,)
    assert result.canonical_summary == {}
    assert result.canonical_block_reasons == ()
    assert result.canonical_warning_codes == ()
    if identity_available:
        _assert_identity_available(result)
    else:
        assert (
            result.registry_version,
            result.pipeline_contract_version,
            result.policy_profile_version,
            result.case_id,
            result.fixture_id,
        ) == ("unavailable",) * 5


def _assert_identity_available(
    result: replay_runner.CanonicalBundleReplayResultV1,
) -> None:
    assert result.registry_version == replay_runner.REGISTRY_VERSION
    assert result.pipeline_contract_version == replay_runner.PIPELINE_CONTRACT_VERSION
    assert result.policy_profile_version == replay_runner.POLICY_PROFILE_VERSION
    assert result.case_id == "canonical_docs_ready"
    assert result.fixture_id == "canonical_docs_fixture_v1"
