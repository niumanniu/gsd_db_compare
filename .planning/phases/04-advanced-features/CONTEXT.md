---
phase: 4
name: Advanced Features (Scheduling & Alerting)
created: 2026-03-28
status: discussed
---

# Phase 4 Context

## Goal

增强运维自动化能力

## Key Decisions

### 1. 调度器架构

**选择:** APScheduler 替代 Celery

- 移除 Celery 依赖
- 使用 APScheduler 作为定时任务调度器
- 轻量级，无需 Redis  broker
- 支持 Cron 表达式

### 2. 通知渠道

**选择:** 邮件通知

- SMTP 协议发送告警邮件
- 支持多个收件人
- HTML 格式邮件（可复用 Phase 2 的 HTML 报告模板）

### 3. 历史记录

**选择:** 完整历史 + 趋势分析

- 每次比对结果保存到数据库
- 支持历史查询和对比
- 趋势分析图表（差异数量随时间变化）

### 4. 告警触发条件

**选择:** 关键差异告警

- 仅关键表差异触发告警
- 非关键表差异仅记录不告警
- 可配置告警阈值（差异行数超过 N 行）

### 5. 调度频率配置

**选择:** Cron 表达式

- 支持复杂调度（如工作日 9:00-18:00 每小时）
- 支持简单间隔（每小时/每天/每周）
- UI 上提供 Cron 表达式生成器（可选）

### 6. 关键表定义

**选择:** 手动标记

- 用户在连接管理界面标记关键表
- 关键表列表保存到数据库
- 比对任务可配置是否仅检查关键表

---

## Technical Implications

### Architecture Changes

1. **移除 Celery**
   ```
   backend/
   ├── celery_config.py  (删除)
   ├── app/worker.py     (删除或改写为 APScheduler)
   ```

2. **新增 APScheduler**
   ```
   backend/
   └── app/
       └── scheduler/
           ├── __init__.py
           ├── scheduler.py    # APScheduler 实例管理
           ├── jobs.py         # 比对任务定义
           └── store.py        # 任务存储（数据库）
   ```

3. **新增通知模块**
   ```
   backend/
   └── app/
       └── notifications/
           ├── __init__.py
           ├── email.py        # SMTP 邮件发送
           └── templates.py    # 邮件模板
   ```

4. **数据库 Schema 变更**
   ```sql
   -- 定时任务配置
   CREATE TABLE scheduled_tasks (
       id INTEGER PRIMARY KEY,
       name VARCHAR(255),
       cron_expression VARCHAR(100),
       source_connection_id INTEGER,
       target_connection_id INTEGER,
       tables TEXT,  -- JSON 数组，包含表名和是否关键标记
       enabled BOOLEAN DEFAULT true,
       created_at TIMESTAMP,
       updated_at TIMESTAMP
   );

   -- 比对历史
   CREATE TABLE comparison_history (
       id INTEGER PRIMARY KEY,
       task_id INTEGER,
       source_table VARCHAR(255),
       target_table VARCHAR(255),
       compare_mode VARCHAR(50),
       source_row_count INTEGER,
       target_row_count INTEGER,
       diff_count INTEGER,
       diff_percentage REAL,
       started_at TIMESTAMP,
       completed_at TIMESTAMP,
       status VARCHAR(50),
       error_message TEXT,
       result_summary TEXT  -- JSON
   );

   -- 关键表标记
   CREATE TABLE critical_tables (
       id INTEGER PRIMARY KEY,
       connection_id INTEGER,
       table_name VARCHAR(255),
       created_at TIMESTAMP
   );
   ```

### Dependencies

```python
APScheduler>=3.10.0    # 任务调度器
# 移除或保留 Celery（如果其他功能依赖）
```

### API Design

```
# 定时任务管理
POST   /api/scheduled-tasks         # 创建定时任务
GET    /api/scheduled-tasks         # 获取任务列表
GET    /api/scheduled-tasks/{id}    # 获取任务详情
PUT    /api/scheduled-tasks/{id}    # 更新任务
DELETE /api/scheduled-tasks/{id}    # 删除任务
POST   /api/scheduled-tasks/{id}/run    # 手动执行
POST   /api/scheduled-tasks/{id}/toggle # 启用/禁用

# 历史比对查询
GET /api/comparison-history?task_id=&page=&limit=

# 关键表管理
POST   /api/critical-tables         # 标记关键表
DELETE /api/critical-tables/{id}    # 移除标记
GET    /api/critical-tables?connection_id=
```

---

## Success Criteria

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
- [ ] 历史记录查询性能良好（分页）

---

## Migration from Celery

### 需要迁移的功能
1. Phase 1/2 中 Celery 的使用场景检查
2. 如果有异步任务，改用 APScheduler 的 `add_job()` 或线程池
3. 如果没有异步任务，直接移除 Celery

### 检查清单
- [ ] `backend/app/worker.py` 用途检查
- [ ] `celery_config.py` 配置检查
- [ ] 是否有`@celery.task` 装饰器
- [ ] 是否有`task.delay()`或`task.apply_async()` 调用

---

## Out of Scope

| Item | Reason |
|------|--------|
| 多通知渠道（钉钉/企业微信） | Phase 4 仅邮件，后续可扩展 |
| 告警升级策略（多次未处理升级） | 复杂场景，后续迭代 |
| 智能基线告警（同比/环比） | 需要机器学习，过于复杂 |
| 自动数据修复 | 只读比对，不修改数据 |

---

## Notes

- APScheduler 支持多种 job store：Memory、SQLAlchemy、Redis、MongoDB
- 建议使用 SQLAlchemy job store 实现持久化
- 邮件模板可复用 Phase 2 的 HTML 报告
- 趋势分析图表在前端使用 Chart.js 或 ECharts
