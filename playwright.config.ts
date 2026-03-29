import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120000,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true, // 无头模式运行
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  reporter: 'list',
});
