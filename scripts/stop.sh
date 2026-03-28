#!/bin/bash
# DB Compare 项目停止脚本
# 停止后端 API 服务和前端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

# 停止进程
stop_process() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}$name 未运行 (无 PID 文件)${NC}"
        return 0
    fi

    local PID=$(cat "$pid_file")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}正在停止 $name (PID: $PID)...${NC}"
        kill "$PID" 2>/dev/null

        # 等待进程结束
        local count=0
        while ps -p "$PID" > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done

        # 如果进程还在运行，强制终止
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}$name 未响应，强制终止...${NC}"
            kill -9 "$PID" 2>/dev/null
        fi

        rm -f "$pid_file"
        echo -e "${GREEN}$name 已停止${NC}"
    else
        echo -e "${YELLOW}$name 未运行 (PID 无效)${NC}"
        rm -f "$pid_file"
    fi
}

# 清理所有 PID 文件
cleanup_pids() {
    if [ -d "$PID_DIR" ]; then
        local pid_count=$(ls -1 "$PID_DIR"/*.pid 2>/dev/null | wc -l)
        if [ "$pid_count" -eq 0 ]; then
            echo -e "${GREEN}清理 PID 目录...${NC}"
            rm -rf "$PID_DIR"
        fi
    fi
}

# 主函数
main() {
    echo ""
    echo "================================"
    echo -e "${GREEN}DB Compare - 数据库比对系统${NC}"
    echo "================================"
    echo ""

    # 确保 PID 目录存在
    if [ ! -d "$PID_DIR" ]; then
        echo -e "${YELLOW}PID 目录不存在，服务可能未启动${NC}"
        exit 0
    fi

    # 停止服务
    stop_process "backend"
    stop_process "frontend"

    # 清理
    cleanup_pids

    echo ""
    echo "================================"
    echo -e "${GREEN}所有服务已停止${NC}"
    echo "================================"
    echo ""
}

# 运行主函数
main
