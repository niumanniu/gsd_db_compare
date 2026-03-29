import { useState, useCallback } from 'react';
import apiClient from '../api/client';
import type {
  MultiTableDataCompareRequest,
  MultiTableDataCompareResponse,
  TableDataResult,
} from '../types/data_compare';

interface UseMultiTableComparison {
  compareTables: (request: MultiTableDataCompareRequest) => Promise<void>;
  isLoading: boolean;
  progress: number;
  results: Map<string, TableDataResult>;
  summary: MultiTableDataCompareResponse['summary'] | null;
  error: string | null;
  reset: () => void;
}

/**
 * Hook for managing multi-table data comparison state
 */
export const useMultiTableComparison = (): UseMultiTableComparison => {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<Map<string, TableDataResult>>(new Map());
  const [summary, setSummary] = useState<MultiTableDataCompareResponse['summary'] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const compareTables = useCallback(async (request: MultiTableDataCompareRequest) => {
    setIsLoading(true);
    setProgress(0);
    setResults(new Map());
    setSummary(null);
    setError(null);

    try {
      // Simulate progress updates during comparison
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 5, 90));
      }, 500);

      const response = await apiClient.post<MultiTableDataCompareResponse>(
        '/api/compare/multi-table-data',
        request
      );

      clearInterval(progressInterval);
      setProgress(100);

      // Store results in map keyed by source_table
      const resultsMap = new Map<string, TableDataResult>();
      response.data.table_results.forEach((result) => {
        resultsMap.set(result.source_table, result);
      });
      setResults(resultsMap);
      setSummary(response.data.summary);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsLoading(false);
    setProgress(0);
    setResults(new Map());
    setSummary(null);
    setError(null);
  }, []);

  return {
    compareTables,
    isLoading,
    progress,
    results,
    summary,
    error,
    reset,
  };
};
