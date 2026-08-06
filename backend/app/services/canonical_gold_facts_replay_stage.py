from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
import math
from pathlib import Path
import re
from typing import Any, Final

from app.services import canonical_bundle_replay_runner as replay_v1
from app.services import canonical_gold_economic_calendar_source_adapter as calendar
from app.services import canonical_gold_economic_window_facts as economic
from app.services import canonical_gold_market_facts_docs_fixture_integration as market_fixture
from app.services import canonical_gold_market_facts_snapshot_projector as market_facts
from app.services import canonical_gold_session_spread_freshness_facts as session_facts
from app.services import canonical_gold_volatility_structure_facts as volatility
from app.services.canonical_bundle_replay_runner import (
    CanonicalBundleReplayCaseV1,
    CanonicalBundleReplayResultV1,
)
from app.services.canonical_gold_economic_calendar_source_adapter import (
    CanonicalGoldEconomicCalendarSourceAdapterResultV1,
)
from app.services.canonical_gold_economic_window_facts import (
    CanonicalGoldEconomicWindowFactsV1,
)
from app.services.canonical_gold_market_facts_source_adapter import (
    CanonicalGoldMarketFactsSourceAdapterResultV1,
)
from app.services.canonical_gold_market_facts_snapshot_projector import (
    CanonicalGoldMarketFactsSnapshotV1,
)
from app.services.canonical_gold_session_spread_freshness_facts import (
    CanonicalGoldSessionSpreadFreshnessFactsV1,
)
from app.services.canonical_gold_volatility_structure_facts import (
    CanonicalGoldVolatilityStructureFactsV1,
)


__all__ = (
    "CanonicalGoldFactsReplayCaseV1",
    "CanonicalGoldFactsReplayExpectedOracleV1",
    "CanonicalGoldFactsReplayRegistryRecordV1",
    "CanonicalGoldFactsReplayResultV1",
    "run_canonical_gold_facts_replay_case_v1",
)


REPLAY_CONTRACT_VERSION: Final = "canonical_bundle_replay_v2"
STAGE_CONTRACT_VERSION: Final = "canonical_gold_facts_replay_stage_v1"
REGISTRY_VERSION: Final = "canonical_gold_facts_replay_registry_v1"
AUTHORITY_PROFILE_VERSION: Final = "canonical_gold_facts_replay_authority_v1"
STAGE_ID: Final = "canonical_gold_facts"
UPSTREAM_REPLAY_CONTRACT_VERSION: Final = "canonical_bundle_replay_v1"
UPSTREAM_REPLAY_REGISTRY_VERSION: Final = "canonical_bundle_replay_registry_v1"

CANONICAL_GOLD_FACTS_REPLAY_MATCHED: Final = "CANONICAL_GOLD_FACTS_REPLAY_MATCHED"
CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID: Final = "CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID"
CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID: Final = "CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID"
CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID: Final = "CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID"
CANONICAL_GOLD_FACTS_REPLAY_DIAGNOSTICS_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_DIAGNOSTICS_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_MARKET_SOURCE_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_MARKET_SOURCE_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_SESSION_FACTS_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_SESSION_FACTS_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_VOLATILITY_FACTS_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_VOLATILITY_FACTS_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_CALENDAR_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_CALENDAR_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_BLOCKED: Final = "CANONICAL_GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_BLOCKED"
CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID: Final = "CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID"
CANONICAL_GOLD_FACTS_REPLAY_MISMATCH: Final = "CANONICAL_GOLD_FACTS_REPLAY_MISMATCH"
CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE: Final = "CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE"

GOLD_FACTS_REPLAY_CASE_INPUT_INVALID: Final = "GOLD_FACTS_REPLAY_CASE_INPUT_INVALID"
GOLD_FACTS_REPLAY_REGISTRY_INVALID: Final = "GOLD_FACTS_REPLAY_REGISTRY_INVALID"
GOLD_FACTS_REPLAY_AUTHORITY_INVALID: Final = "GOLD_FACTS_REPLAY_AUTHORITY_INVALID"
GOLD_FACTS_REPLAY_DIAGNOSTICS_NOT_READY: Final = "GOLD_FACTS_REPLAY_DIAGNOSTICS_NOT_READY"
GOLD_FACTS_REPLAY_MARKET_SOURCE_NOT_READY: Final = "GOLD_FACTS_REPLAY_MARKET_SOURCE_NOT_READY"
GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_NOT_READY: Final = "GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_NOT_READY"
GOLD_FACTS_REPLAY_SESSION_FACTS_NOT_READY: Final = "GOLD_FACTS_REPLAY_SESSION_FACTS_NOT_READY"
GOLD_FACTS_REPLAY_VOLATILITY_FACTS_NOT_READY: Final = "GOLD_FACTS_REPLAY_VOLATILITY_FACTS_NOT_READY"
GOLD_FACTS_REPLAY_CALENDAR_NOT_READY: Final = "GOLD_FACTS_REPLAY_CALENDAR_NOT_READY"
GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_NOT_READY: Final = "GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_NOT_READY"
GOLD_FACTS_REPLAY_RESULT_INVALID: Final = "GOLD_FACTS_REPLAY_RESULT_INVALID"
GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH: Final = "GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH"
GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED: Final = "GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED"

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62})$", re.ASCII)
_PUBLIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$", re.ASCII)

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
class CanonicalGoldFactsReplayCaseV1:
    replay_contract_version: str
    stage_contract_version: str
    stage_id: str
    case_id: str
    fixture_id: str


@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayExpectedOracleV1:
    diagnostics_result: tuple[object, ...]
    market_source_result: tuple[object, ...]
    market_facts_snapshot: tuple[object, ...]
    session_spread_freshness_facts: tuple[object, ...]
    volatility_structure_facts: tuple[object, ...]
    economic_calendar_result: tuple[object, ...]
    economic_window_facts: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayRegistryRecordV1:
    registry_version: str
    replay_contract_version: str
    stage_contract_version: str
    authority_profile_version: str
    stage_id: str
    case_id: str
    fixture_id: str
    diagnostics_case: CanonicalBundleReplayCaseV1
    market_source_profile_version: str
    market_facts_contract_version: str
    session_facts_profile_version: str
    volatility_facts_profile_version: str
    calendar_source_profile_version: str
    economic_window_facts_profile_version: str
    reference_time_utc: str
    expected_market_identity: tuple[object, ...]
    expected_calendar_identity: tuple[object, ...]
    expected_oracle: CanonicalGoldFactsReplayExpectedOracleV1


@dataclass(frozen=True, slots=True)
class CanonicalGoldFactsReplayResultV1:
    replay_contract_version: str
    stage_contract_version: str
    registry_version: str
    stage_id: str
    passed: bool
    status_code: str
    reason_codes: tuple[str, ...]
    identity_available: bool
    case_id: str | None
    fixture_id: str | None
    completed_stage_ids: tuple[str, ...]
    diagnostics_result: CanonicalBundleReplayResultV1 | None
    market_source_result: CanonicalGoldMarketFactsSourceAdapterResultV1 | None
    market_facts_snapshot: CanonicalGoldMarketFactsSnapshotV1 | None
    session_spread_freshness_facts: CanonicalGoldSessionSpreadFreshnessFactsV1 | None
    volatility_structure_facts: CanonicalGoldVolatilityStructureFactsV1 | None
    economic_calendar_result: CanonicalGoldEconomicCalendarSourceAdapterResultV1 | None
    economic_window_facts: CanonicalGoldEconomicWindowFactsV1 | None
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool
    is_trading_permission: bool
    is_execution_instruction: bool
    allowed_to_call_ea: bool
    allowed_to_modify_risk: bool


@dataclass(frozen=True, slots=True)
class _ProductionSchema:
    class_object: type[object]
    type_code: str
    ordered_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _AuthorityCapsule:
    diagnostics_runner: object
    market_source_builder: object
    market_projector: object
    session_builder: object
    volatility_builder: object
    calendar_builder: object
    economic_builder: object
    market_result_validator: object
    calendar_result_validator: object
    market_fixture_paths: tuple[Path, ...]
    calendar_fixture_path: Path


_PRODUCTION_SCHEMAS: Final = (
    _ProductionSchema(replay_v1.CanonicalBundleReplayResultV1, 'CANONICAL_BUNDLE_REPLAY_RESULT_V1', ('replay_contract_version', 'registry_version', 'pipeline_contract_version', 'policy_profile_version', 'case_id', 'fixture_id', 'passed', 'status_code', 'canonical_summary', 'replay_reason_codes', 'canonical_block_reasons', 'canonical_warning_codes', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_execution_instruction', 'allowed_to_call_ea')),
    _ProductionSchema(CanonicalGoldMarketFactsSourceAdapterResultV1, 'CANONICAL_GOLD_MARKET_FACTS_SOURCE_ADAPTER_RESULT_V1', ('contract_version', 'passed', 'status_code', 'reason_codes', 'warning_codes', 'source_available', 'source', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_trading_permission', 'is_execution_instruction', 'allowed_to_call_ea', 'allowed_to_modify_risk')),
    _ProductionSchema(market_facts.CanonicalGoldMarketFactsSourceV1, 'CANONICAL_GOLD_MARKET_FACTS_SOURCE_V1', ('contract_version', 'bundle_schema_version', 'bundle_id', 'sequence', 'canonical_symbol', 'broker_symbol', 'reference_time_utc', 'policy_profile_version', 'upstream_evidence', 'live_tick', 'bars_generated_at_utc', 'timeframes', 'symbol_spec')),
    _ProductionSchema(market_facts.CanonicalGoldUpstreamEvidenceV1, 'CANONICAL_GOLD_UPSTREAM_EVIDENCE_V1', ('reader_passed', 'reader_status_code', 'value_status_code', 'data_quality_passed', 'data_quality_status_code', 'ready_for_readonly_analysis', 'warning_codes', 'same_attempt_identity_bound')),
    _ProductionSchema(market_facts.CanonicalGoldTickSourceV1, 'CANONICAL_GOLD_TICK_SOURCE_V1', ('bid', 'ask', 'spread', 'spread_points', 'digits', 'point', 'tick_time_utc')),
    _ProductionSchema(market_facts.CanonicalGoldTimeframeSourceV1, 'CANONICAL_GOLD_TIMEFRAME_SOURCE_V1', ('timeframe', 'period_seconds', 'bars')),
    _ProductionSchema(market_facts.CanonicalGoldBarSourceV1, 'CANONICAL_GOLD_BAR_SOURCE_V1', ('open_time_utc', 'open', 'high', 'low', 'close', 'tick_volume', 'spread_points')),
    _ProductionSchema(market_facts.CanonicalGoldSymbolSpecSourceV1, 'CANONICAL_GOLD_SYMBOL_SPEC_SOURCE_V1', ('spec_time_utc', 'digits', 'point', 'tick_size', 'tick_value', 'contract_size', 'min_lot', 'lot_step', 'max_lot', 'base_currency', 'profit_currency', 'margin_currency', 'trade_mode_readonly_label', 'session_status_readonly_label')),
    _ProductionSchema(market_facts.CanonicalGoldMarketFactsSnapshotV1, 'CANONICAL_GOLD_MARKET_FACTS_SNAPSHOT_V1', ('contract_version', 'passed', 'status_code', 'reason_codes', 'warning_codes', 'identity_available', 'bundle_schema_version', 'bundle_id', 'sequence', 'canonical_symbol', 'broker_symbol', 'reference_time_utc', 'quote', 'timeframes', 'symbol_spec', 'freshness', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_trading_permission', 'is_execution_instruction', 'allowed_to_call_ea', 'allowed_to_modify_risk')),
    _ProductionSchema(market_facts.CanonicalGoldQuoteFactsV1, 'CANONICAL_GOLD_QUOTE_FACTS_V1', ('bid_decimal', 'ask_decimal', 'spread_decimal', 'spread_points', 'digits', 'point_decimal', 'tick_time_utc')),
    _ProductionSchema(market_facts.CanonicalGoldTimeframeFactsV1, 'CANONICAL_GOLD_TIMEFRAME_FACTS_V1', ('timeframe', 'period_seconds', 'bars')),
    _ProductionSchema(market_facts.CanonicalGoldBarFactsV1, 'CANONICAL_GOLD_BAR_FACTS_V1', ('open_time_utc', 'open_decimal', 'high_decimal', 'low_decimal', 'close_decimal', 'tick_volume', 'spread_points')),
    _ProductionSchema(market_facts.CanonicalGoldSymbolFactsV1, 'CANONICAL_GOLD_SYMBOL_FACTS_V1', ('spec_time_utc', 'digits', 'point_decimal', 'tick_size_decimal', 'tick_value_decimal', 'contract_size_decimal', 'min_lot_decimal', 'lot_step_decimal', 'max_lot_decimal', 'base_currency', 'profit_currency', 'margin_currency', 'trade_mode_readonly_label', 'session_status_readonly_label')),
    _ProductionSchema(market_facts.CanonicalGoldFreshnessFactsV1, 'CANONICAL_GOLD_FRESHNESS_FACTS_V1', ('tick_age_microseconds', 'bars_payload_age_microseconds', 'symbol_spec_age_microseconds')),
    _ProductionSchema(session_facts.CanonicalGoldSessionSpreadFreshnessFactsV1, 'CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FACTS_V1', ('contract_version', 'facts_profile_version', 'passed', 'status_code', 'reason_codes', 'warning_codes', 'identity_available', 'bundle_schema_version', 'bundle_id', 'sequence', 'canonical_symbol', 'broker_symbol', 'reference_time_utc', 'session', 'spread', 'freshness', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_trading_permission', 'is_execution_instruction', 'allowed_to_call_ea', 'allowed_to_modify_risk')),
    _ProductionSchema(session_facts.CanonicalGoldSessionFactsV1, 'CANONICAL_GOLD_SESSION_FACTS_V1', ('utc_weekday_code', 'utc_second_of_day', 'session_bucket_code', 'window_start_second_utc', 'window_end_second_utc', 'seconds_since_window_start', 'seconds_until_window_end', 'observed_writer_session_status_label')),
    _ProductionSchema(session_facts.CanonicalGoldSpreadFactsV1, 'CANONICAL_GOLD_SPREAD_FACTS_V1', ('bid_decimal', 'ask_decimal', 'mid_decimal', 'spread_decimal', 'spread_points', 'digits', 'point_decimal', 'spread_to_mid_ppm_decimal')),
    _ProductionSchema(session_facts.CanonicalGoldSourceFreshnessFactsV1, 'CANONICAL_GOLD_SOURCE_FRESHNESS_FACTS_V1', ('tick_age_microseconds', 'bars_payload_age_microseconds', 'symbol_spec_age_microseconds', 'maximum_source_age_microseconds', 'oldest_source_component_code')),
    _ProductionSchema(volatility.CanonicalGoldVolatilityStructureFactsV1, 'CANONICAL_GOLD_VOLATILITY_STRUCTURE_FACTS_V1', ('contract_version', 'facts_profile_version', 'passed', 'status_code', 'reason_codes', 'warning_codes', 'identity_available', 'source_contract_version', 'bundle_schema_version', 'bundle_id', 'sequence', 'canonical_symbol', 'broker_symbol', 'reference_time_utc', 'timeframes', 'total_pair_count', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_trading_permission', 'is_execution_instruction', 'allowed_to_call_ea', 'allowed_to_modify_risk')),
    _ProductionSchema(volatility.CanonicalGoldTimeframeVolatilityStructureFactsV1, 'CANONICAL_GOLD_TIMEFRAME_VOLATILITY_STRUCTURE_FACTS_V1', ('timeframe', 'period_seconds', 'source_bar_count', 'pair_count', 'bar_pairs')),
    _ProductionSchema(volatility.CanonicalGoldBarPairVolatilityStructureFactsV1, 'CANONICAL_GOLD_BAR_PAIR_VOLATILITY_STRUCTURE_FACTS_V1', ('previous_open_time_utc', 'current_open_time_utc', 'previous_range_decimal', 'current_range_decimal', 'true_range_decimal', 'body_signed_decimal', 'body_absolute_decimal', 'upper_wick_decimal', 'lower_wick_decimal', 'close_change_decimal', 'high_change_decimal', 'low_change_decimal', 'direction_code', 'range_relation_code', 'range_containment_code', 'current_high_vs_previous_high_code', 'current_low_vs_previous_low_code', 'current_close_vs_previous_range_code')),
    _ProductionSchema(calendar.CanonicalGoldEconomicCalendarSourceAdapterResultV1, 'CANONICAL_GOLD_ECONOMIC_CALENDAR_SOURCE_ADAPTER_RESULT_V1', ('contract_version', 'passed', 'status_code', 'reason_codes', 'warning_codes', 'snapshot_available', 'snapshot', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_trading_permission', 'is_execution_instruction', 'allowed_to_call_ea', 'allowed_to_modify_risk')),
    _ProductionSchema(economic.CanonicalGoldEconomicCalendarSnapshotV1, 'CANONICAL_GOLD_ECONOMIC_CALENDAR_SNAPSHOT_V1', ('contract_version', 'calendar_schema_version', 'calendar_snapshot_id', 'source_profile_version', 'generated_at_utc', 'coverage_start_utc', 'coverage_end_utc', 'events', 'upstream_evidence', 'read_only', 'demo_only', 'contains_raw_provider_payload')),
    _ProductionSchema(economic.CanonicalGoldEconomicCalendarUpstreamEvidenceV1, 'CANONICAL_GOLD_ECONOMIC_CALENDAR_UPSTREAM_EVIDENCE_V1', ('adapter_passed', 'adapter_status_code', 'schema_validated', 'identity_validated', 'timestamps_normalized', 'same_snapshot_bound', 'warning_codes', 'raw_payload_discarded')),
    _ProductionSchema(economic.CanonicalGoldEconomicEventSourceV1, 'CANONICAL_GOLD_ECONOMIC_EVENT_SOURCE_V1', ('event_id', 'scheduled_at_utc', 'country_code', 'currency_code', 'event_category_code', 'impact_code', 'source_revision', 'event_status_code')),
    _ProductionSchema(economic.CanonicalGoldEconomicWindowFactsV1, 'CANONICAL_GOLD_ECONOMIC_WINDOW_FACTS_V1', ('contract_version', 'facts_profile_version', 'passed', 'status_code', 'reason_codes', 'warning_codes', 'identity_available', 'source_contract_version', 'bundle_schema_version', 'bundle_id', 'sequence', 'canonical_symbol', 'broker_symbol', 'reference_time_utc', 'calendar_contract_version', 'calendar_schema_version', 'calendar_snapshot_id', 'calendar_source_profile_version', 'calendar_generated_at_utc', 'calendar_coverage_start_utc', 'calendar_coverage_end_utc', 'event_windows', 'summary', 'read_only', 'demo_only', 'is_tradable', 'can_execute', 'is_trading_permission', 'is_execution_instruction', 'allowed_to_call_ea', 'allowed_to_modify_risk')),
    _ProductionSchema(economic.CanonicalGoldEconomicEventWindowFactsV1, 'CANONICAL_GOLD_ECONOMIC_EVENT_WINDOW_FACTS_V1', ('event_id', 'scheduled_at_utc', 'country_code', 'currency_code', 'event_category_code', 'impact_code', 'source_revision', 'window_start_utc', 'window_end_utc', 'event_offset_microseconds', 'window_start_offset_microseconds', 'window_end_offset_microseconds', 'window_relation_code', 'is_active_observation_window')),
    _ProductionSchema(economic.CanonicalGoldEconomicWindowSummaryV1, 'CANONICAL_GOLD_ECONOMIC_WINDOW_SUMMARY_V1', ('calendar_age_microseconds', 'relevant_event_count', 'active_window_count', 'inside_any_observation_window', 'active_event_ids', 'nearest_previous_event_id', 'nearest_previous_event_offset_microseconds', 'nearest_next_event_id', 'nearest_next_event_offset_microseconds', 'highest_active_impact_code')),
)
_SCHEMA_BY_CLASS: Final = {schema.class_object: schema for schema in _PRODUCTION_SCHEMAS}
_SCHEMA_BY_TYPE_CODE: Final = {schema.type_code: schema for schema in _PRODUCTION_SCHEMAS}

_EXPECTED_ORACLE: Final = CanonicalGoldFactsReplayExpectedOracleV1(
    diagnostics_result=
    ('DATACLASS_V1',
     'CANONICAL_BUNDLE_REPLAY_RESULT_V1',
     (('replay_contract_version', ('STRING_V1', 'canonical_bundle_replay_v1')),
      ('registry_version', ('STRING_V1', 'canonical_bundle_replay_registry_v1')),
      ('pipeline_contract_version', ('STRING_V1', 'canonical_diagnostics_pipeline_g153_v1')),
      ('policy_profile_version', ('STRING_V1', 'canonical_diagnostics_default_policy_v1')),
      ('case_id', ('STRING_V1', 'canonical_docs_ready')),
      ('fixture_id', ('STRING_V1', 'canonical_docs_fixture_v1')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_BUNDLE_REPLAY_MATCHED')),
      ('canonical_summary',
       ('DICT_V1',
        ((('STRING_V1', 'passed'), ('BOOL_V1', True)),
         (('STRING_V1', 'status_code'), ('STRING_V1', 'CANONICAL_DIAGNOSTICS_SUMMARY_READY')),
         (('STRING_V1', 'source_scope'),
          ('STRING_V1', 'canonical_mt4_demo_readonly_data_quality_summary_only')),
         (('STRING_V1', 'validation_stage'),
          ('STRING_V1', 'canonical_bundle_v1_diagnostics_summary_adapter')),
         (('STRING_V1', 'fixture_source'),
          ('STRING_V1', 'canonical_bundle_v1_data_quality_gate_result')),
         (('STRING_V1', 'bundle_validation_status'),
          ('DICT_V1',
           ((('STRING_V1', 'passed'), ('BOOL_V1', True)),
            (('STRING_V1', 'status_code'),
             ('STRING_V1', 'CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED')),
            (('STRING_V1', 'block_reasons'), ('LIST_V1', ())),
            (('STRING_V1', 'warning_reasons'), ('LIST_V1', ())),
            (('STRING_V1', 'read_only'), ('BOOL_V1', True)),
            (('STRING_V1', 'demo_only'), ('BOOL_V1', True)),
            (('STRING_V1', 'is_tradable'), ('BOOL_V1', False)),
            (('STRING_V1', 'can_execute'), ('BOOL_V1', False))))),
         (('STRING_V1', 'component_statuses'),
          ('DICT_V1',
           ((('STRING_V1', 'canonical_data_quality_gate'),
             ('DICT_V1',
              ((('STRING_V1', 'passed'), ('BOOL_V1', True)),
               (('STRING_V1', 'status_code'),
                ('STRING_V1', 'CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED')),
               (('STRING_V1', 'block_reasons'), ('LIST_V1', ())),
               (('STRING_V1', 'warning_reasons'), ('LIST_V1', ())),
               (('STRING_V1', 'read_only'), ('BOOL_V1', True)),
               (('STRING_V1', 'demo_only'), ('BOOL_V1', True)),
               (('STRING_V1', 'is_tradable'), ('BOOL_V1', False)),
               (('STRING_V1', 'can_execute'), ('BOOL_V1', False))))),))),
         (('STRING_V1', 'block_reasons'), ('LIST_V1', ())),
         (('STRING_V1', 'warning_reasons'), ('LIST_V1', ())),
         (('STRING_V1', 'readiness_notes'),
          ('LIST_V1',
           (('STRING_V1', 'Canonical DataQualityGate passed for read-only diagnostics adaptation.'),
            ('STRING_V1', 'Readiness is not trading permission.'),
            ('STRING_V1', 'This summary is read-only and cannot execute orders.')))),
         (('STRING_V1', 'next_allowed_stage'),
          ('LIST_V1', (('STRING_V1', 'demo_readonly_diagnostics_response_integration'),))),
         (('STRING_V1', 'next_blocked_stage'),
          ('LIST_V1', (('STRING_V1', 'api_reader_activation'), ('STRING_V1', 'execution_chain')))),
         (('STRING_V1', 'read_only'), ('BOOL_V1', True)),
         (('STRING_V1', 'demo_only'), ('BOOL_V1', True)),
         (('STRING_V1', 'is_tradable'), ('BOOL_V1', False)),
         (('STRING_V1', 'can_execute'), ('BOOL_V1', False)),
         (('STRING_V1', 'is_trading_permission'), ('BOOL_V1', False)),
         (('STRING_V1', 'is_execution_instruction'), ('BOOL_V1', False)),
         (('STRING_V1', 'allowed_to_call_ea'), ('BOOL_V1', False)),
         (('STRING_V1', 'allowed_to_modify_risk'), ('BOOL_V1', False))))),
      ('replay_reason_codes', ('TUPLE_V1', ())),
      ('canonical_block_reasons', ('TUPLE_V1', ())),
      ('canonical_warning_codes', ('TUPLE_V1', ())),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)))),
    market_source_result=
    ('DATACLASS_V1',
     'CANONICAL_GOLD_MARKET_FACTS_SOURCE_ADAPTER_RESULT_V1',
     (('contract_version', ('STRING_V1', '1.0')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_GOLD_SOURCE_ADAPTER_READY')),
      ('reason_codes', ('TUPLE_V1', ())),
      ('warning_codes', ('TUPLE_V1', ())),
      ('source_available', ('BOOL_V1', True)),
      ('source',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_MARKET_FACTS_SOURCE_V1',
        (('contract_version', ('STRING_V1', '1.0')),
         ('bundle_schema_version', ('STRING_V1', '1.0')),
         ('bundle_id', ('STRING_V1', 'demo-bundle-000000000001')),
         ('sequence', ('INT_V1', 1)),
         ('canonical_symbol', ('STRING_V1', 'XAUUSD')),
         ('broker_symbol', ('STRING_V1', 'GOLD')),
         ('reference_time_utc', ('STRING_V1', '2026-07-10T02:30:05.000000Z')),
         ('policy_profile_version', ('STRING_V1', 'canonical_gold_market_facts_policy_v1')),
         ('upstream_evidence',
          ('DATACLASS_V1',
           'CANONICAL_GOLD_UPSTREAM_EVIDENCE_V1',
           (('reader_passed', ('BOOL_V1', True)),
            ('reader_status_code', ('STRING_V1', 'CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID')),
            ('value_status_code', ('STRING_V1', 'CANONICAL_MT4_BUNDLE_V1_VALUE_VALID')),
            ('data_quality_passed', ('BOOL_V1', True)),
            ('data_quality_status_code', ('STRING_V1', 'CANONICAL_MT4_BUNDLE_V1_DATA_QUALITY_PASSED')),
            ('ready_for_readonly_analysis', ('BOOL_V1', True)),
            ('warning_codes', ('TUPLE_V1', ())),
            ('same_attempt_identity_bound', ('BOOL_V1', True))))),
         ('live_tick',
          ('DATACLASS_V1',
           'CANONICAL_GOLD_TICK_SOURCE_V1',
           (('bid', ('FLOAT_HEX_V1', '0x1.1f90000000000p+11')),
            ('ask', ('FLOAT_HEX_V1', '0x1.1f9999999999ap+11')),
            ('spread', ('FLOAT_HEX_V1', '0x1.3333333333333p-2')),
            ('spread_points', ('INT_V1', 30)),
            ('digits', ('INT_V1', 2)),
            ('point', ('FLOAT_HEX_V1', '0x1.47ae147ae147bp-7')),
            ('tick_time_utc', ('STRING_V1', '2026-07-10T02:30:00Z'))))),
         ('bars_generated_at_utc', ('STRING_V1', '2026-07-10T02:30:00Z')),
         ('timeframes',
          ('TUPLE_V1',
           (('DATACLASS_V1',
             'CANONICAL_GOLD_TIMEFRAME_SOURCE_V1',
             (('timeframe', ('STRING_V1', 'M15')),
              ('period_seconds', ('INT_V1', 900)),
              ('bars',
               ('TUPLE_V1',
                (('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-10T02:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1f73333333333p+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1fa3333333333p+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1f5cccccccccdp+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f86666666666p+11')),
                   ('tick_volume', ('INT_V1', 1240)),
                   ('spread_points', ('INT_V1', 30)))),
                 ('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-10T02:15:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1f86666666666p+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1facccccccccdp+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1f7999999999ap+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f9999999999ap+11')),
                   ('tick_volume', ('INT_V1', 830)),
                   ('spread_points', ('INT_V1', 30))))))))),
            ('DATACLASS_V1',
             'CANONICAL_GOLD_TIMEFRAME_SOURCE_V1',
             (('timeframe', ('STRING_V1', 'H1')),
              ('period_seconds', ('INT_V1', 3600)),
              ('bars',
               ('TUPLE_V1',
                (('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-10T00:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1f0cccccccccdp+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1f96666666666p+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1efcccccccccdp+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f76666666666p+11')),
                   ('tick_volume', ('INT_V1', 4100)),
                   ('spread_points', ('INT_V1', 31)))),
                 ('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-10T01:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1f76666666666p+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1facccccccccdp+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1f5cccccccccdp+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f9999999999ap+11')),
                   ('tick_volume', ('INT_V1', 2950)),
                   ('spread_points', ('INT_V1', 30))))))))),
            ('DATACLASS_V1',
             'CANONICAL_GOLD_TIMEFRAME_SOURCE_V1',
             (('timeframe', ('STRING_V1', 'H4')),
              ('period_seconds', ('INT_V1', 14400)),
              ('bars',
               ('TUPLE_V1',
                (('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-09T16:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1e10000000000p+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1f46666666666p+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1dfcccccccccdp+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f0cccccccccdp+11')),
                   ('tick_volume', ('INT_V1', 12300)),
                   ('spread_points', ('INT_V1', 32)))),
                 ('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-09T20:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1f0cccccccccdp+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1facccccccccdp+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1efcccccccccdp+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f9999999999ap+11')),
                   ('tick_volume', ('INT_V1', 8400)),
                   ('spread_points', ('INT_V1', 30))))))))),
            ('DATACLASS_V1',
             'CANONICAL_GOLD_TIMEFRAME_SOURCE_V1',
             (('timeframe', ('STRING_V1', 'D1')),
              ('period_seconds', ('INT_V1', 86400)),
              ('bars',
               ('TUPLE_V1',
                (('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-08T00:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1bacccccccccdp+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1d20000000000p+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1b5999999999ap+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1cc6666666666p+11')),
                   ('tick_volume', ('INT_V1', 49800)),
                   ('spread_points', ('INT_V1', 33)))),
                 ('DATACLASS_V1',
                  'CANONICAL_GOLD_BAR_SOURCE_V1',
                  (('open_time_utc', ('STRING_V1', '2026-07-09T00:00:00Z')),
                   ('open', ('FLOAT_HEX_V1', '0x1.1cc6666666666p+11')),
                   ('high', ('FLOAT_HEX_V1', '0x1.1f46666666666p+11')),
                   ('low', ('FLOAT_HEX_V1', '0x1.1c73333333333p+11')),
                   ('close', ('FLOAT_HEX_V1', '0x1.1f0cccccccccdp+11')),
                   ('tick_volume', ('INT_V1', 53000)),
                   ('spread_points', ('INT_V1', 32)))))))))))),
         ('symbol_spec',
          ('DATACLASS_V1',
           'CANONICAL_GOLD_SYMBOL_SPEC_SOURCE_V1',
           (('spec_time_utc', ('STRING_V1', '2026-07-10T02:30:00Z')),
            ('digits', ('INT_V1', 2)),
            ('point', ('FLOAT_HEX_V1', '0x1.47ae147ae147bp-7')),
            ('tick_size', ('FLOAT_HEX_V1', '0x1.47ae147ae147bp-7')),
            ('tick_value', ('FLOAT_HEX_V1', '0x1.0000000000000p+0')),
            ('contract_size', ('FLOAT_HEX_V1', '0x1.9000000000000p+6')),
            ('min_lot', ('FLOAT_HEX_V1', '0x1.47ae147ae147bp-7')),
            ('lot_step', ('FLOAT_HEX_V1', '0x1.47ae147ae147bp-7')),
            ('max_lot', ('FLOAT_HEX_V1', '0x1.9000000000000p+5')),
            ('base_currency', ('STRING_V1', 'XAU')),
            ('profit_currency', ('STRING_V1', 'USD')),
            ('margin_currency', ('STRING_V1', 'USD')),
            ('trade_mode_readonly_label', ('STRING_V1', 'readonly_metadata_only')),
            ('session_status_readonly_label', ('STRING_V1', 'unknown')))))))),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_trading_permission', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)),
      ('allowed_to_modify_risk', ('BOOL_V1', False)))),
    market_facts_snapshot=
    ('DATACLASS_V1',
     'CANONICAL_GOLD_MARKET_FACTS_SNAPSHOT_V1',
     (('contract_version', ('STRING_V1', '1.0')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_GOLD_MARKET_FACTS_READY')),
      ('reason_codes', ('TUPLE_V1', ())),
      ('warning_codes', ('TUPLE_V1', ())),
      ('identity_available', ('BOOL_V1', True)),
      ('bundle_schema_version', ('STRING_V1', '1.0')),
      ('bundle_id', ('STRING_V1', 'demo-bundle-000000000001')),
      ('sequence', ('INT_V1', 1)),
      ('canonical_symbol', ('STRING_V1', 'XAUUSD')),
      ('broker_symbol', ('STRING_V1', 'GOLD')),
      ('reference_time_utc', ('STRING_V1', '2026-07-10T02:30:05.000000Z')),
      ('quote',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_QUOTE_FACTS_V1',
        (('bid_decimal', ('STRING_V1', '2300.50')),
         ('ask_decimal', ('STRING_V1', '2300.80')),
         ('spread_decimal', ('STRING_V1', '0.30')),
         ('spread_points', ('INT_V1', 30)),
         ('digits', ('INT_V1', 2)),
         ('point_decimal', ('STRING_V1', '0.01')),
         ('tick_time_utc', ('STRING_V1', '2026-07-10T02:30:00Z'))))),
      ('timeframes',
       ('TUPLE_V1',
        (('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_FACTS_V1',
          (('timeframe', ('STRING_V1', 'M15')),
           ('period_seconds', ('INT_V1', 900)),
           ('bars',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-10T02:00:00Z')),
                ('open_decimal', ('STRING_V1', '2299.60')),
                ('high_decimal', ('STRING_V1', '2301.10')),
                ('low_decimal', ('STRING_V1', '2298.90')),
                ('close_decimal', ('STRING_V1', '2300.20')),
                ('tick_volume', ('INT_V1', 1240)),
                ('spread_points', ('INT_V1', 30)))),
              ('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-10T02:15:00Z')),
                ('open_decimal', ('STRING_V1', '2300.20')),
                ('high_decimal', ('STRING_V1', '2301.40')),
                ('low_decimal', ('STRING_V1', '2299.80')),
                ('close_decimal', ('STRING_V1', '2300.80')),
                ('tick_volume', ('INT_V1', 830)),
                ('spread_points', ('INT_V1', 30))))))))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_FACTS_V1',
          (('timeframe', ('STRING_V1', 'H1')),
           ('period_seconds', ('INT_V1', 3600)),
           ('bars',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-10T00:00:00Z')),
                ('open_decimal', ('STRING_V1', '2296.40')),
                ('high_decimal', ('STRING_V1', '2300.70')),
                ('low_decimal', ('STRING_V1', '2295.90')),
                ('close_decimal', ('STRING_V1', '2299.70')),
                ('tick_volume', ('INT_V1', 4100)),
                ('spread_points', ('INT_V1', 31)))),
              ('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-10T01:00:00Z')),
                ('open_decimal', ('STRING_V1', '2299.70')),
                ('high_decimal', ('STRING_V1', '2301.40')),
                ('low_decimal', ('STRING_V1', '2298.90')),
                ('close_decimal', ('STRING_V1', '2300.80')),
                ('tick_volume', ('INT_V1', 2950)),
                ('spread_points', ('INT_V1', 30))))))))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_FACTS_V1',
          (('timeframe', ('STRING_V1', 'H4')),
           ('period_seconds', ('INT_V1', 14400)),
           ('bars',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-09T16:00:00Z')),
                ('open_decimal', ('STRING_V1', '2288.50')),
                ('high_decimal', ('STRING_V1', '2298.20')),
                ('low_decimal', ('STRING_V1', '2287.90')),
                ('close_decimal', ('STRING_V1', '2296.40')),
                ('tick_volume', ('INT_V1', 12300)),
                ('spread_points', ('INT_V1', 32)))),
              ('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-09T20:00:00Z')),
                ('open_decimal', ('STRING_V1', '2296.40')),
                ('high_decimal', ('STRING_V1', '2301.40')),
                ('low_decimal', ('STRING_V1', '2295.90')),
                ('close_decimal', ('STRING_V1', '2300.80')),
                ('tick_volume', ('INT_V1', 8400)),
                ('spread_points', ('INT_V1', 30))))))))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_FACTS_V1',
          (('timeframe', ('STRING_V1', 'D1')),
           ('period_seconds', ('INT_V1', 86400)),
           ('bars',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-08T00:00:00Z')),
                ('open_decimal', ('STRING_V1', '2269.40')),
                ('high_decimal', ('STRING_V1', '2281.00')),
                ('low_decimal', ('STRING_V1', '2266.80')),
                ('close_decimal', ('STRING_V1', '2278.20')),
                ('tick_volume', ('INT_V1', 49800)),
                ('spread_points', ('INT_V1', 33)))),
              ('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_FACTS_V1',
               (('open_time_utc', ('STRING_V1', '2026-07-09T00:00:00Z')),
                ('open_decimal', ('STRING_V1', '2278.20')),
                ('high_decimal', ('STRING_V1', '2298.20')),
                ('low_decimal', ('STRING_V1', '2275.60')),
                ('close_decimal', ('STRING_V1', '2296.40')),
                ('tick_volume', ('INT_V1', 53000)),
                ('spread_points', ('INT_V1', 32)))))))))))),
      ('symbol_spec',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_SYMBOL_FACTS_V1',
        (('spec_time_utc', ('STRING_V1', '2026-07-10T02:30:00Z')),
         ('digits', ('INT_V1', 2)),
         ('point_decimal', ('STRING_V1', '0.01')),
         ('tick_size_decimal', ('STRING_V1', '0.01')),
         ('tick_value_decimal', ('STRING_V1', '1')),
         ('contract_size_decimal', ('STRING_V1', '100')),
         ('min_lot_decimal', ('STRING_V1', '0.01')),
         ('lot_step_decimal', ('STRING_V1', '0.01')),
         ('max_lot_decimal', ('STRING_V1', '50')),
         ('base_currency', ('STRING_V1', 'XAU')),
         ('profit_currency', ('STRING_V1', 'USD')),
         ('margin_currency', ('STRING_V1', 'USD')),
         ('trade_mode_readonly_label', ('STRING_V1', 'readonly_metadata_only')),
         ('session_status_readonly_label', ('STRING_V1', 'unknown'))))),
      ('freshness',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_FRESHNESS_FACTS_V1',
        (('tick_age_microseconds', ('INT_V1', 5000000)),
         ('bars_payload_age_microseconds', ('INT_V1', 5000000)),
         ('symbol_spec_age_microseconds', ('INT_V1', 5000000))))),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_trading_permission', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)),
      ('allowed_to_modify_risk', ('BOOL_V1', False)))),
    session_spread_freshness_facts=
    ('DATACLASS_V1',
     'CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_FACTS_V1',
     (('contract_version', ('STRING_V1', '1.0')),
      ('facts_profile_version', ('STRING_V1', 'canonical_gold_session_spread_freshness_profile_v1')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY')),
      ('reason_codes', ('TUPLE_V1', ())),
      ('warning_codes', ('TUPLE_V1', ())),
      ('identity_available', ('BOOL_V1', True)),
      ('bundle_schema_version', ('STRING_V1', '1.0')),
      ('bundle_id', ('STRING_V1', 'demo-bundle-000000000001')),
      ('sequence', ('INT_V1', 1)),
      ('canonical_symbol', ('STRING_V1', 'XAUUSD')),
      ('broker_symbol', ('STRING_V1', 'GOLD')),
      ('reference_time_utc', ('STRING_V1', '2026-07-10T02:30:05.000000Z')),
      ('session',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_SESSION_FACTS_V1',
        (('utc_weekday_code', ('STRING_V1', 'FRIDAY')),
         ('utc_second_of_day', ('INT_V1', 9005)),
         ('session_bucket_code', ('STRING_V1', 'ASIA_UTC')),
         ('window_start_second_utc', ('INT_V1', 0)),
         ('window_end_second_utc', ('INT_V1', 28800)),
         ('seconds_since_window_start', ('INT_V1', 9005)),
         ('seconds_until_window_end', ('INT_V1', 19795)),
         ('observed_writer_session_status_label', ('STRING_V1', 'unknown'))))),
      ('spread',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_SPREAD_FACTS_V1',
        (('bid_decimal', ('STRING_V1', '2300.50')),
         ('ask_decimal', ('STRING_V1', '2300.80')),
         ('mid_decimal', ('STRING_V1', '2300.650')),
         ('spread_decimal', ('STRING_V1', '0.30')),
         ('spread_points', ('INT_V1', 30)),
         ('digits', ('INT_V1', 2)),
         ('point_decimal', ('STRING_V1', '0.01')),
         ('spread_to_mid_ppm_decimal', ('STRING_V1', '130.397931'))))),
      ('freshness',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_SOURCE_FRESHNESS_FACTS_V1',
        (('tick_age_microseconds', ('INT_V1', 5000000)),
         ('bars_payload_age_microseconds', ('INT_V1', 5000000)),
         ('symbol_spec_age_microseconds', ('INT_V1', 5000000)),
         ('maximum_source_age_microseconds', ('INT_V1', 5000000)),
         ('oldest_source_component_code', ('STRING_V1', 'TICK'))))),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_trading_permission', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)),
      ('allowed_to_modify_risk', ('BOOL_V1', False)))),
    volatility_structure_facts=
    ('DATACLASS_V1',
     'CANONICAL_GOLD_VOLATILITY_STRUCTURE_FACTS_V1',
     (('contract_version', ('STRING_V1', '1.0')),
      ('facts_profile_version', ('STRING_V1', 'canonical_gold_volatility_structure_profile_v1')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY')),
      ('reason_codes', ('TUPLE_V1', ())),
      ('warning_codes', ('TUPLE_V1', ())),
      ('identity_available', ('BOOL_V1', True)),
      ('source_contract_version', ('STRING_V1', '1.0')),
      ('bundle_schema_version', ('STRING_V1', '1.0')),
      ('bundle_id', ('STRING_V1', 'demo-bundle-000000000001')),
      ('sequence', ('INT_V1', 1)),
      ('canonical_symbol', ('STRING_V1', 'XAUUSD')),
      ('broker_symbol', ('STRING_V1', 'GOLD')),
      ('reference_time_utc', ('STRING_V1', '2026-07-10T02:30:05.000000Z')),
      ('timeframes',
       ('TUPLE_V1',
        (('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_VOLATILITY_STRUCTURE_FACTS_V1',
          (('timeframe', ('STRING_V1', 'M15')),
           ('period_seconds', ('INT_V1', 900)),
           ('source_bar_count', ('INT_V1', 2)),
           ('pair_count', ('INT_V1', 1)),
           ('bar_pairs',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_PAIR_VOLATILITY_STRUCTURE_FACTS_V1',
               (('previous_open_time_utc', ('STRING_V1', '2026-07-10T02:00:00Z')),
                ('current_open_time_utc', ('STRING_V1', '2026-07-10T02:15:00Z')),
                ('previous_range_decimal', ('STRING_V1', '2.20')),
                ('current_range_decimal', ('STRING_V1', '1.60')),
                ('true_range_decimal', ('STRING_V1', '1.60')),
                ('body_signed_decimal', ('STRING_V1', '0.60')),
                ('body_absolute_decimal', ('STRING_V1', '0.60')),
                ('upper_wick_decimal', ('STRING_V1', '0.60')),
                ('lower_wick_decimal', ('STRING_V1', '0.40')),
                ('close_change_decimal', ('STRING_V1', '0.60')),
                ('high_change_decimal', ('STRING_V1', '0.30')),
                ('low_change_decimal', ('STRING_V1', '0.90')),
                ('direction_code', ('STRING_V1', 'UP')),
                ('range_relation_code', ('STRING_V1', 'CONTRACTED')),
                ('range_containment_code', ('STRING_V1', 'SHIFTED_UP')),
                ('current_high_vs_previous_high_code', ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')),
                ('current_low_vs_previous_low_code', ('STRING_V1', 'ABOVE_PREVIOUS_LOW')),
                ('current_close_vs_previous_range_code',
                 ('STRING_V1', 'INSIDE_PREVIOUS_RANGE')))),))))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_VOLATILITY_STRUCTURE_FACTS_V1',
          (('timeframe', ('STRING_V1', 'H1')),
           ('period_seconds', ('INT_V1', 3600)),
           ('source_bar_count', ('INT_V1', 2)),
           ('pair_count', ('INT_V1', 1)),
           ('bar_pairs',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_PAIR_VOLATILITY_STRUCTURE_FACTS_V1',
               (('previous_open_time_utc', ('STRING_V1', '2026-07-10T00:00:00Z')),
                ('current_open_time_utc', ('STRING_V1', '2026-07-10T01:00:00Z')),
                ('previous_range_decimal', ('STRING_V1', '4.80')),
                ('current_range_decimal', ('STRING_V1', '2.50')),
                ('true_range_decimal', ('STRING_V1', '2.50')),
                ('body_signed_decimal', ('STRING_V1', '1.10')),
                ('body_absolute_decimal', ('STRING_V1', '1.10')),
                ('upper_wick_decimal', ('STRING_V1', '0.60')),
                ('lower_wick_decimal', ('STRING_V1', '0.80')),
                ('close_change_decimal', ('STRING_V1', '1.10')),
                ('high_change_decimal', ('STRING_V1', '0.70')),
                ('low_change_decimal', ('STRING_V1', '3.00')),
                ('direction_code', ('STRING_V1', 'UP')),
                ('range_relation_code', ('STRING_V1', 'CONTRACTED')),
                ('range_containment_code', ('STRING_V1', 'SHIFTED_UP')),
                ('current_high_vs_previous_high_code', ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')),
                ('current_low_vs_previous_low_code', ('STRING_V1', 'ABOVE_PREVIOUS_LOW')),
                ('current_close_vs_previous_range_code', ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')))),))))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_VOLATILITY_STRUCTURE_FACTS_V1',
          (('timeframe', ('STRING_V1', 'H4')),
           ('period_seconds', ('INT_V1', 14400)),
           ('source_bar_count', ('INT_V1', 2)),
           ('pair_count', ('INT_V1', 1)),
           ('bar_pairs',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_PAIR_VOLATILITY_STRUCTURE_FACTS_V1',
               (('previous_open_time_utc', ('STRING_V1', '2026-07-09T16:00:00Z')),
                ('current_open_time_utc', ('STRING_V1', '2026-07-09T20:00:00Z')),
                ('previous_range_decimal', ('STRING_V1', '10.30')),
                ('current_range_decimal', ('STRING_V1', '5.50')),
                ('true_range_decimal', ('STRING_V1', '5.50')),
                ('body_signed_decimal', ('STRING_V1', '4.40')),
                ('body_absolute_decimal', ('STRING_V1', '4.40')),
                ('upper_wick_decimal', ('STRING_V1', '0.60')),
                ('lower_wick_decimal', ('STRING_V1', '0.50')),
                ('close_change_decimal', ('STRING_V1', '4.40')),
                ('high_change_decimal', ('STRING_V1', '3.20')),
                ('low_change_decimal', ('STRING_V1', '8.00')),
                ('direction_code', ('STRING_V1', 'UP')),
                ('range_relation_code', ('STRING_V1', 'CONTRACTED')),
                ('range_containment_code', ('STRING_V1', 'SHIFTED_UP')),
                ('current_high_vs_previous_high_code', ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')),
                ('current_low_vs_previous_low_code', ('STRING_V1', 'ABOVE_PREVIOUS_LOW')),
                ('current_close_vs_previous_range_code', ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')))),))))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_TIMEFRAME_VOLATILITY_STRUCTURE_FACTS_V1',
          (('timeframe', ('STRING_V1', 'D1')),
           ('period_seconds', ('INT_V1', 86400)),
           ('source_bar_count', ('INT_V1', 2)),
           ('pair_count', ('INT_V1', 1)),
           ('bar_pairs',
            ('TUPLE_V1',
             (('DATACLASS_V1',
               'CANONICAL_GOLD_BAR_PAIR_VOLATILITY_STRUCTURE_FACTS_V1',
               (('previous_open_time_utc', ('STRING_V1', '2026-07-08T00:00:00Z')),
                ('current_open_time_utc', ('STRING_V1', '2026-07-09T00:00:00Z')),
                ('previous_range_decimal', ('STRING_V1', '14.20')),
                ('current_range_decimal', ('STRING_V1', '22.60')),
                ('true_range_decimal', ('STRING_V1', '22.60')),
                ('body_signed_decimal', ('STRING_V1', '18.20')),
                ('body_absolute_decimal', ('STRING_V1', '18.20')),
                ('upper_wick_decimal', ('STRING_V1', '1.80')),
                ('lower_wick_decimal', ('STRING_V1', '2.60')),
                ('close_change_decimal', ('STRING_V1', '18.20')),
                ('high_change_decimal', ('STRING_V1', '17.20')),
                ('low_change_decimal', ('STRING_V1', '8.80')),
                ('direction_code', ('STRING_V1', 'UP')),
                ('range_relation_code', ('STRING_V1', 'EXPANDED')),
                ('range_containment_code', ('STRING_V1', 'SHIFTED_UP')),
                ('current_high_vs_previous_high_code', ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')),
                ('current_low_vs_previous_low_code', ('STRING_V1', 'ABOVE_PREVIOUS_LOW')),
                ('current_close_vs_previous_range_code',
                 ('STRING_V1', 'ABOVE_PREVIOUS_HIGH')))),)))))))),
      ('total_pair_count', ('INT_V1', 4)),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_trading_permission', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)),
      ('allowed_to_modify_risk', ('BOOL_V1', False)))),
    economic_calendar_result=
    ('DATACLASS_V1',
     'CANONICAL_GOLD_ECONOMIC_CALENDAR_SOURCE_ADAPTER_RESULT_V1',
     (('contract_version', ('STRING_V1', '1.0')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY')),
      ('reason_codes', ('TUPLE_V1', ())),
      ('warning_codes', ('TUPLE_V1', ())),
      ('snapshot_available', ('BOOL_V1', True)),
      ('snapshot',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_ECONOMIC_CALENDAR_SNAPSHOT_V1',
        (('contract_version', ('STRING_V1', '1.0')),
         ('calendar_schema_version', ('STRING_V1', '1.0')),
         ('calendar_snapshot_id', ('STRING_V1', 'canonical-gold-economic-calendar-docs-fixture-v1')),
         ('source_profile_version', ('STRING_V1', 'canonical_gold_economic_calendar_source_v1')),
         ('generated_at_utc', ('STRING_V1', '2026-07-10T02:30:04.900000Z')),
         ('coverage_start_utc', ('STRING_V1', '2026-07-09T02:30:05Z')),
         ('coverage_end_utc', ('STRING_V1', '2026-07-11T02:30:05.000001Z')),
         ('events',
          ('TUPLE_V1',
           (('DATACLASS_V1',
             'CANONICAL_GOLD_ECONOMIC_EVENT_SOURCE_V1',
             (('event_id', ('STRING_V1', 'event.001')),
              ('scheduled_at_utc', ('STRING_V1', '2026-07-10T03:00:00Z')),
              ('country_code', ('STRING_V1', 'US')),
              ('currency_code', ('STRING_V1', 'USD')),
              ('event_category_code', ('STRING_V1', 'US_CPI')),
              ('impact_code', ('STRING_V1', 'HIGH')),
              ('source_revision', ('INT_V1', 1)),
              ('event_status_code', ('STRING_V1', 'SCHEDULED')))),
            ('DATACLASS_V1',
             'CANONICAL_GOLD_ECONOMIC_EVENT_SOURCE_V1',
             (('event_id', ('STRING_V1', 'event.002')),
              ('scheduled_at_utc', ('STRING_V1', '2026-07-10T04:00:00Z')),
              ('country_code', ('STRING_V1', 'US')),
              ('currency_code', ('STRING_V1', 'USD')),
              ('event_category_code', ('STRING_V1', 'US_PCE')),
              ('impact_code', ('STRING_V1', 'MEDIUM')),
              ('source_revision', ('INT_V1', 2)),
              ('event_status_code', ('STRING_V1', 'SCHEDULED'))))))),
         ('upstream_evidence',
          ('DATACLASS_V1',
           'CANONICAL_GOLD_ECONOMIC_CALENDAR_UPSTREAM_EVIDENCE_V1',
           (('adapter_passed', ('BOOL_V1', True)),
            ('adapter_status_code', ('STRING_V1', 'CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY')),
            ('schema_validated', ('BOOL_V1', True)),
            ('identity_validated', ('BOOL_V1', True)),
            ('timestamps_normalized', ('BOOL_V1', True)),
            ('same_snapshot_bound', ('BOOL_V1', True)),
            ('warning_codes', ('TUPLE_V1', ())),
            ('raw_payload_discarded', ('BOOL_V1', True))))),
         ('read_only', ('BOOL_V1', True)),
         ('demo_only', ('BOOL_V1', True)),
         ('contains_raw_provider_payload', ('BOOL_V1', False))))),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_trading_permission', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)),
      ('allowed_to_modify_risk', ('BOOL_V1', False)))),
    economic_window_facts=
    ('DATACLASS_V1',
     'CANONICAL_GOLD_ECONOMIC_WINDOW_FACTS_V1',
     (('contract_version', ('STRING_V1', '1.0')),
      ('facts_profile_version', ('STRING_V1', 'canonical_gold_economic_window_profile_v1')),
      ('passed', ('BOOL_V1', True)),
      ('status_code', ('STRING_V1', 'CANONICAL_GOLD_ECONOMIC_WINDOW_READY')),
      ('reason_codes', ('TUPLE_V1', ())),
      ('warning_codes', ('TUPLE_V1', ())),
      ('identity_available', ('BOOL_V1', True)),
      ('source_contract_version', ('STRING_V1', '1.0')),
      ('bundle_schema_version', ('STRING_V1', '1.0')),
      ('bundle_id', ('STRING_V1', 'demo-bundle-000000000001')),
      ('sequence', ('INT_V1', 1)),
      ('canonical_symbol', ('STRING_V1', 'XAUUSD')),
      ('broker_symbol', ('STRING_V1', 'GOLD')),
      ('reference_time_utc', ('STRING_V1', '2026-07-10T02:30:05.000000Z')),
      ('calendar_contract_version', ('STRING_V1', '1.0')),
      ('calendar_schema_version', ('STRING_V1', '1.0')),
      ('calendar_snapshot_id', ('STRING_V1', 'canonical-gold-economic-calendar-docs-fixture-v1')),
      ('calendar_source_profile_version', ('STRING_V1', 'canonical_gold_economic_calendar_source_v1')),
      ('calendar_generated_at_utc', ('STRING_V1', '2026-07-10T02:30:04.900000Z')),
      ('calendar_coverage_start_utc', ('STRING_V1', '2026-07-09T02:30:05Z')),
      ('calendar_coverage_end_utc', ('STRING_V1', '2026-07-11T02:30:05.000001Z')),
      ('event_windows',
       ('TUPLE_V1',
        (('DATACLASS_V1',
          'CANONICAL_GOLD_ECONOMIC_EVENT_WINDOW_FACTS_V1',
          (('event_id', ('STRING_V1', 'event.001')),
           ('scheduled_at_utc', ('STRING_V1', '2026-07-10T03:00:00Z')),
           ('country_code', ('STRING_V1', 'US')),
           ('currency_code', ('STRING_V1', 'USD')),
           ('event_category_code', ('STRING_V1', 'US_CPI')),
           ('impact_code', ('STRING_V1', 'HIGH')),
           ('source_revision', ('INT_V1', 1)),
           ('window_start_utc', ('STRING_V1', '2026-07-10T02:30:00Z')),
           ('window_end_utc', ('STRING_V1', '2026-07-10T03:30:00Z')),
           ('event_offset_microseconds', ('INT_V1', 1795000000)),
           ('window_start_offset_microseconds', ('INT_V1', -5000000)),
           ('window_end_offset_microseconds', ('INT_V1', 3595000000)),
           ('window_relation_code', ('STRING_V1', 'ACTIVE')),
           ('is_active_observation_window', ('BOOL_V1', True)))),
         ('DATACLASS_V1',
          'CANONICAL_GOLD_ECONOMIC_EVENT_WINDOW_FACTS_V1',
          (('event_id', ('STRING_V1', 'event.002')),
           ('scheduled_at_utc', ('STRING_V1', '2026-07-10T04:00:00Z')),
           ('country_code', ('STRING_V1', 'US')),
           ('currency_code', ('STRING_V1', 'USD')),
           ('event_category_code', ('STRING_V1', 'US_PCE')),
           ('impact_code', ('STRING_V1', 'MEDIUM')),
           ('source_revision', ('INT_V1', 2)),
           ('window_start_utc', ('STRING_V1', '2026-07-10T03:45:00Z')),
           ('window_end_utc', ('STRING_V1', '2026-07-10T04:15:00Z')),
           ('event_offset_microseconds', ('INT_V1', 5395000000)),
           ('window_start_offset_microseconds', ('INT_V1', 4495000000)),
           ('window_end_offset_microseconds', ('INT_V1', 6295000000)),
           ('window_relation_code', ('STRING_V1', 'UPCOMING')),
           ('is_active_observation_window', ('BOOL_V1', False))))))),
      ('summary',
       ('DATACLASS_V1',
        'CANONICAL_GOLD_ECONOMIC_WINDOW_SUMMARY_V1',
        (('calendar_age_microseconds', ('INT_V1', 100000)),
         ('relevant_event_count', ('INT_V1', 2)),
         ('active_window_count', ('INT_V1', 1)),
         ('inside_any_observation_window', ('BOOL_V1', True)),
         ('active_event_ids', ('TUPLE_V1', (('STRING_V1', 'event.001'),))),
         ('nearest_previous_event_id', ('NONE_V1',)),
         ('nearest_previous_event_offset_microseconds', ('NONE_V1',)),
         ('nearest_next_event_id', ('STRING_V1', 'event.001')),
         ('nearest_next_event_offset_microseconds', ('INT_V1', 1795000000)),
         ('highest_active_impact_code', ('STRING_V1', 'HIGH'))))),
      ('read_only', ('BOOL_V1', True)),
      ('demo_only', ('BOOL_V1', True)),
      ('is_tradable', ('BOOL_V1', False)),
      ('can_execute', ('BOOL_V1', False)),
      ('is_trading_permission', ('BOOL_V1', False)),
      ('is_execution_instruction', ('BOOL_V1', False)),
      ('allowed_to_call_ea', ('BOOL_V1', False)),
      ('allowed_to_modify_risk', ('BOOL_V1', False)))),
)

_MARKET_IDENTITY: Final = (
    "1.0",
    "1.0",
    "demo-bundle-000000000001",
    1,
    "XAUUSD",
    "GOLD",
    "2026-07-10T02:30:05.000000Z",
)
_CALENDAR_IDENTITY: Final = (
    "1.0",
    "1.0",
    "canonical-gold-economic-calendar-docs-fixture-v1",
    "canonical_gold_economic_calendar_source_v1",
    "2026-07-10T02:30:04.900000Z",
    "2026-07-09T02:30:05Z",
    "2026-07-11T02:30:05.000001Z",
)

_DIAGNOSTICS_CASE: Final = CanonicalBundleReplayCaseV1(
    replay_contract_version=UPSTREAM_REPLAY_CONTRACT_VERSION,
    case_id="canonical_docs_ready",
    fixture_id="canonical_docs_fixture_v1",
)

_APPROVED_REGISTRY: Final = (
    CanonicalGoldFactsReplayRegistryRecordV1(
        registry_version=REGISTRY_VERSION,
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        stage_contract_version=STAGE_CONTRACT_VERSION,
        authority_profile_version=AUTHORITY_PROFILE_VERSION,
        stage_id=STAGE_ID,
        case_id="canonical_docs_ready",
        fixture_id="canonical_docs_fixture_v1",
        diagnostics_case=_DIAGNOSTICS_CASE,
        market_source_profile_version="canonical_gold_market_facts_policy_v1",
        market_facts_contract_version="1.0",
        session_facts_profile_version="canonical_gold_session_spread_freshness_profile_v1",
        volatility_facts_profile_version="canonical_gold_volatility_structure_profile_v1",
        calendar_source_profile_version="canonical_gold_economic_calendar_source_v1",
        economic_window_facts_profile_version="canonical_gold_economic_window_profile_v1",
        reference_time_utc="2026-07-10T02:30:05.000000Z",
        expected_market_identity=_MARKET_IDENTITY,
        expected_calendar_identity=_CALENDAR_IDENTITY,
        expected_oracle=_EXPECTED_ORACLE,
    ),
)
_REGISTRY = _APPROVED_REGISTRY

_MARKET_FIXTURE_FILENAMES: Final = (
    "snapshot_manifest.json",
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
_MARKET_FIXTURE_PATHS: Final = tuple(
    market_fixture._FIXED_PATHS[2] / name for name in _MARKET_FIXTURE_FILENAMES
)

_EXPECTED_RUN_DIAGNOSTICS = replay_v1.run_canonical_bundle_replay_case
_EXPECTED_BUILD_MARKET_SOURCE = market_fixture.build_canonical_gold_market_facts_docs_fixture_source_v1
_EXPECTED_BUILD_MARKET_FACTS = market_facts.build_canonical_gold_market_facts_snapshot_v1
_EXPECTED_BUILD_SESSION_FACTS = session_facts.build_canonical_gold_session_spread_freshness_facts_v1
_EXPECTED_BUILD_VOLATILITY_FACTS = volatility.build_canonical_gold_volatility_structure_facts_v1
_EXPECTED_BUILD_CALENDAR = calendar.build_server_owned_canonical_gold_economic_calendar_snapshot_v1
_EXPECTED_BUILD_ECONOMIC_FACTS = economic.build_canonical_gold_economic_window_facts_v1
_EXPECTED_VALIDATE_MARKET_RESULT = market_fixture._EXPECTED_VALIDATE_RESULT
_EXPECTED_VALIDATE_CALENDAR_RESULT = calendar._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1

_APPROVED_CAPSULE: Final = _AuthorityCapsule(
    diagnostics_runner=_EXPECTED_RUN_DIAGNOSTICS,
    market_source_builder=_EXPECTED_BUILD_MARKET_SOURCE,
    market_projector=_EXPECTED_BUILD_MARKET_FACTS,
    session_builder=_EXPECTED_BUILD_SESSION_FACTS,
    volatility_builder=_EXPECTED_BUILD_VOLATILITY_FACTS,
    calendar_builder=_EXPECTED_BUILD_CALENDAR,
    economic_builder=_EXPECTED_BUILD_ECONOMIC_FACTS,
    market_result_validator=_EXPECTED_VALIDATE_MARKET_RESULT,
    calendar_result_validator=_EXPECTED_VALIDATE_CALENDAR_RESULT,
    market_fixture_paths=_MARKET_FIXTURE_PATHS,
    calendar_fixture_path=calendar._EXPECTED_FIXTURE_PATH,
)
_CAPSULE = _APPROVED_CAPSULE

_STATUS_REASONS: Final = (
    (CANONICAL_GOLD_FACTS_REPLAY_MATCHED, ()),
    (CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID, (GOLD_FACTS_REPLAY_CASE_INPUT_INVALID,)),
    (CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID, (GOLD_FACTS_REPLAY_REGISTRY_INVALID,)),
    (CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID, (GOLD_FACTS_REPLAY_AUTHORITY_INVALID,)),
    (CANONICAL_GOLD_FACTS_REPLAY_DIAGNOSTICS_BLOCKED, (GOLD_FACTS_REPLAY_DIAGNOSTICS_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_MARKET_SOURCE_BLOCKED, (GOLD_FACTS_REPLAY_MARKET_SOURCE_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_BLOCKED, (GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_SESSION_FACTS_BLOCKED, (GOLD_FACTS_REPLAY_SESSION_FACTS_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_VOLATILITY_FACTS_BLOCKED, (GOLD_FACTS_REPLAY_VOLATILITY_FACTS_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_CALENDAR_BLOCKED, (GOLD_FACTS_REPLAY_CALENDAR_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_BLOCKED, (GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_NOT_READY,)),
    (CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, (GOLD_FACTS_REPLAY_RESULT_INVALID,)),
    (CANONICAL_GOLD_FACTS_REPLAY_MISMATCH, (GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH,)),
    (CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, (GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED,)),
)

_BLOCKED_BY_STAGE: Final = (
    (CANONICAL_GOLD_FACTS_REPLAY_DIAGNOSTICS_BLOCKED, GOLD_FACTS_REPLAY_DIAGNOSTICS_NOT_READY),
    (CANONICAL_GOLD_FACTS_REPLAY_MARKET_SOURCE_BLOCKED, GOLD_FACTS_REPLAY_MARKET_SOURCE_NOT_READY),
    (CANONICAL_GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_BLOCKED, GOLD_FACTS_REPLAY_MARKET_SNAPSHOT_NOT_READY),
    (CANONICAL_GOLD_FACTS_REPLAY_SESSION_FACTS_BLOCKED, GOLD_FACTS_REPLAY_SESSION_FACTS_NOT_READY),
    (CANONICAL_GOLD_FACTS_REPLAY_VOLATILITY_FACTS_BLOCKED, GOLD_FACTS_REPLAY_VOLATILITY_FACTS_NOT_READY),
    (CANONICAL_GOLD_FACTS_REPLAY_CALENDAR_BLOCKED, GOLD_FACTS_REPLAY_CALENDAR_NOT_READY),
    (CANONICAL_GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_BLOCKED, GOLD_FACTS_REPLAY_ECONOMIC_WINDOW_NOT_READY),
)

_READY_STATUSES: Final = (
    replay_v1.CANONICAL_BUNDLE_REPLAY_MATCHED,
    "CANONICAL_GOLD_SOURCE_ADAPTER_READY",
    "CANONICAL_GOLD_MARKET_FACTS_READY",
    "CANONICAL_GOLD_SESSION_SPREAD_FRESHNESS_READY",
    "CANONICAL_GOLD_VOLATILITY_STRUCTURE_READY",
    "CANONICAL_GOLD_ECONOMIC_CALENDAR_ADAPTER_READY",
    "CANONICAL_GOLD_ECONOMIC_WINDOW_READY",
)

_BLOCKED_STATUS_REASONS: Final = (
    frozenset(
        (
            (replay_v1.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID, replay_v1.REPLAY_CASE_INPUT_INVALID),
            (replay_v1.CANONICAL_BUNDLE_REPLAY_INPUT_INVALID, replay_v1.REPLAY_CASE_REGISTRY_INVALID),
            (replay_v1.CANONICAL_BUNDLE_REPLAY_RESULT_INVALID, replay_v1.REPLAY_CASE_RESULT_INVALID),
            (replay_v1.CANONICAL_BUNDLE_REPLAY_MISMATCH, replay_v1.REPLAY_CASE_EXPECTATION_MISMATCH),
            (replay_v1.CANONICAL_BUNDLE_REPLAY_SAFE_FAILURE, replay_v1.REPLAY_CASE_EXCEPTION_SANITIZED),
        )
    ),
    frozenset(),
    frozenset(
        (
            (market_facts._INPUT_INVALID_STATUS, market_facts._SOURCE_TYPE_INVALID),
            (market_facts._AUTHORITY_INVALID_STATUS, market_facts._SOURCE_AUTHORITY_INVALID),
            (market_facts._UPSTREAM_BLOCKED_STATUS, market_facts._UPSTREAM_NOT_READY),
            (market_facts._UPSTREAM_BLOCKED_STATUS, market_facts._UPSTREAM_WARNINGS_REJECTED),
            (market_facts._IDENTITY_INVALID_STATUS, market_facts._IDENTITY_INVALID),
            (market_facts._VALUE_INVALID_STATUS, market_facts._TICK_INVALID),
            (market_facts._VALUE_INVALID_STATUS, market_facts._BARS_INVALID),
            (market_facts._VALUE_INVALID_STATUS, market_facts._SYMBOL_SPEC_INVALID),
            (market_facts._VALUE_INVALID_STATUS, market_facts._FRESHNESS_INVALID),
            (market_facts._SAFE_FAILURE_STATUS, market_facts._EXCEPTION_SANITIZED),
        )
    ),
    frozenset(
        (
            (session_facts._INPUT_INVALID_STATUS, session_facts._INPUT_TYPE_INVALID),
            (session_facts._UPSTREAM_BLOCKED_STATUS, session_facts._SNAPSHOT_NOT_READY),
            (session_facts._IDENTITY_INVALID_STATUS, session_facts._SNAPSHOT_IDENTITY_INVALID),
            (session_facts._SESSION_INVALID_STATUS, session_facts._SESSION_INVALID),
            (session_facts._SPREAD_INVALID_STATUS, session_facts._SPREAD_INVALID),
            (session_facts._FRESHNESS_INVALID_STATUS, session_facts._FRESHNESS_INVALID),
            (session_facts._SAFE_FAILURE_STATUS, session_facts._EXCEPTION_SANITIZED),
        )
    ),
    frozenset(
        (
            (volatility._INPUT_INVALID_STATUS, volatility._INPUT_TYPE_INVALID),
            (volatility._UPSTREAM_BLOCKED_STATUS, volatility._SNAPSHOT_NOT_READY),
            (volatility._IDENTITY_INVALID_STATUS, volatility._SNAPSHOT_IDENTITY_INVALID),
            (volatility._TIMEFRAME_INVALID_STATUS, volatility._TIMEFRAME_INPUT_INVALID),
            (volatility._HISTORY_INSUFFICIENT_STATUS, volatility._HISTORY_INSUFFICIENT),
            (volatility._DECIMAL_INVALID_STATUS, volatility._DECIMAL_INPUT_INVALID),
            (volatility._RESULT_INVALID_STATUS, volatility._RESULT_INVALID),
            (volatility._SAFE_FAILURE_STATUS, volatility._EXCEPTION_SANITIZED),
        )
    ),
    frozenset(),
    frozenset(economic._FAILURES),
)

_RESULT_TYPES: Final = (
    CanonicalBundleReplayResultV1,
    CanonicalGoldMarketFactsSourceAdapterResultV1,
    CanonicalGoldMarketFactsSnapshotV1,
    CanonicalGoldSessionSpreadFreshnessFactsV1,
    CanonicalGoldVolatilityStructureFactsV1,
    CanonicalGoldEconomicCalendarSourceAdapterResultV1,
    CanonicalGoldEconomicWindowFactsV1,
)

_FROZEN_ORACLES: Final = (
    _EXPECTED_ORACLE.diagnostics_result,
    _EXPECTED_ORACLE.market_source_result,
    _EXPECTED_ORACLE.market_facts_snapshot,
    _EXPECTED_ORACLE.session_spread_freshness_facts,
    _EXPECTED_ORACLE.volatility_structure_facts,
    _EXPECTED_ORACLE.economic_calendar_result,
    _EXPECTED_ORACLE.economic_window_facts,
)


def run_canonical_gold_facts_replay_case_v1(
    *,
    replay_case: CanonicalGoldFactsReplayCaseV1,
) -> CanonicalGoldFactsReplayResultV1:
    """Run the fixed offline W6 facts replay stage."""

    try:
        if not _case_is_safe(replay_case):
            return _failure(CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID, GOLD_FACTS_REPLAY_CASE_INPUT_INVALID)
        registry_snapshot = _REGISTRY
        if not _registry_is_safe(registry_snapshot):
            return _failure(CANONICAL_GOLD_FACTS_REPLAY_REGISTRY_INVALID, GOLD_FACTS_REPLAY_REGISTRY_INVALID)
        record = _resolve_record(replay_case, registry_snapshot)
        if record is None:
            return _failure(CANONICAL_GOLD_FACTS_REPLAY_INPUT_INVALID, GOLD_FACTS_REPLAY_CASE_INPUT_INVALID)
        capsule_snapshot = _CAPSULE
        if not _authority_is_safe(capsule_snapshot):
            return _failure(CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID, GOLD_FACTS_REPLAY_AUTHORITY_INVALID)
        fixture_snapshot = _fixture_state(capsule_snapshot)
        if fixture_snapshot is None:
            return _failure(CANONICAL_GOLD_FACTS_REPLAY_AUTHORITY_INVALID, GOLD_FACTS_REPLAY_AUTHORITY_INVALID)
        immutable_snapshot = _immutable_state(replay_case, registry_snapshot, capsule_snapshot)
    except Exception:
        return _failure(CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED)

    results: list[object] = []
    try:
        diagnostics_result = replay_v1.run_canonical_bundle_replay_case(replay_case=record.diagnostics_case)
        results.append(diagnostics_result)
        failure = _after_stage(0, diagnostics_result, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, ())
        if failure is not None:
            return failure

        market_source_result = market_fixture.build_canonical_gold_market_facts_docs_fixture_source_v1()
        results.append(market_source_result)
        failure = _after_stage(1, market_source_result, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, tuple(results[:-1]))
        if failure is not None:
            return failure
        source = market_source_result.source
        source_snapshot = _freeze_value(source, allow_market_floats=True)

        market_snapshot = market_facts.build_canonical_gold_market_facts_snapshot_v1(validated_source=source)
        results.append(market_snapshot)
        failure = _after_stage(2, market_snapshot, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, tuple(results[:-1]))
        if failure is not None or _freeze_value(source, allow_market_floats=True) != source_snapshot:
            return failure or _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)
        market_snapshot_state = _freeze_value(market_snapshot)

        session_result = session_facts.build_canonical_gold_session_spread_freshness_facts_v1(market_facts_snapshot=market_snapshot)
        results.append(session_result)
        failure = _after_stage(3, session_result, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, tuple(results[:-1]))
        if failure is not None or _freeze_value(market_snapshot) != market_snapshot_state:
            return failure or _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)

        volatility_result = volatility.build_canonical_gold_volatility_structure_facts_v1(market_facts_snapshot=market_snapshot)
        results.append(volatility_result)
        failure = _after_stage(4, volatility_result, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, tuple(results[:-1]))
        if failure is not None or _freeze_value(market_snapshot) != market_snapshot_state:
            return failure or _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)

        calendar_authority = _build_calendar_authority()
        calendar_authority_state = calendar._authority_snapshot(calendar_authority)
        calendar_result = calendar.build_server_owned_canonical_gold_economic_calendar_snapshot_v1(authority=calendar_authority)
        results.append(calendar_result)
        failure = _after_stage(5, calendar_result, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, tuple(results[:-1]), calendar_authority=calendar_authority)
        if failure is not None or calendar._authority_snapshot(calendar_authority) != calendar_authority_state:
            return failure or _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)
        calendar_snapshot = calendar_result.snapshot
        calendar_snapshot_state = _freeze_value(calendar_snapshot)

        economic_result = economic.build_canonical_gold_economic_window_facts_v1(market_facts_snapshot=market_snapshot, economic_calendar_snapshot=calendar_snapshot)
        results.append(economic_result)
        failure = _after_stage(6, economic_result, record, replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, tuple(results[:-1]))
        if failure is not None or _freeze_value(market_snapshot) != market_snapshot_state or _freeze_value(calendar_snapshot) != calendar_snapshot_state:
            return failure or _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)

        if not _identities_match(record, tuple(results)):
            return _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)
        return _matched_result(record, tuple(results))
    except Exception:
        return _failure(CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE, GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED)


def _after_stage(
    index: int,
    result: object,
    record: CanonicalGoldFactsReplayRegistryRecordV1,
    replay_case: CanonicalGoldFactsReplayCaseV1,
    registry_snapshot: tuple[CanonicalGoldFactsReplayRegistryRecordV1, ...],
    capsule_snapshot: _AuthorityCapsule,
    fixture_snapshot: tuple[object, ...],
    immutable_snapshot: tuple[object, ...],
    earlier_results: tuple[object, ...],
    *,
    calendar_authority: object | None = None,
) -> CanonicalGoldFactsReplayResultV1 | None:
    if not _evidence_is_unchanged(replay_case, registry_snapshot, capsule_snapshot, fixture_snapshot, immutable_snapshot, earlier_results):
        return _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)
    assessment = _assess_stage(index, result, record, calendar_authority=calendar_authority)
    if assessment == "ready":
        return None
    if assessment == "blocked":
        status, reason = _BLOCKED_BY_STAGE[index]
        return _failure(status, reason)
    if assessment == "mismatch":
        return _failure(CANONICAL_GOLD_FACTS_REPLAY_MISMATCH, GOLD_FACTS_REPLAY_EXPECTATION_MISMATCH)
    return _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)


def _assess_stage(
    index: int,
    result: object,
    record: CanonicalGoldFactsReplayRegistryRecordV1,
    *,
    calendar_authority: object | None = None,
) -> str:
    if type(result) is not _RESULT_TYPES[index] or not _has_exact_registered_shape(result):
        return "invalid"
    if index == 1:
        valid = market_fixture._EXPECTED_VALIDATE_RESULT(result=result)
        if type(valid) is not bool or valid is not True:
            return "invalid"
    if index == 5:
        valid = calendar._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1(adapter_result=result, authority=calendar_authority)
        if type(valid) is not bool or valid is not True:
            return "invalid"
    frozen = _freeze_value(result, allow_summary_containers=index == 0, allow_market_floats=index == 1)
    if result.passed is True:
        if not _ready_shape_is_safe(index, result):
            return "invalid"
        return "ready" if frozen == _FROZEN_ORACLES[index] else "mismatch"
    if result.passed is False and _blocked_shape_is_safe(index, result):
        return "blocked"
    return "invalid"


def _ready_shape_is_safe(index: int, result: object) -> bool:
    reasons = result.replay_reason_codes if index == 0 else result.reason_codes
    return (
        result.status_code == _READY_STATUSES[index]
        and type(reasons) is tuple
        and reasons == ()
        and _safety_flags_are_safe(result)
    )


def _blocked_shape_is_safe(index: int, result: object) -> bool:
    reasons = result.replay_reason_codes if index == 0 else result.reason_codes
    return (
        type(result.status_code) is str
        and _PUBLIC_CODE_PATTERN.fullmatch(result.status_code) is not None
        and _is_string_tuple(reasons)
        and len(reasons) == 1
        and _PUBLIC_CODE_PATTERN.fullmatch(reasons[0]) is not None
        and (
            index in {1, 5}
            or (result.status_code, reasons[0]) in _BLOCKED_STATUS_REASONS[index]
        )
        and _failure_evidence_is_cleared(index, result)
        and _safety_flags_are_safe(result)
    )


def _failure_evidence_is_cleared(index: int, result: object) -> bool:
    if index == 0:
        return result.canonical_summary == {} and result.canonical_block_reasons == () and result.canonical_warning_codes == ()
    if index == 1:
        return result.source_available is False and result.source is None and result.warning_codes == ()
    if index == 2:
        return not result.identity_available and result.bundle_schema_version is None and result.bundle_id is None and result.sequence is None and result.canonical_symbol is None and result.broker_symbol is None and result.reference_time_utc is None and result.quote is None and result.timeframes == () and result.symbol_spec is None and result.freshness is None
    if index == 3:
        return not result.identity_available and result.bundle_schema_version is None and result.bundle_id is None and result.sequence is None and result.canonical_symbol is None and result.broker_symbol is None and result.reference_time_utc is None and result.session is None and result.spread is None and result.freshness is None
    if index == 4:
        return not result.identity_available and result.source_contract_version is None and result.bundle_schema_version is None and result.bundle_id is None and result.sequence is None and result.canonical_symbol is None and result.broker_symbol is None and result.reference_time_utc is None and result.timeframes == () and result.total_pair_count == 0
    if index == 5:
        return result.snapshot_available is False and result.snapshot is None and result.warning_codes == ()
    return not result.identity_available and result.source_contract_version is None and result.bundle_schema_version is None and result.bundle_id is None and result.sequence is None and result.canonical_symbol is None and result.broker_symbol is None and result.reference_time_utc is None and result.calendar_contract_version is None and result.calendar_schema_version is None and result.calendar_snapshot_id is None and result.calendar_source_profile_version is None and result.calendar_generated_at_utc is None and result.calendar_coverage_start_utc is None and result.calendar_coverage_end_utc is None and result.event_windows == () and result.summary is None


def _case_is_safe(value: object) -> bool:
    return (
        type(value) is CanonicalGoldFactsReplayCaseV1
        and tuple(field.name for field in fields(value)) == ("replay_contract_version", "stage_contract_version", "stage_id", "case_id", "fixture_id")
        and all(type(getattr(value, field.name)) is str for field in fields(value))
        and value.replay_contract_version == REPLAY_CONTRACT_VERSION
        and value.stage_contract_version == STAGE_CONTRACT_VERSION
        and value.stage_id == STAGE_ID
        and _identifier_is_safe(value.case_id)
        and _identifier_is_safe(value.fixture_id)
    )


def _registry_is_safe(value: object) -> bool:
    return (
        type(value) is tuple
        and len(value) == 1
        and value is _APPROVED_REGISTRY
        and value == _APPROVED_REGISTRY
        and _record_is_safe(value[0])
    )


def _record_is_safe(record: object) -> bool:
    try:
        return (
            type(record) is CanonicalGoldFactsReplayRegistryRecordV1
            and tuple(field.name for field in fields(record)) == tuple(field.name for field in fields(CanonicalGoldFactsReplayRegistryRecordV1))
            and record.registry_version == REGISTRY_VERSION
            and record.replay_contract_version == REPLAY_CONTRACT_VERSION
            and record.stage_contract_version == STAGE_CONTRACT_VERSION
            and record.authority_profile_version == AUTHORITY_PROFILE_VERSION
            and record.stage_id == STAGE_ID
            and record.diagnostics_case == _DIAGNOSTICS_CASE
            and record.market_source_profile_version == "canonical_gold_market_facts_policy_v1"
            and record.market_facts_contract_version == "1.0"
            and record.session_facts_profile_version == "canonical_gold_session_spread_freshness_profile_v1"
            and record.volatility_facts_profile_version == "canonical_gold_volatility_structure_profile_v1"
            and record.calendar_source_profile_version == "canonical_gold_economic_calendar_source_v1"
            and record.economic_window_facts_profile_version == "canonical_gold_economic_window_profile_v1"
            and record.reference_time_utc == "2026-07-10T02:30:05.000000Z"
            and record.expected_market_identity == _MARKET_IDENTITY
            and record.expected_calendar_identity == _CALENDAR_IDENTITY
            and record.expected_oracle is _EXPECTED_ORACLE
            and all(_is_valid_frozen_value(getattr(record.expected_oracle, field.name)) for field in fields(record.expected_oracle))
        )
    except Exception:
        return False


def _resolve_record(replay_case: CanonicalGoldFactsReplayCaseV1, registry: tuple[CanonicalGoldFactsReplayRegistryRecordV1, ...]) -> CanonicalGoldFactsReplayRegistryRecordV1 | None:
    record = registry[0]
    return record if (replay_case.case_id, replay_case.fixture_id) == (record.case_id, record.fixture_id) else None


def _authority_is_safe(value: object) -> bool:
    try:
        return (
            type(value) is _AuthorityCapsule
            and value is _APPROVED_CAPSULE
            and value.diagnostics_runner is _EXPECTED_RUN_DIAGNOSTICS is replay_v1.run_canonical_bundle_replay_case
            and value.market_source_builder is _EXPECTED_BUILD_MARKET_SOURCE is market_fixture.build_canonical_gold_market_facts_docs_fixture_source_v1
            and value.market_projector is _EXPECTED_BUILD_MARKET_FACTS is market_facts.build_canonical_gold_market_facts_snapshot_v1
            and value.session_builder is _EXPECTED_BUILD_SESSION_FACTS is session_facts.build_canonical_gold_session_spread_freshness_facts_v1
            and value.volatility_builder is _EXPECTED_BUILD_VOLATILITY_FACTS is volatility.build_canonical_gold_volatility_structure_facts_v1
            and value.calendar_builder is _EXPECTED_BUILD_CALENDAR is calendar.build_server_owned_canonical_gold_economic_calendar_snapshot_v1
            and value.economic_builder is _EXPECTED_BUILD_ECONOMIC_FACTS is economic.build_canonical_gold_economic_window_facts_v1
            and value.market_result_validator is _EXPECTED_VALIDATE_MARKET_RESULT is market_fixture._EXPECTED_VALIDATE_RESULT
            and value.calendar_result_validator is _EXPECTED_VALIDATE_CALENDAR_RESULT is calendar._is_safe_canonical_gold_economic_calendar_source_adapter_result_v1
            and value.market_fixture_paths is _MARKET_FIXTURE_PATHS
            and value.calendar_fixture_path is calendar._EXPECTED_FIXTURE_PATH
            and _schemas_are_safe()
        )
    except Exception:
        return False


def _schemas_are_safe() -> bool:
    return (
        type(_PRODUCTION_SCHEMAS) is tuple
        and len(_PRODUCTION_SCHEMAS) == 28
        and len(_SCHEMA_BY_CLASS) == len(_SCHEMA_BY_TYPE_CODE) == 28
        and all(type(schema) is _ProductionSchema and tuple(field.name for field in fields(schema.class_object)) == schema.ordered_fields for schema in _PRODUCTION_SCHEMAS)
    )


def _build_calendar_authority() -> calendar._CanonicalGoldEconomicCalendarSourceAuthorityV1:
    return calendar._CanonicalGoldEconomicCalendarSourceAuthorityV1(
        authority_token=calendar._AUTHORITY_TOKEN,
        allowed_root=calendar._EXPECTED_ALLOWED_ROOT,
        fixture_path=calendar._EXPECTED_FIXTURE_PATH,
        reference_time_utc=calendar._FIXED_REFERENCE_TIME,
        expected_identity=calendar._EXPECTED_IDENTITY,
        read_policy=calendar._READ_POLICY,
        calendar_schema_version="1.0",
        source_profile_version="canonical_gold_economic_calendar_source_v1",
    )


def _fixture_state(capsule: _AuthorityCapsule) -> tuple[object, ...] | None:
    try:
        paths = (*capsule.market_fixture_paths, capsule.calendar_fixture_path)
        state = []
        for path in paths:
            if type(path) is not type(calendar._EXPECTED_FIXTURE_PATH) or not path.is_file():
                return None
            stat_result = path.stat()
            state.append((path, stat_result.st_mode, stat_result.st_size, stat_result.st_mtime_ns, path.read_bytes()))
        return tuple(state)
    except Exception:
        return None


def _immutable_state(replay_case: CanonicalGoldFactsReplayCaseV1, registry: tuple[CanonicalGoldFactsReplayRegistryRecordV1, ...], capsule: _AuthorityCapsule) -> tuple[object, ...]:
    return (
        tuple(getattr(replay_case, field.name) for field in fields(replay_case)),
        _record_state(registry[0]),
        tuple((field.name, getattr(registry[0].expected_oracle, field.name)) for field in fields(registry[0].expected_oracle)),
        tuple(getattr(capsule, field.name) for field in fields(capsule)),
    )


def _record_state(record: CanonicalGoldFactsReplayRegistryRecordV1) -> tuple[object, ...]:
    return tuple((field.name, getattr(record, field.name)) for field in fields(record))


def _evidence_is_unchanged(replay_case: CanonicalGoldFactsReplayCaseV1, registry_snapshot: tuple[CanonicalGoldFactsReplayRegistryRecordV1, ...], capsule_snapshot: _AuthorityCapsule, fixture_snapshot: tuple[object, ...], immutable_snapshot: tuple[object, ...], earlier_results: tuple[object, ...]) -> bool:
    try:
        return (
            _REGISTRY is registry_snapshot
            and _CAPSULE is capsule_snapshot
            and _registry_is_safe(registry_snapshot)
            and _authority_is_safe(capsule_snapshot)
            and _immutable_state(replay_case, registry_snapshot, capsule_snapshot) == immutable_snapshot
            and _fixture_state(capsule_snapshot) == fixture_snapshot
            and all(
                _has_exact_registered_shape(value)
                and _freeze_value(
                    value,
                    allow_summary_containers=index == 0,
                    allow_market_floats=index == 1,
                )
                == _FROZEN_ORACLES[index]
                for index, value in enumerate(earlier_results)
            )
        )
    except Exception:
        return False


def _has_exact_registered_shape(value: object) -> bool:
    schema = _SCHEMA_BY_CLASS.get(type(value))
    return schema is not None and tuple(field.name for field in fields(value)) == schema.ordered_fields


def _freeze_value(value: object, *, allow_summary_containers: bool = False, allow_market_floats: bool = False) -> tuple[object, ...]:
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
            raise TypeError
        payload = value.hex()
        if float.fromhex(payload).hex() != payload:
            raise TypeError
        return ("FLOAT_HEX_V1", payload)
    if value_type is tuple:
        return ("TUPLE_V1", tuple(_freeze_value(item, allow_summary_containers=allow_summary_containers, allow_market_floats=allow_market_floats) for item in value))
    if value_type is list and allow_summary_containers:
        return ("LIST_V1", tuple(_freeze_value(item, allow_summary_containers=True) for item in value))
    if value_type is dict and allow_summary_containers:
        pairs = tuple((_freeze_value(key, allow_summary_containers=True), _freeze_value(item, allow_summary_containers=True)) for key, item in value.items())
        if len({key for key, _ in pairs}) != len(pairs):
            raise TypeError
        return ("DICT_V1", pairs)
    if is_dataclass(value) and not isinstance(value, type):
        schema = _SCHEMA_BY_CLASS.get(value_type)
        if schema is None or tuple(field.name for field in fields(value)) != schema.ordered_fields:
            raise TypeError
        encoded = []
        for name in schema.ordered_fields:
            encoded.append((name, _freeze_value(getattr(value, name), allow_summary_containers=value_type is CanonicalBundleReplayResultV1 and name == "canonical_summary", allow_market_floats=allow_market_floats)))
        return ("DATACLASS_V1", schema.type_code, tuple(encoded))
    raise TypeError


def _is_valid_frozen_value(value: object) -> bool:
    try:
        if type(value) is not tuple or not value or type(value[0]) is not str:
            return False
        tag = value[0]
        if tag == "NONE_V1":
            return len(value) == 1
        if tag == "BOOL_V1":
            return len(value) == 2 and type(value[1]) is bool
        if tag == "INT_V1":
            return len(value) == 2 and type(value[1]) is int
        if tag == "STRING_V1":
            return len(value) == 2 and type(value[1]) is str
        if tag == "FLOAT_HEX_V1":
            return len(value) == 2 and type(value[1]) is str and math.isfinite(float.fromhex(value[1])) and float.fromhex(value[1]).hex() == value[1]
        if tag in {"TUPLE_V1", "LIST_V1"}:
            return len(value) == 2 and type(value[1]) is tuple and all(_is_valid_frozen_value(item) for item in value[1])
        if tag == "DICT_V1":
            return len(value) == 2 and type(value[1]) is tuple and all(type(pair) is tuple and len(pair) == 2 and _is_valid_frozen_value(pair[0]) and _is_valid_frozen_value(pair[1]) for pair in value[1]) and len({pair[0] for pair in value[1]}) == len(value[1])
        if tag == "DATACLASS_V1":
            schema = _SCHEMA_BY_TYPE_CODE.get(value[1]) if len(value) == 3 and type(value[1]) is str else None
            return schema is not None and type(value[2]) is tuple and tuple(pair[0] for pair in value[2]) == schema.ordered_fields and all(type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str and _is_valid_frozen_value(pair[1]) for pair in value[2])
        return False
    except Exception:
        return False


def _identities_match(record: CanonicalGoldFactsReplayRegistryRecordV1, results: tuple[object, ...]) -> bool:
    try:
        diagnostics, source_result, snapshot, session_result, volatility_result, calendar_result, economic_result = results
        source = source_result.source
        calendar_snapshot = calendar_result.snapshot
        return (
            (diagnostics.replay_contract_version, diagnostics.registry_version, diagnostics.pipeline_contract_version, diagnostics.policy_profile_version, diagnostics.case_id, diagnostics.fixture_id)
            == (UPSTREAM_REPLAY_CONTRACT_VERSION, UPSTREAM_REPLAY_REGISTRY_VERSION, "canonical_diagnostics_pipeline_g153_v1", "canonical_diagnostics_default_policy_v1", "canonical_docs_ready", "canonical_docs_fixture_v1")
            and _market_identity_from_source(source) == record.expected_market_identity
            and _market_identity_from_snapshot(snapshot) == record.expected_market_identity
            and _market_identity_from_facts(session_result) == record.expected_market_identity[1:]
            and _market_identity_from_volatility(volatility_result) == record.expected_market_identity
            and _market_identity_from_economic(economic_result) == record.expected_market_identity
            and _calendar_identity_from_snapshot(calendar_snapshot) == record.expected_calendar_identity
            and _calendar_identity_from_economic(economic_result) == record.expected_calendar_identity
            and source.reference_time_utc == snapshot.reference_time_utc == session_result.reference_time_utc == volatility_result.reference_time_utc == economic_result.reference_time_utc == record.reference_time_utc
        )
    except Exception:
        return False


def _market_identity_from_source(value: object) -> tuple[object, ...]:
    return (value.contract_version, value.bundle_schema_version, value.bundle_id, value.sequence, value.canonical_symbol, value.broker_symbol, value.reference_time_utc)


def _market_identity_from_snapshot(value: object) -> tuple[object, ...]:
    return (value.contract_version, value.bundle_schema_version, value.bundle_id, value.sequence, value.canonical_symbol, value.broker_symbol, value.reference_time_utc)


def _market_identity_from_facts(value: object) -> tuple[object, ...]:
    return (value.bundle_schema_version, value.bundle_id, value.sequence, value.canonical_symbol, value.broker_symbol, value.reference_time_utc)


def _market_identity_from_volatility(value: object) -> tuple[object, ...]:
    return (value.source_contract_version, value.bundle_schema_version, value.bundle_id, value.sequence, value.canonical_symbol, value.broker_symbol, value.reference_time_utc)


def _market_identity_from_economic(value: object) -> tuple[object, ...]:
    return (value.source_contract_version, value.bundle_schema_version, value.bundle_id, value.sequence, value.canonical_symbol, value.broker_symbol, value.reference_time_utc)


def _calendar_identity_from_snapshot(value: object) -> tuple[object, ...]:
    return (value.contract_version, value.calendar_schema_version, value.calendar_snapshot_id, value.source_profile_version, value.generated_at_utc, value.coverage_start_utc, value.coverage_end_utc)


def _calendar_identity_from_economic(value: object) -> tuple[object, ...]:
    return (value.calendar_contract_version, value.calendar_schema_version, value.calendar_snapshot_id, value.calendar_source_profile_version, value.calendar_generated_at_utc, value.calendar_coverage_start_utc, value.calendar_coverage_end_utc)


def _detach(value: Any) -> Any:
    value_type = type(value)
    if value is None or value_type in {bool, int, float, str}:
        return value
    if value_type is tuple:
        return tuple([_detach(item) for item in value])
    if value_type is list:
        return [_detach(item) for item in value]
    if value_type is dict:
        return {_detach(key): _detach(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return value_type(**{field.name: _detach(getattr(value, field.name)) for field in fields(value)})
    raise TypeError


def _matched_result(record: CanonicalGoldFactsReplayRegistryRecordV1, results: tuple[object, ...]) -> CanonicalGoldFactsReplayResultV1:
    detached = tuple(_detach(value) for value in results)
    result = CanonicalGoldFactsReplayResultV1(
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        stage_contract_version=STAGE_CONTRACT_VERSION,
        registry_version=REGISTRY_VERSION,
        stage_id=STAGE_ID,
        passed=True,
        status_code=CANONICAL_GOLD_FACTS_REPLAY_MATCHED,
        reason_codes=(),
        identity_available=True,
        case_id=record.case_id,
        fixture_id=record.fixture_id,
        completed_stage_ids=tuple(list(STAGE_ORDER)),
        diagnostics_result=detached[0],
        market_source_result=detached[1],
        market_facts_snapshot=detached[2],
        session_spread_freshness_facts=detached[3],
        volatility_structure_facts=detached[4],
        economic_calendar_result=detached[5],
        economic_window_facts=detached[6],
        **_safety_values(),
    )
    return result if _result_is_safe(result) else _failure(CANONICAL_GOLD_FACTS_REPLAY_RESULT_INVALID, GOLD_FACTS_REPLAY_RESULT_INVALID)


def _failure(status: str, reason: str) -> CanonicalGoldFactsReplayResultV1:
    result = CanonicalGoldFactsReplayResultV1(
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        stage_contract_version=STAGE_CONTRACT_VERSION,
        registry_version=REGISTRY_VERSION,
        stage_id=STAGE_ID,
        passed=False,
        status_code=status,
        reason_codes=(reason,),
        identity_available=False,
        case_id=None,
        fixture_id=None,
        completed_stage_ids=(),
        diagnostics_result=None,
        market_source_result=None,
        market_facts_snapshot=None,
        session_spread_freshness_facts=None,
        volatility_structure_facts=None,
        economic_calendar_result=None,
        economic_window_facts=None,
        **_safety_values(),
    )
    if _result_is_safe(result):
        return result
    return CanonicalGoldFactsReplayResultV1(
        replay_contract_version=REPLAY_CONTRACT_VERSION,
        stage_contract_version=STAGE_CONTRACT_VERSION,
        registry_version=REGISTRY_VERSION,
        stage_id=STAGE_ID,
        passed=False,
        status_code=CANONICAL_GOLD_FACTS_REPLAY_SAFE_FAILURE,
        reason_codes=(GOLD_FACTS_REPLAY_EXCEPTION_SANITIZED,),
        identity_available=False,
        case_id=None,
        fixture_id=None,
        completed_stage_ids=(),
        diagnostics_result=None,
        market_source_result=None,
        market_facts_snapshot=None,
        session_spread_freshness_facts=None,
        volatility_structure_facts=None,
        economic_calendar_result=None,
        economic_window_facts=None,
        **_safety_values(),
    )


def _result_is_safe(result: object) -> bool:
    try:
        if type(result) is not CanonicalGoldFactsReplayResultV1 or tuple(field.name for field in fields(result)) != tuple(field.name for field in fields(CanonicalGoldFactsReplayResultV1)):
            return False
        if result.replay_contract_version != REPLAY_CONTRACT_VERSION or result.stage_contract_version != STAGE_CONTRACT_VERSION or result.registry_version != REGISTRY_VERSION or result.stage_id != STAGE_ID or not _safety_flags_are_safe(result):
            return False
        if (result.status_code, result.reason_codes) not in _STATUS_REASONS:
            return False
        if result.passed:
            nested = (result.diagnostics_result, result.market_source_result, result.market_facts_snapshot, result.session_spread_freshness_facts, result.volatility_structure_facts, result.economic_calendar_result, result.economic_window_facts)
            return result.status_code == CANONICAL_GOLD_FACTS_REPLAY_MATCHED and result.identity_available is True and result.case_id == "canonical_docs_ready" and result.fixture_id == "canonical_docs_fixture_v1" and result.completed_stage_ids == STAGE_ORDER and all(type(value) is expected for value, expected in zip(nested, _RESULT_TYPES, strict=True)) and all(_freeze_value(value, allow_summary_containers=index == 0, allow_market_floats=index == 1) == _FROZEN_ORACLES[index] for index, value in enumerate(nested))
        return not result.identity_available and result.case_id is None and result.fixture_id is None and result.completed_stage_ids == () and all(getattr(result, name) is None for name in ("diagnostics_result", "market_source_result", "market_facts_snapshot", "session_spread_freshness_facts", "volatility_structure_facts", "economic_calendar_result", "economic_window_facts"))
    except Exception:
        return False


def _safety_values() -> dict[str, bool]:
    return {"read_only": True, "demo_only": True, "is_tradable": False, "can_execute": False, "is_trading_permission": False, "is_execution_instruction": False, "allowed_to_call_ea": False, "allowed_to_modify_risk": False}


def _safety_flags_are_safe(value: object) -> bool:
    try:
        expected = _safety_values()
        return all(type(getattr(value, name)) is bool and getattr(value, name) is expected_value for name, expected_value in expected.items() if hasattr(value, name)) and value.read_only is True and value.demo_only is True and value.is_tradable is False and value.can_execute is False and value.allowed_to_call_ea is False
    except Exception:
        return False


def _identifier_is_safe(value: object) -> bool:
    return type(value) is str and value.isascii() and _IDENTIFIER_PATTERN.fullmatch(value) is not None


def _is_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)
