/** Comparison history list component with filtering and pagination. */

import React, { useState } from 'react';
import { Table, Tag, Select, Space, Typography, Card } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../api/history';
import type { HistoryRecord } from '../types/history';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

export const ComparisonHistory: React.FC = () => {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>();
  const [taskId, setTaskId] = useState<number | undefined>();
  const LIMIT = 20;

  const { data: response, isLoading } = useQuery({
    queryKey: ['history', page, status, taskId],
    queryFn: () =>
      historyApi
        .getAll({ page, status, task_id: taskId, limit: LIMIT })
        .then((r) => r.data),
    select: (data) => ({
      records: data,
      total: data.length,
    }),
  });

  const columns: ColumnsType<HistoryRecord> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '任务',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 80,
      render: (taskId: number | null) =>
        taskId ? <Tag color="blue">定时任务</Tag> : <Tag>手动</Tag>,
    },
    {
      title: '源表',
      dataIndex: 'source_table',
      key: 'source_table',
      width: 150,
      ellipsis: true,
    },
    {
      title: '目标表',
      dataIndex: 'target_table',
      key: 'target_table',
      width: 150,
      ellipsis: true,
    },
    {
      title: '模式',
      dataIndex: 'compare_mode',
      key: 'compare_mode',
      width: 80,
      render: (mode: string) => {
        const modeMap: Record<string, string> = {
          schema: '架构',
          data: '数据',
          both: '两者',
        };
        return <Tag>{modeMap[mode] || mode}</Tag>;
      },
    },
    {
      title: '差异数',
      dataIndex: 'diff_count',
      key: 'diff_count',
      width: 100,
      render: (count: number, record: HistoryRecord) => (
        <Tag
          color={
            record.has_critical_diffs
              ? 'red'
              : count > 0
              ? 'orange'
              : 'green'
          }
        >
          {count}
        </Tag>
      ),
    },
    {
      title: '差异率',
      dataIndex: 'diff_percentage',
      key: 'diff_percentage',
      width: 90,
      render: (pct: number | null) =>
        pct !== null ? `${pct.toFixed(2)}%` : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          completed: 'green',
          running: 'blue',
          failed: 'red',
          pending: 'gray',
        };
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (msg: string | null) =>
        msg ? (
          <Text type="danger" ellipsis={{ tooltip: msg }}>
            {msg}
          </Text>
        ) : (
          '-'
        ),
    },
  ];

  return (
    <Card
      title="比对历史"
      extra={
        <Space>
          <Select
            placeholder="筛选状态"
            allowClear
            style={{ width: 120 }}
            onChange={setStatus}
            options={[
              { label: '完成', value: 'completed' },
              { label: '失败', value: 'failed' },
              { label: '运行中', value: 'running' },
              { label: '待处理', value: 'pending' },
            ]}
          />
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={response?.records || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize: LIMIT,
          onChange: setPage,
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
        scroll={{ x: 1200 }}
      />
    </Card>
  );
};
