import React, { useState, useCallback, useEffect } from 'react';
import { Form, Input, Select, Button, Card, Space, Typography, message, Alert, Tag, InputNumber } from 'antd';
import type { SchemaDataCompareRequest } from '../types/data_compare';
import type { Connection, SchemaInfo } from '../types';
import apiClient from '../api/client';
import { TableDataResultTable } from './TableDataResultTable';
import { ComparisonProgress } from './ComparisonProgress';
import {
  DatabaseOutlined,
  FilterOutlined,
  EyeOutlined,
  SearchOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;
const { Option } = Select;

interface SchemaDataCompareFormProps {
  connections: Connection[];
}

export interface SchemaComparisonResult {
  summary: {
    source_schema: string;
    target_schema: string;
    source_connection_name: string;
    target_connection_name: string;
    total_source_tables: number;
    total_target_tables: number;
    common_tables: number;
    unmatched_source_tables: number;
    unmatched_target_tables: number;
    compared_tables: number;
    identical_tables: number;
    tables_with_diffs: number;
    error_tables: number;
    total_rows_source: number;
    total_rows_target: number;
    total_diffs_found: number;
    overall_diff_percentage: number | null;
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
  unmatched_source_tables: string[];
  unmatched_target_tables: string[];
  excluded_tables: string[];
}

/**
 * SchemaDataCompareForm - Form for comparing data across entire schema
 */
export const SchemaDataCompareForm: React.FC<SchemaDataCompareFormProps> = ({
  connections,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SchemaComparisonResult | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [sourceSchemas, setSourceSchemas] = useState<SchemaInfo[]>([]);
  const [targetSchemas, setTargetSchemas] = useState<SchemaInfo[]>([]);
  const [tablePreview, setTablePreview] = useState<{
    sourceTables: number;
    targetTables: number;
    commonTables: number;
  } | null>(null);

  const sourceConnectionId = Form.useWatch('source_connection_id', form);
  const targetConnectionId = Form.useWatch('target_connection_id', form);

  // Fetch schemas when connection changes
  useEffect(() => {
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

  // Fetch table preview when schemas change
  useEffect(() => {
    const fetchTablePreview = async () => {
      const sourceSchema = form.getFieldValue('source_schema');
      const targetSchema = form.getFieldValue('target_schema');

      if (sourceConnectionId && targetConnectionId && sourceSchema && targetSchema) {
        try {
          const [sourceResponse, targetResponse] = await Promise.all([
            apiClient.get(`/api/connections/${sourceConnectionId}/tables`, {
              params: { schema: sourceSchema },
            }),
            apiClient.get(`/api/connections/${targetConnectionId}/tables`, {
              params: { schema: targetSchema },
            }),
          ]);

          const sourceTableNames = new Set(sourceResponse.data.map((t: any) => t.table_name));
          const targetTableNames = new Set(targetResponse.data.map((t: any) => t.table_name));

          const common = [...sourceTableNames].filter((t) => targetTableNames.has(t)).length;

          setTablePreview({
            sourceTables: sourceTableNames.size,
            targetTables: targetTableNames.size,
            commonTables: common,
          });
        } catch (error) {
          console.error('Failed to fetch table preview:', error);
          setTablePreview(null);
        }
      } else {
        setTablePreview(null);
      }
    };
    fetchTablePreview();
  }, [sourceConnectionId, targetConnectionId, form]);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    setProgress(0);
    setResult(null);

    try {
      const request: SchemaDataCompareRequest = {
        source_connection_id: values.source_connection_id,
        target_connection_id: values.target_connection_id,
        source_schema: values.source_schema,
        target_schema: values.target_schema,
        exclude_patterns: values.exclude_patterns?.filter((p: string) => p.trim()) || [],
        include_patterns: values.include_patterns?.filter((p: string) => p.trim()) || [],
        only_common_tables: values.only_common_tables,
        mode: values.mode || 'hash',
        threshold: values.threshold,
        sample_size: values.sample_size,
        timeout_per_table: values.timeout_per_table,
      };

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 5, 90));
      }, 500);

      const response = await apiClient.post('/api/compare/schema-data', request);

      clearInterval(progressInterval);
      setProgress(100);
      setResult(response.data);

      message.success('Schema comparison completed!');
    } catch (error: any) {
      console.error('Schema comparison failed:', error);
      message.error(`Comparison failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
    setResult(null);
    setProgress(0);
    setTablePreview(null);
  };

  return (
    <div>
      <Title level={4}>
        <DatabaseOutlined /> Schema-Level Data Comparison
      </Title>

      <Alert
        message="Compare all tables in a schema"
        description="This will compare data across all tables in the selected schemas. For large schemas, consider using hash mode first to quickly identify differences."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        size="large"
        onValuesChange={() => form.validateFields()}
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
              {connections.map((conn) => (
                <Option key={conn.id} value={conn.id}>
                  {conn.name} ({conn.db_type})
                </Option>
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
              options={sourceSchemas.map((s) => ({ label: s.schema_name, value: s.schema_name }))}
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
              {connections.map((conn) => (
                <Option key={conn.id} value={conn.id}>
                  {conn.name} ({conn.db_type})
                </Option>
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
              options={targetSchemas.map((s) => ({ label: s.schema_name, value: s.schema_name }))}
            />
          </Form.Item>
        </Card>

        {/* Table Preview */}
        {tablePreview && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Table Preview:</Text>
              <Space>
                <Tag color="blue">Source: {tablePreview.sourceTables} tables</Tag>
                <Tag color="green">Target: {tablePreview.targetTables} tables</Tag>
                <Tag color="cyan">Common: {tablePreview.commonTables} tables</Tag>
              </Space>
            </Space>
          </Card>
        )}

        {/* Filter Options */}
        <Card
          title={<><FilterOutlined /> Filter Options</>}
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            label="Exclude Patterns"
            name="exclude_patterns"
            tooltip="Tables matching these patterns will be excluded (supports * wildcard)"
            extra="Example: sys_*, *_log, tmp_*"
          >
            <Select
              mode="tags"
              placeholder="Add patterns to exclude (e.g., sys_*, *_log)"
              tokenSeparators={[',']}
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="Include Patterns (optional)"
            name="include_patterns"
            tooltip="If provided, only tables matching these patterns will be included"
            extra="Leave empty to include all tables (except excluded)"
          >
            <Select
              mode="tags"
              placeholder="Add patterns to include"
              tokenSeparators={[',']}
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="Comparison Scope"
            name="only_common_tables"
            initialValue={true}
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>Only common tables (recommended)</Option>
              <Option value={false}>All tables (include unmatched)</Option>
            </Select>
          </Form.Item>
        </Card>

        {/* Comparison Options */}
        <Card
          title="Comparison Options"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item label="Comparison Mode" name="mode" initialValue="hash">
            <Select>
              <Option value="hash">Hash (recommended for schema-level)</Option>
              <Option value="auto">Auto</Option>
              <Option value="sample">Sample</Option>
              <Option value="full">Full (slow, for small schemas only)</Option>
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
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Button size="large" onClick={handleReset}>
              Reset
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
              style={{ minWidth: 200 }}
            >
              Start Schema Comparison
            </Button>
          </Space>
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
            <>
              {/* Unmatched Tables */}
              {(result.unmatched_source_tables.length > 0 || result.unmatched_target_tables.length > 0) && (
                <Card
                  title={<><EyeOutlined /> Unmatched Tables</>}
                  size="small"
                  style={{ marginBottom: 16 }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {result.unmatched_source_tables.length > 0 && (
                      <div>
                        <Text strong>Only in Source ({result.unmatched_source_tables.length}):</Text>
                        <div style={{ marginTop: 4 }}>
                          {result.unmatched_source_tables.map((t) => (
                            <Tag key={t} color="orange">{t}</Tag>
                          ))}
                        </div>
                      </div>
                    )}
                    {result.unmatched_target_tables.length > 0 && (
                      <div>
                        <Text strong>Only in Target ({result.unmatched_target_tables.length}):</Text>
                        <div style={{ marginTop: 4 }}>
                          {result.unmatched_target_tables.map((t) => (
                            <Tag key={t} color="purple">{t}</Tag>
                          ))}
                        </div>
                      </div>
                    )}
                  </Space>
                </Card>
              )}

              {/* Excluded Tables */}
              {result.excluded_tables.length > 0 && (
                <Card
                  title={<><FilterOutlined /> Excluded Tables</>}
                  size="small"
                  style={{ marginBottom: 16 }}
                >
                  <div>
                    {result.excluded_tables.slice(0, 20).map((t) => (
                      <Tag key={t} color="default">{t}</Tag>
                    ))}
                    {result.excluded_tables.length > 20 && (
                      <Text type="secondary"> +{result.excluded_tables.length - 20} more</Text>
                    )}
                  </div>
                </Card>
              )}

              <TableDataResultTable
                summary={{
                  total_tables: result.summary.total_source_tables,
                  compared_tables: result.summary.compared_tables,
                  identical_tables: result.summary.identical_tables,
                  tables_with_diffs: result.summary.tables_with_diffs,
                  error_tables: result.summary.error_tables,
                  total_rows_compared: result.summary.total_rows_source + result.summary.total_rows_target,
                  total_diffs_found: result.summary.total_diffs_found,
                  elapsed_time_seconds: result.summary.elapsed_time_seconds,
                }}
                tableResults={result.table_results}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
};
