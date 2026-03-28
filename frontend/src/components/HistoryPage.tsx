/** Comparison history page with trend chart and history list. */

import React from 'react';
import { Space } from 'antd';
import { TrendChart } from './TrendChart';
import { ComparisonHistory } from './ComparisonHistory';

export const HistoryPage: React.FC = () => {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <TrendChart />
      <ComparisonHistory />
    </Space>
  );
};
