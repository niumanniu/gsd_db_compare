import { useState, useCallback } from 'react';
import apiClient from '../api/client';
import type {
  SchemaDataCompareRequest,
  SchemaDataCompareResponse,
  TableDataResult,
} from '../types/data_compare';

interface UseSchemaDataComparison {
  compareSchema: (request: SchemaDataCompareRequest) => Promise<void>;
  isLoading: boolean;
  progress: number;
  results: Map<string, TableDataResult>;
  summary: SchemaDataCompareResponse['summary'] | null;
  unmatchedSourceTables: string[];
  unmatchedTargetTables: string[];
  excludedTables: string[];
  error: string | null;
  reset: () => void;
}

/**
 * Hook for managing schema-level data comparison state
 */
export const useSchemaDataComparison = (): UseSchemaDataComparison => {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<Map<string, TableDataResult>>(new Map());
  const [summary, setSummary] = useState<SchemaDataCompareResponse['summary'] | null>(null);
  const [unmatchedSourceTables, setUnmatchedSourceTables] = useState<string[]>([]);
  const [unmatchedTargetTables, setUnmatchedTargetTables] = useState<string[]>([]);
  const [excludedTables, setExcludedTables] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const compareSchema = useCallback(async (request: SchemaDataCompareRequest) => {
    setIsLoading(true);
    setProgress(0);
    setResults(new Map());
    setSummary(null);
    setUnmatchedSourceTables([]);
    setUnmatchedTargetTables([]);
    setExcludedTables([]);
    setError(null);

    try {
      // Simulate progress updates during comparison
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 5, 90));
      }, 500);

      const response = await apiClient.post<SchemaDataCompareResponse>(
        '/api/compare/schema-data',
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
      setUnmatchedSourceTables(response.data.unmatched_source_tables);
      setUnmatchedTargetTables(response.data.unmatched_target_tables);
      setExcludedTables(response.data.excluded_tables);
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
    setUnmatchedSourceTables([]);
    setUnmatchedTargetTables([]);
    setExcludedTables([]);
    setError(null);
  }, []);

  return {
    compareSchema,
    isLoading,
    progress,
    results,
    summary,
    unmatchedSourceTables,
    unmatchedTargetTables,
    excludedTables,
    error,
    reset,
  };
};
