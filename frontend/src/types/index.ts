export interface Connection {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface ConnectionCreate {
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export interface TableInfo {
  table_name: string;
  table_type: string;
  row_count: number | null;
  create_time: string | null;
}

export interface SchemaCompareRequest {
  source_connection_id: number;
  source_table: string;
  target_connection_id: number;
  target_table: string;
}

export interface ColumnDiff {
  column_name: string;
  diff_type: string;
  source_definition: Record<string, unknown> | null;
  target_definition: Record<string, unknown> | null;
  differences: string[];
}

export interface IndexDiff {
  index_name: string;
  diff_type: string;
  source_definition: Record<string, unknown> | null;
  target_definition: Record<string, unknown> | null;
  differences: string[];
}

export interface ConstraintDiff {
  constraint_name: string;
  diff_type: string;
  constraint_type: string;
  source_definition: Record<string, unknown> | null;
  target_definition: Record<string, unknown> | null;
  differences: string[];
}

export interface SchemaDiffResponse {
  source_table: string;
  target_table: string;
  column_diffs: ColumnDiff[];
  index_diffs: IndexDiff[];
  constraint_diffs: ConstraintDiff[];
  has_differences: boolean;
  diff_count?: number;
  source_db_type?: string;
  target_db_type?: string;
  comparison_mode?: string;
}

export interface ReportExportRequest {
  diff_result: SchemaDiffResponse;
  source_db: string;
  target_db: string;
}

// Re-export data comparison types
export type {
  DataCompareRequest,
  DataCompareResponse,
  DataSummary,
  FieldDiff,
  RowDiff,
} from './data_compare';

// Re-export scheduled task types
export type {
  ScheduledTask,
  ScheduledTaskCreate,
  ScheduledTaskUpdate,
  TableMapping,
} from './scheduled';

// Re-export history types
export type {
  HistoryRecord,
  TrendDataPoint,
  TrendResponse,
  HistoryStats,
} from './history';

// Re-export critical table types
export type {
  CriticalTable,
  CriticalTableCreate,
  CriticalTableCheckResponse,
} from './critical';
