import React from 'react';
import { Progress, Card, Typography, Steps } from 'antd';
import {
  CheckCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

interface ComparisonProgressProps {
  current: number;
  total: number;
  status?: 'active' | 'exception' | 'success' | 'normal';
  tableStatuses?: Array<{
    tableName: string;
    status: 'pending' | 'running' | 'completed' | 'error';
  }>;
}

/**
 * ComparisonProgress - Displays progress of multi-table comparison
 */
export const ComparisonProgress: React.FC<ComparisonProgressProps> = ({
  current,
  total,
  status = 'active',
  tableStatuses,
}) => {
  const percentage = total > 0 ? (current / total) * 100 : 0;

  const getAntStatus = () => {
    if (status === 'success') return 'success';
    if (status === 'exception') return 'exception';
    return 'active';
  };

  return (
    <Card style={{ marginBottom: 16 }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0, marginBottom: 16 }}>
          <SyncOutlined spin={status === 'active'} /> Comparison Progress
        </Title>

        <Progress
          percent={percentage}
          status={getAntStatus()}
          format={(pct = 0) => `${pct.toFixed(0)}%`}
          strokeColor={{
            '0%': '#1890ff',
            '100%': '#52c41a',
          }}
        />

        <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
          <Text type="secondary">
            {current} / {total} tables completed
          </Text>
          {status === 'active' && (
            <Text type="secondary">Processing...</Text>
          )}
          {status === 'success' && (
            <Text type="success"><CheckCircleOutlined /> Completed</Text>
          )}
          {status === 'exception' && (
            <Text type="danger"><CloseCircleOutlined /> Failed</Text>
          )}
        </div>
      </div>

      {/* Per-table status (if provided) */}
      {tableStatuses && tableStatuses.length > 0 && (
        <div style={{ maxHeight: 200, overflow: 'auto' }}>
          <Steps
            current={-1}
            direction="vertical"
            size="small"
            items={tableStatuses.map((t) => ({
              title: t.tableName,
              status: t.status === 'completed' ? 'finish' : t.status === 'error' ? 'error' : t.status === 'running' ? 'process' : 'wait',
              description: t.status === 'running' ? 'Comparing...' : t.status === 'completed' ? 'Done' : t.status === 'error' ? 'Failed' : 'Pending',
            }))}
          />
        </div>
      )}
    </Card>
  );
};
