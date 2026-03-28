/** API client for comparison history. */

import apiClient from './client';
import type { HistoryRecord, TrendResponse, HistoryStats } from '../types/history';

export const historyApi = {
  /** Get comparison history records with pagination and filters. */
  getAll: (params: {
    task_id?: number;
    status?: string;
    page?: number;
    limit?: number;
  }) =>
    apiClient.get<HistoryRecord[]>('/api/comparison-history', { params }),

  /** Get a specific history record by ID. */
  getById: (id: number) =>
    apiClient.get<HistoryRecord>(`/api/comparison-history/${id}`),

  /** Get trend data for visualizing comparison history over time. */
  getTrend: (params: {
    period?: 'daily' | 'weekly' | 'monthly';
    days?: number;
    task_id?: number;
  }) =>
    apiClient.get<TrendResponse>('/api/comparison-history/trend', { params }),

  /** Get statistics summary of comparison history. */
  getStats: (params?: { task_id?: number }) =>
    apiClient.get<HistoryStats>('/api/comparison-history/stats', { params }),
};
