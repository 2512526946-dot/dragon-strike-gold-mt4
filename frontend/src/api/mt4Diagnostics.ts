import { apiGet } from "./client";

export type Mt4DiagnosticsFileKey =
  | "live_tick"
  | "latest_bars"
  | "symbol_spec"
  | "account_snapshot";

export type Mt4DiagnosticsFileMap<TFileSummary> = Record<
  Mt4DiagnosticsFileKey,
  TFileSummary
>;

export type Mt4ReadSummary = {
  total_files: number;
  present_file_count: number;
  readable_object_count: number;
  missing_files: string[];
  not_file_paths: string[];
  invalid_json_files: string[];
  not_object_files: string[];
  read_error_files: string[];
  all_files_present: boolean;
  all_json_valid: boolean;
  all_objects: boolean;
  can_proceed_to_metadata_checks: boolean;
  status_code: string;
};

export type Mt4MetadataFileSummary = {
  file_name: string;
  expected_file_type: string;
  actual_file_type: string | null;
  has_schema_version: boolean;
  has_file_type: boolean;
  has_source: boolean;
  has_generated_at: boolean;
  file_type_matches: boolean;
  source_matches: boolean;
  can_proceed_to_freshness_checks: boolean;
  status_code: string;
  error_codes: string[];
};

export type Mt4MetadataStatusSummary = {
  all_metadata_present: boolean;
  all_file_types_match: boolean;
  all_sources_match: boolean;
  can_proceed_to_freshness_checks: boolean;
  status_code: string;
  files: Mt4DiagnosticsFileMap<Mt4MetadataFileSummary>;
};

export type Mt4FreshnessFileSummary = {
  file_name: string;
  generated_at: string | null;
  age_seconds: number | null;
  max_age_seconds: number;
  max_future_skew_seconds: number;
  is_parseable: boolean;
  is_fresh: boolean;
  is_stale: boolean;
  is_from_future: boolean;
  can_proceed_to_data_quality_gate: boolean;
  status_code: string;
  error_codes: string[];
};

export type Mt4FreshnessStatusSummary = {
  all_generated_at_parseable: boolean;
  all_files_fresh: boolean;
  any_file_stale: boolean;
  any_file_from_future: boolean;
  can_proceed_to_data_quality_gate: boolean;
  status_code: string;
  files: Mt4DiagnosticsFileMap<Mt4FreshnessFileSummary>;
};

export type Mt4GateV0ResultSummary = {
  stage: string;
  status_code: string;
  can_proceed_to_schema_checks: boolean;
  blocked_by_read_status: boolean;
  blocked_by_metadata: boolean;
  blocked_by_freshness: boolean;
  reasons: string[];
  source_read_status_code: string | null;
  source_metadata_status_code: string | null;
  source_freshness_status_code: string | null;
  is_tradable: false;
  note: string;
};

export type Mt4RequiredFieldsFileSummary = {
  file_name: string;
  required_fields: string[];
  present_fields: string[];
  missing_fields: string[];
  null_fields: string[];
  all_required_fields_present: boolean;
  can_proceed_to_value_checks: boolean;
  status_code: string;
  error_codes: string[];
};

export type Mt4RequiredFieldsStatusSummary = {
  all_required_fields_present: boolean;
  can_proceed_to_value_checks: boolean;
  status_code: string;
  reasons: string[];
  is_tradable: false;
  note: string;
  files: Mt4DiagnosticsFileMap<Mt4RequiredFieldsFileSummary>;
};

export type Mt4FieldTypeIssueSummary = {
  field_path: string;
  expected_type: string;
  actual_type: string;
};

export type Mt4FieldTypesFileSummary = {
  file_name: string;
  expected_field_types: Record<string, string>;
  valid_type_fields: string[];
  wrong_type_fields: string[];
  type_issues: Mt4FieldTypeIssueSummary[];
  all_field_types_valid: boolean;
  can_proceed_to_value_checks: boolean;
  status_code: string;
  error_codes: string[];
};

export type Mt4FieldTypesStatusSummary = {
  all_field_types_valid: boolean;
  can_proceed_to_value_checks: boolean;
  status_code: string;
  reasons: string[];
  is_tradable: false;
  note: string;
  files: Mt4DiagnosticsFileMap<Mt4FieldTypesFileSummary>;
};

export type Mt4NumericRangeIssueSummary = {
  field_path: string;
  rule: string;
};

export type Mt4NumericRangesFileSummary = {
  file_name: string;
  checked_fields: string[];
  invalid_fields: string[];
  range_issues: Mt4NumericRangeIssueSummary[];
  all_numeric_ranges_valid: boolean;
  can_proceed_to_cross_field_checks: boolean;
  status_code: string;
  error_codes: string[];
};

export type Mt4NumericRangesStatusSummary = {
  all_numeric_ranges_valid: boolean;
  can_proceed_to_cross_field_checks: boolean;
  status_code: string;
  reasons: string[];
  is_tradable: false;
  note: string;
  files: Mt4DiagnosticsFileMap<Mt4NumericRangesFileSummary>;
};

export type Mt4CrossFieldIssueSummary = {
  rule_name: string;
  field_paths: string[];
  message: string;
};

export type Mt4CrossFieldFileSummary = {
  file_name: string;
  checked_rules: string[];
  violated_rules: string[];
  cross_field_issues: Mt4CrossFieldIssueSummary[];
  all_cross_field_checks_valid: boolean;
  can_proceed_to_data_quality_gate_finalization: boolean;
  status_code: string;
  error_codes: string[];
};

export type Mt4CrossFieldStatusSummary = {
  all_cross_field_checks_valid: boolean;
  can_proceed_to_data_quality_gate_finalization: boolean;
  status_code: string;
  reasons: string[];
  is_tradable: false;
  note: string;
  files: Mt4DiagnosticsFileMap<Mt4CrossFieldFileSummary>;
};

export type Mt4GateV1ResultSummary = {
  stage: string;
  status_code: string;
  data_quality_passed: boolean;
  can_proceed_to_read_only_analysis: boolean;
  blocked_by_gate_v0: boolean;
  blocked_by_required_fields: boolean;
  blocked_by_field_types: boolean;
  blocked_by_numeric_ranges: boolean;
  blocked_by_cross_field_checks: boolean;
  reasons: string[];
  source_gate_v0_status_code: string | null;
  source_required_fields_status_code: string | null;
  source_field_types_status_code: string | null;
  source_numeric_ranges_status_code: string | null;
  source_cross_field_status_code: string | null;
  is_tradable: false;
  note: string;
};

export type Mt4DiagnosticsResponse = {
  stage: string;
  status_code: string;
  data_quality_passed: boolean;
  can_proceed_to_read_only_analysis: boolean;
  is_tradable: false;
  note: string;
  read_summary: Mt4ReadSummary;
  metadata_status: Mt4MetadataStatusSummary;
  freshness_status: Mt4FreshnessStatusSummary;
  gate_v0_result: Mt4GateV0ResultSummary;
  required_fields_status: Mt4RequiredFieldsStatusSummary;
  field_types_status: Mt4FieldTypesStatusSummary;
  numeric_ranges_status: Mt4NumericRangesStatusSummary;
  cross_field_status: Mt4CrossFieldStatusSummary;
  gate_v1_result: Mt4GateV1ResultSummary;
};

export function getMt4Diagnostics(): Promise<Mt4DiagnosticsResponse> {
  return apiGet<Mt4DiagnosticsResponse>("/api/mt4/diagnostics");
}
