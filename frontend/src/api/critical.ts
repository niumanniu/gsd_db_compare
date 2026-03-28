/** API client for critical tables. */

import apiClient from './client';
import type { CriticalTable, CriticalTableCreate, CriticalTableCheckResponse } from '../types/critical';

export const criticalApi = {
  /** Get all critical tables for a connection. */
  getAll: (connectionId: number) =>
    apiClient.get<CriticalTable[]>('/api/critical-tables', { params: { connection_id: connectionId } }),

  /** Mark a table as critical. */
  create: (data: CriticalTableCreate) =>
    apiClient.post<CriticalTable>('/api/critical-tables', data),

  /** Remove a critical table marker. */
  delete: (id: number) =>
    apiClient.delete(`/api/critical-tables/${id}`),

  /** Check if a table is marked as critical. */
  check: (connectionId: number, tableName: string) =>
    apiClient.get<CriticalTableCheckResponse>('/api/critical-tables/check', {
      params: { connection_id: connectionId, table_name: tableName },
    }),
};
