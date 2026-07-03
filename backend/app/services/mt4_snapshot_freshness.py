from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.services.mt4_snapshot_metadata import (
    Mt4FileMetadataStatus,
    Mt4SnapshotMetadataStatus,
)
from app.services.mt4_snapshot_reader import (
    ACCOUNT_SNAPSHOT_FILE,
    LATEST_BARS_FILE,
    LIVE_TICK_FILE,
    SYMBOL_SPEC_FILE,
)


DEFAULT_FRESHNESS_THRESHOLDS_SECONDS = {
    LIVE_TICK_FILE: 10,
    LATEST_BARS_FILE: 60,
    SYMBOL_SPEC_FILE: 86400,
    ACCOUNT_SNAPSHOT_FILE: 30,
}

DEFAULT_MAX_FUTURE_SKEW_SECONDS = 5

FRESHNESS_OK = "FRESHNESS_OK"
METADATA_NOT_READY = "METADATA_NOT_READY"
MISSING_GENERATED_AT = "MISSING_GENERATED_AT"
INVALID_GENERATED_AT = "INVALID_GENERATED_AT"
GENERATED_AT_STALE = "GENERATED_AT_STALE"
GENERATED_AT_FROM_FUTURE = "GENERATED_AT_FROM_FUTURE"

ALL_FILES_FRESH = "ALL_FILES_FRESH"
SOME_METADATA_NOT_READY = "SOME_METADATA_NOT_READY"
SOME_GENERATED_AT_MISSING = "SOME_GENERATED_AT_MISSING"
SOME_GENERATED_AT_INVALID = "SOME_GENERATED_AT_INVALID"
SOME_FILES_STALE = "SOME_FILES_STALE"
SOME_FILES_FROM_FUTURE = "SOME_FILES_FROM_FUTURE"


@dataclass(frozen=True)
class Mt4FileFreshnessStatus:
    file_name: str
    generated_at: str | None
    parsed_generated_at_utc: datetime | None
    age_seconds: float | None
    max_age_seconds: int
    max_future_skew_seconds: int
    is_parseable: bool
    is_fresh: bool
    is_stale: bool
    is_from_future: bool
    can_proceed_to_data_quality_gate: bool
    status_code: str
    error_codes: list[str]


@dataclass(frozen=True)
class Mt4SnapshotFreshnessStatus:
    live_tick: Mt4FileFreshnessStatus
    latest_bars: Mt4FileFreshnessStatus
    symbol_spec: Mt4FileFreshnessStatus
    account_snapshot: Mt4FileFreshnessStatus
    all_generated_at_parseable: bool
    all_files_fresh: bool
    any_file_stale: bool
    any_file_from_future: bool
    can_proceed_to_data_quality_gate: bool
    status_code: str


def check_mt4_file_freshness(
    metadata_status: Mt4FileMetadataStatus,
    now_utc: datetime,
    max_age_seconds: int,
    max_future_skew_seconds: int = DEFAULT_MAX_FUTURE_SKEW_SECONDS,
) -> Mt4FileFreshnessStatus:
    normalized_now_utc = _to_utc(now_utc)

    if metadata_status.generated_at is None:
        return _not_ready_status(
            metadata_status=metadata_status,
            max_age_seconds=max_age_seconds,
            max_future_skew_seconds=max_future_skew_seconds,
            status_code=MISSING_GENERATED_AT,
            error_code=MISSING_GENERATED_AT,
        )

    if not metadata_status.can_proceed_to_freshness_checks:
        return _not_ready_status(
            metadata_status=metadata_status,
            max_age_seconds=max_age_seconds,
            max_future_skew_seconds=max_future_skew_seconds,
            status_code=METADATA_NOT_READY,
            error_code=METADATA_NOT_READY,
        )

    parsed_generated_at_utc = _parse_generated_at(metadata_status.generated_at)
    if parsed_generated_at_utc is None:
        return Mt4FileFreshnessStatus(
            file_name=metadata_status.file_name,
            generated_at=metadata_status.generated_at,
            parsed_generated_at_utc=None,
            age_seconds=None,
            max_age_seconds=max_age_seconds,
            max_future_skew_seconds=max_future_skew_seconds,
            is_parseable=False,
            is_fresh=False,
            is_stale=False,
            is_from_future=False,
            can_proceed_to_data_quality_gate=False,
            status_code=INVALID_GENERATED_AT,
            error_codes=[INVALID_GENERATED_AT],
        )

    age_seconds = (normalized_now_utc - parsed_generated_at_utc).total_seconds()
    is_from_future = age_seconds < -max_future_skew_seconds
    is_stale = age_seconds > max_age_seconds
    is_fresh = not is_stale and not is_from_future
    error_codes = _freshness_error_codes(
        is_stale=is_stale,
        is_from_future=is_from_future,
    )

    return Mt4FileFreshnessStatus(
        file_name=metadata_status.file_name,
        generated_at=metadata_status.generated_at,
        parsed_generated_at_utc=parsed_generated_at_utc,
        age_seconds=age_seconds,
        max_age_seconds=max_age_seconds,
        max_future_skew_seconds=max_future_skew_seconds,
        is_parseable=True,
        is_fresh=is_fresh,
        is_stale=is_stale,
        is_from_future=is_from_future,
        can_proceed_to_data_quality_gate=is_fresh,
        status_code=_file_status_code(error_codes),
        error_codes=error_codes,
    )


def check_mt4_snapshot_freshness(
    metadata_status: Mt4SnapshotMetadataStatus,
    now_utc: datetime,
    thresholds_seconds: dict[str, int] | None = None,
    max_future_skew_seconds: int = DEFAULT_MAX_FUTURE_SKEW_SECONDS,
) -> Mt4SnapshotFreshnessStatus:
    thresholds = DEFAULT_FRESHNESS_THRESHOLDS_SECONDS | (thresholds_seconds or {})

    live_tick = check_mt4_file_freshness(
        metadata_status.live_tick,
        now_utc,
        thresholds[LIVE_TICK_FILE],
        max_future_skew_seconds,
    )
    latest_bars = check_mt4_file_freshness(
        metadata_status.latest_bars,
        now_utc,
        thresholds[LATEST_BARS_FILE],
        max_future_skew_seconds,
    )
    symbol_spec = check_mt4_file_freshness(
        metadata_status.symbol_spec,
        now_utc,
        thresholds[SYMBOL_SPEC_FILE],
        max_future_skew_seconds,
    )
    account_snapshot = check_mt4_file_freshness(
        metadata_status.account_snapshot,
        now_utc,
        thresholds[ACCOUNT_SNAPSHOT_FILE],
        max_future_skew_seconds,
    )

    file_statuses = (live_tick, latest_bars, symbol_spec, account_snapshot)

    return Mt4SnapshotFreshnessStatus(
        live_tick=live_tick,
        latest_bars=latest_bars,
        symbol_spec=symbol_spec,
        account_snapshot=account_snapshot,
        all_generated_at_parseable=all(status.is_parseable for status in file_statuses),
        all_files_fresh=all(status.is_fresh for status in file_statuses),
        any_file_stale=any(status.is_stale for status in file_statuses),
        any_file_from_future=any(status.is_from_future for status in file_statuses),
        can_proceed_to_data_quality_gate=all(
            status.can_proceed_to_data_quality_gate for status in file_statuses
        ),
        status_code=_snapshot_status_code(file_statuses),
    )


def _not_ready_status(
    *,
    metadata_status: Mt4FileMetadataStatus,
    max_age_seconds: int,
    max_future_skew_seconds: int,
    status_code: str,
    error_code: str,
) -> Mt4FileFreshnessStatus:
    return Mt4FileFreshnessStatus(
        file_name=metadata_status.file_name,
        generated_at=metadata_status.generated_at,
        parsed_generated_at_utc=None,
        age_seconds=None,
        max_age_seconds=max_age_seconds,
        max_future_skew_seconds=max_future_skew_seconds,
        is_parseable=False,
        is_fresh=False,
        is_stale=False,
        is_from_future=False,
        can_proceed_to_data_quality_gate=False,
        status_code=status_code,
        error_codes=[error_code],
    )


def _parse_generated_at(value: str) -> datetime | None:
    normalized_value = value
    if value.endswith("Z"):
        normalized_value = f"{value[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None

    return _to_utc(parsed)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _freshness_error_codes(*, is_stale: bool, is_from_future: bool) -> list[str]:
    if is_from_future:
        return [GENERATED_AT_FROM_FUTURE]
    if is_stale:
        return [GENERATED_AT_STALE]
    return []


def _file_status_code(error_codes: list[str]) -> str:
    if not error_codes:
        return FRESHNESS_OK
    return error_codes[0]


def _snapshot_status_code(
    file_statuses: tuple[Mt4FileFreshnessStatus, ...],
) -> str:
    all_errors = [error for status in file_statuses for error in status.error_codes]

    if METADATA_NOT_READY in all_errors:
        return SOME_METADATA_NOT_READY
    if MISSING_GENERATED_AT in all_errors:
        return SOME_GENERATED_AT_MISSING
    if INVALID_GENERATED_AT in all_errors:
        return SOME_GENERATED_AT_INVALID
    if GENERATED_AT_FROM_FUTURE in all_errors:
        return SOME_FILES_FROM_FUTURE
    if GENERATED_AT_STALE in all_errors:
        return SOME_FILES_STALE
    return ALL_FILES_FRESH
