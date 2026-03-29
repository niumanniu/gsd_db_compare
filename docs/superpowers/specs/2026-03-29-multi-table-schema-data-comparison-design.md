# 多表/Schema 级别数据比对设计方案

**Created:** 2026-03-29
**Author:** Claude Code
**Status:** Approved

---

## 1. 需求概述

### 1.1 背景

当前系统已支持：
- 单表数据比对（`/api/compare/data`）- 比对两个指定表的数据
- 单表 Schema 比对（`/api/compare/schema`）- 比对两个表的结构差异
- 多表 Schema 批量比对 - 批量比对多个表的结构差异
- Database 级 Schema 比对 - 比对整个库的表结构

需要扩展支持：
1. **多表数据批量比对** - 一次性比对多个选中的表，返回每张表的数据差异摘要
2. **Schema 级数据比对** - 比对整个 Schema（数据库/用户）下所有表的数据一致性

### 1.2 使用场景

| 场景 | 描述 | 典型用户 |
|------|------|----------|
| 迁移验证 | 数据库迁移后，验证源库和目标库数据一致性 | DBA、运维 |
| 环境同步检查 | 检查生产环境和测试环境数据差异 | 开发、测试 |
| 数据质量审计 | 定期比对主备库数据，发现潜在问题 | 数据工程师 |

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ TableBrowser│  │ SchemaCompare   │  │ MultiTableData  │  │
│  │ (扩展)      │  │ Form (现有)     │  │ Compare Form    │  │
│  └─────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │ /api/compare/    │  │ /api/compare/                   │  │
│  │ multi-table-data │  │ schema-data                     │  │
│  │ (多表数据比对)    │  │ (Schema 级数据比对)              │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Comparison Engine                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ MultiTableDataComparator (new)                          ││
│  │ - 复用 DataComparator                                   ││
│  │ - 协调多个单表比对                                      ││
│  │ - 聚合结果，生成汇总报告                                ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ SchemaDataComparator (new)                              ││
│  │ - 自动发现 Schema 下所有表                                  │
│  │ - 应用过滤规则（exclude/include patterns）              │
│  │ - 调用 MultiTableDataComparator 执行比对                    │
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database Adapters                           │
│  MySQLAdapter  │  OracleAdapter  │  (future adapters)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 后端设计

### 3.1 Schema 定义 (`backend/app/schemas/api.py`)

#### 3.1.1 多表数据比对

```python
class MultiTableDataCompareRequest(BaseModel):
    """多表数据比对请求"""
    source_connection_id: int
    target_connection_id: int
    source_schema: str  # Schema 名（database/user）
    target_schema: str
    source_tables: list[str]  # 选中的源表列表
    target_tables: list[str]  # 选中的目标表列表
    table_mapping: Optional[dict[str, str]] = None  # {source_table: target_table}

    # 比对参数
    mode: str = "auto"  # auto|full|hash|sample
    threshold: Optional[int] = 100000
    sample_size: Optional[int] = 1000
    timeout_per_table: Optional[int] = 300  # 每表超时（秒）


class TableDataResult(BaseModel):
    """单表比对结果"""
    source_table: str
    target_table: str
    status: str  # success|error|skipped
    source_row_count: int
    target_row_count: int
    diff_count: int
    diff_percentage: Optional[float]
    mode_used: str
    is_identical: bool
    error_message: Optional[str] = None


class MultiTableDataSummary(BaseModel):
    """多表比对汇总"""
    total_tables: int
    compared_tables: int
    identical_tables: int
    tables_with_diffs: int
    error_tables: int
    total_rows_compared: int
    total_diffs_found: int
    elapsed_time_seconds: float


class MultiTableDataCompareResponse(BaseModel):
    """多表数据比对响应"""
    summary: MultiTableDataSummary
    table_results: list[TableDataResult]
```

#### 3.1.2 Schema 级数据比对

```python
class SchemaDataCompareRequest(BaseModel):
    """Schema 级数据比对请求"""
    source_connection_id: int
    target_connection_id: int
    source_schema: str
    target_schema: str

    # 过滤选项
    exclude_patterns: list[str] = []  # 排除的表名模式（支持 * 通配符）
    include_patterns: list[str] = []  # 只包含的表名模式
    only_common_tables: bool = True  # 只比对两个 Schema 都有的表

    # 比对参数
    mode: str = "hash"  # 默认 hash 快速筛查
    threshold: Optional[int] = 100000
    sample_size: Optional[int] = 1000
    timeout_per_table: Optional[int] = 300


class SchemaDataCompareSummary(BaseModel):
    """Schema 级比对汇总"""
    source_schema: str
    target_schema: str
    source_connection_name: str
    target_connection_name: str

    # 表统计
    total_source_tables: int
    total_target_tables: int
    common_tables: int
    unmatched_source_tables: int
    unmatched_target_tables: int

    # 比对结果
    compared_tables: int
    identical_tables: int
    tables_with_diffs: int
    error_tables: int

    # 总体数据量
    total_rows_source: int
    total_rows_target: int
    total_diffs_found: int
    overall_diff_percentage: Optional[float]
    elapsed_time_seconds: float


class SchemaDataCompareResponse(BaseModel):
    """Schema 级数据比对响应"""
    summary: SchemaDataCompareSummary
    table_results: list[TableDataResult]
    unmatched_source_tables: list[str]
    unmatched_target_tables: list[str]
    excluded_tables: list[str]
```

### 3.2 比较器类

#### 3.2.1 MultiTableDataComparator (`backend/app/comparison/multi_table.py`)

```python
class MultiTableDataComparator:
    """多表数据比较器 - 协调多个单表比对"""

    def __init__(
        self,
        source_adapter: DatabaseAdapter,
        target_adapter: DatabaseAdapter,
        source_schema: str,
        target_schema: str,
        mode: str = "auto",
        threshold: int = 100000,
        sample_size: int = 1000,
        timeout_per_table: int = 300,
    ):
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.source_schema = source_schema
        self.target_schema = target_schema
        self.mode = mode
        self.threshold = threshold
        self.sample_size = sample_size
        self.timeout_per_table = timeout_per_table

    def compare(
        self,
        table_mappings: list[tuple[str, str]],
    ) -> MultiTableDataCompareResponse:
        """执行多表比对"""

    def _compare_single_table(
        self,
        source_table: str,
        target_table: str,
    ) -> TableDataResult:
        """复用 DataComparator 进行单表比对"""
```

#### 3.2.2 SchemaDataComparator

```python
class SchemaDataComparator:
    """Schema 级数据比较器"""

    def __init__(
        self,
        source_adapter: DatabaseAdapter,
        target_adapter: DatabaseAdapter,
        source_schema: str,
        target_schema: str,
        mode: str = "hash",
        threshold: int = 100000,
        sample_size: int = 1000,
        timeout_per_table: int = 300,
    ):
        # ... 初始化参数

    def compare(
        self,
        exclude_patterns: list[str] = [],
        include_patterns: list[str] = [],
        only_common_tables: bool = True,
    ) -> SchemaDataCompareResponse:
        """执行 Schema 级数据比对"""
        # 1. 获取两个 Schema 的所有表
        # 2. 应用过滤
        # 3. 确定比对范围
        # 4. 执行比对（复用 MultiTableDataComparator）
        # 5. 构建 Schema 级响应
```

### 3.3 API 端点 (`backend/app/api/data_compare.py`)

```python
@router.post("/multi-table-data", response_model=MultiTableDataCompareResponse)
async def compare_multi_table_data(
    request: MultiTableDataCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MultiTableDataCompareResponse:
    """Compare data across multiple selected tables."""


@router.post("/schema-data", response_model=SchemaDataCompareResponse)
async def compare_schema_data(
    request: SchemaDataCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SchemaDataCompareResponse:
    """Compare data across entire schema (all tables)."""
```

---

## 4. 前端设计

### 4.1 新增组件

```
/src/components/
  ├── MultiTableDataCompareForm.tsx   (新增 - 多表比对表单)
  ├── SchemaDataCompareForm.tsx       (新增 - Schema 级比对表单)
  ├── TableDataResultTable.tsx        (新增 - 结果表格)
  └── ComparisonProgress.tsx          (新增 - 进度展示)

/src/pages/
  ├── MultiTableCompare.tsx           (新增 - 多表比对页面)
  └── SchemaDataCompare.tsx           (新增 - Schema 级比对页面)

/src/hooks/
  └── useMultiTableComparison.ts      (新增 - 比对逻辑)
```

### 4.2 多表比对表单 UI

```
┌────────────────────────────────────────────────────┐
│  多表数据比对                                       │
├────────────────────────────────────────────────────┤
│  源连接：[MySQL-Prod ▼]  Schema: [mydb ▼]          │
│  目标连接：[MySQL-Staging ▼]  Schema: [mydb ▼]     │
├────────────────────────────────────────────────────┤
│  选择要比对的表：                                   │
│  ┌──────────────────────────────────────────────┐  │
│  │ ☑ users          │  ☑ orders                 │  │
│  │ ☑ products       │  ☐ inventory (仅源)       │  │
│  │ ☑ categories     │  ☑ customers              │  │
│  └──────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│  比对模式：○ 自动  ◉ Hash  ○ 全量  ○ 抽样          │
│  超时时间：[300] 秒/表                              │
├────────────────────────────────────────────────────┤
│           [开始比对]                               │
└────────────────────────────────────────────────────┘
```

### 4.3 结果展示 UI

```
┌─────────────────────────────────────────────────────────────┐
│  比对完成 - 5 张表，3 张有差异                                │
├─────────────────────────────────────────────────────────────┤
│  汇总：                                                      │
│  • 比对表数：5  • 一致：2  • 有差异：3  • 错误：0            │
│  • 总行数：1,234,567  • 差异行数：42                        │
├─────────────────────────────────────────────────────────────┤
│  表名        │ 源行数  │ 目标行数  │ 差异数  │ 状态  │ 操作   │
│  ─────────────────────────────────────────────────────────  │
│  users       │ 10,000  │ 10,000   │ 0       │ ✓ 一致 │ 详情  │
│  products    │ 5,000   │ 5,000    │ 12      │ ⚠ 差异 │ 详情  │
│  orders      │ 100,000 │ 100,000  │ 28      │ ⚠ 差异 │ 详情  │
│  categories  │ 50      │ 50       │ 0       │ ✓ 一致 │ 详情  │
│  customers   │ 8,000   │ 7,998    │ 2       │ ⚠ 差异 │ 详情  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 关键设计决策

| 决策点 | 选项 | 决策 | 理由 |
|--------|------|------|------|
| 表匹配 | 自动 vs 手动 | 默认自动（同名匹配）+ 可选映射 | 大多数场景表名相同，允许例外 |
| Schema 比对范围 | 仅共同表 vs 全部表 | 可配置 | 默认只比对共同表，可选包含不匹配表 |
| 比对模式 | 单一模式 vs 分层模式 | 分层 | Schema 级先用 hash 快速筛查，再深入分析差异表 |
| 执行方式 | 并行 vs 串行 | 串行为主 | 避免连接池耗尽，可配置每表超时 |

---

## 6. 数据流

### 6.1 多表数据比对流程

```
用户选择表和参数
       │
       ▼
前端发送 MultiTableDataCompareRequest
       │
       ▼
后端获取连接 → 创建适配器 → 创建 MultiTableDataComparator
       │
       ▼
对每个表对执行 _compare_single_table
       │
       ▼
聚合结果 → 返回 MultiTableDataCompareResponse
       │
       ▼
前端展示汇总和明细
```

### 6.2 Schema 级数据比对流程

```
用户选择 Schema 和过滤规则
       │
       ▼
前端发送 SchemaDataCompareRequest
       │
       ▼
后端获取所有表 → 应用过滤 → 确定比对范围
       │
       ▼
调用 MultiTableDataComparator.compare()
       │
       ▼
构建 SchemaDataCompareResponse
       │
       ▼
前端展示汇总和明细
```

---

## 7. 实施计划

### Phase 1: 后端核心
1. 添加 Schema 定义（`schemas/api.py`）
2. 实现 `MultiTableDataComparator`
3. 实现 `SchemaDataComparator`
4. 添加 API 端点

### Phase 2: 前端 UI
1. 多表选择组件（复选框列表）
2. Schema 级比对表单
3. 结果汇总视图（表格 + 筛选）
4. 进度展示组件

### Phase 3: 增强功能
1. 表名映射 UI
2. 过滤规则配置
3. 报告导出（Excel/PDF）
4. 增量比对支持

---

## 8. 验收标准

### 8.1 多表数据比对

- [ ] 可以选择多个表进行批量比对
- [ ] 支持表名映射配置
- [ ] 返回每张表的比对结果和汇总统计
- [ ] 支持错误处理和超时控制

### 8.2 Schema 级数据比对

- [ ] 自动发现 Schema 下所有表
- [ ] 支持 exclude/include 过滤模式
- [ ] 支持只比对共同表或包含不匹配表
- [ ] 返回未匹配表列表和汇总统计

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大表比对耗时长 | 高 | 默认 hash 模式快速筛查，支持超时控制 |
| 连接池耗尽 | 中 | 串行执行，可配置并发限制 |
| 内存溢出 | 中 | 限制同时处理的表数量，分批处理 |
| 表名不一致 | 低 | 提供手动映射配置 |
