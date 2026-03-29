import { Table, Tag, Typography, Space, Button, Alert } from 'antd';
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

  // Expanded row renderer - shows field-level diffs with full row data
  const expandedRowRender = (row: RowDiff) => {
    // Show full row data for missing rows
    if (row.diff_type === 'missing_in_target' && row.source_row) {
      const sourceDataColumns = [
        {
          title: 'Field Name',
          dataIndex: 'field',
          key: 'field',
          width: '30%',
          render: (text: string) => <Text strong>{text}</Text>,
        },
        {
          title: 'Source Value (Missing in Target)',
          dataIndex: 'value',
          key: 'value',
          width: '70%',
          render: (value: unknown) => (
            <div
              style={{
                backgroundColor: '#fff2f0',
                border: '1px solid #ffccc7',
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
      const sourceDataSource = Object.entries(row.source_row).map(([field, value], idx) => ({
        field,
        value,
        key: idx,
      }));
      return (
        <div>
          <Alert
            message="This row exists in Source but is missing in Target"
            type="warning"
            showIcon
            style={{ marginBottom: 12 }}
          />
          <Table
            columns={sourceDataColumns}
            dataSource={sourceDataSource}
            pagination={false}
            size="small"
          />
        </div>
      );
    }

    if (row.diff_type === 'missing_in_source' && row.target_row) {
      const targetDataColumns = [
        {
          title: 'Field Name',
          dataIndex: 'field',
          key: 'field',
          width: '30%',
          render: (text: string) => <Text strong>{text}</Text>,
        },
        {
          title: 'Target Value (Missing in Source)',
          dataIndex: 'value',
          key: 'value',
          width: '70%',
          render: (value: unknown) => (
            <div
              style={{
                backgroundColor: '#f6ffed',
                border: '1px solid #b7eb8f',
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
      const targetDataSource = Object.entries(row.target_row).map(([field, value], idx) => ({
        field,
        value,
        key: idx,
      }));
      return (
        <div>
          <Alert
            message="This row exists in Target but is missing in Source"
            type="warning"
            showIcon
            style={{ marginBottom: 12 }}
          />
          <Table
            columns={targetDataColumns}
            dataSource={targetDataSource}
            pagination={false}
            size="small"
          />
        </div>
      );
    }

    // Content diff - show field-level comparison
    if (!row.field_diffs || row.field_diffs.length === 0) {
      // No field-level differences but row is marked as content_diff
      // This can happen when rows have the same primary key but all fields match
      return (
        <div>
          <Alert
            message="Row marked as content difference but no specific field differences found"
            type="warning"
            showIcon
          />
        </div>
      );
    }

    const fieldDiffColumns = [
      {
        title: 'Field Name',
        dataIndex: 'field_name',
        key: 'field_name',
        width: '15%',
        render: (text: string) => <Text strong>{text}</Text>,
      },
      {
        title: 'Source Value',
        dataIndex: 'source_value',
        key: 'source_value',
        width: '35%',
        render: (value: unknown, record: FieldDiff) => (
          <div
            style={{
              backgroundColor: '#fff2f0',
              border: '1px solid #ffccc7',
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
        width: '35%',
        render: (value: unknown, record: FieldDiff) => (
          <div
            style={{
              backgroundColor: '#f6ffed',
              border: '1px solid #b7eb8f',
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
        title: 'Difference Type',
        dataIndex: 'diff_type',
        key: 'diff_type',
        width: '15%',
        render: (diffType: FieldDiff['diff_type']) => {
          const config: Record<FieldDiff['diff_type'], { color: string; label: string }> = {
            value: { color: 'orange', label: 'Value' },
            null: { color: 'gold', label: 'Null Check' },
            type: { color: 'red', label: 'Type' },
            length: { color: 'blue', label: 'Length' },
          };
          const { color, label } = config[diffType];
          return <Tag color={color}>{label}</Tag>;
        },
      },
    ];

    return (
      <div>
        <Alert
          message={`${row.field_diffs.length} field(s) have different values`}
          description="Compare the specific field values below"
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
        />
        <Table
          columns={fieldDiffColumns}
          dataSource={row.field_diffs.map((fd, idx) => ({ ...fd, key: idx }))}
          pagination={false}
          size="small"
        />
      </div>
    );
  };

  // Main table columns
  const tableColumns = [
    {
      title: 'Primary Key Value',
      dataIndex: 'primary_key_value',
      key: 'primary_key_value',
      width: '20%',
      render: (value: unknown) => (
        <Text strong style={{ fontSize: 14 }}>{value === null ? 'NULL' : String(value)}</Text>
      ),
      sorter: (a: RowDiff, b: RowDiff) => {
        const aKey = String(a.primary_key_value || '');
        const bKey = String(b.primary_key_value || '');
        return aKey.localeCompare(bKey);
      },
    },
    {
      title: 'Difference Type',
      dataIndex: 'diff_type',
      key: 'diff_type',
      width: '25%',
      render: (diffType: RowDiff['diff_type']) => getDiffTypeTag(diffType),
      filters: [
        { text: 'Missing in Target', value: 'missing_in_target' },
        { text: 'Missing in Source', value: 'missing_in_source' },
        { text: 'Content Differs', value: 'content_diff' },
      ],
      onFilter: (value: unknown, record: RowDiff) => record.diff_type === value,
    },
    {
      title: 'Fields Different',
      dataIndex: 'field_diffs',
      key: 'field_diffs',
      width: '15%',
      render: (fieldDiff: FieldDiff[]) => {
        if (fieldDiff.length === 0) {
          return <Text type="secondary">-</Text>;
        }
        return (
          <Tag color="orange" style={{ fontSize: 12 }}>
            {fieldDiff.length} field{fieldDiff.length !== 1 ? 's' : ''}
          </Tag>
        );
      },
    },
    {
      title: 'Details',
      key: 'details',
      width: '40%',
      render: (_: unknown, record: RowDiff) => {
        if (record.diff_type === 'missing_in_target') {
          return (
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text><WarningOutlined style={{ color: '#ff4d4f' }} /> Row exists in <Text strong>Source</Text> but <Text strong type="danger">NOT in Target</Text></Text>
              <Text type="secondary" style={{ fontSize: 12 }}>Click "Show Details" to view the complete row data</Text>
            </Space>
          );
        }
        if (record.diff_type === 'missing_in_source') {
          return (
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text><CheckCircleOutlined style={{ color: '#52c41a' }} /> Row exists in <Text strong>Target</Text> but <Text strong type="danger">NOT in Source</Text></Text>
              <Text type="secondary" style={{ fontSize: 12 }}>Click "Show Details" to view the complete row data</Text>
            </Space>
          );
        }
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text><DiffOutlined style={{ color: '#faad14' }} /> Row exists in both databases but <Text strong type="warning">{record.field_diffs.length} field(s) differ</Text></Text>
            <Text type="secondary" style={{ fontSize: 12 }}>Click "Show Details" to compare field values side-by-side</Text>
          </Space>
        );
      },
    },
  ];

  // Prepare data source
  const dataSource = diffs.map((diff, index) => ({
    ...diff,
    key: `${index}-${diff.primary_key_value}`,
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
