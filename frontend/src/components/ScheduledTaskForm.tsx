/** Scheduled task form component for creating and editing tasks. */

import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, Modal, Switch, Card, Table, Space, Tag, message } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ScheduledTaskCreate, ScheduledTaskUpdate, TableMapping } from '../types/scheduled';
import type { Connection } from '../types';
import { CronBuilder } from './CronBuilder';

const { TextArea } = Input;

interface ScheduledTaskFormProps {
  visible: boolean;
  editingTask?: ScheduledTaskCreate & { id?: number };
  connections: Connection[];
  onSubmit: (data: ScheduledTaskCreate) => void;
  onCancel: () => void;
}

export const ScheduledTaskForm: React.FC<ScheduledTaskFormProps> = ({
  visible,
  editingTask,
  connections,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [tableMappings, setTableMappings] = useState<TableMapping[]>(
    editingTask?.tables || [{ source: '', target: '', critical: false }]
  );

  // Reset form when editing task changes
  useEffect(() => {
    if (editingTask) {
      form.setFieldsValue({
        name: editingTask.name,
        description: editingTask.description,
        cron_expression: editingTask.cron_expression,
        source_connection_id: editingTask.source_connection_id,
        target_connection_id: editingTask.target_connection_id,
        compare_mode: editingTask.compare_mode || 'schema',
        notification_enabled: editingTask.notification_enabled ?? true,
        enabled: editingTask.enabled ?? true,
      });
      setTableMappings(editingTask.tables || []);
    } else {
      form.resetFields();
      setTableMappings([{ source: '', target: '', critical: false }]);
    }
  }, [editingTask, visible]);

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const data: ScheduledTaskCreate = {
        ...values,
        tables: tableMappings.filter((t) => t.source && t.target),
      };

      if (data.tables.length === 0) {
        message.error('请至少添加一个表映射');
        return;
      }

      onSubmit(data);
    });
  };

  const addTableMapping = () => {
    setTableMappings([...tableMappings, { source: '', target: '', critical: false }]);
  };

  const removeTableMapping = (index: number) => {
    setTableMappings(tableMappings.filter((_, i) => i !== index));
  };

  const updateTableMapping = (index: number, field: keyof TableMapping, value: any) => {
    const newMappings = [...tableMappings];
    newMappings[index] = { ...newMappings[index], [field]: value };
    setTableMappings(newMappings);
  };

  // Get table options from selected connections
  const sourceConnection = connections.find((c) => c.id === form.getFieldValue('source_connection_id'));
  const targetConnection = connections.find((c) => c.id === form.getFieldValue('target_connection_id'));

  return (
    <Modal
      title={editingTask ? '编辑定时任务' : '新建定时任务'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      width={900}
      destroyOnClose
    >
      <Form form={form} layout="vertical" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        <Card size="small" title="基本信息" style={{ marginBottom: 16 }}>
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="如：每日架构检查" />
          </Form.Item>

          <Form.Item name="description" label="任务描述">
            <TextArea rows={2} placeholder="描述此任务的用途..." />
          </Form.Item>

          <Form.Item
            name="cron_expression"
            label="Cron 表达式"
            rules={[{ required: true, message: '请输入 Cron 表达式' }]}
            extra="示例：0 2 * * * (每天 2 点), 0 */2 * * * (每 2 小时)"
          >
            <Input placeholder="0 2 * * *" />
          </Form.Item>

          <CronBuilder
            value={form.getFieldValue('cron_expression')}
            onChange={(value) => form.setFieldValue('cron_expression', value)}
          />
        </Card>

        <Card size="small" title="数据库连接" style={{ marginBottom: 16 }}>
          <Form.Item
            name="source_connection_id"
            label="源连接"
            rules={[{ required: true, message: '请选择源连接' }]}
          >
            <Select
              placeholder="选择源数据库连接"
              options={connections.map((c) => ({ label: c.name, value: c.id }))}
              showSearch
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>

          <Form.Item
            name="target_connection_id"
            label="目标连接"
            rules={[{ required: true, message: '请选择目标连接' }]}
          >
            <Select
              placeholder="选择目标数据库连接"
              options={connections.map((c) => ({ label: c.name, value: c.id }))}
              showSearch
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
        </Card>

        <Card size="small" title="比对配置" style={{ marginBottom: 16 }}>
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

          <Form.Item label="通知设置">
            <Form.Item name="notification_enabled" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
            <span style={{ color: '#999', fontSize: 12 }}>发现差异时发送邮件通知</span>
          </Form.Item>
        </Card>

        <Card size="small" title="表映射配置" extra={<Button type="link" onClick={addTableMapping}><PlusOutlined /> 添加映射</Button>}>
          {tableMappings.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
              暂无表映射，请点击上方「添加映射」按钮
            </div>
          ) : (
            <Table
              dataSource={tableMappings.map((m, i) => ({ ...m, key: i }))}
              pagination={false}
              size="small"
              columns={[
                {
                  title: '源表名',
                  dataIndex: 'source',
                  key: 'source',
                  width: 200,
                  render: (_: unknown, record: TableMapping, index: number) => (
                    <Input
                      value={record.source}
                      onChange={(e) => updateTableMapping(index, 'source', e.target.value)}
                      placeholder="源表名"
                    />
                  ),
                },
                {
                  title: '目标表名',
                  dataIndex: 'target',
                  key: 'target',
                  width: 200,
                  render: (_: unknown, record: TableMapping, index: number) => (
                    <Input
                      value={record.target}
                      onChange={(e) => updateTableMapping(index, 'target', e.target.value)}
                      placeholder="目标表名"
                    />
                  ),
                },
                {
                  title: '关键表',
                  dataIndex: 'critical',
                  key: 'critical',
                  width: 100,
                  render: (_: unknown, record: TableMapping, index: number) => (
                    <Select
                      value={record.critical ? 'true' : 'false'}
                      onChange={(val) => updateTableMapping(index, 'critical', val === 'true')}
                      style={{ width: 80 }}
                      options={[
                        { label: '是', value: 'true' },
                        { label: '否', value: 'false' },
                      ]}
                    />
                  ),
                },
                {
                  title: '操作',
                  key: 'action',
                  width: 80,
                  render: (_: unknown, __: unknown, index: number) => (
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => removeTableMapping(index)}
                    />
                  ),
                },
              ]}
            />
          )}
        </Card>
      </Form>
    </Modal>
  );
};
