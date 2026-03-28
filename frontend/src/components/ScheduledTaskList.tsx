/** Scheduled task list component with management actions. */

import React from 'react';
import { Table, Button, Tag, Space, Popconfirm, message, Typography } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scheduledApi } from '../api/scheduled';
import type { ScheduledTask } from '../types/scheduled';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface ScheduledTaskListProps {
  onEdit?: (task: ScheduledTask) => void;
}

export const ScheduledTaskList: React.FC<ScheduledTaskListProps> = ({ onEdit }) => {
  const queryClient = useQueryClient();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['scheduled-tasks'],
    queryFn: () => scheduledApi.getAll().then((r) => r.data),
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => scheduledApi.toggle(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      message.success('任务状态已更新');
    },
    onError: () => {
      message.error('更新任务状态失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => scheduledApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      message.success('任务已删除');
    },
    onError: () => {
      message.error('删除任务失败');
    },
  });

  const runNowMutation = useMutation({
    mutationFn: (id: number) => scheduledApi.runNow(id).then((r) => r.data),
    onSuccess: () => {
      message.success('任务已启动执行');
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
    },
    onError: (error: any) => {
      message.error(`启动任务失败：${error.response?.data?.detail || error.message}`);
    },
  });

  const columns: ColumnsType<ScheduledTask> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (name, record) => (
        <div>
          <Text strong>{name}</Text>
          {record.description && (
            <div style={{ fontSize: 12, color: '#999' }}>{record.description}</div>
          )}
        </div>
      ),
    },
    {
      title: 'Cron 表达式',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      width: 120,
      render: (cron) => <code style={{ backgroundColor: '#f5f5f5', padding: '2px 6px', borderRadius: 4 }}>{cron}</code>,
    },
    {
      title: '比对模式',
      dataIndex: 'compare_mode',
      key: 'compare_mode',
      width: 100,
      render: (mode) => {
        const modeMap: Record<string, string> = {
          schema: '架构',
          data: '数据',
          both: '架构 + 数据',
        };
        return <Tag>{modeMap[mode] || mode}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>{enabled ? '已启用' : '已禁用'}</Tag>
      ),
    },
    {
      title: '表数量',
      key: 'table_count',
      width: 80,
      render: (_, record) => record.tables.length,
    },
    {
      title: '上次执行',
      dataIndex: 'last_run_at',
      key: 'last_run_at',
      width: 160,
      render: (date) => date ? new Date(date).toLocaleString('zh-CN') : <Text type="secondary">从未</Text>,
    },
    {
      title: '下次执行',
      dataIndex: 'next_run_at',
      key: 'next_run_at',
      width: 160,
      render: (date) => date ? new Date(date).toLocaleString('zh-CN') : <Text type="secondary">-</Text>,
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 280,
      render: (_, record) => (
        <Space size="small" wrap>
          <Button
            size="small"
            onClick={() => runNowMutation.mutate(record.id)}
            disabled={!record.enabled}
          >
            立即执行
          </Button>
          <Button
            size="small"
            onClick={() => toggleMutation.mutate(record.id)}
          >
            {record.enabled ? '禁用' : '启用'}
          </Button>
          <Button
            size="small"
            onClick={() => onEdit?.(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此任务？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Table
        columns={columns}
        dataSource={tasks}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />
    </div>
  );
};
