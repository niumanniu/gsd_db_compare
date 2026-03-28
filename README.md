# DB Compare - 数据库结构比对工具

一个用于比对不同数据库表结构差异的工具，支持 MySQL 和 Oracle 数据库。

## 功能特性

- **数据库连接管理** - 安全存储和管理多个数据库连接配置
- **表结构比对** - 比对字段、索引、约束的差异
- **可视化展示** - 清晰直观的差异展示界面
- **异步任务处理** - 使用 Celery 处理长时间运行的比对任务
- **密码加密** - 使用 Fernet 对称加密存储数据库密码

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL (存储应用数据)
- Redis (Celery 消息队列)

### 后端设置

```bash
cd backend

# 安装依赖
pip install -e .

# 复制环境变量配置
cp .env.example .env

# 生成加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 将输出复制到 .env 文件的 ENCRYPTION_KEY

# 修改 .env 中的数据库连接字符串

# 初始化数据库
alembic upgrade head

# 启动 Celery worker
celery -A celery_config worker --loglevel=info

# 启动 API 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

## 环境变量

### 后端 (.env)

| 变量 | 说明 | 示例 |
|------|------|------|
| DATABASE_URL | PostgreSQL 连接字符串 | postgresql://user:pass@localhost/db_compare |
| ENCRYPTION_KEY | 密码加密密钥 (32 字节) | gAAAAABk... |
| CELERY_BROKER_URL | Redis broker URL | redis://localhost:6379/0 |
| CELERY_RESULT_BACKEND | Redis 结果存储 | redis://localhost:6379/1 |
| LOG_LEVEL | 日志级别 | INFO |

### 前端 (.env)

| 变量 | 说明 | 示例 |
|------|------|------|
| VITE_API_BASE_URL | API 地址 | http://localhost:8000 |

## 使用指南

### 1. 创建数据库连接

1. 点击"Add Connection"按钮
2. 填写连接信息：
   - 连接名称
   - 数据库类型 (MySQL/Oracle)
   - 主机地址
   - 端口
   - 数据库名
   - 用户名
   - 密码
3. 系统会自动测试连接
4. 连接成功后保存

### 2. 比对表结构

1. 切换到"Schema Comparison"标签
2. 选择源连接和目标连接
3. 选择要比对的表
4. 点击"Compare Schemas"
5. 查看差异结果

### 差异类型说明

- **ADDED (绿色)** - 仅在目标表中存在
- **REMOVED (红色)** - 仅在源表中存在
- **MODIFIED (黄色)** - 在两个表中都存在但定义不同

## 项目结构

```
gsd_db_compare/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API 端点
│   │   ├── db/           # 数据库模型和会话
│   │   ├── adapters/     # 数据库适配器
│   │   ├── comparison/   # 比对引擎
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── main.py       # FastAPI 应用
│   │   └── worker.py     # Celery 任务
│   ├── alembic/          # 数据库迁移
│   ├── celery_config.py  # Celery 配置
│   └── pyproject.toml    # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── components/   # React 组件
│   │   ├── hooks/        # React hooks
│   │   ├── types/        # TypeScript 类型
│   │   └── App.tsx       # 主应用
│   └── package.json      # Node 依赖
└── .planning/            # 项目规划文档
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/connections | 创建连接 |
| GET | /api/connections | 获取连接列表 |
| GET | /api/connections/{id}/tables | 获取表列表 |
| POST | /api/compare/schema | 比对表结构 |
| GET | /health | 健康检查 |

## 开发

### 运行测试

```bash
cd backend
pytest
```

### 代码格式化

```bash
cd backend
black .
isort .
```

## 技术栈

**后端**
- FastAPI - Web 框架
- SQLAlchemy 2.0 - ORM
- Alembic - 数据库迁移
- Celery - 异步任务
- Pydantic - 数据验证

**前端**
- React 18 - UI 框架
- TypeScript - 类型安全
- Ant Design - 组件库
- React Query - 服务端状态管理
- Vite - 构建工具

## License

MIT
