#!/bin/bash
# DB Compare 项目状态检查脚本

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
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# 打印横幅
print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   DB Compare - 服务状态                     ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查进程状态
check_process() {
    local name=$1
    local display_name=$2
    local port=$3
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "  ${display_name}: ${RED}○ 未启动${NC}"
        return 1
    fi

    local PID=$(cat "$pid_file")

    if ps -p "$PID" > /dev/null 2>&1; then
        # 检查端口是否可访问
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1 || \
           curl -s "http://localhost:$port" > /dev/null 2>&1; then
            echo -e "  ${display_name}: ${GREEN}● 运行中${NC} (PID: $PID)"
            echo -e "    ${BLUE}→${NC} http://localhost:$port"
            return 0
        else
            echo -e "  ${display_name}: ${YELLOW}● 运行中 (PID: $PID) - 健康检查失败${NC}"
            echo -e "    ${YELLOW}→ 请查看 logs/${name}.log${NC}"
            return 0
        fi
    else
        echo -e "  ${display_name}: ${RED}○ 未运行${NC} (PID 无效)"
        return 1
    fi
}

# 显示日志尾部
show_logs() {
    local name=$1
    local lines=${2:-10}
    local log_file="$LOG_DIR/${name}.log"

    if [ -f "$log_file" ]; then
        echo ""
        echo -e "${BLUE}最近日志 (logs/${name}.log):${NC}"
        echo "--------------------------------"
        tail -n "$lines" "$log_file"
        echo "--------------------------------"
    fi
}

# 主函数
main() {
    print_banner

    local backend_ok=0
    local frontend_ok=0

    echo -e "${GREEN}服务状态:${NC}"
    echo "--------------------------------"

    check_process "backend" "后端 API" "$BACKEND_PORT" && backend_ok=1
    check_process "frontend" "前端服务" "$FRONTEND_PORT" && frontend_ok=1

    echo "--------------------------------"

    # 显示访问地址
    echo ""
    echo -e "${GREEN}访问地址:${NC}"
    if [ $backend_ok -eq 1 ]; then
        echo "  后端 API:  http://localhost:$BACKEND_PORT"
        echo "  API 文档：http://localhost:$BACKEND_PORT/docs"
        echo "  健康检查：http://localhost:$BACKEND_PORT/health"
    else
        echo "  后端 API:  ${RED}未运行${NC}"
    fi

    if [ $frontend_ok -eq 1 ]; then
        echo "  前端页面：http://localhost:$FRONTEND_PORT"
    else
        echo "  前端页面：${RED}未运行${NC}"
    fi

    # 显示操作提示
    echo ""
    echo -e "${GREEN}快速操作:${NC}"
    echo "  启动服务：${BLUE}./scripts/start.sh${NC}"
    echo "  停止服务：${BLUE}./scripts/stop.sh${NC}"
    echo "  查看日志：${BLUE}tail -f logs/backend.log${NC}"

    # 如果有服务失败，显示日志
    if [ $backend_ok -eq 0 ] && [ -f "$LOG_DIR/backend.log" ]; then
        show_logs "backend" 5
    fi

    echo ""
    echo "================================"
}

# 运行主函数
main
