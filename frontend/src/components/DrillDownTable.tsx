import { Table, Tag, Typography, Space, Button } from 'antd';
import type { RowDiff, FieldDiff } from '../types/data_compare';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DiffOutlined,
  WarningOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface DrillDownTableProps {
  diffs: RowDiff[];
  hasMore: boolean;
  onLoadMore?: () => void;
}

/**
 * DrillDownTable displays row-level differences with expandable details.
 * Shows primary key, diff type badge, and expandable field-level diffs.
 */
export const DrillDownTable: React.FC<DrillDownTableProps> = ({
  diffs,
  hasMore,
  onLoadMore,
}) => {
  // Get diff type badge
  const getDiffTypeTag = (diffType: RowDiff['diff_type']) => {
    const config: Record<RowDiff['diff_type'], { color: string; icon: React.ReactNode; label: string }> = {
      missing_in_target: {
        color: 'red',
        icon: <CloseCircleOutlined />,
        label: 'MISSING IN TARGET',
      },
      missing_in_source: {
        color: 'green',
        icon: <CheckCircleOutlined />,
        label: 'MISSING IN SOURCE',
      },
      content_diff: {
        color: 'gold',
        icon: <DiffOutlined />,
        label: 'MODIFIED',
      },
    };

    const { color, icon, label } = config[diffType];
    return <Tag color={color}>{icon} {label}</Tag>;
  };

  // Expanded row renderer - shows field-level diffs
  const expandedRowRender = (row: RowDiff) => {
    if (!row.field_diffs || row.field_diffs.length === 0) {
      return <Text type="secondary">No field-level differences</Text>;
    }

    const fieldDiffColumns = [
      {
        title: 'Field',
        dataIndex: 'field_name',
        key: 'field_name',
        width: '20%',
        render: (text: string) => <Text strong>{text}</Text>,
      },
      {
        title: 'Source Value',
        dataIndex: 'source_value',
        key: 'source_value',
        width: '40%',
        render: (value: unknown, record: FieldDiff) => (
          <div
            style={{
              backgroundColor: record.diff_type === 'null' ? '#fff1b8' : '#fff2f0',
              padding: '8px',
              borderRadius: 4,
              fontFamily: 'monospace',
              fontSize: 12,
            }}
          >
            {value === null ? <Text type="secondary">NULL</Text> : String(value)}
          </div>
        ),
      },
      {
        title: 'Target Value',
        dataIndex: 'target_value',
        key: 'target_value',
        width: '40%',
        render: (value: unknown, record: FieldDiff) => (
          <div
            style={{
              backgroundColor: record.diff_type === 'null' ? '#fff1b8' : '#f6ffed',
              padding: '8px',
              borderRadius: 4,
              fontFamily: 'monospace',
              fontSize: 12,
            }}
          >
            {value === null ? <Text type="secondary">NULL</Text> : String(value)}
          </div>
        ),
      },
    ];

    return (
      <Table
        columns={fieldDiffColumns}
        dataSource={row.field_diffs.map((fd, idx) => ({ ...fd, key: idx }))}
        pagination={false}
        size="small"
        showHeader={true}
      />
    );
  };

  // Main table columns
  const tableColumns = [
    {
      title: 'Primary Key',
      dataIndex: 'primary_key',
      key: 'primary_key',
      width: '25%',
      render: (value: unknown) => (
        <Text strong>{value === null ? 'NULL' : String(value)}</Text>
      ),
      sorter: (a: RowDiff, b: RowDiff) => {
        const aKey = String(a.primary_key || '');
        const bKey = String(b.primary_key || '');
        return aKey.localeCompare(bKey);
      },
    },
    {
      title: 'Diff Type',
      dataIndex: 'diff_type',
      key: 'diff_type',
      width: '25%',
      render: (diffType: RowDiff['diff_type']) => getDiffTypeTag(diffType),
      filters: [
        { text: 'Missing in Target', value: 'missing_in_target' },
        { text: 'Missing in Source', value: 'missing_in_source' },
        { text: 'Modified', value: 'content_diff' },
      ],
      onFilter: (value: unknown, record: RowDiff) => record.diff_type === value,
    },
    {
      title: 'Field Differences',
      dataIndex: 'field_diffs',
      key: 'field_diffs',
      width: '20%',
      render: (fieldDiff: FieldDiff[]) => (
        <Tag color={fieldDiff.length > 0 ? 'orange' : 'default'}>
          {fieldDiff.length} field{fieldDiff.length !== 1 ? 's' : ''}
        </Tag>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: '30%',
      render: (_: unknown, record: RowDiff) => {
        if (record.diff_type === 'missing_in_target') {
          return (
            <Space>
              <WarningOutlined style={{ color: '#ff4d4f' }} />
              <Text type="danger">Row exists only in source</Text>
            </Space>
          );
        }
        if (record.diff_type === 'missing_in_source') {
          return (
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <Text type="success">Row exists only in target</Text>
            </Space>
          );
        }
        return (
          <Space>
            <DiffOutlined style={{ color: '#faad14' }} />
            <Text>Content differs</Text>
          </Space>
        );
      },
    },
  ];

  // Prepare data source
  const dataSource = diffs.map((diff, index) => ({
    ...diff,
    key: `${index}-${diff.primary_key}`,
  }));

  return (
    <div>
      <Table
        columns={tableColumns}
        dataSource={dataSource}
        expandable={{
          expandedRowRender,
          expandIcon: ({ expanded, onExpand, record }) => (
            <Button
              type="text"
              size="small"
              onClick={e => onExpand(record, e)}
              style={{ fontSize: 12 }}
            >
              {expanded ? 'Hide Details' : 'Show Details'}
            </Button>
          ),
        }}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} differences`,
        }}
        size="middle"
      />

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button type="primary" onClick={onLoadMore}>
            Load More Differences
          </Button>
          <Text type="secondary" style={{ marginLeft: 8 }}>
            (More differences available)
          </Text>
        </div>
      )}
    </div>
  );
};
