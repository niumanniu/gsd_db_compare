/** Cron expression builder component with visual UI. */

import React, { useState, useEffect } from 'react';
import { Select, InputNumber, Radio, Space, Card } from 'antd';

interface CronBuilderProps {
  value?: string;
  onChange?: (value: string) => void;
}

export const CronBuilder: React.FC<CronBuilderProps> = ({ value, onChange }) => {
  const [frequency, setFrequency] = useState<'minute' | 'hourly' | 'daily' | 'weekly'>('daily');
  const [hour, setHour] = useState(2);
  const [minute, setMinute] = useState(0);
  const [dayOfWeek, setDayOfWeek] = useState(1);

  // Generate cron expression from selected values
  const generateCron = (): string => {
    switch (frequency) {
      case 'minute':
        return '* * * * *';
      case 'hourly':
        return `${minute} * * * *`;
      case 'daily':
        return `${minute} ${hour} * * *`;
      case 'weekly':
        return `${minute} ${hour} * * ${dayOfWeek}`;
    }
  };

  // Update parent when values change
  useEffect(() => {
    const cron = generateCron();
    if (onChange && (!value || value !== cron)) {
      onChange(cron);
    }
  }, [frequency, hour, minute, dayOfWeek]);

  // Parse existing cron expression on mount
  useEffect(() => {
    if (value) {
      const parts = value.split(' ');
      if (parts.length === 5) {
        const [, hourStr, , , dayOfWeekStr] = parts;
        const parsedMinute = parseInt(parts[0], 10);
        const parsedHour = parseInt(hourStr, 10);
        const parsedDay = parseInt(dayOfWeekStr, 10);

        if (!isNaN(parsedMinute)) setMinute(parsedMinute);
        if (!isNaN(parsedHour)) setHour(parsedHour);
        if (!isNaN(parsedDay)) setDayOfWeek(parsedDay);

        // Determine frequency from pattern
        if (parts[0] === '*' && parts[1] === '*') {
          setFrequency('minute');
        } else if (parts[1] === '*') {
          setFrequency('hourly');
        } else if (parts[4] === '*') {
          setFrequency('daily');
        } else {
          setFrequency('weekly');
        }
      }
    }
  }, []);

  return (
    <Card size="small" title="Cron 表达式生成器" style={{ marginTop: 8 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <span style={{ marginRight: 16 }}>频率:</span>
          <Radio.Group
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            optionType="button"
          >
            <Radio value="minute">每分钟</Radio>
            <Radio value="hourly">每小时</Radio>
            <Radio value="daily">每天</Radio>
            <Radio value="weekly">每周</Radio>
          </Radio.Group>
        </div>

        {frequency === 'hourly' && (
          <div>
            <span style={{ marginRight: 8 }}>在每小时的第</span>
            <InputNumber
              min={0}
              max={59}
              value={minute}
              onChange={(v) => setMinute(v || 0)}
            />
            <span style={{ marginLeft: 8 }}>分钟执行</span>
          </div>
        )}

        {frequency === 'daily' && (
          <div>
            <span style={{ marginRight: 8 }}>在</span>
            <InputNumber
              min={0}
              max={23}
              value={hour}
              onChange={(v) => setHour(v || 0)}
            />
            <span style={{ margin: '0 8px' }}>点</span>
            <InputNumber
              min={0}
              max={59}
              value={minute}
              onChange={(v) => setMinute(v || 0)}
            />
            <span style={{ marginLeft: 8 }}>分执行</span>
          </div>
        )}

        {frequency === 'weekly' && (
          <>
            <div>
              <span style={{ marginRight: 8 }}>在</span>
              <InputNumber
                min={0}
                max={23}
                value={hour}
                onChange={(v) => setHour(v || 0)}
              />
              <span style={{ margin: '0 8px' }}>点</span>
              <InputNumber
                min={0}
                max={59}
                value={minute}
                onChange={(v) => setMinute(v || 0)}
              />
              <span style={{ marginLeft: 8 }}>分执行</span>
            </div>
            <div>
              <span style={{ marginRight: 8 }}>每周</span>
              <Select
                value={dayOfWeek}
                onChange={setDayOfWeek}
                style={{ width: 100 }}
                options={[
                  { label: '周一', value: 1 },
                  { label: '周二', value: 2 },
                  { label: '周三', value: 3 },
                  { label: '周四', value: 4 },
                  { label: '周五', value: 5 },
                  { label: '周六', value: 6 },
                  { label: '周日', value: 0 },
                ]}
              />
              <span style={{ marginLeft: 8 }}>执行</span>
            </div>
          </>
        )}

        <div style={{ padding: '8px 12px', backgroundColor: '#f5f5f5', borderRadius: 4 }}>
          <strong>生成的 Cron 表达式:</strong>{' '}
          <code style={{ color: '#1890ff' }}>{generateCron()}</code>
        </div>

        <div style={{ fontSize: 12, color: '#666' }}>
          <strong>常用示例:</strong>
          <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
            <li><code>* * * * *</code> - 每分钟</li>
            <li><code>0 */2 * * *</code> - 每 2 小时</li>
            <li><code>0 2 * * *</code> - 每天凌晨 2 点</li>
            <li><code>0 9 * * 1</code> - 每周一上午 9 点</li>
          </ul>
        </div>
      </Space>
    </Card>
  );
};
