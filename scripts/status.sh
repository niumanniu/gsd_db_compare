#!/bin/bash
# DB Compare 项目状态检查脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

# 检查进程状态
check_process() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "$name: ${RED}未启动${NC}"
        return 1
    fi

    local PID=$(cat "$pid_file")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "$name: ${GREEN}运行中${NC} (PID: $PID)"
        return 0
    else
        echo -e "$name: ${RED}未运行${NC} (PID 无效)"
        return 1
    fi
}

# 主函数
main() {
    echo ""
    echo "================================"
    echo -e "${GREEN}DB Compare - 数据库比对系统${NC}"
    echo "================================"
    echo ""

    echo -e "${GREEN}服务状态:${NC}"
    echo "----------------"

    local backend_ok=0
    local frontend_ok=0

    check_process "backend" && backend_ok=1
    check_process "frontend" && frontend_ok=1

    echo "----------------"

    # 显示访问地址
    echo ""
    echo -e "${GREEN}访问地址:${NC}"
    if [ $backend_ok -eq 1 ]; then
        echo "  后端 API:  http://localhost:8000"
        echo "  API 文档：http://localhost:8000/docs"
    else
        echo "  后端 API:  ${RED}未运行${NC}"
    fi

    if [ $frontend_ok -eq 1 ]; then
        echo "  前端页面：http://localhost:5173"
    else
        echo "  前端页面：${RED}未运行${NC}"
    fi

    echo ""
    echo "================================"
}

# 运行主函数
main
