import { test, expect } from '@playwright/test';

test.describe('Add Database Connections', () => {
  test('add two MySQL connections and test schema comparison', async ({ page }) => {
    // 访问前端页面
    await page.goto('http://localhost:5173');

    console.log('Page loaded, waiting for content...');

    // 等待页面加载
    await expect(page.getByText('DB Compare')).toBeVisible({ timeout: 10000 });

    // 切换到 Connections 标签
    console.log('Clicking Connections tab...');
    await page.getByRole('tab', { name: 'Connections' }).click();

    // 等待 Connections 页面显示
    await page.waitForTimeout(1000);

    // 点击 "Add Connection" 按钮
    console.log('Clicking Add Connection button...');
    await page.getByRole('button', { name: /Add Connection/ }).click();

    // 等待模态框打开
    await page.waitForTimeout(1000);
    await expect(page.getByText('Create Database Connection')).toBeVisible();

    console.log('Modal opened, filling Source connection...');

    // 填充第一个连接 (Source)
    // 连接名称 - 使用 placeholder 定位
    await page.getByPlaceholder('e.g., Production MySQL').fill('MySQL Source');

    // 数据库类型 - 已经是 MySQL，跳过
    console.log('Database type already set to MySQL');

    // 主机
    await page.getByPlaceholder('e.g., localhost').fill('localhost');

    // 端口
    await page.getByPlaceholder('3306').fill('3306');

    // 数据库名
    await page.getByPlaceholder('e.g., mydb').fill('db_source1');

    // 用户名
    await page.getByPlaceholder('e.g., root').fill('dbuser');

    // 密码 - 使用 XPath 定位 password 输入框
    await page.locator('input[type="password"]').first().fill('dbpassword123');

    // 点击创建
    await page.getByRole('button', { name: /Create Connection/ }).first().click();

    // 等待成功消息
    await page.waitForSelector('text=Connection created successfully', { timeout: 15000 });
    console.log('Source connection created!');

    // 等待模态框关闭
    await page.waitForTimeout(1500);

    // 再次点击 "Add Connection" 按钮
    await page.getByRole('button', { name: /Add Connection/ }).click();
    await page.waitForTimeout(1000);

    // 填充第二个连接 (Target)
    console.log('Filling Target connection...');

    await page.getByPlaceholder('e.g., Production MySQL').fill('MySQL Target');
    await page.getByPlaceholder('e.g., localhost').fill('localhost');
    await page.getByPlaceholder('3306').fill('3307');
    await page.getByPlaceholder('e.g., mydb').fill('db_source2');
    await page.getByPlaceholder('e.g., root').fill('dbuser');
    await page.locator('input[type="password"]').first().fill('dbpassword123');

    // 点击创建
    await page.getByRole('button', { name: /Create Connection/ }).first().click();

    // 等待成功消息
    await page.waitForSelector('text=Connection created successfully', { timeout: 15000 });
    console.log('Target connection created!');

    // 等待模态框关闭
    await page.waitForTimeout(1500);

    // 验证两个连接都已显示
    await expect(page.getByText('MySQL Source')).toBeVisible();
    await expect(page.getByText('MySQL Target')).toBeVisible();

    console.log('Both connections added successfully!');

    // 切换到 Schema Comparison 标签
    await page.getByRole('tab', { name: /Schema Comparison/ }).click();
    await page.waitForTimeout(1000);

    console.log('Schema Comparison page ready!');

    // 截图
    await page.screenshot({ path: 'tests/screenshots/connections-added.png' });
    console.log('Final screenshot saved!');
  });
});
