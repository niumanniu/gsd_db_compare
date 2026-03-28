import { useState } from 'react';
import { Button, Select, Radio, Space, Typography, Alert, Empty, Spin, Divider, Tag } from 'antd';
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useDataComparison } from '../hooks/useDataComparison';
import { SummaryPanel } from './SummaryPanel';
import { DrillDownTable } from './DrillDownTable';
import type { DataCompareRequest } from '../types/data_compare';

const { Title, Text } = Typography;
const { Option } = Select;

interface DataDiffViewerProps {
  sourceConnectionId: number;
  targetConnectionId: number;
  sourceTable: string;
  targetTable: string;
}

/**
 * DataDiffViewer is the main component for data comparison.
 * Integrates SummaryPanel and DrillDownTable with useDataComparison hook.
 */
export const DataDiffViewer: React.FC<DataDiffViewerProps> = ({
  sourceConnectionId,
  targetConnectionId,
  sourceTable,
  targetTable,
}) => {
  // State for comparison configuration
  const [mode, setMode] = useState<'auto' | 'full' | 'hash' | 'sample'>('auto');
  const [threshold, setThreshold] = useState<number>(100000);
  const [sampleSize, setSampleSize] = useState<number>(1000);
  const [hasCompared, setHasCompared] = useState(false);

  // Use data comparison hook
  const { compareData, isComparing, comparisonResult, error, errorMessage, errorStatus, resetComparison } = useDataComparison();

  // Handle compare button click
  const handleCompare = async () => {
    const requestData: DataCompareRequest = {
      source_connection_id: sourceConnectionId,
      target_connection_id: targetConnectionId,
      source_table: sourceTable,
      target_table: targetTable,
      mode,
      threshold,
      sample_size: sampleSize,
    };

    try {
      await compareData(requestData);
      setHasCompared(true);
    } catch (err) {
      // Error is handled by hook
      console.error('Comparison failed:', err);
    }
  };

  // Handle reset
  const handleReset = () => {
    resetComparison();
    setHasCompared(false);
  };

  // Render configuration section
  const renderConfiguration = () => (
    <div style={{ marginBottom: 24, padding: 16, backgroundColor: '#fafafa', borderRadius: 8 }}>
      <Title level={5}>Comparison Configuration</Title>
      
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Text strong>Comparison Mode: </Text>
          <Radio.Group value={mode} onChange={(e) => setMode(e.target.value)}>
            <Radio.Button value="auto">Auto</Radio.Button>
            <Radio.Button value="full">Full</Radio.Button>
            <Radio.Button value="hash">Hash</Radio.Button>
            <Radio.Button value="sample">Sample</Radio.Button>
          </Radio.Group>
        </div>

        <div>
          <Text strong>Threshold (rows): </Text>
          <Select
            value={threshold}
            onChange={(value) => setThreshold(value)}
            style={{ width: 150, marginLeft: 8 }}
            disabled={mode !== 'auto'}
          >
            <Option value={10000}>10,000</Option>
            <Option value={50000}>50,000</Option>
            <Option value={100000}>100,000</Option>
            <Option value={500000}>500,000</Option>
          </Select>
        </div>

        <div>
          <Text strong>Sample Size: </Text>
          <Select
            value={sampleSize}
            onChange={(value) => setSampleSize(value)}
            style={{ width: 150, marginLeft: 8 }}
          >
            <Option value={100}>100</Option>
            <Option value={500}>500</Option>
            <Option value={1000}>1,000</Option>
            <Option value={5000}>5,000</Option>
          </Select>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        <Space>
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            onClick={handleCompare}
            loading={isComparing}
          >
            {isComparing ? 'Comparing...' : 'Compare Data'}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleReset}
            disabled={!comparisonResult && !error}
          >
            Reset
          </Button>
        </Space>
      </Space>
    </div>
  );

  // Render loading state
  const renderLoading = () => (
    <div style={{ textAlign: 'center', padding: '48px 0' }}>
      <Spin size="large" tip="Comparing data..." />
      <div style={{ marginTop: 16, color: '#666' }}>
        This may take a while for large tables
      </div>
    </div>
  );

  // Render error state with enhanced error handling
  const renderError = () => {
    if (!error) return null;

    // Determine if error is recoverable (show retry button)
    const isRecoverable = errorStatus && [408, 503, 504, 502].includes(errorStatus);
    const isTimeout = errorStatus === 504;
    const isNotFound = errorStatus === 404;
    const isAuthError = errorStatus === 401;

    // Get detailed error description
    const errorDescription = (
      <div style={{ marginTop: 8 }}>
        <Text strong>Status Code: </Text>
        <Tag color={errorStatus && errorStatus >= 500 ? 'red' : 'orange'}>
          HTTP {errorStatus || 'UNKNOWN'}
        </Tag>
        {error.detail && (
          <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            Details: {error.detail}
          </div>
        )}
      </div>
    );

    // Get guidance based on error type
    const getGuidance = () => {
      if (isTimeout) {
        return 'Try using Hash mode to quickly check if tables differ, or Sample mode to find specific differences.';
      }
      if (isNotFound) {
        return 'Please verify the table name exists in the database.';
      }
      if (isAuthError) {
        return 'Please check the database credentials in Connection settings.';
      }
      if (errorStatus === 503) {
        return 'Please verify the database is running and connection settings are correct.';
      }
      if (errorStatus === 413) {
        return 'For very large tables, use Hash mode first to check if data differs.';
      }
      return 'You can retry the operation or check your configuration.';
    };

    return (
      <Alert
        message={errorMessage || 'Comparison Failed'}
        description={
          <div>
            {errorDescription}
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Guidance: </Text>
              {getGuidance()}
            </div>
          </div>
        }
        type="error"
        showIcon
        style={{ marginBottom: 24 }}
        action={
          isRecoverable ? (
            <Button size="small" onClick={handleCompare} icon={<ReloadOutlined />}>
              Retry
            </Button>
          ) : null
        }
      />
    );
  };

  // Render results
  const renderResults = () => {
    if (!comparisonResult) return null;

    const { summary, diffs } = comparisonResult;

    return (
      <div>
        {/* Summary Panel */}
        <SummaryPanel
          summary={summary}
          sourceTable={sourceTable}
          targetTable={targetTable}
        />

        {/* Drill Down Table */}
        {diffs && diffs.length > 0 ? (
          <div>
            <Title level={5}>Differences Detail</Title>
            <DrillDownTable
              diffs={diffs}
              hasMore={summary.has_more}
            />
          </div>
        ) : (
          <Empty
            description="No differences found - data is identical!"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </div>
    );
  };

  return (
    <div>
      <Title level={4}>Data Comparison</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        Compare data between {sourceTable} and {targetTable}
      </Text>

      {/* Configuration */}
      {!hasCompared && renderConfiguration()}

      {/* Loading State */}
      {isComparing && renderLoading()}

      {/* Error State */}
      {error && renderError()}

      {/* Results */}
      {comparisonResult && !isComparing && renderResults()}
    </div>
  );
};
