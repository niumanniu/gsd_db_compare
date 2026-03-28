#!/bin/bash
# DB Compare 项目启动脚本
# 启动后端 API 服务和前端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# PID 文件目录
PID_DIR="$PROJECT_ROOT/.pids"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"

# 检查环境变量文件
check_env() {
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        echo -e "${YELLOW}警告：backend/.env 文件不存在${NC}"
        echo -e "${YELLOW}请复制 backend/.env.example 并配置必要的环境变量${NC}"
        if [ -f "$BACKEND_DIR/.env.example" ]; then
            echo -e "${GREEN}正在从 .env.example 创建 .env 文件...${NC}"
            cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
            echo -e "${GREEN}.env 文件已创建，请编辑后重新运行此脚本${NC}"
        fi
        exit 1
    fi
}

# 检查 Python 依赖
check_python_deps() {
    echo -e "${GREEN}检查 Python 依赖...${NC}"
    cd "$BACKEND_DIR"
    if ! python -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}安装 Python 依赖...${NC}"
        pip install -e .
    fi
}

# 检查 Node 依赖
check_node_deps() {
    echo -e "${GREEN}检查 Node 依赖...${NC}"
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装 Node 依赖...${NC}"
        npm install
    fi
}

# 检查数据库
check_database() {
    echo -e "${GREEN}检查数据库...${NC}"
    cd "$BACKEND_DIR"
    if ! python -c "from app.db.session import engine" 2>/dev/null; then
        echo -e "${YELLOW}数据库未初始化，正在执行迁移...${NC}"
        alembic upgrade head
    fi
}

# 启动后端服务
start_backend() {
    echo -e "${GREEN}启动后端服务...${NC}"

    # 创建 PID 和日志目录
    mkdir -p "$PID_DIR" "$LOG_DIR"

    cd "$BACKEND_DIR"

    # 检查后端是否已在运行
    if [ -f "$PID_DIR/backend.pid" ]; then
        PID=$(cat "$PID_DIR/backend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}后端服务已在运行 (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}检测到无效的 PID 文件，清理中...${NC}"
            rm -f "$PID_DIR/backend.pid"
        fi
    fi

    # 启动后端
    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        > "$LOG_DIR/backend.log" 2>&1 &

    PID=$!
    echo $PID > "$PID_DIR/backend.pid"

    # 等待后端启动
    sleep 3
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}后端服务已启动 (PID: $PID)${NC}"
        echo -e "${GREEN}API 文档：http://localhost:8000/docs${NC}"
    else
        echo -e "${RED}后端服务启动失败，请查看 logs/backend.log${NC}"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${GREEN}启动前端服务...${NC}"

    # 创建 PID 和日志目录
    mkdir -p "$PID_DIR" "$LOG_DIR"

    cd "$FRONTEND_DIR"

    # 检查前端是否已在运行
    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}前端服务已在运行 (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}检测到无效的 PID 文件，清理中...${NC}"
            rm -f "$PID_DIR/frontend.pid"
        fi
    fi

    # 启动前端
    nohup npm run dev \
        > "$LOG_DIR/frontend.log" 2>&1 &

    PID=$!
    echo $PID > "$PID_DIR/frontend.pid"

    # 等待前端启动
    sleep 3
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}前端服务已启动 (PID: $PID)${NC}"
        echo -e "${GREEN}访问地址：http://localhost:5173${NC}"
    else
        echo -e "${RED}前端服务启动失败，请查看 logs/frontend.log${NC}"
        return 1
    fi
}

# 显示状态
show_status() {
    echo ""
    echo "================================"
    echo -e "${GREEN}DB Compare 服务状态${NC}"
    echo "================================"

    if [ -f "$PID_DIR/backend.pid" ]; then
        PID=$(cat "$PID_DIR/backend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "后端：${GREEN}运行中${NC} (PID: $PID)"
        else
            echo -e "后端：${RED}未运行${NC}"
        fi
    else
        echo -e "后端：${RED}未启动${NC}"
    fi

    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "前端：${GREEN}运行中${NC} (PID: $PID)"
        else
            echo -e "前端：${RED}未运行${NC}"
        fi
    else
        echo -e "前端：${RED}未启动${NC}"
    fi

    echo "================================"
}

# 主函数
main() {
    echo ""
    echo "================================"
    echo -e "${GREEN}DB Compare - 数据库比对系统${NC}"
    echo "================================"
    echo ""

    # 检查环境
    check_env
    check_python_deps
    check_node_deps
    check_database

    # 启动服务
    start_backend
    start_frontend

    # 显示状态
    show_status

    echo ""
    echo -e "${GREEN}服务启动完成!${NC}"
    echo -e "${YELLOW}停止服务：./scripts/stop.sh${NC}"
    echo ""
}

# 运行主函数
main
