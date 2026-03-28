/** Critical table manager component for marking and managing critical tables. */

import React, { useState } from 'react';
import { Table, Button, Tag, Modal, message, Space, Typography, Card } from 'antd';
import { StarOutlined, StarFilled } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { criticalApi } from '../api/critical';
import type { CriticalTable, CriticalTableCreate } from '../types/critical';

const { Text } = Typography;

interface CriticalTableManagerProps {
  connectionId: number;
  tables: string[]; // All table names for the connection
}

export const CriticalTableManager: React.FC<CriticalTableManagerProps> = ({
  connectionId,
  tables,
}) => {
  const queryClient = useQueryClient();
  const [modalVisible, setModalVisible] = useState(false);

  const { data: criticalTables, isLoading } = useQuery({
    queryKey: ['critical-tables', connectionId],
    queryFn: () => criticalApi.getAll(connectionId).then((r) => r.data),
    enabled: !!connectionId,
  });

  const markMutation = useMutation({
    mutationFn: (data: CriticalTableCreate) =>
      criticalApi.create(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['critical-tables', connectionId] });
      message.success('已标记为关键表');
    },
    onError: () => {
      message.error('标记失败');
    },
  });

  const unmarkMutation = useMutation({
    mutationFn: (id: number) => criticalApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['critical-tables', connectionId] });
      message.success('已取消关键表标记');
    },
    onError: () => {
      message.error('取消标记失败');
    },
  });

  const criticalTableNames = new Set(criticalTables?.map((t) => t.table_name) || []);

  const columns = [
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
      width: 300,
      sorter: (a: { table_name: string }, b: { table_name: string }) =>
        a.table_name.localeCompare(b.table_name),
    },
    {
      title: '状态',
      key: 'is_critical',
      width: 120,
      render: (_: unknown, record: { table_name: string }) => (
        <Tag icon={criticalTableNames.has(record.table_name) ? <StarFilled /> : null} color={criticalTableNames.has(record.table_name) ? 'red' : 'default'}>
          {criticalTableNames.has(record.table_name) ? '关键表' : '普通表'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: unknown, record: { table_name: string }) => (
        <Button
          size="small"
          type={criticalTableNames.has(record.table_name) ? 'default' : 'primary'}
          icon={criticalTableNames.has(record.table_name) ? <StarOutlined /> : <StarFilled />}
          onClick={() => {
            if (criticalTableNames.has(record.table_name)) {
              const critical = criticalTables?.find((t) => t.table_name === record.table_name);
              if (critical) unmarkMutation.mutate(critical.id);
            } else {
              markMutation.mutate({ connection_id: connectionId, table_name: record.table_name });
            }
          }}
        >
          {criticalTableNames.has(record.table_name) ? '取消标记' : '标记为关键'}
        </Button>
      ),
    },
  ];

  const dataSource = tables.map((name) => ({ key: name, table_name: name }));

  return (
    <>
      <Card
        title={
          <Space>
            <StarOutlined />
            <span>关键表管理</span>
          </Space>
        }
        size="small"
        extra={
          <Button size="small" onClick={() => setModalVisible(true)}>
            管理关键表
          </Button>
        }
      >
        {criticalTables && criticalTables.length > 0 ? (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">当前连接的关键表 ({criticalTables.length} 个):</Text>
            <Space wrap>
              {criticalTables.map((t) => (
                <Tag key={t.id} color="red" icon={<StarFilled />}>
                  {t.table_name}
                </Tag>
              ))}
            </Space>
          </Space>
        ) : (
          <Text type="secondary">暂无关键表</Text>
        )}
      </Card>

      <Modal
        title="关键表管理"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Table
          columns={columns}
          dataSource={dataSource}
          loading={isLoading}
          rowKey="key"
          pagination={{ pageSize: 10 }}
          scroll={{ y: 400 }}
        />
      </Modal>
    </>
  );
};
