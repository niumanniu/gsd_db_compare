# Wave 1: 基础设施

**目标:** 完成数据库迁移、APScheduler 调度器、邮件通知模块

---

## Task 1.1: 数据库迁移

**文件:**
- `backend/alembic/versions/002_advanced_features.py`

**表结构:**

### 1. scheduled_tasks (定时任务配置)
```sql
CREATE TABLE scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cron_expression VARCHAR(100) NOT NULL,  -- 如 "0 */2 * * *" 每 2 小时
    source_connection_id INTEGER NOT NULL,
    target_connection_id INTEGER NOT NULL,
    tables TEXT NOT NULL,  -- JSON 数组：[{"source": "tbl1", "target": "tbl2", "critical": true}]
    compare_mode VARCHAR(50) DEFAULT 'schema',  -- schema, data, both
    notification_enabled BOOLEAN DEFAULT true,
    enabled BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_connection_id) REFERENCES db_connections(id),
    FOREIGN KEY (target_connection_id) REFERENCES db_connections(id)
);
```

### 2. comparison_history (比对历史记录)
```sql
CREATE TABLE comparison_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,  -- nullable for ad-hoc comparisons
    source_connection_id INTEGER NOT NULL,
    target_connection_id INTEGER NOT NULL,
    source_table VARCHAR(255) NOT NULL,
    target_table VARCHAR(255) NOT NULL,
    compare_mode VARCHAR(50) NOT NULL,  -- schema, data, both
    source_row_count INTEGER,
    target_row_count INTEGER,
    diff_count INTEGER NOT NULL DEFAULT 0,
    diff_percentage REAL,
    has_critical_diffs BOOLEAN DEFAULT false,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    error_message TEXT,
    result_summary TEXT,  -- JSON: {"column_diffs": N, "index_diffs": N, ...}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id),
    FOREIGN KEY (source_connection_id) REFERENCES db_connections(id),
    FOREIGN KEY (target_connection_id) REFERENCES db_connections(id)
);
CREATE INDEX ix_history_task_id ON comparison_history(task_id);
CREATE INDEX ix_history_status ON comparison_history(status);
CREATE INDEX ix_history_created_at ON comparison_history(created_at);
```

### 3. critical_tables (关键表标记)
```sql
CREATE TABLE critical_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connection_id, table_name),
    FOREIGN KEY (connection_id) REFERENCES db_connections(id) ON DELETE CASCADE
);
CREATE INDEX ix_critical_conn_id ON critical_tables(connection_id);
```

### 4. notification_settings (通知配置)
```sql
CREATE TABLE notification_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smtp_host VARCHAR(255) NOT NULL,
    smtp_port INTEGER NOT NULL DEFAULT 587,
    smtp_username VARCHAR(255) NOT NULL,
    smtp_password_encrypted BLOB NOT NULL,
    use_tls BOOLEAN DEFAULT true,
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255) DEFAULT 'DB Compare',
    default_recipients TEXT,  -- JSON 数组：["email1@example.com", ...]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**验收标准:**
- [ ] Alembic migration 可执行 (`alembic upgrade head`)
- [ ] downgrade 可回滚 (`alembic downgrade -1`)
- [ ] 所有表结构正确
- [ ] 外键约束生效
- [ ] 索引创建成功

---

## Task 1.2: APScheduler 调度器模块

**文件:**
- `backend/app/scheduler/__init__.py`
- `backend/app/scheduler/scheduler.py`
- `backend/app/scheduler/jobs.py`
- `backend/app/scheduler/store.py`

### scheduler.py - 调度器实例管理
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

class SchedulerService:
    def __init__(self, session_factory):
        self.scheduler = None
        self.session_factory = session_factory

    def start(self):
        """初始化并启动调度器"""
        jobstores = {
            'default': SQLAlchemyJobStore(url=self.db_url)
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone='UTC'
        )
        self.scheduler.start()

    def stop(self):
        """停止调度器"""
        if self.scheduler:
            self.scheduler.shutdown()

    def add_job(self, task_id: int, cron_expr: str):
        """添加定时任务"""
        # 解析 cron 表达式并添加 job
        pass

    def remove_job(self, task_id: str):
        """移除定时任务"""
        pass

    def pause_job(self, task_id: str):
        """暂停任务"""
        pass

    def resume_job(self, task_id: str):
        """恢复任务"""
        pass
```

### jobs.py - 比对任务定义
```python
async def execute_scheduled_comparison(task_id: int):
    """执行定时比对任务"""
    # 1. 获取任务配置
    # 2. 获取连接信息
    # 3. 执行比对 (调用现有 comparison 逻辑)
    # 4. 保存历史记录
    # 5. 检查关键表差异
    # 6. 发送通知 (如有差异)
```

### store.py - 任务存储管理
```python
# APScheduler SQLAlchemyJobStore 配置
# 以及自定义任务状态管理
```

**验收标准:**
- [ ] 调度器可启动/停止
- [ ] 可添加 Cron 任务
- [ ] 任务执行时自动调用比对 API
- [ ] 服务重启后任务恢复
- [ ] 支持 pause/resume

---

## Task 1.3: 邮件通知模块

**文件:**
- `backend/app/notifications/__init__.py`
- `backend/app/notifications/email.py`
- `backend/app/notifications/templates.py`
- `backend/app/notifications/templates/alert_email.html`
- `backend/app/notifications/templates/summary_email.html`

### email.py - SMTP 邮件发送
```python
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailService:
    def __init__(self, settings: NotificationSettings):
        self.settings = settings

    async def send_alert(
        self,
        recipients: list[str],
        subject: str,
        html_content: str,
    ) -> bool:
        """发送告警邮件"""
        pass

    async def send_with_retry(
        self,
        message: MIMEMultipart,
        max_retries: int = 3,
        delay: int = 5
    ) -> bool:
        """带重试的发送"""
        pass
```

### templates/alert_email.html - 告警邮件模板
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .alert-critical { background-color: #ffe6e6; border-left: 4px solid #ff4444; }
        .diff-summary { margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="alert-critical">
        <h2>🚨 数据库差异告警</h2>
        <p>任务：{{ task_name }}</p>
        <p>时间：{{ timestamp }}</p>
        <p>严重程度：{{ severity }}</p>
    </div>

    <div class="diff-summary">
        <h3>差异摘要</h3>
        <table>
            <tr><th>源表</th><td>{{ source_table }}</td></tr>
            <tr><th>目标表</th><td>{{ target_table }}</td></tr>
            <tr><th>差异数量</th><td>{{ diff_count }}</td></tr>
        </table>
    </div>

    <a href="{{ report_url }}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">查看详细报告</a>
</body>
</html>
```

**验收标准:**
- [ ] 可配置 SMTP 服务器
- [ ] 邮件发送成功
- [ ] HTML 格式正确
- [ ] 有发送失败日志
- [ ] 支持多收件人

---

## Task 1.4: 依赖更新

**文件:**
- `backend/pyproject.toml`

**修改内容:**
```toml
[project]
dependencies = [
    "fastapi>=0.115,<0.130",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "mysql-connector-python>=8.0",
    "alembic>=1.12",
    "APScheduler>=3.10.0",           # 新增
    "aiosmtplib>=3.0",               # 新增
    "cryptography>=42.0",
    "structlog>=24.0",
    "oracledb>=2.0",
    "Jinja2>=3.1",
    "openpyxl>=3.1",
    # "celery[redis]>=5.4",          # 移除 (如确认无依赖)
]
```

**验收标准:**
- [ ] `uv pip install -e backend` 成功
- [ ] 应用启动正常
- [ ] APScheduler 导入成功
- [ ] 邮件模块导入成功

---

## Wave 1 验收清单

- [ ] 1.1 数据库迁移执行成功
- [ ] 1.2 APScheduler 调度器可添加/执行任务
- [ ] 1.3 邮件可发送成功
- [ ] 1.4 依赖安装成功
- [ ] 所有单元测试通过
- [ ] 代码审查通过
