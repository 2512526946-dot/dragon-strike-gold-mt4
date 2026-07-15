from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.services.canonical_gold_market_facts_source_adapter import (
    _AUTHORITY_TOKEN,
    _CanonicalGoldMarketFactsSourceAuthorityV1,
    _build_canonical_gold_market_facts_source_adapter_safe_failure_v1,
    _is_safe_canonical_gold_market_facts_source_adapter_result_v1,
    CanonicalGoldMarketFactsSourceAdapterResultV1,
    build_server_owned_canonical_gold_market_facts_source_v1,
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


__all__ = ("build_canonical_gold_market_facts_docs_fixture_source_v1",)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FIXED_PATHS = (
    _REPOSITORY_ROOT,
    _REPOSITORY_ROOT / "docs" / "architecture" / "fixtures",
    _REPOSITORY_ROOT
    / "docs"
    / "architecture"
    / "fixtures"
    / "canonical-mt4-demo-readonly-bundle-v1",
)
_EXPECTED_FIXED_PATHS = _FIXED_PATHS
_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
_EXPECTED_REFERENCE_TIME = _REFERENCE_TIME
_FIXTURE_IDENTITY = (
    "1.0",
    "demo-bundle-000000000001",
    1,
    "XAUUSD",
    "GOLD",
)
_EXPECTED_FIXTURE_IDENTITY = _FIXTURE_IDENTITY
_POLICY_PROFILE_VERSION = "canonical_gold_market_facts_policy_v1"

_EXPECTED_AUTHORITY_TOKEN = _AUTHORITY_TOKEN
_EXPECTED_AUTHORITY_TYPE = _CanonicalGoldMarketFactsSourceAuthorityV1
_EXPECTED_RESULT_TYPE = CanonicalGoldMarketFactsSourceAdapterResultV1
_EXPECTED_BUILD_ADAPTER = build_server_owned_canonical_gold_market_facts_source_v1
_EXPECTED_VALIDATE_RESULT = (
    _is_safe_canonical_gold_market_facts_source_adapter_result_v1
)
_EXPECTED_BUILD_SAFE_FAILURE = (
    _build_canonical_gold_market_facts_source_adapter_safe_failure_v1
)
_EXPECTED_READ_POLICY_TYPE = _ReadPolicy
_EXPECTED_FILESYSTEM_POLICY_TYPE = _FilesystemPolicy
_EXPECTED_DATA_QUALITY_POLICY_TYPE = _DataQualityPolicy


def build_canonical_gold_market_facts_docs_fixture_source_v1(
) -> CanonicalGoldMarketFactsSourceAdapterResultV1:
    """Run one fixed offline docs-fixture source-adapter attempt."""

    if not _fixed_dependencies_are_unchanged() or not _fixed_constants_are_valid():
        return _safe_failure_or_none()  # type: ignore[return-value]

    try:
        authority = _build_fresh_authority()
        authority_snapshot = _authority_snapshot(authority)
    except Exception:
        return _safe_failure_or_none()  # type: ignore[return-value]

    if authority_snapshot is None:
        return _safe_failure_or_none()  # type: ignore[return-value]

    try:
        result = build_server_owned_canonical_gold_market_facts_source_v1(
            authority=authority
        )
    except Exception:
        return _safe_failure_or_none()  # type: ignore[return-value]

    if (
        _authority_snapshot(authority) != authority_snapshot
        or not _fixed_dependencies_are_unchanged()
        or not _fixed_constants_are_valid()
    ):
        return _safe_failure_or_none()  # type: ignore[return-value]

    try:
        result_is_safe = _is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=result
        )
    except Exception:
        return _safe_failure_or_none()  # type: ignore[return-value]
    if type(result_is_safe) is not bool or result_is_safe is not True:
        return _safe_failure_or_none()  # type: ignore[return-value]
    if (
        _authority_snapshot(authority) != authority_snapshot
        or not _fixed_dependencies_are_unchanged()
        or not _fixed_constants_are_valid()
    ):
        return _safe_failure_or_none()  # type: ignore[return-value]

    if result.passed is False:
        return result
    source = result.source
    if (
        source.bundle_schema_version,
        source.bundle_id,
        source.sequence,
        source.canonical_symbol,
        source.broker_symbol,
    ) != _FIXTURE_IDENTITY:
        return _safe_failure_or_none()  # type: ignore[return-value]
    return result


def _fixed_dependencies_are_unchanged() -> bool:
    return (
        _AUTHORITY_TOKEN is _EXPECTED_AUTHORITY_TOKEN
        and _CanonicalGoldMarketFactsSourceAuthorityV1 is _EXPECTED_AUTHORITY_TYPE
        and CanonicalGoldMarketFactsSourceAdapterResultV1 is _EXPECTED_RESULT_TYPE
        and _ReadPolicy is _EXPECTED_READ_POLICY_TYPE
        and _FilesystemPolicy is _EXPECTED_FILESYSTEM_POLICY_TYPE
        and _DataQualityPolicy is _EXPECTED_DATA_QUALITY_POLICY_TYPE
        and build_server_owned_canonical_gold_market_facts_source_v1
        is _EXPECTED_BUILD_ADAPTER
        and callable(build_server_owned_canonical_gold_market_facts_source_v1)
        and _is_safe_canonical_gold_market_facts_source_adapter_result_v1
        is _EXPECTED_VALIDATE_RESULT
        and callable(_is_safe_canonical_gold_market_facts_source_adapter_result_v1)
        and _build_canonical_gold_market_facts_source_adapter_safe_failure_v1
        is _EXPECTED_BUILD_SAFE_FAILURE
        and callable(_build_canonical_gold_market_facts_source_adapter_safe_failure_v1)
    )


def _fixed_constants_are_valid() -> bool:
    try:
        repository_root, allowed_root, bundle_dir = _FIXED_PATHS
        concrete_path_type = type(repository_root)
        return (
            _FIXED_PATHS is _EXPECTED_FIXED_PATHS
            and type(_FIXED_PATHS) is tuple
            and len(_FIXED_PATHS) == 3
            and concrete_path_type is type(_EXPECTED_FIXED_PATHS[0])
            and type(allowed_root) is concrete_path_type
            and type(bundle_dir) is concrete_path_type
            and repository_root == Path(__file__).resolve().parents[3]
            and allowed_root
            == repository_root / "docs" / "architecture" / "fixtures"
            and bundle_dir
            == allowed_root / "canonical-mt4-demo-readonly-bundle-v1"
            and _REFERENCE_TIME is _EXPECTED_REFERENCE_TIME
            and type(_REFERENCE_TIME) is datetime
            and _REFERENCE_TIME
            == datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)
            and _REFERENCE_TIME.tzinfo is UTC
            and _FIXTURE_IDENTITY is _EXPECTED_FIXTURE_IDENTITY
            and type(_FIXTURE_IDENTITY) is tuple
            and _FIXTURE_IDENTITY
            == ("1.0", "demo-bundle-000000000001", 1, "XAUUSD", "GOLD")
            and all(
                type(value) is expected_type
                for value, expected_type in zip(
                    _FIXTURE_IDENTITY,
                    (str, str, int, str, str),
                    strict=True,
                )
            )
            and type(_POLICY_PROFILE_VERSION) is str
            and _POLICY_PROFILE_VERSION
            == "canonical_gold_market_facts_policy_v1"
        )
    except Exception:
        return False


def _build_fresh_authority() -> _CanonicalGoldMarketFactsSourceAuthorityV1:
    _, allowed_root, bundle_dir = _FIXED_PATHS
    read_policy = _ReadPolicy(
        writer_heartbeat_max_age_seconds=15,
        live_tick_max_age_seconds=10,
        latest_bars_max_age_seconds=60,
        symbol_spec_max_age_seconds=86400,
        account_snapshot_max_age_seconds=30,
        max_future_skew_seconds=5,
    )
    filesystem_policy = _FilesystemPolicy(
        manifest_max_bytes=65536,
        live_tick_max_bytes=32768,
        latest_bars_max_bytes=2097152,
        symbol_spec_max_bytes=65536,
        account_snapshot_max_bytes=131072,
        max_manifest_consistency_retries=0,
    )
    data_quality_policy = _DataQualityPolicy(allow_upstream_warnings=False)
    return _CanonicalGoldMarketFactsSourceAuthorityV1(
        authority_token=_AUTHORITY_TOKEN,
        allowed_root=allowed_root,
        bundle_dir=bundle_dir,
        reference_time_utc=_REFERENCE_TIME,
        previous_identity=None,
        read_policy=read_policy,
        filesystem_policy=filesystem_policy,
        data_quality_policy=data_quality_policy,
        policy_profile_version=_POLICY_PROFILE_VERSION,
    )


def _authority_snapshot(
    authority: object,
) -> tuple[object, ...] | None:
    try:
        if type(authority) is not _CanonicalGoldMarketFactsSourceAuthorityV1:
            return None
        return (
            type(authority),
            authority.authority_token,
            type(authority.allowed_root),
            authority.allowed_root,
            type(authority.bundle_dir),
            authority.bundle_dir,
            type(authority.reference_time_utc),
            authority.reference_time_utc,
            authority.previous_identity,
            type(authority.read_policy),
            authority.read_policy.writer_heartbeat_max_age_seconds,
            authority.read_policy.live_tick_max_age_seconds,
            authority.read_policy.latest_bars_max_age_seconds,
            authority.read_policy.symbol_spec_max_age_seconds,
            authority.read_policy.account_snapshot_max_age_seconds,
            authority.read_policy.max_future_skew_seconds,
            type(authority.filesystem_policy),
            authority.filesystem_policy.manifest_max_bytes,
            authority.filesystem_policy.live_tick_max_bytes,
            authority.filesystem_policy.latest_bars_max_bytes,
            authority.filesystem_policy.symbol_spec_max_bytes,
            authority.filesystem_policy.account_snapshot_max_bytes,
            authority.filesystem_policy.max_manifest_consistency_retries,
            type(authority.data_quality_policy),
            authority.data_quality_policy.allow_upstream_warnings,
            type(authority.policy_profile_version),
            authority.policy_profile_version,
        )
    except Exception:
        return None


def _safe_failure_or_none(
) -> CanonicalGoldMarketFactsSourceAdapterResultV1 | None:
    if (
        _build_canonical_gold_market_facts_source_adapter_safe_failure_v1
        is not _EXPECTED_BUILD_SAFE_FAILURE
        or not callable(
            _build_canonical_gold_market_facts_source_adapter_safe_failure_v1
        )
    ):
        return None
    try:
        result = _build_canonical_gold_market_facts_source_adapter_safe_failure_v1()
    except Exception:
        return None
    if type(result) is not _EXPECTED_RESULT_TYPE:
        return None
    try:
        result_is_safe = result._is_fixed_sanitized_failure_v1()
    except Exception:
        return None
    if type(result_is_safe) is not bool or result_is_safe is not True:
        return None
    return result
