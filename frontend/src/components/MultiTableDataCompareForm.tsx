import React, { useState, useCallback } from 'react';
import { Form, Input, InputNumber, Select, Button, Checkbox, Card, Space, Typography, message, Alert } from 'antd';
import type { MultiTableDataCompareRequest } from '../types/data_compare';
import type { Connection, SchemaInfo, TableInfo } from '../types';
import { useConnections } from '../hooks/useConnections';
import { TableDataResultTable } from './TableDataResultTable';
import { ComparisonProgress } from './ComparisonProgress';
import apiClient from '../api/client';
import {
  DatabaseOutlined,
  SwapOutlined,
  TableOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;
const { Option } = Select;

interface MultiTableDataCompareFormProps {
  connections: Connection[];
}

export interface TableSelection {
  sourceTables: string[];
  targetTables: string[];
}

export interface ComparisonResult {
  summary: {
    total_tables: number;
    compared_tables: number;
    identical_tables: number;
    tables_with_diffs: number;
    error_tables: number;
    total_rows_compared: number;
    total_diffs_found: number;
    elapsed_time_seconds: number;
  };
  table_results: Array<{
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
  }>;
}

/**
 * MultiTableDataCompareForm - Form for comparing data across multiple tables
 */
export const MultiTableDataCompareForm: React.FC<MultiTableDataCompareFormProps> = ({
  connections,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [sourceSchemas, setSourceSchemas] = useState<SchemaInfo[]>([]);
  const [targetSchemas, setTargetSchemas] = useState<SchemaInfo[]>([]);
  const [sourceTables, setSourceTables] = useState<TableInfo[]>([]);
  const [targetTables, setTargetTables] = useState<TableInfo[]>([]);
  const [selectedSourceTables, setSelectedSourceTables] = useState<string[]>([]);
  const [selectedTargetTables, setSelectedTargetTables] = useState<string[]>([]);

  const sourceConnectionId = Form.useWatch('source_connection_id', form);
  const targetConnectionId = Form.useWatch('target_connection_id', form);
  const sourceSchema = Form.useWatch('source_schema', form);
  const targetSchema = Form.useWatch('target_schema', form);

  // Fetch schemas when connection changes
  React.useEffect(() => {
    const fetchSchemas = async () => {
      if (sourceConnectionId) {
        try {
          const response = await apiClient.get(`/api/connections/${sourceConnectionId}/schemas`);
          setSourceSchemas(response.data);
        } catch (error) {
          console.error('Failed to fetch source schemas:', error);
        }
      }
      if (targetConnectionId) {
        try {
          const response = await apiClient.get(`/api/connections/${targetConnectionId}/schemas`);
          setTargetSchemas(response.data);
        } catch (error) {
          console.error('Failed to fetch target schemas:', error);
        }
      }
    };
    fetchSchemas();
  }, [sourceConnectionId, targetConnectionId]);

  // Fetch tables when schema changes
  React.useEffect(() => {
    const fetchTables = async () => {
      if (sourceConnectionId && sourceSchema) {
        try {
          const response = await apiClient.get(`/api/connections/${sourceConnectionId}/tables`, {
            params: { schema: sourceSchema },
          });
          setSourceTables(response.data);
        } catch (error) {
          console.error('Failed to fetch source tables:', error);
        }
      }
      if (targetConnectionId && targetSchema) {
        try {
          const response = await apiClient.get(`/api/connections/${targetConnectionId}/tables`, {
            params: { schema: targetSchema },
          });
          setTargetTables(response.data);
        } catch (error) {
          console.error('Failed to fetch target tables:', error);
        }
      }
    };
    fetchTables();
  }, [sourceConnectionId, sourceSchema, targetConnectionId, targetSchema]);

  const handleSourceTableSelect = (tables: string[]) => {
    setSelectedSourceTables(tables);
    // Auto-match target tables by name
    const matchedTables = tables.filter(t =>
      targetTables.some(tt => tt.table_name === t)
    );
    setSelectedTargetTables(matchedTables);
  };

  const handleTargetTableSelect = (tables: string[]) => {
    setSelectedTargetTables(tables);
  };

  const handleSubmit = async (values: any) => {
    if (selectedSourceTables.length === 0) {
      message.error('Please select at least one table');
      return;
    }

    setLoading(true);
    setProgress(0);
    setResult(null);

    try {
      const request: MultiTableDataCompareRequest = {
        source_connection_id: values.source_connection_id,
        target_connection_id: values.target_connection_id,
        source_schema: values.source_schema,
        target_schema: values.target_schema,
        source_tables: selectedSourceTables,
        target_tables: selectedTargetTables,
        mode: values.mode || 'auto',
        threshold: values.threshold,
        sample_size: values.sample_size,
        timeout_per_table: values.timeout_per_table,
      };

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const response = await apiClient.post('/api/compare/multi-table-data', request);

      clearInterval(progressInterval);
      setProgress(100);
      setResult(response.data);

      message.success('Comparison completed!');
    } catch (error: any) {
      console.error('Multi-table comparison failed:', error);
      message.error(`Comparison failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={4}>
        <TableOutlined /> Multi-Table Data Comparison
      </Title>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        size="large"
      >
        {/* Connection Selection */}
        <Card
          title={<><DatabaseOutlined /> Source Database</>}
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            label="Connection"
            name="source_connection_id"
            rules={[{ required: true, message: 'Please select source connection' }]}
          >
            <Select placeholder="Select source connection">
              {connections.map(conn => (
                <Option key={conn.id} value={conn.id}>{conn.name} ({conn.db_type})</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="Schema"
            name="source_schema"
            rules={[{ required: true, message: 'Please select source schema' }]}
          >
            <Select
              placeholder="Select schema"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={sourceSchemas.map(s => ({ label: s.schema_name, value: s.schema_name }))}
            />
          </Form.Item>
        </Card>

        <Card
          title={<><DatabaseOutlined /> Target Database</>}
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            label="Connection"
            name="target_connection_id"
            rules={[{ required: true, message: 'Please select target connection' }]}
          >
            <Select placeholder="Select target connection">
              {connections.map(conn => (
                <Option key={conn.id} value={conn.id}>{conn.name} ({conn.db_type})</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="Schema"
            name="target_schema"
            rules={[{ required: true, message: 'Please select target schema' }]}
          >
            <Select
              placeholder="Select schema"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={targetSchemas.map(s => ({ label: s.schema_name, value: s.schema_name }))}
            />
          </Form.Item>
        </Card>

        {/* Table Selection */}
        <Card
          title={<><TableOutlined /> Select Tables to Compare</>}
          size="small"
          style={{ marginBottom: 16 }}
        >
          <div style={{ display: 'flex', gap: 16 }}>
            <div style={{ flex: 1 }}>
              <Text strong>Source Tables</Text>
              <div style={{ marginTop: 8, maxHeight: 300, overflow: 'auto', border: '1px solid #d9d9d9', borderRadius: 4, padding: 8 }}>
                <Checkbox.Group
                  value={selectedSourceTables}
                  onChange={handleSourceTableSelect}
                  style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
                >
                  {sourceTables.map(table => (
                    <Checkbox key={table.table_name} value={table.table_name}>
                      {table.table_name} ({table.row_count || '?'} rows)
                    </Checkbox>
                  ))}
                </Checkbox.Group>
              </div>
              <Text type="secondary" style={{ marginTop: 4, display: 'block' }}>
                Selected: {selectedSourceTables.length} tables
              </Text>
            </div>

            <div style={{ display: 'flex', alignItems: 'center' }}>
              <SwapOutlined style={{ fontSize: 24, color: '#999' }} />
            </div>

            <div style={{ flex: 1 }}>
              <Text strong>Target Tables</Text>
              <div style={{ marginTop: 8, maxHeight: 300, overflow: 'auto', border: '1px solid #d9d9d9', borderRadius: 4, padding: 8 }}>
                <Checkbox.Group
                  value={selectedTargetTables}
                  onChange={handleTargetTableSelect}
                  style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
                >
                  {targetTables.map(table => (
                    <Checkbox
                      key={table.table_name}
                      value={table.table_name}
                      disabled={!sourceTables.some(st => st.table_name === table.table_name)}
                    >
                      {table.table_name} ({table.row_count || '?'} rows)
                      {!sourceTables.some(st => st.table_name === table.table_name) && ' (no match)'}
                    </Checkbox>
                  ))}
                </Checkbox.Group>
              </div>
              <Text type="secondary" style={{ marginTop: 4, display: 'block' }}>
                Selected: {selectedTargetTables.length} tables
              </Text>
            </div>
          </div>

          {selectedSourceTables.length > 0 && selectedSourceTables.length !== selectedTargetTables.length && (
            <Alert
              type="warning"
              message={`Table count mismatch: ${selectedSourceTables.length} source tables vs ${selectedTargetTables.length} target tables`}
              style={{ marginTop: 16 }}
            />
          )}
        </Card>

        {/* Comparison Options */}
        <Card
          title="Comparison Options"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item label="Comparison Mode" name="mode" initialValue="auto">
            <Select>
              <Option value="auto">Auto (recommended)</Option>
              <Option value="full">Full (compare all rows)</Option>
              <Option value="hash">Hash (checksum only)</Option>
              <Option value="sample">Sample (compare sampled rows)</Option>
            </Select>
          </Form.Item>

          <div style={{ display: 'flex', gap: 16 }}>
            <Form.Item
              label="Row Threshold"
              name="threshold"
              initialValue={100000}
              style={{ flex: 1 }}
            >
              <InputNumber
                style={{ width: '100%' }}
                min={1000}
                max={10000000}
                step={10000}
              />
            </Form.Item>

            <Form.Item
              label="Sample Size"
              name="sample_size"
              initialValue={1000}
              style={{ flex: 1 }}
            >
              <InputNumber
                style={{ width: '100%' }}
                min={100}
                max={10000}
                step={100}
              />
            </Form.Item>

            <Form.Item
              label="Timeout (sec/table)"
              name="timeout_per_table"
              initialValue={300}
              style={{ flex: 1 }}
            >
              <InputNumber
                style={{ width: '100%' }}
                min={30}
                max={3600}
                step={30}
              />
            </Form.Item>
          </div>
        </Card>

        <Form.Item style={{ marginBottom: 0 }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
            block
            disabled={selectedSourceTables.length === 0}
          >
            Start Comparison
          </Button>
        </Form.Item>
      </Form>

      {/* Progress and Results */}
      {(loading || result) && (
        <div style={{ marginTop: 24 }}>
          {loading && (
            <ComparisonProgress
              current={progress}
              total={100}
              status="active"
            />
          )}

          {result && (
            <TableDataResultTable
              summary={result.summary}
              tableResults={result.table_results}
            />
          )}
        </div>
      )}
    </div>
  );
};
