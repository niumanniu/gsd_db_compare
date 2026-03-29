import React, { useState } from 'react';
import { Table, Button, Space, Modal, Typography, Tag, Empty, message } from 'antd';
import { PlusOutlined, DeleteOutlined, EyeOutlined, ThunderboltOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Connection } from '../types';
import { ConnectionForm } from './ConnectionForm';

interface ConnectionListProps {
  connections: Connection[];
  isLoading: boolean;
  onCreate: (data: any) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onGetTables?: (id: number) => Promise<any>;
  onTestConnection?: (data: any) => Promise<any>;
  isCreating: boolean;
  isDeleting: boolean;
}

export const ConnectionList: React.FC<ConnectionListProps> = ({
  connections,
  isLoading,
  onCreate,
  onDelete,
  onGetTables,
  onTestConnection,
  isCreating,
  isDeleting,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tablesModalOpen, setTablesModalOpen] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [tables, setTables] = useState<any[]>([]);
  const [testingId, setTestingId] = useState<number | null>(null);

  const handleDelete = (id: number, name: string) => {
    Modal.confirm({
      title: 'Delete Connection',
      content: `Are you sure you want to delete "${name}"? This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          await onDelete(id);
        } catch (error) {
          console.error('Failed to delete:', error);
        }
      },
    });
  };

  const handleViewTables = async (connection: Connection) => {
    if (!onGetTables) return;

    try {
      const tableList = await onGetTables(connection.id);
      setTables(tableList);
      setSelectedConnection(connection);
      setTablesModalOpen(true);
    } catch (error) {
      console.error('Failed to fetch tables:', error);
    }
  };

  const handleTestConnection = async (connection: Connection) => {
    if (!onTestConnection) return;

    setTestingId(connection.id);
    try {
      const result = await onTestConnection(connection.id);

      if (result.success) {
        message.success(`Connection to "${connection.name}" successful!`);
      } else {
        message.error(`Connection failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Test connection failed:', error);
      message.error('Failed to test connection');
    } finally {
      setTestingId(null);
    }
  };

  const columns: ColumnsType<Connection> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <Typography.Text strong>{name}</Typography.Text>,
    },
    {
      title: 'Type',
      dataIndex: 'db_type',
      key: 'db_type',
      render: (type: string) => (
        <Tag color={type === 'mysql' ? 'blue' : 'orange'}>{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Host',
      dataIndex: 'host',
      key: 'host',
    },
    {
      title: 'Port',
      dataIndex: 'port',
      key: 'port',
      width: 80,
    },
    {
      title: 'Database',
      dataIndex: 'database',
      key: 'database',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: Connection) => (
        <Space>
          <Button
            icon={<ThunderboltOutlined />}
            size="small"
            loading={testingId === record.id}
            onClick={() => handleTestConnection(record)}
          >
            Test
          </Button>
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewTables(record)}
          >
            Tables
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            loading={isDeleting}
            onClick={() => handleDelete(record.id, record.name)}
          >
            Delete
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
          loading={isLoading}
          size="large"
        >
          Add Connection
        </Button>
      </div>

      {connections.length === 0 ? (
        <Empty
          description="No connections yet"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" onClick={() => setIsModalOpen(true)} size="large">
            Create Your First Connection
          </Button>
        </Empty>
      ) : (
        <Table
          columns={columns}
          dataSource={connections}
          loading={isLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          style={{
            backgroundColor: '#ffffff',
            borderRadius: 8,
            overflow: 'hidden',
          }}
        />
      )}

      {/* Create Connection Modal */}
      <Modal
        title="Create Database Connection"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width={600}
      >
        <ConnectionForm
          onSubmit={onCreate}
          onSuccess={() => setIsModalOpen(false)}
          loading={isCreating}
        />
      </Modal>

      {/* View Tables Modal */}
      <Modal
        title={`Tables in ${selectedConnection?.database} (${selectedConnection?.name})`}
        open={tablesModalOpen}
        onCancel={() => setTablesModalOpen(false)}
        footer={null}
        width={800}
      >
        <Table
          dataSource={tables}
          loading={!tables}
          rowKey="table_name"
          pagination={{ pageSize: 20 }}
          columns={[
            { title: 'Table Name', dataIndex: 'table_name', key: 'table_name' },
            { title: 'Type', dataIndex: 'table_type', key: 'table_type' },
            {
              title: 'Rows',
              dataIndex: 'row_count',
              key: 'row_count',
              render: (count: number) => count?.toLocaleString() || 'N/A'
            },
          ]}
        />
      </Modal>
    </>
  );
};
