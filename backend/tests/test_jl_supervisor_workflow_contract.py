"""Static workflow contract tests for the bounded JL Supervisor Skill."""

from __future__ import annotations

from pathlib import Path
import re
import tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPOSITORY_ROOT / "AGENTS.md"
JLGO_PATH = REPOSITORY_ROOT / ".agents" / "skills" / "jlgo" / "SKILL.md"
SUPERVISOR_DIR = REPOSITORY_ROOT / ".agents" / "skills" / "jl-supervisor"
SUPERVISOR_SKILL_PATH = SUPERVISOR_DIR / "SKILL.md"
SUPERVISOR_METADATA_PATH = SUPERVISOR_DIR / "agents" / "openai.yaml"
REVIEWER_PATH = (
    REPOSITORY_ROOT / ".codex" / "agents" / "jl-supervisor-reviewer.toml"
)
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "jl_supervisor_single_work_order_contract.md"
)

REQUIRED_WORKFLOW_FILES = (
    SUPERVISOR_SKILL_PATH,
    SUPERVISOR_METADATA_PATH,
    REVIEWER_PATH,
    CONTRACT_PATH,
)
MODEL_GATE_LABELS = ("NORMAL_ALLOWED", "PRO_REQUIRED", "STOP_UNCERTAIN")
HIGH_RISK_TERMS = (
    "real MT4",
    "RiskGate",
    "PositionSizing",
    "ExecutionGate",
    "TradePlanSchema",
    "MQL4",
    "EA",
    "GoLiveGate",
)
REVIEW_OUTCOMES = (
    "PASS",
    "PASS WITH FOLLOW-UP",
    "FIX BEFORE MERGE",
    "NO-GO",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def test_required_supervisor_files_exist() -> None:
    assert all(path.is_file() for path in REQUIRED_WORKFLOW_FILES)


def test_supervisor_frontmatter_has_exact_internal_name() -> None:
    text = _read(SUPERVISOR_SKILL_PATH)
    frontmatter = text.split("---", 2)[1]

    assert re.search(r"(?m)^name:\s*jl-supervisor\s*$", frontmatter)
    assert "one bounded" in frontmatter.casefold()
    assert "explicit user invocation" in frontmatter.casefold()


def test_supervisor_metadata_disables_implicit_invocation() -> None:
    text = _read(SUPERVISOR_METADATA_PATH)

    assert 'display_name: "巨龙监督"' in text
    assert "allow_implicit_invocation: false" in text
    assert "$jl-supervisor" in text
    assert "merge" in text.casefold()
    assert "tag" in text.casefold()


def test_reviewer_agent_is_independent_readonly_and_model_inheriting() -> None:
    with REVIEWER_PATH.open("rb") as file:
        reviewer = tomllib.load(file)

    assert reviewer["name"] == "jl_supervisor_reviewer"
    assert reviewer["model_reasoning_effort"] == "high"
    assert reviewer["sandbox_mode"] == "read-only"
    assert "model" not in reviewer
    assert "independent" in reviewer["description"].casefold()
    assert "does not modify files" in reviewer["description"].casefold()


def test_reviewer_instructions_require_evidence_and_fixed_outcomes() -> None:
    with REVIEWER_PATH.open("rb") as file:
        instructions = tomllib.load(file)["developer_instructions"]
    normalized = _normalized(instructions)

    assert "agents.md" in normalized
    assert "actual git diff" in normalized
    assert "frozen work order" in normalized
    assert "developer self-assessment" in normalized
    assert re.search(
        r"missing(?:\s+\w+){0,3}\s+evidence.*(?:must not|cannot).*pass",
        normalized,
    )
    assert all(outcome in instructions for outcome in REVIEW_OUTCOMES)
    assert all(
        term in normalized
        for term in ("do not modify", "do not commit", "do not push", "do not merge")
    )
    assert "do not tag" in normalized


def test_model_gate_has_three_classes_and_deterministic_priority() -> None:
    combined = _read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH)

    assert all(label in combined for label in MODEL_GATE_LABELS)
    assert "STOP_UNCERTAIN > PRO_REQUIRED > NORMAL_ALLOWED" in combined


def test_high_risk_capabilities_require_pro_before_writes() -> None:
    combined = _read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH)
    normalized = _normalized(combined)

    assert all(term.casefold() in normalized for term in HIGH_RISK_TERMS)
    assert "before" in normalized
    assert "branch" in normalized
    assert "file" in normalized
    assert "pro_required" in normalized


def test_supervisor_has_at_most_two_non_amended_revision_rounds() -> None:
    combined = _normalized(_read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH))

    assert "at most two" in combined or "最多两轮" in combined
    assert "ordinary new commit" in combined or "普通新 commit" in combined
    assert "amend" in combined
    assert "force push" in combined
    assert "weaken" in combined or "弱化" in combined


def test_supervisor_never_merges_pushes_main_tags_deploys_or_activates() -> None:
    combined = _normalized(_read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH))

    for boundary in (
        "no merge",
        "no push main",
        "no tag",
        "no deploy",
        "no activation",
    ):
        assert boundary in combined
    assert "automatic demo" in combined
    assert "live trading" in combined
    assert "second work order" in combined


def test_final_merge_authorization_card_is_complete_and_non_executing() -> None:
    combined = _read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH)

    assert "【Supervisor 执行卡】" in combined
    for field in (
        "Invocation mode",
        "PREFLIGHT result",
        "ModelGate classification",
        "Diff / grep / scope evidence",
        "Stop reason",
    ):
        assert field in combined
    assert "【最终合并授权卡】" in combined
    for field in (
        "Base main",
        "Work branch",
        "Head commit",
        "Exact modified files",
        "Test evidence",
        "Independent review conclusion",
        "Revision rounds used",
        "User approval required",
    ):
        assert field in combined
    assert "Merge performed: no" in combined
    assert "Tag created: no" in combined


def test_reviewer_unavailable_never_becomes_self_pass() -> None:
    combined = _normalized(_read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH))

    assert "reviewer" in combined
    assert "unavailable" in combined or "不可用" in combined
    assert "manual jl-review" in combined or "手工 jl-review" in combined
    assert "must not self-assign pass" in combined or "不得自行 pass" in combined


def test_agents_defines_a_bounded_supervisor_exception() -> None:
    text = _read(AGENTS_PATH)
    normalized = _normalized(text)

    assert "jl-supervisor" in text
    assert "有界例外" in text
    assert "normal_allowed" in normalized
    assert "pro_required" in normalized
    assert "最多两轮" in text
    assert "独立" in text and "reviewer" in normalized
    assert "merge" in normalized and "tag" in normalized


def test_jlgo_routes_to_supervisor_only_under_safe_conditions() -> None:
    text = _read(JLGO_PATH)
    normalized = _normalized(text)

    assert "$jl-supervisor" in text
    for condition in (
        "clean synchronized main",
        "active unmerged",
        "exact file scope",
        "modelgate",
        "stop_uncertain",
    ):
        assert condition in normalized
    assert "explicit" in normalized and "approval" in normalized


def test_supervisor_does_not_treat_existing_skills_as_nested_functions() -> None:
    combined = _normalized(_read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH))

    assert "not a nested skill caller" in combined or "不是嵌套 skill" in combined
    assert "runtime actually activated" in combined or "运行时确实激活" in combined


def test_supervisor_has_no_persistent_state_file() -> None:
    forbidden_suffixes = {".json", ".db", ".sqlite", ".log"}
    forbidden = [
        path
        for path in REPOSITORY_ROOT.rglob("*supervisor*")
        if path.is_file() and path.suffix.casefold() in forbidden_suffixes
    ]

    assert forbidden == []


def test_existing_trading_and_risk_policy_is_preserved() -> None:
    text = _read(AGENTS_PATH)

    for invariant in (
        "Demo-only / Read-only",
        "当前所有交易由用户手动确认和下单",
        "杠杆上限：10 倍",
        "账户权益的 1%",
        "账户权益的 3%",
        "亚洲时段",
        "不允许隔夜持仓",
        "DataQualityGate",
        "GoLiveGate",
        "当前不允许自动下单",
    ):
        assert invariant in text


def test_contract_freezes_one_order_one_branch_and_resource_limits() -> None:
    combined = _normalized(_read(SUPERVISOR_SKILL_PATH) + _read(CONTRACT_PATH))

    assert "one work order" in combined
    assert "one work branch" in combined
    assert "resource" in combined
    assert "progress json" in combined
    assert "persistent runtime log" in combined
