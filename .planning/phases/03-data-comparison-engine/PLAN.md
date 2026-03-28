---
phase: 03-data-comparison-engine
plan: 05
type: summary
wave: N/A
depends_on: ["01-PLAN", "02-PLAN", "03-PLAN", "04-PLAN"]
files_modified: []
autonomous: false
requirements:
  - DATA-COMP-01
  - DATA-COMP-02
  - DATA-COMP-03
  - DATA-COMP-04
  - DATA-COMP-05
  - UI-DATA-01

---

# Phase 3: Data Comparison Engine - Execution Summary

## Phase Overview

**Goal:** 实现数据比对功能，支持小表全量比对和大表哈希 + 抽样比对

**Duration:** Estimated 4 waves of execution

**Primary Focus:**
1. DataComparator 比对引擎（全量、哈希、抽样模式）
2. 批处理/分页查询支持大表比对
3. 数据比对 API 端点
4. UI 组件展示比对结果（摘要 + 下钻明细）

---

## Wave Structure

### Wave 1: DataComparator Core Engine
**Plans:** 01-PLAN
**Focus:** Core comparison engine implementation
**Dependencies:** None (Phase 3 start)

| Plan | Tasks | Key Deliverables |
|------|-------|------------------|
| 01-PLAN | 4 tasks | DataComparator class, full_compare, hash_verify, sample_compare |

**Verification:**
- [ ] DataComparator class implements all comparison modes
- [ ] Full compare mode works for tables < 100,000 rows
- [ ] Hash verify mode computes MD5 checksums correctly
- [ ] Sample compare mode uses primary key interval sampling
- [ ] NULL = NULL treated as equal (non-SQL standard)
- [ ] BLOB/CLOB/TEXT fields compared by length only
- [ ] Batch processing with configurable page size (default 1,000-5,000)

---

### Wave 2: Data Comparison API + Task Tracking
**Plans:** 02-PLAN
**Focus:** API endpoints and database integration
**Dependencies:** Wave 1 complete

| Plan | Tasks | Key Deliverables |
|------|-------|------------------|
| 02-PLAN | 4 tasks | /api/compare/data endpoint, DataCompareRequest/Response schemas, task tracking |

**Verification:**
- [ ] POST /api/compare/data accepts comparison parameters
- [ ] API supports mode selection (auto/full/hash/sample)
- [ ] API returns summary with row counts, diff counts, diff percentage
- [ ] API supports threshold override (default 100,000)
- [ ] Comparison tasks saved to comparison_tasks table
- [ ] Task status tracked (pending/running/completed/failed)

---

### Wave 3: UI Components for Data Comparison
**Plans:** 03-PLAN
**Focus:** Frontend components for data diff display
**Dependencies:** Wave 2 complete

| Plan | Tasks | Key Deliverables |
|------|-------|------------------|
| 03-PLAN | 4 tasks | DataDiffViewer component, SummaryPanel, DrillDownTable, useDataComparison hook |

**Verification:**
- [ ] DataDiffViewer renders comparison summary (row counts, diff counts)
- [ ] SummaryPanel shows diff percentage and mode used
- [ ] DrillDownTable displays差异 rows with highlighted fields
- [ ] useDataComparison hook provides compareData function
- [ ] UI supports pagination for large result sets
- [ ] NULL values displayed consistently

---

### Wave 4: Integration + Edge Cases
**Plans:** 04-PLAN
**Focus:** End-to-end integration and edge case handling
**Dependencies:** Wave 3 complete

| Plan | Tasks | Key Deliverables |
|------|-------|------------------|
| 04-PLAN | 3 tasks | App integration, error handling, performance optimization |

**Verification:**
- [ ] Full comparison-to-display flow works end-to-end
- [ ] Large table (>1M rows) compares within acceptable time
- [ ] Memory usage stays bounded during comparison
- [ ] Error cases handled gracefully (connection lost, timeout)
- [ ] Cross-database data comparison works (MySQL vs Oracle types)

---

## Task Summary by Category

### Backend Tasks (11 tasks total)

| Category | Count | Plans |
|----------|-------|-------|
| Comparison Engine | 4 | 01-PLAN |
| API + Schemas | 4 | 02-PLAN |
| Integration | 3 | 04-PLAN |

### Frontend Tasks (7 tasks total)

| Category | Count | Plans |
|----------|-------|-------|
| Components | 3 | 03-PLAN |
| Hooks | 1 | 03-PLAN |
| Integration | 3 | 04-PLAN |

---

## File Manifest

### New Files to Create

```
backend/
├── app/
│   ├── comparison/
│   │   └── data.py                      # Wave 1 - DataComparator engine
│   ├── schemas/
│   │   └── data_compare.py              # Wave 2 - Data comparison schemas
│   └── api/
│       └── data_compare.py              # Wave 2 - Data comparison endpoints

frontend/
└── src/
    ├── components/
    │   ├── DataDiffViewer.tsx           # Wave 3 - Main data diff display
    │   ├── SummaryPanel.tsx             # Wave 3 - Summary statistics
    │   └── DrillDownTable.tsx           # Wave 3 - Drill-down差异 table
    ├── hooks/
    │   └── useDataComparison.ts         # Wave 3 - Data comparison hook
    └── types/
        └── data_compare.ts              # Wave 3 - TypeScript types
```

### Modified Files

```
backend/
├── app/
│   ├── db/
│   │   └── models.py                    # Wave 2 - Add data compare result fields
│   ├── schemas/
│   │   └── api.py                       # Wave 2 - Add data compare schemas
│   └── api/
│       └── __init__.py                  # Wave 2 - Include data_compare router

frontend/
├── src/
│   ├── types/
│   │   └── index.ts                     # Wave 3 - Export data compare types
│   └── App.tsx                          # Wave 4 - Integrate DataDiffViewer
```

---

## Requirements Traceability

### Phase 3 Requirements (from CONTEXT.md)

| ID | Requirement | Plans | Status |
|----|-------------|-------|--------|
| DATA-COMP-01 | 小表全量比对 (<100K 行) | 01-PLAN | Pending |
| DATA-COMP-02 | 大表哈希 + 抽样比对 (≥100K 行) | 01-PLAN | Pending |
| DATA-COMP-03 | 主键间隔抽样策略 | 01-PLAN | Pending |
| DATA-COMP-04 | 特殊字段仅比对长度 (BLOB/CLOB/TEXT) | 01-PLAN | Pending |
| DATA-COMP-05 | NULL = NULL 视为相同 | 01-PLAN | Pending |
| DATA-COMP-06 | 阈值可配置 (默认 100,000) | 02-PLAN | Pending |
| UI-DATA-01 | 摘要展示 (总行数、差异行数、百分比) | 03-PLAN | Pending |
| UI-DATA-02 | 下钻明细查看 | 03-PLAN | Pending |
| UI-DATA-03 | 差异字段高亮 | 03-PLAN | Pending |
| UI-DATA-04 | 同步执行 UX | 04-PLAN | Pending |

---

## Success Criteria (Phase Level)

### Functional Criteria
- [ ] 小表全量比对正确，无漏报误报
- [ ] 大表哈希校验快速发现差异
- [ ] 抽样比对能准确定位差异行
- [ ] NULL 值处理符合预期（NULL = NULL）
- [ ] 特殊字段长度比对正确
- [ ] 结果展示包含摘要和明细
- [ ] 比对阈值可配置

### Technical Criteria
- [ ] 批处理避免内存溢出
- [ ] 流式查询/游标逐行处理
- [ ] 批处理大小可配置（1,000-5,000 行/批）
- [ ] 比对性能可接受（百万行<5 分钟）

### UI Criteria
- [ ] 摘要清晰展示关键指标
- [ ] 差异明细支持下钻查看
- [ ] 差异字段高亮显示
- [ ] 比对过程中显示进度

### Documentation Criteria
- [ ] 所有 SUMMARY.md 文件创建完成
- [ ] DataComparator API 文档
- [ ] 比对策略说明文档

---

## Out of Scope (Explicitly Deferred)

| Item | Reason | Deferred To |
|------|--------|-------------|
| 跨数据库数据比对（MySQL vs Oracle） | 需完善类型转换，本 Phase 聚焦同构数据库 | Phase 4 |
| 实时数据同步监控 | CONTEXT.md 明确批量比对为主 | N/A |
| 自动数据修复/同步 | 只读比对，不修改数据 | Future |
| 增量比对（仅比对变更数据） | 需要 CDC/日志解析 | Future |
| 异步比对任务 | CONTEXT.md 明确同步执行 | N/A |

---

## Execution Order

```
Wave 1 (DataComparator Core Engine)
├── 01-PLAN: Task 1 → Task 2 → Task 3 → Task 4
│
Wave 2 (Data Comparison API + Task Tracking)
├── 02-PLAN: Task 1 → Task 2 → Task 3 → Task 4
│
Wave 3 (UI Components for Data Comparison)
├── 03-PLAN: Task 1 → Task 2 → Task 3 → Task 4
│
Wave 4 (Integration + Edge Cases)
└── 04-PLAN: Task 1 → Task 2 → Task 3
```

---

## Verification Checklist (Phase Completion)

After all waves complete, verify:

### Backend
- [ ] DataComparator instantiated with correct mode
- [ ] Full compare returns all row differences
- [ ] Hash compare detects differences via MD5
- [ ] Sample compare identifies差异 rows
- [ ] NULL handling treats NULL = NULL as equal
- [ ] BLOB/CLOB comparison checks length only
- [ ] Batch processing handles large tables

### API
- [ ] POST /api/compare/data accepts valid requests
- [ ] API returns correct summary statistics
- [ ] API supports all modes (auto/full/hash/sample)
- [ ] Task records created in database
- [ ] Task status updated correctly

### Frontend
- [ ] `npm run build` succeeds
- [ ] DataDiffViewer renders without errors
- [ ] Summary shows row counts and diff counts
- [ ] DrillDownTable displays差异 rows
- [ ] Diff columns highlighted
- [ ] Pagination works for large result sets

### Integration
- [ ] Full comparison flow: select tables → compare → display results
- [ ] Large table comparison completes without memory issues
- [ ] Error cases display user-friendly messages

---

## Comparison Strategy Details

### Mode Selection Logic (auto mode)

```
Row Count < Threshold (default 100,000)
    └── Full Compare (逐行比对)

Row Count >= Threshold
    └── Hash Verify (整表 MD5)
        ├── Hashes match → Tables identical (done)
        └── Hashes differ → Sample Compare (抽样定位差异)
            └── Return sample differences
```

### Sampling Algorithm

```
Primary Key Interval Sampling:
- Get primary key column name
- Determine sample size (configurable, e.g., 1,000 rows)
- Calculate interval: total_rows / sample_size
- Query: SELECT * FROM table WHERE pk_id % interval = 0
```

### Special Field Handling

| Field Type | Comparison Strategy |
|------------|---------------------|
| BLOB/BINARY | Compare LENGTH(data) |
| CLOB/TEXT | Compare LENGTH(text) |
| JSON | Compare as string (or normalized JSON) |
| TIMESTAMP | Compare normalized values |

### NULL Handling

```
Standard SQL:     NULL = NULL → UNKNOWN (not equal)
This Project:     NULL = NULL → TRUE (equal)

Implementation:
- Before comparison, check both values for NULL
- If both NULL → consider equal
- If one NULL → consider different
```

---

## Performance Considerations

### Memory Management
- Stream results using server-side cursors
- Process in batches of 1,000-5,000 rows
- Clear batch data from memory after processing
- Use generators for memory-efficient iteration

### Query Optimization
- Index on primary key for efficient sampling
- Use LIMIT/OFFSET for pagination
- Avoid SELECT * - select only needed columns
- Consider parallel batch processing (future)

### Timeout Handling
- Set reasonable query timeouts
- Handle connection drops gracefully
- Provide progress feedback to users

---

## Next Phase Preview (Phase 4: Advanced Features)

Phase 4 will add:
- 定时比对任务（调度器）
- 告警通知（邮件/钉钉/企业微信）
- 历史比对记录查询
- 趋势分析和报表

Phase 3 sets the foundation for:
- 数据比对核心能力
- 批处理架构
- 结果展示 UI

---

*This summary document serves as the master execution plan for Phase 3. Individual plan files (01-PLAN.md through 04-PLAN.md) contain detailed task specifications.*
