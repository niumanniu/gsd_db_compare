import { useComparison } from '../hooks/useComparison';
import type { SchemaDiffResponse } from '../types';
import { Collapse, Table, Typography, Tag, Empty } from 'antd';
import {
  DiffOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';

const { Panel } = Collapse;
const { Text, Paragraph } = Typography;

interface SchemaDiffViewerProps {
  diffResult: SchemaDiffResponse | null;
  sourceDbName?: string;
  targetDbName?: string;
  sourceDbType?: string;
  targetDbType?: string;
}

interface DiffTableRecord {
  key: string;
  name: string;
  diffType: string;
  source: string;
  target: string;
  differences: string[];
}

const getDiffTypeTag = (diffType: string) => {
  const colorMap: Record<string, string> = {
    added: 'green',
    removed: 'red',
    modified: 'gold',
  };

  const iconMap: Record<string, React.ReactNode> = {
    added: <CheckCircleOutlined />,
    removed: <CloseCircleOutlined />,
    modified: <DiffOutlined />,
  };

  return (
    <Tag color={colorMap[diffType] || 'default'}>
      {iconMap[diffType]} {diffType.toUpperCase()}
    </Tag>
  );
};

const buildColumnTableData = (columnDiff: SchemaDiffResponse['column_diffs']): DiffTableRecord[] => {
  return columnDiff.map((diff, index) => ({
    key: `col-${index}`,
    name: diff.column_name,
    diffType: diff.diff_type,
    source: diff.source_definition
      ? `${diff.source_definition.type}${diff.source_definition.nullable ? ' | NULL' : ' | NOT NULL'}`
      : 'N/A',
    target: diff.target_definition
      ? `${diff.target_definition.type}${diff.target_definition.nullable ? ' | NULL' : ' | NOT NULL'}`
      : 'N/A',
    differences: diff.differences,
  }));
};

const buildIndexTableData = (indexDiff: SchemaDiffResponse['index_diffs']): DiffTableRecord[] => {
  return indexDiff.map((diff, index) => ({
    key: `idx-${index}`,
    name: diff.index_name,
    diffType: diff.diff_type,
    source: diff.source_definition
      ? `Cols: ${Array.isArray(diff.source_definition.columns) ? diff.source_definition.columns.join(', ') : 'N/A'}`
      : 'N/A',
    target: diff.target_definition
      ? `Cols: ${Array.isArray(diff.target_definition.columns) ? diff.target_definition.columns.join(', ') : 'N/A'}`
      : 'N/A',
    differences: diff.differences,
  }));
};

const buildConstraintTableData = (constraintDiff: SchemaDiffResponse['constraint_diffs']): DiffTableRecord[] => {
  return constraintDiff.map((diff, index) => ({
    key: `con-${index}`,
    name: diff.constraint_name,
    diffType: diff.diff_type,
    source: diff.source_definition
      ? `${diff.constraint_type} (${Array.isArray(diff.source_definition.columns) ? diff.source_definition.columns.join(', ') : 'N/A'})`
      : 'N/A',
    target: diff.target_definition
      ? `${diff.constraint_type} (${Array.isArray(diff.target_definition.columns) ? diff.target_definition.columns.join(', ') : 'N/A'})`
      : 'N/A',
    differences: diff.differences,
  }));
};

const columnTableColumns = [
  { title: 'Column', dataIndex: 'name', key: 'name', render: (text: string) => <Text strong>{text}</Text> },
  {
    title: 'Diff Type',
    dataIndex: 'diffType',
    key: 'diffType',
    render: getDiffTypeTag,
  },
  { title: 'Source', dataIndex: 'source', key: 'source' },
  { title: 'Target', dataIndex: 'target', key: 'target' },
  {
    title: 'Differences',
    dataIndex: 'differences',
    key: 'differences',
    render: (diffs: string[]) => (
      <ul style={{ margin: 0, paddingLeft: 16 }}>
        {diffs.map((d, i) => <li key={i}>{d}</li>)}
      </ul>
    ),
  },
];

export const SchemaDiffViewer: React.FC<SchemaDiffViewerProps> = ({
  diffResult,
  sourceDbName,
  targetDbName,
  sourceDbType,
  targetDbType,
}) => {
  if (!diffResult) {
    return (
      <Empty
        description="No comparison results yet"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  const columnData = buildColumnTableData(diffResult.column_diffs);
  const indexData = buildIndexTableData(diffResult.index_diffs);
  const constraintData = buildConstraintTableData(diffResult.constraint_diffs);

  const summaryItems = [
    { label: 'Column Differences', count: diffResult.column_diffs.length },
    { label: 'Index Differences', count: diffResult.index_diffs.length },
    { label: 'Constraint Differences', count: diffResult.constraint_diffs.length },
  ];

  const comparisonModeLabel = diffResult.comparison_mode === 'same-database'
    ? 'Same Database Type'
    : 'Cross Database Comparison';

  return (
    <div style={{ marginTop: 24 }}>
      {/* Database Info Header */}
      <div style={{ marginBottom: 16, padding: 12, background: '#e6f7ff', borderRadius: 8, border: '1px solid #91d5ff' }}>
        <Text strong>Comparison: </Text>
        <Tag color="blue">{sourceDbType?.toUpperCase() || 'MySQL'}</Tag>
        <Text type="secondary"> {sourceDbName || 'Unknown'} </Text>
        <ArrowRightOutlined style={{ margin: '0 8px' }} />
        <Tag color="blue">{targetDbType?.toUpperCase() || 'MySQL'}</Tag>
        <Text type="secondary"> {targetDbName || 'Unknown'} </Text>
        <div style={{ marginTop: 8 }}>
          <Tag color={diffResult.comparison_mode === 'same-database' ? 'green' : 'orange'}>
            {comparisonModeLabel}
          </Tag>
        </div>
      </div>

      <Typography.Title level={4}>Comparison Results</Typography.Title>

      {/* Summary Cards */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        {summaryItems.map((item) => (
          <div
            key={item.label}
            style={{
              padding: '16px 24px',
              backgroundColor: item.count > 0 ? '#fff7e6' : '#f6ffed',
              border: '1px solid',
              borderColor: item.count > 0 ? '#ffd591' : '#b7eb8f',
              borderRadius: 8,
              minWidth: 150,
            }}
          >
            <div style={{ fontSize: 24, fontWeight: 'bold', color: item.count > 0 ? '#fa8c16' : '#52c41a' }}>
              {item.count}
            </div>
            <div style={{ color: '#666' }}>{item.label}</div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div style={{ marginBottom: 16 }}>
        <Text strong>Legend: </Text>
        <Tag color="green"><CheckCircleOutlined /> ADDED</Tag>
        <Tag color="red"><CloseCircleOutlined /> REMOVED</Tag>
        <Tag color="gold"><DiffOutlined /> MODIFIED</Tag>
      </div>

      {/* Expandable Sections */}
      <Collapse defaultActiveKey={['1', '2', '3']} accordion={false}>
        <Panel
          header={
            <span>
              <DiffOutlined /> Columns ({diffResult.column_diffs.length} differences)
            </span>
          }
          key="1"
        >
          {columnData.length > 0 ? (
            <Table
              columns={columnTableColumns}
              dataSource={columnData}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          ) : (
            <Paragraph type="secondary">No column differences found.</Paragraph>
          )}
        </Panel>

        <Panel
          header={
            <span>
              <DiffOutlined /> Indexes ({diffResult.index_diffs.length} differences)
            </span>
          }
          key="2"
        >
          {indexData.length > 0 ? (
            <Table
              columns={columnTableColumns}
              dataSource={indexData}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          ) : (
            <Paragraph type="secondary">No index differences found.</Paragraph>
          )}
        </Panel>

        <Panel
          header={
            <span>
              <DiffOutlined /> Constraints ({diffResult.constraint_diffs.length} differences)
            </span>
          }
          key="3"
        >
          {constraintData.length > 0 ? (
            <Table
              columns={columnTableColumns}
              dataSource={constraintData}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          ) : (
            <Paragraph type="secondary">No constraint differences found.</Paragraph>
          )}
        </Panel>
      </Collapse>

      {/* Overall Status */}
      <div style={{ marginTop: 24, padding: 16, backgroundColor: diffResult.has_differences ? '#fff7e6' : '#f6ffed', borderRadius: 8 }}>
        <Paragraph style={{ margin: 0 }}>
          <Text strong>
            {diffResult.has_differences ? '⚠️ Differences Found' : '✅ Schemas Match'}
          </Text>
          {!diffResult.has_differences && ' - The two tables have identical schemas.'}
        </Paragraph>
      </div>
    </div>
  );
};
