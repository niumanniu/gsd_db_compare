import { useMutation } from '@tanstack/react-query';
import apiClient from '../api/client';
import type {
  SchemaCompareRequest,
  SchemaDiffResponse,
  ReportExportRequest,
  MultiTableCompareRequest,
  MultiTableCompareResponse,
  DatabaseCompareRequest,
  DatabaseCompareResponse,
} from '../types';

export function useComparison() {
  const compareMutation = useMutation<SchemaDiffResponse, Error, SchemaCompareRequest>({
    mutationFn: (data: SchemaCompareRequest) =>
      apiClient.post('/api/compare/schema', data).then(r => r.data),
  });

  // Multi-table batch comparison
  const compareBatchMutation = useMutation<MultiTableCompareResponse, Error, MultiTableCompareRequest>({
    mutationFn: (data: MultiTableCompareRequest) =>
      apiClient.post('/api/compare/schema/batch', data).then(r => r.data),
  });

  // Database-level comparison
  const compareDatabaseMutation = useMutation<DatabaseCompareResponse, Error, DatabaseCompareRequest>({
    mutationFn: (data: DatabaseCompareRequest) =>
      apiClient.post('/api/compare/schema/database', data).then(r => r.data),
  });

  // Report export mutations
  const exportHtmlMutation = useMutation({
    mutationFn: async (data: ReportExportRequest) => {
      const response = await apiClient.post('/api/reports/html', data, {
        responseType: 'blob',
      });
      return response.data;
    },
  });

  const exportExcelMutation = useMutation({
    mutationFn: async (data: ReportExportRequest) => {
      const response = await apiClient.post('/api/reports/excel', data, {
        responseType: 'blob',
      });
      return response.data;
    },
  });

  // Utility function to download blob
  const downloadReport = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return {
    // Single table comparison
    compareSchemas: compareMutation.mutateAsync,
    isComparing: compareMutation.isPending,
    comparisonResult: compareMutation.data ?? null,
    error: compareMutation.error,
    resetComparison: compareMutation.reset,

    // Multi-table comparison
    compareBatch: compareBatchMutation.mutateAsync,
    isComparingBatch: compareBatchMutation.isPending,
    batchComparisonResult: compareBatchMutation.data ?? null,

    // Database comparison
    compareDatabase: compareDatabaseMutation.mutateAsync,
    isComparingDatabase: compareDatabaseMutation.isPending,
    databaseComparisonResult: compareDatabaseMutation.data ?? null,

    // Report exports
    exportHTML: exportHtmlMutation.mutateAsync,
    exportExcel: exportExcelMutation.mutateAsync,
    isExporting: exportHtmlMutation.isPending || exportExcelMutation.isPending,
    downloadReport,
  };
}
