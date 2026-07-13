from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSourceV1:
    contract_version: str
    bundle_schema_version: str
    bundle_id: str
    sequence: int
    canonical_symbol: str
    broker_symbol: str
    reference_time_utc: str
    policy_profile_version: str
    upstream_evidence: CanonicalGoldUpstreamEvidenceV1
    live_tick: CanonicalGoldTickSourceV1
    bars_generated_at_utc: str
    timeframes: tuple[CanonicalGoldTimeframeSourceV1, ...]
    symbol_spec: CanonicalGoldSymbolSpecSourceV1


@dataclass(frozen=True, slots=True)
class CanonicalGoldUpstreamEvidenceV1:
    reader_passed: bool
    reader_status_code: str
    value_status_code: str
    data_quality_passed: bool
    data_quality_status_code: str
    ready_for_readonly_analysis: bool
    warning_codes: tuple[str, ...]
    same_attempt_identity_bound: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldTickSourceV1:
    bid: int | float
    ask: int | float
    spread: int | float
    spread_points: int
    digits: int
    point: int | float
    tick_time_utc: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldTimeframeSourceV1:
    timeframe: str
    period_seconds: int
    bars: tuple[CanonicalGoldBarSourceV1, ...]


@dataclass(frozen=True, slots=True)
class CanonicalGoldBarSourceV1:
    open_time_utc: str
    open: int | float
    high: int | float
    low: int | float
    close: int | float
    tick_volume: int
    spread_points: int


@dataclass(frozen=True, slots=True)
class CanonicalGoldSymbolSpecSourceV1:
    spec_time_utc: str
    digits: int
    point: int | float
    tick_size: int | float
    tick_value: int | float
    contract_size: int | float
    min_lot: int | float
    lot_step: int | float
    max_lot: int | float
    base_currency: str
    profit_currency: str
    margin_currency: str
    trade_mode_readonly_label: str
    session_status_readonly_label: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldMarketFactsSnapshotV1:
    contract_version: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    identity_available: bool
    bundle_schema_version: str | None
    bundle_id: str | None
    sequence: int | None
    canonical_symbol: str | None
    broker_symbol: str | None
    reference_time_utc: str | None
    quote: CanonicalGoldQuoteFactsV1 | None
    timeframes: tuple[CanonicalGoldTimeframeFactsV1, ...]
    symbol_spec: CanonicalGoldSymbolFactsV1 | None
    freshness: CanonicalGoldFreshnessFactsV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


@dataclass(frozen=True, slots=True)
class CanonicalGoldQuoteFactsV1:
    bid_decimal: str
    ask_decimal: str
    spread_decimal: str
    spread_points: int
    digits: int
    point_decimal: str
    tick_time_utc: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldTimeframeFactsV1:
    timeframe: str
    period_seconds: int
    bars: tuple[CanonicalGoldBarFactsV1, ...]


@dataclass(frozen=True, slots=True)
class CanonicalGoldBarFactsV1:
    open_time_utc: str
    open_decimal: str
    high_decimal: str
    low_decimal: str
    close_decimal: str
    tick_volume: int
    spread_points: int


@dataclass(frozen=True, slots=True)
class CanonicalGoldSymbolFactsV1:
    spec_time_utc: str
    digits: int
    point_decimal: str
    tick_size_decimal: str
    tick_value_decimal: str
    contract_size_decimal: str
    min_lot_decimal: str
    lot_step_decimal: str
    max_lot_decimal: str
    base_currency: str
    profit_currency: str
    margin_currency: str
    trade_mode_readonly_label: str
    session_status_readonly_label: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldFreshnessFactsV1:
    tick_age_microseconds: int
    bars_payload_age_microseconds: int
    symbol_spec_age_microseconds: int
