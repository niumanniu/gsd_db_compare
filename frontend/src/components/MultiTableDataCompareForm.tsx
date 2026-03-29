import React, { useState, useCallback } from 'react';
import { Form, Input, InputNumber, Select, Button, Checkbox, Card, Space, Typography, message, Alert, Row, Col, Tag, Modal } from 'antd';
import type { MultiTableDataCompareRequest } from '../types/data_compare';
import type { Connection, SchemaInfo, TableInfo } from '../types';
import { useConnections } from '../hooks/useConnections';
import { TableDataResultTable } from './TableDataResultTable';
import { ComparisonProgress } from './ComparisonProgress';
import { DataDiffViewer } from './DataDiffViewer';
import apiClient from '../api/client';
import {
  DatabaseOutlined,
  SwapOutlined,
  TableOutlined,
  CheckCircleOutlined,
  DiffOutlined,
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
  const [selectedTableForDetail, setSelectedTableForDetail] = useState<{
    sourceTable: string;
    targetTable: string;
  } | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

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
          setSourceTables(response.data || []);
        } catch (error) {
          console.error('Failed to fetch source tables:', error);
          setSourceTables([]);
        }
      } else {
        setSourceTables([]);
      }
      if (targetConnectionId && targetSchema) {
        try {
          const response = await apiClient.get(`/api/connections/${targetConnectionId}/tables`, {
            params: { schema: targetSchema },
          });
          setTargetTables(response.data || []);
        } catch (error) {
          console.error('Failed to fetch target tables:', error);
          setTargetTables([]);
        }
      } else {
        setTargetTables([]);
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

  const handleViewDetails = useCallback((tableResult: any) => {
    setSelectedTableForDetail({
      sourceTable: tableResult.source_table,
      targetTable: tableResult.target_table,
    });
    setDetailModalOpen(true);
  }, []);

  const handleDetailModalClose = () => {
    setDetailModalOpen(false);
    setSelectedTableForDetail(null);
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
        {/* Connection Selection - Unified Layout */}
        <Card
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16} style={{ marginBottom: 20 }}>
            <Col span={12}>
              <Text strong style={{
                display: 'block',
                marginBottom: 8,
                fontSize: '13px',
                color: 'rgba(0, 0, 0, 0.65)',
              }}>Source Connection</Text>
              <Form.Item
                name="source_connection_id"
                rules={[{ required: true, message: 'Please select source connection' }]}
              >
                <Select
                  style={{ width: '100%' }}
                  placeholder="Select source connection"
                  size="large"
                >
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
            </Col>
            <Col span={12}>
              <Text strong style={{
                display: 'block',
                marginBottom: 8,
                fontSize: '13px',
                color: 'rgba(0, 0, 0, 0.65)',
              }}>Target Connection</Text>
              <Form.Item
                name="target_connection_id"
                rules={[{ required: true, message: 'Please select target connection' }]}
              >
                <Select
                  style={{ width: '100%' }}
                  placeholder="Select target connection"
                  size="large"
                >
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
            </Col>
          </Row>
        </Card>

        {/* Table Selection */}
        <Card
          title={<><TableOutlined /> Select Tables to Compare</>}
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col span={12}>
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
            </Col>

            <Col span={12} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <SwapOutlined style={{ fontSize: 24, color: '#999' }} />
                <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>Compare</div>
              </div>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Text strong>Target Tables (auto-matched)</Text>
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
            </Col>
          </Row>

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

        {/* Compare Button - Centered */}
        <div style={{ textAlign: 'center', marginTop: 24, marginBottom: 16 }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
            disabled={selectedSourceTables.length === 0}
            icon={<SwapOutlined />}
            style={{
              padding: '12px 32px',
              fontSize: '15px',
              fontWeight: 500,
              borderRadius: 6,
            }}
          >
            {loading ? 'Comparing...' : 'Start Comparison'}
          </Button>
        </div>
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
              {/* Database Info Header - Consistent with SchemaDiffViewer */}
              <div style={{
                marginBottom: 16,
                padding: 16,
                background: '#e6f4ff',
                borderRadius: 8,
                border: '1px solid #bae0ff',
              }}>
                <Text strong>Comparison: </Text>
                <Tag color="blue">Multi-Table Data</Tag>
                <Text type="secondary"> ({result.table_results.length} tables compared)</Text>
              </div>

              {/* Summary Cards - Consistent with SchemaDiffViewer */}
              <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
                <div
                  style={{
                    padding: '16px 24px',
                    backgroundColor: result.summary.tables_with_diffs > 0 ? '#fff7e6' : '#f6ffed',
                    border: '1px solid',
                    borderColor: result.summary.tables_with_diffs > 0 ? '#ffd591' : '#b7eb8f',
                    borderRadius: 8,
                    minWidth: 180,
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: result.summary.tables_with_diffs > 0 ? '#fa8c16' : '#52c41a' }}>
                    {result.summary.identical_tables}
                  </div>
                  <div style={{ color: 'rgba(0, 0, 0, 0.65)', marginTop: 4, fontSize: 13 }}>Identical Tables</div>
                </div>
                <div
                  style={{
                    padding: '16px 24px',
                    backgroundColor: result.summary.tables_with_diffs > 0 ? '#fff7e6' : '#f6ffed',
                    border: '1px solid',
                    borderColor: result.summary.tables_with_diffs > 0 ? '#ffd591' : '#b7eb8f',
                    borderRadius: 8,
                    minWidth: 180,
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: result.summary.tables_with_diffs > 0 ? '#fa8c16' : '#52c41a' }}>
                    {result.summary.tables_with_diffs}
                  </div>
                  <div style={{ color: 'rgba(0, 0, 0, 0.65)', marginTop: 4, fontSize: 13 }}>Tables with Diffs</div>
                </div>
                <div
                  style={{
                    padding: '16px 24px',
                    backgroundColor: result.summary.error_tables > 0 ? '#fff7e6' : '#f6ffed',
                    border: '1px solid',
                    borderColor: result.summary.error_tables > 0 ? '#ffd591' : '#b7eb8f',
                    borderRadius: 8,
                    minWidth: 180,
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: result.summary.error_tables > 0 ? '#fa8c16' : '#52c41a' }}>
                    {result.summary.error_tables}
                  </div>
                  <div style={{ color: 'rgba(0, 0, 0, 0.65)', marginTop: 4, fontSize: 13 }}>Error Tables</div>
                </div>
                <div
                  style={{
                    padding: '16px 24px',
                    backgroundColor: '#f5f5f5',
                    border: '1px solid #d9d9d9',
                    borderRadius: 8,
                    minWidth: 180,
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: '#666' }}>
                    {result.summary.total_rows_compared.toLocaleString()}
                  </div>
                  <div style={{ color: 'rgba(0, 0, 0, 0.65)', marginTop: 4, fontSize: 13 }}>Rows Compared</div>
                </div>
              </div>

              {/* Legend */}
              <div style={{
                marginBottom: 16,
                padding: 12,
                backgroundColor: '#fafafa',
                borderRadius: 6,
                border: '1px solid #f0f0f0',
              }}>
                <Text strong style={{ marginRight: 12 }}>Legend: </Text>
                <Tag color="green" style={{ marginRight: 8 }}><CheckCircleOutlined /> IDENTICAL</Tag>
                <Tag color="gold" style={{ marginRight: 8 }}><DiffOutlined /> HAS DIFFS</Tag>
                <Tag color="red" style={{ marginRight: 8 }}>ERROR</Tag>
              </div>

              <TableDataResultTable
                summary={result.summary}
                tableResults={result.table_results}
                onViewDetails={handleViewDetails}
              />
            </>
          )}
        </div>
      )}

      {/* Detail Modal - Data Diff Viewer */}
      <Modal
        title={
          <Space>
            <TableOutlined />
            Data Comparison Details: {selectedTableForDetail?.sourceTable}
          </Space>
        }
        open={detailModalOpen}
        onCancel={handleDetailModalClose}
        footer={null}
        width={1400}
        centered
      >
        {selectedTableForDetail && sourceConnectionId && targetConnectionId && (
          <DataDiffViewer
            sourceConnectionId={sourceConnectionId}
            targetConnectionId={targetConnectionId}
            sourceTable={selectedTableForDetail.sourceTable}
            targetTable={selectedTableForDetail.targetTable}
          />
        )}
      </Modal>
    </div>
  );
};
