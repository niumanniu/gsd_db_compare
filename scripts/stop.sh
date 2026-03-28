#!/bin/bash
# DB Compare 项目停止脚本
# 停止后端 API 服务和前端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/logs"

# 打印横幅
print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   DB Compare - 停止服务                     ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# 停止进程（优雅方式）
stop_process() {
    local name=$1
    local display_name=$2
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "  ${display_name}: ${YELLOW}未运行${NC}"
        return 0
    fi

    local PID=$(cat "$pid_file")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "  ${display_name}: ${YELLOW}正在停止 (PID: $PID)...${NC}"
        kill -TERM "$PID" 2>/dev/null

        # 等待进程优雅退出
        local count=0
        while ps -p "$PID" > /dev/null 2>&1 && [ $count -lt 5 ]; do
            sleep 1
            count=$((count + 1))
        done

        # 如果进程还在运行，强制终止
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "  ${display_name}: ${YELLOW}强制终止...${NC}"
            kill -9 "$PID" 2>/dev/null
            sleep 1
        fi

        rm -f "$pid_file"
        echo -e "  ${display_name}: ${GREEN}已停止${NC}"
    else
        echo -e "  ${display_name}: ${YELLOW}未运行 (清理无效 PID)${NC}"
        rm -f "$pid_file"
    fi
}

# 清理目录
cleanup() {
    # 清理空的 PID 目录
    if [ -d "$PID_DIR" ]; then
        local pid_count=$(ls -1 "$PID_DIR"/*.pid 2>/dev/null | wc -l || echo "0")
        if [ "$pid_count" -eq 0 ]; then
            rmdir "$PID_DIR" 2>/dev/null || true
        fi
    fi
}

# 主函数
main() {
    print_banner

    # 检查 PID 目录是否存在
    if [ ! -d "$PID_DIR" ]; then
        echo -e "${YELLOW}PID 目录不存在，服务可能未启动${NC}"
        echo ""
        return 0
    fi

    echo -e "${GREEN}正在停止服务...${NC}"
    echo ""

    # 停止服务
    stop_process "backend" "后端 API"
    stop_process "frontend" "前端服务"

    # 清理
    cleanup

    echo ""
    echo "================================"
    echo -e "${GREEN}所有服务已停止${NC}"
    echo "================================"
    echo ""
}

# 运行主函数
main
