"""Static vectors for the non-activating verification transition contract.

These tests deliberately do not import or call the production TaskSizeGate,
Skills, or a future workflow adapter. They lock the WF-4M contract only and do
not prove runtime integration, activation, verification, or G174 authority.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re
from types import MappingProxyType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "task_size_gate_non_activating_verification_transition_contract.md"
)

MATURITIES = (
    "NOT_STARTED",
    "POLICY_ONLY",
    "CONTRACT_ONLY",
    "TESTS_ONLY",
    "IMPLEMENTED",
    "INTEGRATED",
    "ACTIVATED",
    "VERIFIED",
)
NORMAL_FORWARD_TRANSITIONS = (
    ("NOT_STARTED", "POLICY_ONLY"),
    ("POLICY_ONLY", "CONTRACT_ONLY"),
    ("CONTRACT_ONLY", "TESTS_ONLY"),
    ("TESTS_ONLY", "IMPLEMENTED"),
    ("IMPLEMENTED", "INTEGRATED"),
    ("INTEGRATED", "ACTIVATED"),
    ("ACTIVATED", "VERIFIED"),
)
NON_ACTIVATING_TRANSITION = MappingProxyType(
    {
        "current_maturity": "INTEGRATED",
        "target_maturity": "VERIFIED",
        "maturity_reason": "non-activating verification",
        "objective_count": 1,
        "capability_layers": ("VERIFICATION",),
        "cross_package_activation": False,
    }
)
EXPECTED_AFFECTED_SURFACES = ("offline_verification_evidence",)
EXPECTED_RISK_AND_POLICY_IMPACTS = (
    "verification_does_not_grant_activation",
    "no_runtime_authority_change",
    "no_trading_or_execution_authority",
)
EXPECTED_PROHIBITED_CAPABILITIES = (
    "merge",
    "push_main",
    "tag",
    "deployment",
    "activation",
    "runtime_source_change",
    "mt4_access",
    "ea_call",
    "order_execution",
    "trading",
    "second_work_order",
)

VALID_TRANSITION_VECTORS = (
    MappingProxyType(
        {
            "case_id": "non_activating_verification_normal",
            **NON_ACTIVATING_TRANSITION,
            "affected_surfaces": EXPECTED_AFFECTED_SURFACES,
            "risk_and_policy_impacts": EXPECTED_RISK_AND_POLICY_IMPACTS,
            "prohibited_capabilities": EXPECTED_PROHIBITED_CAPABILITIES,
            "model_gate": "NORMAL_ALLOWED",
            "expected_decision": "ALLOW_SINGLE_WORK_ORDER",
            "expected_eligibility": "ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "non_activating_verification_pro",
            **NON_ACTIVATING_TRANSITION,
            "affected_surfaces": EXPECTED_AFFECTED_SURFACES,
            "risk_and_policy_impacts": EXPECTED_RISK_AND_POLICY_IMPACTS,
            "prohibited_capabilities": EXPECTED_PROHIBITED_CAPABILITIES,
            "model_gate": "PRO_REQUIRED",
            "expected_decision": "ALLOW_SINGLE_WORK_ORDER",
            "expected_eligibility": "CONDITIONAL_PRO_RESUME",
        }
    ),
)

PRESERVED_TRANSITION_VECTORS = tuple(
    MappingProxyType(
        {
            "current_maturity": current,
            "target_maturity": target,
            "expected_decision": "ALLOW_SINGLE_WORK_ORDER",
        }
    )
    for current, target in NORMAL_FORWARD_TRANSITIONS
) + (
    MappingProxyType(
        {
            "current_maturity": "TESTS_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "maturity-preserving test hardening",
            "expected_decision": "ALLOW_SINGLE_WORK_ORDER",
        }
    ),
)

INVALID_TRANSITION_VECTORS = (
    *tuple(
        MappingProxyType(
            {
                "case_id": f"lower_{current.casefold()}_to_verified",
                "current_maturity": current,
                "target_maturity": "VERIFIED",
                "expected_decision": "STOP_UNCERTAIN",
            }
        )
        for current in MATURITIES[:5]
    ),
    *tuple(
        MappingProxyType(
            {
                "case_id": f"backward_{target.casefold()}_to_{current.casefold()}",
                "current_maturity": target,
                "target_maturity": current,
                "expected_decision": "STOP_UNCERTAIN",
            }
        )
        for current, target in NORMAL_FORWARD_TRANSITIONS
    ),
    MappingProxyType(
        {
            "case_id": "unrelated_not_started_to_contract",
            "current_maturity": "NOT_STARTED",
            "target_maturity": "CONTRACT_ONLY",
            "expected_decision": "STOP_UNCERTAIN",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unrelated_policy_to_tests",
            "current_maturity": "POLICY_ONLY",
            "target_maturity": "TESTS_ONLY",
            "expected_decision": "STOP_UNCERTAIN",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unrelated_tests_to_integrated",
            "current_maturity": "TESTS_ONLY",
            "target_maturity": "INTEGRATED",
            "expected_decision": "STOP_UNCERTAIN",
        }
    ),
)


class _StringSubclass(str):
    pass


INVALID_EXACT_TUPLE_VECTORS = (
    MappingProxyType(
        {
            "case_id": "missing_value",
            "field": "risk_and_policy_impacts",
            "value": EXPECTED_RISK_AND_POLICY_IMPACTS[:-1],
        }
    ),
    MappingProxyType(
        {
            "case_id": "extra_value",
            "field": "affected_surfaces",
            "value": EXPECTED_AFFECTED_SURFACES + ("extra_surface",),
        }
    ),
    MappingProxyType(
        {
            "case_id": "reordered_values",
            "field": "risk_and_policy_impacts",
            "value": tuple(reversed(EXPECTED_RISK_AND_POLICY_IMPACTS)),
        }
    ),
    MappingProxyType(
        {
            "case_id": "duplicate_value",
            "field": "prohibited_capabilities",
            "value": EXPECTED_PROHIBITED_CAPABILITIES + ("merge",),
        }
    ),
    MappingProxyType(
        {
            "case_id": "alias_value",
            "field": "prohibited_capabilities",
            "value": ("merge_to_main",) + EXPECTED_PROHIBITED_CAPABILITIES[1:],
        }
    ),
    MappingProxyType(
        {
            "case_id": "case_changed_value",
            "field": "affected_surfaces",
            "value": ("OFFLINE_VERIFICATION_EVIDENCE",),
        }
    ),
    MappingProxyType(
        {
            "case_id": "subclassed_value",
            "field": "affected_surfaces",
            "value": (_StringSubclass("offline_verification_evidence"),),
        }
    ),
    MappingProxyType(
        {
            "case_id": "wrong_container",
            "field": "affected_surfaces",
            "value": frozenset(EXPECTED_AFFECTED_SURFACES),
        }
    ),
    MappingProxyType(
        {
            "case_id": "meaningless_nonempty_value",
            "field": "risk_and_policy_impacts",
            "value": ("something_safe",),
        }
    ),
)

INVALID_TRANSITION_EVIDENCE_VECTORS = (
    MappingProxyType(
        {
            "case_id": "missing_reason",
            "field": "maturity_reason",
            "value": None,
        }
    ),
    MappingProxyType(
        {
            "case_id": "aliased_reason",
            "field": "maturity_reason",
            "value": "verification without activation",
        }
    ),
    MappingProxyType(
        {
            "case_id": "subclassed_reason",
            "field": "maturity_reason",
            "value": _StringSubclass("non-activating verification"),
        }
    ),
    MappingProxyType(
        {
            "case_id": "extra_layer",
            "field": "capability_layers",
            "value": ("VERIFICATION", "ACTIVATION"),
        }
    ),
    MappingProxyType(
        {
            "case_id": "wrong_layer",
            "field": "capability_layers",
            "value": ("ACTIVATION",),
        }
    ),
    MappingProxyType(
        {
            "case_id": "zero_objectives",
            "field": "objective_count",
            "value": 0,
        }
    ),
    MappingProxyType(
        {
            "case_id": "multiple_objectives",
            "field": "objective_count",
            "value": 2,
        }
    ),
    MappingProxyType(
        {
            "case_id": "cross_package_activation",
            "field": "cross_package_activation",
            "value": True,
        }
    ),
)

CALLER_CHECKPOINT_VECTORS = (
    MappingProxyType(
        {
            "case_id": "jlgo_scope_ambiguous",
            "checkpoint": "JLGO_PLANNING",
            "failure": "scope_ambiguous",
            "expected_evaluator_calls": 0,
            "expected_writes": False,
            "expected_result": "STOP_UNCERTAIN",
            "expected_next_skill": None,
        }
    ),
    MappingProxyType(
        {
            "case_id": "pre_write_runtime_scope_drift",
            "checkpoint": "PRE_WRITE",
            "failure": "runtime_authority_surface_present",
            "expected_evaluator_calls": 0,
            "expected_writes": False,
            "expected_result": "STOP_UNCERTAIN",
            "expected_next_skill": None,
        }
    ),
    MappingProxyType(
        {
            "case_id": "review_runtime_scope_drift",
            "checkpoint": "JL_REVIEW",
            "failure": "cumulative_diff_contains_runtime_authority",
            "expected_result": "NO-GO",
            "expected_merge_recommendation": False,
            "expected_next_skill": None,
        }
    ),
)


def _read_contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _fenced_block_after(text: str, marker: str, language: str) -> str:
    _, separator, remainder = text.partition(marker)
    assert separator, f"missing contract marker: {marker}"
    match = re.search(
        rf"```{re.escape(language)}\r?\n(.*?)\r?\n```",
        remainder,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing {language} block after: {marker}"
    return match.group(1)


def _contract_tuple_assignments() -> MappingProxyType[str, tuple[str, ...]]:
    block = _fenced_block_after(
        _read_contract(),
        "### 4.1 Exact canonical evidence values",
        "python",
    )
    tree = ast.parse(block)
    assignments: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        assert isinstance(node, ast.Assign)
        assert len(node.targets) == 1
        assert isinstance(node.targets[0], ast.Name)
        value = ast.literal_eval(node.value)
        assert type(value) is tuple
        assert all(type(item) is str for item in value)
        assignments[node.targets[0].id] = value
    return MappingProxyType(assignments)


def test_maturity_vocabulary_is_exactly_eight_values() -> None:
    block = _fenced_block_after(
        _read_contract(),
        "The maturity vocabulary remains exactly these eight values",
        "text",
    )

    assert tuple(block.splitlines()) == MATURITIES
    assert len(MATURITIES) == 8
    assert len(set(MATURITIES)) == 8
    assert "ACTIVATED_AND_VERIFIED" not in MATURITIES


def test_non_activating_transition_and_exact_evidence_are_locked() -> None:
    contract = _read_contract()
    assignments = _contract_tuple_assignments()

    assert _fenced_block_after(
        contract,
        "The only new maturity-changing form is:",
        "text",
    ) == "INTEGRATED -> VERIFIED"
    assert NON_ACTIVATING_TRANSITION == {
        "current_maturity": "INTEGRATED",
        "target_maturity": "VERIFIED",
        "maturity_reason": "non-activating verification",
        "objective_count": 1,
        "capability_layers": ("VERIFICATION",),
        "cross_package_activation": False,
    }
    assert assignments == {
        "NON_ACTIVATING_VERIFICATION_AFFECTED_SURFACES": (
            "offline_verification_evidence",
        ),
        "NON_ACTIVATING_VERIFICATION_RISK_AND_POLICY_IMPACTS": (
            "verification_does_not_grant_activation",
            "no_runtime_authority_change",
            "no_trading_or_execution_authority",
        ),
        "NON_ACTIVATING_VERIFICATION_PROHIBITED_CAPABILITIES": (
            "merge",
            "push_main",
            "tag",
            "deployment",
            "activation",
            "runtime_source_change",
            "mt4_access",
            "ea_call",
            "order_execution",
            "trading",
            "second_work_order",
        ),
    }


def test_valid_vectors_use_exact_built_in_values_and_expected_gate_outcomes() -> None:
    assert tuple(vector["case_id"] for vector in VALID_TRANSITION_VECTORS) == (
        "non_activating_verification_normal",
        "non_activating_verification_pro",
    )
    for vector in VALID_TRANSITION_VECTORS:
        assert type(vector["current_maturity"]) is str
        assert type(vector["target_maturity"]) is str
        assert type(vector["maturity_reason"]) is str
        assert type(vector["objective_count"]) is int
        assert type(vector["capability_layers"]) is tuple
        assert type(vector["cross_package_activation"]) is bool
        assert vector["affected_surfaces"] == EXPECTED_AFFECTED_SURFACES
        assert vector["risk_and_policy_impacts"] == (
            EXPECTED_RISK_AND_POLICY_IMPACTS
        )
        assert vector["prohibited_capabilities"] == (
            EXPECTED_PROHIBITED_CAPABILITIES
        )
        assert vector["expected_decision"] == "ALLOW_SINGLE_WORK_ORDER"

    assert tuple(
        (vector["model_gate"], vector["expected_eligibility"])
        for vector in VALID_TRANSITION_VECTORS
    ) == (
        ("NORMAL_ALLOWED", "ELIGIBLE"),
        ("PRO_REQUIRED", "CONDITIONAL_PRO_RESUME"),
    )


def test_normal_and_maturity_preserving_transitions_remain_locked() -> None:
    contract_block = _fenced_block_after(
        _read_contract(),
        "The future rule preserves the existing normal forward transitions:",
        "text",
    )
    parsed = tuple(
        tuple(part.strip() for part in line.split("->"))
        for line in contract_block.splitlines()
    )

    assert parsed == NORMAL_FORWARD_TRANSITIONS
    assert tuple(
        (vector["current_maturity"], vector["target_maturity"])
        for vector in PRESERVED_TRANSITION_VECTORS[:-1]
    ) == NORMAL_FORWARD_TRANSITIONS
    assert PRESERVED_TRANSITION_VECTORS[-1] == {
        "current_maturity": "TESTS_ONLY",
        "target_maturity": "TESTS_ONLY",
        "maturity_reason": "maturity-preserving test hardening",
        "expected_decision": "ALLOW_SINGLE_WORK_ORDER",
    }


def test_lower_backward_and_unrelated_jump_vectors_fail_closed() -> None:
    case_ids = tuple(vector["case_id"] for vector in INVALID_TRANSITION_VECTORS)

    assert len(case_ids) == len(set(case_ids)) == 15
    assert {
        vector["current_maturity"]
        for vector in INVALID_TRANSITION_VECTORS
        if vector["target_maturity"] == "VERIFIED"
    } == set(MATURITIES[:5])
    assert all(
        vector["expected_decision"] == "STOP_UNCERTAIN"
        for vector in INVALID_TRANSITION_VECTORS
    )


def test_invalid_exact_tuple_vectors_cover_every_required_failure_class() -> None:
    assert tuple(vector["case_id"] for vector in INVALID_EXACT_TUPLE_VECTORS) == (
        "missing_value",
        "extra_value",
        "reordered_values",
        "duplicate_value",
        "alias_value",
        "case_changed_value",
        "subclassed_value",
        "wrong_container",
        "meaningless_nonempty_value",
    )
    assert {
        vector["field"] for vector in INVALID_EXACT_TUPLE_VECTORS
    } == {
        "affected_surfaces",
        "risk_and_policy_impacts",
        "prohibited_capabilities",
    }
    assert type(INVALID_EXACT_TUPLE_VECTORS[6]["value"][0]) is not str
    assert type(INVALID_EXACT_TUPLE_VECTORS[7]["value"]) is not tuple


def test_invalid_transition_evidence_vectors_are_exact_and_fail_closed() -> None:
    assert tuple(
        vector["case_id"] for vector in INVALID_TRANSITION_EVIDENCE_VECTORS
    ) == (
        "missing_reason",
        "aliased_reason",
        "subclassed_reason",
        "extra_layer",
        "wrong_layer",
        "zero_objectives",
        "multiple_objectives",
        "cross_package_activation",
    )
    assert type(INVALID_TRANSITION_EVIDENCE_VECTORS[2]["value"]) is not str
    assert INVALID_TRANSITION_EVIDENCE_VECTORS[-1]["value"] is True
    assert "must fail closed under the existing\n`STOP_UNCERTAIN` behavior" in (
        _read_contract()
    )


def test_caller_scope_failures_lock_zero_call_no_write_and_review_no_go() -> None:
    by_case = {vector["case_id"]: vector for vector in CALLER_CHECKPOINT_VECTORS}

    for case_id in ("jlgo_scope_ambiguous", "pre_write_runtime_scope_drift"):
        vector = by_case[case_id]
        assert vector["expected_evaluator_calls"] == 0
        assert vector["expected_writes"] is False
        assert vector["expected_result"] == "STOP_UNCERTAIN"
        assert vector["expected_next_skill"] is None

    review = by_case["review_runtime_scope_drift"]
    assert review["expected_result"] == "NO-GO"
    assert review["expected_merge_recommendation"] is False
    assert review["expected_next_skill"] is None


def test_verified_never_grants_activation_or_runtime_authority() -> None:
    contract = _read_contract()

    assert "`VERIFIED` does not mean `ACTIVATED`" in contract
    assert "Verification evidence does not grant\nactivation" in contract
    for forbidden_authority in (
        "deployment",
        "MT4 access",
        "EA authority",
        "execution authority",
        "trading permission",
    ):
        assert forbidden_authority in contract
    assert "WF-4M does not authorize G174" in contract


def test_vectors_are_immutable_and_have_no_runtime_import_or_write_path() -> None:
    with pytest.raises(TypeError):
        VALID_TRANSITION_VECTORS[0]["target_maturity"] = "ACTIVATED"
    with pytest.raises(TypeError):
        CALLER_CHECKPOINT_VECTORS[0]["expected_evaluator_calls"] = 1

    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imported_modules <= {
        "__future__",
        "ast",
        "pathlib",
        "re",
        "types",
        "pytest",
    }
    assert "app" not in imported_modules
    assert "task_size_gate" not in imported_modules
    assert "evaluate_task_size_gate" not in called_names
    assert called_attributes.isdisjoint(
        {"write_text", "write_bytes", "unlink", "rename", "replace"}
    )


def test_static_vectors_do_not_claim_later_delivery_stages() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    contract = _read_contract()

    assert "do not prove runtime integration, activation, verification" in source
    assert "-> immutable contract vectors\n    -> production TaskSizeGate evaluator" in (
        contract
    )
    assert "-> JLGO planning propagation" in contract
    assert "-> jl-develop and jl-supervisor pre-write propagation" in contract
    assert "-> jl-review checkpoint propagation" in contract
    assert "-> re-plan the blocked G174 verification order" in contract
