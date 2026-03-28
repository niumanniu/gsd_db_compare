# Wave 3: 前端 UI

**目标:** 完成前端界面开发

**依赖:** Wave 2 完成 (API 开发)

---

## Task 3.1: 类型定义和 API 客户端

**文件:**
- `frontend/src/types/scheduled.ts`
- `frontend/src/types/history.ts`
- `frontend/src/types/critical.ts`
- `frontend/src/api/scheduled.ts`
- `frontend/src/api/history.ts`
- `frontend/src/api/critical.ts`

### TypeScript 类型定义

```typescript
// frontend/src/types/scheduled.ts

export interface TableMapping {
  source: string;
  target: string;
  critical: boolean;
}

export interface ScheduledTask {
  id: number;
  name: string;
  description: string | null;
  cron_expression: string;
  source_connection_id: number;
  target_connection_id: number;
  tables: TableMapping[];
  compare_mode: 'schema' | 'data' | 'both';
  notification_enabled: boolean;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledTaskCreate {
  name: string;
  description?: string;
  cron_expression: string;
  source_connection_id: number;
  target_connection_id: number;
  tables: TableMapping[];
  compare_mode?: 'schema' | 'data' | 'both';
  notification_enabled?: boolean;
  enabled?: boolean;
}

export interface ScheduledTaskUpdate {
  name?: string;
  description?: string;
  cron_expression?: string;
  tables?: TableMapping[];
  compare_mode?: 'schema' | 'data' | 'both';
  notification_enabled?: boolean;
  enabled?: boolean;
}
```

```typescript
// frontend/src/types/history.ts

export interface HistoryRecord {
  id: number;
  task_id: number | null;
  source_connection_id: number;
  target_connection_id: number;
  source_table: string;
  target_table: string;
  compare_mode: string;
  source_row_count: number | null;
  target_row_count: number | null;
  diff_count: number;
  diff_percentage: number | null;
  has_critical_diffs: boolean;
  started_at: string;
  completed_at: string | null;
  status: string;
  error_message: string | null;
  result_summary: Record<string, unknown> | null;
  created_at: string;
}

export interface TrendDataPoint {
  date: string;
  diff_count: number;
  completed_count: number;
}

export interface TrendResponse {
  period: 'daily' | 'weekly' | 'monthly';
  data_points: TrendDataPoint[];
  total_comparisons: number;
  total_diffs: number;
  avg_diff_count: number;
}

export interface HistoryStats {
  total_comparisons: number;
  completed: number;
  failed: number;
  avg_diff_count: number;
  max_diff_count: number;
  last_24h_comparisons: number;
  last_7d_comparisons: number;
}
```

### API 客户端

```typescript
// frontend/src/api/scheduled.ts

import api from './client';
import type {
  ScheduledTask,
  ScheduledTaskCreate,
  ScheduledTaskUpdate,
} from '../types/scheduled';

export const scheduledApi = {
  getAll: (enabledOnly = false) =>
    api.get<ScheduledTask[]>('/api/scheduled-tasks', { params: { enabled_only: enabledOnly } }),

  getById: (id: number) =>
    api.get<ScheduledTask>(`/api/scheduled-tasks/${id}`),

  create: (data: ScheduledTaskCreate) =>
    api.post<ScheduledTask>('/api/scheduled-tasks', data),

  update: (id: number, data: ScheduledTaskUpdate) =>
    api.put<ScheduledTask>(`/api/scheduled-tasks/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api/scheduled-tasks/${id}`),

  runNow: (id: number) =>
    api.post<{ status: string; message: string }>(`/api/scheduled-tasks/${id}/run`),

  toggle: (id: number) =>
    api.post<ScheduledTask>(`/api/scheduled-tasks/${id}/toggle`),
};
```

```typescript
// frontend/src/api/history.ts

import api from './client';
import type { HistoryRecord, TrendResponse, HistoryStats } from '../types/history';

export const historyApi = {
  getAll: (params: {
    task_id?: number;
    status?: string;
    page?: number;
    limit?: number;
  }) =>
    api.get<HistoryRecord[]>('/api/comparison-history', { params }),

  getById: (id: number) =>
    api.get<HistoryRecord>(`/api/comparison-history/${id}`),

  getTrend: (params: {
    period?: 'daily' | 'weekly' | 'monthly';
    days?: number;
    task_id?: number;
  }) =>
    api.get<TrendResponse>('/api/comparison-history/trend', { params }),

  getStats: (params?: { task_id?: number }) =>
    api.get<HistoryStats>('/api/comparison-history/stats', { params }),
};
```

**验收标准:**
- [ ] TypeScript 类型完整
- [ ] API 客户端封装正确
- [ ] 有错误处理
- [ ] 类型导出正确

---

## Task 3.2: 任务管理 UI

**文件:**
- `frontend/src/components/ScheduledTaskList.tsx`
- `frontend/src/components/ScheduledTaskForm.tsx`
- `frontend/src/components/CronBuilder.tsx` (可选)

### ScheduledTaskList.tsx - 任务列表

```tsx
import React from 'react';
import { Table, Button, Tag, Space, Popconfirm, message } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scheduledApi } from '../api/scheduled';
import type { ScheduledTask } from '../types/scheduled';

export const ScheduledTaskList: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['scheduled-tasks'],
    queryFn: () => scheduledApi.getAll(),
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => scheduledApi.toggle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      message.success('任务状态已更新');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => scheduledApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      message.success('任务已删除');
    },
  });

  const runNowMutation = useMutation({
    mutationFn: (id: number) => scheduledApi.runNow(id),
    onSuccess: () => {
      message.success('任务已启动执行');
    },
  });

  const columns: ColumnsType<ScheduledTask> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: 'Cron 表达式', dataIndex: 'cron_expression', key: 'cron_expression' },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>{enabled ? '已启用' : '已禁用'}</Tag>
      ),
    },
    {
      title: '上次执行',
      dataIndex: 'last_run_at',
      key: 'last_run_at',
      render: (date) => date ? new Date(date).toLocaleString() : '从未',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => runNowMutation.mutate(record.id)}>
            立即执行
          </Button>
          <Button size="small" onClick={() => toggleMutation.mutate(record.id)}>
            {record.enabled ? '禁用' : '启用'}
          </Button>
          <Button size="small">编辑</Button>
          <Popconfirm
            title="确定删除此任务？"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary">新建定时任务</Button>
      </div>
      <Table
        columns={columns}
        dataSource={tasks}
        loading={isLoading}
        rowKey="id"
      />
    </div>
  );
};
```

### ScheduledTaskForm.tsx - 任务表单

```tsx
import React from 'react';
import { Form, Input, Select, Button, Modal, Card } from 'antd';
import type { ScheduledTaskCreate, TableMapping } from '../types/scheduled';

interface Props {
  visible: boolean;
  editingTask?: ScheduledTask;
  connections: Connection[];
  onSubmit: (data: ScheduledTaskCreate) => void;
  onCancel: () => void;
}

export const ScheduledTaskForm: React.FC<Props> = ({
  visible,
  editingTask,
  connections,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      onSubmit(values);
    });
  };

  return (
    <Modal
      title={editingTask ? '编辑定时任务' : '新建定时任务'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      width={800}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="任务名称"
          rules={[{ required: true, message: '请输入任务名称' }]}
        >
          <Input placeholder="如：每日架构检查" />
        </Form.Item>

        <Form.Item
          name="cron_expression"
          label="Cron 表达式"
          rules={[{ required: true, message: '请输入 Cron 表达式' }]}
          extra="如：0 2 * * * (每天 2 点), 0 */2 * * * (每 2 小时)"
        >
          <Input placeholder="0 2 * * *" />
        </Form.Item>

        <Form.Item
          name="source_connection_id"
          label="源连接"
          rules={[{ required: true, message: '请选择源连接' }]}
        >
          <Select
            options={connections.map((c) => ({ label: c.name, value: c.id }))}
          />
        </Form.Item>

        <Form.Item
          name="target_connection_id"
          label="目标连接"
          rules={[{ required: true, message: '请选择目标连接' }]}
        >
          <Select
            options={connections.map((c) => ({ label: c.name, value: c.id }))}
          />
        </Form.Item>

        <Form.Item
          name="compare_mode"
          label="比对模式"
          initialValue="schema"
        >
          <Select>
            <Select.Option value="schema">架构比对</Select.Option>
            <Select.Option value="data">数据比对</Select.Option>
            <Select.Option value="both">架构 + 数据</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="表映射">
          {/* 表映射配置组件 */}
        </Form.Item>
      </Form>
    </Modal>
  );
};
```

### CronBuilder.tsx - Cron 生成器 (可选)

```tsx
import React, { useState } from 'react';
import { Select, InputNumber, Radio, Space } from 'antd';

// 简化的 Cron 生成器
export const CronBuilder: React.FC<{
  value?: string;
  onChange?: (value: string) => void;
}> = ({ value, onChange }) => {
  const [frequency, setFrequency] = useState<'minute' | 'hourly' | 'daily' | 'weekly'>('daily');
  const [hour, setHour] = useState(2);
  const [minute, setMinute] = useState(0);

  // 根据选择生成 Cron 表达式
  const generateCron = () => {
    switch (frequency) {
      case 'minute':
        return '* * * * *';
      case 'hourly':
        return `${minute} * * * *`;
      case 'daily':
        return `${minute} ${hour} * * *`;
      case 'weekly':
        return `${minute} ${hour} * * 1`; // 每周一
    }
  };

  return (
    <Space>
      <Radio.Group value={frequency} onChange={(e) => setFrequency(e.target.value)}>
        <Radio value="minute">每分钟</Radio>
        <Radio value="hourly">每小时</Radio>
        <Radio value="daily">每天</Radio>
        <Radio value="weekly">每周</Radio>
      </Radio.Group>
      {frequency === 'daily' && (
        <>
          <span>在</span>
          <InputNumber min={0} max={23} value={hour} onChange={setHour} />
          <span>点</span>
          <InputNumber min={0} max={59} value={minute} onChange={setMinute} />
          <span>分</span>
        </>
      )}
      <div>生成的表达式：{generateCron()}</div>
    </Space>
  );
};
```

**验收标准:**
- [ ] 列表可刷新
- [ ] 表单验证正确
- [ ] 操作反馈清晰 (message/toast)
- [ ] 状态同步及时
- [ ] Cron 表达式显示清晰

---

## Task 3.3: 历史查看 UI

**文件:**
- `frontend/src/components/ComparisonHistory.tsx`
- `frontend/src/components/TrendChart.tsx`

### ComparisonHistory.tsx - 历史记录列表

```tsx
import React, { useState } from 'react';
import { Table, Tag, Select, Space, DatePicker, Button } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../api/history';
import type { HistoryRecord } from '../types/history';

export const ComparisonHistory: React.FC = () => {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>();
  const LIMIT = 20;

  const { data: records, isLoading } = useQuery({
    queryKey: ['history', page, status],
    queryFn: () => historyApi.getAll({ page, status, limit: LIMIT }),
  });

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '源表',
      dataIndex: 'source_table',
      key: 'source_table',
    },
    {
      title: '目标表',
      dataIndex: 'target_table',
      key: 'target_table',
    },
    {
      title: '差异数',
      dataIndex: 'diff_count',
      key: 'diff_count',
      render: (count: number, record: HistoryRecord) => (
        <Tag color={record.has_critical_diffs ? 'red' : count > 0 ? 'orange' : 'green'}>
          {count}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          completed: 'green',
          running: 'blue',
          failed: 'red',
          pending: 'gray',
        };
        return <Tag color={colorMap[status]}>{status}</Tag>;
      },
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
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
            ]}
          />
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={records}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize: LIMIT,
          onChange: setPage,
        }}
      />
    </div>
  );
};
```

### TrendChart.tsx - 趋势图表

```tsx
import React from 'react';
import { Line } from '@ant-design/charts';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../api/history';

export const TrendChart: React.FC = () => {
  const { data: trend } = useQuery({
    queryKey: ['history-trend'],
    queryFn: () => historyApi.getTrend({ period: 'daily', days: 30 }),
  });

  const chartData = trend?.data_points.map((point) => ({
    date: point.date,
    差异数量: point.diff_count,
    比对次数: point.completed_count,
  })) || [];

  const config = {
    data: chartData,
    xField: 'date',
    yField: '数值',
    seriesField: '类型',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  return (
    <div>
      <h3>差异趋势 (近 30 天)</h3>
      <Line {...config} />
    </div>
  );
};
```

**验收标准:**
- [ ] 列表分页正常
- [ ] 图表渲染正确
- [ ] 筛选功能工作
- [ ] 响应式设计

---

## Task 3.4: 关键表标记 UI

**文件:**
- `frontend/src/components/CriticalTableManager.tsx`

### CriticalTableManager.tsx

```tsx
import React from 'react';
import { Table, Button, Tag, Modal, message, Checkbox } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { criticalApi } from '../api/critical';

interface Props {
  connectionId: number;
  tables: string[]; // 当前连接的所有表
}

export const CriticalTableManager: React.FC<Props> = ({
  connectionId,
  tables,
}) => {
  const queryClient = useQueryClient();
  const [selectedTables, setSelectedTables] = React.useState<string[]>([]);

  const { data: criticalTables } = useQuery({
    queryKey: ['critical-tables', connectionId],
    queryFn: () => criticalApi.getAll(connectionId),
  });

  const markMutation = useMutation({
    mutationFn: (tableName: string) =>
      criticalApi.create({ connection_id: connectionId, table_name: tableName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['critical-tables', connectionId] });
      message.success('已标记为关键表');
    },
  });

  const unmarkMutation = useMutation({
    mutationFn: (id: number) => criticalApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['critical-tables', connectionId] });
      message.success('已取消关键表标记');
    },
  });

  const criticalTableNames = new Set(criticalTables?.map((t) => t.table_name));

  const columns = [
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
    },
    {
      title: '状态',
      key: 'is_critical',
      render: (_: unknown, record: { table_name: string }) => (
        <Tag color={criticalTableNames.has(record.table_name) ? 'red' : 'default'}>
          {criticalTableNames.has(record.table_name) ? '关键表' : '普通表'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: { table_name: string }) => (
        <Button
          size="small"
          onClick={() => {
            if (criticalTableNames.has(record.table_name)) {
              // 取消标记
              const critical = criticalTables?.find((t) => t.table_name === record.table_name);
              if (critical) unmarkMutation.mutate(critical.id);
            } else {
              markMutation.mutate(record.table_name);
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
    <div>
      <h3>关键表管理</h3>
      <Table columns={columns} dataSource={dataSource} rowKey="key" size="small" />
    </div>
  );
};
```

**集成到 TableBrowser:**

```tsx
// 在 TableBrowser.tsx 中添加关键表标记功能
<Button
  icon={<StarOutlined />}
  onClick={() => setShowCriticalManager(true)}
>
  关键表管理
</Button>
```

**验收标准:**
- [ ] 标记功能可用
- [ ] 高亮显示清晰
- [ ] 状态同步及时
- [ ] 与 TableBrowser 集成

---

## Wave 3 验收清单

- [ ] 3.1 TypeScript 类型和 API 客户端完整
- [ ] 3.2 任务管理 UI 功能完整
- [ ] 3.3 历史查看 UI 和趋势图表正常
- [ ] 3.4 关键表标记 UI 集成完成
- [ ] 前后端联调通过
- [ ] 无明显 UI/UX 问题
- [ ] 响应式设计正常
