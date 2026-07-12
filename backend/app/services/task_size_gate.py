from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


TASK_SIZES: Final = ("XS", "S", "M", "L", "XL")
TASK_DECISIONS: Final = (
    "ALLOW_SINGLE_WORK_ORDER",
    "SPLIT_REQUIRED",
    "STOP_UNCERTAIN",
)
MODEL_GATES: Final = ("NORMAL_ALLOWED", "PRO_REQUIRED", "STOP_UNCERTAIN")
SUPERVISOR_ELIGIBILITY_VALUES: Final = (
    "ELIGIBLE",
    "CONDITIONAL_PRO_RESUME",
    "NOT_ELIGIBLE",
)
CAPABILITY_MATURITIES: Final = (
    "NOT_STARTED",
    "POLICY_ONLY",
    "CONTRACT_ONLY",
    "TESTS_ONLY",
    "IMPLEMENTED",
    "INTEGRATED",
    "ACTIVATED",
    "VERIFIED",
)
CAPABILITY_LAYERS: Final = (
    "POLICY",
    "CONTRACT",
    "TESTS",
    "IMPLEMENTATION",
    "INTEGRATION",
    "ACTIVATION",
    "VERIFICATION",
)

ALLOW_SINGLE_WORK_ORDER = "ALLOW_SINGLE_WORK_ORDER"
SPLIT_REQUIRED = "SPLIT_REQUIRED"
STOP_UNCERTAIN = "STOP_UNCERTAIN"

NORMAL_ALLOWED = "NORMAL_ALLOWED"
PRO_REQUIRED = "PRO_REQUIRED"

ELIGIBLE = "ELIGIBLE"
CONDITIONAL_PRO_RESUME = "CONDITIONAL_PRO_RESUME"
NOT_ELIGIBLE = "NOT_ELIGIBLE"

INPUT_INVALID = "TASK_SIZE_GATE_INPUT_INVALID"
SIZE_UNCLASSIFIABLE = "TASK_SIZE_GATE_SIZE_UNCLASSIFIABLE"
UNKNOWN_EVIDENCE = "TASK_SIZE_GATE_UNKNOWN_EVIDENCE"
MODEL_STOP_UNCERTAIN = "TASK_SIZE_GATE_MODEL_STOP_UNCERTAIN"
CROSS_PACKAGE_ACTIVATION = "TASK_SIZE_GATE_CROSS_PACKAGE_ACTIVATION"
MULTIPLE_OBJECTIVES = "TASK_SIZE_GATE_MULTIPLE_OBJECTIVES"
NON_ADJACENT_LAYERS = "TASK_SIZE_GATE_NON_ADJACENT_LAYERS"
OVERSIZED = "TASK_SIZE_GATE_OVERSIZED"
SINGLE_WORK_ORDER_ALLOWED = "TASK_SIZE_GATE_SINGLE_WORK_ORDER_ALLOWED"
PRO_MODEL_REQUIRED = "TASK_SIZE_GATE_PRO_REQUIRED"

_TASK_SIZE_ORDER = {value: index for index, value in enumerate(TASK_SIZES)}
_LAYER_ORDER = {value: index for index, value in enumerate(CAPABILITY_LAYERS)}
_HEX_COMMIT = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True, slots=True)
class TaskSizeGateEvidence:
    objective: str
    objective_count: int
    wbs_package_ids: tuple[str, ...]
    current_maturity: str
    target_maturity: str
    maturity_reason: str
    base_branch: str
    base_main_commit: str
    work_branch: str
    commit_message: str
    push_destination: str
    stop_conditions: tuple[str, ...]
    estimated_engineering_hours_lower: int | None
    estimated_engineering_hours_upper: int | None
    allowed_files: tuple[str, ...]
    prohibited_files: tuple[str, ...]
    prohibited_capabilities: tuple[str, ...]
    capability_layers: tuple[str, ...]
    subsystem_boundaries: tuple[str, ...]
    affected_surfaces: tuple[str, ...]
    required_checks: tuple[str, ...]
    known_dependencies: tuple[str, ...]
    dependency_evidence_known: bool
    risk_and_policy_impacts: tuple[str, ...]
    high_risk_reasons: tuple[str, ...]
    model_gate: str
    model_gate_evidence: tuple[str, ...]
    unknowns: tuple[str, ...]
    cross_package_activation: bool


@dataclass(frozen=True, slots=True)
class TaskSizeGateResult:
    task_size: str | None
    task_decision: str
    model_gate: str
    supervisor_eligibility: str
    reason_codes: tuple[str, ...]


def evaluate_task_size_gate(*, evidence: object) -> TaskSizeGateResult:
    """Classify caller-owned work-order evidence without runtime side effects."""

    try:
        if type(evidence) is not TaskSizeGateEvidence:
            return _blocked_result(task_size=None, reason_code=INPUT_INVALID)

        task_size, size_inputs_valid = _classify_task_size(evidence)
        if not size_inputs_valid:
            return _blocked_result(task_size=None, reason_code=INPUT_INVALID)
        if task_size is None:
            return _blocked_result(task_size=None, reason_code=SIZE_UNCLASSIFIABLE)

        if not _non_size_evidence_is_valid(evidence):
            return _blocked_result(task_size=task_size, reason_code=INPUT_INVALID)
        if evidence.unknowns or not evidence.dependency_evidence_known:
            return _blocked_result(task_size=task_size, reason_code=UNKNOWN_EVIDENCE)
        if evidence.model_gate == STOP_UNCERTAIN:
            return _blocked_result(
                task_size=task_size,
                reason_code=MODEL_STOP_UNCERTAIN,
            )

        model_gate = (
            PRO_REQUIRED
            if evidence.cross_package_activation or evidence.high_risk_reasons
            else evidence.model_gate
        )
        reason_codes = _decision_reason_codes(
            evidence=evidence,
            task_size=task_size,
            model_gate=model_gate,
        )
        task_decision = (
            SPLIT_REQUIRED
            if any(
                code
                in {
                    CROSS_PACKAGE_ACTIVATION,
                    MULTIPLE_OBJECTIVES,
                    NON_ADJACENT_LAYERS,
                    OVERSIZED,
                }
                for code in reason_codes
            )
            else ALLOW_SINGLE_WORK_ORDER
        )

        return TaskSizeGateResult(
            task_size=task_size,
            task_decision=task_decision,
            model_gate=model_gate,
            supervisor_eligibility=_supervisor_eligibility(
                task_size=task_size,
                task_decision=task_decision,
                model_gate=model_gate,
            ),
            reason_codes=reason_codes,
        )
    except Exception:
        return _blocked_result(task_size=None, reason_code=INPUT_INVALID)


def _blocked_result(*, task_size: str | None, reason_code: str) -> TaskSizeGateResult:
    return TaskSizeGateResult(
        task_size=task_size,
        task_decision=STOP_UNCERTAIN,
        model_gate=STOP_UNCERTAIN,
        supervisor_eligibility=NOT_ELIGIBLE,
        reason_codes=(reason_code,),
    )


def _classify_task_size(
    evidence: TaskSizeGateEvidence,
) -> tuple[str | None, bool]:
    hour_size, hours_valid = _hour_size(
        lower=evidence.estimated_engineering_hours_lower,
        upper=evidence.estimated_engineering_hours_upper,
    )
    file_size, files_valid = _file_size(evidence.allowed_files)
    layer_size, layers_valid = _layer_size(evidence.capability_layers)
    if not all((hours_valid, files_valid, layers_valid)):
        return None, False
    if None in (hour_size, file_size, layer_size):
        return None, True

    task_size = max(
        (hour_size, file_size, layer_size),
        key=_TASK_SIZE_ORDER.__getitem__,
    )
    if type(evidence.objective_count) is int and evidence.objective_count > 1:
        task_size = _largest_size(task_size, "L")
    if evidence.cross_package_activation is True:
        task_size = "XL"
    return task_size, True


def _hour_size(*, lower: object, upper: object) -> tuple[str | None, bool]:
    if lower is None and upper is None:
        return None, True
    if type(lower) is not int or type(upper) is not int:
        return None, False
    if lower < 1 or upper < lower:
        return None, False
    if upper <= 2:
        return "XS", True
    if upper <= 8:
        return "S", True
    if upper <= 16:
        return "M", True
    if upper <= 40:
        return "L", True
    return "XL", True


def _file_size(files: object) -> tuple[str | None, bool]:
    if not _strict_string_tuple(files, allow_empty=True):
        return None, False
    if not files:
        return None, True
    if not all(_safe_relative_file(value) for value in files):
        return None, False
    count = len(files)
    if count == 1:
        return "XS", True
    if count <= 3:
        return "S", True
    if count <= 5:
        return "M", True
    if count <= 10:
        return "L", True
    return "XL", True


def _layer_size(layers: object) -> tuple[str | None, bool]:
    if not _strict_string_tuple(layers, allow_empty=True):
        return None, False
    if not layers:
        return None, True
    if any(value not in _LAYER_ORDER for value in layers):
        return None, False
    indexes = tuple(_LAYER_ORDER[value] for value in layers)
    if indexes != tuple(sorted(indexes)):
        return None, False
    count = len(layers)
    if count == 1:
        return "XS", True
    if count == 2:
        return ("M" if _layers_are_adjacent(indexes) else "L"), True
    if count == 3:
        return "L", True
    return "XL", True


def _non_size_evidence_is_valid(evidence: TaskSizeGateEvidence) -> bool:
    if not _plain_nonempty_string(evidence.objective):
        return False
    if type(evidence.objective_count) is not int or evidence.objective_count < 1:
        return False
    if not _strict_string_tuple(evidence.wbs_package_ids, allow_empty=False):
        return False
    if not all(re.fullmatch(r"W\d+", value) for value in evidence.wbs_package_ids):
        return False
    if type(evidence.current_maturity) is not str:
        return False
    if evidence.current_maturity not in CAPABILITY_MATURITIES:
        return False
    if type(evidence.target_maturity) is not str:
        return False
    if evidence.target_maturity not in CAPABILITY_MATURITIES:
        return False
    if not _valid_maturity_reason(evidence):
        return False
    if type(evidence.base_branch) is not str or evidence.base_branch != "main":
        return False
    if type(evidence.base_main_commit) is not str:
        return False
    if _HEX_COMMIT.fullmatch(evidence.base_main_commit) is None:
        return False
    if not _plain_nonempty_string(evidence.work_branch):
        return False
    if not evidence.work_branch.startswith("work/"):
        return False
    if not _plain_nonempty_string(evidence.commit_message):
        return False
    if type(evidence.push_destination) is not str:
        return False
    if evidence.push_destination != f"origin/{evidence.work_branch}":
        return False
    if not _strict_string_tuple(evidence.stop_conditions, allow_empty=False):
        return False
    if not _safe_relative_file_tuple(evidence.prohibited_files, allow_empty=True):
        return False
    required_tuples = (
        evidence.prohibited_capabilities,
        evidence.subsystem_boundaries,
        evidence.affected_surfaces,
        evidence.required_checks,
        evidence.risk_and_policy_impacts,
        evidence.model_gate_evidence,
    )
    if not all(_strict_string_tuple(value, allow_empty=False) for value in required_tuples):
        return False
    if not _strict_string_tuple(evidence.known_dependencies, allow_empty=True):
        return False
    if not _strict_string_tuple(evidence.high_risk_reasons, allow_empty=True):
        return False
    if not _strict_string_tuple(evidence.unknowns, allow_empty=True):
        return False
    if type(evidence.dependency_evidence_known) is not bool:
        return False
    if type(evidence.cross_package_activation) is not bool:
        return False
    if type(evidence.model_gate) is not str or evidence.model_gate not in MODEL_GATES:
        return False
    return True


def _valid_maturity_reason(evidence: TaskSizeGateEvidence) -> bool:
    if not _plain_nonempty_string(evidence.maturity_reason):
        return False
    if evidence.current_maturity != evidence.target_maturity:
        return True
    normalized = evidence.maturity_reason.casefold()
    return "hardening" in normalized or "maintenance" in normalized


def _decision_reason_codes(
    *,
    evidence: TaskSizeGateEvidence,
    task_size: str,
    model_gate: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence.cross_package_activation:
        reasons.append(CROSS_PACKAGE_ACTIVATION)
    if evidence.objective_count > 1:
        reasons.append(MULTIPLE_OBJECTIVES)
    layer_indexes = tuple(_LAYER_ORDER[value] for value in evidence.capability_layers)
    if len(layer_indexes) == 2 and not _layers_are_adjacent(layer_indexes):
        reasons.append(NON_ADJACENT_LAYERS)
    if task_size in {"L", "XL"}:
        reasons.append(OVERSIZED)
    if not reasons:
        reasons.append(SINGLE_WORK_ORDER_ALLOWED)
    if model_gate == PRO_REQUIRED:
        reasons.append(PRO_MODEL_REQUIRED)
    return tuple(reasons)


def _supervisor_eligibility(
    *,
    task_size: str,
    task_decision: str,
    model_gate: str,
) -> str:
    if task_decision != ALLOW_SINGLE_WORK_ORDER or task_size not in {"XS", "S"}:
        return NOT_ELIGIBLE
    if model_gate == NORMAL_ALLOWED:
        return ELIGIBLE
    if model_gate == PRO_REQUIRED:
        return CONDITIONAL_PRO_RESUME
    return NOT_ELIGIBLE


def _strict_string_tuple(value: object, *, allow_empty: bool) -> bool:
    if type(value) is not tuple:
        return False
    if not allow_empty and not value:
        return False
    if any(not _plain_nonempty_string(item) for item in value):
        return False
    return len(value) == len(set(value))


def _safe_relative_file_tuple(value: object, *, allow_empty: bool) -> bool:
    return _strict_string_tuple(value, allow_empty=allow_empty) and all(
        _safe_relative_file(item) for item in value
    )


def _safe_relative_file(value: str) -> bool:
    if value.startswith(("/", "\\")) or ":" in value:
        return False
    if any(token in value for token in ("*", "?", "[", "]")):
        return False
    return ".." not in value.replace("\\", "/").split("/")


def _plain_nonempty_string(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _layers_are_adjacent(indexes: tuple[int, ...]) -> bool:
    return all(right == left + 1 for left, right in zip(indexes, indexes[1:]))


def _largest_size(left: str, right: str) -> str:
    return left if _TASK_SIZE_ORDER[left] >= _TASK_SIZE_ORDER[right] else right
