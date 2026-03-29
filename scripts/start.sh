#!/bin/bash
# DB Compare 项目启动脚本
# 启动后端 API 服务和前端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# PID 文件目录
PID_DIR="$PROJECT_ROOT/.pids"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"

# 后端主机和端口
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# 前端端口
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# 检查是否只启动后端
BACKEND_ONLY=false
if [ "$1" == "--backend-only" ] || [ "$1" == "-b" ]; then
    BACKEND_ONLY=true
fi

# 检查是否只启动前端
FRONTEND_ONLY=false
if [ "$1" == "--frontend-only" ] || [ "$1" == "-f" ]; then
    FRONTEND_ONLY=true
fi

# 打印横幅
print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   DB Compare - 数据库比对系统               ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查环境变量文件
check_env() {
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        echo -e "${YELLOW}警告：backend/.env 文件不存在${NC}"
        if [ -f "$BACKEND_DIR/.env.example" ]; then
            echo -e "${GREEN}正在从 .env.example 创建 .env 文件...${NC}"
            cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
            echo -e "${RED}.env 文件已创建，请配置必要的变量后重新运行${NC}"
            echo -e "${YELLOW}需要配置：DATABASE_URL, ENCRYPTION_KEY${NC}"
        else
            echo -e "${RED}错误：backend/.env.example 也不存在${NC}"
        fi
        exit 1
    fi

    # 检查必要的环境变量
    if grep -q "ENCRYPTION_KEY=<your-32-byte-encryption-key>" "$BACKEND_DIR/.env" 2>/dev/null; then
        echo -e "${RED}错误：请先配置 ENCRYPTION_KEY${NC}"
        echo -e "${YELLOW}生成命令：python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"${NC}"
        exit 1
    fi
}

# 检查 Python 依赖
check_python_deps() {
    echo -e "${GREEN}检查 Python 依赖...${NC}"
    cd "$BACKEND_DIR"
    if ! python -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}安装 Python 依赖...${NC}"
        pip install -e . -q
    fi
}

# 检查 Node 依赖
check_node_deps() {
    echo -e "${GREEN}检查 Node 依赖...${NC}"
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装 Node 依赖...${NC}"
        npm install --silent
    fi
}

# 检查并初始化数据库
check_database() {
    echo -e "${GREEN}检查数据库...${NC}"
    cd "$BACKEND_DIR"

    # 尝试执行迁移（如果失败则跳过）
    if ! python -c "from sqlalchemy import create_engine; import os; print('Database check OK')" 2>/dev/null; then
        echo -e "${YELLOW}执行数据库迁移...${NC}"
        alembic upgrade head 2>/dev/null || echo -e "${YELLOW}迁移可能需要手动配置数据库后执行${NC}"
    fi
}

# 启动后端服务
start_backend() {
    echo -e "${GREEN}启动后端服务...${NC}"

    mkdir -p "$PID_DIR" "$LOG_DIR"
    cd "$BACKEND_DIR"

    # 加载 .env 环境变量
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | grep -v '^[[:space:]]*$' | xargs)
        echo -e "${BLUE}已加载 .env 环境变量${NC}"
    fi

    # 检查是否已在运行
    if [ -f "$PID_DIR/backend.pid" ]; then
        PID=$(cat "$PID_DIR/backend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}后端服务已在运行 (PID: $PID)${NC}"
            return 0
        else
            rm -f "$PID_DIR/backend.pid"
        fi
    fi

    # 启动后端
    nohup uvicorn app.main:app \
        --host "$BACKEND_HOST" \
        --port "$BACKEND_PORT" \
        --reload \
        > "$LOG_DIR/backend.log" 2>&1 &

    PID=$!
    echo $PID > "$PID_DIR/backend.pid"

    # 等待启动
    sleep 2

    # 检查是否成功启动
    if ps -p "$PID" > /dev/null 2>&1; then
        # 等待服务就绪
        for i in {1..10}; do
            if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
                echo -e "${GREEN}后端服务已启动 (PID: $PID)${NC}"
                echo -e "${GREEN}API 文档：http://localhost:$BACKEND_PORT/docs${NC}"
                return 0
            fi
            sleep 1
        done
        echo -e "${YELLOW}后端服务已启动但健康检查未就绪 (PID: $PID)${NC}"
        echo -e "${YELLOW}请查看 logs/backend.log 了解详细信息${NC}"
    else
        echo -e "${RED}后端服务启动失败，请查看 logs/backend.log${NC}"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${GREEN}启动前端服务...${NC}"

    mkdir -p "$PID_DIR" "$LOG_DIR"
    cd "$FRONTEND_DIR"

    # 检查是否已在运行
    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}前端服务已在运行 (PID: $PID)${NC}"
            return 0
        else
            rm -f "$PID_DIR/frontend.pid"
        fi
    fi

    # 设置前端端口
    export PORT="$FRONTEND_PORT"

    # 启动前端
    nohup npm run dev \
        > "$LOG_DIR/frontend.log" 2>&1 &

    PID=$!
    echo $PID > "$PID_DIR/frontend.pid"

    # 等待启动
    sleep 3

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}前端服务已启动 (PID: $PID)${NC}"
        echo -e "${GREEN}访问地址：http://localhost:$FRONTEND_PORT${NC}"
    else
        echo -e "${RED}前端服务启动失败，请查看 logs/frontend.log${NC}"
        return 1
    fi
}

# 显示状态
show_status() {
    echo ""
    echo "================================"
    echo -e "${GREEN}服务状态${NC}"
    echo "--------------------------------"

    local running=0

    if [ -f "$PID_DIR/backend.pid" ]; then
        PID=$(cat "$PID_DIR/backend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "  后端：${GREEN}● 运行中${NC} (PID: $PID)"
            echo -e "       http://localhost:$BACKEND_PORT/docs"
            running=$((running + 1))
        else
            echo -e "  后端：${RED}○ 未运行${NC}"
        fi
    fi

    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "  前端：${GREEN}● 运行中${NC} (PID: $PID)"
            echo -e "       http://localhost:$FRONTEND_PORT"
            running=$((running + 1))
        else
            echo -e "  前端：${RED}○ 未运行${NC}"
        fi
    fi

    echo "================================"
    if [ $running -eq 2 ]; then
        echo -e "${GREEN}所有服务运行正常${NC}"
    elif [ $running -eq 0 ]; then
        echo -e "${YELLOW}没有服务在运行${NC}"
    fi
    echo ""
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服务...${NC}"
    "$PROJECT_ROOT/scripts/stop.sh"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    print_banner

    if [ "$BACKEND_ONLY" = true ]; then
        echo -e "${BLUE}模式：仅启动后端${NC}"
        check_env
        check_python_deps
        check_database
        start_backend
    elif [ "$FRONTEND_ONLY" = true ]; then
        echo -e "${BLUE}模式：仅启动前端${NC}"
        check_node_deps
        start_frontend
    else
        echo -e "${BLUE}模式：启动所有服务${NC}"
        check_env
        check_python_deps
        check_node_deps
        check_database
        start_backend
        start_frontend
    fi

    show_status

    if [ "$BACKEND_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
        echo -e "${YELLOW}提示：按 Ctrl+C 停止所有服务${NC}"
        echo -e "${YELLOW}或使用：./scripts/stop.sh${NC}"
        echo ""

        # 保持运行并监听信号
        while true; do
            sleep 60
        done
    fi
}

# 运行主函数
main
