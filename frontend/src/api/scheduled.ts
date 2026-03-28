/** API client for scheduled tasks. */

import apiClient from './client';
import type {
  ScheduledTask,
  ScheduledTaskCreate,
  ScheduledTaskUpdate,
} from '../types/scheduled';

export const scheduledApi = {
  /** Get all scheduled tasks. */
  getAll: (enabledOnly = false) =>
    apiClient.get<ScheduledTask[]>('/api/scheduled-tasks', { params: { enabled_only: enabledOnly } }),

  /** Get a specific scheduled task by ID. */
  getById: (id: number) =>
    apiClient.get<ScheduledTask>(`/api/scheduled-tasks/${id}`),

  /** Create a new scheduled task. */
  create: (data: ScheduledTaskCreate) =>
    apiClient.post<ScheduledTask>('/api/scheduled-tasks', data),

  /** Update an existing scheduled task. */
  update: (id: number, data: ScheduledTaskUpdate) =>
    apiClient.put<ScheduledTask>(`/api/scheduled-tasks/${id}`, data),

  /** Delete a scheduled task. */
  delete: (id: number) =>
    apiClient.delete(`/api/scheduled-tasks/${id}`),

  /** Run a scheduled task immediately. */
  runNow: (id: number) =>
    apiClient.post<{ status: string; message: string }>(`/api/scheduled-tasks/${id}/run`),

  /** Toggle a scheduled task's enabled status. */
  toggle: (id: number) =>
    apiClient.post<ScheduledTask>(`/api/scheduled-tasks/${id}/toggle`),
};
