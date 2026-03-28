# Phase 4: Advanced Features - Verification Document

**Phase:** 04
**Name:** Scheduling & Alerting
**Created:** 2026-03-28
**Updated:** 2026-03-28
**Status:** COMPLETE - All Waves 1-4 Done

---

## Wave 3 (Frontend UI) Status

### TypeScript Types
- [x] scheduled.ts - ScheduledTask, TableMapping types
- [x] history.ts - HistoryRecord, TrendResponse types
- [x] critical.ts - CriticalTable types
- [x] API clients - scheduledApi, historyApi, criticalApi

### UI Components
- [x] CronBuilder.tsx - Visual cron expression generator
- [x] ScheduledTaskList.tsx - Task table with actions
- [x] ScheduledTaskForm.tsx - Create/edit modal with table mapping
- [x] ScheduledTasksPage.tsx - Integrated task management page
- [x] ComparisonHistory.tsx - History list with filtering
- [x] TrendChart.tsx - Line chart for trend visualization
- [x] HistoryPage.tsx - Integrated history view
- [x] CriticalTableManager.tsx - Star icon marking UI

### Frontend Build
- [x] npm run build - SUCCESS
- [x] TypeScript compilation - No errors
- [x] All components integrated into App.tsx

---

## UAT Checklist

### 1. 定时任务管理

| ID | 测试项 | 预期结果 | 状态 |
|----|--------|----------|------|
| UAT-01 | 创建定时任务 | 任务成功创建，Cron 表达式验证通过 | ⬜ |
| UAT-02 | 使用快捷 Cron 选择 | 每分钟/每小时/每天等预设正确生成表达式 | ⬜ |
| UAT-03 | 编辑定时任务 | 任务信息更新成功 | ⬜ |
| UAT-04 | 启用/禁用任务 | 任务状态切换成功，调度器同步 | ⬜ |
| UAT-05 | 手动执行任务 | 任务立即执行，返回执行状态 | ⬜ |
| UAT-06 | 删除定时任务 | 任务从数据库和调度器移除 | ⬜ |
| UAT-07 | 服务重启后任务恢复 | 定时任务自动加载并继续执行 | ⬜ |

### 2. 邮件通知

| ID | 测试项 | 预期结果 | 状态 |
|----|--------|----------|------|
| UAT-08 | 配置 SMTP 服务器 | 配置保存成功，连接测试通过 | ⬜ |
| UAT-09 | 发送测试邮件 | 测试邮件成功接收 | ⬜ |
| UAT-010 | 关键表差异告警 | 有关键表差异时发送邮件 | ⬜ |
| UAT-011 | 非关键表差异 | 无关键表差异时不发送邮件 | ⬜ |
| UAT-012 | 多收件人通知 | 多个邮箱地址都收到邮件 | ⬜ |
| UAT-013 | HTML 邮件格式 | 邮件内容格式正确，链接可点击 | ⬜ |
| UAT-014 | 发送失败重试 | 发送失败后有重试机制 | ⬜ |

### 3. 历史记录

| ID | 测试项 | 预期结果 | 状态 |
|----|--------|----------|------|
| UAT-015 | 历史记录列表 | 按时间倒序显示，分页正确 | ⬜ |
| UAT-016 | 状态筛选 | 按 completed/failed/pending 筛选正确 | ⬜ |
| UAT-017 | 任务筛选 | 按特定任务 ID 筛选正确 | ⬜ |
| UAT-018 | 趋势图表 | 显示近 30 天差异数量变化 | ⬜ |
| UAT-019 | 统计摘要 | 总数/完成率/平均差异数正确 | ⬜ |
| UAT-020 | 详情查看 | 点击查看显示完整比对结果 | ⬜ |

### 4. 关键表管理

| ID | 测试项 | 预期结果 | 状态 |
|----|--------|----------|------|
| UAT-021 | 标记关键表 | 表标记成功，数据库保存 | ⬜ |
| UAT-022 | 取消标记 | 标记移除成功 | ⬜ |
| UAT-023 | 关键表列表 | 按连接查询返回正确列表 | ⬜ |
| UAT-024 | UI 高亮显示 | 关键表在列表中红色高亮 | ⬜ |
| UAT-025 | 重复标记处理 | 同一表不能重复标记 | ⬜ |

### 5. 集成场景

| ID | 测试项 | 预期结果 | 状态 |
|----|--------|----------|------|
| UAT-026 | 完整工作流 | 创建任务 → 执行 → 产生差异 → 邮件告警 → 历史记录 | ⬜ |
| UAT-027 | 并发任务 | 多个定时任务同时执行不冲突 | ⬜ |
| UAT-028 | 大数据量历史 | 大量历史记录下分页查询性能良好 | ⬜ |

---

## Technical Verification

### 1. APScheduler

| ID | 验证项 | 预期结果 | 状态 |
|----|--------|----------|------|
| TECH-01 | 调度器启动 | FastAPI 启动时调度器自动初始化 | ⬜ |
| TECH-02 | 调度器关闭 | FastAPI 关闭时调度器优雅停止 | ⬜ |
| TECH-03 | 任务持久化 | 任务保存到 SQLAlchemyJobStore | ⬜ |
| TECH-04 | Cron 解析 | 标准 5 字段 Cron 表达式正确解析 | ⬜ |
| TECH-05 | 任务恢复 | 重启后从数据库加载所有启用任务 | ⬜ |
| TECH-06 | 时区处理 | 任务执行时间与时区配置一致 | ⬜ |

### 2. 数据库迁移

| ID | 验证项 | 预期结果 | 状态 |
|----|--------|----------|------|
| TECH-07 | Migration 执行 | `alembic upgrade head` 成功 | ⬜ |
| TECH-08 | Migration 回滚 | `alembic downgrade -1` 成功 | ⬜ |
| TECH-09 | 表结构正确 | 所有表/索引/外键创建成功 | ⬜ |
| TECH-10 | 数据完整性 | 外键约束生效，级联删除正常 | ⬜ |

### 3. API 测试

| ID | 验证项 | 预期结果 | 状态 |
|----|--------|----------|------|
| TECH-11 | Swagger 文档 | `/docs` 显示所有新增端点 | ⬜ |
| TECH-12 | 参数验证 | 无效参数返回 422 | ⬜ |
| TECH-13 | 错误处理 | 404/400/500 错误响应正确 | ⬜ |
| TECH-14 | 认证授权 | (如有) 权限验证正常 | ⬜ |

### 4. 性能测试

| ID | 验证项 | 预期结果 | 状态 |
|----|--------|----------|------|
| TECH-15 | 历史查询响应 | 1000 条记录下查询 <500ms | ⬜ |
| TECH-16 | 趋势数据计算 | 30 天趋势数据生成 <200ms | ⬜ |
| TECH-17 | 邮件发送时间 | 单次发送 <5s | ⬜ |
| TECH-18 | 调度器内存 | 空闲时 <50MB | ⬜ |

### 5. Celery 迁移

| ID | 验证项 | 预期结果 | 状态 |
|----|--------|----------|------|
| TECH-19 | Celery 移除 | `celery_config.py` 和 `app/worker.py` 删除 | ✅ |
| TECH-20 | 依赖清理 | `pyproject.toml` 无 celery 依赖 | ✅ |
| TECH-21 | 无遗留引用 | 代码中无 `import celery` 引用 | ✅ |
| TECH-22 | 功能正常 | 原有比对功能正常工作 | ✅ |

---

## Test Scripts

### 自动化测试运行

```bash
# 后端单元测试
cd backend
pytest tests/test_scheduled_tasks.py -v
pytest tests/test_history.py -v
pytest tests/test_critical_tables.py -v
pytest tests/test_notifications.py -v

# 集成测试
pytest tests/integration/test_phase4.py -v

# 覆盖率报告
pytest --cov=app --cov-report=html
```

### 手动测试脚本

```bash
# 1. 创建测试连接
curl -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Source",
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "test_db",
    "username": "root",
    "password": "password"
  }'

# 2. 创建定时任务
curl -X POST http://localhost:8000/api/scheduled-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Check",
    "cron_expression": "0 2 * * *",
    "source_connection_id": 1,
    "target_connection_id": 2,
    "tables": [{"source": "users", "target": "users", "critical": true}],
    "compare_mode": "schema"
  }'

# 3. 手动执行任务
curl -X POST http://localhost:8000/api/scheduled-tasks/1/run

# 4. 查询历史记录
curl "http://localhost:8000/api/comparison-history?page=1&limit=20"

# 5. 获取趋势数据
curl "http://localhost:8000/api/comparison-history/trend?period=daily&days=30"

# 6. 标记关键表
curl -X POST http://localhost:8000/api/critical-tables \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": 1,
    "table_name": "users"
  }'
```

---

## Sign-off

### 开发完成确认

- [ ] 所有 Wave 计划完成
- [ ] 代码审查通过
- [ ] 单元测试通过
- [ ] 集成测试通过

### 产品经理确认

- [ ] UAT 测试全部通过
- [ ] 功能符合需求
- [ ] UI/UX 验收通过

### 技术负责人确认

- [ ] 技术验证全部通过
- [ ] 性能指标达标
- [ ] 安全审查通过
- [ ] 文档完整

---

## Known Issues

| Issue | Severity | Workaround | Status |
|-------|----------|------------|--------|
| (待填写) | Low/Med/High | (如有) | Open/Resolved |

---

## Rollback Plan

如需回滚 Phase 4:

```bash
# 1. 回滚数据库迁移
alembic downgrade -1

# 2. 恢复 Celery (如已移除)
git checkout HEAD -- backend/celery_config.py backend/app/worker.py
git checkout HEAD -- backend/pyproject.toml

# 3. 重启应用
# (停止当前服务，恢复备份，重新启动)
```

---

*Last updated: 2026-03-28*
