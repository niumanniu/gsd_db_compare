# Phase 4: Architecture Documentation

**Overview:** APScheduler 定时任务调度与邮件告警系统架构

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FastAPI Application                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      API Layer                               │    │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐ │    │
│  │  │scheduled_tasks  │ │    history      │ │critical_tables │ │    │
│  │  │    /api/        │ │   /api/         │ │   /api/        │ │    │
│  │  └────────┬────────┘ └────────┬────────┘ └───────┬────────┘ │    │
│  └───────────┼───────────────────┼──────────────────┼──────────┘    │
│              │                   │                  │               │
│  ┌───────────▼───────────────────▼──────────────────▼──────────┐    │
│  │                     Service Layer                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │    │
│  │  │  Scheduler   │  │ Notification │  │  Comparison     │   │    │
│  │  │   Service    │  │   Service    │  │   Service       │   │    │
│  │  │  (APScheduler)│ │  (SMTP/Email)│  │                 │   │    │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Job Executor                              │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │  execute_scheduled_comparison(task_id)               │   │    │
│  │  │    ├─ Fetch task config                              │   │    │
│  │  │    ├─ Get connections                                │   │    │
│  │  │    ├─ Run comparison (schema/data)                   │   │    │
│  │  │    ├─ Save history                                   │   │    │
│  │  │    ├─ Check critical diffs                           │   │    │
│  │  │    └─ Send notification (if needed)                  │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Database (PostgreSQL)                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │
│  │ scheduled_tasks │ │comparison_history│ │ critical_tables │        │
│  │ - id            │ │ - id            │ │ - id            │        │
│  │ - name          │ │ - task_id       │ │ - connection_id │        │
│  │ - cron_expr     │ │ - source_table  │ │ - table_name    │        │
│  │ - tables (JSON) │ │ - diff_count    │ │ - description   │        │
│  │ - enabled       │ │ - status        │ │                 │        │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘        │
│  ┌─────────────────┐ ┌─────────────────┐                            │
│  │notification_set │ │ apscheduler_... │  (APScheduler internal)    │
│  │ - smtp_host     │ │ - job_id        │                            │
│  │ - smtp_port     │ │ - next_run      │                            │
│  │ - sender_email  │ │ - job_state     │                            │
│  └─────────────────┘ └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        External Services                             │
│  ┌─────────────────┐                                               │
│  │   SMTP Server   │ ◄── Email notifications                       │
│  │   (SendGrid/    │     - Alert emails                            │
│  │    Gmail/ etc)  │     - Summary reports                         │
│  └─────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Scheduler Service

**职责:** 定时任务调度管理

**核心类:**
```python
class SchedulerService:
    """APScheduler 调度器服务"""

    def __init__(self, session_factory: async_sessionmaker):
        self.scheduler: AsyncIOScheduler
        self.session_factory = session_factory

    def start(self) -> None:
        """启动调度器"""

    def stop(self) -> None:
        """停止调度器"""

    async def add_job(self, task: ScheduledTask) -> str:
        """添加定时任务"""

    async def remove_job(self, task_id: int) -> None:
        """移除定时任务"""

    async def pause_job(self, task_id: int) -> None:
        """暂停任务"""

    async def resume_job(self, task_id: int) -> None:
        """恢复任务"""

    async def load_persisted_tasks(self) -> None:
        """从数据库加载已存在的任务"""
```

**Cron 表达式格式:**
```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 6, 0=Sunday)
│ │ │ │ │
* * * * *
```

**预设 Cron 表达式:**
| 频率 | 表达式 |
|------|--------|
| 每分钟 | `* * * * *` |
| 每 5 分钟 | `*/5 * * * *` |
| 每小时 | `0 * * * *` |
| 每 2 小时 | `0 */2 * * *` |
| 每天 2 点 | `0 2 * * *` |
| 每周一 9 点 | `0 9 * * 1` |
| 每月 1 号 | `0 0 1 * *` |

---

### 2. Notification Service

**职责:** 邮件通知发送

**核心类:**
```python
class EmailService:
    """SMTP 邮件通知服务"""

    def __init__(self, settings: NotificationSettings):
        self.settings = settings

    async def send_alert(
        self,
        recipients: list[str],
        subject: str,
        html_content: str,
    ) -> bool:
        """发送告警邮件"""

    async def send_with_retry(
        self,
        message: MIMEMultipart,
        max_retries: int = 3,
        delay: int = 5,
    ) -> bool:
        """带重试的发送"""
```

**邮件模板:**
- `alert_email.html` - 关键差异告警
- `summary_email.html` - 汇总报告

---

### 3. Comparison Executor

**职责:** 执行比对任务

**核心函数:**
```python
async def execute_scheduled_comparison(
    task_id: int,
    execution_type: str = "scheduled",  # or "manual"
) -> ComparisonResult:
    """
    执行定时比对任务

    流程:
    1. 获取任务配置
    2. 获取数据库连接
    3. 执行比对 (schema/data)
    4. 保存历史记录
    5. 检查关键表差异
    6. 发送通知 (如需要)
    """
```

---

### 4. Database Models

**scheduled_tasks:**
```python
class ScheduledTaskModel(Base):
    __tablename__ = "scheduled_tasks"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False)
    cron_expression: str = Column(String(100), nullable=False)
    tables: dict = Column(JSON, nullable=False)  # [{"source": str, "target": str, "critical": bool}]
    enabled: bool = Column(Boolean, default=True)
    # ... 其他字段
```

**comparison_history:**
```python
class ComparisonHistoryModel(Base):
    __tablename__ = "comparison_history"

    id: int = Column(Integer, primary_key=True)
    task_id: Optional[int] = Column(Integer, ForeignKey("scheduled_tasks.id"))
    diff_count: int = Column(Integer, default=0)
    has_critical_diffs: bool = Column(Boolean, default=False)
    status: str = Column(String(50), nullable=False)
    # ... 其他字段
```

**critical_tables:**
```python
class CriticalTableModel(Base):
    __tablename__ = "critical_tables"

    id: int = Column(Integer, primary_key=True)
    connection_id: int = Column(Integer, ForeignKey("db_connections.id"))
    table_name: str = Column(String(255), nullable=False)
    # ... 其他字段
```

---

## Data Flow

### 定时任务执行流程

```
1. APScheduler 触发任务
         │
         ▼
2. execute_scheduled_comparison(task_id)
         │
         ├─► 3. Fetch task config from DB
         │
         ├─► 4. Get connections (source/target)
         │
         ├─► 5. Run comparison
         │       │
         │       ├─► Schema comparison
         │       └─► Data comparison (if configured)
         │
         ├─► 6. Save result to comparison_history
         │
         ├─► 7. Check for critical diffs
         │       │
         │       ├─► Has critical diffs ──► 8. Send email notification
         │       │
         │       └─► No critical diffs ──► (skip notification)
         │
         └─► 9. Update task last_run_at
```

### 邮件通知触发条件

```
比对完成
    │
    ▼
检查 has_critical_diffs
    │
    ├─► True ──► 检查 notification_enabled
    │               │
    │               ├─► True ──► 发送邮件
    │               │
    │               └─► False ──► 不发送
    │
    └─► False ──► 不发送
```

---

## API Endpoints Summary

### Scheduled Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scheduled-tasks` | 创建任务 |
| GET | `/api/scheduled-tasks` | 获取列表 |
| GET | `/api/scheduled-tasks/{id}` | 获取详情 |
| PUT | `/api/scheduled-tasks/{id}` | 更新任务 |
| DELETE | `/api/scheduled-tasks/{id}` | 删除任务 |
| POST | `/api/scheduled-tasks/{id}/run` | 手动执行 |
| POST | `/api/scheduled-tasks/{id}/toggle` | 启用/禁用 |

### Comparison History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/comparison-history` | 获取列表 |
| GET | `/api/comparison-history/{id}` | 获取详情 |
| GET | `/api/comparison-history/trend` | 趋势分析 |
| GET | `/api/comparison-history/stats` | 统计摘要 |

### Critical Tables
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/critical-tables` | 标记关键表 |
| DELETE | `/api/critical-tables/{id}` | 移除标记 |
| GET | `/api/critical-tables` | 获取列表 |
| GET | `/api/critical-tables/check` | 检查是否关键 |

---

## Security Considerations

### 1. 密码加密
- SMTP 密码使用 Fernet 加密存储
- 与数据库连接密码使用相同加密方案

### 2. 访问控制
- (可选) API 端点需要认证
- 定时任务只能由授权用户创建/修改

### 3. 输入验证
- Cron 表达式格式验证
- 表名白名单验证 (防止 SQL 注入)

### 4. 审计日志
- 所有任务执行记录到 `comparison_history`
- 邮件发送记录日志

---

## Scalability

### 单实例限制

APScheduler 设计为单进程调度器，不支持分布式。如需多实例部署:

**方案 A: 数据库锁**
```python
# 使用数据库行锁确保只有一个实例执行任务
async with db.begin():
    task = await db.get(ScheduledTask, task_id, for_update=True)
    if not task.locked_by or task.lock_expired():
        task.lock_by(instance_id)
        await execute()
```

**方案 B: 外部协调**
- 使用 Redis 分布式锁
- 使用 Kubernetes CronJob 替代

### 性能优化

| 优化项 | 方案 |
|--------|------|
| 历史数据归档 | 定期归档旧记录到冷存储 |
| 查询缓存 | 趋势数据缓存 5 分钟 |
| 并发控制 | 同一任务不允许多实例并发执行 |
| 邮件限流 | 每分钟最多发送 N 封邮件 |

---

## Monitoring

### 健康检查

```python
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "scheduler": scheduler.is_running(),
        "smtp": smtp_connected,
    }
```

### 关键指标

| 指标 | 说明 |
|------|------|
| `scheduler_jobs_count` | 调度器中任务数量 |
| `comparisons_total` | 累计比对次数 |
| `comparisons_failed` | 失败次数 |
| `emails_sent_total` | 邮件发送总数 |
| `critical_diffs_count` | 关键差异数量 |

---

*Last updated: 2026-03-28*
