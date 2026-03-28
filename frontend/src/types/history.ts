/** TypeScript types for comparison history API. */

export interface HistoryRecord {
  id: number;
  task_id: number | null;
  source_connection_id: number;
  target_connection_id: number;
  source_table: string;
  target_table: string;
  compare_mode: string;
  source_row_count: number | null;
  target_row_count: number | null;
  diff_count: number;
  diff_percentage: number | null;
  has_critical_diffs: boolean;
  started_at: string;
  completed_at: string | null;
  status: string;
  error_message: string | null;
  result_summary: Record<string, unknown> | null;
  created_at: string;
}

export interface TrendDataPoint {
  date: string;
  diff_count: number;
  completed_count: number;
}

export interface TrendResponse {
  period: 'daily' | 'weekly' | 'monthly';
  data_points: TrendDataPoint[];
  total_comparisons: number;
  total_diffs: number;
  avg_diff_count: number;
}

export interface HistoryStats {
  total_comparisons: number;
  completed: number;
  failed: number;
  avg_diff_count: number;
  max_diff_count: number;
  last_24h_comparisons: number;
  last_7d_comparisons: number;
}
