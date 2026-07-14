from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
from pathlib import Path as _Path

from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldMarketFactsSourceV1 as _CanonicalGoldMarketFactsSourceV1,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_filesystem_reader import (
    CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy as _FilesystemPolicy,
)
from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy as _ReadPolicy,
)
from app.services.data_quality_gate import (
    CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy as _DataQualityPolicy,
)


_AUTHORITY_TOKEN = object()


@_dataclass(frozen=True, slots=True)
class _CanonicalBundlePreviousIdentityV1:
    bundle_id: str
    sequence: int


@_dataclass(frozen=True, slots=True)
class _CanonicalGoldMarketFactsSourceAuthorityV1:
    authority_token: object
    allowed_root: _Path
    bundle_dir: _Path
    reference_time_utc: _datetime
    previous_identity: _CanonicalBundlePreviousIdentityV1 | None
    read_policy: _ReadPolicy
    filesystem_policy: _FilesystemPolicy
    data_quality_policy: _DataQualityPolicy
    policy_profile_version: str


@_dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSourceAdapterResultV1:
    contract_version: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    source_available: bool
    source: _CanonicalGoldMarketFactsSourceV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool
