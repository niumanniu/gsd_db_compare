/** TypeScript types for data comparison API. */

import type { SchemaDiffResponse } from './index';

/** Request payload for data comparison. */
export interface DataCompareRequest {
  source_connection_id: number;
  target_connection_id: number;
  source_table: string;
  target_table: string;
  mode?: 'auto' | 'full' | 'hash' | 'sample';
  threshold?: number;
  sample_size?: number;
  batch_size?: number;
}

/** Single field-level difference. */
export interface FieldDiff {
  field_name: string;
  source_value: unknown | null;
  target_value: unknown | null;
  diff_type: 'value' | 'null' | 'type' | 'length';  // Maps to backend's 'difference_type'
}

/** Row-level difference between source and target. */
export interface RowDiff {
  primary_key_value: unknown;
  diff_type: 'missing_in_target' | 'missing_in_source' | 'content_diff';
  field_diffs: FieldDiff[];
  source_row: Record<string, unknown> | null;
  target_row: Record<string, unknown> | null;
}

/** Summary statistics from data comparison. */
export interface DataSummary {
  source_table: string;
  target_table: string;
  source_row_count: number;
  target_row_count: number;
  diff_count: number;
  diff_percentage: number | null;
  mode_used: 'full' | 'hash' | 'sample' | 'hash+sample';
  has_more: boolean;
  source_hash?: string;
  target_hash?: string;
  sampled_row_count?: number;
}

/** Response payload for data comparison. */
export interface DataCompareResponse {
  summary: DataSummary;
  diffs: RowDiff[];
  has_more: boolean;
}

// ============ Multi-Table Comparison Types ============

/** Request for batch multi-table schema comparison. */
export interface MultiTableCompareRequest {
  source_connection_id: number;
  target_connection_id: number;
  source_tables: string[];
  target_tables: string[];
  table_mapping?: Record<string, string>;
}

/** Summary of a single table comparison in batch/database compare. */
export interface TableCompareSummary {
  source_table: string;
  target_table: string;
  has_differences: boolean;
  diff_count: number;
  status: 'success' | 'error';
  error_message?: string;
}

/** Response for multi-table batch comparison. */
export interface MultiTableCompareResponse {
  summary: TableCompareSummary[];
  table_results: Record<string, SchemaDiffResponse>;
}

/** Request for database-level comparison. */
export interface DatabaseCompareRequest {
  source_connection_id: number;
  target_connection_id: number;
  exclude_patterns: string[];
}

/** Response for database-level comparison. */
export interface DatabaseCompareResponse {
  source_database: string;
  target_database: string;
  source_connection_name: string;
  target_connection_name: string;
  source_connection_id: number;
  target_connection_id: number;
  total_tables: number;
  compared_tables: number;
  tables_with_diffs: number;
  table_summaries: TableCompareSummary[];
  excluded_tables: string[];
  unmatched_source_tables: string[];
  unmatched_target_tables: string[];
}

// ============ Multi-Table Data Comparison Types ============

/** Request for multi-table data comparison. */
export interface MultiTableDataCompareRequest {
  source_connection_id: number;
  target_connection_id: number;
  source_schema: string;
  target_schema: string;
  source_tables: string[];
  target_tables: string[];
  table_mapping?: Record<string, string>;
  mode?: 'auto' | 'full' | 'hash' | 'sample';
  threshold?: number;
  sample_size?: number;
  timeout_per_table?: number;
}

/** Result of single table data comparison. */
export interface TableDataResult {
  source_table: string;
  target_table: string;
  status: 'success' | 'error' | 'skipped';
  source_row_count: number;
  target_row_count: number;
  diff_count: number;
  diff_percentage: number | null;
  mode_used: string;
  is_identical: boolean;
  error_message?: string;
  source_hash?: string;
  target_hash?: string;
}

/** Summary statistics for multi-table data comparison. */
export interface MultiTableDataSummary {
  total_tables: number;
  compared_tables: number;
  identical_tables: number;
  tables_with_diffs: number;
  error_tables: number;
  total_rows_compared: number;
  total_diffs_found: number;
  elapsed_time_seconds: number;
}

/** Response for multi-table data comparison. */
export interface MultiTableDataCompareResponse {
  summary: MultiTableDataSummary;
  table_results: TableDataResult[];
}

// ============ Schema-Level Data Comparison Types ============

/** Request for schema-level data comparison. */
export interface SchemaDataCompareRequest {
  source_connection_id: number;
  target_connection_id: number;
  source_schema: string;
  target_schema: string;
  exclude_patterns?: string[];
  include_patterns?: string[];
  only_common_tables?: boolean;
  mode?: 'auto' | 'full' | 'hash' | 'sample';
  threshold?: number;
  sample_size?: number;
  timeout_per_table?: number;
}

/** Summary statistics for schema-level comparison. */
export interface SchemaDataCompareSummary {
  source_schema: string;
  target_schema: string;
  source_connection_name: string;
  target_connection_name: string;
  total_source_tables: number;
  total_target_tables: number;
  common_tables: number;
  unmatched_source_tables: number;
  unmatched_target_tables: number;
  compared_tables: number;
  identical_tables: number;
  tables_with_diffs: number;
  error_tables: number;
  total_rows_source: number;
  total_rows_target: number;
  total_diffs_found: number;
  overall_diff_percentage: number | null;
  elapsed_time_seconds: number;
}

/** Response for schema-level data comparison. */
export interface SchemaDataCompareResponse {
  summary: SchemaDataCompareSummary;
  table_results: TableDataResult[];
  unmatched_source_tables: string[];
  unmatched_target_tables: string[];
  excluded_tables: string[];
}
