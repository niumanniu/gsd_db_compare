#!/bin/bash
# DB Compare 项目重启脚本
# 先停止服务，然后重新启动

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# 打印横幅
print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   DB Compare - 重启服务                     ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# 主函数
main() {
    print_banner

    echo -e "${YELLOW}正在停止现有服务...${NC}"
    "$SCRIPTS_DIR/stop.sh"

    echo ""
    echo -e "${GREEN}等待 2 秒...${NC}"
    sleep 2

    echo ""
    echo -e "${GREEN}正在启动服务...${NC}"
    "$SCRIPTS_DIR/start.sh" "$@"
}

# 运行主函数
main
