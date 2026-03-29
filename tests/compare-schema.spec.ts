import { test, expect } from '@playwright/test';

test.describe('Add Database Connections and Compare', () => {
  test('add two MySQL connections and test schema comparison', async ({ page }) => {
    // 访问前端页面
    await page.goto('http://localhost:5173');

    console.log('Page loaded, waiting for content...');

    // 等待页面加载
    await expect(page.getByText('DB Compare')).toBeVisible({ timeout: 10000 });

    // 切换到 Connections 标签
    console.log('Clicking Connections tab...');
    await page.getByRole('tab', { name: 'Connections' }).click();
    await page.waitForTimeout(1000);

    // 如果已有连接，先删除
    const existingConnections = await page.getByText('MySQL Source').count();
    if (existingConnections > 0) {
      console.log('Found existing connections, skipping creation');
    } else {
      // 点击 "Add Connection" 按钮
      console.log('Clicking Add Connection button...');
      await page.getByRole('button', { name: /Add Connection/ }).click();
      await page.waitForTimeout(1000);

      // 填充第一个连接 (Source)
      console.log('Filling Source connection...');
      await page.getByPlaceholder('e.g., Production MySQL').fill('MySQL Source');
      await page.getByPlaceholder('e.g., localhost').fill('localhost');
      await page.getByPlaceholder('3306').fill('3306');
      await page.getByPlaceholder('e.g., mydb').fill('db_source1');
      await page.getByPlaceholder('e.g., root').fill('dbuser');
      await page.locator('input[type="password"]').first().fill('dbpassword123');

      // 点击创建
      await page.getByRole('button', { name: /Create Connection/ }).first().click();
      await page.waitForSelector('text=Connection created successfully', { timeout: 15000 });
      console.log('Source connection created!');
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
      await page.waitForSelector('text=Connection created successfully', { timeout: 15000 });
      console.log('Target connection created!');
      await page.waitForTimeout(1500);
    }

    // 验证两个连接都已显示
    await expect(page.getByText('MySQL Source')).toBeVisible();
    await expect(page.getByText('MySQL Target')).toBeVisible();
    console.log('Both connections verified!');

    // 切换到 Schema Comparison 标签
    console.log('Switching to Schema Comparison tab...');
    await page.getByRole('tab', { name: /Schema Comparison/ }).click();
    await page.waitForTimeout(2000);

    // 选择源连接和表 - 使用文本定位
    console.log('Selecting source connection and table...');
    // 点击包含 "Select source connection" 文本的元素
    await page.getByText('Select source connection').click();
    await page.waitForTimeout(1000);
    await page.getByText('MySQL Source').first().click();
    await page.waitForTimeout(1500);

    await page.getByText('Select table').first().click();
    await page.waitForTimeout(500);
    await page.getByText('users').first().click();
    await page.waitForTimeout(500);

    // 选择目标连接和表
    console.log('Selecting target connection and table...');
    await page.getByText('Select target connection').click();
    await page.waitForTimeout(1000);
    await page.getByText('MySQL Target').first().click();
    await page.waitForTimeout(1500);

    await page.getByText('Select table').nth(1).click();
    await page.waitForTimeout(500);
    await page.getByText('users').first().click();
    await page.waitForTimeout(500);

    // 点击比较按钮
    console.log('Clicking Compare Schemas button...');
    await page.getByRole('button', { name: /Compare Schemas/ }).click();

    // 等待比较完成
    console.log('Waiting for comparison results...');
    await page.waitForSelector('text=Comparison Results, text=/ADDED|REMOVED|MODIFIED/', { timeout: 30000 });
    await page.waitForTimeout(2000);

    // 验证比较结果
    console.log('Verifying comparison results...');
    const diffFound = await page.getByText(/phone|idx_phone/).count() > 0;
    expect(diffFound).toBeTruthy();
    console.log('Schema differences detected correctly!');

    // 截图
    await page.screenshot({ path: 'tests/screenshots/schema-comparison-result.png' });
    console.log('Comparison result screenshot saved!');
  });
});
