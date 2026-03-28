/** TypeScript types for scheduled tasks API. */

export interface TableMapping {
  source: string;
  target: string;
  critical: boolean;
}

export interface ScheduledTask {
  id: number;
  name: string;
  description: string | null;
  cron_expression: string;
  source_connection_id: number;
  target_connection_id: number;
  tables: TableMapping[];
  compare_mode: 'schema' | 'data' | 'both';
  notification_enabled: boolean;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledTaskCreate {
  name: string;
  description?: string;
  cron_expression: string;
  source_connection_id: number;
  target_connection_id: number;
  tables: TableMapping[];
  compare_mode?: 'schema' | 'data' | 'both';
  notification_enabled?: boolean;
  enabled?: boolean;
}

export interface ScheduledTaskUpdate {
  name?: string;
  description?: string;
  cron_expression?: string;
  tables?: TableMapping[];
  compare_mode?: 'schema' | 'data' | 'both';
  notification_enabled?: boolean;
  enabled?: boolean;
}
