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
