"""Immutable G208 contract vectors only; no future replay-stage runtime."""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass, make_dataclass, replace
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Final

import pytest

from app.services import canonical_bundle_replay_runner as replay_v1
from app.services import canonical_gold_economic_calendar_source_adapter as calendar
from app.services import canonical_gold_economic_window_facts as economic
from app.services import (
    canonical_gold_market_facts_docs_fixture_integration as market_fixture,
)
from app.services import canonical_gold_market_facts_source_adapter as market_adapter
from app.services import canonical_gold_market_facts_snapshot_projector as market_facts
from app.services import (
    canonical_gold_session_spread_freshness_facts as session_facts,
)
from app.services import canonical_gold_volatility_structure_facts as volatility


CONTRACT_PATH: Final = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "implementation_plans"
    / "canonical_gold_facts_replay_stage_v1_contract.md"
)

PUBLIC_EXPORTS: Final = (
    "CanonicalGoldFactsReplayCaseV1",
    "CanonicalGoldFactsReplayExpectedOracleV1",
    "CanonicalGoldFactsReplayRegistryRecordV1",
    "CanonicalGoldFactsReplayResultV1",
    "run_canonical_gold_facts_replay_case_v1",
)

PUBLIC_SIGNATURE: Final = """def run_canonical_gold_facts_replay_case_v1(
    *,
    replay_case: CanonicalGoldFactsReplayCaseV1,
) -> CanonicalGoldFactsReplayResultV1:"""

CASE_FIELDS: Final = (
    ("replay_contract_version", "str"),
    ("stage_contract_version", "str"),
    ("stage_id", "str"),
    ("case_id", "str"),
    ("fixture_id", "str"),
)

ORACLE_FIELDS: Final = (
    ("diagnostics_result", "tuple[object, ...]"),
    ("market_source_result", "tuple[object, ...]"),
    ("market_facts_snapshot", "tuple[object, ...]"),
    ("session_spread_freshness_facts", "tuple[object, ...]"),
    ("volatility_structure_facts", "tuple[object, ...]"),
    ("economic_calendar_result", "tuple[object, ...]"),
    ("economic_window_facts", "tuple[object, ...]"),
)

REGISTRY_FIELDS: Final = (
    ("registry_version", "str"),
    ("replay_contract_version", "str"),
    ("stage_contract_version", "str"),
    ("authority_profile_version", "str"),
    ("stage_id", "str"),
    ("case_id", "str"),
    ("fixture_id", "str"),
    ("diagnostics_case", "CanonicalBundleReplayCaseV1"),
    ("market_source_profile_version", "str"),
    ("market_facts_contract_version", "str"),
    ("session_facts_profile_version", "str"),
    ("volatility_facts_profile_version", "str"),
    ("calendar_source_profile_version", "str"),
    ("economic_window_facts_profile_version", "str"),
    ("reference_time_utc", "str"),
    ("expected_market_identity", "tuple[object, ...]"),
    ("expected_calendar_identity", "tuple[object, ...]"),
    ("expected_oracle", "CanonicalGoldFactsReplayExpectedOracleV1"),
)

RESULT_FIELDS: Final = (
    ("replay_contract_version", "str"),
    ("stage_contract_version", "str"),
    ("registry_version", "str"),
    ("stage_id", "str"),
    ("passed", "bool"),
    ("status_code", "str"),
    ("reason_codes", "tuple[str, ...]"),
    ("identity_available", "bool"),
    ("case_id", "str | None"),
    ("fixture_id", "str | None"),
    ("completed_stage_ids", "tuple[str, ...]"),
    ("diagnostics_result", "CanonicalBundleReplayResultV1 | None"),
    (
        "market_source_result",
        "CanonicalGoldMarketFactsSourceAdapterResultV1 | None",
    ),
    ("market_facts_snapshot", "CanonicalGoldMarketFactsSnapshotV1 | None"),
    (
        "session_spread_freshness_facts",
        "CanonicalGoldSessionSpreadFreshnessFactsV1 | None",
    ),
    (
        "volatility_structure_facts",
        "CanonicalGoldVolatilityStructureFactsV1 | None",
    ),
    (
        "economic_calendar_result",
        "CanonicalGoldEconomicCalendarSourceAdapterResultV1 | None",
    ),
    ("economic_window_facts", "CanonicalGoldEconomicWindowFactsV1 | None"),
    ("read_only", "bool"),
    ("demo_only", "bool"),
    ("is_tradable", "bool"),
    ("can_execute", "bool"),
    ("is_trading_permission", "bool"),
    ("is_execution_instruction", "bool"),
    ("allowed_to_call_ea", "bool"),
    ("allowed_to_modify_risk", "bool"),
)

PUBLIC_SCHEMAS: Final = MappingProxyType(
    {
        "CanonicalGoldFactsReplayCaseV1": CASE_FIELDS,
        "CanonicalGoldFactsReplayExpectedOracleV1": ORACLE_FIELDS,
        "CanonicalGoldFactsReplayRegistryRecordV1": REGISTRY_FIELDS,
        "CanonicalGoldFactsReplayResultV1": RESULT_FIELDS,
    }
)

CONTRACT_CONSTANTS: Final = MappingProxyType(
    {
        "REPLAY_CONTRACT_VERSION": "canonical_bundle_replay_v2",
        "STAGE_CONTRACT_VERSION": "canonical_gold_facts_replay_stage_v1",
        "REGISTRY_VERSION": "canonical_gold_facts_replay_registry_v1",
        "AUTHORITY_PROFILE_VERSION": "canonical_gold_facts_replay_authority_v1",
        "STAGE_ID": "canonical_gold_facts",
        "UPSTREAM_REPLAY_CONTRACT_VERSION": "canonical_bundle_replay_v1",
        "UPSTREAM_REPLAY_REGISTRY_VERSION": "canonical_bundle_replay_registry_v1",
        "IDENTIFIER_PATTERN": "^[a-z0-9](?:[a-z0-9_-]{0,62})$",
        "PUBLIC_CODE_PATTERN": "^[A-Z][A-Z0-9_]{0,127}$",
    }
)

PROFILE_CONSTANTS: Final = MappingProxyType(
    {
        "market_source_profile_version": "canonical_gold_market_facts_policy_v1",
        "market_facts_contract_version": "1.0",
        "session_facts_profile_version": (
            "canonical_gold_session_spread_freshness_profile_v1"
        ),
        "volatility_facts_profile_version": (
            "canonical_gold_volatility_structure_profile_v1"
        ),
        "calendar_source_profile_version": (
            "canonical_gold_economic_calendar_source_v1"
        ),
        "economic_window_facts_profile_version": (
            "canonical_gold_economic_window_profile_v1"
        ),
        "reference_time_utc": "2026-07-10T02:30:05.000000Z",
    }
)

MARKET_IDENTITY_FIELDS: Final = (
    "source_contract_version",
    "bundle_schema_version",
    "bundle_id",
    "sequence",
    "canonical_symbol",
    "broker_symbol",
    "reference_time_utc",
)

CALENDAR_IDENTITY_FIELDS: Final = (
    "calendar_contract_version",
    "calendar_schema_version",
    "calendar_snapshot_id",
    "calendar_source_profile_version",
    "calendar_generated_at_utc",
    "calendar_coverage_start_utc",
    "calendar_coverage_end_utc",
)

STAGE_ORDER: Final = (
    "canonical_diagnostics_v1",
    "canonical_gold_market_source_v1",
    "canonical_gold_market_snapshot_v1",
    "canonical_gold_session_spread_freshness_v1",
    "canonical_gold_volatility_structure_v1",
    "canonical_gold_economic_calendar_v1",
    "canonical_gold_economic_window_v1",
)


@dataclass(frozen=True, slots=True)
class OracleAlternativeVector:
    tag: str
    arity: int
    payload_kind: str


ORACLE_ALTERNATIVES: Final = (
    OracleAlternativeVector("NONE_V1", 1, "none"),
    OracleAlternativeVector("BOOL_V1", 2, "exact_bool"),
    OracleAlternativeVector("INT_V1", 2, "exact_int"),
    OracleAlternativeVector("STRING_V1", 2, "exact_str"),
    OracleAlternativeVector("FLOAT_HEX_V1", 2, "canonical_float_hex_str"),
    OracleAlternativeVector("TUPLE_V1", 2, "encoded_tuple"),
    OracleAlternativeVector("LIST_V1", 2, "encoded_tuple"),
    OracleAlternativeVector("DICT_V1", 2, "encoded_pairs"),
    OracleAlternativeVector("DATACLASS_V1", 3, "type_code_and_fields"),
)

ALTERNATIVE_BY_TAG: Final = MappingProxyType(
    {vector.tag: vector for vector in ORACLE_ALTERNATIVES}
)

@dataclass(frozen=True, slots=True)
class ProductionDataclassVector:
    class_object: type[object]
    type_code: str
    ordered_fields: tuple[str, ...]


PRODUCTION_DATACLASS_VECTORS: Final = (
    ProductionDataclassVector(
        replay_v1.CanonicalBundleReplayResultV1,
        "CANONICAL_BUNDLE_REPLAY_RESULT_V1",
        (
            "replay_contract_version",
            "registry_version",
            "pipeline_contract_version",
            "policy_profile_version",
            "case_id",
            "fixture_id",
            "passed",
            "status_code",
            "canonical_summary",
            "replay_reason_codes",
            "canonical_block_reasons",
            "canonical_warning_codes",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_execution_instruction",
            "allowed_to_call_ea",
        ),
    ),
    ProductionDataclassVector(
        market_adapter.CanonicalGoldMarketFactsSourceAdapterResultV1,
        "CANONICAL_GOLD_MARKET_FACTS_SOURCE_ADAPTER_RESULT_V1",
        (
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
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldMarketFactsSourceV1,
        "CANONICAL_GOLD_MARKET_FACTS_SOURCE_V1",
        (
            "contract_version",
            "bundle_schema_version",
            "bundle_id",
            "sequence",
            "canonical_symbol",
            "broker_symbol",
            "reference_time_utc",
            "policy_profile_version",
            "upstream_evidence",
            "live_tick",
            "bars_generated_at_utc",
            "timeframes",
            "symbol_spec",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldUpstreamEvidenceV1,
        "CANONICAL_GOLD_UPSTREAM_EVIDENCE_V1",
        (
            "reader_passed",
            "reader_status_code",
            "value_status_code",
            "data_quality_passed",
            "data_quality_status_code",
            "ready_for_readonly_analysis",
            "warning_codes",
            "same_attempt_identity_bound",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldTickSourceV1,
        "CANONICAL_GOLD_TICK_SOURCE_V1",
        ("bid", "ask", "spread", "spread_points", "digits", "point", "tick_time_utc"),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldTimeframeSourceV1,
        "CANONICAL_GOLD_TIMEFRAME_SOURCE_V1",
        ("timeframe", "period_seconds", "bars"),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldBarSourceV1,
        "CANONICAL_GOLD_BAR_SOURCE_V1",
        (
            "open_time_utc",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread_points",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldSymbolSpecSourceV1,
        "CANONICAL_GOLD_SYMBOL_SPEC_SOURCE_V1",
        (
            "spec_time_utc",
            "digits",
            "point",
            "tick_size",
            "tick_value",
            "contract_size",
            "min_lot",
            "lot_step",
            "max_lot",
            "base_currency",
            "profit_currency",
            "margin_currency",
            "trade_mode_readonly_label",
            "session_status_readonly_label",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldMarketFactsSnapshotV1,
        "CANONICAL_GOLD_MARKET_FACTS_SNAPSHOT_V1",
        (
            "contract_version",
            "passed",
            "status_code",
            "reason_codes",
            "warning_codes",
            "identity_available",
            "bundle_schema_version",
            "bundle_id",
            "sequence",
            "canonical_symbol",
            "broker_symbol",
            "reference_time_utc",
            "quote",
            "timeframes",
            "symbol_spec",
            "freshness",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldQuoteFactsV1,
        "CANONICAL_GOLD_QUOTE_FACTS_V1",
        (
            "bid_decimal",
            "ask_decimal",
            "spread_decimal",
            "spread_points",
            "digits",
            "point_decimal",
            "tick_time_utc",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldTimeframeFactsV1,
        "CANONICAL_GOLD_TIMEFRAME_FACTS_V1",
        ("timeframe", "period_seconds", "bars"),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldBarFactsV1,
        "CANONICAL_GOLD_BAR_FACTS_V1",
        (
            "open_time_utc",
            "open_decimal",
            "high_decimal",
            "low_decimal",
            "close_decimal",
            "tick_volume",
            "spread_points",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldSymbolFactsV1,
        "CANONICAL_GOLD_SYMBOL_FACTS_V1",
        (
            "spec_time_utc",
            "digits",
            "point_decimal",
            "tick_size_decimal",
            "tick_value_decimal",
            "contract_size_decimal",
            "min_lot_decimal",
            "lot_step_decimal",
            "max_lot_decimal",
            "base_currency",
            "profit_currency",
            "margin_currency",
            "trade_mode_readonly_label",
            "session_status_readonly_label",
        ),
    ),
    ProductionDataclassVector(
        market_facts.CanonicalGoldFreshnessFactsV1,
        "CANONICAL_GOLD_FRESHNESS_FACTS_V1",
        (
            "tick_age_microseconds",
            "bars_payload_age_microseconds",
            "symbol_spec_age_microseconds",
        ),
    ),
    ProductionDataclassVector(
        session_facts.CanonicalGoldSessionSpreadFreshnessFactsV1,
        "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FACTS_V1",
        (
            "contract_version",
            "facts_profile_version",
            "passed",
            "status_code",
            "reason_codes",
            "warning_codes",
            "identity_available",
            "bundle_schema_version",
            "bundle_id",
            "sequence",
            "canonical_symbol",
            "broker_symbol",
            "reference_time_utc",
            "session",
            "spread",
            "freshness",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        ),
    ),
    ProductionDataclassVector(
        session_facts.CanonicalGoldSessionFactsV1,
        "CANONICAL_GOLD_SESSION_FACTS_V1",
        (
            "utc_weekday_code",
            "utc_second_of_day",
            "session_bucket_code",
            "window_start_second_utc",
            "window_end_second_utc",
            "seconds_since_window_start",
            "seconds_until_window_end",
            "observed_writer_session_status_label",
        ),
    ),
    ProductionDataclassVector(
        session_facts.CanonicalGoldSpreadFactsV1,
        "CANONICAL_GOLD_SPREAD_FACTS_V1",
        (
            "bid_decimal",
            "ask_decimal",
            "mid_decimal",
            "spread_decimal",
            "spread_points",
            "digits",
            "point_decimal",
            "spread_to_mid_ppm_decimal",
        ),
    ),
    ProductionDataclassVector(
        session_facts.CanonicalGoldSourceFreshnessFactsV1,
        "CANONICAL_GOLD_SOURCE_FRESHNESS_FACTS_V1",
        (
            "tick_age_microseconds",
            "bars_payload_age_microseconds",
            "symbol_spec_age_microseconds",
            "maximum_source_age_microseconds",
            "oldest_source_component_code",
        ),
    ),
    ProductionDataclassVector(
        volatility.CanonicalGoldVolatilityStructureFactsV1,
        "CANONICAL_GOLD_VOLATILITY_STRUCTURE_FACTS_V1",
        (
            "contract_version",
            "facts_profile_version",
            "passed",
            "status_code",
            "reason_codes",
            "warning_codes",
            "identity_available",
            "source_contract_version",
            "bundle_schema_version",
            "bundle_id",
            "sequence",
            "canonical_symbol",
            "broker_symbol",
            "reference_time_utc",
            "timeframes",
            "total_pair_count",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        ),
    ),
    ProductionDataclassVector(
        volatility.CanonicalGoldTimeframeVolatilityStructureFactsV1,
        "CANONICAL_GOLD_TIMEFRAME_VOLATILITY_STRUCTURE_FACTS_V1",
        ("timeframe", "period_seconds", "source_bar_count", "pair_count", "bar_pairs"),
    ),
    ProductionDataclassVector(
        volatility.CanonicalGoldBarPairVolatilityStructureFactsV1,
        "CANONICAL_GOLD_BAR_PAIR_VOLATILITY_STRUCTURE_FACTS_V1",
        (
            "previous_open_time_utc",
            "current_open_time_utc",
            "previous_range_decimal",
            "current_range_decimal",
            "true_range_decimal",
            "body_signed_decimal",
            "body_absolute_decimal",
            "upper_wick_decimal",
            "lower_wick_decimal",
            "close_change_decimal",
            "high_change_decimal",
            "low_change_decimal",
            "direction_code",
            "range_relation_code",
            "range_containment_code",
            "current_high_vs_previous_high_code",
            "current_low_vs_previous_low_code",
            "current_close_vs_previous_range_code",
        ),
    ),
    ProductionDataclassVector(
        calendar.CanonicalGoldEconomicCalendarSourceAdapterResultV1,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_SOURCE_ADAPTER_RESULT_V1",
        (
            "contract_version",
            "passed",
            "status_code",
            "reason_codes",
            "warning_codes",
            "snapshot_available",
            "snapshot",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        ),
    ),
    ProductionDataclassVector(
        economic.CanonicalGoldEconomicCalendarSnapshotV1,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_SNAPSHOT_V1",
        (
            "contract_version",
            "calendar_schema_version",
            "calendar_snapshot_id",
            "source_profile_version",
            "generated_at_utc",
            "coverage_start_utc",
            "coverage_end_utc",
            "events",
            "upstream_evidence",
            "read_only",
            "demo_only",
            "contains_raw_provider_payload",
        ),
    ),
    ProductionDataclassVector(
        economic.CanonicalGoldEconomicCalendarUpstreamEvidenceV1,
        "CANONICAL_GOLD_ECONOMIC_CALENDAR_UPSTREAM_EVIDENCE_V1",
        (
            "adapter_passed",
            "adapter_status_code",
            "schema_validated",
            "identity_validated",
            "timestamps_normalized",
            "same_snapshot_bound",
            "warning_codes",
            "raw_payload_discarded",
        ),
    ),
    ProductionDataclassVector(
        economic.CanonicalGoldEconomicEventSourceV1,
        "CANONICAL_GOLD_ECONOMIC_EVENT_SOURCE_V1",
        (
            "event_id",
            "scheduled_at_utc",
            "country_code",
            "currency_code",
            "event_category_code",
            "impact_code",
            "source_revision",
            "event_status_code",
        ),
    ),
    ProductionDataclassVector(
        economic.CanonicalGoldEconomicWindowFactsV1,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_FACTS_V1",
        (
            "contract_version",
            "facts_profile_version",
            "passed",
            "status_code",
            "reason_codes",
            "warning_codes",
            "identity_available",
            "source_contract_version",
            "bundle_schema_version",
            "bundle_id",
            "sequence",
            "canonical_symbol",
            "broker_symbol",
            "reference_time_utc",
            "calendar_contract_version",
            "calendar_schema_version",
            "calendar_snapshot_id",
            "calendar_source_profile_version",
            "calendar_generated_at_utc",
            "calendar_coverage_start_utc",
            "calendar_coverage_end_utc",
            "event_windows",
            "summary",
            "read_only",
            "demo_only",
            "is_tradable",
            "can_execute",
            "is_trading_permission",
            "is_execution_instruction",
            "allowed_to_call_ea",
            "allowed_to_modify_risk",
        ),
    ),
    ProductionDataclassVector(
        economic.CanonicalGoldEconomicEventWindowFactsV1,
        "CANONICAL_GOLD_ECONOMIC_EVENT_WINDOW_FACTS_V1",
        (
            "event_id",
            "scheduled_at_utc",
            "country_code",
            "currency_code",
            "event_category_code",
            "impact_code",
            "source_revision",
            "window_start_utc",
            "window_end_utc",
            "event_offset_microseconds",
            "window_start_offset_microseconds",
            "window_end_offset_microseconds",
            "window_relation_code",
            "is_active_observation_window",
        ),
    ),
    ProductionDataclassVector(
        economic.CanonicalGoldEconomicWindowSummaryV1,
        "CANONICAL_GOLD_ECONOMIC_WINDOW_SUMMARY_V1",
        (
            "calendar_age_microseconds",
            "relevant_event_count",
            "active_window_count",
            "inside_any_observation_window",
            "active_event_ids",
            "nearest_previous_event_id",
            "nearest_previous_event_offset_microseconds",
            "nearest_next_event_id",
            "nearest_next_event_offset_microseconds",
            "highest_active_impact_code",
        ),
    ),
)

DATACLASS_SCHEMA_BY_CLASS: Final = MappingProxyType(
    {vector.class_object: vector for vector in PRODUCTION_DATACLASS_VECTORS}
)
DATACLASS_SCHEMA_BY_TYPE_CODE: Final = MappingProxyType(
    {vector.type_code: vector for vector in PRODUCTION_DATACLASS_VECTORS}
)

STATUS_REASON_VECTORS: Final = (
    ("CANONICAL_GOLD_FACTS_REPLAY_MATCHED", ()),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID",
        ("GOLD_FACTS_REPLAY_CASE_INPUT_INVALID",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID",
        ("GOLD_FACTS_REPLAY_REGISTRY_INVALID",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID",
        ("GOLD_FACTS_REPLAY_AUTHORITY_INVALID",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_DIAGNOSTICS_BLOCKED",
        ("GOLD_FACTS_REPLAY_DIAGNOSTICS_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_MARKET_SOURCE_BLOCKED",
        ("GOLD_FACTS_REPLAY_MARKET_SOURCE_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_BLOCKED",
        ("GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_SESSION_FACTS_BLOCKED",
        ("GOLD_FACTS_REPLAY_SESSION_FACTS_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_VOLATILITY_FACTS_BLOCKED",
        ("GOLD_FACTS_REPLAY_VOLATILITY_FACTS_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_CALENDAR_BLOCKED",
        ("GOLD_FACTS_REPLAY_CALENDAR_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_BLOCKED",
        ("GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_NOT_READY",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID",
        ("GOLD_FACTS_REPLAY_RESULT_INVALID",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_MISMATCH",
        ("GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH",),
    ),
    (
        "CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE",
        ("GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED",),
    ),
)

FIRST_ERROR_PRIORITY: Final = (
    "public case shape and values",
    "registry shape, version, case resolution, identity, profiles, and oracle",
    "dependency bindings, private authority, and fixed fixture snapshots",
    "existing v1 diagnostics exact type, safe state, oracle, and drift",
    "G185 exact type, safe state, oracle, and drift",
    "G178 exact type, safe state, oracle, identity, and drift",
    "G191 exact type, safe state, oracle, identity, and drift",
    "G196 exact type, safe state, oracle, identity, and drift",
    "G204 exact type, safe state, oracle, identity, and drift",
    "G201 exact type, safe state, oracle, identity, and drift",
    "detached result construction and independent result validation",
    "exception sanitization at the public boundary",
)

CALL_ACCOUNTING: Final = (
    (
        "Case, registry, oracle, dependency, authority, or fixture precheck",
        "Zero",
        "Zero",
    ),
    (
        "Existing v1 diagnostics result",
        "Diagnostics once",
        "G185 and later zero",
    ),
    ("G185 result", "Earlier stages once", "G178 and later zero"),
    ("G178 result", "Earlier stages once", "G191 and later zero"),
    ("G191 result", "Earlier stages once", "G196 and later zero"),
    ("G196 result", "Earlier stages once", "G204 and G201 zero"),
    ("G204 result", "Earlier stages once", "G201 zero"),
    ("G201 result", "Every stage once", "No retry"),
)

FAILURE_CLEARED_FIELDS: Final = MappingProxyType(
    {
        "passed": False,
        "identity_available": False,
        "case_id": None,
        "fixture_id": None,
        "completed_stage_ids": (),
        "diagnostics_result": None,
        "market_source_result": None,
        "market_facts_snapshot": None,
        "session_spread_freshness_facts": None,
        "volatility_structure_facts": None,
        "economic_calendar_result": None,
        "economic_window_facts": None,
    }
)

SAFETY_FLAGS: Final = MappingProxyType(
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

STAGED_DELIVERY: Final = (
    "G208 contract",
    "immutable tests-only contract vectors",
    "production types and bounded replay-stage runner",
    "genuine offline integration evidence using the unmodified production chain",
    "deterministic non-activating replay-stage verification",
)


@dataclass(frozen=True, slots=True)
class InvalidFrozenVector:
    mutation: str
    value: object


class StrictFloatSubclass(float):
    pass


class StrictStringSubclass(str):
    pass


REPLAY_RESULT_VECTOR: Final = DATACLASS_SCHEMA_BY_CLASS[
    replay_v1.CanonicalBundleReplayResultV1
]
EMPTY_REPLAY_RESULT_FIELDS: Final = tuple(
    (name, ("NONE_V1",)) for name in REPLAY_RESULT_VECTOR.ordered_fields
)

INVALID_FROZEN_VECTORS: Final = (
    InvalidFrozenVector("missing_tag", ()),
    InvalidFrozenVector("unknown_tag", ("UNKNOWN_V1",)),
    InvalidFrozenVector("case_changed_tag", ("list_v1", ())),
    InvalidFrozenVector("extra_none_payload", ("NONE_V1", None)),
    InvalidFrozenVector("bool_as_int", ("INT_V1", True)),
    InvalidFrozenVector("int_as_bool", ("BOOL_V1", 1)),
    InvalidFrozenVector("string_subclass", ("STRING_V1", StrictStringSubclass("x"))),
    InvalidFrozenVector("malformed_float", ("FLOAT_HEX_V1", "1.5")),
    InvalidFrozenVector("nan_float", ("FLOAT_HEX_V1", "nan")),
    InvalidFrozenVector("infinite_float", ("FLOAT_HEX_V1", "inf")),
    InvalidFrozenVector("float_payload_subclass", ("FLOAT_HEX_V1", StrictStringSubclass("0x1.0p+0"))),
    InvalidFrozenVector("list_payload_is_list", ("LIST_V1", [])),
    InvalidFrozenVector("tuple_payload_is_list", ("TUPLE_V1", [])),
    InvalidFrozenVector("dict_pair_wrong_arity", ("DICT_V1", ((("STRING_V1", "k"),),))),
    InvalidFrozenVector(
        "unknown_dataclass_type",
        ("DATACLASS_V1", "UNKNOWN_TYPE_V1", ()),
    ),
    InvalidFrozenVector(
        "duplicate_dataclass_field",
        (
            "DATACLASS_V1",
            "CANONICAL_BUNDLE_REPLAY_RESULT_V1",
            (("passed", ("BOOL_V1", True)), ("passed", ("BOOL_V1", True))),
        ),
    ),
    InvalidFrozenVector(
        "dataclass_field_wrong_container",
        (
            "DATACLASS_V1",
            "CANONICAL_BUNDLE_REPLAY_RESULT_V1",
            [["passed", ("BOOL_V1", True)]],
        ),
    ),
    InvalidFrozenVector(
        "missing_dataclass_field",
        (
            "DATACLASS_V1",
            REPLAY_RESULT_VECTOR.type_code,
            EMPTY_REPLAY_RESULT_FIELDS[:-1],
        ),
    ),
    InvalidFrozenVector(
        "extra_dataclass_field",
        (
            "DATACLASS_V1",
            REPLAY_RESULT_VECTOR.type_code,
            EMPTY_REPLAY_RESULT_FIELDS + (("extra", ("NONE_V1",)),),
        ),
    ),
    InvalidFrozenVector(
        "reordered_dataclass_fields",
        (
            "DATACLASS_V1",
            REPLAY_RESULT_VECTOR.type_code,
            (
                EMPTY_REPLAY_RESULT_FIELDS[1],
                EMPTY_REPLAY_RESULT_FIELDS[0],
                *EMPTY_REPLAY_RESULT_FIELDS[2:],
            ),
        ),
    ),
    InvalidFrozenVector(
        "aliased_dataclass_field",
        (
            "DATACLASS_V1",
            REPLAY_RESULT_VECTOR.type_code,
            (
                ("replay_version", ("NONE_V1",)),
                *EMPTY_REPLAY_RESULT_FIELDS[1:],
            ),
        ),
    ),
    InvalidFrozenVector(
        "duplicate_dict_key",
        (
            "DICT_V1",
            (
                (("STRING_V1", "same"), ("INT_V1", 1)),
                (("STRING_V1", "same"), ("INT_V1", 2)),
            ),
        ),
    ),
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="ascii")


def _public_exports(text: str) -> tuple[str, ...]:
    match = re.search(
        r'(?ms)^__all__ = \(\n(?P<body>.*?)^\)$',
        text,
    )
    assert match is not None
    return tuple(re.findall(r'^\s+"([^"]+)",$', match.group("body"), re.MULTILINE))


def _class_fields(text: str, class_name: str) -> tuple[tuple[str, str], ...]:
    match = re.search(
        rf"(?ms)^class {re.escape(class_name)}:\n"
        rf"(?P<body>(?:    [^\n]+\n)+)",
        text,
    )
    assert match is not None
    return tuple(
        (field, annotation)
        for field, annotation in re.findall(
            r"^    ([a-z_][a-z0-9_]*): (.+)$",
            match.group("body"),
            re.MULTILINE,
        )
    )


def _constant_rows(text: str) -> dict[str, str]:
    return {
        name: value
        for name, value in re.findall(
            r"^([A-Z][A-Z0-9_]+) = ([^\n]+)$",
            text,
            re.MULTILINE,
        )
    }


def _profile_rows(text: str) -> dict[str, str]:
    return {
        name: value
        for name, value in re.findall(
            r"^([a-z][a-z0-9_]+) = ([^\n]+)$",
            text,
            re.MULTILINE,
        )
        if name in PROFILE_CONSTANTS
    }


def _stage_order(text: str) -> tuple[str, ...]:
    match = re.search(
        r"(?ms)^STAGE_ORDER = \(\n(?P<body>.*?)^\)$",
        text,
    )
    assert match is not None
    return tuple(
        re.findall(r"^    ([a-z0-9_]+),$", match.group("body"), re.MULTILINE)
    )


def _status_rows(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    rows: list[tuple[str, tuple[str, ...]]] = []
    for status, reasons in re.findall(
        r"^\| `([A-Z][A-Z0-9_]+)` \| `(\([^`]*\))` \|$",
        text,
        re.MULTILINE,
    ):
        if reasons == "()":
            parsed = ()
        else:
            parsed = tuple(re.findall(r'"([A-Z][A-Z0-9_]+)"', reasons))
        rows.append((status, parsed))
    return tuple(rows)


def _numbered_priority(text: str) -> tuple[str, ...]:
    section = text.split("The deterministic first-error priority is:\n", 1)[1]
    section = section.split("\n\nWithin a stage", 1)[0]
    values: list[str] = []
    current = ""
    for line in section.splitlines():
        match = re.match(r"^\d+\. (.+?)(?:;|; and|\. and)?$", line)
        if match is not None:
            if current:
                values.append(current)
            current = match.group(1)
        elif line.startswith("   "):
            current += " " + line.strip()
    if current:
        values.append(current)
    return tuple(
        value.removesuffix("; and").removesuffix(";").removesuffix(".")
        for value in values
    )


def _table_rows(
    text: str,
    *,
    first_column: str,
) -> tuple[tuple[str, str, str], ...]:
    lines = text.splitlines()
    header = f"| {first_column} | Earlier calls | Current and later calls |"
    start = lines.index(header)
    rows: list[tuple[str, str, str]] = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        assert len(cells) == 3
        rows.append(cells)
    return tuple(rows)


def _identity_fields(text: str, name: str) -> tuple[str, ...]:
    match = re.search(
        rf"(?ms)^{re.escape(name)} = \(\n(?P<body>.*?)^\)$",
        text,
    )
    assert match is not None
    return tuple(
        re.findall(
            r"^    ([a-z_][a-z0-9_]*): exact (?:str|int),$",
            match.group("body"),
            re.MULTILINE,
        )
    )


def _staged_delivery(text: str) -> tuple[str, ...]:
    match = re.search(
        r"(?ms)^1\. G208 contract\n"
        r"2\. immutable tests-only contract vectors\n"
        r"3\. production types and bounded replay-stage runner\n"
        r"4\. genuine offline integration evidence using the unmodified production chain\n"
        r"5\. deterministic non-activating replay-stage verification$",
        text,
    )
    assert match is not None
    return tuple(line.split(". ", 1)[1] for line in match.group(0).splitlines())


def _is_valid_frozen_value(value: object) -> bool:
    if type(value) is not tuple or not value or type(value[0]) is not str:
        return False
    tag = value[0]
    vector = ALTERNATIVE_BY_TAG.get(tag)
    if vector is None or len(value) != vector.arity:
        return False
    if tag == "NONE_V1":
        return True
    if tag == "BOOL_V1":
        return type(value[1]) is bool
    if tag == "INT_V1":
        return type(value[1]) is int
    if tag == "STRING_V1":
        return type(value[1]) is str
    if tag == "FLOAT_HEX_V1":
        return _is_canonical_finite_float_hex(value[1])
    if tag in {"TUPLE_V1", "LIST_V1"}:
        return type(value[1]) is tuple and all(
            _is_valid_frozen_value(item) for item in value[1]
        )
    if tag == "DICT_V1":
        if type(value[1]) is not tuple or not all(
            type(pair) is tuple
            and len(pair) == 2
            and _is_valid_frozen_value(pair[0])
            and _is_valid_frozen_value(pair[1])
            for pair in value[1]
        ):
            return False
        keys = tuple(pair[0] for pair in value[1])
        return len(keys) == len(set(keys))
    if tag == "DATACLASS_V1":
        if (
            type(value[1]) is not str
            or type(value[2]) is not tuple
        ):
            return False
        schema = DATACLASS_SCHEMA_BY_TYPE_CODE.get(value[1])
        if schema is None:
            return False
        names: list[str] = []
        for pair in value[2]:
            if (
                type(pair) is not tuple
                or len(pair) != 2
                or type(pair[0]) is not str
                or not pair[0]
                or not _is_valid_frozen_value(pair[1])
            ):
                return False
            names.append(pair[0])
        return tuple(names) == schema.ordered_fields
    return False


def _is_canonical_finite_float_hex(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        decoded = float.fromhex(value)
    except (OverflowError, ValueError):
        return False
    return math.isfinite(decoded) and decoded.hex() == value


def _freeze_real_value(
    value: object,
    *,
    allow_summary_containers: bool = False,
    allow_market_floats: bool = False,
) -> tuple[object, ...]:
    value_type = type(value)
    if value is None:
        return ("NONE_V1",)
    if value_type is bool:
        return ("BOOL_V1", value)
    if value_type is int:
        return ("INT_V1", value)
    if value_type is str:
        return ("STRING_V1", value)
    if value_type is float:
        if not allow_market_floats or not math.isfinite(value):
            raise TypeError("unsupported float")
        payload = value.hex()
        if type(payload) is not str or float.fromhex(payload).hex() != payload:
            raise TypeError("noncanonical float")
        return ("FLOAT_HEX_V1", payload)
    if value_type is tuple:
        return (
            "TUPLE_V1",
            tuple(
                _freeze_real_value(
                    item,
                    allow_summary_containers=allow_summary_containers,
                    allow_market_floats=allow_market_floats,
                )
                for item in value
            ),
        )
    if value_type is list:
        if not allow_summary_containers:
            raise TypeError("list outside diagnostics summary")
        return (
            "LIST_V1",
            tuple(
                _freeze_real_value(item, allow_summary_containers=True)
                for item in value
            ),
        )
    if value_type is dict:
        if not allow_summary_containers:
            raise TypeError("dict outside diagnostics summary")
        return (
            "DICT_V1",
            tuple(
                (
                    _freeze_real_value(key, allow_summary_containers=True),
                    _freeze_real_value(item, allow_summary_containers=True),
                )
                for key, item in value.items()
            ),
        )
    if is_dataclass(value) and not isinstance(value, type):
        schema = DATACLASS_SCHEMA_BY_CLASS.get(value_type)
        if schema is None:
            raise TypeError("unregistered dataclass")
        if tuple(field.name for field in fields(value)) != schema.ordered_fields:
            raise TypeError("registered dataclass schema drift")
        encoded_fields: list[tuple[str, tuple[object, ...]]] = []
        for field_name in schema.ordered_fields:
            is_summary = (
                value_type is replay_v1.CanonicalBundleReplayResultV1
                and field_name == "canonical_summary"
            )
            encoded_fields.append(
                (
                    field_name,
                    _freeze_real_value(
                        getattr(value, field_name),
                        allow_summary_containers=is_summary,
                        allow_market_floats=allow_market_floats,
                    ),
                )
            )
        return ("DATACLASS_V1", schema.type_code, tuple(encoded_fields))
    raise TypeError("unsupported value")


def _walk_frozen(value: tuple[object, ...]) -> tuple[tuple[object, ...], ...]:
    nodes = [value]
    tag = value[0]
    if tag in {"TUPLE_V1", "LIST_V1"}:
        for item in value[1]:
            nodes.extend(_walk_frozen(item))
    elif tag == "DICT_V1":
        for key, item in value[1]:
            nodes.extend(_walk_frozen(key))
            nodes.extend(_walk_frozen(item))
    elif tag == "DATACLASS_V1":
        for _, item in value[2]:
            nodes.extend(_walk_frozen(item))
    return tuple(nodes)


EXPECTED_PROFILE_VECTOR: Final = (
    ("market_source_profile_version", "canonical_gold_market_facts_policy_v1"),
    ("market_facts_contract_version", "1.0"),
    (
        "session_facts_profile_version",
        "canonical_gold_session_spread_freshness_profile_v1",
    ),
    (
        "volatility_facts_profile_version",
        "canonical_gold_volatility_structure_profile_v1",
    ),
    (
        "calendar_source_profile_version",
        "canonical_gold_economic_calendar_source_v1",
    ),
    (
        "economic_window_facts_profile_version",
        "canonical_gold_economic_window_profile_v1",
    ),
    ("reference_time_utc", "2026-07-10T02:30:05.000000Z"),
)

EXPECTED_DIAGNOSTICS_IDENTITY: Final = (
    "canonical_bundle_replay_v1",
    "canonical_bundle_replay_registry_v1",
    "canonical_diagnostics_pipeline_g153_v1",
    "canonical_diagnostics_default_policy_v1",
    "canonical_docs_ready",
    "canonical_docs_fixture_v1",
)

EXPECTED_MARKET_IDENTITY: Final = (
    "1.0",
    "1.0",
    "demo-bundle-000000000001",
    1,
    "XAUUSD",
    "GOLD",
    "2026-07-10T02:30:05.000000Z",
)

EXPECTED_DIAGNOSTICS_ORACLE: Final = (
    "DATACLASS_V1",
    "CANONICAL_BUNDLE_REPLAY_RESULT_V1",
    (
        ("replay_contract_version", ("STRING_V1", "canonical_bundle_replay_v1")),
        (
            "registry_version",
            ("STRING_V1", "canonical_bundle_replay_registry_v1"),
        ),
        (
            "pipeline_contract_version",
            ("STRING_V1", "canonical_diagnostics_pipeline_g153_v1"),
        ),
        (
            "policy_profile_version",
            ("STRING_V1", "canonical_diagnostics_default_policy_v1"),
        ),
        ("case_id", ("STRING_V1", "canonical_docs_ready")),
        ("fixture_id", ("STRING_V1", "canonical_docs_fixture_v1")),
        ("passed", ("BOOL_V1", True)),
        ("status_code", ("STRING_V1", "CANONICAL_BUNDLE_REPLAY_MATCHED")),
        (
            "canonical_summary",
            (
                "DICT_V1",
                (
                    (("STRING_V1", "passed"), ("BOOL_V1", True)),
                    (
                        ("STRING_V1", "status_code"),
                        ("STRING_V1", "CANONICAL_DIAGNOSTICS_SUMMARY_READY"),
                    ),
                    (
                        ("STRING_V1", "source_scope"),
                        (
                            "STRING_V1",
                            "canonical_mt4_demo_readonly_data_quality_summary_only",
                        ),
                    ),
                    (
                        ("STRING_V1", "validation_stage"),
                        (
                            "STRING_V1",
                            "canonical_bundle_v1_diagnostics_summary_adapter",
                        ),
                    ),
                    (
                        ("STRING_V1", "fixture_source"),
                        (
                            "STRING_V1",
                            "canonical_bundle_v1_data_quality_gate_result",
                        ),
                    ),
                    (
                        ("STRING_V1", "bundle_validation_status"),
                        (
                            "DICT_V1",
                            (
                                (("STRING_V1", "passed"), ("BOOL_V1", True)),
                                (
                                    ("STRING_V1", "status_code"),
                                    (
                                        "STRING_V1",
                                        "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
                                    ),
                                ),
                                (
                                    ("STRING_V1", "block_reasons"),
                                    ("LIST_V1", ()),
                                ),
                                (
                                    ("STRING_V1", "warning_reasons"),
                                    ("LIST_V1", ()),
                                ),
                                (("STRING_V1", "read_only"), ("BOOL_V1", True)),
                                (("STRING_V1", "demo_only"), ("BOOL_V1", True)),
                                (("STRING_V1", "is_tradable"), ("BOOL_V1", False)),
                                (("STRING_V1", "can_execute"), ("BOOL_V1", False)),
                            ),
                        ),
                    ),
                    (
                        ("STRING_V1", "component_statuses"),
                        (
                            "DICT_V1",
                            (
                                (
                                    ("STRING_V1", "canonical_data_quality_gate"),
                                    (
                                        "DICT_V1",
                                        (
                                            (
                                                ("STRING_V1", "passed"),
                                                ("BOOL_V1", True),
                                            ),
                                            (
                                                ("STRING_V1", "status_code"),
                                                (
                                                    "STRING_V1",
                                                    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
                                                ),
                                            ),
                                            (
                                                ("STRING_V1", "block_reasons"),
                                                ("LIST_V1", ()),
                                            ),
                                            (
                                                ("STRING_V1", "warning_reasons"),
                                                ("LIST_V1", ()),
                                            ),
                                            (
                                                ("STRING_V1", "read_only"),
                                                ("BOOL_V1", True),
                                            ),
                                            (
                                                ("STRING_V1", "demo_only"),
                                                ("BOOL_V1", True),
                                            ),
                                            (
                                                ("STRING_V1", "is_tradable"),
                                                ("BOOL_V1", False),
                                            ),
                                            (
                                                ("STRING_V1", "can_execute"),
                                                ("BOOL_V1", False),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (("STRING_V1", "block_reasons"), ("LIST_V1", ())),
                    (("STRING_V1", "warning_reasons"), ("LIST_V1", ())),
                    (
                        ("STRING_V1", "readiness_notes"),
                        (
                            "LIST_V1",
                            (
                                (
                                    "STRING_V1",
                                    "Canonical DataQualityGate passed for read-only diagnostics adaptation.",
                                ),
                                (
                                    "STRING_V1",
                                    "Readiness is not trading permission.",
                                ),
                                (
                                    "STRING_V1",
                                    "This summary is read-only and cannot execute orders.",
                                ),
                            ),
                        ),
                    ),
                    (
                        ("STRING_V1", "next_allowed_stage"),
                        (
                            "LIST_V1",
                            (
                                (
                                    "STRING_V1",
                                    "demo_readonly_diagnostics_response_integration",
                                ),
                            ),
                        ),
                    ),
                    (
                        ("STRING_V1", "next_blocked_stage"),
                        (
                            "LIST_V1",
                            (
                                ("STRING_V1", "api_reader_activation"),
                                ("STRING_V1", "execution_chain"),
                            ),
                        ),
                    ),
                    (("STRING_V1", "read_only"), ("BOOL_V1", True)),
                    (("STRING_V1", "demo_only"), ("BOOL_V1", True)),
                    (("STRING_V1", "is_tradable"), ("BOOL_V1", False)),
                    (("STRING_V1", "can_execute"), ("BOOL_V1", False)),
                    (
                        ("STRING_V1", "is_trading_permission"),
                        ("BOOL_V1", False),
                    ),
                    (
                        ("STRING_V1", "is_execution_instruction"),
                        ("BOOL_V1", False),
                    ),
                    (("STRING_V1", "allowed_to_call_ea"), ("BOOL_V1", False)),
                    (
                        ("STRING_V1", "allowed_to_modify_risk"),
                        ("BOOL_V1", False),
                    ),
                ),
            ),
        ),
        ("replay_reason_codes", ("TUPLE_V1", ())),
        ("canonical_block_reasons", ("TUPLE_V1", ())),
        ("canonical_warning_codes", ("TUPLE_V1", ())),
        ("read_only", ("BOOL_V1", True)),
        ("demo_only", ("BOOL_V1", True)),
        ("is_tradable", ("BOOL_V1", False)),
        ("can_execute", ("BOOL_V1", False)),
        ("is_execution_instruction", ("BOOL_V1", False)),
        ("allowed_to_call_ea", ("BOOL_V1", False)),
    ),
)

EXPECTED_MARKET_RESULT: Final = (
    market_adapter.CanonicalGoldMarketFactsSourceAdapterResultV1(
        contract_version="1.0",
        passed=True,
        status_code="CANONICAL_GOLD_SOURCE_ADAPTER_READY",
        reason_codes=(),
        warning_codes=(),
        source_available=True,
        source=market_facts.CanonicalGoldMarketFactsSourceV1(
            contract_version="1.0",
            bundle_schema_version="1.0",
            bundle_id="demo-bundle-000000000001",
            sequence=1,
            canonical_symbol="XAUUSD",
            broker_symbol="GOLD",
            reference_time_utc="2026-07-10T02:30:05.000000Z",
            policy_profile_version="canonical_gold_market_facts_policy_v1",
            upstream_evidence=market_facts.CanonicalGoldUpstreamEvidenceV1(
                reader_passed=True,
                reader_status_code="CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID",
                value_status_code="CANONICAL_MT4_BUNDLE_V1_VALUE_VALID",
                data_quality_passed=True,
                data_quality_status_code=(
                    "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED"
                ),
                ready_for_readonly_analysis=True,
                warning_codes=(),
                same_attempt_identity_bound=True,
            ),
            live_tick=market_facts.CanonicalGoldTickSourceV1(
                bid=2300.5,
                ask=2300.8,
                spread=0.3,
                spread_points=30,
                digits=2,
                point=0.01,
                tick_time_utc="2026-07-10T02:30:00Z",
            ),
            bars_generated_at_utc="2026-07-10T02:30:00Z",
            timeframes=(
                market_facts.CanonicalGoldTimeframeSourceV1(
                    timeframe="M15",
                    period_seconds=900,
                    bars=(
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-10T02:00:00Z",
                            2299.6,
                            2301.1,
                            2298.9,
                            2300.2,
                            1240,
                            30,
                        ),
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-10T02:15:00Z",
                            2300.2,
                            2301.4,
                            2299.8,
                            2300.8,
                            830,
                            30,
                        ),
                    ),
                ),
                market_facts.CanonicalGoldTimeframeSourceV1(
                    timeframe="H1",
                    period_seconds=3600,
                    bars=(
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-10T00:00:00Z",
                            2296.4,
                            2300.7,
                            2295.9,
                            2299.7,
                            4100,
                            31,
                        ),
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-10T01:00:00Z",
                            2299.7,
                            2301.4,
                            2298.9,
                            2300.8,
                            2950,
                            30,
                        ),
                    ),
                ),
                market_facts.CanonicalGoldTimeframeSourceV1(
                    timeframe="H4",
                    period_seconds=14400,
                    bars=(
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-09T16:00:00Z",
                            2288.5,
                            2298.2,
                            2287.9,
                            2296.4,
                            12300,
                            32,
                        ),
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-09T20:00:00Z",
                            2296.4,
                            2301.4,
                            2295.9,
                            2300.8,
                            8400,
                            30,
                        ),
                    ),
                ),
                market_facts.CanonicalGoldTimeframeSourceV1(
                    timeframe="D1",
                    period_seconds=86400,
                    bars=(
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-08T00:00:00Z",
                            2269.4,
                            2281.0,
                            2266.8,
                            2278.2,
                            49800,
                            33,
                        ),
                        market_facts.CanonicalGoldBarSourceV1(
                            "2026-07-09T00:00:00Z",
                            2278.2,
                            2298.2,
                            2275.6,
                            2296.4,
                            53000,
                            32,
                        ),
                    ),
                ),
            ),
            symbol_spec=market_facts.CanonicalGoldSymbolSpecSourceV1(
                spec_time_utc="2026-07-10T02:30:00Z",
                digits=2,
                point=0.01,
                tick_size=0.01,
                tick_value=1.0,
                contract_size=100.0,
                min_lot=0.01,
                lot_step=0.01,
                max_lot=50.0,
                base_currency="XAU",
                profit_currency="USD",
                margin_currency="USD",
                trade_mode_readonly_label="readonly_metadata_only",
                session_status_readonly_label="unknown",
            ),
        ),
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
        is_trading_permission=False,
        is_execution_instruction=False,
        allowed_to_call_ea=False,
        allowed_to_modify_risk=False,
    )
)

EXPECTED_MARKET_ORACLE: Final = (
    "DATACLASS_V1",
    "CANONICAL_GOLD_MARKET_FACTS_SOURCE_ADAPTER_RESULT_V1",
    (
        ("contract_version", ("STRING_V1", "1.0")),
        ("passed", ("BOOL_V1", True)),
        ("status_code", ("STRING_V1", "CANONICAL_GOLD_SOURCE_ADAPTER_READY")),
        ("reason_codes", ("TUPLE_V1", ())),
        ("warning_codes", ("TUPLE_V1", ())),
        ("source_available", ("BOOL_V1", True)),
        (
            "source",
            (
                "DATACLASS_V1",
                "CANONICAL_GOLD_MARKET_FACTS_SOURCE_V1",
                (
                    ("contract_version", ("STRING_V1", "1.0")),
                    ("bundle_schema_version", ("STRING_V1", "1.0")),
                    (
                        "bundle_id",
                        ("STRING_V1", "demo-bundle-000000000001"),
                    ),
                    ("sequence", ("INT_V1", 1)),
                    ("canonical_symbol", ("STRING_V1", "XAUUSD")),
                    ("broker_symbol", ("STRING_V1", "GOLD")),
                    (
                        "reference_time_utc",
                        ("STRING_V1", "2026-07-10T02:30:05.000000Z"),
                    ),
                    (
                        "policy_profile_version",
                        (
                            "STRING_V1",
                            "canonical_gold_market_facts_policy_v1",
                        ),
                    ),
                    (
                        "upstream_evidence",
                        (
                            "DATACLASS_V1",
                            "CANONICAL_GOLD_UPSTREAM_EVIDENCE_V1",
                            (
                                ("reader_passed", ("BOOL_V1", True)),
                                (
                                    "reader_status_code",
                                    (
                                        "STRING_V1",
                                        "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID",
                                    ),
                                ),
                                (
                                    "value_status_code",
                                    (
                                        "STRING_V1",
                                        "CANONICAL_MT4_BUNDLE_V1_VALUE_VALID",
                                    ),
                                ),
                                ("data_quality_passed", ("BOOL_V1", True)),
                                (
                                    "data_quality_status_code",
                                    (
                                        "STRING_V1",
                                        "CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED",
                                    ),
                                ),
                                (
                                    "ready_for_readonly_analysis",
                                    ("BOOL_V1", True),
                                ),
                                ("warning_codes", ("TUPLE_V1", ())),
                                (
                                    "same_attempt_identity_bound",
                                    ("BOOL_V1", True),
                                ),
                            ),
                        ),
                    ),
                    (
                        "live_tick",
                        (
                            "DATACLASS_V1",
                            "CANONICAL_GOLD_TICK_SOURCE_V1",
                            (
                                (
                                    "bid",
                                    ("FLOAT_HEX_V1", "0x1.1f90000000000p+11"),
                                ),
                                (
                                    "ask",
                                    ("FLOAT_HEX_V1", "0x1.1f9999999999ap+11"),
                                ),
                                (
                                    "spread",
                                    ("FLOAT_HEX_V1", "0x1.3333333333333p-2"),
                                ),
                                ("spread_points", ("INT_V1", 30)),
                                ("digits", ("INT_V1", 2)),
                                (
                                    "point",
                                    ("FLOAT_HEX_V1", "0x1.47ae147ae147bp-7"),
                                ),
                                (
                                    "tick_time_utc",
                                    ("STRING_V1", "2026-07-10T02:30:00Z"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "bars_generated_at_utc",
                        ("STRING_V1", "2026-07-10T02:30:00Z"),
                    ),
                    (
                        "timeframes",
                        (
                            "TUPLE_V1",
                            (
                                (
                                    "DATACLASS_V1",
                                    "CANONICAL_GOLD_TIMEFRAME_SOURCE_V1",
                                    (
                                        ("timeframe", ("STRING_V1", "M15")),
                                        ("period_seconds", ("INT_V1", 900)),
                                        (
                                            "bars",
                                            (
                                                "TUPLE_V1",
                                                (
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-10T02:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f73333333333p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1fa3333333333p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f5cccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f86666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 1240),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 30),
                                                            ),
                                                        ),
                                                    ),
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-10T02:15:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f86666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1facccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f7999999999ap+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f9999999999ap+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 830),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 30),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "DATACLASS_V1",
                                    "CANONICAL_GOLD_TIMEFRAME_SOURCE_V1",
                                    (
                                        ("timeframe", ("STRING_V1", "H1")),
                                        ("period_seconds", ("INT_V1", 3600)),
                                        (
                                            "bars",
                                            (
                                                "TUPLE_V1",
                                                (
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-10T00:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f0cccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f96666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1efcccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f76666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 4100),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 31),
                                                            ),
                                                        ),
                                                    ),
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-10T01:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f76666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1facccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f5cccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f9999999999ap+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 2950),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 30),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "DATACLASS_V1",
                                    "CANONICAL_GOLD_TIMEFRAME_SOURCE_V1",
                                    (
                                        ("timeframe", ("STRING_V1", "H4")),
                                        ("period_seconds", ("INT_V1", 14400)),
                                        (
                                            "bars",
                                            (
                                                "TUPLE_V1",
                                                (
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-09T16:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1e10000000000p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f46666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1dfcccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f0cccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 12300),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 32),
                                                            ),
                                                        ),
                                                    ),
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-09T20:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f0cccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1facccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1efcccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f9999999999ap+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 8400),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 30),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "DATACLASS_V1",
                                    "CANONICAL_GOLD_TIMEFRAME_SOURCE_V1",
                                    (
                                        ("timeframe", ("STRING_V1", "D1")),
                                        ("period_seconds", ("INT_V1", 86400)),
                                        (
                                            "bars",
                                            (
                                                "TUPLE_V1",
                                                (
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-08T00:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1bacccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1d20000000000p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1b5999999999ap+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1cc6666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 49800),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 33),
                                                            ),
                                                        ),
                                                    ),
                                                    (
                                                        "DATACLASS_V1",
                                                        "CANONICAL_GOLD_BAR_SOURCE_V1",
                                                        (
                                                            (
                                                                "open_time_utc",
                                                                (
                                                                    "STRING_V1",
                                                                    "2026-07-09T00:00:00Z",
                                                                ),
                                                            ),
                                                            (
                                                                "open",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1cc6666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "high",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f46666666666p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "low",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1c73333333333p+11",
                                                                ),
                                                            ),
                                                            (
                                                                "close",
                                                                (
                                                                    "FLOAT_HEX_V1",
                                                                    "0x1.1f0cccccccccdp+11",
                                                                ),
                                                            ),
                                                            (
                                                                "tick_volume",
                                                                ("INT_V1", 53000),
                                                            ),
                                                            (
                                                                "spread_points",
                                                                ("INT_V1", 32),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "symbol_spec",
                        (
                            "DATACLASS_V1",
                            "CANONICAL_GOLD_SYMBOL_SPEC_SOURCE_V1",
                            (
                                (
                                    "spec_time_utc",
                                    ("STRING_V1", "2026-07-10T02:30:00Z"),
                                ),
                                ("digits", ("INT_V1", 2)),
                                (
                                    "point",
                                    ("FLOAT_HEX_V1", "0x1.47ae147ae147bp-7"),
                                ),
                                (
                                    "tick_size",
                                    ("FLOAT_HEX_V1", "0x1.47ae147ae147bp-7"),
                                ),
                                (
                                    "tick_value",
                                    ("FLOAT_HEX_V1", "0x1.0000000000000p+0"),
                                ),
                                (
                                    "contract_size",
                                    ("FLOAT_HEX_V1", "0x1.9000000000000p+6"),
                                ),
                                (
                                    "min_lot",
                                    ("FLOAT_HEX_V1", "0x1.47ae147ae147bp-7"),
                                ),
                                (
                                    "lot_step",
                                    ("FLOAT_HEX_V1", "0x1.47ae147ae147bp-7"),
                                ),
                                (
                                    "max_lot",
                                    ("FLOAT_HEX_V1", "0x1.9000000000000p+5"),
                                ),
                                ("base_currency", ("STRING_V1", "XAU")),
                                ("profit_currency", ("STRING_V1", "USD")),
                                ("margin_currency", ("STRING_V1", "USD")),
                                (
                                    "trade_mode_readonly_label",
                                    ("STRING_V1", "readonly_metadata_only"),
                                ),
                                (
                                    "session_status_readonly_label",
                                    ("STRING_V1", "unknown"),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        ("read_only", ("BOOL_V1", True)),
        ("demo_only", ("BOOL_V1", True)),
        ("is_tradable", ("BOOL_V1", False)),
        ("can_execute", ("BOOL_V1", False)),
        ("is_trading_permission", ("BOOL_V1", False)),
        ("is_execution_instruction", ("BOOL_V1", False)),
        ("allowed_to_call_ea", ("BOOL_V1", False)),
        ("allowed_to_modify_risk", ("BOOL_V1", False)),
    ),
)


def test_vectors_are_immutable_and_public_schemas_are_exact() -> None:
    assert tuple(PUBLIC_SCHEMAS) == PUBLIC_EXPORTS[:-1]
    assert tuple(len(value) for value in PUBLIC_SCHEMAS.values()) == (5, 7, 18, 26)
    assert type(PUBLIC_EXPORTS) is tuple
    assert type(ORACLE_ALTERNATIVES) is tuple
    assert type(PRODUCTION_DATACLASS_VECTORS) is tuple
    assert type(DATACLASS_SCHEMA_BY_CLASS) is MappingProxyType
    assert type(DATACLASS_SCHEMA_BY_TYPE_CODE) is MappingProxyType
    assert len(PRODUCTION_DATACLASS_VECTORS) == 28
    assert len(DATACLASS_SCHEMA_BY_CLASS) == len(PRODUCTION_DATACLASS_VECTORS)
    assert len(DATACLASS_SCHEMA_BY_TYPE_CODE) == len(PRODUCTION_DATACLASS_VECTORS)
    assert tuple(PROFILE_CONSTANTS.items()) == EXPECTED_PROFILE_VECTOR
    assert type(EXPECTED_DIAGNOSTICS_IDENTITY) is tuple
    assert type(EXPECTED_MARKET_IDENTITY) is tuple
    assert type(EXPECTED_DIAGNOSTICS_ORACLE) is tuple
    assert type(EXPECTED_MARKET_ORACLE) is tuple
    for vector in PRODUCTION_DATACLASS_VECTORS:
        assert type(vector.class_object) is type
        assert type(vector.type_code) is str
        assert type(vector.ordered_fields) is tuple
        assert tuple(field.name for field in fields(vector.class_object)) == (
            vector.ordered_fields
        )
        assert DATACLASS_SCHEMA_BY_CLASS[vector.class_object] is vector
        assert DATACLASS_SCHEMA_BY_TYPE_CODE[vector.type_code] is vector
    with pytest.raises(TypeError):
        PUBLIC_SCHEMAS["extra"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        DATACLASS_SCHEMA_BY_CLASS[object] = REPLAY_RESULT_VECTOR  # type: ignore[index]
    with pytest.raises((AttributeError, TypeError)):
        ORACLE_ALTERNATIVES[0].tag = "CHANGED"  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        EXPECTED_MARKET_RESULT.passed = False  # type: ignore[misc]


def test_contract_locks_exports_signature_schemas_and_versions() -> None:
    text = _contract_text()
    assert _public_exports(text) == PUBLIC_EXPORTS
    assert PUBLIC_SIGNATURE in text
    for class_name, expected_fields in PUBLIC_SCHEMAS.items():
        assert _class_fields(text, class_name) == expected_fields
    constants = _constant_rows(text)
    assert {
        name: constants[name] for name in CONTRACT_CONSTANTS
    } == dict(CONTRACT_CONSTANTS)
    assert _profile_rows(text) == dict(PROFILE_CONSTANTS)
    assert "`canonical_bundle_replay_v2` is a new future wrapper contract" in text
    assert "The future v2 implementation must call the existing" in text
    assert "`run_canonical_bundle_replay_case` entry point" in text
    assert "It must not copy v1, call G153" in text


def test_oracle_grammar_type_codes_and_identity_shapes_are_closed() -> None:
    text = _contract_text()
    normalized_text = " ".join(text.split())
    assert tuple(vector.tag for vector in ORACLE_ALTERNATIVES) == (
        "NONE_V1",
        "BOOL_V1",
        "INT_V1",
        "STRING_V1",
        "FLOAT_HEX_V1",
        "TUPLE_V1",
        "LIST_V1",
        "DICT_V1",
        "DATACLASS_V1",
    )
    assert all(tag in text for tag in ALTERNATIVE_BY_TAG)
    assert _identity_fields(text, "expected_market_identity") == MARKET_IDENTITY_FIELDS
    assert (
        _identity_fields(text, "expected_calendar_identity")
        == CALENDAR_IDENTITY_FIELDS
    )
    assert (
        "one closed mapping from each exact production class object"
        in normalized_text
    )
    assert "one unique fixed ASCII type code" in text
    assert "require exact class identity and the complete declared field order" in text
    assert "accepting finite floats only in validator-approved G185 source fields" in text
    assert "accepting dicts and lists only in the validator-approved v1" in text


def test_real_v1_and_g185_ready_results_are_representable_without_mutation() -> None:
    replay_case = replay_v1.CanonicalBundleReplayCaseV1(
        replay_contract_version=replay_v1.REPLAY_CONTRACT_VERSION,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
    )
    diagnostics = replay_v1.run_canonical_bundle_replay_case(replay_case=replay_case)
    market = market_fixture.build_canonical_gold_market_facts_docs_fixture_source_v1()
    assert diagnostics.passed is True
    assert diagnostics.status_code == replay_v1.CANONICAL_BUNDLE_REPLAY_MATCHED
    assert (
        market_adapter._is_safe_canonical_gold_market_facts_source_adapter_result_v1(
            result=market
        )
        is True
    )
    assert market.passed is True
    assert market.source_available is True
    assert market.source is not None
    diagnostics_before = deepcopy(diagnostics)
    market_before = deepcopy(market)

    frozen_diagnostics = _freeze_real_value(diagnostics)
    frozen_market = _freeze_real_value(market, allow_market_floats=True)

    assert diagnostics == diagnostics_before
    assert market == market_before
    assert (
        diagnostics.replay_contract_version,
        diagnostics.registry_version,
        diagnostics.pipeline_contract_version,
        diagnostics.policy_profile_version,
        diagnostics.case_id,
        diagnostics.fixture_id,
    ) == EXPECTED_DIAGNOSTICS_IDENTITY
    assert market.source is not None
    assert (
        market.source.contract_version,
        market.source.bundle_schema_version,
        market.source.bundle_id,
        market.source.sequence,
        market.source.canonical_symbol,
        market.source.broker_symbol,
        market.source.reference_time_utc,
    ) == EXPECTED_MARKET_IDENTITY
    assert market == EXPECTED_MARKET_RESULT
    assert frozen_diagnostics == EXPECTED_DIAGNOSTICS_ORACLE
    assert frozen_market == EXPECTED_MARKET_ORACLE
    assert _is_valid_frozen_value(frozen_diagnostics)
    assert _is_valid_frozen_value(frozen_market)
    assert type(diagnostics.canonical_summary) is dict
    assert len(diagnostics.canonical_summary) == 20
    assert any(type(value) is list for value in diagnostics.canonical_summary.values())
    diagnostics_tags = {node[0] for node in _walk_frozen(frozen_diagnostics)}
    market_tags = {node[0] for node in _walk_frozen(frozen_market)}
    assert {"DATACLASS_V1", "DICT_V1", "LIST_V1"} <= diagnostics_tags
    assert "FLOAT_HEX_V1" in market_tags
    assert all(
        type(node) is tuple
        for node in _walk_frozen(frozen_diagnostics) + _walk_frozen(frozen_market)
    )


def test_class_identity_schema_and_static_oracle_bypasses_fail_closed() -> None:
    replay_case = replay_v1.CanonicalBundleReplayCaseV1(
        replay_contract_version=replay_v1.REPLAY_CONTRACT_VERSION,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
    )
    diagnostics = replay_v1.run_canonical_bundle_replay_case(
        replay_case=replay_case
    )
    market = market_fixture.build_canonical_gold_market_facts_docs_fixture_source_v1()

    same_name_impostor = make_dataclass(
        "CanonicalBundleReplayResultV1",
        (("passed", bool),),
        frozen=True,
        slots=True,
    )(passed=True)
    replay_subclass = type(
        "ReplayResultSubclass",
        (replay_v1.CanonicalBundleReplayResultV1,),
        {"__slots__": ()},
    )
    subclass_instance = replay_subclass(
        **{
            field.name: getattr(diagnostics, field.name)
            for field in fields(diagnostics)
        }
    )
    with pytest.raises(TypeError, match="unregistered dataclass"):
        _freeze_real_value(same_name_impostor)
    with pytest.raises(TypeError, match="unregistered dataclass"):
        _freeze_real_value(subclass_instance)

    drifted_diagnostics = deepcopy(diagnostics)
    drifted_diagnostics.canonical_summary["read_only"] = False
    assert _is_valid_frozen_value(_freeze_real_value(drifted_diagnostics))
    assert _freeze_real_value(drifted_diagnostics) != EXPECTED_DIAGNOSTICS_ORACLE

    assert market.source is not None
    drifted_source = replace(market.source, broker_symbol="GOLD_DRIFT")
    drifted_market = replace(market, source=drifted_source)
    assert _is_valid_frozen_value(
        _freeze_real_value(drifted_market, allow_market_floats=True)
    )
    assert (
        _freeze_real_value(drifted_market, allow_market_floats=True)
        != EXPECTED_MARKET_ORACLE
    )


def test_float_hex_signed_zero_and_type_tag_isolation_are_exact() -> None:
    encoded_list = _freeze_real_value(["x"], allow_summary_containers=True)
    encoded_tuple = _freeze_real_value(("x",), allow_summary_containers=True)
    encoded_float = _freeze_real_value(1.5, allow_market_floats=True)
    encoded_string = _freeze_real_value((1.5).hex())
    encoded_dict = _freeze_real_value({"x": 1}, allow_summary_containers=True)
    encoded_dataclass = (
        "DATACLASS_V1",
        "CANONICAL_BUNDLE_REPLAY_RESULT_V1",
        (("passed", ("BOOL_V1", True)),),
    )
    assert len(
        {
            encoded_list,
            encoded_tuple,
            encoded_float,
            encoded_string,
            encoded_dict,
            encoded_dataclass,
        }
    ) == 6
    assert _freeze_real_value(0.0, allow_market_floats=True) == (
        "FLOAT_HEX_V1",
        "0x0.0p+0",
    )
    assert _freeze_real_value(-0.0, allow_market_floats=True) == (
        "FLOAT_HEX_V1",
        "-0x0.0p+0",
    )
    for invalid in (
        float("nan"),
        float("inf"),
        float("-inf"),
        StrictFloatSubclass(1.0),
    ):
        with pytest.raises(TypeError):
            _freeze_real_value(invalid, allow_market_floats=True)


def test_invalid_frozen_shape_type_and_tag_vectors_fail_closed() -> None:
    assert len(INVALID_FROZEN_VECTORS) == 22
    assert len({vector.mutation for vector in INVALID_FROZEN_VECTORS}) == len(
        INVALID_FROZEN_VECTORS
    )
    for vector in INVALID_FROZEN_VECTORS:
        assert _is_valid_frozen_value(vector.value) is False, vector.mutation


def test_stage_order_call_accounting_and_fail_fast_rules_are_exact() -> None:
    text = _contract_text()
    assert _stage_order(text) == STAGE_ORDER
    assert _table_rows(text, first_column="Failure point") == CALL_ACCOUNTING
    assert "No stage may be omitted, duplicated, reordered, run concurrently" in text
    assert "Each accepted dependency is called at most once." in text
    assert "There is no retry, fallback, alternate registry, alternate fixture" in text
    assert "completed_stage_ids` is either this exact tuple" in text


def test_status_reason_priority_failure_clearing_and_safety_are_exact() -> None:
    text = _contract_text()
    assert _status_rows(text) == STATUS_REASON_VECTORS
    assert _numbered_priority(text) == FIRST_ERROR_PRIORITY
    for field, value in FAILURE_CLEARED_FIELDS.items():
        rendered = "None" if value is None else ("false" if value is False else "()")
        assert f"{field} = {rendered}" in text
    for field, value in SAFETY_FLAGS.items():
        rendered = "true" if value else "false"
        assert f"{field} = {rendered}" in text
    assert "unsafe shape or contradiction precedes blocked-state mapping" in text
    assert "blocked-state mapping precedes oracle mismatch" in text


def test_cross_stage_identity_detachment_and_sensitive_isolation_are_locked() -> None:
    text = _contract_text()
    assert "The market identity must be equal across:" in text
    assert "The calendar identity must be equal across:" in text
    assert "G191 and G196 must receive the same exact G178 snapshot object" in text
    assert "G201 must receive that same G178 snapshot object" in text
    assert "Every run must return a fresh result." in text
    assert "each of the seven nested results must be a fresh detached copy" in text
    assert "no mutable object may be shared between runs" in text
    assert "raw market or calendar fixture payloads" in text
    assert "authority tokens, policy objects, dependency objects" in text
    assert "runtime MT4 state" in text


def test_contract_mutation_probes_reject_schema_stage_mapping_and_grammar_drift() -> None:
    text = _contract_text()
    mutations = (
        text.replace(
            '    "CanonicalGoldFactsReplayResultV1",\n',
            '    "CanonicalGoldFactsReplayResultV2",\n',
            1,
        ),
        text.replace(
            "    fixture_id: str\n",
            "    changed_fixture_id: str\n",
            1,
        ),
        text.replace(
            "    canonical_gold_market_source_v1,\n"
            "    canonical_gold_market_snapshot_v1,\n",
            "    canonical_gold_market_snapshot_v1,\n"
            "    canonical_gold_market_source_v1,\n",
            1,
        ),
        text.replace(
            '| `CANONICAL_GOLD_FACTS_REPLAY_MISMATCH` | '
            '`("GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH",)` |',
            '| `CANONICAL_GOLD_FACTS_REPLAY_MISMATCH` | '
            '`("GOLD_FACTS_REPLAY_RESULT_INVALID",)` |',
            1,
        ),
        text.replace("FrozenListV1 :=", "FrozenSequenceV1 :=", 1),
        text.replace("value.hex()", "str(value)", 1),
    )
    assert _public_exports(mutations[0]) != PUBLIC_EXPORTS
    assert _class_fields(
        mutations[1], "CanonicalGoldFactsReplayCaseV1"
    ) != CASE_FIELDS
    assert _stage_order(mutations[2]) != STAGE_ORDER
    assert _status_rows(mutations[3]) != STATUS_REASON_VECTORS
    assert "FrozenListV1 :=" not in mutations[4]
    assert "value.hex()" not in mutations[5]


def test_staged_delivery_and_capability_boundaries_remain_closed() -> None:
    text = _contract_text()
    assert _staged_delivery(text) == STAGED_DELIVERY
    assert "W6 as a package remains `TESTS_ONLY`" in text
    assert "| Tests | Not implemented." in text
    assert "| Implementation | Not implemented." in text
    assert "| Integration | Not implemented." in text
    assert "| Activation | Not implemented and not authorized." in text
    assert "| Verification | Not implemented for this replay stage." in text
    assert "This contract is not runtime evidence." in text
    assert "activation, execution, or trading capability exists." in text


def test_vector_module_has_no_future_runtime_import_or_implementation() -> None:
    source = Path(__file__).read_text(encoding="ascii")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert "app.services.canonical_gold_facts_replay_stage" not in imported_modules
    assert all(
        "canonical_gold_facts_replay_stage" not in module
        for module in imported_modules
    )
    defined_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "CanonicalGoldFactsReplayCaseV1" not in defined_names
    assert "CanonicalGoldFactsReplayExpectedOracleV1" not in defined_names
    assert "CanonicalGoldFactsReplayRegistryRecordV1" not in defined_names
    assert "CanonicalGoldFactsReplayResultV1" not in defined_names
    assert "run_canonical_gold_facts_replay_case_v1" not in defined_names
    assert (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "canonical_gold_facts_replay_stage.py"
    ).is_file()
