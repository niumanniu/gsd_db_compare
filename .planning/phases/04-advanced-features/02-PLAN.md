# Wave 2: API 开发

**目标:** 完成所有后端 API 接口

**依赖:** Wave 1 完成 (数据库迁移、调度器、邮件模块)

---

## Task 2.1: 任务管理 API

**文件:**
- `backend/app/api/scheduled_tasks.py`
- `backend/app/schemas/scheduled_tasks.py`

### Pydantic Schemas

```python
# backend/app/schemas/scheduled_tasks.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TableMapping(BaseModel):
    """表映射配置"""
    source: str
    target: str
    critical: bool = False

class ScheduledTaskCreate(BaseModel):
    """创建定时任务请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cron_expression: str = Field(..., description="Cron 表达式，如 '0 */2 * * *'")
    source_connection_id: int
    target_connection_id: int
    tables: List[TableMapping]
    compare_mode: str = Field(default='schema', pattern='^(schema|data|both)$')
    notification_enabled: bool = True
    enabled: bool = True

class ScheduledTaskUpdate(BaseModel):
    """更新定时任务请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    tables: Optional[List[TableMapping]] = None
    compare_mode: Optional[str] = None
    notification_enabled: Optional[bool] = None
    enabled: Optional[bool] = None

class ScheduledTaskResponse(BaseModel):
    """定时任务响应"""
    id: int
    name: str
    description: Optional[str]
    cron_expression: str
    source_connection_id: int
    target_connection_id: int
    tables: List[TableMapping]
    compare_mode: str
    notification_enabled: bool
    enabled: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### API Endpoints

```python
# backend/app/api/scheduled_tasks.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db_session
from app.scheduler import get_scheduler_service

router = APIRouter(prefix="/api/scheduled-tasks", tags=["scheduled-tasks"])

@router.post("", response_model=ScheduledTaskResponse, status_code=201)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """创建定时任务"""
    # 1. 验证连接存在
    # 2. 创建数据库记录
    # 3. 添加到 APScheduler
    # 4. 返回任务信息
    pass

@router.get("", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
) -> List[ScheduledTaskResponse]:
    """获取定时任务列表"""
    query = select(ScheduledTaskModel)
    if enabled_only:
        query = query.where(ScheduledTaskModel.enabled == True)
    result = await db.execute(query.order_by(ScheduledTaskModel.name))
    return result.scalars().all()

@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """获取定时任务详情"""
    pass

@router.put("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """更新定时任务"""
    # 1. 更新数据库记录
    # 2. 如果 cron 表达式变化，更新调度器
    # 3. 如果 enabled 状态变化，pause/resume 任务
    pass

@router.delete("/{task_id}", status_code=204)
async def delete_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """删除定时任务"""
    # 1. 从调度器移除
    # 2. 删除数据库记录
    pass

@router.post("/{task_id}/run", response_model=dict)
async def run_scheduled_task_now(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """手动立即执行定时任务"""
    # 1. 触发一次比对任务
    # 2. 返回执行状态
    return {"status": "started", "message": "Task execution started"}

@router.post("/{task_id}/toggle", response_model=ScheduledTaskResponse)
async def toggle_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """启用/禁用定时任务"""
    # 1. 切换 enabled 状态
    # 2. pause/resume 调度器任务
    pass
```

**验收标准:**
- [ ] 所有端点可调用
- [ ] 参数验证正确 (Cron 表达式格式、连接存在性)
- [ ] 与 APScheduler 集成正常
- [ ] 错误处理完善 (404, 400, 500)
- [ ] Swagger 文档完整

---

## Task 2.2: 历史查询 API

**文件:**
- `backend/app/api/history.py`
- `backend/app/schemas/history.py`

### Pydantic Schemas

```python
# backend/app/schemas/history.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class HistoryRecord(BaseModel):
    """单次比对历史记录"""
    id: int
    task_id: Optional[int]
    source_connection_id: int
    target_connection_id: int
    source_table: str
    target_table: str
    compare_mode: str
    source_row_count: Optional[int]
    target_row_count: Optional[int]
    diff_count: int
    diff_percentage: Optional[float]
    has_critical_diffs: bool
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    result_summary: Optional[dict]
    created_at: datetime

class TrendDataPoint(BaseModel):
    """趋势图数据点"""
    date: str
    diff_count: int
    completed_count: int

class TrendResponse(BaseModel):
    """趋势分析响应"""
    period: str  # daily, weekly, monthly
    data_points: List[TrendDataPoint]
    total_comparisons: int
    total_diffs: int
    avg_diff_count: float

class HistoryStats(BaseModel):
    """统计摘要"""
    total_comparisons: int
    completed: int
    failed: int
    avg_diff_count: float
    max_diff_count: int
    last_24h_comparisons: int
    last_7d_comparisons: int
```

### API Endpoints

```python
# backend/app/api/history.py

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

router = APIRouter(prefix="/api/comparison-history", tags=["history"])

@router.get("", response_model=List[HistoryRecord])
async def list_comparison_history(
    task_id: Optional[int] = Query(None, description="按任务 ID 筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> List[HistoryRecord]:
    """获取历史记录列表 (分页)"""
    offset = (page - 1) * limit
    query = select(HistoryRecord)
    if task_id:
        query = query.where(HistoryRecord.task_id == task_id)
    if status:
        query = query.where(HistoryRecord.status == status)
    query = query.order_by(HistoryRecord.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{history_id}", response_model=HistoryRecord)
async def get_comparison_history(
    history_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> HistoryRecord:
    """获取单次比对详情"""
    pass

@router.get("/trend", response_model=TrendResponse)
async def get_comparison_trend(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    task_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> TrendResponse:
    """获取趋势分析数据"""
    # 1. 按时间段聚合 diff_count
    # 2. 计算平均值和总数
    # 3. 返回趋势图数据
    pass

@router.get("/stats", response_model=HistoryStats)
async def get_comparison_stats(
    task_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> HistoryStats:
    """获取统计摘要"""
    # 1. 总数、完成数、失败数
    # 2. 平均差异数
    # 3. 最近 24h/7d 统计
    pass
```

**验收标准:**
- [ ] 分页查询正常
- [ ] 趋势数据计算正确
- [ ] 统计摘要准确
- [ ] 查询性能良好 (有索引)
- [ ] 大数据量下响应时间 <500ms

---

## Task 2.3: 关键表管理 API

**文件:**
- `backend/app/api/critical_tables.py`
- `backend/app/schemas/critical_tables.py`

### Pydantic Schemas

```python
# backend/app/schemas/critical_tables.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CriticalTableCreate(BaseModel):
    """标记关键表请求"""
    connection_id: int
    table_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class CriticalTableResponse(BaseModel):
    """关键表响应"""
    id: int
    connection_id: int
    table_name: str
    description: Optional[str]
    created_at: datetime

class CriticalTableCheckResponse(BaseModel):
    """关键表检查响应"""
    is_critical: bool
    table_name: str
    connection_id: int
```

### API Endpoints

```python
# backend/app/api/critical_tables.py

from fastapi import APIRouter, HTTPException, Depends, Query, status

router = APIRouter(prefix="/api/critical-tables", tags=["critical-tables"])

@router.post("", response_model=CriticalTableResponse, status_code=201)
async def mark_critical_table(
    table_data: CriticalTableCreate,
    db: AsyncSession = Depends(get_db_session),
) -> CriticalTableResponse:
    """标记关键表"""
    # 1. 检查是否已存在
    # 2. 创建记录
    # 3. 返回
    pass

@router.delete("/{table_id}", status_code=204)
async def unmark_critical_table(
    table_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """移除关键表标记"""
    pass

@router.get("", response_model=List[CriticalTableResponse])
async def list_critical_tables(
    connection_id: int = Query(..., description="连接 ID"),
    db: AsyncSession = Depends(get_db_session),
) -> List[CriticalTableResponse]:
    """获取连接的关键表列表"""
    pass

@router.get("/check", response_model=CriticalTableCheckResponse)
async def check_critical_table(
    connection_id: int = Query(...),
    table_name: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
) -> CriticalTableCheckResponse:
    """检查表是否是关键表"""
    pass
```

**验收标准:**
- [ ] 标记功能正常
- [ ] 唯一性约束生效
- [ ] 按连接查询正确
- [ ] 与告警逻辑集成 (差异检查时判断关键表)

---

## Task 2.4: API 集成测试

**文件:**
- `backend/tests/test_scheduled_tasks.py`
- `backend/tests/test_history.py`
- `backend/tests/test_critical_tables.py`

### 测试用例示例

```python
# backend/tests/test_scheduled_tasks.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_scheduled_task(client: AsyncClient, test_connections):
    """测试创建定时任务"""
    response = await client.post("/api/scheduled-tasks", json={
        "name": "Daily Schema Check",
        "cron_expression": "0 2 * * *",
        "source_connection_id": test_connections[0].id,
        "target_connection_id": test_connections[1].id,
        "tables": [
            {"source": "users", "target": "users", "critical": True}
        ],
        "compare_mode": "schema"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Daily Schema Check"
    assert data["enabled"] == True

@pytest.mark.asyncio
async def test_toggle_scheduled_task(client: AsyncClient, test_task):
    """测试启用/禁用任务"""
    response = await client.post(f"/api/scheduled-tasks/{test_task.id}/toggle")
    assert response.status_code == 200
    assert response.json()["enabled"] == False

@pytest.mark.asyncio
async def test_invalid_cron_expression(client: AsyncClient):
    """测试无效 Cron 表达式"""
    response = await client.post("/api/scheduled-tasks", json={
        "name": "Invalid Task",
        "cron_expression": "invalid",
        "source_connection_id": 1,
        "target_connection_id": 2,
        "tables": []
    })
    assert response.status_code == 400
```

**验收标准:**
- [ ] 测试覆盖率 >80%
- [ ] 所有测试通过
- [ ] 有集成测试用例
- [ ] 有 mock 数据
- [ ] CI/CD 可运行测试

---

## Wave 2 验收清单

- [ ] 2.1 任务管理 API 所有端点工作正常
- [ ] 2.2 历史查询 API 分页和趋势数据正确
- [ ] 2.3 关键表管理 API 集成正常
- [ ] 2.4 测试覆盖率 >80%
- [ ] Swagger 文档完整 (`/docs`)
- [ ] 代码审查通过
