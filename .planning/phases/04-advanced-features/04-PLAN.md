# Wave 4: Celery 迁移与集成测试

**目标:** 移除 Celery，完成集成测试和文档

**依赖:** Wave 3 完成 (前端 UI)

---

## Task 4.1: Celery 使用情况检查

**检查清单:**

### 1. 文件检查

```bash
# 检查 Celery 相关文件
ls -la backend/celery_config.py
ls -la backend/app/worker.py

# 搜索 Celery 引用
grep -r "celery" backend/ --include="*.py"
grep -r "@celery" backend/ --include="*.py"
grep -r "\.delay(" backend/ --include="*.py"
grep -r "\.apply_async(" backend/ --include="*.py"
```

### 2. 代码审查

**backend/celery_config.py:**
```python
# 检查内容
- Celery 应用配置
- Broker/Backend 配置
- 任务序列化设置
```

**backend/app/worker.py:**
```python
# 检查内容
- @celery.task 装饰器
- 任务定义 (compare_schema_task)
- 任务调用方式
```

### 3. 依赖检查

```bash
# 检查 pyproject.toml
grep celery backend/pyproject.toml

# 检查实际导入
python -c "import celery; print(celery.__version__)"
```

### 4. 运行时报文检查

```bash
# 启动应用，检查是否有 Celery 相关日志
uvicorn app.main:app --reload
```

### 输出报告

**Celery 使用报告模板:**

```markdown
## Celery 使用报告

### 发现的文件
- [ ] backend/celery_config.py
- [ ] backend/app/worker.py

### 任务列表
| 任务名 | 用途 | 调用位置 |
|--------|------|----------|
| compare_schema_task | 异步比对架构 | POST /api/compare/schema |

### 调用方式
- [ ] 同步调用 (.delay())
- [ ] 异步调用 (.apply_async())
- [ ] 链式调用 (chain, group)

### 迁移建议
- [ ] 完全移除 (无其他依赖)
- [ ] 部分迁移 (保留其他功能)
- [ ] 暂不迁移 (需要进一步评估)
```

**验收标准:**
- [ ] 完成所有检查项
- [ ] 输出书面报告
- [ ] 明确迁移方案

---

## Task 4.2: Celery 代码迁移/移除

### 方案 A: 完全移除 (推荐)

**前提:** Celery 仅用于比对任务，无其他依赖

**步骤:**

1. **删除 Celery 文件**
```bash
rm backend/celery_config.py
rm backend/app/worker.py
```

2. **更新 pyproject.toml**
```toml
[project]
dependencies = [
    "fastapi>=0.115,<0.130",
    # ... 其他依赖
    "APScheduler>=3.10.0",
    "aiosmtplib>=3.0",
    # "celery[redis]>=5.4",  # 注释或删除
    # "redis>=5.0",          # 如仅 Celery 使用，可删除
]
```

3. **更新 main.py (移除 Celery 导入)**
```python
# backend/app/main.py

# 删除 Celery 相关导入
# from celery_config import celery_app

# 添加 APScheduler 生命周期管理
from app.scheduler import get_scheduler_service

@app.on_event("startup")
async def startup_event():
    """启动时初始化调度器"""
    scheduler = get_scheduler_service()
    scheduler.start()
    # 加载现有定时任务到调度器
    await scheduler.load_persisted_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时停止调度器"""
    scheduler = get_scheduler_service()
    scheduler.stop()
```

4. **更新比对 API (如需要)**

如果现有 API 使用 Celery 异步执行，需要改为:
- 方案 1: 直接同步执行 (适用于快速比对)
- 方案 2: 使用 APScheduler 的 `add_job()` 一次性任务

```python
# 方案 2 示例
@router.post("/schema", response_model=SchemaDiffResponse)
async def compare_schemas(request: SchemaCompareRequest) -> SchemaDiffResponse:
    # 创建一次性任务
    job_id = f"adhoc_{uuid4()}"
    scheduler.add_job(
        execute_comparison,
        args=[request],
        id=job_id,
        misfire_grace_time=None,  # 立即执行
    )
    return {"status": "queued", "job_id": job_id}
```

### 方案 B: 部分保留

**前提:** 其他功能依赖 Celery

**步骤:**

1. **保留 celery_config.py**
2. **迁移比对任务到 APScheduler**
3. **更新 worker.py 为 APScheduler 任务**

```python
# backend/app/worker.py -> backend/app/scheduler/jobs.py

from app.scheduler.scheduler import get_scheduler_service

# 不再使用 @celery.task 装饰器
async def execute_scheduled_comparison(task_id: int):
    """定时比对任务 (原 compare_schema_task)"""
    # 逻辑保持不变
    pass
```

**验收标准:**
- [ ] Celery 依赖移除 (或保留最小化)
- [ ] 原有功能正常
- [ ] 代码清理完成
- [ ] 应用启动无 Celery 错误

---

## Task 4.3: 集成测试和文档

### 集成测试用例

**测试脚本:** `backend/tests/integration/test_phase4.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_scheduled_task_workflow(client: AsyncClient):
    """测试完整定时任务工作流"""
    # 1. 创建连接
    conn1 = await create_test_connection(client, "源库")
    conn2 = await create_test_connection(client, "目标库")

    # 2. 创建定时任务
    task_response = await client.post("/api/scheduled-tasks", json={
        "name": "测试任务",
        "cron_expression": "0 */2 * * *",
        "source_connection_id": conn1.id,
        "target_connection_id": conn2.id,
        "tables": [{"source": "users", "target": "users", "critical": True}],
    })
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    # 3. 手动执行任务
    run_response = await client.post(f"/api/scheduled-tasks/{task_id}/run")
    assert run_response.status_code == 200

    # 4. 等待执行完成 (模拟)
    await asyncio.sleep(5)

    # 5. 检查历史记录
    history_response = await client.get(
        "/api/comparison-history",
        params={"task_id": task_id}
    )
    assert len(history_response.json()) > 0

    # 6. 检查趋势数据
    trend_response = await client.get("/api/comparison-history/trend")
    assert trend_response.status_code == 200

    # 7. 禁用任务
    toggle_response = await client.post(f"/api/scheduled-tasks/{task_id}/toggle")
    assert toggle_response.json()["enabled"] == False

    # 8. 删除任务
    delete_response = await client.delete(f"/api/scheduled-tasks/{task_id}")
    assert delete_response.status_code == 204
```

### 邮件通知测试

```python
@pytest.mark.asyncio
async def test_email_notification_on_critical_diff(
    client: AsyncClient,
    mock_smtp_server,
):
    """测试关键表差异触发邮件通知"""
    # 1. 标记关键表
    await client.post("/api/critical-tables", json={
        "connection_id": 1,
        "table_name": "users"
    })

    # 2. 创建带通知的任务
    task = await create_scheduled_task(client, notification_enabled=True)

    # 3. 执行任务 (模拟差异)
    await client.post(f"/api/scheduled-tasks/{task.id}/run")

    # 4. 验证邮件发送
    assert mock_smtp_server.email_sent
    assert "关键表差异" in mock_smtp_server.last_email.subject
```

### 文档

**文件:** `.planning/phases/04-advanced-features/VERIFY.md`

```markdown
# Phase 4 验证文档

## 功能验证

### 定时任务管理
- [ ] 创建定时任务成功
- [ ] Cron 表达式验证正确
- [ ] 启用/禁用任务成功
- [ ] 手动执行任务成功
- [ ] 删除任务成功

### 邮件通知
- [ ] SMTP 配置保存成功
- [ ] 邮件发送成功
- [ ] 关键表差异触发告警
- [ ] 非关键表差异不告警

### 历史记录
- [ ] 历史记录保存成功
- [ ] 分页查询正常
- [ ] 趋势图数据正确
- [ ] 统计摘要准确

### 关键表管理
- [ ] 标记关键表成功
- [ ] 取消标记成功
- [ ] 列表查询正确
- [ ] UI 高亮显示

## 技术验证

### APScheduler
- [ ] 调度器启动/停止正常
- [ ] 任务持久化到数据库
- [ ] 服务重启后任务恢复
- [ ] 并发任务不冲突

### Celery 迁移
- [ ] Celery 依赖移除
- [ ] 原有功能正常
- [ ] 无 Celery 相关错误

## 性能验证
- [ ] 历史查询响应 <500ms
- [ ] 邮件发送 <5s
- [ ] 调度器内存占用 <50MB
```

### 用户文档 (可选)

**文件:** `docs/user-guide/scheduled-tasks.md`

```markdown
# 定时任务使用指南

## 创建定时任务

1. 导航到「定时任务」页面
2. 点击「新建任务」
3. 填写任务信息:
   - 任务名称
   - Cron 表达式 (或使用快捷选择)
   - 源/目标连接
   - 表映射
4. 点击保存

## Cron 表达式示例

| 频率 | 表达式 |
|------|--------|
| 每分钟 | `* * * * *` |
| 每小时 | `0 * * * *` |
| 每天 2 点 | `0 2 * * *` |
| 每周一 9 点 | `0 9 * * 1` |

## 邮件告警配置

1. 导航到「设置」> 「通知配置」
2. 填写 SMTP 服务器信息
3. 测试连接
4. 保存

## 查看历史记录

1. 导航到「历史记录」页面
2. 使用筛选器查找特定任务
3. 点击记录查看详情
4. 查看趋势图表
```

**验收标准:**
- [ ] 所有功能端到端测试通过
- [ ] 用户文档完整
- [ ] 有故障排查指南
- [ ] 代码审查通过

---

## Wave 4 验收清单

- [ ] 4.1 Celery 使用报告完成
- [ ] 4.2 Celery 迁移/移除完成
- [ ] 4.3 集成测试全部通过
- [ ] 4.3 验证文档完成
- [ ] 用户文档完成
- [ ] Phase 4 总结完成
