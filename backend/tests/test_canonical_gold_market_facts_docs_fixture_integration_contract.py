from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from types import MappingProxyType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "implementation_plans"
    / "canonical_gold_market_facts_docs_fixture_integration_contract.md"
)
TEST_PATH = Path(__file__).resolve()


@dataclass(frozen=True, slots=True)
class AuthorityVector:
    field: str
    exact_value: str


@dataclass(frozen=True, slots=True)
class CallAccountingVector:
    outcome: str
    adapter_calls: int
    validator_calls: int
    sanitizer_calls: int


@dataclass(frozen=True, slots=True)
class OutcomeVector:
    name: str
    accounting_outcome: str
    expected_disposition: str
    source_available: bool
    accepted_unchanged: bool


@dataclass(frozen=True, slots=True)
class CallerOverrideVector:
    name: str
    attempted_override: str
    adapter_calls: int
    accepted: bool


PUBLIC_INTERFACE_LINES = (
    "def build_canonical_gold_market_facts_docs_fixture_source_v1(",
    ") -> CanonicalGoldMarketFactsSourceAdapterResultV1:",
    "    ...",
)

PUBLIC_EXPORTS = (
    "build_canonical_gold_market_facts_docs_fixture_source_v1",
)

PRIVATE_G182_IMPORTS = (
    "_AUTHORITY_TOKEN",
    "_CanonicalGoldMarketFactsSourceAuthorityV1",
    "_build_canonical_gold_market_facts_source_adapter_safe_failure_v1",
    "_is_safe_canonical_gold_market_facts_source_adapter_result_v1",
    "CanonicalGoldMarketFactsSourceAdapterResultV1",
    "build_server_owned_canonical_gold_market_facts_source_v1",
)

VALIDATOR_INTERFACE_LINES = (
    "def _is_safe_canonical_gold_market_facts_source_adapter_result_v1(",
    "    *,",
    "    result: object,",
    ") -> bool:",
    "    ...",
)

SANITIZER_INTERFACE_LINES = (
    "def _build_canonical_gold_market_facts_source_adapter_safe_failure_v1(",
    ") -> CanonicalGoldMarketFactsSourceAdapterResultV1:",
    "    ...",
)

PATH_AUTHORITY = MappingProxyType(
    {
        "repository_root_derivation": "Path(__file__).resolve().parents[3]",
        "allowed_root_suffix": "docs/architecture/fixtures",
        "bundle_dir_name": "canonical-mt4-demo-readonly-bundle-v1",
        "runtime_path_type": "exact concrete WindowsPath or PosixPath",
    }
)

FIXTURE_IDENTITY = (
    AuthorityVector("schema_version", '"1.0"'),
    AuthorityVector("bundle_id", '"demo-bundle-000000000001"'),
    AuthorityVector("sequence", "1"),
    AuthorityVector("canonical_symbol", '"XAUUSD"'),
    AuthorityVector("broker_symbol", '"GOLD"'),
)

AUTHORITY_FIELDS = (
    AuthorityVector(
        "authority_token",
        "Existing G182 module-private singleton identity",
    ),
    AuthorityVector("allowed_root", "Fixed path from section 5.1"),
    AuthorityVector("bundle_dir", "Fixed path from section 5.1"),
    AuthorityVector(
        "reference_time_utc",
        "Fixed exact UTC datetime from section 5.2",
    ),
    AuthorityVector("previous_identity", "`None`"),
    AuthorityVector("read_policy", "Exact policy values below"),
    AuthorityVector("filesystem_policy", "Exact policy values below"),
    AuthorityVector("data_quality_policy", "Exact policy values below"),
    AuthorityVector(
        "policy_profile_version",
        "`canonical_gold_market_facts_policy_v1`",
    ),
)

REFERENCE_TIME = "datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)"

READ_POLICY = MappingProxyType(
    {
        "writer_heartbeat_max_age_seconds": 15,
        "live_tick_max_age_seconds": 10,
        "latest_bars_max_age_seconds": 60,
        "symbol_spec_max_age_seconds": 86400,
        "account_snapshot_max_age_seconds": 30,
        "max_future_skew_seconds": 5,
    }
)

FILESYSTEM_POLICY = MappingProxyType(
    {
        "manifest_max_bytes": 65536,
        "live_tick_max_bytes": 32768,
        "latest_bars_max_bytes": 2097152,
        "symbol_spec_max_bytes": 65536,
        "account_snapshot_max_bytes": 131072,
        "max_manifest_consistency_retries": 0,
    }
)

DATA_QUALITY_POLICY = MappingProxyType(
    {"allow_upstream_warnings": False}
)

CALL_CHAIN = (
    "Confirm that its fixed constants, exact private imports, direct G182 "
    "callable, G182 validator, and G182 safe-failure constructor are available "
    "and unchanged.",
    "Construct fresh exact policy objects from section 5.3.",
    "Construct one fresh private G182 authority object from section 5.",
    "Freeze a scalar snapshot of the authority values for post-call comparison.",
    "Call `build_server_owned_canonical_gold_market_facts_source_v1` exactly "
    "once with only `authority=<fresh authority>`.",
    "Confirm the authority snapshot is unchanged. On drift, return one result "
    "from the G182 safe-failure constructor without validating or repairing "
    "the adapter result.",
    "Call the G182-owned result validator exactly once with only "
    "`result=<adapter result>`. If it returns exact `False` or raises, return "
    "one result from the G182 safe-failure constructor.",
    "Return a validated blocked result unchanged without inspecting or "
    "reclassifying its status or source internals.",
    "On validated READY, compare only the five fixed scalar fixture identity "
    "fields in section 5.1. On mismatch, return one result from the G182 "
    "safe-failure constructor; do not construct or repair a result locally.",
    "Return the validated exact adapter result only after all applicable "
    "checks pass.",
    "Release the private authority and any result-local references when the "
    "call stack unwinds.",
)

CALL_ACCOUNTING = (
    CallAccountingVector(
        "Fixed constant or authority construction invalid while sanitizer is available",
        0,
        0,
        1,
    ),
    CallAccountingVector(
        "G182 callable unavailable or changed before invocation",
        0,
        0,
        1,
    ),
    CallAccountingVector(
        "G182 validator unavailable or changed before invocation",
        0,
        0,
        1,
    ),
    CallAccountingVector(
        "G182 sanitizer unavailable or changed before invocation",
        0,
        0,
        0,
    ),
    CallAccountingVector("G182 invocation begins and raises", 1, 0, 1),
    CallAccountingVector("Post-call authority drift", 1, 0, 1),
    CallAccountingVector(
        "G182 returns an invalid or polluted result",
        1,
        1,
        1,
    ),
    CallAccountingVector(
        "G182 returns a validated blocked result",
        1,
        1,
        0,
    ),
    CallAccountingVector(
        "G182 returns validated READY with fixed identity mismatch",
        1,
        1,
        1,
    ),
    CallAccountingVector(
        "G182 returns validated READY for the fixed fixture",
        1,
        1,
        0,
    ),
)

OUTCOME_VECTORS = (
    OutcomeVector(
        "genuine_ready",
        "G182 returns validated READY for the fixed fixture",
        "return_validated_result",
        True,
        True,
    ),
    OutcomeVector(
        "valid_blocked",
        "G182 returns a validated blocked result",
        "return_validated_result",
        False,
        True,
    ),
    OutcomeVector(
        "invalid_result",
        "G182 returns an invalid or polluted result",
        "return_sanitized_failure",
        False,
        False,
    ),
    OutcomeVector(
        "adapter_exception",
        "G182 invocation begins and raises",
        "return_sanitized_failure",
        False,
        False,
    ),
    OutcomeVector(
        "identity_drift",
        "G182 returns validated READY with fixed identity mismatch",
        "return_sanitized_failure",
        False,
        False,
    ),
    OutcomeVector(
        "policy_or_authority_drift",
        "Post-call authority drift",
        "return_sanitized_failure",
        False,
        False,
    ),
    OutcomeVector(
        "dependency_drift",
        "G182 callable unavailable or changed before invocation",
        "return_sanitized_failure",
        False,
        False,
    ),
    OutcomeVector(
        "sanitizer_unavailable",
        "G182 sanitizer unavailable or changed before invocation",
        "integration_unavailable_no_source",
        False,
        False,
    ),
)

SANITIZED_FAILURE = MappingProxyType(
    {
        "status_code": "CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        "reason_codes": ("GOLD_SOURCE_EXCEPTION_SANITIZED",),
        "warning_codes": (),
        "source_available": False,
        "source": None,
    }
)

SAFETY_FLAGS = MappingProxyType(
    {
        "read_only": True,
        "demo_only": True,
        "is_tradable": False,
        "can_execute": False,
        "is_trading_permission": False,
        "is_execution_instruction": False,
        "allowed_to_call_ea": False,
        "allowed_to_modify_risk": False,
    }
)

CALLER_OVERRIDES = (
    CallerOverrideVector("path", "caller path", 0, False),
    CallerOverrideVector("clock", "caller time", 0, False),
    CallerOverrideVector("previous_identity", "caller identity", 0, False),
    CallerOverrideVector("policy", "caller policy", 0, False),
    CallerOverrideVector("dependency", "caller dependency", 0, False),
    CallerOverrideVector("source", "caller source", 0, False),
    CallerOverrideVector("oracle", "caller expected outcome", 0, False),
)

W1_OWNERSHIP = (
    "filesystem containment and symlink protection;",
    "file-size, JSON, manifest-consistency, and checksum checks;",
    "manifest and payload schema/value validation;",
    "manifest/payload identity equality;",
    "accepted-attempt token and capsule creation; and",
    "the reader/value/Gate status details consumed by G182.",
)

IMMUTABILITY_REQUIREMENTS = (
    "the checked-in fixture tree is byte-for-byte unchanged before and after "
    "the call without exposing digests in a public result;",
    "the fixed authority values and direct dependency identities are unchanged;",
    "repeated genuine executions return equal adapter results;",
    "every execution returns a fresh result object and a fresh detached source;",
    "nested source records and tuples are fresh, frozen, and detached;",
    "mutating or replacing any returned local reference cannot alter fixture "
    "assets, another result, or a later result; and",
    "no path, raw payload, checksum, exception text, traceback, internal source "
    "status, or private token appears in the public result or test diagnostics.",
)

FAIL_CLOSED_CONDITIONS = (
    "missing, extra, reordered, subclassed, aliased, mutable, or wrong-container "
    "fixed constants, policies, authority fields, result fields, source fields, "
    "or identity values;",
    "a caller-supplied path, clock, previous identity, policy, dependency, source, "
    "expected status, reason, warning, or oracle;",
    "private token, authority type, adapter callable, G182 validator, G182 "
    "sanitizer, fixture path, reference time, policy, or expected identity drift;",
    "dependency unavailability, authority-construction failure, G182 exception, "
    "invalid G182 result, READY identity mismatch, or post-call authority drift;",
    "warning-bearing, partial, unsafe, contradictory, or polluted output; or",
    "any attempt to use diagnostics, W5 ReplayRunner, runtime `data/`, environment, "
    "settings, network, database, cache, API, frontend, MT4, or EA state.",
)

ISOLATION_RULES = (
    "`demo_readonly_canonical_docs_fixture_diagnostics_summary_producer`;",
    "`canonical_bundle_replay_runner`;",
    "G151 diagnostics adapter or G153 diagnostics pipeline;",
    "G178 projector;",
    "API routers, settings, frontend, plugin, MT4, EA, strategy, risk, order, "
    "execution, or trading modules.",
)

REQUIRED_CONTRACT_VECTORS = (
    "the exact future module, single public function, zero-argument signature, "
    "return annotation, and `__all__` rule;",
    "exact private-import authority, G182 validator/sanitizer interfaces, and "
    "non-re-export rules;",
    "exact path derivation, fixture directory, reference time, previous identity, "
    "policy profile, read policy, filesystem policy, and Gate policy;",
    "exact fixture identity and W1 ownership boundary;",
    "zero/one G182 call accounting and no direct reader/Gate call;",
    "exact G182-owned adapter-result validation and sanitized failure envelope;",
    "genuine READY, valid G182 blocked, invalid result, exception, identity drift, "
    "policy drift, dependency drift, and post-call drift vectors;",
    "fixture, authority, result, and nested-source immutability requirements;",
    "repeated execution determinism and fresh-object requirements; and",
    "no diagnostics producer, W5 ReplayRunner, projector, ambient I/O, API, MT4, "
    "EA, order, execution, trading, activation, or verification claim.",
)

STAGED_DELIVERY = (
    "immutable tests-only vectors for this contract;",
    "the zero-argument production fixture integration boundary;",
    "genuine offline fixture integration evidence through W1 and G182;",
    "deterministic non-activating verification;",
    "separate contracts and delivery for later W6 facts and features; and",
    "a separately versioned ReplayRunner W6 stage before W7.",
)

FORBIDDEN_RUNTIME_IMPORTS = (
    "demo_readonly_canonical_docs_fixture_diagnostics_summary_producer",
    "canonical_bundle_replay_runner",
    "G178 projector",
)

SENSITIVE_OUTPUT_TERMS = (
    "path",
    "raw payload",
    "checksum",
    "exception text",
    "traceback",
    "internal source status",
    "private token",
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _section(text: str, start: str, end: str) -> str:
    start_index = text.index(start) + len(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def _fenced_block_lines(
    text: str,
    start: str,
    end: str,
    *,
    language: str,
) -> tuple[str, ...]:
    section = _section(text, start, end)
    opening = f"```{language}\n"
    block_start = section.index(opening) + len(opening)
    block_end = section.index("\n```", block_start)
    return tuple(section[block_start:block_end].splitlines())


def _markdown_table(
    text: str,
    start: str,
    end: str,
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    lines = tuple(
        line
        for line in _section(text, start, end).splitlines()
        if line.startswith("|")
    )
    rows = tuple(
        tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        for line in lines
    )
    assert len(rows) >= 2
    assert all(len(row) == len(rows[0]) for row in rows)
    assert all(
        cell and set(cell.replace(" ", "")) <= {"-", ":"}
        for cell in rows[1]
    )
    return rows[0], rows[2:]


def _bullet_items(text: str, start: str, end: str) -> tuple[str, ...]:
    items: list[str] = []
    current = ""
    for line in _section(text, start, end).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            if current:
                items.append(_normalize_whitespace(current))
            current = stripped[2:]
        elif current and stripped:
            current += " " + stripped
    if current:
        items.append(_normalize_whitespace(current))
    return tuple(items)


def _numbered_items(text: str, start: str, end: str) -> tuple[str, ...]:
    items: list[str] = []
    ordinals: list[int] = []
    current = ""
    for line in _section(text, start, end).splitlines():
        stripped = line.strip()
        marker, separator, content = stripped.partition(". ")
        if separator and marker.isascii() and marker.isdigit():
            if current:
                items.append(_normalize_whitespace(current))
            ordinals.append(int(marker))
            current = content
        elif current and stripped:
            current += " " + stripped
    if current:
        items.append(_normalize_whitespace(current))
    assert tuple(ordinals) == tuple(range(1, len(items) + 1))
    return tuple(items)


def test_vectors_are_frozen_closed_and_strictly_typed() -> None:
    with pytest.raises(FrozenInstanceError):
        FIXTURE_IDENTITY[0].field = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        CALL_ACCOUNTING[0].adapter_calls = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        OUTCOME_VECTORS[0].name = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        READ_POLICY["live_tick_max_age_seconds"] = 11  # type: ignore[index]

    assert type(PUBLIC_INTERFACE_LINES) is tuple
    assert type(PRIVATE_G182_IMPORTS) is tuple
    assert type(FIXTURE_IDENTITY) is tuple
    assert type(AUTHORITY_FIELDS) is tuple
    assert type(CALL_ACCOUNTING) is tuple
    assert type(OUTCOME_VECTORS) is tuple
    assert type(CALLER_OVERRIDES) is tuple
    assert type(STAGED_DELIVERY) is tuple
    assert type(READ_POLICY) is MappingProxyType
    assert type(FILESYSTEM_POLICY) is MappingProxyType
    assert type(DATA_QUALITY_POLICY) is MappingProxyType
    assert type(SANITIZED_FAILURE) is MappingProxyType
    assert type(SAFETY_FLAGS) is MappingProxyType
    assert len(PRIVATE_G182_IMPORTS) == 6
    assert len(FIXTURE_IDENTITY) == 5
    assert len(AUTHORITY_FIELDS) == 9
    assert len(CALL_ACCOUNTING) == 10
    assert len(OUTCOME_VECTORS) == 8
    assert len(SAFETY_FLAGS) == 8
    assert len(IMMUTABILITY_REQUIREMENTS) == 7
    assert len(FAIL_CLOSED_CONDITIONS) == 6
    assert len(ISOLATION_RULES) == 5
    assert len(REQUIRED_CONTRACT_VECTORS) == 10
    assert len(STAGED_DELIVERY) == 6


def test_future_surface_and_private_authority_are_exact() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)

    assert (
        "backend/app/services/"
        "canonical_gold_market_facts_docs_fixture_integration.py"
        in text
    )
    assert _fenced_block_lines(
        text,
        "It may expose exactly one production name:",
        "The function has no positional parameters",
        language="python",
    ) == PUBLIC_INTERFACE_LINES
    assert _fenced_block_lines(
        text,
        "Its `__all__`, if present, is exactly:",
        "No API router",
        language="python",
    ) == (f'("{PUBLIC_EXPORTS[0]}",)',)
    assert _fenced_block_lines(
        text,
        "The integration module may privately import exactly these G182-owned symbols.",
        "It must not re-export",
        language="text",
    ) == PRIVATE_G182_IMPORTS
    assert _fenced_block_lines(
        text,
        "Their exact future interfaces are:",
        "The validator is the sole authority",
        language="python",
    ) == VALIDATOR_INTERFACE_LINES + ("",) + SANITIZER_INTERFACE_LINES

    assert "validator is the sole authority for exact G182 result" in normalized
    assert "safe-failure constructor is the sole authority" in normalized
    assert "integration module must call these helpers" in normalized
    assert "must not import G178" in normalized
    assert "copy the validator" in normalized
    assert "reproduce the status mapping" in normalized


def test_fixed_path_time_identity_and_policy_authority_are_exact() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)

    assert PATH_AUTHORITY["repository_root_derivation"] in text
    assert PATH_AUTHORITY["allowed_root_suffix"] in text
    assert PATH_AUTHORITY["bundle_dir_name"] in text
    assert "exact concrete `WindowsPath` or `PosixPath`" in normalized
    assert REFERENCE_TIME in text

    expected_identity = tuple(
        f"{vector.field} = {vector.exact_value}" for vector in FIXTURE_IDENTITY
    )
    identity_block = _fenced_block_lines(
        text,
        "The accepted fixture identity is fixed to:",
        "These values are an integration oracle",
        language="text",
    )
    assert identity_block == expected_identity

    assert _markdown_table(
        text,
        "The authority values are fixed exactly as follows:",
        "The exact `CanonicalMt4DemoReadonlyBundleV1ReadPolicy` values are:",
    ) == (
        ("Authority field", "Exact value"),
        tuple(
            (f"`{vector.field}`", vector.exact_value)
            for vector in AUTHORITY_FIELDS
        ),
    )

    assert _fenced_block_lines(
        text,
        "The exact `CanonicalMt4DemoReadonlyBundleV1ReadPolicy` values are:",
        "The exact `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy` values are:",
        language="text",
    ) == tuple(f"{field} = {value}" for field, value in READ_POLICY.items())
    assert _fenced_block_lines(
        text,
        "The exact `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy` values are:",
        "The exact `CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy` value is:",
        language="text",
    ) == tuple(f"{field} = {value}" for field, value in FILESYSTEM_POLICY.items())
    assert _fenced_block_lines(
        text,
        "The exact `CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy` value is:",
        "Every scalar must have its exact built-in type.",
        language="text",
    ) == ("allow_upstream_warnings = false",)
    assert "Every scalar must have its exact built-in type." in text
    assert "fresh policy and authority objects for every invocation" in normalized


def test_call_chain_and_accounting_are_closed_and_ordered() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    observed_chain = _numbered_items(
        text,
        "The future zero-argument function performs these steps in order:",
        "The integration boundary must not call the reader",
    )
    assert len(observed_chain) == len(CALL_CHAIN) == 11
    assert observed_chain == CALL_CHAIN

    assert _markdown_table(text, "## 7. Call Accounting", "An invocation consumes") == (
        ("Outcome", "G182 adapter", "G182 validator", "G182 sanitizer"),
        tuple(
            (
                vector.outcome,
                str(vector.adapter_calls),
                str(vector.validator_calls),
                str(vector.sanitizer_calls),
            )
            for vector in CALL_ACCOUNTING
        ),
    )
    assert all(vector.adapter_calls in {0, 1} for vector in CALL_ACCOUNTING)
    assert all(vector.validator_calls in {0, 1} for vector in CALL_ACCOUNTING)
    assert all(vector.sanitizer_calls in {0, 1} for vector in CALL_ACCOUNTING)
    assert "No failure permits retry, fallback, another call" in normalized
    assert "sanitizer is the terminal failure constructor" in normalized
    assert "must not handcraft a fallback envelope" in normalized


def test_outcome_vectors_bind_accounting_and_disposition() -> None:
    accounting = {vector.outcome: vector for vector in CALL_ACCOUNTING}
    assert len(accounting) == len(CALL_ACCOUNTING)
    assert tuple(vector.name for vector in OUTCOME_VECTORS) == (
        "genuine_ready",
        "valid_blocked",
        "invalid_result",
        "adapter_exception",
        "identity_drift",
        "policy_or_authority_drift",
        "dependency_drift",
        "sanitizer_unavailable",
    )
    for vector in OUTCOME_VECTORS:
        calls = accounting[vector.accounting_outcome]
        assert calls.adapter_calls in {0, 1}
        if vector.accepted_unchanged:
            assert calls.sanitizer_calls == 0
            assert vector.expected_disposition == "return_validated_result"
        else:
            assert vector.expected_disposition in {
                "return_sanitized_failure",
                "integration_unavailable_no_source",
            }
            assert vector.source_available is False

    assert accounting[OUTCOME_VECTORS[0].accounting_outcome] == (
        CallAccountingVector(
            "G182 returns validated READY for the fixed fixture", 1, 1, 0
        )
    )
    assert accounting[OUTCOME_VECTORS[1].accounting_outcome] == (
        CallAccountingVector("G182 returns a validated blocked result", 1, 1, 0)
    )


def test_g182_validator_sanitizer_and_safe_envelope_remain_authoritative() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)

    expected_failure_lines = tuple(
        f"{field} = {_contract_literal(value)}"
        for field, value in SANITIZED_FAILURE.items()
    )
    assert _fenced_block_lines(
        text,
        "Every such path must call the G182-owned",
        "The fixed safety flags remain unchanged.",
        language="text",
    ) == expected_failure_lines

    assert _fenced_block_lines(
        text,
        "Every accepted result has exactly:",
        "A validator-approved G182 blocked result",
        language="text",
    ) == tuple(
        f"{field} = {_contract_literal(value)}" for field, value in SAFETY_FLAGS.items()
    )
    assert "only after that validator returns exact built-in `True`" in text
    assert "15 fields, order, strict types" in normalized
    assert "eight safety flags remain exclusively governed by G179/G182" in normalized
    assert "validated blocked result unchanged" in normalized
    assert "integration module does not construct this envelope" in normalized
    assert "does not import its private status constants" in normalized


def _contract_literal(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "None"
    if type(value) is tuple:
        if not value:
            return "()"
        return "(" + ",".join(str(item) for item in value) + ",)"
    return str(value)


def test_caller_override_and_fail_closed_vectors_are_concrete() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    assert tuple(vector.name for vector in CALLER_OVERRIDES) == (
        "path",
        "clock",
        "previous_identity",
        "policy",
        "dependency",
        "source",
        "oracle",
    )
    assert all(vector.adapter_calls == 0 for vector in CALLER_OVERRIDES)
    assert all(vector.accepted is False for vector in CALLER_OVERRIDES)
    for vector in CALLER_OVERRIDES:
        assert vector.attempted_override.split()[1] in normalized

    fail_closed = _bullet_items(
        text,
        "The future boundary fails closed for:",
        "The boundary must not sort",
    )
    assert fail_closed == FAIL_CLOSED_CONDITIONS
    assert "must not sort, normalize, repair, narrow, retry, fallback" in normalized


def test_same_attempt_w1_ownership_immutability_and_isolation_are_exact() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    assert _bullet_items(text, "W1 exclusively owns:", "The integration module") == (
        W1_OWNERSHIP
    )
    assert "one G182 invocation and therefore one W1 accepted attempt" in normalized
    assert "must not parse fixture files" in normalized
    assert "combine evidence from different attempts" in normalized

    immutability = _bullet_items(
        text,
        "Later integration evidence must prove all of the following:",
        "Determinism here is an offline fixture property.",
    )
    assert immutability == IMMUTABILITY_REQUIREMENTS
    for term in SENSITIVE_OUTPUT_TERMS:
        assert term in immutability[-1]

    isolation = _bullet_items(
        text,
        "The integration implementation must not import or call:",
        "The G178 prohibition applies",
    )
    assert isolation == ISOLATION_RULES
    for module in FORBIDDEN_RUNTIME_IMPORTS:
        assert module in normalized
    assert "must not read environment variables" in normalized
    assert "READY is not activation" in normalized
    assert "permission to trade" in normalized


def test_required_vectors_and_staged_delivery_are_closed() -> None:
    text = _contract_text()
    normalized = _normalize_whitespace(text)
    required_vectors = _bullet_items(
        text,
        "A later tests-only work order must use immutable static vectors",
        "Static vectors are tests-only evidence.",
    )
    assert required_vectors == REQUIRED_CONTRACT_VECTORS

    assert _numbered_items(
        text,
        "Later work remains separately planned and approved:",
        "No stage silently includes the next.",
    ) == STAGED_DELIVERY
    assert "Contract is not tests, tests are not implementation" in normalized
    assert "W6 as a package remains `TESTS_ONLY`" in text
    assert "does not authorize a source adapter runtime" in normalized


def test_closed_oracles_reject_reviewed_contract_mutations() -> None:
    text = _contract_text()

    expanded_signature = text.replace(
        ") -> CanonicalGoldMarketFactsSourceAdapterResultV1:\n",
        "    *, caller_path: object,\n"
        ") -> CanonicalGoldMarketFactsSourceAdapterResultV1:\n",
        1,
    )
    assert _fenced_block_lines(
        expanded_signature,
        "It may expose exactly one production name:",
        "The function has no positional parameters",
        language="python",
    ) != PUBLIC_INTERFACE_LINES

    removed_private_import = text.replace("_AUTHORITY_TOKEN\n", "", 1)
    assert _fenced_block_lines(
        removed_private_import,
        "The integration module may privately import exactly these G182-owned symbols.",
        "It must not re-export",
        language="text",
    ) != PRIVATE_G182_IMPORTS

    reordered_calls = text.replace(
        "| G182 invocation begins and raises | 1 | 0 | 1 |\n"
        "| Post-call authority drift | 1 | 0 | 1 |",
        "| Post-call authority drift | 1 | 0 | 1 |\n"
        "| G182 invocation begins and raises | 1 | 0 | 1 |",
        1,
    )
    assert _markdown_table(
        reordered_calls, "## 7. Call Accounting", "An invocation consumes"
    )[1] != tuple(
        (
            vector.outcome,
            str(vector.adapter_calls),
            str(vector.validator_calls),
            str(vector.sanitizer_calls),
        )
        for vector in CALL_ACCOUNTING
    )

    expanded_stage = text.replace(
        "1. immutable tests-only vectors for this contract;",
        "1. immutable tests-only vectors and production implementation;",
        1,
    )
    assert _numbered_items(
        expanded_stage,
        "Later work remains separately planned and approved:",
        "No stage silently includes the next.",
    ) != STAGED_DELIVERY

    weakened_g178_boundary = text.replace(
        "must\nnot import G178",
        "may\nimport G178",
        1,
    )
    assert "must not import G178" not in _normalize_whitespace(
        weakened_g178_boundary
    )

    extra_policy = text.replace(
        "max_future_skew_seconds = 5\n```",
        "max_future_skew_seconds = 5\ncaller_policy_override = true\n```",
        1,
    )
    assert _fenced_block_lines(
        extra_policy,
        "The exact `CanonicalMt4DemoReadonlyBundleV1ReadPolicy` values are:",
        "The exact `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy` values are:",
        language="text",
    ) != tuple(f"{field} = {value}" for field, value in READ_POLICY.items())

    reordered_policy = text.replace(
        "writer_heartbeat_max_age_seconds = 15\n"
        "live_tick_max_age_seconds = 10",
        "live_tick_max_age_seconds = 10\n"
        "writer_heartbeat_max_age_seconds = 15",
        1,
    )
    assert _fenced_block_lines(
        reordered_policy,
        "The exact `CanonicalMt4DemoReadonlyBundleV1ReadPolicy` values are:",
        "The exact `CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy` values are:",
        language="text",
    ) != tuple(f"{field} = {value}" for field, value in READ_POLICY.items())

    unsafe_flag = text.replace(
        "allowed_to_modify_risk = false\n```",
        "allowed_to_modify_risk = false\ncan_trade = true\n```",
        1,
    )
    assert _fenced_block_lines(
        unsafe_flag,
        "Every accepted result has exactly:",
        "A validator-approved G182 blocked result",
        language="text",
    ) != tuple(
        f"{field} = {_contract_literal(value)}" for field, value in SAFETY_FLAGS.items()
    )

    weakened_required_vector = text.replace(
        "- exact G182-owned adapter-result validation and sanitized failure envelope;",
        "- adapter-result validation when convenient;",
        1,
    )
    assert _bullet_items(
        weakened_required_vector,
        "A later tests-only work order must use immutable static vectors",
        "Static vectors are tests-only evidence.",
    ) != REQUIRED_CONTRACT_VECTORS

    extra_fail_closed_entry = text.replace(
        "- any attempt to use diagnostics, W5 ReplayRunner, runtime `data/`, environment,",
        "- caller policy may override the fixed fixture;\n"
        "- any attempt to use diagnostics, W5 ReplayRunner, runtime `data/`, environment,",
        1,
    )
    assert _bullet_items(
        extra_fail_closed_entry,
        "The future boundary fails closed for:",
        "The boundary must not sort",
    ) != FAIL_CLOSED_CONDITIONS

    reordered_immutability = text.replace(
        "- repeated genuine executions return equal adapter results;\n"
        "- every execution returns a fresh result object and a fresh detached source;",
        "- every execution returns a fresh result object and a fresh detached source;\n"
        "- repeated genuine executions return equal adapter results;",
        1,
    )
    assert _bullet_items(
        reordered_immutability,
        "Later integration evidence must prove all of the following:",
        "Determinism here is an offline fixture property.",
    ) != IMMUTABILITY_REQUIREMENTS

    weakened_isolation = text.replace("- G178 projector;", "- G178 projector may run;", 1)
    assert _bullet_items(
        weakened_isolation,
        "The integration implementation must not import or call:",
        "The G178 prohibition applies",
    ) != ISOLATION_RULES


def test_static_vectors_do_not_import_or_implement_future_runtime() -> None:
    source = TEST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imported_modules == {
        "__future__",
        "ast",
        "dataclasses",
        "pathlib",
        "types",
        "pytest",
    }
    assert not any(module.startswith("app") for module in imported_modules)

    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "build_canonical_gold_market_facts_docs_fixture_source_v1" not in (
        function_names
    )
    assert "_is_safe_canonical_gold_market_facts_source_adapter_result_v1" not in (
        function_names
    )
    assert "_build_canonical_gold_market_facts_source_adapter_safe_failure_v1" not in (
        function_names
    )
    assert "monkey" + "patch" not in source
    assert "unittest" + ".mock" not in source
