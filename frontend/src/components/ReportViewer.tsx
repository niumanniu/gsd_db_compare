import { Button, Space, message } from 'antd';
import { DownloadOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import apiClient from '../api/client';
import type { SchemaDiffResponse } from '../types';

interface ReportViewerProps {
  diffResult: SchemaDiffResponse | null;
  sourceDb: string;
  targetDb: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  diffResult,
  sourceDb,
  targetDb,
}) => {
  const handleExportHTML = async () => {
    try {
      const response = await apiClient.post('/api/reports/html', {
        diff_result: diffResult,
        source_db: sourceDb,
        target_db: targetDb,
      }, {
        responseType: 'blob',
      });
      // Trigger download
      const blob = new Blob([response.data], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `comparison_report_${Date.now()}.html`;
      link.click();
      window.URL.revokeObjectURL(url);
      message.success('HTML report downloaded');
    } catch (error) {
      console.error('HTML export failed:', error);
      message.error('Failed to generate HTML report');
    }
  };

  const handleExportExcel = async () => {
    try {
      const response = await apiClient.post('/api/reports/excel', {
        diff_result: diffResult,
        source_db: sourceDb,
        target_db: targetDb,
      }, {
        responseType: 'blob',
      });
      // Trigger download
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `comparison_report_${Date.now()}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
      message.success('Excel report downloaded');
    } catch (error) {
      console.error('Excel export failed:', error);
      message.error('Failed to generate Excel report');
    }
  };

  if (!diffResult) {
    return null;
  }

  return (
    <div style={{ marginTop: 24, padding: '16px', background: '#f5f5f5', borderRadius: 8 }}>
      <div style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
        Export Report
      </div>
      <Space>
        <Button
          type="primary"
          icon={<FileTextOutlined />}
          onClick={handleExportHTML}
          disabled={!diffResult}
        >
          Export HTML
        </Button>
        <Button
          type="primary"
          icon={<FileExcelOutlined />}
          onClick={handleExportExcel}
          disabled={!diffResult}
        >
          Export Excel
        </Button>
      </Space>
    </div>
  );
};
