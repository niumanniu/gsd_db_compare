/** TypeScript types for critical tables API. */

export interface CriticalTable {
  id: number;
  connection_id: number;
  table_name: string;
  created_at: string;
}

export interface CriticalTableCreate {
  connection_id: number;
  table_name: string;
}

export interface CriticalTableCheckResponse {
  table_name: string;
  is_critical: boolean;
}
