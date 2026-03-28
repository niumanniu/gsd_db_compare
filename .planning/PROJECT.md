# DB Compare - 数据库库表比对系统

## What This Is

DB Compare 是一个面向运维团队的数据库比对工具，支持 MySQL 和 Oracle 数据库，提供表结构比对和数据比对功能，帮助运维人员快速识别数据库间的差异，确保环境一致性。

## Core Value

让运维团队快速发现和验证数据库结构及数据差异，减少人工比对错误，提高变更验证效率。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 多数据库支持：MySQL、Oracle
- [ ] 表结构比对：字段、索引、约束、默认值等
- [ ] 数据比对：支持全量比对、抽样比对、关键表比对
- [ ] 差异可视化：清晰展示结构和数据差异
- [ ] 比对报告生成：导出 HTML/PDF 格式报告
- [ ] 连接管理：安全存储和管理数据库连接信息
- [ ] 定时比对：支持计划任务定期执行比对
- [ ] 告警通知：差异超出阈值时通知

### Out of Scope

- 自动同步/修复 — 只读比对，不执行写操作
- 实时同步监控 — 批量比对为主，非实时
- 其他数据库类型 — 初期聚焦 MySQL/Oracle，后续扩展
- 数据迁移功能 — 仅比对，不迁移

## Context

**技术环境：**
- 数据库类型：MySQL (5.7/8.0+)、Oracle (12c/18c/19c+)
- 部署环境：公司内部服务器
- 网络要求：需要能访问目标数据库

**目标用户：**
- 运维工程师：环境变更验证、故障排查
- DBA：数据库结构审核、数据一致性检查
- 测试人员：测试环境与生产环境比对

**成功标准：**
- 比对任务执行时间可接受
- 差异识别准确率 100%
- 用户能快速理解比对结果

## Constraints

- **部署模式**：公司内部服务器 — 数据不出内网
- **操作模式**：只读查询 — 不执行 DDL/DML 写操作
- **并发限制**：比对任务串行或小并发 — 避免影响生产库性能
- **数据量**：大表比对需要分页/抽样 — 避免内存溢出

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 只读比对模式 | 降低风险，先证明价值再考虑同步功能 | — Pending |
| 支持 MySQL + Oracle | 这两种是公司主要数据库类型 | — Pending |
| 结构比对 + 数据比对 | 覆盖运维最常见的两个比对场景 | — Pending |
| 差异化比对策略 | 大表抽样、小表全量，平衡性能和准确性 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-28 after initialization*
