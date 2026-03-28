/** Trend chart component for visualizing comparison history over time. */

import React from 'react';
import { Card, Select, Space } from 'antd';
import { Line } from '@ant-design/charts';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../api/history';

export const TrendChart: React.FC = () => {
  const [period, setPeriod] = React.useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [days, setDays] = React.useState(30);

  const { data: trend, isLoading } = useQuery({
    queryKey: ['history-trend', period, days],
    queryFn: () =>
      historyApi.getTrend({ period, days }).then((r) => r.data),
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
    color: ['#1890ff', '#faad14'],
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      showMarkers: true,
    },
    xAxis: {
      label: {
        autoRotate: true,
        autoHide: false,
      },
    },
    yAxis: {
      min: 0,
    },
  };

  return (
    <Card
      title="差异趋势"
      extra={
        <Space size="small">
          <Select
            value={period}
            onChange={(val) => setPeriod(val)}
            style={{ width: 100 }}
            options={[
              { label: '每日', value: 'daily' },
              { label: '每周', value: 'weekly' },
              { label: '每月', value: 'monthly' },
            ]}
          />
          <Select
            value={days}
            onChange={(val) => setDays(val)}
            style={{ width: 100 }}
            options={[
              { label: '7 天', value: 7 },
              { label: '30 天', value: 30 },
              { label: '90 天', value: 90 },
            ]}
          />
        </Space>
      }
      loading={isLoading}
    >
      {chartData.length > 0 ? (
        <Line {...config} />
      ) : (
        <div
          style={{
            textAlign: 'center',
            padding: '40px 0',
            color: '#999',
          }}
        >
          暂无趋势数据
        </div>
      )}

      {trend && (
        <Space split={<span>|</span>} style={{ marginTop: 16, fontSize: 13 }}>
          <span>
            <strong>总比对次数:</strong> {trend.total_comparisons}
          </span>
          <span>
            <strong>总差异数:</strong> {trend.total_diffs}
          </span>
          <span>
            <strong>平均差异:</strong> {trend.avg_diff_count.toFixed(1)}
          </span>
        </Space>
      )}
    </Card>
  );
};
