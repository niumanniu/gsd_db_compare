# DB Compare - 数据库库表比对系统

一个面向运维团队的数据库比对工具，支持 MySQL 和 Oracle 数据库，提供表结构比对和数据比对功能。

## 核心价值

让运维团队快速发现和验证数据库结构及数据差异，减少人工比对错误，提高变更验证效率。

## 功能特性

- **多数据库支持** - MySQL (5.7/8.0+)、Oracle (12c/18c/19c+)
- **表结构比对** - 比对字段、索引、约束、默认值的差异
- **数据比对** - 支持全量比对、抽样比对、关键表比对
- **差异可视化** - 清晰展示结构和数据差异
- **报告生成** - 导出 HTML/Excel 格式比对报告
- **连接管理** - 安全存储和管理数据库连接信息
- **定时任务** - 使用 APScheduler 支持计划任务定期执行比对
- **密码加密** - 使用 Fernet 对称加密存储数据库密码

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL (存储应用数据)

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

## 约束

- **只读模式** - 不执行 DDL/DML 写操作
- **内部部署** - 数据不出内网
- **并发限制** - 比对任务串行或小并发，避免影响生产库性能

## 项目结构

```
gsd_db_compare/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API 端点
│   │   ├── db/           # 数据库模型和会话
│   │   ├── adapters/     # 数据库适配器 (MySQL/Oracle)
│   │   ├── comparison/   # 比对引擎
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── reports/      # 报告生成 (HTML/Excel)
│   │   ├── main.py       # FastAPI 应用
│   │   └── worker.py     # 定时任务
│   ├── alembic/          # 数据库迁移
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
- APScheduler - 异步任务调度
- Pydantic - 数据验证
- Cryptography - 密码加密
- MySQL Connector / OracleDB - 数据库驱动

**前端**
- React 18 - UI 框架
- TypeScript - 类型安全
- Ant Design - 组件库
- Zustand - 状态管理
- TanStack Query - 服务端状态管理
- TanStack Table - 表格处理
- Vite - 构建工具

## 目标用户

- **运维工程师** - 环境变更验证、故障排查
- **DBA** - 数据库结构审核、数据一致性检查
- **测试人员** - 测试环境与生产环境比对

## License

MIT
