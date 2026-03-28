import { useMutation } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { DataCompareRequest, DataCompareResponse } from '../types/data_compare';

// Extended error type with status code
interface ApiError extends Error {
  status?: number;
  detail?: string;
}

/**
 * Error messages mapped by status code
 */
const ERROR_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your connections and table names.',
  401: 'Authentication failed. Please verify database credentials.',
  404: 'Table not found. Please verify the table name exists.',
  413: 'Memory limit exceeded. Try using Hash mode for large tables.',
  503: 'Database connection failed. Please check connection settings.',
  504: 'Comparison timed out. Try using Hash or Sample mode for large tables.',
};

/**
 * Get user-friendly error message based on status code
 */
const getUserMessage = (status?: number, defaultMessage?: string): string => {
  if (status && ERROR_MESSAGES[status]) {
    return ERROR_MESSAGES[status];
  }
  if (defaultMessage) {
    return defaultMessage;
  }
  return 'An unexpected error occurred. Please try again.';
};

export function useDataComparison() {
  const compareDataMutation = useMutation<DataCompareResponse, ApiError, DataCompareRequest>({
    mutationFn: async (data: DataCompareRequest) => {
      try {
        const response = await apiClient.post('/api/compare/data', data);
        return response.data;
      } catch (error: any) {
        // Extract status code and detail from axios error
        const apiError: ApiError = new Error(
          error.response?.data?.detail || error.message || 'Connection failed'
        );
        apiError.status = error.response?.status;
        apiError.detail = error.response?.data?.detail;
        throw apiError;
      }
    },
  });

  // Get user-friendly error message
  const errorMessage = compareDataMutation.error
    ? getUserMessage(compareDataMutation.error.status, compareDataMutation.error.message)
    : null;

  return {
    compareData: compareDataMutation.mutateAsync,
    isComparing: compareDataMutation.isPending,
    comparisonResult: compareDataMutation.data ?? null,
    error: compareDataMutation.error,
    errorMessage,
    errorStatus: compareDataMutation.error?.status,
    resetComparison: compareDataMutation.reset,
  };
}
