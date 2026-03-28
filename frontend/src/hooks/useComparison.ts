import { useMutation } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { SchemaCompareRequest, SchemaDiffResponse, ReportExportRequest } from '../types';

export function useComparison() {
  const compareMutation = useMutation<SchemaDiffResponse, Error, SchemaCompareRequest>({
    mutationFn: (data: SchemaCompareRequest) =>
      apiClient.post('/api/compare/schema', data).then(r => r.data),
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
    compareSchemas: compareMutation.mutateAsync,
    isComparing: compareMutation.isPending,
    comparisonResult: compareMutation.data ?? null,
    error: compareMutation.error,
    resetComparison: compareMutation.reset,
    exportHTML: exportHtmlMutation.mutateAsync,
    exportExcel: exportExcelMutation.mutateAsync,
    isExporting: exportHtmlMutation.isPending || exportExcelMutation.isPending,
    downloadReport,
  };
}
