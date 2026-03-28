/** Scheduled tasks management page. */

import React, { useState } from 'react';
import { Button, Card, message, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scheduledApi } from '../api/scheduled';
import { ScheduledTaskList } from './ScheduledTaskList';
import { ScheduledTaskForm } from './ScheduledTaskForm';
import { useConnections } from '../hooks/useConnections';
import type { ScheduledTask, ScheduledTaskCreate } from '../types/scheduled';

export const ScheduledTasksPage: React.FC = () => {
  const [formVisible, setFormVisible] = useState(false);
  const [editingTask, setEditingTask] = useState<ScheduledTaskCreate & { id?: number } | undefined>();
  const queryClient = useQueryClient();

  const { connections } = useConnections();

  const createMutation = useMutation({
    mutationFn: (data: ScheduledTaskCreate) =>
      scheduledApi.create(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      message.success('任务创建成功');
      setFormVisible(false);
      setEditingTask(undefined);
    },
    onError: (error: any) => {
      message.error(`创建任务失败：${error.response?.data?.detail || error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ScheduledTaskCreate }) =>
      scheduledApi.update(id, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-tasks'] });
      message.success('任务更新成功');
      setFormVisible(false);
      setEditingTask(undefined);
    },
    onError: (error: any) => {
      message.error(`更新任务失败：${error.response?.data?.detail || error.message}`);
    },
  });

  const handleCreate = () => {
    setEditingTask(undefined);
    setFormVisible(true);
  };

  const handleEdit = (task: ScheduledTask) => {
    setEditingTask({
      id: task.id,
      name: task.name,
      description: task.description || undefined,
      cron_expression: task.cron_expression,
      source_connection_id: task.source_connection_id,
      target_connection_id: task.target_connection_id,
      tables: task.tables,
      compare_mode: task.compare_mode,
      notification_enabled: task.notification_enabled,
      enabled: task.enabled,
    });
    setFormVisible(true);
  };

  const handleSubmit = (data: ScheduledTaskCreate) => {
    if (editingTask?.id) {
      updateMutation.mutate({ id: editingTask.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <>
      <Card
        title="定时任务管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建任务
          </Button>
        }
      >
        <ScheduledTaskList onEdit={handleEdit} />
      </Card>

      <ScheduledTaskForm
        visible={formVisible}
        editingTask={editingTask}
        connections={connections}
        onSubmit={handleSubmit}
        onCancel={() => {
          setFormVisible(false);
          setEditingTask(undefined);
        }}
      />
    </>
  );
};
