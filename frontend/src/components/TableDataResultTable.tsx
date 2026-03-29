import React from 'react';
import { Table, Tag, Typography, Card, Statistic, Row, Col, Space, Button } from 'antd';
import type { ColumnType } from 'antd/es/table';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  SyncOutlined,
  EyeOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

interface TableResult {
  source_table: string;
  target_table: string;
  status: string;
  source_row_count: number;
  target_row_count: number;
  diff_count: number;
  diff_percentage: number | null;
  mode_used: string;
  is_identical: boolean;
  error_message?: string;
}

interface Summary {
  total_tables: number;
  compared_tables: number;
  identical_tables: number;
  tables_with_diffs: number;
  error_tables: number;
  total_rows_compared: number;
  total_diffs_found: number;
  elapsed_time_seconds: number;
}

interface TableDataResultTableProps {
  summary: Summary;
  tableResults: TableResult[];
  onViewDetails?: (tableResult: TableResult) => void;
}

/**
 * TableDataResultTable - Displays multi-table comparison results
 */
export const TableDataResultTable: React.FC<TableDataResultTableProps> = ({
  summary,
  tableResults,
  onViewDetails,
}) => {
  const getStatusTag = (status: string, isIdentical?: boolean, errorMessage?: string) => {
    if (status === 'error') {
      return (
        <Tag icon={<CloseCircleOutlined />} color="error">
          ERROR
        </Tag>
      );
    }
    if (isIdentical) {
      return (
        <Tag icon={<CheckCircleOutlined />} color="success">
          IDENTICAL
        </Tag>
      );
    }
    return (
      <Tag icon={<WarningOutlined />} color="warning">
        DIFFERS
      </Tag>
    );
  };

  const columns: ColumnType<TableResult>[] = [
    {
      title: 'Source Table',
      dataIndex: 'source_table',
      key: 'source_table',
      width: 200,
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Target Table',
      dataIndex: 'target_table',
      key: 'target_table',
      width: 200,
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (_: any, record: TableResult) => getStatusTag(record.status, record.is_identical, record.error_message),
    },
    {
      title: 'Source Rows',
      dataIndex: 'source_row_count',
      key: 'source_row_count',
      width: 100,
      align: 'right',
      render: (count: number) => count.toLocaleString(),
    },
    {
      title: 'Target Rows',
      dataIndex: 'target_row_count',
      key: 'target_row_count',
      width: 100,
      align: 'right',
      render: (count: number) => count.toLocaleString(),
    },
    {
      title: 'Diff Count',
      dataIndex: 'diff_count',
      key: 'diff_count',
      width: 100,
      align: 'right',
      render: (count: number, record: TableResult) => (
        <Text type={count > 0 ? 'danger' : 'secondary'}>
          {count > 0 ? count.toLocaleString() : '-'}
        </Text>
      ),
    },
    {
      title: 'Diff %',
      dataIndex: 'diff_percentage',
      key: 'diff_percentage',
      width: 80,
      align: 'right',
      render: (pct: number | null, record: TableResult) => {
        if (record.status === 'error' || pct === null) return '-';
        return `${pct.toFixed(2)}%`;
      },
    },
    {
      title: 'Mode',
      dataIndex: 'mode_used',
      key: 'mode_used',
      width: 80,
      render: (mode: string) => <Text type="secondary">{mode}</Text>,
    },
    {
      title: 'Error',
      key: 'error_message',
      width: 200,
      render: (_: any, record: TableResult) => (
        record.error_message ? (
          <Text type="danger" ellipsis={{ tooltip: record.error_message }}>
            {record.error_message}
          </Text>
        ) : (
          '-'
        )
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 80,
      render: (_: any, record: TableResult) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => onViewDetails?.(record)}
          disabled={record.status === 'error'}
        >
          Details
        </Button>
      ),
    },
  ];

  return (
    <div>
      {/* Summary Cards */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={5} style={{ marginTop: 0, marginBottom: 16 }}>
          Comparison Summary
        </Title>
        <Row gutter={16}>
          <Col span={4}>
            <Statistic
              title="Total Tables"
              value={summary.total_tables}
              prefix={<SyncOutlined spin={false} />}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Compared"
              value={summary.compared_tables}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Identical"
              value={summary.identical_tables}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="With Diffs"
              value={summary.tables_with_diffs}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Errors"
              value={summary.error_tables}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Time (sec)"
              value={summary.elapsed_time_seconds}
              precision={1}
            />
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Statistic
              title="Total Rows Compared"
              value={summary.total_rows_compared}
              formatter={(v) => v?.toLocaleString()}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="Total Diffs Found"
              value={summary.total_diffs_found}
              valueStyle={{ color: summary.total_diffs_found > 0 ? '#ff4d4f' : '#52c41a' }}
              formatter={(v) => v?.toLocaleString()}
            />
          </Col>
        </Row>
      </Card>

      {/* Results Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={tableResults}
          rowKey={(record) => `${record.source_table}-${record.target_table}`}
          pagination={{ pageSize: 20 }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>
    </div>
  );
};
