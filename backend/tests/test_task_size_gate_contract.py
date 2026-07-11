"""Immutable contract vectors for the future repository TaskSizeGate.

These tests deliberately do not import or implement a TaskSizeGate evaluator.
They lock the approved vocabulary, boundary cases, decision combinations, and
standard work-order fields that a later production implementation must satisfy.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "task_size_gate_and_standard_work_order_contract.md"
)
AGENTS_PATH = REPOSITORY_ROOT / "AGENTS.md"
SUPERVISOR_SKILL_PATH = (
    REPOSITORY_ROOT / ".agents" / "skills" / "jl-supervisor" / "SKILL.md"
)

TASK_SIZES = ("XS", "S", "M", "L", "XL")
TASK_DECISIONS = (
    "ALLOW_SINGLE_WORK_ORDER",
    "SPLIT_REQUIRED",
    "STOP_UNCERTAIN",
)
MODEL_GATE_RESULTS = ("NORMAL_ALLOWED", "PRO_REQUIRED", "STOP_UNCERTAIN")
SUPERVISOR_ELIGIBILITY = (
    "ELIGIBLE",
    "CONDITIONAL_PRO_RESUME",
    "NOT_ELIGIBLE",
)
CAPABILITY_LAYERS = (
    "POLICY",
    "CONTRACT",
    "TESTS",
    "IMPLEMENTATION",
    "INTEGRATION",
    "ACTIVATION",
    "VERIFICATION",
)

HOUR_BOUNDARY_VECTORS = (
    MappingProxyType({"upper_bound": 1, "expected_task_size": "XS"}),
    MappingProxyType({"upper_bound": 2, "expected_task_size": "XS"}),
    MappingProxyType({"upper_bound": 3, "expected_task_size": "S"}),
    MappingProxyType({"upper_bound": 8, "expected_task_size": "S"}),
    MappingProxyType({"upper_bound": 9, "expected_task_size": "M"}),
    MappingProxyType({"upper_bound": 16, "expected_task_size": "M"}),
    MappingProxyType({"upper_bound": 17, "expected_task_size": "L"}),
    MappingProxyType({"upper_bound": 40, "expected_task_size": "L"}),
    MappingProxyType({"upper_bound": 41, "expected_task_size": "XL"}),
)
FILE_BOUNDARY_VECTORS = (
    MappingProxyType({"file_count": 1, "expected_task_size": "XS"}),
    MappingProxyType({"file_count": 2, "expected_task_size": "S"}),
    MappingProxyType({"file_count": 3, "expected_task_size": "S"}),
    MappingProxyType({"file_count": 4, "expected_task_size": "M"}),
    MappingProxyType({"file_count": 5, "expected_task_size": "M"}),
    MappingProxyType({"file_count": 6, "expected_task_size": "L"}),
    MappingProxyType({"file_count": 10, "expected_task_size": "L"}),
    MappingProxyType({"file_count": 11, "expected_task_size": "XL"}),
)
LAYER_BOUNDARY_VECTORS = (
    MappingProxyType(
        {
            "layers": ("TESTS",),
            "adjacent": True,
            "expected_task_size": "XS",
        }
    ),
    MappingProxyType(
        {
            "layers": ("TESTS", "IMPLEMENTATION"),
            "adjacent": True,
            "expected_task_size": "M",
        }
    ),
    MappingProxyType(
        {
            "layers": ("CONTRACT", "IMPLEMENTATION"),
            "adjacent": False,
            "expected_task_size": "L",
        }
    ),
    MappingProxyType(
        {
            "layers": ("TESTS", "IMPLEMENTATION", "INTEGRATION"),
            "adjacent": True,
            "expected_task_size": "L",
        }
    ),
    MappingProxyType(
        {
            "layers": (
                "CONTRACT",
                "TESTS",
                "IMPLEMENTATION",
                "INTEGRATION",
            ),
            "adjacent": True,
            "expected_task_size": "XL",
        }
    ),
)

DECISION_VECTOR_KEYS = frozenset(
    {
        "case_id",
        "hours_upper_bound",
        "file_count",
        "layers",
        "layers_adjacent",
        "objective_count",
        "high_risk_reasons",
        "cross_package_activation",
        "size_classifiable",
        "other_required_evidence_known",
        "current_maturity",
        "target_maturity",
        "maturity_reason",
        "expected_task_size",
        "expected_task_decision",
        "expected_model_gate",
        "expected_supervisor_eligibility",
    }
)
DECISION_VECTORS = (
    MappingProxyType(
        {
            "case_id": "small_normal_tests_only",
            "hours_upper_bound": 6,
            "file_count": 3,
            "layers": ("TESTS",),
            "layers_adjacent": True,
            "objective_count": 1,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "CONTRACT_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "contract vectors",
            "expected_task_size": "S",
            "expected_task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "expected_model_gate": "NORMAL_ALLOWED",
            "expected_supervisor_eligibility": "ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "conservative_file_maximum",
            "hours_upper_bound": 1,
            "file_count": 4,
            "layers": ("TESTS",),
            "layers_adjacent": True,
            "objective_count": 1,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "CONTRACT_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "contract vectors",
            "expected_task_size": "M",
            "expected_task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "expected_model_gate": "NORMAL_ALLOWED",
            "expected_supervisor_eligibility": "NOT_ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "non_adjacent_layers",
            "hours_upper_bound": 4,
            "file_count": 2,
            "layers": ("CONTRACT", "IMPLEMENTATION"),
            "layers_adjacent": False,
            "objective_count": 1,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "CONTRACT_ONLY",
            "target_maturity": "IMPLEMENTED",
            "maturity_reason": "non-adjacent transition",
            "expected_task_size": "L",
            "expected_task_decision": "SPLIT_REQUIRED",
            "expected_model_gate": "NORMAL_ALLOWED",
            "expected_supervisor_eligibility": "NOT_ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "multiple_independent_objectives",
            "hours_upper_bound": 4,
            "file_count": 2,
            "layers": ("TESTS",),
            "layers_adjacent": True,
            "objective_count": 2,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "CONTRACT_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "multiple objectives must split",
            "expected_task_size": "L",
            "expected_task_decision": "SPLIT_REQUIRED",
            "expected_model_gate": "NORMAL_ALLOWED",
            "expected_supervisor_eligibility": "NOT_ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "small_high_risk_contract",
            "hours_upper_bound": 6,
            "file_count": 1,
            "layers": ("CONTRACT",),
            "layers_adjacent": True,
            "objective_count": 1,
            "high_risk_reasons": ("canonical_protocol",),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "POLICY_ONLY",
            "target_maturity": "CONTRACT_ONLY",
            "maturity_reason": "canonical protocol contract",
            "expected_task_size": "S",
            "expected_task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "expected_model_gate": "PRO_REQUIRED",
            "expected_supervisor_eligibility": "CONDITIONAL_PRO_RESUME",
        }
    ),
    MappingProxyType(
        {
            "case_id": "cross_package_activation",
            "hours_upper_bound": 8,
            "file_count": 3,
            "layers": ("INTEGRATION", "ACTIVATION"),
            "layers_adjacent": True,
            "objective_count": 1,
            "high_risk_reasons": ("execution_chain",),
            "cross_package_activation": True,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "INTEGRATED",
            "target_maturity": "ACTIVATED",
            "maturity_reason": "cross-package activation",
            "expected_task_size": "XL",
            "expected_task_decision": "SPLIT_REQUIRED",
            "expected_model_gate": "PRO_REQUIRED",
            "expected_supervisor_eligibility": "NOT_ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "unclassifiable_size",
            "hours_upper_bound": None,
            "file_count": None,
            "layers": (),
            "layers_adjacent": False,
            "objective_count": 1,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": False,
            "other_required_evidence_known": False,
            "current_maturity": "CONTRACT_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "insufficient evidence",
            "expected_task_size": None,
            "expected_task_decision": "STOP_UNCERTAIN",
            "expected_model_gate": "STOP_UNCERTAIN",
            "expected_supervisor_eligibility": "NOT_ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "known_size_unknown_dependency",
            "hours_upper_bound": 6,
            "file_count": 3,
            "layers": ("TESTS",),
            "layers_adjacent": True,
            "objective_count": 1,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": False,
            "current_maturity": "CONTRACT_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "dependency evidence unknown",
            "expected_task_size": "S",
            "expected_task_decision": "STOP_UNCERTAIN",
            "expected_model_gate": "STOP_UNCERTAIN",
            "expected_supervisor_eligibility": "NOT_ELIGIBLE",
        }
    ),
    MappingProxyType(
        {
            "case_id": "maturity_preserving_hardening",
            "hours_upper_bound": 4,
            "file_count": 1,
            "layers": ("TESTS",),
            "layers_adjacent": True,
            "objective_count": 1,
            "high_risk_reasons": (),
            "cross_package_activation": False,
            "size_classifiable": True,
            "other_required_evidence_known": True,
            "current_maturity": "TESTS_ONLY",
            "target_maturity": "TESTS_ONLY",
            "maturity_reason": "maturity-preserving test hardening",
            "expected_task_size": "S",
            "expected_task_decision": "ALLOW_SINGLE_WORK_ORDER",
            "expected_model_gate": "NORMAL_ALLOWED",
            "expected_supervisor_eligibility": "ELIGIBLE",
        }
    ),
)

STANDARD_WORK_ORDER_SECTIONS = (
    "【Work order identity】",
    "【Git checkpoint】",
    "【Gate decisions】",
    "【Exact scope】",
    "【Technical contract】",
    "【Verification】",
    "【Delivery】",
    "【WBS accounting】",
    "【Final report】",
)
STANDARD_WORK_ORDER_FIELDS = (
    "One objective",
    "WBS package IDs",
    "Current maturity",
    "Target maturity",
    "Base branch and immutable base commit",
    "TaskSize evidence by hours, files, and layers",
    "Task decision",
    "ModelGate reasons",
    "Supervisor eligibility",
    "Files allowed to add",
    "Forbidden capabilities and policy changes",
    "Fail-closed semantics",
    "Input immutability and output-safety requirements",
    "Targeted tests",
    "Full backend tests",
    "Isolation grep",
    "Exact file-scope check",
    "Stop conditions",
    "Ordinary commit message",
    "Merge, tag, deployment, and activation boundaries",
    "Expected remaining-hour movement",
    "Required `【下一步操作卡】`",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def test_contract_is_present_and_runtime_remains_unimplemented() -> None:
    text = _read(CONTRACT_PATH)
    normalized = _normalized(text)

    assert "status: wf-4b contract-only design" in normalized
    assert "does not implement tasksizegate" in normalized
    assert "no tasksizegate parser, evaluator, or command exists" in normalized
    assert "no automated size gate is active" in normalized


def test_exact_vocabularies_are_locked() -> None:
    assert TASK_SIZES == ("XS", "S", "M", "L", "XL")
    assert TASK_DECISIONS == (
        "ALLOW_SINGLE_WORK_ORDER",
        "SPLIT_REQUIRED",
        "STOP_UNCERTAIN",
    )
    assert MODEL_GATE_RESULTS == (
        "NORMAL_ALLOWED",
        "PRO_REQUIRED",
        "STOP_UNCERTAIN",
    )
    assert SUPERVISOR_ELIGIBILITY == (
        "ELIGIBLE",
        "CONDITIONAL_PRO_RESUME",
        "NOT_ELIGIBLE",
    )
    assert CAPABILITY_LAYERS == (
        "POLICY",
        "CONTRACT",
        "TESTS",
        "IMPLEMENTATION",
        "INTEGRATION",
        "ACTIVATION",
        "VERIFICATION",
    )


def test_contract_contains_exact_task_size_threshold_rows() -> None:
    text = _read(CONTRACT_PATH)
    normalized = _normalized(text)

    expected_rows = (
        "| `XS` | 2 hours | 1 | 1 |",
        "| `S` | 8 hours | 3 | 1 |",
        "| `M` | 16 hours | 5 | 2 adjacent layers |",
        "| `L` | 40 hours | 10 | 3 layers |",
        "| `XL` | More than 40 hours | More than 10 | More than 3 layers |",
    )
    assert all(row in text for row in expected_rows)
    assert "the final tasksize is the largest result" in normalized


def test_hour_boundary_vectors_are_exact_and_complete() -> None:
    assert tuple(
        (vector["upper_bound"], vector["expected_task_size"])
        for vector in HOUR_BOUNDARY_VECTORS
    ) == (
        (1, "XS"),
        (2, "XS"),
        (3, "S"),
        (8, "S"),
        (9, "M"),
        (16, "M"),
        (17, "L"),
        (40, "L"),
        (41, "XL"),
    )


def test_file_boundary_vectors_are_exact_and_complete() -> None:
    assert tuple(
        (vector["file_count"], vector["expected_task_size"])
        for vector in FILE_BOUNDARY_VECTORS
    ) == (
        (1, "XS"),
        (2, "S"),
        (3, "S"),
        (4, "M"),
        (5, "M"),
        (6, "L"),
        (10, "L"),
        (11, "XL"),
    )


def test_layer_boundary_vectors_cover_adjacency_and_cardinality() -> None:
    assert tuple(
        (
            vector["layers"],
            vector["adjacent"],
            vector["expected_task_size"],
        )
        for vector in LAYER_BOUNDARY_VECTORS
    ) == (
        (("TESTS",), True, "XS"),
        (("TESTS", "IMPLEMENTATION"), True, "M"),
        (("CONTRACT", "IMPLEMENTATION"), False, "L"),
        (("TESTS", "IMPLEMENTATION", "INTEGRATION"), True, "L"),
        (("CONTRACT", "TESTS", "IMPLEMENTATION", "INTEGRATION"), True, "XL"),
    )


def test_decision_vectors_have_exact_shape_and_unique_case_ids() -> None:
    assert all(set(vector) == DECISION_VECTOR_KEYS for vector in DECISION_VECTORS)
    case_ids = tuple(vector["case_id"] for vector in DECISION_VECTORS)

    assert len(case_ids) == len(set(case_ids))
    assert set(case_ids) == {
        "small_normal_tests_only",
        "conservative_file_maximum",
        "non_adjacent_layers",
        "multiple_independent_objectives",
        "small_high_risk_contract",
        "cross_package_activation",
        "unclassifiable_size",
        "known_size_unknown_dependency",
        "maturity_preserving_hardening",
    }


def test_decision_vectors_lock_conservative_size_and_split_rules() -> None:
    by_case = {vector["case_id"]: vector for vector in DECISION_VECTORS}

    assert by_case["conservative_file_maximum"]["expected_task_size"] == "M"
    assert by_case["conservative_file_maximum"][
        "expected_supervisor_eligibility"
    ] == "NOT_ELIGIBLE"
    assert by_case["non_adjacent_layers"]["expected_task_size"] == "L"
    assert by_case["non_adjacent_layers"]["expected_task_decision"] == (
        "SPLIT_REQUIRED"
    )
    assert by_case["multiple_independent_objectives"]["expected_task_size"] == (
        "L"
    )
    assert by_case["multiple_independent_objectives"][
        "expected_task_decision"
    ] == "SPLIT_REQUIRED"
    assert by_case["cross_package_activation"]["expected_task_size"] == "XL"
    assert by_case["cross_package_activation"]["expected_task_decision"] == (
        "SPLIT_REQUIRED"
    )


def test_null_is_only_for_unclassifiable_stop_uncertain() -> None:
    null_cases = [
        vector for vector in DECISION_VECTORS if vector["expected_task_size"] is None
    ]

    assert len(null_cases) == 1
    assert null_cases[0]["case_id"] == "unclassifiable_size"
    assert null_cases[0]["size_classifiable"] is False
    assert null_cases[0]["expected_task_decision"] == "STOP_UNCERTAIN"
    assert null_cases[0]["expected_model_gate"] == "STOP_UNCERTAIN"
    assert all(
        vector["expected_task_size"] is not None
        for vector in DECISION_VECTORS
        if vector["expected_task_decision"] != "STOP_UNCERTAIN"
    )


def test_known_size_is_preserved_when_other_evidence_is_uncertain() -> None:
    vector = next(
        vector
        for vector in DECISION_VECTORS
        if vector["case_id"] == "known_size_unknown_dependency"
    )

    assert vector["size_classifiable"] is True
    assert vector["other_required_evidence_known"] is False
    assert vector["expected_task_size"] == "S"
    assert vector["expected_task_decision"] == "STOP_UNCERTAIN"
    assert vector["expected_model_gate"] == "STOP_UNCERTAIN"
    assert vector["expected_supervisor_eligibility"] == "NOT_ELIGIBLE"


def test_high_risk_model_gate_does_not_inflate_task_size() -> None:
    vector = next(
        vector
        for vector in DECISION_VECTORS
        if vector["case_id"] == "small_high_risk_contract"
    )

    assert vector["expected_task_size"] == "S"
    assert vector["expected_task_decision"] == "ALLOW_SINGLE_WORK_ORDER"
    assert vector["expected_model_gate"] == "PRO_REQUIRED"
    assert vector["expected_supervisor_eligibility"] == "CONDITIONAL_PRO_RESUME"


def test_supervisor_eligibility_matrix_is_locked() -> None:
    by_case = {vector["case_id"]: vector for vector in DECISION_VECTORS}

    assert by_case["small_normal_tests_only"][
        "expected_supervisor_eligibility"
    ] == "ELIGIBLE"
    assert by_case["small_high_risk_contract"][
        "expected_supervisor_eligibility"
    ] == "CONDITIONAL_PRO_RESUME"
    assert all(
        by_case[case_id]["expected_supervisor_eligibility"] == "NOT_ELIGIBLE"
        for case_id in (
            "conservative_file_maximum",
            "non_adjacent_layers",
            "multiple_independent_objectives",
            "cross_package_activation",
            "unclassifiable_size",
            "known_size_unknown_dependency",
        )
    )


def test_maturity_changing_and_preserving_vectors_are_distinct() -> None:
    by_case = {vector["case_id"]: vector for vector in DECISION_VECTORS}
    changing = by_case["small_normal_tests_only"]
    preserving = by_case["maturity_preserving_hardening"]

    assert changing["current_maturity"] == "CONTRACT_ONLY"
    assert changing["target_maturity"] == "TESTS_ONLY"
    assert preserving["current_maturity"] == preserving["target_maturity"]
    assert "maturity-preserving" in preserving["maturity_reason"]
    assert preserving["expected_task_decision"] == "ALLOW_SINGLE_WORK_ORDER"


def test_standard_work_order_sections_and_fields_are_complete() -> None:
    text = _read(CONTRACT_PATH)

    assert all(section in text for section in STANDARD_WORK_ORDER_SECTIONS)
    assert all(field in text for field in STANDARD_WORK_ORDER_FIELDS)
    assert "Omitted fields must be written explicitly as `not applicable`" in text


def test_contract_remains_aligned_with_model_gate_and_supervisor_policy() -> None:
    contract = _normalized(_read(CONTRACT_PATH))
    agents = _normalized(_read(AGENTS_PATH))
    supervisor = _normalized(_read(SUPERVISOR_SKILL_PATH))

    assert "stop_uncertain > pro_required > normal_allowed" in contract
    assert "stop_uncertain > pro_required > normal_allowed" in supervisor
    assert all(result.casefold() in supervisor for result in MODEL_GATE_RESULTS)
    assert "normal_allowed" in agents
    assert "pro_required" in agents
    assert "no merge" in supervisor
    assert "no tag" in supervisor
    assert "no activation" in supervisor


def test_vectors_and_source_are_immutable_and_have_no_runtime_dependency() -> None:
    with pytest.raises(TypeError):
        HOUR_BOUNDARY_VECTORS[0]["expected_task_size"] = "XL"
    with pytest.raises(TypeError):
        DECISION_VECTORS[0]["expected_task_decision"] = "STOP_UNCERTAIN"

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
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imported_modules <= {"__future__", "ast", "pathlib", "types", "pytest"}
    assert "app" not in imported_modules
    assert "os" not in imported_modules
    assert "subprocess" not in imported_modules
    assert called_attributes.isdisjoint(
        {"write_text", "write_bytes", "unlink", "rename", "replace"}
    )
