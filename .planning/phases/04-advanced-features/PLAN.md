# Phase 4: Advanced Features (Scheduling & Alerting) - Master Plan

**Version:** 1.0
**Created:** 2026-03-28
**Status:** Planning

---

## Goal

增强运维自动化能力，实现定时比对任务、邮件告警通知、历史记录管理和趋势分析功能。

---

## Scope Summary

| Feature | Description | Priority |
|---------|-------------|----------|
| APScheduler 调度器 | 替代 Celery，实现定时任务调度 | P0 |
| 邮件通知模块 | SMTP 邮件发送告警通知 | P0 |
| 数据库迁移 | 新增 scheduled_tasks, comparison_history, critical_tables 表 | P0 |
| 任务管理 API | 定时任务 CRUD 和执行接口 | P0 |
| 历史查询 API | 比对历史记录和趋势分析接口 | P1 |
| 关键表管理 API | 关键表标记和管理接口 | P1 |
| 任务管理 UI | 定时任务配置和管理界面 | P1 |
| 历史查看 UI | 历史记录查询和趋势图表 | P2 |
| 关键表标记 UI | 关键表标记界面集成 | P2 |
| Celery 迁移 | 移除 Celery 依赖和代码 | P1 |

---

## Wave Breakdown

### Wave 1: 基础设施 (Tasks 1-4)
**目标:** 完成数据库迁移、APScheduler 调度器、邮件通知模块

| Task | Dependencies | Estimated Effort |
|------|--------------|------------------|
| 1.1 数据库迁移 | 无 | 2-3h |
| 1.2 APScheduler 调度器模块 | 1.1 | 3-4h |
| 1.3 邮件通知模块 | 无 | 2-3h |
| 1.4 依赖更新 | 1.2, 1.3 | 0.5h |

**验证标准:**
- 数据库表创建成功
- APScheduler 可添加/执行定时任务
- 邮件可发送成功

---

### Wave 2: API 开发 (Tasks 5-8)
**目标:** 完成所有后端 API 接口

| Task | Dependencies | Estimated Effort |
|------|--------------|------------------|
| 2.1 任务管理 API | Wave 1 | 4-5h |
| 2.2 历史查询 API | Wave 1 | 3-4h |
| 2.3 关键表管理 API | Wave 1 | 2-3h |
| 2.4 API 集成测试 | 2.1, 2.2, 2.3 | 2h |

**验证标准:**
- 所有 API 端点可正常调用
- API 文档完整 (Swagger/OpenAPI)
- 单元测试覆盖率 >80%

---

### Wave 3: 前端 UI (Tasks 9-12)
**目标:** 完成前端界面开发

| Task | Dependencies | Estimated Effort |
|------|--------------|------------------|
| 3.1 类型定义和 API 客户端 | Wave 2 | 2h |
| 3.2 任务管理 UI | 2.1, 3.1 | 4-5h |
| 3.3 历史查看 UI | 2.2, 3.1 | 4-5h |
| 3.4 关键表标记 UI | 2.3, 3.1 | 2-3h |

**验证标准:**
- UI 界面可正常操作
- 前后端联调通过
- 无明显 UI/UX 问题

---

### Wave 4: Celery 迁移与集成测试 (Tasks 13-15)
**目标:** 移除 Celery，完成集成测试

| Task | Dependencies | Estimated Effort |
|------|--------------|------------------|
| 4.1 Celery 使用情况检查 | 无 | 1h |
| 4.2 Celery 代码迁移/移除 | 4.1, Wave 3 | 2-3h |
| 4.3 集成测试和文档 | Wave 3, 4.2 | 3-4h |

**验证标准:**
- Celery 依赖完全移除
- 所有功能正常工作
- 有完整的用户文档

---

## Task Dependencies Graph

```
Wave 1 (基础设施)
├── 1.1 数据库迁移 ──┬──> 1.2 APScheduler 调度器 ──┐
│                    │                              │
│                    └──> 1.3 邮件通知模块 ─────────┤
│                                                   ↓
Wave 2 (API 开发)                              Wave 3 (UI)
├── 2.1 任务管理 API ───────────────────────────> 3.2 任务管理 UI
│                         ↑                      │
├── 2.2 历史查询 API ─────┼─────────────────────> 3.3 历史查看 UI
│                         │                      │
├── 2.3 关键表管理 API ───┼─────────────────────> 3.4 关键表标记 UI
│                         │                      │
│                         └──> 3.1 类型定义 ──────┘
│
Wave 4 (迁移与测试)
├── 4.1 Celery 检查 ──> 4.2 Celery 移除 ──> 4.3 集成测试
```

---

## Detailed Tasks

### Wave 1: 基础设施

#### Task 1.1: 数据库迁移
**文件:**
- `backend/alembic/versions/002_advanced_features.py` (新增)

**内容:**
- `scheduled_tasks` 表 - 定时任务配置
- `comparison_history` 表 - 比对历史记录
- `critical_tables` 表 - 关键表标记
- `notification_settings` 表 - 邮件通知配置

**验收标准:**
- [ ] Alembic migration 可执行
- [ ] 所有表结构正确
- [ ] 有对应的 downgrade 函数

---

#### Task 1.2: APScheduler 调度器模块
**文件:**
- `backend/app/scheduler/__init__.py` (新增)
- `backend/app/scheduler/scheduler.py` (新增) - APScheduler 实例管理
- `backend/app/scheduler/jobs.py` (新增) - 比对任务定义
- `backend/app/scheduler/store.py` (新增) - 数据库持久化

**功能:**
- 创建/销毁调度器实例
- 添加/移除定时任务
- Cron 表达式解析
- 任务执行日志

**验收标准:**
- [ ] 调度器可启动/停止
- [ ] 可添加 Cron 任务
- [ ] 任务执行时自动调用比对 API
- [ ] 服务重启后任务恢复

---

#### Task 1.3: 邮件通知模块
**文件:**
- `backend/app/notifications/__init__.py` (新增)
- `backend/app/notifications/email.py` (新增) - SMTP 邮件发送
- `backend/app/notifications/templates.py` (新增) - 邮件模板
- `backend/app/notifications/templates/` (新增目录)
  - `alert_email.html` - 告警邮件模板
  - `summary_email.html` - 汇总邮件模板

**功能:**
- SMTP 配置管理
- HTML 邮件发送
- 多收件人支持
- 发送失败重试

**验收标准:**
- [ ] 可配置 SMTP 服务器
- [ ] 邮件发送成功
- [ ] HTML 格式正确
- [ ] 有发送失败日志

---

#### Task 1.4: 依赖更新
**文件:**
- `backend/pyproject.toml` (修改)

**内容:**
- 添加 `APScheduler>=3.10.0`
- 移除 `celery[redis]` (如确认无其他依赖)
- 添加 `aiosmtplib>=3.0` (异步 SMTP)

**验收标准:**
- [ ] 依赖安装成功
- [ ] 应用启动正常

---

### Wave 2: API 开发

#### Task 2.1: 任务管理 API
**文件:**
- `backend/app/api/scheduled_tasks.py` (新增)
- `backend/app/schemas/scheduled_tasks.py` (新增)

**端点:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scheduled-tasks` | 创建定时任务 |
| GET | `/api/scheduled-tasks` | 获取任务列表 |
| GET | `/api/scheduled-tasks/{id}` | 获取任务详情 |
| PUT | `/api/scheduled-tasks/{id}` | 更新任务 |
| DELETE | `/api/scheduled-tasks/{id}` | 删除任务 |
| POST | `/api/scheduled-tasks/{id}/run` | 手动执行 |
| POST | `/api/scheduled-tasks/{id}/toggle` | 启用/禁用 |

**验收标准:**
- [ ] 所有端点可调用
- [ ] 参数验证正确
- [ ] 与调度器集成
- [ ] 错误处理完善

---

#### Task 2.2: 历史查询 API
**文件:**
- `backend/app/api/history.py` (新增)
- `backend/app/schemas/history.py` (新增)

**端点:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/comparison-history` | 获取历史记录 (分页) |
| GET | `/api/comparison-history/{id}` | 获取单次详情 |
| GET | `/api/comparison-history/trend` | 趋势分析数据 |
| GET | `/api/comparison-history/stats` | 统计摘要 |

**验收标准:**
- [ ] 分页查询正常
- [ ] 趋势数据计算正确
- [ ] 查询性能良好

---

#### Task 2.3: 关键表管理 API
**文件:**
- `backend/app/api/critical_tables.py` (新增)
- `backend/app/schemas/critical_tables.py` (新增)

**端点:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/critical-tables` | 标记关键表 |
| DELETE | `/api/critical-tables/{id}` | 移除标记 |
| GET | `/api/critical-tables` | 获取关键表列表 |
| GET | `/api/critical-tables/check` | 检查是否关键表 |

**验收标准:**
- [ ] 标记功能正常
- [ ] 按连接查询正确
- [ ] 与告警逻辑集成

---

#### Task 2.4: API 集成测试
**文件:**
- `backend/tests/test_scheduled_tasks.py` (新增)
- `backend/tests/test_history.py` (新增)
- `backend/tests/test_critical_tables.py` (新增)

**验收标准:**
- [ ] 测试覆盖率 >80%
- [ ] 所有测试通过
- [ ] 有集成测试用例

---

### Wave 3: 前端 UI

#### Task 3.1: 类型定义和 API 客户端
**文件:**
- `frontend/src/types/scheduled.ts` (新增)
- `frontend/src/types/history.ts` (新增)
- `frontend/src/api/scheduled.ts` (新增)
- `frontend/src/api/history.ts` (新增)

**验收标准:**
- [ ] TypeScript 类型完整
- [ ] API 客户端封装正确
- [ ] 有错误处理

---

#### Task 3.2: 任务管理 UI
**文件:**
- `frontend/src/components/ScheduledTaskList.tsx` (新增)
- `frontend/src/components/ScheduledTaskForm.tsx` (新增)
- `frontend/src/components/CronBuilder.tsx` (新增，可选)

**功能:**
- 任务列表展示
- 创建/编辑任务表单
- Cron 表达式输入 (可选可视化生成器)
- 启用/禁用切换
- 手动执行按钮

**验收标准:**
- [ ] 列表可刷新
- [ ] 表单验证正确
- [ ] 操作反馈清晰
- [ ] 状态同步及时

---

#### Task 3.3: 历史查看 UI
**文件:**
- `frontend/src/components/ComparisonHistory.tsx` (新增)
- `frontend/src/components/TrendChart.tsx` (新增)

**功能:**
- 历史记录列表 (分页)
- 趋势图表 (差异数量随时间变化)
- 筛选器 (时间范围、任务、表名)
- 详情查看

**验收标准:**
- [ ] 列表分页正常
- [ ] 图表渲染正确
- [ ] 筛选功能工作
- [ ] 响应式设计

---

#### Task 3.4: 关键表标记 UI
**文件:**
- `frontend/src/components/CriticalTableManager.tsx` (新增)

**功能:**
- 在 TableBrowser 中集成标记功能
- 关键表高亮显示
- 批量标记/取消

**验收标准:**
- [ ] 标记功能可用
- [ ] 高亮显示清晰
- [ ] 状态同步及时

---

### Wave 4: Celery 迁移与集成测试

#### Task 4.1: Celery 使用情况检查
**文件:**
- 检查清单

**检查项:**
- [ ] `backend/app/worker.py` 中的任务
- [ ] `celery_config.py` 配置
- [ ] 是否有其他地方调用 `@celery.task`
- [ ] 是否有 `task.delay()` 或 `apply_async()` 调用

**输出:**
- Celery 使用报告
- 迁移方案建议

---

#### Task 4.2: Celery 代码迁移/移除
**文件:**
- `backend/app/worker.py` (删除或改写)
- `backend/celery_config.py` (删除)
- `backend/pyproject.toml` (移除 celery 依赖)

**方案:**
1. 如果 Celery 仅用于比对任务 → 完全移除，改用 APScheduler
2. 如果有其他用途 → 保留必要部分，迁移比对任务

**验收标准:**
- [ ] Celery 依赖移除
- [ ] 原有功能正常
- [ ] 代码清理完成

---

#### Task 4.3: 集成测试和文档
**文件:**
- `.planning/phases/04-advanced-features/VERIFY.md` (新增)
- `docs/user-guide.md` (新增，可选)

**测试项:**
- 创建定时任务并执行
- 验证邮件通知
- 查看历史记录
- 趋势图表显示
- 关键表告警触发

**验收标准:**
- [ ] 所有功能端到端测试通过
- [ ] 用户文档完整
- [ ] 有故障排查指南

---

## Verification Criteria Summary

### 功能标准
- [ ] 创建定时任务，使用 Cron 表达式配置频率
- [ ] 启用/禁用定时任务
- [ ] 手动触发定时任务立即执行
- [ ] 关键表标记功能工作正常
- [ ] 仅关键表差异触发邮件告警
- [ ] 邮件通知发送成功
- [ ] 历史比对记录保存完整
- [ ] 趋势分析图表展示差异变化

### 技术标准
- [ ] APScheduler 任务持久化到数据库
- [ ] 服务重启后定时任务自动恢复
- [ ] 并发比对任务不会冲突
- [ ] 邮件发送失败有重试机制
- [ ] 历史记录查询性能良好 (分页)
- [ ] Celery 依赖完全移除

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| APScheduler 与 FastAPI 集成复杂 | 中 | 使用 startup/shutdown 事件管理生命周期 |
| 邮件发送失败无通知 | 中 | 添加发送失败日志和告警 |
| 历史数据量大影响性能 | 中 | 添加分页和索引，考虑数据归档 |
| Celery 迁移影响现有功能 | 高 | 充分测试，保留回滚方案 |
| Cron 表达式配置复杂 | 低 | 提供预设模板和可视化生成器 |

---

## Out of Scope

- 多通知渠道 (钉钉/企业微信) - 后续扩展
- 告警升级策略 - 后续迭代
- 智能基线告警 (同比/环比) - 需要机器学习
- 自动数据修复 - 只读比对，不修改数据

---

## Files Summary

### 新增文件 (Backend)
```
backend/
├── alembic/versions/
│   └── 002_advanced_features.py
├── app/
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── scheduler.py
│   │   ├── jobs.py
│   │   └── store.py
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── templates.py
│   │   └── templates/
│   │       ├── alert_email.html
│   │       └── summary_email.html
│   ├── api/
│   │   ├── scheduled_tasks.py
│   │   ├── history.py
│   │   └── critical_tables.py
│   └── schemas/
│       ├── scheduled_tasks.py
│       ├── history.py
│       └── critical_tables.py
└── tests/
    ├── test_scheduled_tasks.py
    ├── test_history.py
    └── test_critical_tables.py
```

### 新增文件 (Frontend)
```
frontend/src/
├── types/
│   ├── scheduled.ts
│   └── history.ts
├── api/
│   ├── scheduled.ts
│   └── history.ts
└── components/
    ├── ScheduledTaskList.tsx
    ├── ScheduledTaskForm.tsx
    ├── CronBuilder.tsx (optional)
    ├── ComparisonHistory.tsx
    ├── TrendChart.tsx
    └── CriticalTableManager.tsx
```

### 删除/修改文件
```
backend/
├── celery_config.py (删除)
├── app/worker.py (删除或改写)
└── pyproject.toml (修改依赖)
```
