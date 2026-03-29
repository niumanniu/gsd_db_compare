import React, { useState } from 'react';
import { Table, Typography, Tag, Empty, Button, Space, Modal, Collapse, Spin } from 'antd';
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DiffOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import type {
  MultiTableCompareResponse,
  DatabaseCompareResponse,
  TableCompareSummary,
  SchemaDiffResponse,
} from '../types';
import { SchemaDiffViewer } from './SchemaDiffViewer';

const { Panel } = Collapse;
const { Text, Title, Paragraph } = Typography;

interface MultiTableDiffViewerProps {
  result: MultiTableCompareResponse | null;
  onTableClick?: (tableName: string) => void;
}

export const MultiTableDiffViewer: React.FC<MultiTableDiffViewerProps> = ({
  result,
  onTableClick,
}) => {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  if (!result) {
    return (
      <Empty
        description="No comparison results yet"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  const { summary, table_results } = result;

  // Build table columns
  const columns = [
    {
      title: 'Source Table',
      dataIndex: 'source_table',
      key: 'source_table',
      render: (text: string, record: TableCompareSummary) => (
        <Text strong>{text}</Text>
      ),
    },
    {
      title: 'Target Table',
      dataIndex: 'target_table',
      key: 'target_table',
      render: (text: string) => <Text>{text}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: 'success' | 'error') => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Has Differences',
      dataIndex: 'has_differences',
      key: 'has_differences',
      render: (hasDiffs: boolean) => (
        <Tag color={hasDiffs ? 'orange' : 'green'}>
          {hasDiffs ? <DiffOutlined /> : <CheckCircleOutlined />}
          {hasDiffs ? 'YES' : 'NO'}
        </Tag>
      ),
    },
    {
      title: 'Diff Count',
      dataIndex: 'diff_count',
      key: 'diff_count',
      render: (count: number, record: TableCompareSummary) => (
        <Text type={count > 0 ? 'danger' : 'secondary'}>{count}</Text>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: unknown, record: TableCompareSummary) => (
        <Button
          type="link"
          size="small"
          disabled={record.status !== 'success' || !record.has_differences}
          onClick={() => setSelectedTable(record.source_table)}
        >
          View Details
        </Button>
      ),
    },
  ];

  // Calculate summary stats
  const totalTables = summary.length;
  const tablesWithDiffs = summary.filter(s => s.has_differences).length;
  const errorTables = summary.filter(s => s.status === 'error').length;

  return (
    <div style={{ marginTop: 24 }}>
      {/* Summary Header */}
      <div style={{
        padding: 16,
        background: '#e6f4ff',
        borderRadius: 8,
        border: '1px solid #bae0ff',
        marginBottom: 16,
      }}>
        <Title level={4} style={{ margin: '0 0 12px 0' }}>
          <ThunderboltOutlined /> Multi-Table Comparison Summary
        </Title>
        <Space size="large">
          <div>
            <Text strong>Total Tables:</Text> <Text>{totalTables}</Text>
          </div>
          <div>
            <Text strong>With Differences:</Text> <Text type="danger">{tablesWithDiffs}</Text>
          </div>
          <div>
            <Text strong>Errors:</Text> <Text type="danger">{errorTables}</Text>
          </div>
        </Space>
      </div>

      {/* Results Table */}
      <Table
        columns={columns}
        dataSource={summary}
        rowKey="source_table"
        pagination={{ pageSize: 10 }}
        size="middle"
      />

      {/* Detail Modal */}
      <Modal
        title={`Details: ${selectedTable}`}
        open={!!selectedTable}
        onCancel={() => setSelectedTable(null)}
        footer={null}
        width={1200}
      >
        {selectedTable && table_results[selectedTable] && (
          <SchemaDiffViewer
            diffResult={table_results[selectedTable]}
            sourceDbName={selectedTable}
            targetDbName={table_results[selectedTable].target_table}
          />
        )}
      </Modal>
    </div>
  );
};

// ============ Database Compare Viewer ============

interface DatabaseDiffViewerProps {
  result: DatabaseCompareResponse | null;
  onTableClick?: (tableName: string) => void;
}

export const DatabaseDiffViewer: React.FC<DatabaseDiffViewerProps> = ({
  result,
  onTableClick,
}) => {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedTableDetail, setSelectedTableDetail] = useState<SchemaDiffResponse | null>(null);

  if (!result) {
    return (
      <Empty
        description="No database comparison results yet"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  const {
    source_database,
    target_database,
    source_connection_name,
    target_connection_name,
    total_tables,
    compared_tables,
    tables_with_diffs,
    table_summaries,
    excluded_tables,
    unmatched_source_tables,
    unmatched_target_tables,
  } = result;

  const columns = [
    {
      title: 'Table Name',
      dataIndex: 'source_table',
      key: 'source_table',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: 'success' | 'error') => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Has Differences',
      dataIndex: 'has_differences',
      key: 'has_differences',
      render: (hasDiffs: boolean) => (
        <Tag color={hasDiffs ? 'orange' : 'green'}>
          {hasDiffs ? <DiffOutlined /> : <CheckCircleOutlined />}
          {hasDiffs ? 'YES' : 'NO'}
        </Tag>
      ),
    },
    {
      title: 'Diff Count',
      dataIndex: 'diff_count',
      key: 'diff_count',
      render: (count: number, record: TableCompareSummary) => (
        <Text type={count > 0 ? 'danger' : 'secondary'}>{count}</Text>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: unknown, record: TableCompareSummary) => (
        <Button
          type="link"
          size="small"
          disabled={record.status !== 'success' || !record.has_differences}
          onClick={() => handleViewDetails(record.source_table)}
        >
          View Details
        </Button>
      ),
    },
  ];

  // Handle view details - fetch detailed schema comparison
  const handleViewDetails = async (tableName: string) => {
    setSelectedTable(tableName);
    setLoadingDetail(true);
    setSelectedTableDetail(null);

    try {
      // Fetch detailed schema comparison from API
      const response = await fetch('/api/compare/schema', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_connection_id: result.source_connection_id,
          source_table: tableName,
          target_connection_id: result.target_connection_id,
          target_table: tableName,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedTableDetail(data);
      }
    } catch (error) {
      console.error('Failed to fetch schema details:', error);
    } finally {
      setLoadingDetail(false);
    }
  };

  return (
    <div style={{ marginTop: 24 }}>
      {/* Summary Header */}
      <div style={{
        padding: 16,
        background: '#e6f4ff',
        borderRadius: 8,
        border: '1px solid #bae0ff',
        marginBottom: 16,
      }}>
        <Title level={4} style={{ margin: '0 0 12px 0' }}>
          <DatabaseOutlined /> Database Comparison Summary
        </Title>
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          <div>
            <Text strong>Source:</Text> <Text>{source_connection_name}</Text> ({source_database})
            <span style={{ margin: '0 16px' }}>→</span>
            <Text strong>Target:</Text> <Text>{target_connection_name}</Text> ({target_database})
          </div>
          <Space size="large">
            <div>
              <Text strong>Total Matched Tables:</Text> <Text>{total_tables}</Text>
            </div>
            <div>
              <Text strong>Compared:</Text> <Text>{compared_tables}</Text>
            </div>
            <div>
              <Text strong>With Differences:</Text> <Text type="danger">{tables_with_diffs}</Text>
            </div>
          </Space>
        </Space>
      </div>

      {/* Unmatched Tables Warning */}
      {(unmatched_source_tables.length > 0 || unmatched_target_tables.length > 0) && (
        <div style={{
          padding: 12,
          background: '#fff7e6',
          borderRadius: 6,
          border: '1px solid #ffd591',
          marginBottom: 16,
        }}>
          <Text strong type="warning">⚠️ Unmatched Tables </Text>
          {unmatched_source_tables.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Only in source ({unmatched_source_tables.length}): </Text>
              <Text code>{unmatched_source_tables.slice(0, 10).join(', ')}</Text>
              {unmatched_source_tables.length > 10 && <Text type="secondary">...</Text>}
            </div>
          )}
          {unmatched_target_tables.length > 0 && (
            <div style={{ marginTop: 4 }}>
              <Text type="secondary">Only in target ({unmatched_target_tables.length}): </Text>
              <Text code>{unmatched_target_tables.slice(0, 10).join(', ')}</Text>
              {unmatched_target_tables.length > 10 && <Text type="secondary">...</Text>}
            </div>
          )}
        </div>
      )}

      {/* Excluded Tables */}
      {excluded_tables.length > 0 && (
        <Collapse style={{ marginBottom: 16 }}>
          <Panel header={`Excluded Tables (${excluded_tables.length})`} key="excluded">
            <Space wrap>
              {excluded_tables.map((table) => (
                <Tag key={table} color="default">{table}</Tag>
              ))}
            </Space>
          </Panel>
        </Collapse>
      )}

      {/* Results Table */}
      <Table
        columns={columns}
        dataSource={table_summaries}
        rowKey="source_table"
        pagination={{ pageSize: 10 }}
        size="middle"
        scroll={{ x: 800 }}
      />

      {/* Detail Modal */}
      <Modal
        title={`Details: ${selectedTable}`}
        open={!!selectedTable}
        onCancel={() => setSelectedTable(null)}
        footer={null}
        width={1200}
      >
        {loadingDetail ? (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <Spin size="large" tip="Loading schema details..." />
          </div>
        ) : selectedTableDetail ? (
          <SchemaDiffViewer
            diffResult={selectedTableDetail}
            sourceDbName={selectedTable ?? ''}
            targetDbName={selectedTable ?? ''}
          />
        ) : selectedTable ? (
          <Empty description="Failed to load schema details" />
        ) : null}
      </Modal>
    </div>
  );
};
