---
phase: 3
name: Data Comparison Engine
created: 2026-03-28
status: discussed
---

# Phase 3 Context

## Goal

实现数据比对功能

## Key Decisions

### 1. 比对策略

**选择:** 混合模式

- **小表 (< 100,000 行):** 全量逐行比对
- **大表 (≥ 100,000 行):** 先哈希校验，发现差异后再抽样定位
- **阈值配置:** 默认 100,000 行，可通过配置修改

### 2. 抽样策略

**选择:** 主键间隔抽样

- 按主键等间隔采样
- 快速且分布相对均匀
- 适合大表快速发现问题

### 3. 特殊字段处理

**选择:** 仅比对长度

- BLOB/CLOB/TEXT 字段不逐字节比对
- 检查数据长度是否一致
- 长度不同则标记为差异

### 4. NULL 值处理

**选择:** NULL = NULL 视为相同

- 两个 NULL 值视为相等
- 更直观的比对行为（非 SQL 标准）

### 5. 结果展示

**选择:** 两者结合

- 先展示摘要（总行数、差异行数、差异百分比）
- 支持下钻查看差异明细
- 差异数据表格展示，高亮差异字段

### 6. 执行方式

**选择:** 同步执行

- 数据比对采用同步方式
- 不引入 Celery 异步任务
- 保持架构轻量化

---

## Technical Implications

### Architecture

```
DataComparator (新增)
├── compare() - 主入口，根据行数自动选择模式
├── _full_compare() - 全量逐行比对
├── _hash_verify() - 哈希校验
├── _sample_compare() - 抽样比对
└── _compare_batch() - 批处理（分页查询）
```

### API Design

```
POST /api/compare/data
{
  "source_connection_id": 1,
  "target_connection_id": 2,
  "table_name": "users",
  "mode": "auto|full|sample|hash",  # auto=自动选择
  "threshold": 100000                # 可选，覆盖默认阈值
}

Response:
{
  "summary": {
    "source_row_count": 150000,
    "target_row_count": 150000,
    "diff_count": 12,
    "diff_percentage": 0.008,
    "mode_used": "hash+sample"
  },
  "sample_diffs": [...],  // 抽样发现的差异
  "has_more": true        // 是否还有更多差异
}
```

### Dependencies

无需新增依赖，使用现有：
- `hashlib` (Python 标准库) - MD5/Checksum 计算

---

## Success Criteria

- [ ] 小表全量比对正确
- [ ] 大表哈希校验快速发现差异
- [ ] 抽样比对能定位差异行
- [ ] NULL 值处理符合预期
- [ ] 特殊字段长度比对正确
- [ ] 结果展示摘要 + 明细
- [ ] 阈值可配置

---

## Notes

- 性能优化是关键，避免全表加载到内存
- 使用流式查询/游标逐行处理
- 批处理大小建议 1,000-5,000 行/批
