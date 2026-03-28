# DB Compare Roadmap

## Phase Structure

### Phase 1: Foundation (Core Connection & Schema Comparison)
**Goal:** 建立基础框架，实现 MySQL 表结构比对

**Features:**
- 数据库连接管理（支持 MySQL）
- 元数据获取（表、字段、索引、约束）
- 表结构比对引擎
- 简单的 Web 界面展示差异

**Deliverables:**
- 项目基础架构（Backend + Frontend）
- MySQL 连接池和查询引擎
- 结构比对核心算法
- 基础 UI 展示

**Research needs:**
- MySQL information_schema 查询优化
- 表结构差异化算法（字段顺序、类型、默认值）

---

### Phase 2: Multi-Database Support (Oracle + Enhanced Comparison)
**Goal:** 扩展 Oracle 支持，完善比对功能

**Features:**
- Oracle 数据库连接支持
- Oracle 元数据获取（ALL_TAB_COLUMNS, ALL_CONSTRAINTS 等）
- 跨数据库类型比对（MySQL vs Oracle）
- 比对报告生成（HTML 导出）

**Deliverables:**
- Oracle 适配器
- 统一元数据抽象层
- 报告生成模块

**Research needs:**
- Oracle 系统表查询语法
- MySQL/Oracle 数据类型映射表
- 字符集和排序规则差异处理

---

### Phase 3: Data Comparison Engine
**Goal:** 实现数据比对功能

**Features:**
- 全量数据比对（小表）
- 抽样数据比对（大表）
- 关键表/关键字段比对
- 数据差异统计和可视化

**Deliverables:**
- 数据比对引擎
- 分页/批处理查询
- 数据哈希校验
- 差异高亮展示

**Research needs:**
- 高效数据比对算法（MD5 校验、逐行比对）
- 大表比对性能优化策略
- BLOB/CLOB 字段比对处理

---

### Phase 4: Advanced Features (Scheduling & Alerting)
**Goal:** 增强运维自动化能力

**Features:**
- 定时比对任务
- 告警通知（邮件/钉钉/企业微信）
- 历史比对记录
- 趋势分析和报表

**Deliverables:**
- 任务调度系统
- 通知集成模块
- 历史记录存储和查询
- 统计报表功能

**Research needs:**
- 任务调度器选型（Celery vs APScheduler）
- 通知渠道集成 API

---

## Milestone Timeline

```
Phase 1 (Foundation)
├── M1: 项目初始化，MySQL 连接成功
├── M2: 元数据获取完成
├── M3: 结构比对引擎工作
└── M4: 基础 UI 展示差异

Phase 2 (Oracle Support)
├── M5: Oracle 连接成功
├── M6: Oracle 元数据适配
├── M7: 跨库比对支持
└── M8: 报告生成功能

Phase 3 (Data Comparison)
├── M9: 全量比对引擎
├── M10: 抽样比对策略
├── M11: 数据哈希校验
└── M12: 数据差异 UI

Phase 4 (Automation)
├── M13: 定时任务调度
├── M14: 告警通知集成
├── M15: 历史记录功能
└── M16: 统计报表
```

## Technical Foundation

**Recommended Stack:**
- **Backend:** Python 3.11+ + FastAPI
- **Frontend:** React 18+ + TypeScript + Ant Design
- **Database:** PostgreSQL (存储配置和历史记录)
- **ORM:** SQLAlchemy 2.0+
- **Task Queue:** Celery + Redis (Phase 4)

**Key Libraries:**
- `mysql-connector-python` / `cx_Oracle` — 数据库驱动
- `sqlalchemy` — 元数据反射和查询
- `fastapi` — Web API
- `jinja2` — 报告模板

## Anti-Goals (What We're Not Building)

- **自动同步工具** — 只比对，不修改
- **实时同步监控** — 批量比对为主
- **数据迁移平台** — 聚焦比对场景
- **通用数据库客户端** — 垂直场景工具

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| 结构比对准确率 | 100% | 测试用例验证 |
| 大表比对性能 | <5 分钟 (百万行) | 性能测试 |
| 用户满意度 | >4/5 | 用户反馈 |
| 误报率 | <1% | 生产验证 |

---
*Last updated: 2026-03-28 after initialization*
