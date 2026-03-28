import React from 'react';
import { Select, Table, Button, Space, Typography, Empty, Row, Col } from 'antd';
import type { TableInfo } from '../types';

const { Option } = Select;

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
}) => {
  const canCompare = sourceConnectionId && targetConnectionId && sourceTable && targetTable;

  return (
    <div style={{ marginBottom: 24 }}>
      <Typography.Title level={4}>Schema Comparison</Typography.Title>

      {/* Connection Selection */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Typography.Text strong>Source Connection</Typography.Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="Select source connection"
            value={sourceConnectionId}
            onChange={onSourceConnectionChange}
            disabled={!connections.length}
          >
            {connections.map((conn) => (
              <Option key={conn.id} value={conn.id}>
                {conn.name} ({conn.db_type})
              </Option>
            ))}
          </Select>
        </Col>
        <Col span={12}>
          <Typography.Text strong>Target Connection</Typography.Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="Select target connection"
            value={targetConnectionId}
            onChange={onTargetConnectionChange}
            disabled={!connections.length}
          >
            {connections.map((conn) => (
              <Option key={conn.id} value={conn.id}>
                {conn.name} ({conn.db_type})
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      {/* Table Selection */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Typography.Text strong>Source Table</Typography.Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder={sourceConnectionId ? 'Select table' : 'Select connection first'}
            value={sourceTable}
            onChange={onSourceTableChange}
            disabled={!sourceConnectionId || isLoadingTables}
            showSearch
            optionFilterProp="children"
          >
            {sourceTables.map((table) => (
              <Option key={table.table_name} value={table.table_name}>
                {table.table_name} {table.row_count ? `(${table.row_count.toLocaleString()} rows)` : ''}
              </Option>
            ))}
          </Select>
        </Col>
        <Col span={12}>
          <Typography.Text strong>Target Table</Typography.Text>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder={targetConnectionId ? 'Select table' : 'Select connection first'}
            value={targetTable}
            onChange={onTargetTableChange}
            disabled={!targetConnectionId || isLoadingTables}
            showSearch
            optionFilterProp="children"
          >
            {targetTables.map((table) => (
              <Option key={table.table_name} value={table.table_name}>
                {table.table_name} {table.row_count ? `(${table.row_count.toLocaleString()} rows)` : ''}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      {/* Compare Button */}
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Button
          type="primary"
          size="large"
          onClick={onCompare}
          disabled={!canCompare}
          loading={isComparing}
        >
          {isComparing ? 'Comparing...' : 'Compare Schemas'}
        </Button>
      </div>

      {/* Table Previews */}
      {(sourceTables.length > 0 || targetTables.length > 0) && (
        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={12}>
            <Typography.Title level={5}>Source Tables</Typography.Title>
            <Table
              dataSource={sourceTables}
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
                onClick: () => onSourceTableChange(record.table_name),
                style: {
                  cursor: 'pointer',
                  backgroundColor: sourceTable === record.table_name ? '#e6f7ff' : undefined,
                },
              })}
            />
          </Col>
          <Col span={12}>
            <Typography.Title level={5}>Target Tables</Typography.Title>
            <Table
              dataSource={targetTables}
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
                onClick: () => onTargetTableChange(record.table_name),
                style: {
                  cursor: 'pointer',
                  backgroundColor: targetTable === record.table_name ? '#e6f7ff' : undefined,
                },
              })}
            />
          </Col>
        </Row>
      )}
    </div>
  );
};
