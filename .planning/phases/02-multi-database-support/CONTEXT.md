---
phase: 2
name: Multi-Database Support (Oracle)
created: 2026-03-28
status: discussed
---

# Phase 2 Context

## Goal

扩展 Oracle 支持，完善比对功能

## Key Decisions

### 1. Oracle 驱动

**选择:** `oracledb` (Oracle 官方 Python 驱动)

- 支持 Oracle 11g+
- 比 `cx_Oracle` 更好的维护和性能
- 纯 Python 实现，无需额外编译

### 2. 比对场景优先级

**Phase 2 重点:** **MySQL vs MySQL** (同类型数据库比对)

- Phase 1 已实现基础 MySQL 比对
- Phase 2 先完善 MySQL 比对的稳定性和功能
- **跨数据库比对 (MySQL vs Oracle) 推迟到后续 Phase**
- Oracle vs Oracle 作为次要优先级

### 3. 报告导出格式

**支持格式:**
- **HTML** - 可交互的网页报告
- **Excel** - 便于进一步数据分析

**报告内容:**
- 比对摘要 (差异总数、严重性分级)
- 表结构差异详情 (字段、索引、约束)
- 比对时间戳和耗时

### 4. 元数据覆盖范围

**核心:** 聚焦于**表结构**比对

**包含:**
- 表 (Tables)
- 列 (Columns)
- 索引 (Indexes)
- 约束 (Constraints)
- 默认值 (DEFAULT)
- 注释 (COMMENTS)

**排除:** (本 Phase 不处理)
- 分区 (PARTITIONS)
- 触发器 (TRIGGERS)
- 视图 (VIEWS)
- 序列 (SEQUENCES)
- 存储过程/函数

### 5. 调度器策略

**决策:** **不使用 Celery**

- Phase 2 报告生成采用**同步执行**
- 未来 Phase 4 考虑使用 **APScheduler** 替代 Celery
- 保持架构轻量化

### 6. 测试环境

**现状:** 无 Oracle 测试环境

**策略:**
- Phase 2 **优先保证 MySQL 比对功能完善**
- 暂不配置 Oracle Docker 环境
- Oracle 支持在 MySQL 比对稳定后再推进

---

## Technical Implications

### Architecture Changes

1. **DatabaseAdapter 扩展**
   ```
   DatabaseAdapter (abstract)
   ├── MySQLAdapter (已实现)
   └── OracleAdapter (Phase 2 - 可选)
   ```

2. **报告生成模块** (新增)
   - HTML 模板引擎 (Jinja2)
   - Excel 导出 (openpyxl / xlsxwriter)

3. **统一元数据格式**
   - 保持现有 `TableMetadata` 等模型
   - 确保 Oracle 适配器输出相同格式

### Dependencies

```python
oracledb          # Oracle 驱动
Jinja2            # HTML 模板
openpyxl          # Excel 导出
```

---

## Success Criteria

- [ ] MySQL vs MySQL 比对功能完善且稳定
- [ ] HTML 报告导出功能正常工作
- [ ] Excel 报告导出功能正常工作
- [ ] 报告内容包含完整的差异信息和摘要统计
- [ ] 代码架构支持未来扩展 Oracle 适配器

---

## Notes

- 跨数据库比对 (MySQL vs Oracle) 涉及复杂的数据类型映射，需要单独规划
- Oracle 环境配置较复杂，建议等 MySQL 比对完全稳定后再推进
- 报告生成采用同步方式，避免引入额外的调度复杂度
