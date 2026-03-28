/** TypeScript types for data comparison API. */

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
  diff_type: 'value' | 'null' | 'type' | 'length';
}

/** Row-level difference between source and target. */
export interface RowDiff {
  primary_key: unknown;
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
