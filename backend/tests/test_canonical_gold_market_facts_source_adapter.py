from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import get_type_hints

import pytest

import app.services.canonical_gold_market_facts_source_adapter as adapter_module
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldMarketFactsSourceV1,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
)
from app.services.data_quality_gate import (
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy,
)


RESULT_FIELDS = (
    "contract_version",
    "passed",
    "status_code",
    "reason_codes",
    "warning_codes",
    "source_available",
    "source",
    "read_only",
    "demo_only",
    "is_tradable",
    "can_execute",
    "is_trading_permission",
    "is_execution_instruction",
    "allowed_to_call_ea",
    "allowed_to_modify_risk",
)


def test_previous_identity_type_is_exact_frozen_and_slotted() -> None:
    identity = adapter_module._CanonicalBundlePreviousIdentityV1(
        bundle_id="bundle-1",
        sequence=1,
    )

    assert tuple(field.name for field in fields(type(identity))) == (
        "bundle_id",
        "sequence",
    )
    assert get_type_hints(type(identity)) == {
        "bundle_id": str,
        "sequence": int,
    }
    assert not hasattr(identity, "__dict__")
    with pytest.raises(FrozenInstanceError):
        identity.sequence = 2  # type: ignore[misc]


def test_authority_type_has_exact_fields_annotations_and_private_token() -> None:
    authority = _authority()

    assert tuple(field.name for field in fields(type(authority))) == (
        "authority_token",
        "allowed_root",
        "bundle_dir",
        "reference_time_utc",
        "previous_identity",
        "read_policy",
        "filesystem_policy",
        "data_quality_policy",
        "policy_profile_version",
    )
    assert get_type_hints(type(authority)) == {
        "authority_token": object,
        "allowed_root": Path,
        "bundle_dir": Path,
        "reference_time_utc": datetime,
        "previous_identity": (
            adapter_module._CanonicalBundlePreviousIdentityV1 | None
        ),
        "read_policy": CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
        "filesystem_policy": CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
        "data_quality_policy": CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy,
        "policy_profile_version": str,
    }
    assert type(adapter_module._AUTHORITY_TOKEN) is object
    assert authority.authority_token is adapter_module._AUTHORITY_TOKEN
    assert type(authority.allowed_root) is type(Path("server-root"))
    assert type(authority.bundle_dir) is type(authority.allowed_root)
    assert not hasattr(authority, "__dict__")
    with pytest.raises(FrozenInstanceError):
        authority.policy_profile_version = "changed"  # type: ignore[misc]


def test_result_type_has_exact_fields_annotations_and_fresh_construction() -> None:
    first = _blocked_result()
    second = _blocked_result()

    assert tuple(field.name for field in fields(type(first))) == RESULT_FIELDS
    assert get_type_hints(type(first)) == {
        "contract_version": str,
        "passed": bool,
        "status_code": str,
        "reason_codes": tuple[str, ...],
        "warning_codes": tuple[str, ...],
        "source_available": bool,
        "source": CanonicalGoldMarketFactsSourceV1 | None,
        "read_only": bool,
        "demo_only": bool,
        "is_tradable": bool,
        "can_execute": bool,
        "is_trading_permission": bool,
        "is_execution_instruction": bool,
        "allowed_to_call_ea": bool,
        "allowed_to_modify_risk": bool,
    }
    assert first == second
    assert first is not second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.passed = True  # type: ignore[misc]


def test_type_module_has_no_adapter_behavior_or_runtime_io() -> None:
    path = Path(adapter_module.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    public_names = {
        name for name in vars(adapter_module) if not name.startswith("_")
    }
    public_names.discard("annotations")
    assert public_names == {"CanonicalGoldMarketFactsSourceAdapterResultV1"}
    assert not hasattr(
        adapter_module,
        "build_server_owned_canonical_gold_market_facts_source_v1",
    )
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )
    assert "read_and_validate_canonical_mt4_demo_readonly_bundle_v1" not in source
    assert "evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate" not in source
    assert "build_canonical_gold_market_facts_snapshot_v1" not in source
    assert "os.environ" not in source
    assert "app.api" not in source
    assert "ReplayRunner" not in source
    assert "MT4" not in source


def _authority() -> object:
    previous_identity = adapter_module._CanonicalBundlePreviousIdentityV1(
        bundle_id="bundle-1",
        sequence=1,
    )
    return adapter_module._CanonicalGoldMarketFactsSourceAuthorityV1(
        authority_token=adapter_module._AUTHORITY_TOKEN,
        allowed_root=Path("server-root"),
        bundle_dir=Path("server-root") / "bundle",
        reference_time_utc=datetime(2026, 7, 14, tzinfo=UTC),
        previous_identity=previous_identity,
        read_policy=CanonicalMt4DemoReadonlyBundleV1ReadPolicy(),
        filesystem_policy=CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy(
            max_manifest_consistency_retries=0,
        ),
        data_quality_policy=CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy(),
        policy_profile_version="canonical_gold_market_facts_policy_v1",
    )


def _blocked_result() -> adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1:
    return adapter_module.CanonicalGoldMarketFactsSourceAdapterResultV1(
        contract_version="1.0",
        passed=False,
        status_code="CANONICAL_GOLD_SOURCE_ADAPTER_SAFE_FAILURE",
        reason_codes=("GOLD_SOURCE_EXCEPTION_SANITIZED",),
        warning_codes=(),
        source_available=False,
        source=None,
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )
