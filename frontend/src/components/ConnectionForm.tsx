import React from 'react';
import { Form, Input, InputNumber, Select, Button, message } from 'antd';
import type { ConnectionCreate } from '../types';

interface ConnectionFormProps {
  onSubmit: (data: ConnectionCreate) => Promise<void>;
  onSuccess?: () => void;
  loading?: boolean;
}

export const ConnectionForm: React.FC<ConnectionFormProps> = ({
  onSubmit,
  onSuccess,
  loading = false,
}) => {
  const [form] = Form.useForm();

  const handleFinish = async (values: ConnectionCreate) => {
    try {
      await onSubmit(values);
      message.success('Connection created successfully!');
      form.resetFields();
      onSuccess?.();
    } catch (error) {
      console.error('Failed to create connection:', error);
      message.error('Failed to create connection. Please check your credentials.');
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      autoComplete="off"
      size="large"
    >
      <Form.Item
        label="Connection Name"
        name="name"
        rules={[{ required: true, message: 'Please enter a connection name' }]}
      >
        <Input placeholder="e.g., Production MySQL" />
      </Form.Item>

      <Form.Item
        label="Database Type"
        name="db_type"
        initialValue="mysql"
        rules={[{ required: true, message: 'Please select database type' }]}
      >
        <Select>
          <Select.Option value="mysql">MySQL</Select.Option>
          <Select.Option value="oracle">Oracle</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        label="Host"
        name="host"
        rules={[{ required: true, message: 'Please enter host' }]}
      >
        <Input placeholder="e.g., localhost" />
      </Form.Item>

      <Form.Item
        label="Port"
        name="port"
        rules={[{ required: true, message: 'Please enter port' }]}
      >
        <InputNumber style={{ width: '100%' }} min={1} max={65535} placeholder="3306" />
      </Form.Item>

      <Form.Item
        label="Database"
        name="database"
        rules={[{ required: true, message: 'Please enter database name' }]}
      >
        <Input placeholder="e.g., mydb" />
      </Form.Item>

      <Form.Item
        label="Username"
        name="username"
        rules={[{ required: true, message: 'Please enter username' }]}
      >
        <Input placeholder="e.g., root" />
      </Form.Item>

      <Form.Item
        label="Password"
        name="password"
        rules={[{ required: true, message: 'Please enter password' }]}
      >
        <Input.Password placeholder="Enter password" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          {loading ? 'Testing & Creating...' : 'Create Connection'}
        </Button>
      </Form.Item>
    </Form>
  );
};
