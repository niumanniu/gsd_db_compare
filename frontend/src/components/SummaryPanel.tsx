import { Card, Statistic, Row, Col, Tag, Typography } from 'antd';
import { ArrowRightOutlined } from '@ant-design/icons';
import type { DataSummary } from '../types/data_compare';

const { Text } = Typography;

interface SummaryPanelProps {
  summary: DataSummary;
  sourceTable: string;
  targetTable: string;
  sourceDbType?: string;
  targetDbType?: string;
}

/**
 * Get color for diff percentage based on severity
 */
const getDiffPercentageColor = (percentage: number | null): string => {
  if (percentage === null || percentage === 0) return '#52c41a'; // Green
  if (percentage < 1) return '#faad14'; // Yellow
  if (percentage < 5) return '#fa8c16'; // Orange
  return '#ff4d4f'; // Red
};

/**
 * Get color for diff count based on severity
 */
const getDiffCountColor = (count: number): string => {
  if (count === 0) return '#52c41a'; // Green
  if (count < 100) return '#faad14'; // Yellow
  if (count < 1000) return '#fa8c16'; // Orange
  return '#ff4d4f'; // Red
};

/**
 * Format diff percentage for display
 */
const formatPercentage = (percentage: number | null): string => {
  if (percentage === null) return 'N/A';
  return `${percentage.toFixed(2)}%`;
};

/**
 * SummaryPanel displays data comparison statistics
 * Shows row counts, diff counts, and percentage with color coding
 */
export const SummaryPanel: React.FC<SummaryPanelProps> = ({
  summary,
  sourceTable,
  targetTable,
  sourceDbType,
  targetDbType,
}) => {
  const {
    source_row_count,
    target_row_count,
    diff_count,
    diff_percentage,
    mode_used,
    source_hash,
    target_hash,
    sampled_row_count,
  } = summary;

  const diffPercentageColor = getDiffPercentageColor(diff_percentage);
  const diffCountColor = getDiffCountColor(diff_count);

  return (
    <Card style={{ marginBottom: 24 }}>
      {/* Header with table names */}
      <div style={{ marginBottom: 16 }}>
        <Text strong style={{ fontSize: 16 }}>
          Data Comparison: {sourceTable} <ArrowRightOutlined style={{ margin: '0 8px', color: '#666' }} /> {targetTable}
        </Text>
        {sourceDbType && targetDbType && (
          <div style={{ marginTop: 8 }}>
            <Tag color="blue">{sourceDbType.toUpperCase()}</Tag>
            <ArrowRightOutlined style={{ margin: '0 8px', color: '#666' }} />
            <Tag color="blue">{targetDbType.toUpperCase()}</Tag>
          </div>
        )}
        <Tag
          color={mode_used.includes('hash') ? 'purple' : 'cyan'}
          style={{ marginLeft: 8 }}
        >
          Mode: {mode_used}
        </Tag>
      </div>

      {/* Statistics Grid */}
      <Row gutter={16}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Source Row Count"
              value={source_row_count}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Target Row Count"
              value={target_row_count}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Difference Count"
              value={diff_count}
              valueStyle={{ color: diffCountColor }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Diff Percentage"
              value={formatPercentage(diff_percentage)}
              valueStyle={{ color: diffPercentageColor }}
              suffix={diff_percentage !== null && diff_percentage > 0 ? '%' : ''}
            />
          </Card>
        </Col>
      </Row>

      {/* Additional info based on mode */}
      {(source_hash || sampled_row_count) && (
        <div style={{ marginTop: 16, padding: '8px 12px', backgroundColor: '#f5f5f5', borderRadius: 4 }}>
          {source_hash && target_hash && (
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary">Hash Values: </Text>
              <code style={{ fontSize: 11, color: '#666' }}>
                Source: {source_hash?.substring(0, 16)}... | Target: {target_hash?.substring(0, 16)}...
              </code>
              {source_hash === target_hash && (
                <Tag color="green" style={{ marginLeft: 8 }}>Hashes Match</Tag>
              )}
            </div>
          )}
          {sampled_row_count !== undefined && (
            <div>
              <Text type="secondary">Sampled Rows: </Text>
              <Text strong>{sampled_row_count.toLocaleString()}</Text>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
