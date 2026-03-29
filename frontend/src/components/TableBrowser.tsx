import React, { useState, useMemo } from 'react';
import { Select, Table, Button, Space, Typography, Empty, Row, Col, Input, Tag, Checkbox } from 'antd';
import { ThunderboltOutlined, SwapOutlined, DatabaseOutlined } from '@ant-design/icons';
import type { TableInfo, SchemaInfo } from '../types';
import type { TableRowSelection } from 'antd/es/table/interface';

const { Option } = Select;

type CompareMode = 'single' | 'multi' | 'database';

interface TableBrowserProps {
  connections: { id: number; name: string; db_type: string }[];
  sourceConnectionId: number | null;
  targetConnectionId: number | null;
  onSourceConnectionChange: (id: number | null) => void;
  onTargetConnectionChange: (id: number | null) => void;
  sourceTables: TableInfo[];
  targetTables: TableInfo[];
  sourceTable: string | null;
  targetTable: string | null;
  onSourceTableChange: (table: string | null) => void;
  onTargetTableChange: (table: string | null) => void;
  onCompare: () => void;
  isComparing: boolean;
  isLoadingTables: boolean;
  // New props for multi-table and database comparison
  compareMode?: CompareMode;
  onCompareModeChange?: (mode: CompareMode) => void;
  sourceTablesSelected?: string[];
  targetTablesSelected?: string[];
  onSourceTablesSelectedChange?: (tables: string[]) => void;
  onTargetTablesSelectedChange?: (tables: string[]) => void;
  onCompareBatch?: () => void;
  isComparingBatch?: boolean;
  excludePatterns?: string[];
  onExcludePatternsChange?: (patterns: string[]) => void;
  onCompareDatabase?: () => void;
  isComparingDatabase?: boolean;
  // Schema selection for database-level mode
  sourceSchema?: string | null;
  targetSchema?: string | null;
  onSourceSchemaChange?: (schema: string | null) => void;
  onTargetSchemaChange?: (schema: string | null) => void;
  sourceSchemas?: SchemaInfo[];
  targetSchemas?: SchemaInfo[];
  isFetchingSchemas?: boolean;
}

export const TableBrowser: React.FC<TableBrowserProps> = ({
  connections,
  sourceConnectionId,
  targetConnectionId,
  onSourceConnectionChange,
  onTargetConnectionChange,
  sourceTables,
  targetTables,
  sourceTable,
  targetTable,
  onSourceTableChange,
  onTargetTableChange,
  onCompare,
  isComparing,
  isLoadingTables,
  compareMode = 'single',
  onCompareModeChange,
  sourceTablesSelected = [],
  targetTablesSelected = [],
  onSourceTablesSelectedChange,
  onTargetTablesSelectedChange,
  onCompareBatch,
  isComparingBatch,
  excludePatterns = [],
  onExcludePatternsChange,
  onCompareDatabase,
  isComparingDatabase,
  sourceSchema,
  targetSchema,
  onSourceSchemaChange,
  onTargetSchemaChange,
  sourceSchemas,
  targetSchemas,
  isFetchingSchemas,
}) => {
  const [excludeInput, setExcludeInput] = useState('');

  // Single table compare: check if both tables selected
  const canCompareSingle = sourceConnectionId && targetConnectionId && sourceTable && targetTable;

  // Multi-table compare: check if at least one table selected in both
  const canCompareBatch = sourceConnectionId && targetConnectionId &&
    sourceTablesSelected.length > 0 && targetTablesSelected.length > 0;

  // Database compare: check if both connections selected
  const canCompareDatabase = sourceConnectionId && targetConnectionId;

  // Auto-match tables for multi-table mode
  const autoMatchedTables = useMemo(() => {
    const sourceSet = new Set(sourceTablesSelected);
    const targetSet = new Set(targetTablesSelected);
    const matched: Record<string, string> = {};

    sourceSet.forEach(table => {
      if (targetSet.has(table)) {
        matched[table] = table;
      }
    });

    return matched;
  }, [sourceTablesSelected, targetTablesSelected]);

  // Tables to show in multi-select (filtered by exclude patterns for database mode)
  const getFilteredTables = (tables: TableInfo[], isSource: boolean) => {
    if (compareMode !== 'database') return tables;

    return tables.filter(table => {
      for (const pattern of excludePatterns) {
        const regex = new RegExp(`^${pattern.replace(/\*/g, '.*').replace(/\?/g, '.')}$`, 'i');
        if (regex.test(table.table_name)) {
          return false;
        }
      }
      return true;
    });
  };

  const filteredSourceTables = getFilteredTables(sourceTables, true);
  const filteredTargetTables = getFilteredTables(targetTables, false);

  const handleExcludePatternAdd = () => {
    if (excludeInput.trim() && onExcludePatternsChange) {
      onExcludePatternsChange([...excludePatterns, ...excludeInput.split(',').map(p => p.trim()).filter(Boolean)]);
      setExcludeInput('');
    }
  };

  const handleExcludePatternRemove = (pattern: string) => {
    if (onExcludePatternsChange) {
      onExcludePatternsChange(excludePatterns.filter(p => p !== pattern));
    }
  };

  return (
    <div style={{
      marginBottom: 24,
      padding: 24,
      backgroundColor: '#ffffff',
      borderRadius: 8,
      boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Typography.Title level={4} style={{
          marginBottom: 0,
          fontSize: '16px',
          fontWeight: 600,
          color: 'rgba(0, 0, 0, 0.88)',
        }}>
          Schema Comparison
        </Typography.Title>

        {/* Mode Switcher */}
        <Space size="small">
          <Tag
            color={compareMode === 'single' ? 'blue' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() => onCompareModeChange?.('single')}
          >
            Single Table
          </Tag>
          <Tag
            color={compareMode === 'multi' ? 'blue' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() => onCompareModeChange?.('multi')}
          >
            Multi Table
          </Tag>
          <Tag
            color={compareMode === 'database' ? 'blue' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() => onCompareModeChange?.('database')}
          >
            Database Level
          </Tag>
        </Space>
      </div>

      {/* Connection Selection (same for all modes) */}
      <Row gutter={16} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <Typography.Text strong style={{
            display: 'block',
            marginBottom: 8,
            fontSize: '13px',
            color: 'rgba(0, 0, 0, 0.65)',
          }}>Source Connection</Typography.Text>
          <Select
            style={{ width: '100%' }}
            placeholder="Select source connection"
            value={sourceConnectionId}
            onChange={onSourceConnectionChange}
            disabled={!connections.length}
            size="large"
          >
            {connections.map((conn) => (
              <Option key={conn.id} value={conn.id}>
                {conn.name} ({conn.db_type})
              </Option>
            ))}
          </Select>
        </Col>
        <Col span={12}>
          <Typography.Text strong style={{
            display: 'block',
            marginBottom: 8,
            fontSize: '13px',
            color: 'rgba(0, 0, 0, 0.65)',
          }}>Target Connection</Typography.Text>
          <Select
            style={{ width: '100%' }}
            placeholder="Select target connection"
            value={targetConnectionId}
            onChange={onTargetConnectionChange}
            disabled={!connections.length}
            size="large"
          >
            {connections.map((conn) => (
              <Option key={conn.id} value={conn.id}>
                {conn.name} ({conn.db_type})
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      {/* Schema Selection - Database Level Mode */}
      {compareMode === 'database' && (
        <Row gutter={16} style={{ marginBottom: 20 }}>
          <Col span={12}>
            <Typography.Text strong>Source Schema (Database)</Typography.Text>
            <Select
              style={{ width: '100%' }}
              placeholder="Select schema"
              value={sourceSchema}
              onChange={onSourceSchemaChange}
              disabled={!sourceConnectionId}
              showSearch
              optionFilterProp="children"
              loading={isFetchingSchemas}
            >
              {sourceSchemas?.map((schema) => (
                <Option key={schema.schema_name} value={schema.schema_name}>
                  {schema.schema_name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={12}>
            <Typography.Text strong>Target Schema (User)</Typography.Text>
            <Select
              style={{ width: '100%' }}
              placeholder="Select schema"
              value={targetSchema}
              onChange={onTargetSchemaChange}
              disabled={!targetConnectionId}
              showSearch
              optionFilterProp="children"
              loading={isFetchingSchemas}
            >
              {targetSchemas?.map((schema) => (
                <Option key={schema.schema_name} value={schema.schema_name}>
                  {schema.schema_name}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      )}

      {/* Table Selection - Varies by mode */}
      {compareMode === 'single' && (
        <Row gutter={16} style={{ marginBottom: 20 }}>
          <Col span={12}>
            <Typography.Text strong style={{
              display: 'block',
              marginBottom: 8,
              fontSize: '13px',
              color: 'rgba(0, 0, 0, 0.65)',
            }}>Source Table</Typography.Text>
            <Select
              style={{ width: '100%' }}
              placeholder={sourceConnectionId ? 'Select table' : 'Select connection first'}
              value={sourceTable}
              onChange={onSourceTableChange}
              disabled={!sourceConnectionId || isLoadingTables}
              showSearch
              optionFilterProp="children"
              size="large"
            >
              {sourceTables.map((table) => (
                <Option key={table.table_name} value={table.table_name}>
                  {table.table_name} {table.row_count ? `(${table.row_count.toLocaleString()} rows)` : ''}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={12}>
            <Typography.Text strong style={{
              display: 'block',
              marginBottom: 8,
              fontSize: '13px',
              color: 'rgba(0, 0, 0, 0.65)',
            }}>Target Table</Typography.Text>
            <Select
              style={{ width: '100%' }}
              placeholder={targetConnectionId ? 'Select table' : 'Select connection first'}
              value={targetTable}
              onChange={onTargetTableChange}
              disabled={!targetConnectionId || isLoadingTables}
              showSearch
              optionFilterProp="children"
              size="large"
            >
              {targetTables.map((table) => (
                <Option key={table.table_name} value={table.table_name}>
                  {table.table_name} {table.row_count ? `(${table.row_count.toLocaleString()} rows)` : ''}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      )}

      {compareMode === 'multi' && (
        <Row gutter={16} style={{ marginBottom: 20 }}>
          <Col span={12}>
            <Typography.Text strong style={{
              display: 'block',
              marginBottom: 8,
              fontSize: '13px',
              color: 'rgba(0, 0, 0, 0.65)',
            }}>Source Tables (Select multiple)</Typography.Text>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder={sourceConnectionId ? 'Select tables' : 'Select connection first'}
              value={sourceTablesSelected}
              onChange={onSourceTablesSelectedChange}
              disabled={!sourceConnectionId || isLoadingTables}
              showSearch
              optionFilterProp="children"
              size="large"
              maxTagCount="responsive"
            >
              {sourceTables.map((table) => (
                <Option key={table.table_name} value={table.table_name}>
                  {table.table_name} {table.row_count ? `(${table.row_count.toLocaleString()})` : ''}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={12}>
            <Typography.Text strong style={{
              display: 'block',
              marginBottom: 8,
              fontSize: '13px',
              color: 'rgba(0, 0, 0, 0.65)',
            }}>Target Tables (Select multiple)</Typography.Text>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder={targetConnectionId ? 'Select tables' : 'Select connection first'}
              value={targetTablesSelected}
              onChange={onTargetTablesSelectedChange}
              disabled={!targetConnectionId || isLoadingTables}
              showSearch
              optionFilterProp="children"
              size="large"
              maxTagCount="responsive"
            >
              {targetTables.map((table) => (
                <Option key={table.table_name} value={table.table_name}>
                  {table.table_name} {table.row_count ? `(${table.row_count.toLocaleString()})` : ''}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      )}

      {compareMode === 'database' && (
        <Row gutter={16} style={{ marginBottom: 20 }}>
          <Col span={24}>
            <Typography.Text strong style={{
              display: 'block',
              marginBottom: 8,
              fontSize: '13px',
              color: 'rgba(0, 0, 0, 0.65)',
            }}>Exclude Tables (Supports wildcards like sys_*, *_log)</Typography.Text>
            <Space.Compact style={{ width: '100%' }}>
              <Input
                value={excludeInput}
                onChange={(e) => setExcludeInput(e.target.value)}
                placeholder="Enter patterns separated by commas"
                onPressEnter={handleExcludePatternAdd}
              />
              <Button type="primary" onClick={handleExcludePatternAdd}>Add</Button>
            </Space.Compact>
            {excludePatterns.length > 0 && (
              <div style={{ marginTop: 8 }}>
                {excludePatterns.map((pattern) => (
                  <Tag
                    key={pattern}
                    closable
                    onClose={() => handleExcludePatternRemove(pattern)}
                    color="orange"
                    style={{ marginRight: 4, marginBottom: 4 }}
                  >
                    {pattern}
                  </Tag>
                ))}
              </div>
            )}
          </Col>
        </Row>
      )}

      {/* Compare Button */}
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        {compareMode === 'single' && (
          <Button
            type="primary"
            size="large"
            onClick={onCompare}
            disabled={!canCompareSingle}
            loading={isComparing}
            icon={<SwapOutlined />}
            style={{
              padding: '12px 32px',
              fontSize: '15px',
              fontWeight: 500,
              borderRadius: 6,
            }}
          >
            {isComparing ? 'Comparing...' : 'Compare Schemas'}
          </Button>
        )}

        {compareMode === 'multi' && (
          <Button
            type="primary"
            size="large"
            onClick={onCompareBatch}
            disabled={!canCompareBatch}
            loading={isComparingBatch}
            icon={<ThunderboltOutlined />}
            style={{
              padding: '12px 32px',
              fontSize: '15px',
              fontWeight: 500,
              borderRadius: 6,
            }}
          >
            {isComparingBatch ? 'Comparing...' : `Batch Compare (${Object.keys(autoMatchedTables).length} matched tables)`}
          </Button>
        )}

        {compareMode === 'database' && (
          <Button
            type="primary"
            size="large"
            onClick={onCompareDatabase}
            disabled={!canCompareDatabase}
            loading={isComparingDatabase}
            icon={<DatabaseOutlined />}
            style={{
              padding: '12px 32px',
              fontSize: '15px',
              fontWeight: 500,
              borderRadius: 6,
            }}
          >
            {isComparingDatabase ? 'Comparing...' : 'Compare Databases'}
          </Button>
        )}
      </div>

      {/* Table Previews */}
      {(sourceTables.length > 0 || targetTables.length > 0) && compareMode !== 'database' && (
        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={12}>
            <Typography.Title level={5} style={{
              fontSize: '14px',
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.88)',
              marginBottom: 12,
            }}>
              {compareMode === 'multi' ? 'Source Tables (Click to select)' : 'Source Tables'}
            </Typography.Title>
            <Table
              dataSource={compareMode === 'multi' ? filteredSourceTables : sourceTables}
              columns={[
                { title: 'Table Name', dataIndex: 'table_name', key: 'table_name' },
                { title: 'Type', dataIndex: 'table_type', key: 'table_type' },
                {
                  title: 'Rows',
                  dataIndex: 'row_count',
                  key: 'row_count',
                  render: (count: number | null) => count?.toLocaleString() || 'N/A',
                },
              ]}
              pagination={{ pageSize: 5 }}
              size="small"
              loading={isLoadingTables}
              onRow={(record) => ({
                onClick: () => {
                  if (compareMode === 'single') {
                    onSourceTableChange(record.table_name);
                  }
                },
                style: {
                  cursor: compareMode === 'single' ? 'pointer' : 'default',
                  backgroundColor: sourceTable === record.table_name ? '#e6f4ff' : undefined,
                },
              })}
              rowSelection={compareMode === 'multi' ? {
                selectedRowKeys: sourceTablesSelected,
                onChange: (selectedRowKeys: (string | number)[], selectedRows: TableInfo[]) => {
                  onSourceTablesSelectedChange?.(selectedRowKeys as string[]);
                },
              } as TableRowSelection<TableInfo> : undefined}
            />
          </Col>
          <Col span={12}>
            <Typography.Title level={5} style={{
              fontSize: '14px',
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.88)',
              marginBottom: 12,
            }}>
              {compareMode === 'multi' ? 'Target Tables (Click to select)' : 'Target Tables'}
            </Typography.Title>
            <Table
              dataSource={compareMode === 'multi' ? filteredTargetTables : targetTables}
              columns={[
                { title: 'Table Name', dataIndex: 'table_name', key: 'table_name' },
                { title: 'Type', dataIndex: 'table_type', key: 'table_type' },
                {
                  title: 'Rows',
                  dataIndex: 'row_count',
                  key: 'row_count',
                  render: (count: number | null) => count?.toLocaleString() || 'N/A',
                },
              ]}
              pagination={{ pageSize: 5 }}
              size="small"
              loading={isLoadingTables}
              onRow={(record) => ({
                onClick: () => {
                  if (compareMode === 'single') {
                    onTargetTableChange(record.table_name);
                  }
                },
                style: {
                  cursor: compareMode === 'single' ? 'pointer' : 'default',
                  backgroundColor: targetTable === record.table_name ? '#e6f4ff' : undefined,
                },
              })}
              rowSelection={compareMode === 'multi' ? {
                selectedRowKeys: targetTablesSelected,
                onChange: (selectedRowKeys: (string | number)[], selectedRows: TableInfo[]) => {
                  onTargetTablesSelectedChange?.(selectedRowKeys as string[]);
                },
              } as TableRowSelection<TableInfo> : undefined}
            />
          </Col>
        </Row>
      )}
    </div>
  );
};
